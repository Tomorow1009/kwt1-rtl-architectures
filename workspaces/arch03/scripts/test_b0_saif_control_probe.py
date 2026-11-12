"""Small control-probe fixtures; no real B0 power or control verdict."""
import copy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

import b0_saif_control_probe as tool
from test_b0_saif_unknown_inventory import fixture as base_fixture, record, TICKS
from test_native_saif_activity import WINDOW


def fixture(macro=True, unknown_control=False, conditional=False):
    top = [record(key) for key in tool.SHARED_TOP + tool.SHARED_BITS]
    if unknown_control:
        top[top.index(record('cmd_read'))] = record('cmd_read', 5)
    if conditional:
        top[top.index(record('cmd_read'))] = record('cmd_read')[:-1] + ' (COND cond (TX 1)))'
    adapters = []
    for bank in range(32):
        for side in ('low', 'high'):
            name = 'banks[%d].%s' % (bank, side)
            controls = ' '.join(record(key) for key in tool.ADAPTER_REQUIRED)
            child = ''
            if macro and bank == 0 and side == 'low':
                child = '(INSTANCE memory (PORT %s))' % ' '.join(record(key) for key in tool.MACRO_REQUIRED)
            adapters.append('(INSTANCE %s (NET %s) %s)' % (name, controls, child))
    shared = '(INSTANCE u_arch03_shared (NET %s) %s)' % (' '.join(top), ' '.join(adapters))
    old = '(INSTANCE u_arch03_shared (NET %s))' % record('Q')
    raw = base_fixture();assert raw.count(old) == 1
    raw = raw.replace(old, shared)
    aon = '(INSTANCE u_sirv_aon (NET %s %s %s))' % (
        ' '.join(record(key) for key in tool.AON_REQUIRED), record('n123', 10),
        record('Queue_1_io_deq_bits_index[0]', 10))
    raw = raw.replace('(INSTANCE u_e203_subsys_mems', aon + '\n(INSTANCE u_e203_subsys_mems', 1)
    return raw


class ControlTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='b0_control_fixture_')
        self.root = Path(self.temp.name);self.path = self.root/'layer_01.saif'
        self.path.write_bytes(fixture().encode('ascii'))
        self.expected = tool.native.audit(self.path, WINDOW)

    def tearDown(self):self.temp.cleanup()

    def scan(self, expected=None):
        return tool.scan(self.path, WINDOW, expected or self.expected)

    def test_complete_audit_exact_and_one_source_read(self):
        original = Path.open;opens = []
        def watch(path, *args, **kwargs):
            if path == self.path:opens.append((args, kwargs))
            return original(path, *args, **kwargs)
        with mock.patch.object(Path, 'open', watch):result = self.scan()
        self.assertEqual(len(opens), 1)
        self.assertEqual(opens[0][0], ('rb',))
        self.assertEqual(result['activity'], self.expected)
        self.assertFalse(result['system_power_verified'])
        self.assertFalse(result['joint_timing_proved'])
        self.assertFalse(result['full_control_cone_audited'])
        self.assertTrue(result['coverage']['generated_n_and_T_cones_still_require_mapped_review'])

    def test_all_adapters_do_not_replace_missing_macro_ports(self):
        result = self.scan();missing = result['coverage']['missing']
        self.assertEqual(len([x for x in missing if x[0] == 'shared_macro']), 63*20)
        self.assertFalse([x for x in missing if x[0] == 'shared_adapter'])
        self.assertFalse(result['coverage']['required_presence_complete'])
        self.assertTrue(result['coverage']['adapter_is_not_macro_pin_evidence'])
        self.assertEqual(sum(any(x['kind'] == 'shared_macro' for x in r['roles'])
                             for r in result['selected']), 20)

    def test_aon_controls_selected_but_payload_and_generated_not_waived(self):
        result = self.scan()
        names = [r['saif_name'].split('/')[-1] for r in result['selected']]
        self.assertTrue(set(tool.AON_REQUIRED) <= set(names))
        self.assertNotIn('n123', names)
        self.assertNotIn('Queue_1_io_deq_bits_index[0]', names)
        self.assertTrue(result['coverage']['generated_n_and_T_cones_still_require_mapped_review'])

    def test_decimal_time_and_control_unknown_preserved(self):
        self.path.write_bytes(fixture(unknown_control=True).encode('ascii'))
        expected = tool.native.audit(self.path, WINDOW);result = self.scan(expected)
        row = next(r for r in result['selected'] if r['saif_name'].endswith('/cmd_read'))
        self.assertEqual(row['unknown_ticks'], TICKS//2)
        self.assertEqual(tool.Decimal(row['unknown_ns']), tool.Decimal(TICKS//2)*tool.Decimal('.000001'))
        self.assertIsNone(row['reported_TZ_ticks'])
        self.assertTrue(row['combined_TX_X_or_Z'])
        self.assertEqual(result['coverage']['selected_unknown_records'], 1)

    def test_selected_conditional_payload_is_preserved(self):
        self.path.write_bytes(fixture(conditional=True).encode('ascii'))
        result = self.scan(tool.native.audit(self.path, WINDOW))
        row = next(r for r in result['selected'] if r['saif_name'].endswith('/cmd_read'))
        self.assertEqual(row['conditional_entries'], [['COND','cond',['TX','1']]])
        self.assertEqual(result['coverage']['selected_conditional_records'], 1)
        self.assertFalse(result['joint_timing_proved'])

    def test_wrong_sha_scope_and_truncated_sources_rejected(self):
        expected = copy.deepcopy(self.expected);expected['sha256'] = '0'*64
        with self.assertRaisesRegex(ValueError, 'differs from frozen'):self.scan(expected)
        original = self.path.read_bytes()
        self.path.write_bytes(original.replace(b'u_e203_soc_top', b'u_e203_soc_bad'))
        with self.assertRaisesRegex(ValueError, 'outside frozen'):self.scan()
        self.path.write_bytes(original[:-2]);expected = copy.deepcopy(self.expected)
        expected['bytes'] = self.path.stat().st_size
        with self.assertRaisesRegex(ValueError, 'Truncated'):self.scan(expected)

    def test_nested_and_flattened_bank_paths_and_unreviewed_paths(self):
        prefix = ('tb_top','u_e203_soc_top','u_arch03_shared')
        a = tool.select(prefix+('banks[3]','low','memory'), 'CEN')
        b = tool.select(prefix+('banks[3].low','memory'), 'CEN')
        self.assertEqual(a,b)
        self.assertEqual(a, [dict(kind='shared_macro',bank=3,side='low',key='CEN')])
        self.assertFalse(tool.select(prefix+('renamed_macro',), 'CEN'))
        with self.assertRaisesRegex(ValueError,'bank index'):
            tool.select(prefix+('banks[32].low',), 'cs')
        aon = ('tb_top', 'u_e203_soc_top', 'u_sirv_aon')
        for name in ('io_reset_n', 'io_hfclk', 'Queue_1_io_deq_ready'):
            self.assertTrue(tool.select(aon, name))
        self.assertFalse(tool.select(aon, 'Queue_1_io_deq_bits_index[0]'))

    def test_wen_and_mask_missing_are_explicit_not_complete(self):
        rows = []
        for bank in range(32):
            for side in ('low', 'high'):
                for kind, names in (('shared_macro', tool.MACRO_REQUIRED),
                                    ('shared_adapter', tool.ADAPTER_REQUIRED)):
                    for key in names:
                        if key in ('WEN[15]', 'mask[1]'):continue
                        rows.append(dict(roles=[dict(kind=kind,bank=bank,side=side,key=key)],
                                         unknown_ticks=0,conditional_records=0))
        result = tool.coverage(rows,dict(shared={'s'},aon={'a'}))
        self.assertEqual(sum(x[-1] == 'WEN[15]' for x in result['missing']),64)
        self.assertEqual(sum(x[-1] == 'mask[1]' for x in result['missing']),64)
        self.assertFalse(result['required_presence_complete'])

    def prepare(self):
        def put(path, data):
            path.parent.mkdir(parents=True, exist_ok=True);tool.save(path,data);return tool.sha(path)
        arun = self.root/'activity'/'systolic_b_saif';arun.mkdir(parents=True)
        (arun/'layer_01.saif').write_bytes(self.path.read_bytes())
        expected = dict(self.expected, file='layer_01.saif')
        acts = put(arun/'summary.json',dict(status='B_native_saif_function_and_complete_windows_passed',
            firmware_sha256='1'*64,synthesis_summary_sha256='2'*64,
            cases=[dict(case='layer_01',activity=expected,task_window=WINDOW)]))
        put(arun.parent/'state.json',dict(stages=dict(systolic_b_saif=dict(status='passed',summary_sha256=acts))))
        report = self.root/'export'/'report.json'
        report_sha = put(report,dict(schema='systolic-b-evidence-export-v1',netlist_sha256='3'*64,
            firmware_sha256='1'*64,references=dict(synthesis=dict(sha256='2'*64)),
            activity_reference=dict(run=str(arun),sha256=acts)))
        inv = self.root/'inventory'/'summary.json'
        inv_sha = put(inv,dict(schema='b0-complete-saif-unknown-map-v1',
            status='complete_existing_unknown_inventory_review_required',tool_sha256=tool.UNKNOWN_TOOL_SHA,
            report=str(report),report_sha256=report_sha,netlist_sha256='3'*64,
            activity_summary_sha256=acts,cases=[dict(case='layer_01',activity=expected)]))
        return inv,inv_sha

    def test_collector_binds_sources_and_preserves_failures(self):
        inv, inv_sha = self.prepare()
        before = {str(p):tool.sha(p) for p in self.root.rglob('*') if p.is_file()}
        output = self.root/'new_probe'
        result = tool.collect(inv,inv_sha,self.root,output)
        self.assertEqual(result['status'],'selected_control_residence_collected_review_required')
        self.assertFalse(result['coverage']['required_presence_complete'])
        self.assertEqual(result['runtime_dependencies'],tool.dependencies())
        self.assertEqual(before,{name:tool.sha(name) for name in before})
        with self.assertRaisesRegex(ValueError,'no overwrite'):
            tool.collect(inv,inv_sha,self.root,output)
        low = self.root/'low'
        with mock.patch.object(tool.shutil,'disk_usage',return_value=SimpleNamespace(free=tool.RESERVE)):
            with self.assertRaisesRegex(ValueError,'reserve insufficient'):
                tool.collect(inv,inv_sha,self.root,low)
        self.assertTrue((low/'failure.json').is_file())
        changed = self.root/'changed_dependency'
        good = tool.dependencies();bad = copy.deepcopy(good)
        bad['native_saif_activity']['sha256'] = 'f'*64
        with mock.patch.object(tool,'dependencies',side_effect=[good,bad]):
            with self.assertRaisesRegex(ValueError,'dependency identity changed'):
                tool.collect(inv,inv_sha,self.root,changed)
        self.assertTrue((changed/'failure.json').is_file())
        self.assertTrue((changed/'partial_selected.json').is_file())
        self.assertFalse((changed/'summary.json').exists())


if __name__ == '__main__':unittest.main(verbosity=2)
