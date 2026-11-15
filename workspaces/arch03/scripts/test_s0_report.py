"""S0 report identity isolation and full-window/area decision checks."""
from decimal import Decimal
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import s0_report
import t80_report as report


class S0ReportTests(unittest.TestCase):
    def test_schema_cannot_silently_use_legacy_scope(self):
        for request,cfg in (({'schema':'arch03-s0-report-request-v1'},None),
                            ({'schema':'arch03-t80-report-request-v1'},{})):
            with self.assertRaisesRegex(ValueError,'schema'):
                report.build(request,s0_config=cfg)

    def test_s0_limit_and_no_implicit_acceptance(self):
        area={'conservative_budget_mm2':'1.10'}
        self.assertTrue(report.selection({},area)['numerical_area_limit_met'])
        candidate=report.selection({},area,True)
        self.assertFalse(candidate['numerical_area_limit_met'])
        self.assertFalse(candidate['eligible_for_next_hardware_stage'])
        self.assertEqual(candidate['project_limit_mm2'],'1.00')
        self.assertTrue(report.selection({},{'conservative_budget_mm2':'1.00'},True)['numerical_area_limit_met'])

    def test_new_context_does_not_replace_final_netlist_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);run=root/'mapping';run.mkdir()
            origin=dict(baseline_summary_sha256=s0_report.mapping.BASELINE_SUMMARY,
                baseline_netlist_sha256=s0_report.mapping.BASELINE_NETLIST,
                original_summary=dict(scope='t80_whole_soc_task_mode_preliminary_synthesis',
                    link_report=dict(platform_baseline_sha256='a'*64,library_inputs={'db':'b'*64})))
            path=run/'origin_identity.json';path.write_text(json.dumps(origin))
            new=dict(scope=s0_report.s0_validation.SCOPE,
                link_report={'origin_identity_sha256':s0_report.digest(path)},artifacts={'mapped.v':'c'*64})
            ref={'run':str(run),'sha256':'d'*64};cfg={'server_root':str(root)}
            with patch.object(s0_report.s0_validation,'verify_synthesis',return_value=(new,{})):
                result=s0_report.synthesis_context(ref,cfg)
                self.assertEqual(result['summary']['artifacts']['mapped.v'],'c'*64)
                self.assertEqual(result['library_inputs'],{'db':'b'*64})
                origin['baseline_netlist_sha256']='e'*64
                path.write_text(json.dumps(origin))
                new['link_report']['origin_identity_sha256']=s0_report.digest(path)
                with self.assertRaisesRegex(ValueError,'origin differs'):
                    s0_report.synthesis_context(ref,cfg)

    def test_power_weighting_and_missing_layer_not_zero(self):
        rows=[]
        for i,name in enumerate(report.LAYERS):
            cycles=10000 if i<6 else 30000
            duration=Decimal(cycles)*Decimal('6.666666')
            power=Decimal('.02') if i<6 else Decimal('.08')
            rows.append(dict(case=name,cycles=cycles,duration_ns=str(duration),activity={},
                raw_average_power_w=str(power),raw_energy_j=str(power*duration*Decimal('1e-9'))))
        result=report.aggregate_rows(rows)
        self.assertEqual(Decimal(result['raw_time_weighted_power_w']),Decimal('.065'))
        self.assertEqual(Decimal(result['raw_arithmetic_layer_mean_power_w']),Decimal('.05'))
        rows[-1].update(raw_energy_j=None,raw_average_power_w=None)
        result=report.aggregate_rows(rows)
        self.assertEqual(result['power_layers'],11)
        self.assertIsNone(result['raw_time_weighted_power_w'])
        self.assertIsNone(result['raw_energy_per_task_j'])
        rows[-1]['duration_ns']='3'
        with self.assertRaisesRegex(ValueError,'exact period'):report.aggregate_rows(rows)


if __name__=='__main__':unittest.main()
