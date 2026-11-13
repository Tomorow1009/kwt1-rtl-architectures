"""Failure injection after an EDA child is accepted, without launching EDA."""
import errno
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import t64_finish_queue
import t80_finish_queue


class QueueFailure(unittest.TestCase):
    def exercise(self, module, fail_save=False, exit_code=0):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);queue=root/'queue';queue.mkdir()
            run=root/'child'/'stage';state=dict(completed=[])
            child=Mock(pid=12345)
            ref=dict(run=str(run),sha256='a'*64)
            def save(path, current):
                if fail_save and current['status']=='running':
                    raise OSError(errno.ENOSPC, 'injected full shared disk')
            with patch.object(module.subprocess,'Popen',return_value=child), \
                 patch.object(module,'atomic_save',side_effect=save), \
                 patch.object(module.ProcessLedger,'drain',return_value=(exit_code,[])) as drain, \
                 patch.object(module,'completed',return_value=ref) as completed:
                if fail_save:
                    with self.assertRaises(OSError) as error:
                        module.run_child(['fake'],run,'stage',queue,state,root/'lock')
                    self.assertEqual(error.exception.errno,errno.ENOSPC)
                elif exit_code:
                    with self.assertRaises(ValueError):
                        module.run_child(['fake'],run,'stage',queue,state,root/'lock')
                else:
                    self.assertEqual(module.run_child(['fake'],run,'stage',queue,state,root/'lock'),ref)
                drain.assert_called_once_with(None,child)
                self.assertIsNone(state['child_pid'])
                if fail_save or exit_code:
                    completed.assert_not_called()
                    self.assertEqual(state['completed'],[])
                else:
                    self.assertEqual(state['completed'],[dict(stage='stage',reference=ref)])

    def test_state_write_failure_still_reaps_child(self):
        for module in (t80_finish_queue,t64_finish_queue):
            with self.subTest(module=module.__name__):self.exercise(module,fail_save=True)

    def test_failed_child_is_not_recorded_passed(self):
        for module in (t80_finish_queue,t64_finish_queue):
            with self.subTest(module=module.__name__):self.exercise(module,exit_code=1)

    def test_success_records_only_reaped_child(self):
        for module in (t80_finish_queue,t64_finish_queue):
            with self.subTest(module=module.__name__):self.exercise(module)


if __name__=='__main__':unittest.main()
