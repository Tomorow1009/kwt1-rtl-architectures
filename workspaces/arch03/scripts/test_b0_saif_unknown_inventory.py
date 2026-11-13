"""Small synthetic SAIF fixtures; not an actual B0 activity/power verdict."""
import copy
import gzip
import hashlib
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

import b0_saif_unknown_inventory as tool
from test_native_saif_activity import WINDOW
TICKS = 199999980000


def record(name, unknown=0):
    bad = TICKS * unknown // 10
    return '(%s (T0 %d) (T1 0) (TX %d) (TC %d))' % (name, TICKS-bad, bad, int(unknown != 10))


def fixture():
    ports = []
    for name, (_, width) in tool.native.SYSMEM.items():
        ports += [record('sysmem_icb_'+(name if width == 1 else name+'[%d]' % bit)) for bit in range(width)]
    return '''(SAIFILE (SAIFVERSION "2.0") (PROGRAM_NAME "VCS fixture")
 (TIMESCALE 1 fs) (DURATION 199999980000)
 (INSTANCE tb_top (INSTANCE u_e203_soc_top
 (PORT %s)
 (NET %s)
 (INSTANCE u_e203_cpu_top (NET %s)
   (INSTANCE u_e203_itcm_ram (NET %s))
   (INSTANCE u_e203_dtcm_ram (NET %s)))
 (INSTANCE u_e203_subsys_mems (NET %s)
   (INSTANCE u_arch03_accel (NET %s %s %s %s)
     (INSTANCE memory (NET %s)))
   (INSTANCE u_arch03_arb (NET %s))
   (INSTANCE u_arch03_router (NET %s))
   (INSTANCE u_arch03_shared (NET %s)))
 )))''' % (' '.join(ports), record('unused[1]', 10), record('cpu_state', 10),
        record('Q'), record('Q'), record('fabric'),
        record('committed_data[31]', 5), record('committed_data\\[0\\]', 5),
        record('committed_valid'), record('committed_ready'), record('internal_state', 10),
        record('arb'), record('router'), record('Q'))


def index():
    root = tool.ROOT;mems = root+'.u_e203_subsys_mems';accel = mems+'.u_arch03_accel'
    return dict(scopes={root:'TOP', mems:'MEMS', accel:'ACCEL'}, modules={
        'TOP':dict(nets={'unused':(1,0)}, net_uses={}),
        'MEMS':dict(nets={'fabric':None}, net_uses={}),
        'ACCEL':dict(nets={'committed_data':(31,0), 'committed_valid':None, 'committed_ready':None},
                    net_uses={'committed_data':[(0,15)], 'committed_valid':[None], 'committed_ready':[None]})},
        external={root+'.u_e203_cpu_top':'CPU', accel+'.memory':'RAMSP128X16',
                  mems+'.u_arch03_shared':'RAMSP4096X16', mems+'.u_arch03_arb':'ARB', mems+'.u_arch03_router':'ROUTER'})


class UnknownTests(unittest.TestCase):
    def test_new_transport_profiles_bind_their_own_stages(self):
        for name, rows in (('T80', 5), ('T64', 4)):
            report = dict(schema='arch03-'+name.lower()+'-evidence-export-v1', stage=name,
                          numeric_format='0x000e0c20', layout_id=0x00100004, shift=10, row_lanes=rows)
            self.assertEqual(tool.profile_contract(report),
                             (name, name.lower()+'_synth', name.lower()+'_saif',
                              name+'_native_saif_function_and_complete_windows_passed'))
            for key, wrong in (('stage','N1'),('row_lanes',9-rows),('shift',16),
                               ('numeric_format','old'),('layout_id',0x00100003)):
                invalid = dict(report);invalid[key] = wrong
                with self.assertRaisesRegex(ValueError, 'frozen numerical identity'):
                    tool.profile_contract(invalid)

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix='b0_unknown_fixture_')
        self.path = Path(self.directory.name)/'layer_01.saif'
        self.path.write_bytes(fixture().encode('ascii'))
        self.window = dict(WINDOW)
        self.expected = tool.native.audit(self.path, self.window)
        self.rows = []

    def tearDown(self):self.directory.cleanup()

    def scan(self, expected=None):
        return tool.scan(self.path, self.window, expected or self.expected, index(), self.rows.append)

    def test_every_unknown_and_all_original_statistics_bound(self):
        result = self.scan()
        self.assertEqual(result['activity'], self.expected)
        self.assertEqual(result['unknown_rows'], 5)
        self.assertEqual(len(self.rows), 5)
        self.assertEqual(sum(row['unknown_ticks'] for row in self.rows), 4*TICKS)
        self.assertEqual(len(result['watched_committed_path']), 4)
        self.assertFalse(result['global_alias_connectivity_proved'])
        self.assertFalse(result['unknown_effect_on_power_approved'])
        self.assertTrue(all(row['mapping']['is_no_load_waiver'] is False for row in self.rows))

    def test_combined_xz_is_not_reported_as_separate_known_z(self):
        self.scan()
        self.assertTrue(all(row['combined_TX_X_or_Z'] for row in self.rows))
        self.assertTrue(all(row['reported_TZ_ticks'] is None for row in self.rows))

    def test_selected_bit_and_escaped_saif_bit_are_resolved(self):
        self.scan()
        high = next(row for row in self.rows if row['saif_name'].endswith('committed_data[31]'))
        low = next(row for row in self.rows if row['saif_name'].endswith('committed_data[0]'))
        self.assertEqual(high['mapping']['expression_occurrences'], 0)
        self.assertEqual(high['mapping']['disposition'], 'mapped_local_declaration_only_global_alias_review_required')
        self.assertEqual(low['mapping']['expression_occurrences'], 1)
        self.assertEqual(low['mapping']['disposition'], 'mapped_expression_requires_time_review')

    def test_literal_bracket_scalar_is_not_mistaken_for_vector(self):
        net = index();module = net['modules']['ACCEL']
        module['nets']['committed_data[31]'] = None
        module['net_uses']['committed_data[31]'] = [None]
        got = tool.mapped_signal(('tb_top','u_e203_soc_top','u_e203_subsys_mems','u_arch03_accel'),
                                 'committed_data[31]', net)
        self.assertEqual(got['expression_occurrences'], 1)
        self.assertIsNone(got['selected_bits'])

    def test_external_model_unknowns_still_require_review(self):
        self.scan()
        item = next(row for row in self.rows if row['saif_name'].endswith('memory/internal_state'))
        self.assertEqual(item['mapping']['reference'], 'RAMSP128X16')
        self.assertEqual(item['mapping']['disposition'], 'external_cell_port_or_model_internal_requires_review')
        self.assertTrue(item['mapping']['library_pin_or_private_model_node_unresolved'])
        self.assertFalse(item['mapping']['is_no_load_waiver'])

    def test_wrong_frozen_hash_is_rejected(self):
        expected = copy.deepcopy(self.expected);expected['sha256'] = '0'*64
        with self.assertRaisesRegex(ValueError, 'differs from frozen receipt'):self.scan(expected)

    def test_conditional_subrecords_do_not_claim_complete_unknown_inventory(self):
        raw = self.path.read_text(encoding='ascii').replace('(TC 1))', '(TC 1) (COND "A" (TX 1)))', 1)
        self.path.write_bytes(raw.encode('ascii'))
        expected = tool.native.audit(self.path,self.window)
        result = self.scan(expected)
        self.assertEqual(result['unknown_rows'],5)
        self.assertTrue(result['top_level_unknown_declarations_listed'])
        self.assertFalse(result['full_unknown_declarations_listed'])
        self.assertFalse(result['conditional_subrecords_expanded'])

    def test_truncated_saif_rejected(self):
        self.path.write_bytes(self.path.read_bytes()[:-2])
        expected = copy.deepcopy(self.expected);expected['bytes'] = self.path.stat().st_size
        with self.assertRaisesRegex(ValueError, 'Truncated SAIF'):self.scan(expected)

    def test_wrong_dwell_rejected(self):
        raw = self.path.read_bytes().replace(b'(TX 99999990000)', b'(TX 99999990001)', 1)
        self.path.write_bytes(raw)
        with self.assertRaisesRegex(ValueError, 'Dwell mismatch'):self.scan()

    def test_wrong_scope_rejected(self):
        raw = self.path.read_bytes().replace(b'u_e203_soc_top', b'u_e203_soc_bad', 1)
        self.path.write_bytes(raw)
        with self.assertRaisesRegex(ValueError, 'outside frozen whole SoC'):self.scan()

    def test_missing_source_bit_rejected(self):
        first = next(iter(tool.native.SYSMEM));raw = self.path.read_text(encoding='ascii')
        # Replace a single bit name without changing the number of declarations.
        width = tool.native.SYSMEM[first][1]
        target = 'sysmem_icb_'+(first if width == 1 else first+'[0]')
        raw = raw.replace('('+target+' ', '('+target+'_BAD ', 1)
        self.path.write_bytes(raw.encode('ascii'))
        expected = copy.deepcopy(self.expected);expected['bytes'] = self.path.stat().st_size
        with self.assertRaisesRegex(ValueError, 'Source port bits differ'):self.scan(expected)

    def test_real_mapped_parser_keeps_bit_uses(self):
        text = '''module e203_soc_top(a,b);
input a;
output b;
wire [1:0] data;
wire unused;
assign data[0] = a;
assign b = data[0];
endmodule
'''
        mapped = tool.index_netlist(text)
        used = tool.mapped_signal(('tb_top','u_e203_soc_top'), 'data[0]', mapped)
        unused = tool.mapped_signal(('tb_top','u_e203_soc_top'), 'data[1]', mapped)
        self.assertGreater(used['expression_occurrences'], 0)
        self.assertEqual(unused['expression_occurrences'], 0)
        self.assertFalse(unused['is_no_load_waiver'])

    def test_collector_pins_inputs_and_publishes_complete_jsonl_only(self):
        root = Path(self.directory.name)
        n1 = getattr(self, 'n1_fixture', False)
        synth_stage = 'n1_synth' if n1 else 'systolic_b_synth'
        activity_stage = 'n1_saif' if n1 else 'systolic_b_saif'
        def write(path, value):
            path.parent.mkdir(parents=True, exist_ok=True)
            tool.save(path, value)
            return tool.sha(path)
        srun = root/'synthesis'/synth_stage;srun.mkdir(parents=True)
        mapped = srun/'mapped.v';mapped.write_bytes(b'fixture mapped input')
        ss = write(srun/'summary.json', dict(artifacts={'mapped.v':tool.sha(mapped)}))
        write(srun.parent/'state.json', dict(stages={synth_stage:dict(status='passed',summary_sha256=ss)}))
        arun = root/'activity'/activity_stage;arun.mkdir(parents=True)
        cases = []
        for name in tool.LAYERS:
            path = arun/(name+'.saif');path.write_bytes(self.path.read_bytes())
            expected = dict(self.expected, file=path.name)
            cases.append(dict(case=name,activity=expected,task_window=self.window))
        acts = write(arun/'summary.json', dict(status=('N1' if n1 else 'B')+'_native_saif_function_and_complete_windows_passed',
            synthesis_summary_sha256=ss, firmware_sha256='1'*64, cases=cases,
            numeric_format='0x000e0c20',layout_id=0x00100004,gate_summary_sha256='2'*64))
        write(arun.parent/'state.json',dict(stages={activity_stage:dict(status='passed',summary_sha256=acts)}))
        report = root/'export'/'report.json'
        report_sha = write(report,dict(schema='arch03-n1-evidence-export-v1' if n1 else 'systolic-b-evidence-export-v1',
            stage='N1',numeric_format='0x000e0c20',layout_id=0x00100004,shift=10,row_lanes=5,
            activity_reference=dict(run=str(arun),sha256=acts),
            references=dict(synthesis=dict(run=str(srun),sha256=ss),gate=dict(sha256='2'*64)),
            netlist_sha256=tool.sha(mapped),firmware_sha256='1'*64))
        write(report.parent/'receipt.json',dict(artifacts={'report.json':report_sha}))
        before = {str(p):tool.sha(p) for p in root.rglob('*') if p.is_file()}
        output = root/'new_analysis'
        with mock.patch.object(tool,'index_netlist',return_value=index()):
            got = tool.collect(report,report_sha,root,output,cases=('layer_01',))
        self.assertFalse(got['full12_collected'])
        self.assertFalse(got['system_power_verified'])
        self.assertEqual(got['only_existing_N1_activity_used'], n1)
        self.assertEqual(got['only_existing_B0_activity_used'], not n1)
        self.assertEqual(set(got['runtime_dependencies']), set(tool.DEPENDENCIES)|{'tool'})
        self.assertEqual(got['runtime_dependencies'], tool.dependencies())
        lines = gzip.decompress((output/'layer_01.unknown.jsonl.gz').read_bytes()).splitlines()
        self.assertEqual(len(lines),5)
        self.assertTrue(all(json.loads(line)['unknown_ticks']>0 for line in lines))
        self.assertFalse(list(output.glob('*.partial')))
        self.assertEqual(before,{name:tool.sha(Path(name)) for name in before})
        with self.assertRaisesRegex(ValueError,'no overwrite'):
            with mock.patch.object(tool,'index_netlist',return_value=index()):
                tool.collect(report,report_sha,root,output,cases=('layer_01',))
        low = root/'low_space'
        with mock.patch.object(tool,'index_netlist',return_value=index()), mock.patch.object(
                tool.shutil,'disk_usage',return_value=SimpleNamespace(free=tool.RESERVE_BYTES)):
            with self.assertRaisesRegex(ValueError,'initial bounded output budget'):
                tool.collect(report,report_sha,root,low,cases=('layer_01',))
        self.assertTrue((low/'failure.json').is_file())
        self.assertFalse(list(low.glob('*.unknown*')))

    def test_n1_collector_binds_own_stages_and_retains_unknowns(self):
        self.n1_fixture = True
        self.test_collector_pins_inputs_and_publishes_complete_jsonl_only()

    def test_n1_identity_cannot_be_changed_by_schema_alone(self):
        report = dict(schema='arch03-n1-evidence-export-v1',stage='N1',numeric_format='0x000e0c20',
                      layout_id=0x00100004,shift=10,row_lanes=5)
        self.assertEqual(tool.profile_contract(report)[0], 'N1')
        for key, value in [('stage','B'),('numeric_format','Q12'),('layout_id',0x00100003),
                           ('shift',12),('row_lanes',4)]:
            with self.subTest(key=key), self.assertRaisesRegex(ValueError,'export identity'):
                tool.profile_contract(dict(report, **{key:value}))

    def test_dependency_change_is_rejected(self):
        identity = tool.dependencies()
        identity['dma16_unknown_netlist']['sha256'] = '0'*64
        with self.assertRaisesRegex(ValueError,'dependency identity changed'):
            tool.dependencies_unchanged(identity)

    def test_midstream_space_guard_preserves_partial(self):
        partial = Path(self.directory.name)/'retained.partial'
        partial.write_bytes(b'partial inventory')
        with mock.patch.object(tool.shutil,'disk_usage',return_value=SimpleNamespace(free=tool.RESERVE_BYTES-1)):
            with self.assertRaisesRegex(ValueError,'reserve reached'):tool.output_guard(partial.parent)
        self.assertEqual(partial.read_bytes(),b'partial inventory')


if __name__ == '__main__':unittest.main(verbosity=2)
