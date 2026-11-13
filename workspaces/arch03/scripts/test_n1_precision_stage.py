"""Lifecycle tests: never overlap an existing stage or mislabel failed precision."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import n1_precision_stage as stage


class PrecisionStageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.bundle = self.root/'bundle'
        (self.bundle/'runs').mkdir(parents=True)
        self.session = self.bundle/'runs/precision01'
        self.cfg = {'server_root': str(self.root)}
        self.ops = {'manifest_sha256': 'a'*64}
        self.patches = [patch.object(stage.common, 'ROOT', self.bundle),
            patch.object(stage.common, 'ACTIVE_CHILD', None), patch.object(stage.common, 'LOCK', None),
            patch.object(stage.common, 'inputs', return_value={}),
            patch.object(stage.n1_paths, 'recheck'), patch.object(stage.n1_paths, 'receipt', return_value={}),
            patch.object(stage, 'operations_identity', return_value=self.ops)]
        for p in self.patches:p.start()

    def tearDown(self):
        for p in reversed(self.patches):p.stop()
        self.temp.cleanup()

    def run_stage(self, result):
        def audit(a, h, d, output):
            self.assertTrue((self.root/'.arch02_team_lock/owner.json').is_file())
            self.assertFalse(output.exists())
            output.mkdir()
            stage.common.save(output/'summary.json', result)
            return result
        return stage.execute(self.cfg, self.session, 'a', 'b', 'd', self.ops, audit)

    def test_success_preserves_summary_and_releases(self):
        self.run_stage({'status':'passed', 'internal_precision_verified':True})
        record = json.loads((self.session/'state.json').read_text())['stages']['n1_precision']
        self.assertEqual(record['status'], 'passed')
        self.assertEqual(len(record['summary_sha256']), 64)
        self.assertFalse((self.root/'.arch02_team_lock').exists())

    def test_precision_failure_never_passes(self):
        with self.assertRaisesRegex(ValueError, 'did not pass'):
            self.run_stage({'status':'failed_precision', 'internal_precision_verified':False})
        self.assertTrue((self.session/'n1_precision/summary.json').exists())
        record = json.loads((self.session/'state.json').read_text())['stages']['n1_precision']
        self.assertEqual(record['status'], 'failed')
        self.assertNotIn('summary_sha256', record)
        self.assertFalse((self.root/'.arch02_team_lock').exists())

    def test_existing_lock_is_untouched_and_no_output(self):
        lock = self.root/'.arch02_team_lock'
        lock.mkdir(); (lock/'owner.json').write_text('existing-owner')
        with self.assertRaises(FileExistsError):self.run_stage({})
        self.assertFalse(self.session.exists())
        self.assertEqual((lock/'owner.json').read_text(), 'existing-owner')

    def test_existing_session_is_untouched(self):
        self.session.mkdir(); (self.session/'evidence').write_text('preserve')
        with self.assertRaisesRegex(ValueError, 'new session'):self.run_stage({})
        self.assertEqual((self.session/'evidence').read_text(), 'preserve')
        self.assertFalse((self.root/'.arch02_team_lock').exists())


if __name__ == '__main__':unittest.main()
