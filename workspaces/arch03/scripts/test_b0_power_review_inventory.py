"""Synthetic evidence-tool checks only; never a B0 power acceptance."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import b0_power_review_inventory as review


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(value, sort_keys=True).encode('utf8')
    path.write_bytes(raw)
    return review.digest(raw)


def stage(root, name, kind, value):
    run = root / name / kind
    sha = save(run / 'summary.json', value)
    save(run.parent / 'state.json', dict(stages={kind: dict(status='passed', summary_sha256=sha)}))
    return dict(run=str(run), sha256=sha)


def fixture(root):
    def artifact(run, name, value):
        return save(run / name, value)
    synthesis_run = root / 'synth' / 'systolic_b_synth'
    synth = dict(artifacts={'mapped.v': '0' * 64}, link_report=dict(library_inputs={'library': '1' * 64}))
    for name in ('technology_verification.json', 'memory_library_verification.json'):
        synth['artifacts'][name] = artifact(synthesis_run, name, {'synthetic_fixture': True})
    sr = stage(root, 'synth', 'systolic_b_synth', synth)
    act_rows = []
    activity_run = root / 'activity' / 'systolic_b_saif'
    activity_run.mkdir(parents=True)
    for name in review.LAYERS:
        raw = b'SYNTHETIC_SAIF_MUST_NOT_BE_PARSED'
        (activity_run / (name + '.saif')).write_bytes(raw)
        activity = dict(file=name + '.saif', bytes=len(raw), sha256=review.digest(raw),
            duration_ns='1000', timescale_ns='0.000001', statistics=dict(unknown_declarations=17),
            unknown_representation='VCS_combined_TX_X_or_Z', X_and_Z_separately_measured=False,
            declaration_counts_include_aliases=True, component_counts_overlap=True,
            component_activity=dict(accelerator=dict(unknown_declarations=17, unknown_examples=['x'])))
        act_rows.append(dict(case=name, activity=activity, task_window=dict(cycles=150)))
    ar = stage(root, 'activity', 'systolic_b_saif', dict(
        status='B_native_saif_function_and_complete_windows_passed', cases=act_rows))
    rows, powers = [], []
    for name, act in zip(review.LAYERS, act_rows):
        mapping = dict(default=0, exact_mapping=10, implied=0, total=10)
        numeric = dict(duration_ns='1000', average_power_w='0.07', energy_j='0.00000007',
            sources=dict(mapping, static_probability=mapping), isolated_defaults=dict(count=0, names=[]),
            sram=dict(cell_count=220, cells={}))
        run = root / name / 'systolic_b_power'
        power = dict(case=name, scope='systolic_b_whole_soc_native_saif_pre_layout_power',
            status='reports_and_numbers_ready_unknown_impact_review_required',
            synthesis_summary_sha256=sr['sha256'], gate_summary_sha256='2' * 64,
            activity_summary_sha256=ar['sha256'], firmware_sha256='3' * 64,
            task_window=act['task_window'], activity=act['activity'], numbers=numeric,
            component_leaf_counts=dict(accelerator=100), power_clock=dict(period_ns='6.666666'),
            required_reviews=['Unknown influence'], artifacts={})
        for filename in review.SMALL_REPORTS:
            value = numeric if filename == 'numbers.json' else {'synthetic_fixture': True}
            power['artifacts'][filename] = artifact(run, filename, value)
        powers.append(stage(root, name, 'systolic_b_power', power))
        rows.append(dict(case=name, duration_ns='1000', raw_average_power_w='0.07',
            raw_energy_j='0.00000007', power=numeric, activity=act['activity']))
    report = dict(schema='systolic-b-evidence-export-v1', cases=rows, power_references=powers,
        activity_reference=ar, references=dict(synthesis=sr, gate=dict(sha256='2' * 64)),
        netlist_sha256='0' * 64, libraries_sha256=synth['link_report']['library_inputs'],
        firmware_sha256='3' * 64, production_hardware=dict(synthetic_fixture=True), conditions={},
        aggregate=dict(raw_time_weighted_power_w='0.07', raw_energy_per_task_j='0.00000007'))
    report_path = root / 'export' / 'report.json'
    update_report(report_path, report)
    return report_path, report


def update_report(path, value):
    sha = save(path, value)
    save(path.parent / 'receipt.json', dict(schema='systolic-b-export-receipt-v1', artifacts={'report.json': sha}))


class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='b0_power_fixture_')
        self.root = Path(self.temp.name)
        self.path, self.report = fixture(self.root)

    def tearDown(self):
        self.temp.cleanup()

    def inspect(self):
        return review.inspect(self.path, self.root)

    def test_inventory_is_not_acceptance_and_never_reads_wave(self):
        original = review.Reader.read
        def guarded(reader, path, expected=None):
            self.assertNotEqual(Path(path).suffix, '.saif')
            return original(reader, path, expected)
        before = set(self.root.rglob('*'))
        with patch.object(review.Reader, 'read', guarded):
            result = self.inspect()
        self.assertEqual(before, set(self.root.rglob('*')))
        self.assertEqual(result['aggregate']['raw_time_weighted_power_w'], '0.07')
        self.assertFalse(result['system_power_verified'])
        self.assertFalse(result['layers']['layer_01']['saif_fresh_hash_verified'])
        self.assertEqual(result['layers']['layer_01']['activity']['statistics']['unknown_declarations'], 17)

    def test_modified_export_rejected(self):
        self.path.write_bytes(self.path.read_bytes() + b' ')
        with self.assertRaisesRegex(ValueError, 'SHA differs'):
            self.inspect()

    def test_modified_raw_evidence_rejected(self):
        raw = Path(self.report['power_references'][0]['run']) / 'power.log'
        raw.write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'SHA differs'):
            self.inspect()

    def test_unfinished_stage_rejected(self):
        run = Path(self.report['power_references'][0]['run'])
        save(run.parent / 'state.json', {'stages': {'systolic_b_power': {'status': 'running'}}})
        with self.assertRaisesRegex(ValueError, 'not completed'):
            self.inspect()

    def test_scope_escape_rejected(self):
        self.report['references']['synthesis']['run'] = str(self.root.parent)
        update_report(self.path, self.report)
        with self.assertRaises(ValueError):
            self.inspect()

    def test_wrong_phase_rejected(self):
        self.report['schema'] = 'arch03-n1-evidence-export-v1'
        update_report(self.path, self.report)
        with self.assertRaisesRegex(ValueError, 'Not a B0'):
            self.inspect()

    def test_aggregate_mismatch_rejected(self):
        self.report['aggregate']['raw_time_weighted_power_w'] = '0.071'
        update_report(self.path, self.report)
        with self.assertRaisesRegex(ValueError, 'weighted aggregate differs'):
            self.inspect()

    def test_missing_saif_not_silently_accepted(self):
        (Path(self.report['activity_reference']['run']) / 'layer_01.saif').unlink()
        with self.assertRaisesRegex(ValueError, 'SAIF absent'):
            self.inspect()

    def test_missing_layer_rejected(self):
        self.report['power_references'].pop()
        update_report(self.path, self.report)
        with self.assertRaisesRegex(ValueError, 'fixed12 power'):
            self.inspect()

    def test_size_bound_rejected(self):
        with self.assertRaisesRegex(ValueError, 'bounded read'):
            review.inspect(self.path, self.root, max_file_bytes=16)

    def test_total_read_bound_rejected(self):
        with self.assertRaisesRegex(ValueError, 'read budget'):
            review.inspect(self.path, self.root, max_total_bytes=16)

    def test_size_plan_matches_actual_two_pass_reads_without_reading_artifacts(self):
        original = review.Reader.read
        def guarded(reader, path, expected=None):
            self.assertIn(Path(path), (self.path, self.path.parent / 'receipt.json'))
            return original(reader, path, expected)
        with patch.object(review.Reader, 'read', guarded):
            plan = review.plan_reads(self.path, self.root)
        result = self.inspect()
        self.assertEqual(plan['planned_two_pass_hash_read_bytes'], result['bytes_read'])
        self.assertGreater(plan['candidate_explicit_total_limit_bytes'], result['bytes_read'])
        self.assertTrue(plan['no_limit_was_changed'])
        self.assertFalse(plan['system_power_verified'])

    def test_size_plan_reports_oversize_without_reading_it(self):
        artifact = Path(self.report['power_references'][0]['run']) / 'power.log'
        with artifact.open('r+b') as stream:stream.truncate(17 * 1024 * 1024)
        plan = review.plan_reads(self.path, self.root)
        self.assertFalse(plan['all_existing_files_within_single_file_limit'])
        row = next(item for item in plan['files'] if item['path'] == str(artifact.resolve()))
        self.assertFalse(row['within_single_file_limit'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
