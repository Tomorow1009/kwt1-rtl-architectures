"""Reject wrong window, hierarchy, residence counts and toggles before PT."""
import unittest
from native_saif_probe import parse_small_saif

class SaifTests(unittest.TestCase):
    def test_actual_vcs_region_format_preserves_combined_unknown(self):
        text='''/* This file was generated with saif_region command flow. */
(SAIFILE (PROGRAM_NAME "VCS Q-2020.03-SP2-6_Full64") (TIMESCALE 1 fs)
(DURATION 60000000.00) (INSTANCE tb_saif (INSTANCE dut (NET
(probe (T0 30000000)(T1 10000000)(TX 20000000)(TC 2)(IG 0))
(toggle (T0 40000000)(T1 20000000)(TX 0)(TC 4)(IG 0))))))'''
        result=parse_small_saif(text)
        self.assertEqual(result['unknown_representation'],'VCS_combined_TX_X_or_Z')
        self.assertFalse(result['X_and_Z_separately_measured'])
        self.assertNotIn('TZ',result['signals']['probe']['counts'])
        for before,after in [('60000000.00','60000000.01'),('TX 20000000','TX 10000000'),
                             ('VCS Q-','unknown Q-')]:
            with self.assertRaises(ValueError):parse_small_saif(text.replace(before,after))

    def test_window_dwell_and_toggles(self):
        text='(SAIFILE (TIMESCALE 1 ps) (DURATION 60000) (INSTANCE tb_saif (INSTANCE dut (PORT (probe (T0 30000)(T1 10000)(TX 10000)(TZ 10000)(TC 3)) (toggle (T0 40000)(T1 20000)(TX 0)(TZ 0)(TC 4))))))'
        self.assertEqual(parse_small_saif(text)['duration_ns'],60)
        for before,after in [('DURATION 60000','DURATION 60001'),('TZ 10000','TZ 9999'),
                             ('TC 4','TC 5'),('INSTANCE dut','INSTANCE wrong'),('TIMESCALE 1 ps','TIMESCALE 1 ns')]:
            with self.assertRaises(ValueError):parse_small_saif(text.replace(before,after))
        for bad in (text[:-1],text+text,'binary-output-not-saif'):
            with self.assertRaises(ValueError):parse_small_saif(bad)

if __name__=='__main__':unittest.main()
