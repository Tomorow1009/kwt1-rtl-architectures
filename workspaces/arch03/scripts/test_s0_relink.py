import inspect
import unittest
import s0_relink as r


class RelinkGuards(unittest.TestCase):
    def test_only_observed_library_error_inventory_can_reuse_blocks(self):
        line="Error: 'standard.db:standard' doesn't specify a unique library\n"
        end='Error: ARCH03_SYNTH_ABORT Unmapped/ambiguous leaf DRNQV2_12TR40\n'
        r.validate_errors(line*1578+end)
        for bad in (line*1577+end,line*1578+end+'Error: other\n',line*1578+end.replace('DRNQV2','OTHER')):
            with self.assertRaises(ValueError):r.validate_errors(bad)
        self.assertEqual(len(r.STATE),64)

    def test_relink_dispatch_only_regenerates_final_reports(self):
        source=inspect.getsource(r.execute)
        self.assertIn('mapping.finalize(',source)
        self.assertNotIn('mapping.execute(',source)
        self.assertNotIn('compile ',source)
        self.assertIn('reusable(',source)
        self.assertIn('mapping.checked_file(name,want)',source)


if __name__=='__main__':unittest.main()
