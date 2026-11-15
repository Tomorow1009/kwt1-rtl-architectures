"""Refuse wrong regression scopes and retain the shared-lock failure semantics."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import t64_precision as numeric
import t64_precision_join as join
import t64_precision_stage as stage
import t64_finish_queue as queue


class PrecisionTests(unittest.TestCase):
    def test_four_row_batch_reaches_task_validation_and_five_row_rejected(self):
        # A complete header must reach the independent per-task inventory.
        # Rejecting every valid four-row run is not a successful safety check.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory);run = root/'run';run.mkdir()
            fw = root/'fw';fw.mkdir();stage.common.save(fw/'manifest.json', {})
            identity = dict(dataset_inventory_sha256=join.data.DATA100_INVENTORY_SHA,
                            samples=20,tasks=240,row_lanes=4,compile_count=1,
                            firmware_manifest_sha256=join.sha(fw/'manifest.json'),dataset=str(root/'data'))
            contract = dict(schema='arch03-t64-asic-build-v4',diagnostic=None,row_lanes=4,
                            layout_id=0x00100004,clock_period_ns='6.666666',firmware=str(fw))
            report = dict(schema='arch03-t64-first20-batch-v4',asic_cpu_verified=True,tasks=240,
                          checked_outputs=6082560,checked_totals=6082560,failed=0,shift=10,
                          numeric_format_id=0x000e0c20)
            for identity_rows, contract_rows in ((4,4),(5,4),(4,5)):
                identity['row_lanes']=identity_rows;contract['row_lanes']=contract_rows
                stage.common.save(run/'t64_build_contract.json',contract)
                identity['build_contract_sha256']=join.sha(run/'t64_build_contract.json')
                stage.common.save(run/'batch_identity.json',identity)
                report['batch_identity_sha256']=join.sha(run/'batch_identity.json')
                with patch.object(join.soc,'verify_frozen'),patch.object(join.data,'index_dataset',
                        side_effect=RuntimeError('task inventory reached')) as inventory:
                    if identity_rows==contract_rows==4:
                        with self.assertRaisesRegex(RuntimeError,'task inventory reached'):
                            join.audit_batch(run,report)
                        inventory.assert_called_once_with(root/'data')
                    else:
                        with self.assertRaisesRegex(ValueError,'identity changed|Wrong T64 build'):
                            join.audit_batch(run,report)
                        inventory.assert_not_called()

    def test_prior_contention_requires_identical_hardware_and_actual_cpu(self):
        with tempfile.TemporaryDirectory() as temp:
            old = Path(temp)/'old'
            new = Path(temp)/'new'
            run = old/'runs/contention/t64_contention'
            run.mkdir(parents=True)
            new.mkdir()
            observer = 'workspaces/arch03/tb/arch03_t64_sequence_monitor.svh'
            for root, version in ((old, 'old observer'), (new, 'fixed observer')):
                (root/observer).parent.mkdir(parents=True)
                (root/observer).write_text(version)
                (root/'hardware.sv').write_text('frozen hardware')
                stage.common.save(root/'manifest.json', {'files':
                    {name: stage.common.sha(root/name) for name in (observer, 'hardware.sv')}})
            stage.common.save(run/'summary.json', {'contention_verified': True, 'cpu_executed': True})
            digest = stage.common.sha(run/'summary.json')
            stage.common.save(run.parent/'state.json', {'stages': {'t64_contention':
                {'status': 'passed', 'summary_sha256': digest}}})
            request = {'prior_contention': {'run': str(run), 'sha256': digest}}
            with patch.object(queue.common, 'ROOT', new):
                self.assertEqual(queue.prior_contention(request)['sha256'], digest)
                manifest = json.loads((new/'manifest.json').read_text())
                manifest['files']['hardware.sv'] = '0'*64
                stage.common.save(new/'manifest.json', manifest)
                with self.assertRaisesRegex(ValueError, 'hardware, firmware or tools changed'):
                    queue.prior_contention(request)

    def test_full100_and_old_path_are_rejected(self):
        for schema, count in [('arch03-n1-batch-v4', 240), ('arch03-t64-first20-batch-v4', 1200)]:
            with self.assertRaisesRegex(ValueError, 'ASIC240 is incomplete'):
                join.audit_batch('.', dict(schema=schema, asic_cpu_verified=True, tasks=count))

    def test_software_only_cannot_establish_rtl_precision(self):
        with self.assertRaisesRegex(ValueError, 'own T64 ASIC240'):
            join.audit_precision(dict(source_mode=numeric.SOURCE_MODE, archive_sha256='a'*64),
                                 dict(integer_bit_exact=False))

    def test_only20_software_tasks_are_permitted(self):
        for samples in (1, 100):
            with self.assertRaisesRegex(ValueError, 'first20'):
                numeric._audit('absent', 'a'*64, 'absent', 'absent', samples)

    def test_failure_releases_own_lock_preserves_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            batch = root/'old/t64_batch20'
            batch.mkdir(parents=True)
            stage.common.save(batch/'summary.json', {'status': 'passed'})
            digest = stage.common.sha(batch/'summary.json')
            stage.common.save(batch.parent/'state.json', {'stages': {'t64_batch20':
                {'status': 'passed', 'summary_sha256': digest}}})
            bundle = root/'bundle'
            (bundle/'runs').mkdir(parents=True)
            session = bundle/'runs/new'
            cfg = {'server_root': str(root)}
            with patch.object(stage.common, 'ROOT', bundle), patch.object(stage.common, 'ACTIVE_CHILD', None), patch.object(stage.common, 'LOCK', None):
                with patch.object(stage.numeric, '_audit', side_effect=ValueError('numerical failure')):
                    with self.assertRaisesRegex(ValueError, 'numerical failure'):
                        stage.execute(cfg, session, 'a', 'b', 'c', batch, digest, {})
            record = json.loads((session/'state.json').read_text())['stages']['t64_precision']
            self.assertEqual(record['status'], 'failed')
            self.assertNotIn('summary_sha256', record)
            self.assertFalse((root/'.arch02_team_lock').exists())
            self.assertTrue((batch/'summary.json').exists())

    def test_observer_refuses_replaced_batch_and_full100(self):
        with tempfile.TemporaryDirectory() as temp:
            run = Path(temp)/'session/t64_batch20'
            run.mkdir(parents=True)
            request = dict(batch_run=str(run), batch_pid=123, batch_started='original')
            record = dict(run=str(run), pid=999, started='original', status='running')
            stage.common.save(run.parent/'state.json', {'stages': {'t64_batch20': record}})
            with self.assertRaisesRegex(ValueError, 'identity changed'):
                queue.observe_batch(request)
            stage.common.save(run/'summary.json', dict(schema='arch03-t64-first20-batch-v4',
                tasks=1200, checked_outputs=30412800, checked_totals=30412800, failed=0))
            record.update(pid=123, status='passed', summary_sha256=stage.common.sha(run/'summary.json'))
            stage.common.save(run.parent/'state.json', {'stages': {'t64_batch20': record}})
            with self.assertRaisesRegex(ValueError, 'Wrong T64 batch scope'):
                queue.observe_batch(request)


if __name__ == '__main__':
    unittest.main()
