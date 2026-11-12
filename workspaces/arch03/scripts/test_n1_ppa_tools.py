"""Local logic/Tcl checks only; no N1 netlist, VCS/PT run or PPA acceptance."""
import copy
from decimal import Decimal
import json
from pathlib import Path
import tempfile
import tkinter
import unittest
from unittest.mock import patch

import n1_power as power
import n1_report as report
import n1_saif as saif
from test_dma16_power import fake_databases
from test_native_saif_activity import WINDOW


class N1PowerToolsTests(unittest.TestCase):
    def rows(self):
        rows=[]
        for index,name in enumerate(report.LAYERS):
            cycles=10000 if index<6 else 30000
            duration=Decimal(cycles)*Decimal('6.666666')
            watts=Decimal('.02') if index<6 else Decimal('.08')
            rows.append(dict(case=name,cycles=cycles,duration_ns=str(duration),activity={'fixture':True},
                raw_average_power_w=str(watts),raw_energy_j=str(watts*duration*Decimal('1e-9'))))
        return rows

    def test_power_tcl_keeps_exact_clock_actual_SAIF_and_all_macros(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);fake_databases(root)
            text=power.script({},root,root/'layer_01.saif',WINDOW,'tb_top/u_e203_soc_top',root/'mapped.precise.sdc')
            self.assertEqual(tkinter.Tcl().call('info','complete',text),1)
            for wanted in ('!= 220','*/u_arch03_accel/* RAMSP128X16 92',
                           'read_saif -strip_path tb_top/u_e203_soc_top',
                           'power_x_transition_derate_factor','report_disable_timing',
                           'abs($hf_period-6.666666)>1e-12','power_component_inventory.tsv'):
                self.assertIn(wanted,text)
            self.assertNotIn('!= 224',text);self.assertNotIn('read_vcd ',text)
            self.assertIn('read_sdc {'+str(root/'mapped.precise.sdc')+'}',text)

    def test_power_tcl_rejects_unreviewed_activity_root(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);fake_databases(root)
            with self.assertRaisesRegex(ValueError,'strip path'):
                power.script({},root,root/'layer_01.saif',WINDOW,'accelerator_only',root/'precise.sdc')

    def test_precision_export_preserves_original_SDC(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);synth=root/'synth';out=root/'power';synth.mkdir();out.mkdir()
            original='create_clock [get_ports hfextclk] -name hf_clk -period 6.66667 -waveform {0 3.33333}\nset_load 0.01 [all_outputs]\n'
            source=synth/'mapped.sdc';source.write_text(original)
            (synth/'summary.json').write_text(json.dumps(dict(artifacts={'mapped.sdc':power.sha(source)},metrics={'period_ns':'6.666666'})))
            target,receipt=power.precise_clock(synth,out)
            self.assertEqual(source.read_text(),original)
            self.assertEqual(target.read_text(),original.replace('6.66667','6.666666').replace('3.33333','3.333333'))
            self.assertFalse(receipt['original_sdc_modified']);self.assertTrue(receipt['other_constraints_unchanged'])
            source.write_text(original+'# mutation\n')
            with self.assertRaisesRegex(ValueError,'SDC changed'):power.precise_clock(synth,root)

    def test_numerical_parser_never_inherits_B_acceptance(self):
        numbers=dict(sram=dict(cell_count=220,counts={'itcm':32,'dtcm':32,'shared':64,'accelerator':92}),
                     sources={'unknown':7},system_power_verified=True)
        with patch.object(power,'native_extract_reports',return_value=numbers):
            result=power.extract_reports(Path('not_a_real_run'))
        self.assertEqual(result['numeric_format'],'0x000e0c20')
        self.assertFalse(result['system_power_verified']);self.assertEqual(result['sources']['unknown'],7)
        for count in (0,219,224):
            bad=copy.deepcopy(numbers);bad['sram']['cell_count']=count
            with patch.object(power,'native_extract_reports',return_value=bad):
                with self.assertRaisesRegex(ValueError,'inventory'):power.extract_reports(Path('fixture'))

    def test_full_window_weighting_and_missing_power_is_not_zero(self):
        rows=self.rows();result=report.aggregate_rows(rows)
        self.assertEqual(Decimal(result['raw_time_weighted_power_w']),Decimal('.065'))
        self.assertEqual(Decimal(result['raw_arithmetic_layer_mean_power_w']),Decimal('.05'))
        self.assertTrue(result['goal_6300_met_by_cycles'])
        rows[-1]['raw_energy_j']=None;rows[-1]['raw_average_power_w']=None
        result=report.aggregate_rows(rows)
        self.assertEqual(result['power_layers'],11)
        self.assertIsNone(result['raw_energy_per_task_j']);self.assertIsNone(result['raw_time_weighted_power_w'])

    def test_aggregate_rejects_bad_window_energy_and_duplicates(self):
        for change in ('duration','energy','nan','duplicate','zero','partial'):
            rows=self.rows()
            if change=='duration':rows[0]['duration_ns']='1'
            if change=='energy':rows[0]['raw_energy_j']='1'
            if change=='nan':rows[0]['raw_average_power_w']='NaN'
            if change=='duplicate':rows[-1]['case']=rows[0]['case']
            if change=='zero':rows[0]['cycles']=0
            if change=='partial':rows[0]['raw_energy_j']=None
            with self.assertRaises(ValueError,msg=change):report.aggregate_rows(rows)

    def test_area_and_power_numerical_gates_do_not_approve_stage(self):
        aggregate=report.aggregate_rows(self.rows())
        area=dict(units='um^2',conservative_budget_mm2=1.19)
        plain=report.selection(aggregate,area)
        self.assertTrue(plain['numerical_area_limit_met']);self.assertIsNone(plain['raw_energy_nonincrease'])
        self.assertFalse(plain['eligible_for_next_hardware_stage'])
        area['conservative_budget_mm2']=1.201
        self.assertFalse(report.selection(aggregate,area)['numerical_area_limit_met'])
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'B0_report.json'
            baseline=dict(schema='systolic-b-evidence-export-v1',aggregate=aggregate,
                          verification={'system_power_verified':False})
            path.write_text(json.dumps(baseline))
            selected=report.selection(aggregate,area,dict(report=str(path),sha256=report.sha(path)))
            self.assertEqual(Decimal(selected['raw_energy_ratio_to_B0']),1)
            self.assertTrue(selected['raw_average_power_increase_at_most_10percent'])
            self.assertFalse(selected['baseline']['system_power_verified'])
            self.assertFalse(selected['relative_power_admission_passed'])
            self.assertFalse(selected['eligible_for_next_hardware_stage'])

    def test_power_comparison_reports_real_constraint_failure(self):
        current=report.aggregate_rows(self.rows());baseline=copy.deepcopy(current)
        baseline['raw_energy_per_task_j']=str(Decimal(current['raw_energy_per_task_j'])/2)
        baseline['raw_time_weighted_power_w']=str(Decimal(current['raw_time_weighted_power_w'])/2)
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'B0.json';path.write_text(json.dumps(dict(schema='systolic-b-evidence-export-v1',aggregate=baseline)))
            result=report.selection(current,dict(units='um^2',conservative_budget_mm2=1.1),dict(report=str(path),sha256=report.sha(path)))
            self.assertFalse(result['raw_energy_nonincrease'])
            self.assertFalse(result['raw_average_power_increase_at_most_10percent'])

    def test_stage_rechecks_artifact_bytes(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);run=root/'n1_synth';run.mkdir();artifact=run/'mapped.v';artifact.write_text('original')
            summary=run/'summary.json';summary.write_text(json.dumps(dict(artifacts={'mapped.v':report.sha(artifact)})))
            ref=dict(run=str(run),sha256=report.sha(summary))
            (root/'state.json').write_text(json.dumps(dict(stages={'n1_synth':dict(status='passed',summary_sha256=ref['sha256'])})))
            report.stage(ref,'n1_synth');artifact.write_text('changed')
            with self.assertRaisesRegex(ValueError,'artifact'):report.stage(ref,'n1_synth')

    def test_SAIF_requires_all_twelve_layers_before_tool_call(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            with self.assertRaisesRegex(ValueError,'all twelve'):
                saif.verify(dict(server_root=folder),root,root,'bad',root,'bad',('layer_01',),None)

    def test_SAIF_rejects_old_numeric_and_polling_gate_before_EDA(self):
        for wrong in ('layout', 'numeric', 'polling', 'fake_total'):
            with tempfile.TemporaryDirectory() as folder:
                root=Path(folder);gate=root/'gate';out=root/'capture';gate.mkdir();out.mkdir()
                rows=[dict(case=name,numeric_format='0x000e0c20',capture={'total_checked':False},
                    irq_proof=dict(enabled=True,external=1,timer=1,wfi=1,events=1,unhandled=0))
                    for name in saif.data.CASES14]
                result=dict(scope=saif.SCOPE,gate_simulation_verified=True,cpu_executed=True,
                    sdf_annotated=False,numeric_format='0x000e0c20',layout_id=0x00100004,shift=10,
                    internal_total_observable=False,cases=rows)
                if wrong=='layout':result['layout_id']=0x00100003
                if wrong=='numeric':result['numeric_format']='0x00101028'
                if wrong=='polling':rows[0]['irq_proof']['enabled']=False
                if wrong=='fake_total':rows[0]['capture']['total_checked']=True
                summary=gate/'summary.json';summary.write_text(json.dumps(result));digest=saif.sha(summary)
                (root/'state.json').write_text(json.dumps(dict(stages={'n1_gate':dict(status='passed',summary_sha256=digest)})))
                with patch.object(saif,'qualification',return_value={}):
                    with self.assertRaises(ValueError,msg=wrong):
                        saif.verify(dict(server_root=folder),out,gate,digest,root,'unused',saif.LAYERS,None)

    def test_storage_budget_retains_twenty_percent_margin(self):
        with tempfile.TemporaryDirectory() as folder:
            class Space:
                free=2*1024**3+1200
            with patch.object(saif.shutil,'disk_usage',return_value=Space()):
                receipt=saif.storage_guard(folder,10,100)
                self.assertEqual(receipt['required_bytes'],Space.free)
                Space.free-=1
                with self.assertRaisesRegex(ValueError,'Insufficient'):saif.storage_guard(folder,10,100)


if __name__=='__main__':unittest.main()
