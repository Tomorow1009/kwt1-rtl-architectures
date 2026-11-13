"""Complete-window energy accounting must survive unequal task durations."""
from decimal import Decimal
import unittest
import t80_report
import t64_report


class TransportPowerAccounting(unittest.TestCase):
    def rows(self):
        result=[]
        for i in range(12):
            cycles=10000 if i<6 else 30000
            power=Decimal('.02') if i<6 else Decimal('.08')
            duration=Decimal(cycles)*Decimal('6.666666')
            result.append(dict(case='layer_%02d'%(i+1),cycles=cycles,duration_ns=str(duration),
                               activity={'fixture':True},raw_average_power_w=str(power),
                               raw_energy_j=str(power*duration*Decimal('1e-9'))))
        return result

    def test_time_weighting_and_missing_measurement_not_zero(self):
        for module in (t80_report,t64_report):
            rows=self.rows();total=module.aggregate_rows(rows)
            self.assertEqual(Decimal(total['raw_time_weighted_power_w']),Decimal('.065'))
            self.assertEqual(Decimal(total['raw_arithmetic_layer_mean_power_w']),Decimal('.05'))
            self.assertEqual(total['nominal_150MHz_tasks_per_second'],7500)
            rows[-1].update(raw_energy_j=None,raw_average_power_w=None)
            partial=module.aggregate_rows(rows)
            self.assertEqual(partial['power_layers'],11)
            self.assertIsNone(partial['raw_time_weighted_power_w'])
            self.assertIsNone(partial['raw_energy_per_task_j'])

    def test_window_and_energy_disagreement_rejected(self):
        for module in (t80_report,t64_report):
            for key,value in (('duration_ns','1'),('raw_energy_j','1'),('raw_energy_j','NaN')):
                rows=self.rows();rows[0][key]=value
                with self.assertRaises(ValueError):module.aggregate_rows(rows)


if __name__=='__main__':unittest.main()
