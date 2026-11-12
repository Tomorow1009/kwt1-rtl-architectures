"""Small sequential-wrapper fixtures; no real B0 activity or power approval."""
import copy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

import b0_controls_remaining11 as tool
from test_b0_saif_control_probe import fixture
from test_native_saif_activity import WINDOW


class RemainingTests(unittest.TestCase):
    def put(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value), encoding='utf8')
        return tool.probe.sha(path)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='b0_remaining11_fixture_')
        self.root = Path(self.temp.name).resolve();self.arun = self.root/'activity'/'systolic_b_saif'
        self.arun.mkdir(parents=True);raw = fixture().encode('ascii');rows = []
        for n in range(1, 13):
            name = 'layer_%02d' % n;p = self.arun/(name+'.saif');p.write_bytes(raw)
            expected = tool.probe.native.audit(p, WINDOW)
            rows.append(dict(case=name, activity=expected, task_window=WINDOW))
        activity_sha = self.put(self.arun/'summary.json', dict(
            status='B_native_saif_function_and_complete_windows_passed', firmware_sha256='1'*64,
            synthesis_summary_sha256='2'*64, cases=rows))
        self.put(self.arun.parent/'state.json', dict(stages=dict(systolic_b_saif=dict(
            status='passed', summary_sha256=activity_sha))))
        report = self.root/'report.json'
        report_sha = self.put(report, dict(schema='systolic-b-evidence-export-v1',
            netlist_sha256='3'*64, firmware_sha256='1'*64,
            references=dict(synthesis=dict(sha256='2'*64)),
            activity_reference=dict(run=str(self.arun), sha256=activity_sha)))
        self.inv = self.root/'inventory.json';self.inv_data = dict(
            schema='b0-complete-saif-unknown-map-v1',
            status='complete_existing_unknown_inventory_review_required',
            tool_sha256=tool.probe.UNKNOWN_TOOL_SHA, report=str(report), report_sha256=report_sha,
            netlist_sha256='3'*64, activity_summary_sha256=activity_sha,
            cases=[dict(case=r['case'], activity=r['activity']) for r in rows[1:]])
        self.inv_sha = self.put(self.inv, self.inv_data)
        l01 = tool.probe.scan(self.arun/'layer_01.saif', WINDOW, rows[0]['activity'])
        l01.update(schema='b0-selected-control-residence-v1',
            status='selected_control_residence_collected_review_required', case='layer_01',
            netlist_sha256='3'*64, firmware_sha256='1'*64,
            selection_contract=tool.selection_contract(), runtime_dependencies=tool.probe.dependencies())
        self.l01 = self.root/'l01_control.json';self.l01_data = l01
        self.l01_sha = self.put(self.l01, l01)

    def tearDown(self):self.temp.cleanup()

    def run_collect(self, name='new'):
        return tool.collect(self.inv, self.inv_sha, self.l01, self.l01_sha, self.root, self.root/name)

    def test_exact_eleven_one_read_each_no_l01_no_input_changes(self):
        before = {str(p):tool.probe.sha(p) for p in self.root.rglob('*') if p.is_file()}
        original = Path.open;seen = []
        def watch(path, *args, **kwargs):
            if path.suffix == '.saif':seen.append((path.name, args))
            return original(path, *args, **kwargs)
        with mock.patch.object(Path, 'open', watch):result = self.run_collect()
        self.assertEqual(seen, [(name+'.saif', ('rb',)) for name in tool.CASES])
        self.assertEqual(result['completed_cases'], 11)
        self.assertTrue(result['full12_receipt_coverage'])
        for name in ('system_power_verified','full_control_cone_audited','joint_timing_proved',
                     'source_activity_modified','l01_saif_rescanned','unknown_inventory_regenerated'):
            self.assertIs(result[name], False)
        self.assertEqual(before, {name:tool.probe.sha(name) for name in before})
        self.assertTrue(all(r['missing_count'] > 0 for r in result['cases']))
        for row in result['cases']:
            item = tool.probe.small(row['summary'], row['summary_sha256'])
            self.assertEqual(item['source_read_passes'], 1)
            self.assertFalse(item['coverage']['required_presence_complete'])
        with self.assertRaisesRegex(ValueError,'no overwrite'):self.run_collect()

    def test_l01_in_remaining_set_rejected_before_scanning(self):
        self.inv_data['cases'][0]['case'] = 'layer_01'
        self.inv_sha = self.put(self.inv, self.inv_data)
        with mock.patch.object(tool.probe, 'scan') as scan:
            with self.assertRaisesRegex(ValueError, 'exactly L02-L12'):self.run_collect()
        scan.assert_not_called();self.assertTrue((self.root/'new'/'failure.json').is_file())

    def test_l01_contract_or_dependency_cannot_be_borrowed(self):
        self.l01_data['selection_contract']['macro_required'] = []
        self.l01_sha = self.put(self.l01, self.l01_data)
        with self.assertRaisesRegex(ValueError, 'L01 control receipt differs'):self.run_collect()
        self.l01_data['selection_contract'] = tool.selection_contract()
        self.l01_data['runtime_dependencies']['native_saif_activity']['sha256'] = 'f'*64
        self.l01_sha = self.put(self.l01, self.l01_data)
        with self.assertRaisesRegex(ValueError, 'scanner dependencies differ'):self.run_collect('dependency')

    def test_source_mismatch_keeps_completed_prefix_and_partial(self):
        path = self.arun/'layer_04.saif'
        raw = path.read_bytes();self.assertIn(b'(TC 1)', raw)
        path.write_bytes(raw.replace(b'(TC 1)', b'(TC 2)', 1))
        with self.assertRaisesRegex(ValueError, 'differs from frozen'):self.run_collect()
        failure = tool.probe.small(self.root/'new'/'failure.json')
        self.assertEqual(failure['failed_case'], 'layer_04')
        self.assertEqual([r['case'] for r in failure['completed_cases']], ['layer_02','layer_03'])
        self.assertFalse(failure['full12_receipt_coverage'])
        self.assertTrue((self.root/'new'/'layer_04'/'partial_selected.json').is_file())
        self.assertFalse((self.root/'new'/'summary.json').exists())

    def test_dependency_change_after_scan_keeps_failure(self):
        good = tool.identity();bad = copy.deepcopy(good);bad['wrapper']['sha256'] = 'f'*64
        with mock.patch.object(tool, 'identity', side_effect=[good,bad]):
            with self.assertRaisesRegex(ValueError,'dependency identity changed'):self.run_collect()
        self.assertTrue((self.root/'new'/'failure.json').is_file())
        self.assertTrue((self.root/'new'/'layer_02'/'partial_selected.json').is_file())
        self.assertFalse((self.root/'new'/'layer_02'/'summary.json').exists())

    def test_space_guard_runs_before_scan(self):
        with mock.patch.object(tool.probe.shutil, 'disk_usage', return_value=SimpleNamespace(free=tool.probe.RESERVE)), \
             mock.patch.object(tool.probe, 'scan') as scan:
            with self.assertRaisesRegex(ValueError,'reserve insufficient'):self.run_collect()
        scan.assert_not_called();self.assertTrue((self.root/'new'/'failure.json').is_file())

    def test_wrong_inventory_sha_preserves_failure(self):
        self.inv_sha = '0'*64
        with self.assertRaisesRegex(ValueError, 'Input JSON SHA differs'):self.run_collect()
        failure = tool.probe.small(self.root/'new'/'failure.json')
        self.assertEqual(failure['completed_cases'], [])
        self.assertFalse((self.root/'new'/'verified_request.json').exists())


if __name__ == '__main__':unittest.main(verbosity=2)
