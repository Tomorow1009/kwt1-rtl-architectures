"""Actual DC decorated-net/PIN format must never be reported as clean."""
import unittest
import c32_drc_audit as drc
from test_n1_drc_audit import REPORT


class DecoratedConstraints(unittest.TestCase):
    def test_decorated_net_and_pin_subrecords(self):
        report='''max_transition
Net Required Actual Slack
core/n9916 (dont_touch)
 1.35 1.37 -0.02 (VIOLATED)
 PIN : core/U25153/A1
 1.35 1.37 -0.02 (VIOLATED)
 PIN : core/U25167/A1
 1.35 1.37 -0.02 (VIOLATED)
core/n9950 (dont_touch)
 1.35 1.36 -0.01 (VIOLATED)
'''
        r=drc.constraints_inventory(report)
        self.assertFalse(r['explicit_no_violations'])
        self.assertTrue(r['extraction_complete'])
        self.assertEqual(r['violation_record_count'],4)
        self.assertEqual(r['query_targets'],['core/n9916','core/n9950'])
        self.assertEqual(r['violations'][1]['target'],'core/U25153/A1')

    def test_old_inline_and_plain_wrapped_reports(self):
        r=drc.constraints_inventory(REPORT)
        self.assertEqual(r['violation_record_count'],5)
        self.assertEqual(r['unique_query_target_count'],3)
        self.assertTrue(r['extraction_complete'])
        self.assertFalse(r['explicit_no_violations'])

    def test_unknown_decorators_and_truncated_rows_stay_unresolved(self):
        for header in ('core/n1 (unknown_flag)','PIN : core/U1/A extra','core/n1 (dont_touch)\n'):
            with self.subTest(header=header):
                r=drc.constraints_inventory('max_transition\n'+header+'\n 1.35 1.37 -0.02 (VIOLATED)\n')
                self.assertFalse(r['explicit_no_violations'])
                self.assertFalse(r['extraction_complete'])
        with self.assertRaises(ValueError):
            drc.constraints_inventory(drc.NO_VIOLATIONS+'\nmax_transition\ncore/n1 (dont_touch)\n 1.35 1.37 -0.02 (VIOLATED)')


if __name__=='__main__':unittest.main()
