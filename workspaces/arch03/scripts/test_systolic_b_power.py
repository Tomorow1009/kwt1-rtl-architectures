"""New B power inventory and native-SAIF wiring, without EDA acceptance."""
import tempfile
import unittest
import tkinter
from pathlib import Path
from test_dma16_power import fake_databases
from test_native_saif_activity import WINDOW
from systolic_b_power import script
from icb32_power_numbers import parse_sram


def sram(count):
    rows=['Design : e203_soc_top','Report : -cell_power']
    for name,n in [('u_e203_itcm_gnrl_ram',32),('u_e203_dtcm_gnrl_ram',32),
                   ('u_arch03_shared',64),('u_arch03_accel',count)]:
        for i in range(n):
            rows.append('soc/%s/bank%d/mem 1.00000000e-06 2.00000000e-06 3.00000000e-07 3.30000000e-06 (0.1%%) a'%(name,i))
    return '\n'.join(rows)+'\n'


class BPowerTests(unittest.TestCase):
    def test_B_92_macros_cannot_accept_R4_96_inventory(self):
        self.assertEqual(parse_sram(sram(92),'systolic_b')['cell_count'],220)
        self.assertEqual(parse_sram(sram(96))['cell_count'],224)
        with self.assertRaises(ValueError):parse_sram(sram(96),'systolic_b')
        with self.assertRaises(ValueError):parse_sram(sram(92))

    def test_native_script_preserves_conditions_and_B_macro_guards(self):
        with tempfile.TemporaryDirectory() as folder:
            run=Path(folder);fake_databases(run)
            text=script({},run,run/'layer_01.saif',WINDOW,'tb_top/u_e203_soc_top')
            self.assertEqual(tkinter.Tcl().call('info','complete',text),1)
            self.assertIn('!= 220',text);self.assertNotIn('!= 224',text)
            self.assertIn('read_saif -strip_path tb_top/u_e203_soc_top',text)
            self.assertNotIn('read_vcd ',text)
            self.assertIn('*/u_arch03_accel/* RAMSP128X16 92',text)
            self.assertIn('power_x_transition_derate_factor',text)
            self.assertIn('report_disable_timing',text)


if __name__=='__main__':unittest.main()
