import ast
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import tkinter
import dma16_power as p
import dma16_activity as a
from activity import ROLES
from dma16_synth import SYSMEM, sysmem_bits


def waveform():
    lines = ['$timescale 1fs $end', '$scope module tb_top $end', '$scope module u_e203_soc_top $end']
    for i, (name, (_, width)) in enumerate(sorted(SYSMEM.items())):
        lines.append('$var wire %d p%d sysmem_icb_%s %s$end' %
                     (width, i, name, '' if width == 1 else '[%d:0] ' % (width-1)))
    for i, instance in enumerate(list(ROLES.values())+['u_arch03_arb', 'u_arch03_router']):
        lines += ['$scope module '+instance+' $end', '$var wire 1 s%d clk $end' % i, '$upscope $end']
    lines += ['$upscope $end', '$upscope $end', '$enddefinitions $end', '#0', '$dumpoff $end', '#100000000', '$dumpon']
    lines += ['0s%d' % i for i in range(8)]+['b0 p%d' % i for i in range(10)]
    lines += ['$end', '#110000000', '1s0', 'xs1', '#119999998', '$dumpoff', 'xs0', '$end']
    return '\n'.join(lines)+'\n'


def window():
    return dict(start_ns='100', end_ns='119.999998', period_ns='6.666666', cycles=3,
                start_cycle=15, end_cycle=18, finished_cycle=21, finished_ns='139.999996',
                boundary=p.BOUNDARY, transfer_bytes=191616)


def audited_activity(path):
    return dict(status='scope_and_window_verified', file=path.name, sha256=p.stream_sha(path), bytes=path.stat().st_size,
                scope='tb_top.u_e203_soc_top', start_ns='100', end_ns='119.999998', active_value_records=20,
                unknown_value_records=1, component_declarations={k: 1 for k in ROLES},
                component_value_records={k: 1 for k in ROLES}, dma16_header=a.audit_header(path))


def fake_databases(run):
    (run/'libs').mkdir()
    files = []
    for name in ('standard', 'small', 'large'):
        file = run/'libs'/(name+'.db'); file.write_text(name); files.append(file)
    (run/'source_inputs.json').write_text(json.dumps({str(f): p.sha(f) for f in files}))


class Dma16PowerTests(unittest.TestCase):
    def test_exact_first_valid_last_ack_and_later_drain_proof(self):
        self.assertEqual(p.window_values(window()), ('100', '119.999998', '19.999998'))
        for key, value in [('boundary', 'begin_to_fifo'), ('transfer_bytes', 144640), ('end_cycle', 19),
                           ('finished_cycle', 17), ('finished_ns', '119'), ('period_ns', '6.667')]:
            changed = window(); changed[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                p.window_values(changed)

    def test_header_needs_new_fabric_and_full_top_loading_bus(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'activity.vcd'; path.write_text(waveform())
            result = a.audit_header(path)
            self.assertEqual(result['source_port_bits'], 106)
            self.assertFalse(result['external_source_model_in_power_scope'])
            for old, new in [('u_arch03_arb', 'missing_arb'), ('u_arch03_router', 'missing_router'),
                             ('sysmem_icb_rsp_err', 'old_rsp_err'), ('[31:0]', '[32:1]')]:
                path.write_text(waveform().replace(old, new))
                with self.subTest(old=old), self.assertRaises(ValueError):
                    a.audit_header(path)

    def test_unknown_records_remain_explicit_review_items_not_zero(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'test.vcd'; path.write_text(waveform()); activity = audited_activity(path)
            self.assertEqual(p.validate_activity(activity, window()), '19.999998')
            for key, value in [('unknown_value_records', None), ('unknown_value_records', -1),
                               ('unknown_value_records', 21), ('active_value_records', 0), ('dma16_header', {})]:
                changed = dict(activity); changed[key] = value
                with self.assertRaises(ValueError):
                    p.validate_activity(changed, window())

    def test_power_script_has_same_corner_databases_162_macros_and_full_window(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); fake_databases(root)
            script = p.script({}, root, root/'task.vcd', window())
        self.assertIn('!= 162', script); self.assertNotIn('!= 138', script)
        self.assertIn('-time {100 119.999998}', script)
        self.assertIn('set_app_var sh_continue_on_error false', script)
        for token in ('-include_boundary_nets', '-include_mapping_types', '-list_not_annotated',
                      'power_x_transition_derate_factor', 'power_include_initial_x_transitions',
                      'power_component_inventory.tsv', 'u_arch03_router', p.MARKER):
            self.assertIn(token, script)
        self.assertNotIn('set_switching_activity', script)
        self.assertEqual(tkinter.Tcl().call('info', 'complete', script), 1)

    def test_sdc_failure_cannot_reach_power_analysis(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); fake_databases(root); script = p.script({}, root, root/'test.vcd', window())
        t = tkinter.Tcl()
        t.eval(r'''
set power_ran 0
proc set_app_var {name value} {set ::$name $value}
proc read_verilog {args} {}
proc current_design {args} {}
proc link_design {} {return 1}
proc read_sdc {args} {error "injected bad SysMem constraints"}
proc update_power {args} {set ::power_ran 1}
proc puts {args} {}
proc exit {code} {error "TASK_EXIT $code"}
proc quit {} {error UNEXPECTED_QUIT}
''')
        with self.assertRaisesRegex(tkinter.TclError, 'TASK_EXIT 1'):
            t.eval(script)
        self.assertEqual(int(t.getvar('power_ran')), 0)
        self.assertFalse(t.getboolean(t.getvar('sh_continue_on_error')))

    def test_gate_provenance_rejects_legacy_scope_and_changed_waveform(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); gate = root/'session/dma16_gate'; gate.mkdir(parents=True)
            source = gate/'source.sv'; source.write_text('immutable test source')
            inputs = gate/'source_inputs.json'; inputs.write_text(json.dumps({str(source): p.sha(source)}))
            vcd = gate/'layer_01.vcd'; vcd.write_text(waveform())
            row = dict(case='layer_01', outputs=25344, layout_sha256='a'*64, task_window=window(), activity=audited_activity(vcd))
            report = dict(scope=p.GATE_SCOPE, gate_simulation_verified=True, cpu_executed=True, cases=[row],
                          firmware_sha256='b'*64, source_inputs_sha256=p.sha(inputs),
                          synthesis_run=str(root/'synth'), synthesis_summary_sha256='c'*64)
            def write_report():
                summary = gate/'summary.json'; summary.write_text(json.dumps(report)); digest = p.sha(summary)
                (gate.parent/'state.json').write_text(json.dumps({'stages': {'dma16_gate':
                     dict(status='passed', summary_sha256=digest)}})); return digest
            digest = write_report()
            with patch.object(p, 'verify_synthesis', return_value=None) as verify:
                p.gate_activity(gate, digest, 'layer_01', {'server_root': str(root)})
                self.assertEqual(verify.call_count, 1)
                report['scope'] = 'whole_soc_mapped_functional_without_SDF'; digest = write_report()
                with self.assertRaisesRegex(ValueError, 'has not passed'):
                    p.gate_activity(gate, digest, 'layer_01', {'server_root': str(root)})
                report['scope'] = p.GATE_SCOPE; digest = write_report(); vcd.write_text(waveform()+'\n')
                with self.assertRaisesRegex(ValueError, 'activity changed'):
                    p.gate_activity(gate, digest, 'layer_01', {'server_root': str(root)})

    def test_collection_requires_actual_settings_components_and_units_reports(self):
        with tempfile.TemporaryDirectory() as directory:
            run = Path(directory)
            for name in p.REQUIRED:
                (run/name).write_text('test fixture only')
            (run/'power_sysmem_ports.tsv').write_text('\n'.join('%s\t%s' % item for item in sysmem_bits().items()))
            (run/'power_component_inventory.tsv').write_text('\n'.join('%s\t1' % name for name in
                ('accelerator', 'dma_arbiter', 'dma_router', 'shared', 'itcm', 'dtcm', 'platform_other')))
            settings = run/'power_settings.rpt'
            settings.write_text('power_analysis_mode averaged\npower_x_transition_derate_factor 0.5\npower_include_initial_x_transitions false\n')
            self.assertEqual(len(p.collect_reports(run, {}, p.MARKER)), 7)
            settings.write_text('power_analysis_mode averaged\n')
            with self.assertRaisesRegex(ValueError, 'PrimeTime setting'):
                p.collect_reports(run, {}, p.MARKER)
            with self.assertRaises(ValueError):
                p.collect_reports(run, {}, p.MARKER+'\nError: PT-063 Library Compiler')

    def test_twelve_reports_cannot_mix_configs_or_imply_zero_missing_power(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'a.vcd'; path.write_text(waveform())
            reports = [dict(case=case, scope=p.POWER_SCOPE, status='reports_ready_review_required',
                       gate_summary_sha256='a'*64, synthesis_summary_sha256='b'*64, firmware_sha256='c'*64,
                       layout_sha256=('%064x' % i), task_window=window(), duration_ns='19.999998',
                       activity=audited_activity(path), artifacts={n: 'd'*64 for n in p.REQUIRED})
                       for i, case in enumerate(p.LAYERS)]
            result = p.summarize_twelve(reports)
            self.assertIsNone(result['total_energy_j']); self.assertIsNone(result['total_average_power_w'])
            self.assertFalse(result['system_power_verified'])
            with self.assertRaises(ValueError):
                p.summarize_twelve(reports[:-1])
            with self.assertRaises(ValueError):
                p.summarize_twelve(reports[:-1]+[reports[0]])
            reports[-1]['firmware_sha256'] = 'e'*64
            with self.assertRaisesRegex(ValueError, 'Mixed/missing'):
                p.summarize_twelve(reports)

    def test_python36_grammar(self):
        for module in (p, a):
            ast.parse(Path(module.__file__).read_text(), feature_version=(3, 6))


@unittest.skipUnless(shutil.which('g++'), 'Native compiler unavailable')
class Dma16NativeActivityTests(unittest.TestCase):
    def test_full_native_scan_preserves_unknowns_and_detects_truncation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); binary = root/'scanner.exe'
            source = Path(a.__file__).with_name('activity_scan.cpp')
            subprocess.run([shutil.which('g++'), '-O2', '-std=c++11', str(source), '-o', str(binary)], check=True)
            path = root/'dma16.vcd'; path.write_text(waveform())
            result = a.audit_vcd(path, window(), binary)
            self.assertEqual(result['unknown_value_records'], 1)
            self.assertTrue(result['unknown_activity_review_required'])
            self.assertFalse(result['power_estimated'])
            self.assertFalse(result['mapped_netlist_annotation_verified'])
            self.assertEqual(result['dma16_header']['source_port_bits'], 106)
            path.write_text(waveform().split('#119999998')[0])
            with self.assertRaises(ValueError):
                a.audit_vcd(path, window(), binary)


if __name__ == '__main__':
    unittest.main()
