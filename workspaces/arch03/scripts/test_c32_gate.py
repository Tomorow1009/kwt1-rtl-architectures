"""Independent RTL-port/negative provenance checks for the C32 gate observer."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import tkinter

import c32_gate as gate
import c32_gate_monitor as monitor
from test_icb32_gate_power import rtl_ports
from test_dma16_gate import top
import n1_data as data


def probe():
    cells={r:'actual_mems/'+s for r,s in gate.INSTANCE_SUFFIXES.items()};lines=[];pins={}
    for role,reference in gate.REFERENCES.items():
        lines.append('cell\t%s\t%s\t%s'%(role,cells[role],reference));pins[role]=[]
        for name,direction in gate.port_bits(rtl_ports(reference)).items():
            path=cells[role]+'/'+name;pins[role].append(path);lines.append('pin\t%s\t%s\t%s'%(role,path,direction))
    for name in ('test_mode','pllbypass','plloutdivby1'):
        lines.append('guard\t%s\tclock/u_e203_subsys_hclkgen/%s\tin'%(name,name))
    lines.append('guard\tbootrom_selected\taon/u_sirv_aon_wrapper/bootrom_deglitch/io_q\tout')
    groups=dict(dma_interface=[p for p in pins['accel'] if '/dma_' in p],core_interface=pins['core'],
        status_interface=pins['accel']+pins['core']+pins['decoder'])
    return '\n'.join(lines),'\n'.join('%s\t%d\t%s'%(name,len(paths),' '.join(paths)) for name,paths in groups.items())


class C32GateTests(unittest.TestCase):
    def test_probe_matches_independently_read_rtl_ports_and_rejects_old_arbiter(self):
        for role,ref in gate.REFERENCES.items():self.assertEqual(gate.interfaces()[role],rtl_ports(ref),role)
        text,frozen=probe();receipt=gate.parse_probe(text,frozen);self.assertFalse(receipt['alias_binding_used'])
        for bit in ('arb/accepted_queue_count[3]','decoder/out_data[63]','core/result[31]'):
            line=next(line for line in text.splitlines() if bit in line)
            with self.assertRaises(ValueError):gate.parse_probe(text.replace(line,''),frozen)
        with self.assertRaises(ValueError):gate.parse_probe(text.replace('arch03_icb_arb2_queued','arch03_icb_arb2_turnover'),frozen)

    def test_monitor_uses_actual_port_payload_and_no_internal_total_alias(self):
        text,frozen=probe();receipt=gate.parse_probe(text,frozen)
        source=(gate.A3/'tb/arch03_c32_monitor.svh').read_text()
        for depth in (2,):
            generated=monitor.generate(source,receipt['bindings'],depth)
            for forbidden in ('`A3DMA','`A3MEM','pe_valid','converted_total','total.hex','input_bytes_q',
                              'transport.empty','TRANSACTION_DEPTH','ARCH03_N1_TOTAL_PROOF'):
                self.assertNotIn(forbidden,generated)
            self.assertIn('arch03_p80_gate_proof #(.DEPTH(%d))'%depth,generated)
            self.assertIn('arch03_p80_route_observer #(.DEPTH(%d))'%depth,generated)
            self.assertIn('.cpu_accept(u_e203_soc_top.actual_mems.u_arch03_arb.cpu_cmd_valid',generated)
            self.assertIn(monitor.PROOF,generated)
        for depth in (0,1,3,4,8,16):
            with self.assertRaises(ValueError):monitor.generate(source,receipt['bindings'],depth)
        tb=gate.testbench(top(),receipt);self.assertIn('arch03_c32_gate_monitor.svh',tb)

    def test_result_scope_rejects_missing_route_duplicate_marker_and_fabricated_total(self):
        positive='P80_BUS_ROUTE_PASS fixture\n'+monitor.PROOF
        with patch.object(gate.runtime_parser,'parse_result',return_value={'status':'fixture'}) as parser:
            self.assertEqual(gate.parse_result(positive,0),{'status':'fixture'})
            self.assertEqual(parser.call_args[0][2],[monitor.PROOF])
        for bad in (monitor.PROOF,positive+'\n'+monitor.PROOF,positive+'\nARCH03_N1_TOTAL_PROOF count=25344'):
            with self.assertRaises(ValueError):gate.parse_result(bad,0)

    def test_capture_checks_coordinates_and_saturation_without_filling_total(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);values=[i-12672 for i in range(25344)];sats=[int(i%37==0) for i in range(25344)]
            data.write_hex(root/'result.hex',values,16);data.write_hex(root/'saturated.hex',sats,1)
            lines=['%d,%d,%d,%d'%(i//256,i%256,values[i],sats[i]) for i in reversed(range(25344))]
            capture=root/'out.csv';capture.write_text('\n'.join(lines)+'\n')
            result=gate.check_capture(capture,root);self.assertFalse(result['total_checked']);self.assertEqual(result['outputs'],25344)
            for bad in (lines[:-1],lines+[lines[0]],['98,255,12671,1']+lines[1:]):
                capture.write_text('\n'.join(bad)+'\n')
                with self.assertRaises(ValueError):gate.check_capture(capture,root)


if __name__=='__main__':unittest.main()
