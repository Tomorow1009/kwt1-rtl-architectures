import copy
import json
import tempfile
import unittest
from pathlib import Path
from native_saif_replay import capture_commands
from native_saif_crosscheck import compare
from test_native_saif_activity import WINDOW

class ReplayTests(unittest.TestCase):
    def test_replay_cannot_write_frozen_capture_or_create_VCD(self):
        with tempfile.TemporaryDirectory() as folder:
            gate=Path(folder)/'old';run=Path(folder)/'new';gate.mkdir();run.mkdir()
            old=['/vcs','-top','tb_top','-o',str(gate/'simv'),str(gate/'mapped.v')]
            runtime=[str(gate/'simv'),'+CAPTURE='+str(gate/'layer_01.csv'),
                '+BOOT_DIR='+str(gate/'boot'),'+ACTIVITY='+str(gate/'layer_01.vcd')]
            (gate/'compile_command.json').write_text(json.dumps(old))
            (gate/'layer_01_command.json').write_text(json.dumps(runtime))
            compile_cmd,command,script=capture_commands(gate,run,dict(case='layer_01',task_window=WINDOW))
            self.assertIn(str(gate/'mapped.v'),compile_cmd)
            self.assertIn('-debug_access+all',compile_cmd)
            self.assertIn('+CAPTURE='+str(run/'layer_01.csv'),command)
            self.assertIn('+BOOT_DIR='+str(gate/'boot'),command)
            self.assertFalse(any(arg.startswith('+ACTIVITY=') for arg in command))
            self.assertIn('run 100ns',script);self.assertIn('run 199999.98ns',script)
            self.assertEqual(json.loads((gate/'compile_command.json').read_text()),old)
            (gate/'compile_command.json').write_text(json.dumps(old+['+define+FPGA']))
            with self.assertRaises(ValueError):capture_commands(gate,run,dict(case='layer_01',task_window=WINDOW))

    def test_crosscheck_requires_same_mapping_and_one_percent(self):
        p=dict(internal='0.7',switching='0.2',leakage='0.1',total='1.0')
        baseline=dict(base_units=dict(time='ns'),settings=dict(mode='averaged'),
            sources=dict(exact_mapping=100),reported_power_w=p,
            modules=dict(cpu=dict(derived_power_w=p)))
        candidate=copy.deepcopy(baseline)
        candidate['reported_power_w']['total']='1.01'
        self.assertTrue(compare(baseline,candidate)['passed'])
        candidate['modules']['cpu']['derived_power_w']['total']='1.01001'
        self.assertFalse(compare(baseline,candidate)['passed'])
        candidate['sources']['exact_mapping']=99
        with self.assertRaises(ValueError):compare(baseline,candidate)

if __name__=='__main__':unittest.main()
