"""Tiny owned fixtures only; never touches a historical waveform or server."""
import gzip
import hashlib
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

import archive_r4_l01 as tool
REAL_UNUSED = tool.unused


class L01ArchiveTests(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).resolve().parents[3]
        self.temporary = tempfile.TemporaryDirectory(dir=str(root/'local_runs'), prefix='l01_archive_test_')
        self.bundles = Path(self.temporary.name)
        self.base = self.bundles/'new_n1_bundle'
        (self.base/'runs').mkdir(parents=True)
        self.source = self.bundles/tool.SOURCE_RELATIVE
        self.source.parent.mkdir(parents=True)
        self.payload = (b'$timescale 1ps $end\n#12345\nb101100 q17\n'*4096)+bytes(range(256))*20
        self.source.write_bytes(self.payload)
        self.summary = self.source.parent/'summary.json'
        self.expected = dict(file='layer_01.vcd', bytes=len(self.payload), sha256=hashlib.sha256(self.payload).hexdigest())
        tool.save(self.summary, dict(status='passed', cases=[dict(case='layer_01', activity=self.expected)]))
        self.summary_sha = tool.digest(self.summary)
        tool.save(self.source.parent.parent/'state.json',
                  dict(stages={'icb32_gate':dict(status='passed', summary_sha256=self.summary_sha)}))
        self.patches = [mock.patch.object(tool, 'SUMMARY_SHA', self.summary_sha),
                        mock.patch.object(tool, '_uid', return_value=self.source.stat().st_uid),
                        mock.patch.object(tool, 'unused'),
                        mock.patch.object(tool.shutil, 'disk_usage', return_value=SimpleNamespace(free=10*1024**3))]
        for patch in self.patches:patch.start()
        self.context = tool.frozen_context(self.base)

    def tearDown(self):
        for patch in reversed(self.patches):patch.stop()
        self.temporary.cleanup()

    def test_roundtrip_retains_original_without_explicit_remove(self):
        run = self.base/'runs/retain'
        result = tool.archive(self.context, run)
        self.assertEqual(result['status'], 'lossless_verified_original_retained')
        self.assertTrue(self.source.exists())
        self.assertEqual(gzip.decompress((run/'layer_01.vcd.gz').read_bytes()), self.payload)
        self.assertEqual(result['restored_sha256'], self.expected['sha256'])
        self.assertEqual(tool.digest(self.summary), self.summary_sha)
        self.assertEqual(result['level'], 6)
        self.assertEqual(result['budget']['sample_bytes'], len(self.payload))
        self.assertFalse((run/'layer_01.vcd.gz.partial').exists())
        self.assertGreaterEqual(tool.unused.call_count, 3)

    def test_remove_only_verified_duplicate_raw(self):
        run = self.base/'runs/remove'
        result = tool.archive(self.context, run, remove=True)
        self.assertFalse(self.source.exists())
        self.assertEqual(result['status'], 'lossless_archived_raw_removed')
        self.assertTrue(result['original_removed'])
        self.assertEqual(gzip.decompress((run/'layer_01.vcd.gz').read_bytes()), self.payload)
        self.assertEqual(tool.digest(self.summary), self.summary_sha)
        self.assertEqual(tool.digest(self.context['state']), self.context['state_sha256'])

    def test_low_preflight_space_never_compresses_or_removes(self):
        run = self.base/'runs/low_space'
        with mock.patch.object(tool.shutil, 'disk_usage', return_value=SimpleNamespace(free=tool.RESERVE_BYTES)):
            with self.assertRaisesRegex(ValueError, 'Insufficient space'):
                tool.archive(self.context, run, remove=True)
        self.assertEqual(self.source.read_bytes(), self.payload)
        self.assertFalse((run/'layer_01.vcd.gz.partial').exists())
        self.assertFalse((run/'layer_01.vcd.gz').exists())
        self.assertFalse(json.loads((run/'receipt.json').read_text())['original_removed'])

    def test_midstream_space_loss_preserves_raw_and_partial(self):
        run = self.base/'runs/midstream'
        checks = [SimpleNamespace(free=10*1024**3), SimpleNamespace(free=tool.RESERVE_BYTES-1)]
        with mock.patch.object(tool.shutil, 'disk_usage', side_effect=checks):
            with self.assertRaisesRegex(ValueError, '2 GiB reserve'):
                tool.archive(self.context, run, remove=True)
        self.assertEqual(self.source.read_bytes(), self.payload)
        self.assertTrue((run/'layer_01.vcd.gz.partial').exists())
        self.assertFalse((run/'layer_01.vcd.gz').exists())

    def test_wrong_hash_never_deletes(self):
        run = self.base/'runs/wrong_hash'
        self.context['expected']['sha256'] = '0'*64
        with self.assertRaisesRegex(ValueError, 'Actual source SHA'):
            tool.archive(self.context, run, remove=True)
        self.assertEqual(self.source.read_bytes(), self.payload)
        self.assertFalse((run/'layer_01.vcd.gz').exists())

    def test_restoration_mismatch_retains_raw_and_partial(self):
        run = self.base/'runs/wrong_restore'
        with mock.patch.object(tool.gzip, 'open', return_value=io.BytesIO(b'not the original stream')):
            with self.assertRaisesRegex(ValueError, 'Complete decompression'):
                tool.archive(self.context, run, remove=True)
        self.assertEqual(self.source.read_bytes(), self.payload)
        self.assertTrue((run/'layer_01.vcd.gz.partial').exists())
        self.assertFalse((run/'layer_01.vcd.gz').exists())

    def test_final_fuser_busy_retains_both_verified_copy_and_raw(self):
        run = self.base/'runs/final_busy'
        tool.unused.side_effect = [None, None, None, ValueError('File in use or fuser check failed')]
        with self.assertRaisesRegex(ValueError, 'File in use'):
            tool.archive(self.context, run, remove=True)
        self.assertEqual(self.source.read_bytes(), self.payload)
        self.assertEqual(gzip.decompress((run/'layer_01.vcd.gz').read_bytes()), self.payload)
        self.assertFalse(json.loads((run/'receipt.json').read_text())['original_removed'])

    def test_fuser_non_one_exit_codes_fail_closed(self):
        for code in (0, 2, 127):
            with mock.patch.object(tool.subprocess, 'run', return_value=SimpleNamespace(returncode=code)):
                with self.assertRaisesRegex(ValueError, 'fuser check failed'): REAL_UNUSED([self.source])
        with mock.patch.object(tool.subprocess, 'run', return_value=SimpleNamespace(returncode=1)):
            REAL_UNUSED([self.source])

    def test_ownership_mismatch_retains_source(self):
        with mock.patch.object(tool, '_uid', return_value=self.source.stat().st_uid+1):
            with self.assertRaisesRegex(ValueError, 'owned regular file'):
                tool.archive(self.context, self.base/'runs/wrong_owner', remove=True)
        self.assertTrue(self.source.exists())

    def test_changed_summary_and_source_fail_closed(self):
        self.source.write_bytes(self.payload+b'changed')
        with self.assertRaisesRegex(ValueError, 'Frozen source changed'):
            tool.archive(self.context, self.base/'runs/changed', remove=True)
        self.assertTrue(self.source.exists())

    def test_existing_output_and_outside_output_refused(self):
        output = self.base/'runs/existing';output.mkdir()
        with self.assertRaisesRegex(ValueError, 'run exists'):
            tool.archive(self.context, output, remove=True)
        with self.assertRaisesRegex(ValueError, 'direct child'):
            tool.archive(self.context, self.bundles/'elsewhere', remove=True)
        self.assertTrue(self.source.exists())

    def test_wrong_source_path_never_deleted(self):
        other = self.source.with_name('layer_02.vcd');other.write_bytes(self.payload)
        self.context['source'] = other
        with self.assertRaisesRegex(ValueError, 'exact pinned R4 L01'):
            tool.archive(self.context, self.base/'runs/wrong_path', remove=True)
        self.assertTrue(other.exists());self.assertTrue(self.source.exists())


if __name__ == '__main__':
    unittest.main()
