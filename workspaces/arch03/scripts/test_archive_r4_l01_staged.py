"""Small owned fixtures with mocked separate devices; no server operations."""
import gzip
import hashlib
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

import archive_r4_l01_staged as tool
frozen = tool.frozen


class StagedTests(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).resolve().parents[3]
        self.directory = tempfile.TemporaryDirectory(dir=str(root / 'local_runs'), prefix='r4_staged_test_')
        self.root = Path(self.directory.name)
        self.bundles = self.root / 'bundles'
        self.base = self.bundles / 'new_n1_bundle'
        (self.base / 'runs').mkdir(parents=True)
        self.tmp_parent = self.root / 'tmp';self.tmp_parent.mkdir()
        self.tmp = self.tmp_parent / 's4_21usr-r4-l01-fixture01'
        self.output = self.base / 'runs' / tool.OUTPUT_NAME
        self.source = self.bundles / frozen.SOURCE_RELATIVE
        self.source.parent.mkdir(parents=True)
        self.payload = (b'$timescale 1ps $end\n#1234\nb101010 data\n' * 4096) + bytes(range(256)) * 20
        self.source.write_bytes(self.payload)
        self.expected = dict(file='layer_01.vcd', bytes=len(self.payload),
                             sha256=hashlib.sha256(self.payload).hexdigest())
        self.summary = self.source.parent / 'summary.json'
        frozen.save(self.summary, dict(status='passed', cases=[dict(case='layer_01', activity=self.expected)]))
        self.summary_sha = frozen.digest(self.summary)
        frozen.save(self.source.parent.parent / 'state.json',
                    dict(stages={'icb32_gate': dict(status='passed', summary_sha256=self.summary_sha)}))
        self.original_stat = Path.stat
        # Windows does not expose POSIX mode700/st_blocks. Tests emulate only
        # those platform interfaces; actual compression/files/receipts are real.
        def info(path, *args, **kwargs):
            actual = self.original_stat(path, *args, **kwargs)
            if path == self.tmp or path == self.output:
                values = {key: getattr(actual, key) for key in dir(actual) if key.startswith('st_')}
                values['st_mode'] = (actual.st_mode & ~0o777) | 0o700
                return SimpleNamespace(**values)
            return actual
        self.patches = [mock.patch.object(frozen, 'SUMMARY_SHA', self.summary_sha),
            mock.patch.object(frozen, '_uid', return_value=self.source.stat().st_uid),
            mock.patch.object(frozen, 'unused'), mock.patch.object(tool, 'account', return_value='s4_21usr'),
            mock.patch.object(tool, 'TMP_PARENT', self.tmp_parent),
            mock.patch.object(tool, 'device', side_effect=lambda p: 2 if self.tmp_parent in Path(p).parents else 1),
            mock.patch.object(tool, 'allocated_bytes', return_value=len(self.payload)),
            mock.patch.object(tool.shutil, 'disk_usage', return_value=SimpleNamespace(free=20 * 1024**3)),
            mock.patch.object(Path, 'stat', info)]
        for item in self.patches:item.start()
        self.context = frozen.frozen_context(self.base)

    def tearDown(self):
        for item in reversed(self.patches):item.stop()
        self.directory.cleanup()

    def run_archive(self, remove=True):
        return tool.archive(self.context, self.output, self.tmp, remove)

    def receipt(self):
        return json.loads((self.tmp / 'receipt.json').read_text(encoding='utf8'))

    def assert_tmp_complete(self):
        self.assertEqual(gzip.decompress((self.tmp / 'layer_01.vcd.gz').read_bytes()), self.payload)

    def test_roundtrip_remove_only_after_full_proof_and_return(self):
        record = self.run_archive()
        self.assertFalse(self.source.exists())
        self.assertEqual(record['status'], 'completed_returned_archive')
        self.assertTrue(record['original_removed'])
        self.assertTrue(record['complete_tmp_archive_verified'])
        self.assertTrue(record['final_return_verified'])
        self.assertFalse((self.tmp / 'layer_01.vcd.gz').exists())
        self.assertEqual(gzip.decompress((self.output / 'layer_01.vcd.gz').read_bytes()), self.payload)
        self.assertEqual(frozen.digest(self.summary), self.summary_sha)
        self.assertEqual(frozen.digest(self.context['state']), self.context['state_sha256'])

    def test_no_remove_flag_retains_raw(self):
        result = self.run_archive(False)
        self.assertEqual(result['status'], 'completed_returned_archive')
        self.assertFalse(result['original_removed'])
        self.assertEqual(self.source.read_bytes(), self.payload)

    def test_same_filesystem_refused(self):
        with mock.patch.object(tool, 'device', return_value=1):
            with self.assertRaisesRegex(ValueError, 'filesystem must differ'):self.run_archive()
        self.assertEqual(self.source.read_bytes(), self.payload)

    def test_wrong_tmp_name_refused(self):
        with self.assertRaisesRegex(ValueError, 'unique /tmp'):
            tool.archive(self.context, self.output, self.tmp_parent / 'other-user-dir', True)
        self.assertTrue(self.source.exists())

    def test_existing_tmp_refused(self):
        self.tmp.mkdir()
        with self.assertRaisesRegex(ValueError, 'directory exists'):self.run_archive()
        self.assertTrue(self.source.exists())

    def test_low_tmp_budget_preserves_raw(self):
        with mock.patch.object(tool.shutil, 'disk_usage', return_value=SimpleNamespace(free=frozen.RESERVE_BYTES)):
            with self.assertRaisesRegex(ValueError, 'temporary filesystem budget'):self.run_archive()
        self.assertTrue(self.source.exists())
        self.assertFalse(self.receipt()['complete_tmp_archive_verified'])

    def test_wrong_source_hash_retains_raw_and_partial(self):
        self.context['expected']['sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'source stream SHA'):self.run_archive()
        self.assertEqual(self.source.read_bytes(), self.payload)
        self.assertTrue((self.tmp / 'layer_01.vcd.gz.partial').exists())

    def test_restore_failure_never_removes_raw(self):
        with mock.patch.object(tool.gzip, 'open', return_value=io.BytesIO(b'wrong restored data')):
            with self.assertRaisesRegex(ValueError, 'decompression SHA'):self.run_archive()
        self.assertEqual(self.source.read_bytes(), self.payload)
        self.assertFalse(self.receipt()['complete_tmp_archive_verified'])

    def test_insufficient_reclaim_budget_retains_both(self):
        with mock.patch.object(tool, 'return_budget', return_value=dict(free_bytes=0, required_bytes=10**12)):
            result = self.run_archive()
        self.assertEqual(result['status'], 'verified_tmp_and_raw_retained_insufficient_return_budget')
        self.assertTrue(self.source.exists());self.assert_tmp_complete()

    def test_space_loss_after_raw_removal_retains_complete_tmp_then_resumes(self):
        ready = dict(free_bytes=20 * 1024**3, required_bytes=2 * 1024**3)
        low = dict(free_bytes=1, required_bytes=2 * 1024**3)
        with mock.patch.object(tool, 'return_budget', side_effect=[ready, low]):
            result = self.run_archive()
        self.assertEqual(result['status'], 'verified_tmp_waiting_for_return_space')
        self.assertFalse(self.source.exists());self.assert_tmp_complete()
        result = tool.resume_copy(self.base, self.tmp)
        self.assertEqual(result['status'], 'completed_returned_archive')
        self.assertEqual(gzip.decompress((self.output / 'layer_01.vcd.gz').read_bytes()), self.payload)

    def test_interrupted_return_preserves_only_complete_tmp_and_failed_partial(self):
        real_guard = frozen.chunk_guard
        def guard(path, incoming=0):
            if Path(path) == self.output:raise OSError('synthetic storage2 ENOSPC')
            return real_guard(path, incoming)
        with mock.patch.object(frozen, 'chunk_guard', side_effect=guard):
            with self.assertRaisesRegex(OSError, 'ENOSPC'):self.run_archive()
        self.assertFalse(self.source.exists());self.assert_tmp_complete()
        attempts = list(self.output.glob('*.partial'))
        self.assertEqual(len(attempts), 1)
        tool.resume_copy(self.base, self.tmp)
        self.assertTrue(attempts[0].exists())
        self.assertEqual(gzip.decompress((self.output / 'layer_01.vcd.gz').read_bytes()), self.payload)

    def test_corrupt_complete_tmp_recovery_never_copies(self):
        with mock.patch.object(tool, 'return_budget', return_value=dict(free_bytes=0, required_bytes=10**12)):
            self.run_archive()
        (self.tmp / 'layer_01.vcd.gz').write_bytes(b'corrupt')
        with self.assertRaisesRegex(ValueError, 'temporary gzip changed'):tool.resume_copy(self.base, self.tmp)
        self.assertTrue(self.source.exists())
        self.assertFalse((self.output / 'layer_01.vcd.gz').exists())

    def test_original_metadata_change_refuses_resume(self):
        with mock.patch.object(tool, 'return_budget', return_value=dict(free_bytes=0, required_bytes=10**12)):
            self.run_archive()
        self.summary.write_bytes(self.summary.read_bytes() + b' ')
        with self.assertRaisesRegex(ValueError, 'Wrong pinned R4 summary'):tool.resume_copy(self.base, self.tmp)
        self.assert_tmp_complete();self.assertTrue(self.source.exists())

    def test_busy_original_never_removed(self):
        frozen.unused.side_effect = [None, None, ValueError('File in use')]
        with self.assertRaisesRegex(ValueError, 'File in use'):self.run_archive()
        self.assertTrue(self.source.exists());self.assert_tmp_complete()

    def test_resume_does_not_delete_retained_raw(self):
        with mock.patch.object(tool, 'return_budget', return_value=dict(free_bytes=0, required_bytes=10**12)):
            self.run_archive()
        self.assertTrue(self.source.exists());self.assert_tmp_complete()
        tool.resume_copy(self.base, self.tmp)
        self.assertEqual(self.source.read_bytes(), self.payload)

    def test_crash_after_unlink_reconciles_durable_intent(self):
        ready = dict(free_bytes=20 * 1024**3, required_bytes=2 * 1024**3)
        low = dict(free_bytes=1, required_bytes=2 * 1024**3)
        with mock.patch.object(tool, 'return_budget', side_effect=[ready, low]):self.run_archive()
        record = self.receipt()
        record['original_removed'] = False
        record['status'] = 'verified_tmp_raw_removal_intent'
        frozen.save(self.tmp / 'receipt.json', record)
        result = tool.resume_copy(self.base, self.tmp)
        self.assertTrue(result['source_absence_reconciled_after_durable_removal_intent'])
        self.assertTrue(result['original_removed'])
        self.assertEqual(result['status'], 'completed_returned_archive')

    def test_missing_raw_without_durable_intent_rejected(self):
        with mock.patch.object(tool, 'return_budget', return_value=dict(free_bytes=0, required_bytes=10**12)):
            self.run_archive()
        self.source.unlink()
        with self.assertRaisesRegex(ValueError, 'without this run durable'):tool.resume_copy(self.base, self.tmp)
        self.assert_tmp_complete()

    def test_final_published_but_tmp_cleanup_interrupted(self):
        raised = [False]
        def unused(paths):
            if self.output / 'layer_01.vcd.gz' in paths and not raised[0]:
                raised[0] = True
                raise OSError('synthetic final cleanup interruption')
        frozen.unused.side_effect = unused
        with self.assertRaisesRegex(OSError, 'cleanup interruption'):self.run_archive()
        self.assert_tmp_complete()
        final = self.output / 'layer_01.vcd.gz'
        before = final.read_bytes()
        result = tool.resume_copy(self.base, self.tmp)
        self.assertEqual(result['status'], 'completed_returned_archive')
        self.assertEqual(final.read_bytes(), before)

    def test_final_receipt_after_tmp_unlink_can_be_recovered(self):
        self.run_archive()
        record = self.receipt()
        record['status'] = 'returned_archive_verified_tmp_retained'
        record['temporary_archive_removed'] = False
        frozen.save(self.tmp / 'receipt.json', record)
        result = tool.resume_copy(self.base, self.tmp)
        self.assertTrue(result['completed_receipt_reconciled'])
        self.assertEqual(result['status'], 'completed_returned_archive')


if __name__ == '__main__':
    unittest.main(verbosity=2)
