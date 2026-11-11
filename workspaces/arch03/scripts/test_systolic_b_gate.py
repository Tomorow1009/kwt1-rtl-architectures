"""Check mapped-observer contracts against actual B RTL port declarations."""
import unittest
import systolic_b_gate as gate
from systolic_b_gate_monitor import generate
from test_icb32_gate_power import rtl_ports
from test_dma16_gate import top


def probe():
    cells={role:'actual_mems/'+suffix for role,suffix in gate.INSTANCE_SUFFIXES.items()}
    lines=[];pins={}
    for role,reference in gate.REFERENCES.items():
        lines.append('cell\t%s\t%s\t%s'%(role,cells[role],reference));pins[role]=[]
        for name,direction in gate.port_bits(rtl_ports(reference)).items():
            path=cells[role]+'/'+name;pins[role].append(path)
            lines.append('pin\t%s\t%s\t%s'%(role,path,direction))
    for name in ('test_mode','pllbypass','plloutdivby1'):
        lines.append('guard\t%s\tclock/u_e203_subsys_hclkgen/%s\tin'%(name,name))
    lines.append('guard\tbootrom_selected\taon/u_sirv_aon_wrapper/bootrom_deglitch/io_q\tout')
    groups={'dma_interface':[p for p in pins['accel'] if '/dma_' in p],
            'core_interface':pins['core'],
            'status_interface':pins['accel']+pins['core']+pins['decoder']}
    frozen='\n'.join('%s\t%d\t%s'%(name,len(paths),' '.join(paths)) for name,paths in groups.items())
    return '\n'.join(lines),frozen


class GateTests(unittest.TestCase):
    def test_ports_and_binding_reject_missing_or_wrong_decoder(self):
        for role,reference in gate.REFERENCES.items():
            self.assertEqual(gate.interfaces()[role],rtl_ports(reference),role)
        text,frozen=probe();receipt=gate.parse_probe(text,frozen)
        self.assertEqual(receipt['port_interfaces']['core']['result'],('out',32))
        self.assertEqual(receipt['port_interfaces']['core']['saturated'],('out',2))
        for bit in ('decoder_v3/out_data[63]','core/result[31]','core/layout_v3'):
            line=next(line for line in text.splitlines() if bit in line)
            with self.assertRaises(ValueError):gate.parse_probe(text.replace(line,''),frozen)
        with self.assertRaises(ValueError):gate.parse_probe(text,frozen.replace('decoder_v3/out_data[63]','decoder_v3/out_data[99]'))
        with self.assertRaises(ValueError):gate.parse_probe(text.replace('/decoder_v3','/decoder'),frozen)

    def test_generated_observer_keeps_pair_checks_and_has_no_implementation_aliases(self):
        text,frozen=probe();receipt=gate.parse_probe(text,frozen)
        monitor=generate((gate.A3/'tb/arch03_systolic_b_monitor.svh').read_text(),receipt['bindings'])
        for alias in ('input_bytes_q','load_count_q','error_q','half_q','transport.empty','`A3DMA','`A3MEM'):
            self.assertNotIn(alias,monitor)
        self.assertIn('core.result[a3_lane*16+:16]',monitor)
        self.assertIn('core.saturated[a3_lane]',monitor)
        self.assertIn('requires explicit v3 layout',monitor)
        self.assertIn('arch03_systolic_b_gate_monitor.svh',gate.testbench(top(),receipt))
        wrong=dict(receipt['bindings']);wrong['decoder']=wrong['accel']+'.decoder'
        with self.assertRaises(ValueError):generate((gate.A3/'tb/arch03_systolic_b_monitor.svh').read_text(),wrong)


if __name__=='__main__':unittest.main()
