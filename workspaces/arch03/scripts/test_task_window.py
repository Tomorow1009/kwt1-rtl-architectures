import unittest
from server_run import read_task_window


class WindowTests(unittest.TestCase):
    line=('ARCH03_TASK_WINDOW start_cycle=10 end_cycle=110 cycles=100 '
          'start_ns=66.666660 end_ns=733.333260 period_ns=6.666666 '
          'input_words=23488 output_words=25344')

    def test_consistent_measured_window(self):
        self.assertEqual(read_task_window(self.line)['cycles'],100)

    def test_missing_duplicate_and_partial(self):
        for value in ('',self.line+'\n'+self.line,self.line.replace('25344','25343')):
            with self.assertRaises(ValueError):read_task_window(value)

    def test_wrong_period_and_wrong_duration(self):
        for value in (self.line.replace('period_ns=6.666666','period_ns=6.667'),
                      self.line.replace('733.333260','733.333270'),
                      self.line.replace('cycles=100','cycles=101')):
            with self.assertRaises(ValueError):read_task_window(value)


if __name__=='__main__':unittest.main()
