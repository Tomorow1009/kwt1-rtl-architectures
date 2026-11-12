"""Repair tool provenance/constraint safeguards; not hardware verification."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import systolic_b_drc_repair as repair
from asic_link import sha


class RepairTests(unittest.TestCase):
    def test_mapped_only_and_original_report_guards(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/'libs').mkdir()
            for name in ('standard.db', 'm128.db', 'm4096.db'):
                (root/'libs'/name).write_text('fixture')
            text = repair.repair_script(root, {'standard_library_member':'standard.db'})
            self.assertEqual([s.strip() for s in text.splitlines() if s.startswith('compile ')],
                             ['compile -incremental_mapping -only_design_rule'])
            self.assertIn('read_ddc repair_seed.ddc', text)
            self.assertIn('source task_mode.sdc', text)
            self.assertIn('Expected four reviewed LF timer', text)
            self.assertIn('!= 220', text)
            self.assertIn('report_constraint -all_violators', text)
            self.assertNotIn('set_max_transition', text)

    def test_copy_rejects_changed_input_and_existing_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); src = root/'source'; dst = root/'copy'
            src.write_bytes(b'original mapped design'); digest = sha(src)
            repair.checked_copy(src, dst, digest)
            self.assertEqual(src.read_bytes(), dst.read_bytes())
            with self.assertRaises(ValueError):repair.checked_copy(src, dst, digest)
            src.write_bytes(b'changed')
            with self.assertRaises(ValueError):repair.checked_copy(src, root/'new', digest)
            self.assertFalse((root/'new').exists())

    def test_changed_constraints_abort_before_dc_or_copy(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); original=root/'prior'; run=root/'new'
            original.mkdir(); run.mkdir(); (original/'task_mode.sdc').write_text('relaxed constraints')
            with patch('systolic_b_gate.verify_synthesis', return_value=({}, {})):
                with self.assertRaisesRegex(ValueError,'exact original task constraints'):
                    repair.repair({},run,original,'0'*64,lambda *a:self.fail('must not launch DC'))
            self.assertEqual(list(run.iterdir()),[])


if __name__=='__main__':unittest.main()
