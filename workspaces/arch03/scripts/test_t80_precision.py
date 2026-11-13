"""Refuse wrong regression scopes and retain the shared-lock failure semantics."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import t80_precision as numeric
import t80_precision_join as join
import t80_precision_stage as stage
import t80_finish_queue as queue


class PrecisionTests(unittest.TestCase):
    def test_full100_and_old_path_are_rejected(self):
        for schema, count in [('arch03-n1-batch-v4', 240), ('arch03-t80-first20-batch-v4', 1200)]:
            with self.assertRaisesRegex(ValueError, 'ASIC240 is incomplete'):
                join.audit_batch('.', dict(schema=schema, asic_cpu_verified=True, tasks=count))

    def test_software_only_cannot_establish_rtl_precision(self):
        with self.assertRaisesRegex(ValueError, 'own T80 ASIC240'):
            join.audit_precision(dict(source_mode=numeric.SOURCE_MODE, archive_sha256='a'*64),
                                 dict(integer_bit_exact=False))

    def test_only20_software_tasks_are_permitted(self):
        for samples in (1, 100):
            with self.assertRaisesRegex(ValueError, 'first20'):
                numeric._audit('absent', 'a'*64, 'absent', 'absent', samples)

    def test_failure_releases_own_lock_preserves_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            batch = root/'old/t80_batch20'
            batch.mkdir(parents=True)
            stage.common.save(batch/'summary.json', {'status': 'passed'})
            digest = stage.common.sha(batch/'summary.json')
            stage.common.save(batch.parent/'state.json', {'stages': {'t80_batch20':
                {'status': 'passed', 'summary_sha256': digest}}})
            bundle = root/'bundle'
            (bundle/'runs').mkdir(parents=True)
            session = bundle/'runs/new'
            cfg = {'server_root': str(root)}
            with patch.object(stage.common, 'ROOT', bundle), patch.object(stage.common, 'ACTIVE_CHILD', None), patch.object(stage.common, 'LOCK', None):
                with patch.object(stage.numeric, '_audit', side_effect=ValueError('numerical failure')):
                    with self.assertRaisesRegex(ValueError, 'numerical failure'):
                        stage.execute(cfg, session, 'a', 'b', 'c', batch, digest, {})
            record = json.loads((session/'state.json').read_text())['stages']['t80_precision']
            self.assertEqual(record['status'], 'failed')
            self.assertNotIn('summary_sha256', record)
            self.assertFalse((root/'.arch02_team_lock').exists())
            self.assertTrue((batch/'summary.json').exists())

    def test_observer_refuses_replaced_batch_and_full100(self):
        with tempfile.TemporaryDirectory() as temp:
            run = Path(temp)/'session/t80_batch20'
            run.mkdir(parents=True)
            request = dict(batch_run=str(run), batch_pid=123, batch_started='original')
            record = dict(run=str(run), pid=999, started='original', status='running')
            stage.common.save(run.parent/'state.json', {'stages': {'t80_batch20': record}})
            with self.assertRaisesRegex(ValueError, 'identity changed'):
                queue.observe_batch(request)
            stage.common.save(run/'summary.json', dict(schema='arch03-t80-first20-batch-v4',
                tasks=1200, checked_outputs=30412800, checked_totals=30412800, failed=0))
            record.update(pid=123, status='passed', summary_sha256=stage.common.sha(run/'summary.json'))
            stage.common.save(run.parent/'state.json', {'stages': {'t80_batch20': record}})
            with self.assertRaisesRegex(ValueError, 'Wrong T80 batch scope'):
                queue.observe_batch(request)


if __name__ == '__main__':
    unittest.main()
