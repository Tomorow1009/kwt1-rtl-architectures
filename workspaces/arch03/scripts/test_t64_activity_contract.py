"""Exercise actual replay/audit/PT construction against four-transfer windows."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from test_native_saif_activity import WINDOW,fixture
from test_dma16_power import fake_databases
from native_saif_replay import capture_commands
from native_saif_activity import audit
from icb32_power import window_values as old_window
from t64_window import window_values
from t64_power import script


class FourTransferActivity(unittest.TestCase):
    def window(self):
        return dict(WINDOW,transfer_bytes=50784,transfer_transactions=12696)

    def test_separate_contracts_and_reject_bad_timing(self):
        new=self.window()
        self.assertEqual(window_values(new),old_window(WINDOW))
        with self.assertRaises(ValueError):window_values(WINDOW)
        with self.assertRaises(ValueError):old_window(new)
        for key,value in [('transfer_bytes',50780),('transfer_transactions',12695),
                          ('finished_cycle',30014),('finished_ns','200099'),
                          ('end_ns','200099.99'),('period_ns','6.667')]:
            with self.subTest(key=key),self.assertRaises(ValueError):
                window_values(dict(new,**{key:value}))

    def test_replay_and_full_activity_preserve_actual_duration(self):
        with tempfile.TemporaryDirectory() as d:
            gate=Path(d)/'gate';run=Path(d)/'run';gate.mkdir();run.mkdir()
            original=['/vcs','-top','tb_top','-o',str(gate/'simv'),str(gate/'mapped.v')]
            (gate/'compile_command.json').write_text(json.dumps(original))
            (gate/'layer_01_command.json').write_text(json.dumps([str(gate/'simv'),'+CAPTURE='+str(gate/'layer_01.csv')]))
            row=dict(case='layer_01',task_window=self.window())
            cmd,runtime,ucli=capture_commands(gate,run,row,window_reader=window_values)
            self.assertIn(str(gate/'mapped.v'),cmd)
            self.assertIn('run 100ns',ucli);self.assertIn('run 199999.98ns',ucli)
            self.assertEqual(json.loads((gate/'compile_command.json').read_text()),original)
            saif=run/'layer_01.saif';saif.write_text(fixture())
            result=audit(saif,self.window(),window_reader=window_values)
            self.assertEqual(result['source_port_bits'],106)
            self.assertEqual(result['statistics']['unknown_declarations'],8)
            with self.assertRaises(ValueError):audit(saif,self.window())

    def test_PT_four_transfers_and_original_macro_clock_checks(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);fake_databases(p)
            text=script({},p,p/'L01.saif',self.window(),'tb_top/u_e203_soc_top',p/'precise.sdc')
            self.assertIn('read_saif -strip_path tb_top/u_e203_soc_top',text)
            self.assertNotIn('read_vcd ',text)
            self.assertIn('!= 220',text)
            self.assertIn('abs($hf_period-6.666666)>1e-12',text)
            self.assertIn('report_disable_timing',text)


if __name__=='__main__':unittest.main()
