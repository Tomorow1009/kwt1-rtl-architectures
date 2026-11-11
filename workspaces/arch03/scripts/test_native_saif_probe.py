"""Reject wrong window, hierarchy, residence counts and toggles before PT."""
import unittest
from native_saif_probe import parse_small_saif

class SaifTests(unittest.TestCase):
    def test_window_dwell_and_toggles(self):
        text='(SAIFILE (TIMESCALE 1 ps) (DURATION 60000) (INSTANCE tb_saif (INSTANCE dut (PORT (probe (T0 30000)(T1 10000)(TX 10000)(TZ 10000)(TC 3)) (toggle (T0 40000)(T1 20000)(TX 0)(TZ 0)(TC 4))))))'
        self.assertEqual(parse_small_saif(text)['duration_ns'],60)
        for before,after in [('DURATION 60000','DURATION 60001'),('TZ 10000','TZ 9999'),
                             ('TC 4','TC 5'),('INSTANCE dut','INSTANCE wrong'),('TIMESCALE 1 ps','TIMESCALE 1 ns')]:
            with self.assertRaises(ValueError):parse_small_saif(text.replace(before,after))
        for bad in (text[:-1],text+text,'binary-output-not-saif'):
            with self.assertRaises(ValueError):parse_small_saif(bad)

if __name__=='__main__':unittest.main()
