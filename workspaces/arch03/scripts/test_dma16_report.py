"""Adversarial report fixtures only, not ASIC or PPA evidence."""
import ast
import copy
import csv
from decimal import Decimal
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import dma16_report as r
from test_dma16_power import audited_activity, waveform, window


def fixtures(root):
    vcd = root/'fixture.vcd'; vcd.write_text(waveform())
    rows = []; numbers = []
    for i, name in enumerate(list(r.LAYERS)+['extremes', 'rounding'], 1):
        task = window(); task.update(cycles=3*i, end_cycle=15+3*i, finished_cycle=18+3*i,
            end_ns=str(Decimal(100)+Decimal('19.999998')*i), finished_ns=str(Decimal(100)+Decimal('19.999998')*(i+1)))
        activity = audited_activity(vcd); activity['end_ns'] = task['end_ns']
        layout = '%064x' % i; duration = Decimal(task['end_ns'])-100
        rows.append(dict(case=name, outputs=25344, result={'cycles': 3*i}, task_window=task,
                         layout_sha256=layout, activity=activity))
        if name in r.LAYERS:
            watts = Decimal(i)/1000
            numbers.append(dict(case=name, synthesis_summary_sha256='b'*64, gate_summary_sha256='c'*64,
                firmware_sha256='d'*64, layout_sha256=layout, activity=activity, duration_ns=str(duration),
                reported_power_w={'total': str(watts), 'leakage': '0.0001'}, derived_dynamic_w=str(watts-Decimal('0.0001')),
                raw_reported_energy_j=str(watts*duration*Decimal('1e-9')), module_breakdown=None, sram_breakdown=None,
                warning_occurrences_by_artifact={}, power_summary_sha256=('%064x' % (i+100))))
    asic = dict(scope='asic_rtl_functional', cpu_executed=True, asic_cpu_verified=True,
                global_FPGA_defined=False, cases=copy.deepcopy(rows), compile_receipt={'firmware_sha256': 'd'*64})
    gate = dict(scope=r.power.GATE_SCOPE, gate_simulation_verified=True, cpu_executed=True, cases=rows,
                synthesis_summary_sha256='b'*64, firmware_sha256='d'*64)
    synth = dict(scope='dma16_whole_soc_task_mode_preliminary_synthesis', synthesis_completed=True,
                 metrics={'period_ns': '6.666666', 'RAMSP128X16': 32, 'RAMSP4096X16': 130})
    refs = {name: {'run': str(root/name), 'sha256': char*64} for name, char in [('asic', 'a'), ('synthesis', 'b'), ('gate', 'c')]}
    return asic, gate, synth, refs, numbers


class ReportTests(unittest.TestCase):
    def test_weighted_energy_uses_each_exact_window_not_average_of_powers(self):
        with tempfile.TemporaryDirectory() as d:
            a, g, s, refs, n = fixtures(Path(d))
            rows, summary = r.join_cases(a, g, s, refs, n)
        self.assertEqual(summary['total_cycles'], 234)
        self.assertEqual(Decimal(summary['mean_cycles']), Decimal('19.5'))
        self.assertEqual(Decimal(summary['raw_time_weighted_average_power_w']), sum(Decimal(i*i) for i in range(1, 13))/Decimal(78000))
        self.assertNotEqual(Decimal(summary['raw_time_weighted_average_power_w']), Decimal('0.0065'))
        self.assertIsNone(summary['approved_average_power_w'])
        self.assertTrue(all(not x['system_power_verified'] for x in rows))

    def test_partial_power_never_fills_missing_layers_with_zero(self):
        with tempfile.TemporaryDirectory() as d:
            a, g, s, refs, n = fixtures(Path(d)); rows, summary = r.join_cases(a, g, s, refs, n[:1])
        self.assertEqual(summary['power_layers'], 1)
        self.assertIsNone(summary['raw_total_energy_j'])
        self.assertIsNone(rows[1]['raw_average_power_w'])
        self.assertIsNotNone(rows[0]['raw_energy_j'])

    def test_mixed_firmware_synthesis_layout_activity_and_duplicate_power_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            a, g, s, refs, n = fixtures(Path(d))
            for key in ('firmware_sha256', 'synthesis_summary_sha256', 'gate_summary_sha256', 'layout_sha256'):
                bad = copy.deepcopy(n); bad[0][key] = 'e'*64
                with self.subTest(key=key), self.assertRaises(ValueError): r.join_cases(a, g, s, refs, bad)
            bad = copy.deepcopy(n); bad[0]['activity']['sha256'] = 'e'*64
            with self.assertRaises(ValueError): r.join_cases(a, g, s, refs, bad)
            with self.assertRaises(ValueError): r.join_cases(a, g, s, refs, n+[n[0]])
            bad = copy.deepcopy(n); bad[0]['duration_ns'] = '123'
            with self.assertRaises(ValueError): r.join_cases(a, g, s, refs, bad)

    def test_incomplete_cases_scope_cycle_mismatch_and_relaxed_clock_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            a, g, s, refs, n = fixtures(Path(d))
            for key, value in [('scope', 'FPGA_fixture'), ('cpu_executed', False), ('global_FPGA_defined', True)]:
                bad = dict(a); bad[key] = value
                with self.subTest(key=key), self.assertRaises(ValueError): r.join_cases(bad, g, s, refs, [])
            bad = copy.deepcopy(g); bad['cases'].pop()
            with self.assertRaises(ValueError): r.join_cases(a, bad, s, refs, [])
            bad = copy.deepcopy(g); bad['cases'][0]['result']['cycles'] += 1
            with self.assertRaises(ValueError): r.join_cases(a, bad, s, refs, [])
            bad = copy.deepcopy(s); bad['metrics']['period_ns'] = '6.667'
            with self.assertRaises(ValueError): r.join_cases(a, g, bad, refs, [])

    def test_changed_stage_artifact_and_failed_state_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); run = root/'dma16_gate'; run.mkdir(); (run/'proof.txt').write_text('proof')
            (run/'summary.json').write_text(json.dumps({'artifacts': {'proof.txt': r.sha(run/'proof.txt')}}))
            ref = {'run': str(run), 'sha256': r.sha(run/'summary.json')}
            state = {'stages': {'dma16_gate': {'status': 'passed', 'summary_sha256': ref['sha256']}}}
            (root/'state.json').write_text(json.dumps(state)); r.load_stage(ref, 'dma16_gate')
            (run/'proof.txt').write_text('changed')
            with self.assertRaises(ValueError): r.load_stage(ref, 'dma16_gate')
            (run/'proof.txt').write_text('proof'); state['stages']['dma16_gate']['status'] = 'failed'
            (root/'state.json').write_text(json.dumps(state))
            with self.assertRaises(ValueError): r.load_stage(ref, 'dma16_gate')

    def test_old_incomplete_batch_is_not_final_asic_acceptance(self):
        self.assertEqual(r.audit_batch(None, {})['outputs'], 0)
        with tempfile.TemporaryDirectory() as d:
            path = Path(d); (path/'state.json').write_text(json.dumps({'identity': {}, 'status': 'passed',
                'asic_executed': False, 'outputs': 37*25344, 'completed': [{}]*37}))
            with self.assertRaisesRegex(ValueError, 'incomplete'):
                r.audit_batch({'run': d, 'sha256': r.sha(path/'state.json')}, {})

    def test_relocated_rtl_identity_and_platform_identity(self):
        values = {'/original/workspaces/arch03/rtl/mod%d.sv' % i: ('%064x' % i) for i in range(10)}
        self.assertEqual(r.rtl_inventory(values), r.rtl_inventory({k.replace('/original/', '/different/'): v for k, v in values.items()}))
        with self.assertRaises(ValueError): r.rtl_inventory(dict(list(values.items())[:9]))
        self.assertEqual(r.platform_inventory({'/run/platform/rtl/top.v': 'a'*64}), {'top.v': 'a'*64})
        with self.assertRaises(ValueError): r.platform_inventory({})

    def test_exports_csv_nulls_chinese_report_receipt_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); a, g, s, refs, n = fixtures(root)
            rows, summary = r.join_cases(a, g, s, refs, [])
            report = dict(cases=rows, aggregate=summary, references=refs,
                batch={'status': 'not_run', 'tasks': 0, 'outputs': 0}, unverified=['fixture pending review'],
                history=[{'status': 'failed', 'description': 'fixture preserved', 'run': 'old_run'}])
            output = root/'export'; r.write_outputs(report, output)
            with (output/'tasks.csv').open(encoding='utf-8-sig', newline='') as stream: values = list(csv.DictReader(stream))
            self.assertEqual(values[0]['raw_average_power_w'], '')
            self.assertIn('不是官方', (output/'report_zh.md').read_text(encoding='utf8'))
            receipt = r.read(output/'receipt.json')
            self.assertEqual(len(receipt['artifacts']), 5)
            for name, digest in receipt['artifacts'].items(): self.assertEqual(r.sha(output/name), digest)
            with self.assertRaises(ValueError): r.write_outputs(report, output)

    def test_python36_grammar(self):
        ast.parse(Path(r.__file__).read_text(encoding='utf8'), feature_version=(3, 6))


if __name__ == '__main__': unittest.main()
