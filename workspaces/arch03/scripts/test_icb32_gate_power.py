"""New observer/area/activity wiring checks; no EDA or CPU acceptance here."""
import json
import re
import tempfile
import unittest
from pathlib import Path
import tkinter
import icb32_gate as gate
import icb32_power as power
from icb32_gate_monitor import generate
from test_dma16_gate import top
from test_dma16_power import fake_databases


def rtl_ports(reference):
    text=(gate.A3/'rtl'/(reference+'.sv')).read_text()
    header=re.search(r'module\s+\w+(?:\s*#\(.*?\))?\s*\((.*?)\);',text,re.S).group(1)
    ports={}
    for direction,body in re.findall(r'\b(input|output)\b(.*?)(?=\b(?:input|output)\b|$)',header,re.S):
        width=re.search(r'\[(\d+):0\]',body);bits=int(width.group(1))+1 if width else 1
        body=re.sub(r'\[[^]]+\]|\b(?:wire|reg|signed)\b','',body)
        for name in body.split(','):
            name=name.strip()
            if name:ports[name]=('in' if direction=='input' else 'out',bits)
    return ports


def probe():
    parent='actual_mems';cells={role:parent+'/'+suffix for role,suffix in gate.INSTANCE_SUFFIXES.items()}
    lines=[];pins={}
    for role,ref in gate.REFERENCES.items():
        lines.append('cell\t%s\t%s\t%s'%(role,cells[role],ref))
        pins[role]=[]
        for name,direction in gate.port_bits(rtl_ports(ref)).items():
            path=cells[role]+'/'+name;pins[role].append(path)
            lines.append('pin\t%s\t%s\t%s'%(role,path,direction))
    for name in ('test_mode','pllbypass','plloutdivby1'):
        lines.append('guard\t%s\tclock/u_e203_subsys_hclkgen/%s\tin'%(name,name))
    lines.append('guard\tbootrom_selected\taon/u_sirv_aon_wrapper/bootrom_deglitch/io_q\tout')
    groups={'dma_interface':[p for p in pins['accel'] if '/dma_' in p],
            'core_interface':pins['core'],'decoder_interface':pins['decoder']}
    frozen='\n'.join('%s\t%d\t%s'%(name,len(paths),' '.join(paths)) for name,paths in groups.items())
    return '\n'.join(lines),frozen


class GatePowerTests(unittest.TestCase):
    def test_interfaces_against_real_rtl_and_reject_missing_bit(self):
        for role,ref in gate.REFERENCES.items():self.assertEqual(gate.interfaces()[role],rtl_ports(ref),role)
        text,frozen=probe();receipt=gate.parse_probe(text,frozen)
        monitor=generate((gate.A3/'tb/arch03_icb32_monitor.svh').read_text(),receipt['bindings'])
        for alias in ('input_bytes_q','load_count_q','error_q','half_q','transport.empty','`A3DMA','`A3MEM'):
            self.assertNotIn(alias,monitor)
        tb=gate.testbench(top(),receipt);self.assertIn('arch03_icb32_gate_monitor.svh',tb)
        pin=next(line for line in text.splitlines() if 'decoder/out_data[63]' in line)
        with self.assertRaises(ValueError):gate.parse_probe(text.replace(pin,''),frozen)
        with self.assertRaises(ValueError):gate.parse_probe(text,frozen.replace('decoder/out_data[63]','decoder/out_data[99]'))

    def test_real_local_window_and_dynamic_payload(self):
        from icb32_data import read_window
        fixture=json.loads((Path(__file__).parent/'test_fixtures/icb32_local_windows.json').read_text())
        for case in fixture['cases']:
            size=case['encoded_bytes'];window=read_window(case['window_line'],case['result'],size)
            power.window_values(window)
            for key,value in [('transfer_bytes',191616),('transfer_transactions',47904),('encoded_bytes',size-4),('period_ns','6.667')]:
                bad=dict(window);bad[key]=value
                with self.assertRaises(ValueError):power.window_values(bad)

    def test_pt_and_probe_templates(self):
        with tempfile.TemporaryDirectory() as directory:
            run=Path(directory);fake_databases(run)
            cfg=json.loads((gate.ROOT/'handoff/team/server_config.json').read_text())
            from icb32_data import read_window
            case=json.loads((Path(__file__).parent/'test_fixtures/icb32_local_windows.json').read_text())['cases'][0]
            window=read_window(case['window_line'],case['result'],case['encoded_bytes'])
            tcl=power.script(cfg,run,run/'activity.vcd',window)
            self.assertIn('!= 224',tcl);self.assertNotIn('!= 162',tcl)
            for script in (tcl,gate.probe_script(run)):
                self.assertEqual(tkinter.Tcl().call('info','complete',script),1)


if __name__=='__main__':unittest.main()
