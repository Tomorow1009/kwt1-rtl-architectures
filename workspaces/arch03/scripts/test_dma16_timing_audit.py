import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import dma16_timing_audit as a
from test_dma16_power import fake_databases


class TimingAuditTests(unittest.TestCase):
    def test_inventory_rejects_missing_duplicate_and_malformed_evidence(self):
        text = 'threshold\t1000\ncount\t2\nnet\ttop/clk\nnet\ttop/reset_n\n'
        self.assertEqual(a.parse_high_fanout(text)['nets'], ['top/clk', 'top/reset_n'])
        for bad in (text.replace('1000', '999'), text.replace('count\t2', 'count\t3'),
                    text.replace('top/reset_n', 'top/clk'), text+'garbage\n',
                    text.replace('top/reset_n', ''), text.replace('count\t2', 'count\t-1')):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                a.parse_high_fanout(bad)
        self.assertEqual(a.parse_high_fanout('threshold\t1000\ncount\t0\n')['count'], 0)

    def test_query_preserves_original_probe_and_never_writes_mapped_design(self):
        with tempfile.TemporaryDirectory() as directory:
            run = Path(directory); fake_databases(run)
            text = a.script(run)
            self.assertIn('all_high_fanout -nets -threshold 1000', text)
            self.assertIn('read_ddc', text)
            self.assertIn(a.PROBE_MARKER, text)
            self.assertNotIn('compile_ultra', text)
            self.assertNotIn('write_file', text)
        with patch.object(a, 'probe_script', return_value='changed'):
            with self.assertRaises(ValueError): a.script(Path('.'))


if __name__ == '__main__':
    unittest.main()
