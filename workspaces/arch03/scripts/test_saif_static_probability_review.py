import unittest
import saif_static_probability_review as review


class OneOptionOnly(unittest.TestCase):
    def test_original_source_and_constraints_unchanged(self):
        source = 'read_verilog {original.v}\nread_sdc {original.sdc}\n    read_saif -strip_path top {original.saif}\nupdate_power\n'
        changed = review.transform(source)
        before, after = source.split('    read_saif', 1)
        self.assertTrue(changed.startswith(before))
        self.assertTrue(changed.endswith('    read_saif'+after))
        self.assertEqual(changed.count('read_saif '), 1)
        self.assertIn('set_app_var '+review.SETTING+' true', changed)
        self.assertNotIn('set_switching_activity', changed)
        self.assertNotIn('set_case_analysis', changed)

    def test_rejects_other_activity_or_existing_override(self):
        for source in ('read_vcd original.vcd\n', 'read_saif a\nread_saif b\n',
                       review.SETTING+' true\nread_saif a\n'):
            with self.assertRaises(ValueError):review.transform(source)


if __name__ == '__main__':unittest.main()
