"""Original-reference power contracts; no fabricated tool measurements."""
import ast
import copy
import json
import tempfile
import unittest
from pathlib import Path
import tkinter
import mmio8_power as p


def window():
    return dict(boundary=p.BOUNDARY, total_useful_data_region_bytes=191616,
        period_ns='6.666666', start_ns='11', start_edge_ns='10', start_phase_ns='1',
        end_ns='676.666600', start_cycle=10, end_cycle=110, cycles=100,
        successful_data_region_icb_transactions=dict(source_read_acks=11744, input_write_acks=11744,
                                                    input_read_acks=23488, output_write_acks=25344))


def activity():
    groups = {n: 2 for n in ('cpu', 'itcm', 'dtcm', 'accelerator', 'shared', 'interconnect')}
    return dict(status='scope_and_window_verified', scope='tb_top.u_e203_soc_top',
        start_ns='11', end_ns='676.666600', active_value_records=100, unknown_value_records=3,
        component_declarations=groups, component_value_records=groups,
        mmio8_source_header=dict(status='mmio8_source_declarations_verified', source_port_bits=106),
        sha256='a'*64, bytes=1000)


class Mmio8PowerTests(unittest.TestCase):
    def test_exact_valid_event_excludes_no_first_wait_and_no_extra_phase(self):
        self.assertEqual(p.window_values(window()), ('11', '676.666600', '665.666600'))
        w = window(); w.update(start_ns='10', start_phase_ns='0')
        self.assertEqual(p.window_values(w), ('10', '676.666600', '666.666600'))

    def test_reject_phase_clock_counts_and_old_or_dma_windows(self):
        for key, value in (('boundary', 'begin_marker_response_to_last_output_write_response'),
            ('total_useful_data_region_bytes', 144640), ('start_phase_ns', '0'),
            ('period_ns', '6.667'), ('cycles', 99), ('start_ns', 'nan'),
            ('end_ns', '676.7'), ('start_phase_ns', '-1'), ('end_cycle', 111)):
            bad = window(); bad[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                p.window_values(bad)
        bad = window(); bad['successful_data_region_icb_transactions']['output_write_acks'] = 12672
        with self.assertRaises(ValueError):
            p.window_values(bad)

    def test_pt_script_same_analysis_but_original_macros_and_exact_time(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); (root/'libs').mkdir(); paths = []
            for name in ('std', 'small', 'big'):
                path = root/'libs'/(name+'.db'); path.write_text(name); paths.append(path)
            (root/'source_inputs.json').write_text(json.dumps({str(x): p.sha(x) for x in paths}))
            script = p.script({}, root, root/'case.vcd', window())
        self.assertEqual(tkinter.Tcl().call('info', 'complete', script), 1)
        self.assertIn('-time {11 676.666600}', script)
        self.assertNotIn('-time {10 ', script)
        self.assertIn('[sizeof_collection $m128] != 8', script)
        self.assertIn('[sizeof_collection $memories] != 138', script)
        for expected in ('check_timing -verbose', 'report_disable_timing -nosplit',
                         'read_vcd -zero_delay', 'power_include_initial_x_transitions',
                         'source_arbiter', 'source_router', p.MARKER):
            self.assertIn(expected, script)
        for bad in ('set_switching_activity', '!= 162', 'dma_arbiter', 'set_false_path'):
            self.assertNotIn(bad, script)

    def test_complete_activity_and_actual_unknowns_required(self):
        self.assertEqual(p.validate_activity(activity(), window()), '665.666600')
        for key, value in (('start_ns', '10'), ('scope', 'tb_top.source'),
                ('unknown_value_records', -1), ('unknown_value_records', 101),
                ('active_value_records', 0), ('sha256', 'x'), ('mmio8_source_header', {})):
            bad = activity(); bad[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                p.validate_activity(bad, window())
        bad = copy.deepcopy(activity()); del bad['component_value_records']['shared']
        with self.assertRaises(ValueError):
            p.validate_activity(bad, window())

    def test_old_gate_summary_rejected_before_waveform_access(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); gate = root/'session/mmio8_gate'; gate.mkdir(parents=True)
            (gate/'summary.json').write_text(json.dumps(dict(scope='whole_soc_mapped_functional_without_SDF',
                cpu_executed=True, gate_simulation_verified=True, DMA_present=False)))
            digest = p.sha(gate/'summary.json')
            (gate.parent/'state.json').write_text(json.dumps({'stages': {'mmio8_gate': {
                'status': 'passed', 'summary_sha256': digest}}}))
            with self.assertRaisesRegex(ValueError, 'Original MMIO8'):
                p.gate_activity(gate, digest, 'layer_01', {'server_root': str(root)})

    def test_python36_and_complete_required_reports(self):
        ast.parse(Path(p.__file__).read_text(), feature_version=(3, 6))
        self.assertIn('disabled_timing.rpt', p.REQUIRED)
        self.assertIn('power_with_boundary_nets.rpt', p.REQUIRED)


if __name__ == '__main__':
    unittest.main()
