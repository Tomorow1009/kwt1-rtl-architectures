"""Failure-oriented comparison tests; fixtures do not establish silicon power."""
import ast
import copy
from decimal import Decimal
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import dma16_x_compare as p
from test_dma16_x_sensitivity import reports


def point_fixture(root, name):
    run = root/name/'dma16_x_sensitivity'; run.mkdir(parents=True)
    reports(run, name)
    for filename in p.sensitivity.power.REQUIRED:
        if not (run/filename).exists(): (run/filename).write_text('fixture\n')
    source = {'/design/'+n: 'a'*64 for n in ('mapped.v', 'mapped.sdc', 'std.db', 'large.db', 'small.db')}
    (run/'source_inputs.json').write_text(json.dumps(source))
    (run/'x_sensitivity.tcl').write_text('fixture\n')
    values = p.sensitivity.numeric_reports(run, '200', name)
    (run/'numbers.json').write_text(json.dumps(values))
    report = dict(point=name, scope=p.sensitivity.SCOPE, status='diagnostic_reports_ready_review_required',
                  system_power_verified=False, physical_error_bound=False, replaces_frozen_estimate=False,
                  actual_settings=values['actual_settings'], case='layer_01', gate_summary_sha256='b'*64,
                  synthesis_summary_sha256='c'*64, firmware_sha256='d'*64, layout_sha256='e'*64,
                  duration_ns='200', task_window={'fixture': True}, activity={'fixture': True},
                  component_leaf_counts={'fixture': 1}, tool='/tools/pt_shell',
                  artifacts={f.name:p.sha(f) for f in run.iterdir() if f.is_file()})
    (run/'summary.json').write_text(json.dumps(report)); digest=p.sha(run/'summary.json')
    (run.parent/'state.json').write_text(json.dumps({'stages':{'dma16_x_sensitivity':{
        'status':'passed','summary_sha256':digest}}}))
    return run,digest


class CompareTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.root=Path(self.temp.name)
        self.runs={name:point_fixture(self.root,name) for name in p.sensitivity.POINTS}
        with patch.object(p.sensitivity.power,'validate_activity',return_value='200'):
            self.points=[p.load_point(*item) for item in self.runs.values()]
        frozen=next(x for x in self.points if x['point']=='frozen')
        self.baseline=copy.deepcopy(frozen);self.baseline['run']='/original/power'

    def tearDown(self):self.temp.cleanup()

    def test_four_points_reproduce_original_without_power_approval(self):
        result=p.compare(self.points,self.baseline)
        self.assertTrue(result['frozen_repeat_exactly_reproduced'])
        self.assertEqual(Decimal(result['selected_point_energy_spread_j']),0)
        for key in ('system_power_verified','physical_error_bound','replaces_frozen_estimate'):
            self.assertFalse(result[key])

    def test_signed_differences_and_spread_keep_all_points(self):
        rows=copy.deepcopy(self.points)
        rows[0]['values']['raw_reported_energy_j']='0'
        rows[0]['values']['reported_power_w']['total']='0'
        result=p.compare(rows,self.baseline)
        self.assertEqual(len(result['points']),4)
        self.assertEqual(Decimal(result['points'][0]['delta_from_original_energy_j']),
                         -Decimal(self.baseline['values']['raw_reported_energy_j']))
        self.assertEqual(Decimal(result['selected_point_energy_spread_j']),
                         Decimal(self.baseline['values']['raw_reported_energy_j']))

    def test_changed_artifact_and_failed_stage_are_rejected(self):
        run,digest=self.runs['zero'];(run/'power.rpt').write_text('changed')
        with self.assertRaisesRegex(ValueError,'artifact'):p.load_point(run,digest)
        run,digest=self.runs['one'];state=json.loads((run.parent/'state.json').read_text())
        state['stages']['dma16_x_sensitivity']['status']='failed'
        (run.parent/'state.json').write_text(json.dumps(state))
        with self.assertRaisesRegex(ValueError,'completed'):p.load_point(run,digest)

    def test_no_missing_duplicate_or_shared_point_runs(self):
        candidates=[self.points[:-1],self.points[:3]+[self.points[0]]]
        changed=copy.deepcopy(self.points);changed[1]['run']=changed[0]['run'];candidates.append(changed)
        for rows in candidates:
            with self.assertRaises(ValueError):p.compare(rows,self.baseline)

    def test_all_frozen_identity_dimensions_and_settings_must_match(self):
        for field in p.IDENTITY:
            rows=copy.deepcopy(self.points);rows[0]['identity'][field]='changed'
            with self.subTest(field=field),self.assertRaisesRegex(ValueError,'Different frozen'):
                p.compare(rows,self.baseline)
        rows=copy.deepcopy(self.points);rows[0]['values']['actual_settings']=p.sensitivity.point_settings('one')
        with self.assertRaisesRegex(ValueError,'settings'):p.compare(rows,self.baseline)

    def test_repeat_drift_is_rejected_not_silently_selected(self):
        for field in ('reported_power_w','reported_group_power_w','module_breakdown','sram_breakdown',
                      'boundary_inclusive','raw_reported_energy_j'):
            baseline=copy.deepcopy(self.baseline);baseline['values'][field]='different'
            with self.subTest(field=field),self.assertRaisesRegex(ValueError,'Frozen repeat'):
                p.compare(self.points,baseline)

    def test_missing_library_and_altered_saved_numbers_are_rejected(self):
        run,digest=self.runs['zero'];(run/'source_inputs.json').write_text('{}')
        with self.assertRaisesRegex(ValueError,'library identity'):p.analysis_inputs(run)
        run,digest=self.runs['one'];values=json.loads((run/'numbers.json').read_text())
        values['raw_reported_energy_j']='0';(run/'numbers.json').write_text(json.dumps(values))
        summary=json.loads((run/'summary.json').read_text())
        summary['artifacts']['numbers.json']=p.sha(run/'numbers.json')
        (run/'summary.json').write_text(json.dumps(summary));digest=p.sha(run/'summary.json')
        (run.parent/'state.json').write_text(json.dumps({'stages':{'dma16_x_sensitivity':{
            'status':'passed','summary_sha256':digest}}}))
        with patch.object(p.sensitivity.power,'validate_activity',return_value='200'):
            with self.assertRaisesRegex(ValueError,'Saved/recomputed'):p.load_point(run,digest)

    def test_python36_grammar(self):
        ast.parse(Path(p.__file__).read_text(),feature_version=(3,6))


if __name__=='__main__':unittest.main()
