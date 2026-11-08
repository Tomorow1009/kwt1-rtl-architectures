import unittest
from timing_contract import CLOCK_PERIOD_NS, validate_period


class TimingTests(unittest.TestCase):
    def test_exact_target(self):
        self.assertEqual(validate_period(CLOCK_PERIOD_NS), 6.666666)

    def test_old_and_invalid_periods_rejected(self):
        for value in ('6.667', '6.666666667', 0, -1, 'NaN', 'Infinity', 'bad'):
            with self.assertRaises(ValueError):
                validate_period(value)


if __name__ == '__main__':
    unittest.main()
