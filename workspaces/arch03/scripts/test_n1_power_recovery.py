import tempfile
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import n1_power_recovery_20261113 as recovery


class StorageWaitTests(unittest.TestCase):
    def scenario(self, kind):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            run, lock = output/'session/n1_power', output/'lock'
            state, calls = dict(completed=[], child_pid=None), []
            def child(command, output, state, label, run, stage, lock):
                calls.append(label)
                if len(calls) == 1:
                    if kind == 'stage_exists':run.parent.mkdir()
                    if kind == 'lock_exists':lock.mkdir()
                    text = ('self.lock.mkdir()\nOSError: [Errno 28] No space left on device: '
                            '/storage2/IC/.arch02_team_lock')
                    if kind == 'other_failure':text = 'Unrelated failure'
                    (output/(label+'.driver.log')).write_text(text)
                    raise ValueError('Child failed')
                state['completed'].append(dict(label=label))
                return {'passed': True}
            q = SimpleNamespace(run_child=child, atomic_save=lambda *args: None, now=lambda: 'time')
            with patch.object(recovery.time, 'sleep') as sleep:
                if kind == 'recover':
                    recovery.storage_wait_child(q, [], output, state, 'power03', run, 'n1_power', lock)
                    self.assertEqual(state['completed'], [dict(label='power03')])
                    self.assertEqual(len(state['storage_wait_attempts']), 1)
                    self.assertEqual(len(calls), 2)
                    sleep.assert_called_once_with(30)
                else:
                    with self.assertRaises(ValueError):
                        recovery.storage_wait_child(q, [], output, state, 'power03', run, 'n1_power', lock)
                    self.assertEqual(len(calls), 1)
                    sleep.assert_not_called()

    def test_initial_mkdir_enospc_can_wait(self):self.scenario('recover')
    def test_started_stage_never_retried(self):self.scenario('stage_exists')
    def test_existing_lock_never_cleared(self):self.scenario('lock_exists')
    def test_unrelated_failure_never_retried(self):self.scenario('other_failure')
    def test_pinned_digests_are_full_sha256(self):
        for value in (recovery.STATE_SHA, recovery.REQUEST_SHA):
            self.assertRegex(value, r'^[0-9a-f]{64}$')


if __name__ == '__main__':unittest.main()
