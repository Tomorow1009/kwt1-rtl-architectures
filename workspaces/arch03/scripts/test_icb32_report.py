"""Report mixing/aggregation checks; synthetic records are not hardware PASS."""
import copy
import json
import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch
import icb32_report as report


class ReportTests(unittest.TestCase):
    def test_clock_conditions_retain_actual_rounded_power_import(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'mapped.sdc'
            path.write_text('create_clock [get_ports hfextclk] -name hf_clk -period 6.66667 -waveform {0 3.33333}\n')
            summary=dict(metrics=dict(period_ns='6.666666'),artifacts={'mapped.sdc':report.sha(path)})
            values=report.clock_conditions(summary,directory,True)
            self.assertEqual(values['period_ns'],'6.666666')
            self.assertEqual(values['original_sdc_period_ns'],'6.66667')
            self.assertTrue(values['power_imported_original_sdc'])
            path.write_text(path.read_text().replace('6.66667','6.667'))
            with self.assertRaisesRegex(ValueError,'SDC changed'):
                report.clock_conditions(summary,directory,True)

    def test_optional_delivery_does_not_claim_timing_rerun(self):
        self.assertEqual(report.delivery_sdc_evidence(None,{},{}),
                         dict(status='not_imported',timing_rerun=False))

    def test_delivery_receipt_cannot_hide_an_extra_constraint_change(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);srun=root/'synth';out=root/'delivery';srun.mkdir();out.mkdir()
            original='create_clock [get_ports hfextclk] -name hf_clk -period 6.66667 -waveform {0 3.33333}\n'
            (srun/'mapped.sdc').write_bytes(original.encode('ascii'))
            precise,change=report.restore_clock(original,'6.666666')
            target=out/'mapped.precise.sdc';target.write_bytes(precise.encode('ascii'))
            summary=dict(metrics=dict(period_ns='6.666666'),artifacts={
                'mapped.sdc':report.sha(srun/'mapped.sdc'),'mapped.v':'b'*64,'metrics.txt':'c'*64})
            sr=dict(run=str(srun),sha256='a'*64)
            receipt=dict(schema='icb32-delivery-sdc-v1',synthesis_summary_sha256=sr['sha256'],
                inputs_sha256=summary['artifacts'],delivery_sdc_sha256=report.sha(target),clock_change=change,
                other_constraints_unchanged=True,netlist_modified=False,historical_power_sdc_modified=False,
                timing_rerun=False,timing_verified=False)
            rp=out/'receipt.json';rp.write_text(json.dumps(receipt));ref=dict(run=str(out),sha256=report.sha(rp))
            result=report.delivery_sdc_evidence(ref,sr,summary)
            self.assertEqual(result['status'],'precise_export_rechecked')
            self.assertFalse(result['timing_verified'])
            target.write_bytes(target.read_bytes()+b'set_false_path -from [all_inputs]\n')
            receipt['delivery_sdc_sha256']=report.sha(target)
            rp.write_text(json.dumps(receipt));ref['sha256']=report.sha(rp)
            with self.assertRaisesRegex(ValueError,'beyond'):
                report.delivery_sdc_evidence(ref,sr,summary)

    def setUp(self):
        fixture=json.loads((Path(__file__).parent/'test_fixtures/icb32_local_windows.json').read_text())['cases'][0]
        window=report.data.read_window(fixture['window_line'],fixture['result'],fixture['encoded_bytes'])
        self.rows={name:dict(layout_sha256='a'*64,codec_sha256='b'*64,capture={'fixture':True},
            result=fixture['result'],task_window=window,activity=dict(sha256='c'*64,
                active_value_records=100,unknown_value_records=2)) for name in report.LAYERS}
        self.a=dict(scope='asic_rtl_functional',asic_cpu_verified=True,cpu_executed=True,
            global_FPGA_defined=False,compile_receipt=dict(firmware_manifest_sha256='d'*64))
        self.g=dict(scope=report.power.GATE_SCOPE,gate_simulation_verified=True,cpu_executed=True,
            sdf_annotated=False,synthesis_summary_sha256='e'*64,firmware_sha256='d'*64)
        self.s=dict(scope='icb32_whole_soc_task_mode_preliminary_synthesis',synthesis_completed=True,
            metrics=dict(period_ns='6.666666',RAMSP128X16=96,RAMSP4096X16=128))
        self.refs=dict(asic={'run':'unused'},gate={'run':'unused'},synthesis={'sha256':'e'*64})

    def test_missing_power_remains_null_and_target_is_5000(self):
        with patch.object(report,'indexed_cases',return_value=self.rows):
            rows,total=report.join_cases(self.a,self.g,self.s,self.refs,[])
        self.assertIsNone(total['raw_energy_per_task_j'])
        self.assertIsNone(total['raw_time_weighted_average_power_w'])
        self.assertFalse(total['goal_5000_tasks_per_second_met_by_cycles'])
        self.assertEqual(rows[0]['transfer_bytes'],37428*2+50688)
        self.assertEqual(rows[0]['transfer_transactions'],37428//2+12672)
        self.assertFalse(rows[0]['system_power_verified'])

    def test_old_macros_or_mixed_firmware_are_rejected(self):
        old=copy.deepcopy(self.s);old['metrics'].update(RAMSP128X16=32,RAMSP4096X16=130)
        with self.assertRaisesRegex(ValueError,'macro'):
            report.join_cases(self.a,self.g,old,self.refs,[])
        other=copy.deepcopy(self.g);other['firmware_sha256']='f'*64
        with self.assertRaisesRegex(ValueError,'Mixed frozen'):
            report.join_cases(self.a,other,self.s,self.refs,[])

    def test_new_gate_must_match_actual_codec_and_results(self):
        bad=copy.deepcopy(self.rows);bad['layer_01']['codec_sha256']='0'*64
        with patch.object(report,'indexed_cases',side_effect=[self.rows,bad]):
            with self.assertRaisesRegex(ValueError,'layout, output'):
                report.join_cases(self.a,self.g,self.s,self.refs,[])


if __name__=='__main__':unittest.main()
