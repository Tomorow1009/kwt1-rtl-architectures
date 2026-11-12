"""Offline N1 mapped-observer contracts; no EDA or CPU acceptance."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import tkinter

import n1_gate as gate
import n1_data
import n1_gate_monitor as monitor
import n1_timing_audit as timing
from test_icb32_gate_power import rtl_ports
from test_dma16_gate import top
from test_dma16_power import fake_databases


def probe():
    cells={role:'actual_mems/'+suffix for role,suffix in gate.INSTANCE_SUFFIXES.items()}
    lines=[];pins={}
    for role,reference in gate.REFERENCES.items():
        lines.append('cell\t%s\t%s\t%s' % (role,cells[role],reference));pins[role]=[]
        for name,direction in gate.port_bits(rtl_ports(reference)).items():
            path=cells[role]+'/'+name;pins[role].append(path)
            lines.append('pin\t%s\t%s\t%s' % (role,path,direction))
    for name in ('test_mode','pllbypass','plloutdivby1'):
        lines.append('guard\t%s\tclock/u_e203_subsys_hclkgen/%s\tin' % (name,name))
    lines.append('guard\tbootrom_selected\taon/u_sirv_aon_wrapper/bootrom_deglitch/io_q\tout')
    groups={'dma_interface':[p for p in pins['accel'] if '/dma_' in p],
            'core_interface':pins['core'],'decoder_interface':pins['decoder'],
            'status_interface':pins['accel']+pins['core']+pins['decoder']}
    frozen='\n'.join('%s\t%d\t%s' % (name,len(paths),' '.join(paths)) for name,paths in groups.items())
    return '\n'.join(lines),frozen


class N1GateTests(unittest.TestCase):
    def test_ports_are_actual_n1_and_missing_wrong_old_decoder_rejected(self):
        for role,reference in gate.REFERENCES.items():
            self.assertEqual(gate.interfaces()[role],rtl_ports(reference),role)
        text,frozen=probe();receipt=gate.parse_probe(text,frozen)
        self.assertFalse(receipt['alias_binding_used'])
        for bit in ('decoder/out_data[63]','core/result[31]','core/layout_v3'):
            line=next(line for line in text.splitlines() if bit in line)
            with self.assertRaises(ValueError):gate.parse_probe(text.replace(line,''),frozen)
        for bad in (text.replace('arch03_n1_accel','arch03_systolic_b_accel'),
                    text.replace('/decoder','/decoder_v3')):
            with self.assertRaises(ValueError):gate.parse_probe(bad,frozen)
        with self.assertRaises(ValueError):gate.parse_probe(text,frozen.replace('decoder/out_data[63]','decoder/out_data[99]'))

    def test_monitor_scope_is_actual_result_saturation_not_reference_total(self):
        text,frozen=probe();receipt=gate.parse_probe(text,frozen)
        source=(gate.A3/'tb/arch03_n1_monitor.svh').read_text()
        generated=monitor.generate(source,receipt['bindings'])
        for forbidden in ('input_bytes_q','load_count_q','error_q','half_q','transport.empty',
                          '`A3DMA','`A3MEM','converted_total','slot_block','pe_valid',
                          'n1_actual_total','n1_expected_total','total.hex','ARCH03_N1_TOTAL_PROOF'):
            self.assertNotIn(forbidden,generated)
        self.assertIn('core.result[a3_lane*16+:16]',generated)
        self.assertIn('core.saturated[a3_lane]',generated)
        self.assertIn('internal_total_observable=false',generated)
        self.assertIn('$fdisplay(a3_file,"%0d,%0d,%0d,%0d"',generated)
        self.assertIn(monitor.PROOF,generated)
        self.assertIn('arch03_n1_gate_monitor.svh',gate.testbench(top(),receipt))
        wrong=dict(receipt['bindings']);wrong['decoder']=wrong['accel']+'.decoder_v3'
        with self.assertRaises(ValueError):monitor.generate(source,wrong)
        with self.assertRaises(ValueError):monitor.generate(source.replace('n1_total_count!=25344','n1_total_count!=1'),receipt['bindings'])

    def test_exact_gate_marker_required_and_rtl_marker_not_accepted(self):
        with patch.object(gate.runtime_parser,'parse_result',return_value={'status':'fixture'}) as parser:
            result=gate.parse_result(monitor.PROOF,7,['fixture-marker'])
            self.assertEqual(result,{'status':'fixture'})
            self.assertEqual(parser.call_args[0][2],['fixture-marker',monitor.PROOF])
        for log in ('',monitor.PROOF+'\n'+monitor.PROOF,
                    monitor.PROOF+'\nARCH03_N1_TOTAL_PROOF count=25344'):
            with self.assertRaises(ValueError):gate.parse_result(log,0)
        with self.assertRaisesRegex(ValueError,'signed33 total proof'):
            n1_data.parse_result(monitor.PROOF,0)

    def test_capture_actual_four_fields_coordinates_and_saturation(self):
        with tempfile.TemporaryDirectory() as name:
            folder=Path(name);capture=folder/'output.csv'
            values=[-32768+i%65536 for i in range(25344)]
            sats=[int(i%97==0) for i in range(25344)]
            n1_data.write_hex(folder/'result.hex',values,16)
            n1_data.write_hex(folder/'saturated.hex',sats,1)
            lines=['%d,%d,%d,%d' % (i//256,i%256,values[i],sats[i]) for i in range(25344)]
            capture.write_text('\n'.join(lines)+'\n')
            checked=gate.check_capture(capture,folder)
            self.assertEqual(checked['outputs'],25344)
            self.assertFalse(checked['total_checked'])
            self.assertFalse(checked['internal_total_observable'])
            for wrong in (lines[:-1],lines+[lines[0]],['99,0,0,0']+lines[1:],
                          ['0,0,0,0']+lines[1:],['0,0,-32768,0']+lines[1:],
                          [line+',123' for line in lines]):
                capture.write_text('\n'.join(wrong)+'\n')
                with self.assertRaises(ValueError):gate.check_capture(capture,folder)

    def test_probe_and_timing_query_are_readonly_complete_tcl(self):
        with tempfile.TemporaryDirectory() as name:
            folder=Path(name);fake_databases(folder)
            for text in (gate.probe_script(folder),timing.script(folder)):
                self.assertEqual(tkinter.Tcl().call('info','complete',text),1)
                self.assertIn('arch03_n1_accel',text)
                for forbidden in ('\ncompile ', '\nset_false_path ', '\nset_disable_timing ',
                                  '\nset_clock_gating_check ', '\nwrite -format'):
                    self.assertNotIn(forbidden,text)
            self.assertIn('all_high_fanout -nets -threshold 1000',timing.script(folder))

    def test_high_fanout_parser_never_drops_missing_duplicate_nets(self):
        self.assertEqual(timing.parse_high_fanout('threshold\t1000\ncount\t1\nnet\tx/y\n')['count'],1)
        for text in ('threshold\t999\ncount\t0', 'threshold\t1000\ncount\t1',
                     'threshold\t1000\ncount\t2\nnet\tx\nnet\tx'):
            with self.assertRaises(ValueError):timing.parse_high_fanout(text)

    def test_b0_summary_cannot_be_n1_synthesis(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name);run=root/'synthesis';run.mkdir()
            summary={'synthesis_completed':True,'scope':'systolic_b_whole_soc_task_mode_preliminary_synthesis'}
            (run/'summary.json').write_text(json.dumps(summary))
            digest=gate.sha(run/'summary.json')
            (root/'state.json').write_text(json.dumps({'stages':{'n1_synth':{'status':'passed','summary_sha256':digest}}}))
            with self.assertRaisesRegex(ValueError,'not complete'):
                gate.verify_synthesis(run,digest,{'server_root':str(root)})


if __name__=='__main__':unittest.main()
