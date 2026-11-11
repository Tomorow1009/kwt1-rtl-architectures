"""The observed serialization bug and unsafe alternate inputs, not hardware tests."""
import unittest
from icb32_delivery_sdc import restore_clock


class DeliveryClockTests(unittest.TestCase):
    def setUp(self):
        self.line = 'create_clock [get_ports hfextclk] -name hf_clk -period 6.66667 -waveform {0 3.33333}'
        self.other = ('# frozen constraints\nset_case_analysis 0 [get_ports io_pads_jtag_TCK_i_ival]\n'
                      'create_clock [get_ports lfextclk] -name lf_clk -period 66 -waveform {0 33}\n'
                      'set_false_path -from [get_ports lfextclk] -to [get_pins {timer/r[0]/D}]\n')

    def test_restores_period_and_duty_cycle_without_changing_exceptions(self):
        corrected, info = restore_clock(self.other+self.line+'\n', '6.666666000000')
        self.assertEqual(corrected, self.other+self.line.replace('6.66667', '6.666666').replace('3.33333}', '3.333333}')+'\n')
        self.assertEqual(info['original_serialized_period_ns'], '6.66667')
        self.assertEqual(restore_clock(corrected, '6.666666')[0], corrected)
        windows=(self.other+self.line+'\n').replace('\n','\r\n')
        self.assertEqual(restore_clock(windows,'6.666666')[0],corrected.replace('\n','\r\n'))

    def test_rejects_changed_or_ambiguous_clock_instead_of_silently_overwriting(self):
        for text, period in ((self.line, '6.666667'),
                             (self.line.replace('6.66667', '7.0'), '6.666666'),
                             (self.line+'\n'+self.line, '6.666666'),
                             (self.other, '6.666666')):
            with self.subTest(text=text, period=period), self.assertRaises(ValueError):
                restore_clock(text, period)


if __name__ == '__main__':
    unittest.main()
