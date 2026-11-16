"""Negative scope/lifecycle tests; no server connection or source removal."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).with_name('P80_B0_ARCHIVED_BATCH_CLEANUP13_20261116.py')
spec = importlib.util.spec_from_file_location('cleanup13', str(SOURCE))
cleanup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cleanup)


class CleanupGuards(unittest.TestCase):
    def test_allow_only_archived_input_scope(self):
        good = cleanup.RUN_REL+'/cases/sample_000001_layer_01/task_boot/itcm_b00_h0.hex'
        self.assertEqual(cleanup.candidate_name(good), good)
        for bad in ('/etc/passwd', '../'+good, good.replace('systolic-b-v3','mmio8'),
                    good.replace('cases/', 'cases/../'),
                    'T80_Delivery_20261113/input.hex', good.replace('sample_000001','sample_00001')):
            with self.subTest(path=bad), self.assertRaises(ValueError):
                cleanup.candidate_name(bad)
        for suffix in ('.csv', '.npz', '.json', '.log', '.sv', '.v', '.saif', '.vcd', '.ddc'):
            with self.subTest(suffix=suffix), self.assertRaises(ValueError):
                cleanup.candidate_name(good[:-4]+suffix)

    def test_original_queue_and_export_must_finish_and_exit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/'p80_export_review05').mkdir()
            first = dict(source_sha256='46e2a8fb416db99febbc9c2bb6ea09b619b515bb185711c2a3a9782277d11651',
                         status='reports_ready_review_required', finished='fixture', pid=123)
            second = dict(source_sha256='952242ef4a1ea2b9ee5bcde89ec0cd4b4c48f2bd504a55ae8a3f1031a31fee4b',
                          status='facts_joined_manual_conclusion_required', finished='fixture', pid=456)

            def write():
                (root/'p80_final_combined05.json').write_text(json.dumps(first))
                (root/'p80_export_review05/state.json').write_text(json.dumps(second))

            def proc_path(path):
                self.assertTrue(str(path).startswith('/proc/'))
                return root/'fixture_proc'/str(path).split('/')[-1]

            with patch.object(cleanup, 'ROOT', root), patch.object(cleanup, 'Path', proc_path):
                write(); cleanup.stopped()
                for value in ('running', 'failed'):
                    first['status'] = value; write()
                    with self.assertRaises(ValueError): cleanup.stopped()
                first['status'] = 'reports_ready_review_required'
                second['status'] = 'waiting_original_finish'; write()
                with self.assertRaises(ValueError): cleanup.stopped()
                second['status'] = 'facts_joined_manual_conclusion_required'
                second['finished'] = None; write()
                with self.assertRaises(ValueError): cleanup.stopped()
                second['finished'] = 'fixture'
                second['source_sha256'] = '0'*64; write()
                with self.assertRaises(ValueError): cleanup.stopped()
                second['source_sha256'] = '952242ef4a1ea2b9ee5bcde89ec0cd4b4c48f2bd504a55ae8a3f1031a31fee4b'
                write(); (root/'fixture_proc/123').mkdir(parents=True)
                with self.assertRaises(ValueError): cleanup.stopped()


if __name__ == '__main__':
    unittest.main()
