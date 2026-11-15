import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import s0_validation as validation
import t80_gate as gate


class S0ProvenanceTests(unittest.TestCase):
    def test_s0_gate_routes_to_separate_verifier_after_hash_check(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);run=root/'mapped';run.mkdir()
            (run/'summary.json').write_text(json.dumps(dict(scope=validation.SCOPE)))
            want=gate.sha(run/'summary.json');cfg={'server_root':str(root)}
            with patch.object(validation,'verify_synthesis',return_value=('S0','area')) as checked:
                self.assertEqual(gate.verify_synthesis(run,want,cfg),('S0','area'))
                checked.assert_called_once_with(run,want,cfg)
                with self.assertRaises(ValueError):gate.verify_synthesis(run,'0'*64,cfg)
                self.assertEqual(checked.call_count,1)

    def test_monolithic_t80_report_does_not_satisfy_s0_identity(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);run=root/'mapped';run.mkdir()
            report=dict(scope='t80_whole_soc_task_mode_preliminary_synthesis',synthesis_completed=True)
            (run/'summary.json').write_text(json.dumps(report));want=gate.sha(run/'summary.json')
            (root/'state.json').write_text(json.dumps({'stages':{'t80_synth':{'status':'passed','summary_sha256':want}}}))
            with self.assertRaisesRegex(ValueError,'incomplete'):
                validation.verify_synthesis(run,want,{'server_root':str(root)})


if __name__=='__main__':unittest.main()
