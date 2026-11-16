import unittest
from decimal import Decimal
import c32_report as report


class C32ReportTests(unittest.TestCase):
    def test_other_hardware_stage_cannot_be_exported_as_c32(self):
        for schema in ('arch03-t80-report-request-v1','arch03-s0-report-request-v1'):
            with self.assertRaisesRegex(ValueError,'explicit C32'):
                report.build({'schema':schema},{})

    def test_power_is_weighted_by_complete_window_not_layer_count(self):
        rows=[]
        for i,name in enumerate(report.LAYERS):
            cycles=100 if i<6 else 200;power=Decimal('0.1' if i<6 else '0.2')
            duration=cycles*Decimal('6.666666')
            rows.append(dict(case=name,cycles=cycles,duration_ns=str(duration),activity={},
                raw_average_power_w=str(power),raw_energy_j=str(power*duration*Decimal('1e-9'))))
        actual=report.aggregate_rows(rows)
        self.assertEqual(Decimal(actual['raw_time_weighted_power_w']),Decimal('0.5')/3)
        self.assertNotEqual(actual['raw_time_weighted_power_w'],actual['raw_arithmetic_layer_mean_power_w'])
        rows[-1]['raw_energy_j']=rows[-1]['raw_average_power_w']=None
        self.assertIsNone(report.aggregate_rows(rows)['raw_time_weighted_power_w'])


if __name__=='__main__':unittest.main()
