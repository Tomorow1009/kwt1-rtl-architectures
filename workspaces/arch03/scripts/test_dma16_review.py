"""Adversarial review-binding fixtures, not production evidence."""
import ast
import copy
import json
from pathlib import Path
import tempfile
import unittest
import dma16_review as r


def fixtures():
    refs = {key: {'sha256': char*64} for key, char in [('asic', 'a'), ('synthesis', 'b'), ('gate', 'c')]}
    record = dict(schema='dma16-frozen-review-v1', scope='SS_0p99V_125C_stable_task_mode_pre_layout',
        physical_signoff=False, official_scoring_confirmed=False, official_precision_verified=False,
        decisions=dict(task_mode_synthesis_timing='accepted_for_declared_scope', project_area_upper_bound='accepted_for_declared_scope',
                       system_power='pending_review'), metrics=dict(period_ns='6.666666', setup_slack_ns='0.0000290871',
            hold_slack_ns='0.00136402', area_upper_mm2='0.434796781612', project_area_limit_mm2='2.00'))
    record.update({key+'_summary_sha256': value['sha256'] for key, value in refs.items()})
    synth = dict(metrics=dict(period_ns='6.666666000000', max='0.0000290871', min='0.00136402', latches=0),
        loop_check={'combinational_loops_detected': False},
        area_summary=dict(units='um^2', leaf_count=139430, macro_count=162, conservative_budget_mm2=0.434796781612),
        area_basis=dict(units='um^2', standard_cells_checked=1276))
    timing = dict(scope='dma16_frozen_mapped_ddc_readonly_timing_diagnostics', synthesis_summary_sha256='b'*64,
        netlist_modified=False, high_fanout=dict(count=3, nets=['u_e203_subsys_top/core_csr_clk',
            'u_e203_subsys_top/hfclk', 'u_e203_subsys_top/u_sirv_aon_top/crossing_clock']))
    ports = dict(schema='dma16_mapped_port_diagnostic_v1', synthesis_summary_sha256='b'*64, netlist_modified=False,
        module_count=1334, port_warning_count=4852, disposition_counts={'declaration_only': 4852},
        warning_counts={'LINT-1': 4, 'LINT-2': 178, 'LINT-8': 178, 'LINT-28': 4674, 'LINT-32': 4549, 'LINT-33': 502},
        ports=[dict(disposition='declaration_only', expression_occurrences=0) for _ in range(4852)])
    return record, refs, synth, timing, ports


class ReviewTests(unittest.TestCase):
    def test_acceptance_is_scoped_and_never_implies_power_or_official_results(self):
        accepted = r.validate(*fixtures())
        self.assertTrue(accepted['timing_verified']); self.assertTrue(accepted['project_area_upper_bound_verified'])
        for key in ('system_power_verified', 'physical_signoff', 'official_scoring_confirmed'):
            self.assertFalse(accepted[key])

    def test_mixed_source_scope_and_unsupported_approval_are_rejected(self):
        for key, value in [('asic_summary_sha256', 'f'*64), ('gate_summary_sha256', 'f'*64),
                           ('scope', 'physical_signoff'), ('physical_signoff', True), ('official_scoring_confirmed', True)]:
            values = fixtures(); values[0][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): r.validate(*values)
        values = fixtures(); values[0]['decisions']['system_power'] = 'accepted'
        with self.assertRaises(ValueError): r.validate(*values)

    def test_negative_timing_and_changed_clock_cannot_be_approved_by_record(self):
        for actual, declared, value in [('max', 'setup_slack_ns', '-0.001'), ('min', 'hold_slack_ns', '-0.001'),
                                       ('period_ns', 'period_ns', '6.667')]:
            values = fixtures(); values[2]['metrics'][actual] = value; values[0]['metrics'][declared] = value
            with self.subTest(actual=actual), self.assertRaises(ValueError): r.validate(*values)
        values = fixtures(); values[2]['loop_check']['combinational_loops_detected'] = True
        with self.assertRaises(ValueError): r.validate(*values)

    def test_missing_port_object_used_expression_or_unreviewed_clock_is_rejected(self):
        values = fixtures(); values[4]['ports'].pop()
        with self.assertRaises(ValueError): r.validate(*values)
        values = fixtures(); values[4]['ports'][1500]['expression_occurrences'] = 1
        with self.assertRaises(ValueError): r.validate(*values)
        values = fixtures(); values[4]['warning_counts']['LINT-99'] = 1
        with self.assertRaises(ValueError): r.validate(*values)
        values = fixtures(); values[3]['high_fanout']['nets'][0] = 'data_network'
        with self.assertRaises(ValueError): r.validate(*values)

    def test_area_excess_wrong_units_and_incomplete_geometry_are_rejected(self):
        values = fixtures(); values[2]['area_summary']['conservative_budget_mm2'] = 2.01
        values[0]['metrics']['area_upper_mm2'] = '2.01'
        with self.assertRaises(ValueError): r.validate(*values)
        for key, value in [('units', 'mm^2'), ('standard_cells_checked', 1200)]:
            values = fixtures(); values[2]['area_basis'][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): r.validate(*values)

    def test_files_explanation_and_original_structural_inputs_are_bound(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); record, refs, synth, timing, ports = fixtures()
            doc = root/'review.md'; doc.write_text('explicit scoped engineering decision')
            original = root/'mapped.v'; original.write_text('fixture source')
            ports['inputs_sha256'] = {str(original): r.sha(original)}
            pp = root/'ports.json'; pp.write_text(json.dumps(ports))
            record.update(review_document='workspaces/arch03/review.md', review_document_sha256=r.sha(doc),
                          timing_diagnostic_summary_sha256='d'*64, port_diagnostic_sha256=r.sha(pp),
                          first_power_summary_sha256='e'*64)
            rp = root/'review.json'; rp.write_text(json.dumps(record))
            request = dict(record={'path': str(rp), 'sha256': r.sha(rp)}, document=str(doc),
                timing={'run': str(root), 'sha256': 'd'*64}, ports={'path': str(pp), 'sha256': r.sha(pp)},
                first_power={'run': str(root), 'sha256': 'e'*64})
            def load(ref, stage):
                return timing if stage == 'dma16_timing_audit' else dict(synthesis_summary_sha256='b'*64, gate_summary_sha256='c'*64)
            report = dict(references=refs, verification={'system_power_verified': False}, unverified=[
                'Strict clock/constraints/disabled arcs and high-fanout review', 'Added-area attribution review', 'Power remains pending'])
            out = r.apply(copy.deepcopy(report), request, synth, load)
            self.assertEqual(out['unverified'], ['Power remains pending'])
            self.assertFalse(out['verification']['system_power_verified'])
            original.write_text('altered')
            with self.assertRaisesRegex(ValueError, 'source changed'):
                r.apply(copy.deepcopy(report), request, synth, load)
            doc.write_text('different interpretation')
            with self.assertRaisesRegex(ValueError, 'explanation'):
                r.apply(copy.deepcopy(report), request, synth, load)
            rp.write_text('{}')
            with self.assertRaisesRegex(ValueError, 'artifact changed'):
                r.apply(copy.deepcopy(report), request, synth, load)

    def test_python36_grammar(self):
        ast.parse(Path(r.__file__).read_text(encoding='utf8'), feature_version=(3, 6))


if __name__ == '__main__': unittest.main()
