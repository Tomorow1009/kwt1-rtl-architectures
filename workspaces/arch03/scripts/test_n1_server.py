"""Exercise the shared-lock and versioned-stage boundaries without EDA."""
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch
import n1_server


class N1ServerBoundary(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root/'handoff/team').mkdir(parents=True)
        (self.root/'handoff/team/server_config.json').write_text(json.dumps(dict(server_root=str(self.root))))
        self.common = n1_server.common
        self.root_patch = patch.object(self.common, 'ROOT', self.root)
        self.root_patch.start(); self.addCleanup(self.root_patch.stop)
        self.free_patch = patch.object(n1_server.shutil, 'disk_usage', return_value=types.SimpleNamespace(free=20*1024**3))
        self.free_patch.start(); self.addCleanup(self.free_patch.stop)
        self.common.ACTIVE_CHILD = None

    def invoke(self, *args):
        with patch.object(sys, 'argv', ['n1_server.py']+list(args)), patch.object(self.common, 'inputs'):
            n1_server.main()

    def test_actual_stage_names_and_lock_release(self):
        def verify(*args, **kwargs):
            self.assertTrue((self.root/'.arch02_team_lock/owner.json').is_file())
            return dict(status='fixture_only', cpu_executed=False)
        with patch.dict(sys.modules, {'n1_soc': types.SimpleNamespace(verify=verify)}):
            self.invoke('soc', '--session', 'fresh')
        state = json.loads((self.root/'runs/fresh/state.json').read_text())
        self.assertEqual(set(state['stages']), {'n1_soc'})
        self.assertTrue((self.root/'runs/fresh/n1_soc/summary.json').is_file())
        self.assertFalse((self.root/'.arch02_team_lock').exists())
        with self.assertRaisesRegex(ValueError, 'fresh session'):
            self.invoke('soc', '--session', 'fresh')

    def test_preexisting_lock_is_preserved(self):
        lock = self.root/'.arch02_team_lock'; lock.mkdir()
        (lock/'owner.json').write_text('{"pid":1234,"session":"other"}')
        before = (lock/'owner.json').read_bytes()
        with self.assertRaises(FileExistsError):
            self.invoke('soc', '--session', 'fresh')
        self.assertEqual((lock/'owner.json').read_bytes(), before)
        self.assertFalse((self.root/'runs/fresh').exists())

    def test_missing_predecessor_fails_before_lock_or_run(self):
        for stage in ('gate', 'timing_audit', 'saif', 'power'):
            with self.assertRaisesRegex(ValueError, 'directory and SHA256'):
                self.invoke(stage, '--session', 'missing')
        self.assertFalse((self.root/'.arch02_team_lock').exists())
        self.assertFalse((self.root/'runs').exists())

    def test_failed_stage_is_recorded_without_retaining_owned_lock(self):
        def fail(*args, **kwargs):
            raise RuntimeError('deliberate fixture failure')
        with patch.dict(sys.modules, {'n1_soc': types.SimpleNamespace(verify=fail)}):
            with self.assertRaisesRegex(RuntimeError, 'deliberate fixture'):
                self.invoke('soc', '--session', 'failed')
        record = json.loads((self.root/'runs/failed/state.json').read_text())['stages']['n1_soc']
        self.assertEqual(record['status'], 'failed')
        self.assertFalse((self.root/'.arch02_team_lock').exists())


if __name__ == '__main__':
    unittest.main()
