"""Exercise evidence tampering and coverage failures in disposable fixtures."""
import json
from pathlib import Path
import tempfile
import unittest

from inspect_existing import inspect, sha, inside


class ExistingEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.write('server_config.json', {'server_root': str(self.root), 'models': {}})
        (self.root / 'rtl.sv').write_text('module example; endmodule\n')
        for name in ['layer_%02d' % n for n in range(1, 13)] + ['extremes', 'rounding']:
            self.write('validated_data/' + name + '/layout.json', {'shift': 11 if name == 'rounding' else 12})
            (self.root / 'validated_data' / name / 'load.hex').write_text('0000\n')
        files = {p.relative_to(self.root).as_posix(): sha(p) for p in self.root.rglob('*') if p.is_file()}
        data = {'X:/real_sample_001/manifest.json': '0' * 64}
        for n in range(1, 13):
            for kind in ('float', 'integer'):
                data['X:/real_sample_001/layer_%02d/%s_tensors.npz' % (n, kind)] = '1' * 64
        self.write('manifest.json', dict(development=False, source_commit='a' * 40, files=files, data_hashes=data))
        self.write('runs/software/summary.json', dict(status='passed', software_real_outputs=304128))
        self.write('runs/unit/summary.json', dict(status='passed'))
        (self.root / 'capture.csv').write_text('0,1,1,0\n')
        self.write('runs/vcs/summary.json', dict(status='passed', real_outputs=304128,
            vendor_model_mode='functional', bundle_manifest_sha256=sha(self.root / 'manifest.json'),
            sources={str(self.root / 'rtl.sv'): sha(self.root / 'rtl.sv')},
            jobs=[dict(passed=True, tag='layer_01', capture_sha256=sha(self.root / 'capture.csv'))]))
        (self.root / 'runs/vcs/layer_01.csv').write_bytes((self.root / 'capture.csv').read_bytes())
        (self.root / 'mapped.ddc').write_bytes(b'fixture-only')
        self.write('runs/audit/summary.json', dict(status='passed', integer_and_capture_rechecked=304128,
            latches=0, macro_counts={'RAMSP128X16': 8, 'RAMSP4096X16': 2},
            slack_ns={'max': 0.01, 'min': 0.001}, physical_signoff=False,
            artifact_hashes={str(self.root / 'mapped.ddc'): sha(self.root / 'mapped.ddc')}))
        stages = {name: dict(status='passed', exit_code=0) for name in
                  ('preflight', 'software', 'unit', 'vcs', 'synth', 'hold', 'audit')}
        for name in ('software', 'unit', 'vcs', 'audit'):
            run = self.root / 'runs' / name
            stages[name].update(run=str(run), summary_sha256=sha(run / 'summary.json'))
        self.write('team_sessions/acceptance01/state.json',
                   dict(manifest_sha256=sha(self.root / 'manifest.json'), stages=stages))

    def write(self, rel, obj):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(obj))

    def test_valid_fixture_and_no_writes(self):
        before = {str(p): sha(p) for p in self.root.rglob('*') if p.is_file()}
        report = inspect(self.root, 'acceptance01')
        self.assertEqual(report['status'], 'existing_evidence_integrity_passed')
        self.assertFalse(report['physical_signoff'])
        self.assertEqual(before, {str(p): sha(p) for p in self.root.rglob('*') if p.is_file()})

    def test_changed_input(self):
        (self.root / 'rtl.sv').write_text('changed')
        with self.assertRaisesRegex(ValueError, 'bundle input'):
            inspect(self.root, 'acceptance01')

    def test_changed_summary(self):
        self.write('runs/software/summary.json', dict(status='passed', software_real_outputs=1))
        with self.assertRaisesRegex(ValueError, 'stage summary'):
            inspect(self.root, 'acceptance01')

    def test_changed_capture(self):
        (self.root / 'runs/vcs/layer_01.csv').write_text('changed')
        with self.assertRaisesRegex(ValueError, 'Changed capture'):
            inspect(self.root, 'acceptance01')

    def test_changed_artifact(self):
        (self.root / 'mapped.ddc').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'audit artifact'):
            inspect(self.root, 'acceptance01')

    def test_running_stage(self):
        path = self.root / 'team_sessions/acceptance01/state.json'
        state = json.loads(path.read_text()); state['stages']['hold']['status'] = 'running'
        path.write_text(json.dumps(state))
        with self.assertRaisesRegex(ValueError, 'Stage not passed'):
            inspect(self.root, 'acceptance01')

    def test_no_path_escape(self):
        with self.assertRaises(ValueError):
            inside(self.root, '../outside')

    def test_lock_reported_not_removed(self):
        lock = self.root / '.arch02_team_lock'; lock.mkdir()
        self.assertTrue(inspect(self.root, 'acceptance01')['team_lock_exists'])
        self.assertTrue(lock.is_dir())


if __name__ == '__main__':
    unittest.main(verbosity=2)
