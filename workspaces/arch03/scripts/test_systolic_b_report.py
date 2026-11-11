"""Missing/unequal-window power and immutable evidence export checks."""
from decimal import Decimal
import json
from pathlib import Path
import tempfile
import unittest
import systolic_b_report as report


class ReportTests(unittest.TestCase):
    def rows(self):
        # Six short 20mW tasks, six three-times-longer 80mW tasks:
        # mean power is 50mW, but complete-window weighted power is 65mW.
        rows=[]
        for i,name in enumerate(report.LAYERS):
            cycles=10000 if i<6 else 30000
            duration=Decimal(cycles)*Decimal('6.666666')
            power=Decimal('.02') if i<6 else Decimal('.08')
            rows.append(dict(case=name,cycles=cycles,duration_ns=str(duration),
                activity={'fixture':True},raw_average_power_w=str(power),
                raw_energy_j=str(power*duration*Decimal('1e-9'))))
        return rows

    def test_full_window_weighting_and_partial_power_is_not_zero(self):
        rows=self.rows();result=report.aggregate_rows(rows)
        self.assertEqual(Decimal(result['raw_time_weighted_power_w']),Decimal('.065'))
        self.assertEqual(Decimal(result['raw_arithmetic_layer_mean_power_w']),Decimal('.05'))
        self.assertEqual(result['nominal_150MHz_tasks_per_second'],7500)
        self.assertEqual(result['nominal_150MHz_MMAC_per_second'],12165.12)
        rows[-1]['raw_energy_j']=None;rows[-1]['raw_average_power_w']=None
        result=report.aggregate_rows(rows)
        self.assertEqual(result['power_layers'],11)
        self.assertIsNone(result['raw_energy_per_task_j'])
        self.assertIsNone(result['raw_time_weighted_power_w'])
        rows[-1]['case']=rows[0]['case']
        with self.assertRaisesRegex(ValueError,'layer set'):report.aggregate_rows(rows)

    def test_stage_rechecks_actual_artifact_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            session=Path(directory);run=session/'systolic_b_synth';run.mkdir()
            artifact=run/'mapped.v';artifact.write_text('original frozen netlist')
            summary=run/'summary.json'
            summary.write_text(json.dumps({'artifacts':{'mapped.v':report.sha(artifact)}}))
            ref=dict(run=str(run),sha256=report.sha(summary))
            (session/'state.json').write_text(json.dumps({'stages':{'systolic_b_synth':
                {'status':'passed','summary_sha256':ref['sha256']}}}))
            report.stage(ref,'systolic_b_synth')
            artifact.write_text('different netlist with unchanged receipt')
            with self.assertRaisesRegex(ValueError,'artifact'):report.stage(ref,'systolic_b_synth')


if __name__=='__main__':unittest.main()
