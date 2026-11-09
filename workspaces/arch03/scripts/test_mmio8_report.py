"""Synthetic export fixtures only, not measured MMIO8 PPA."""
import ast
import copy
import csv
import json
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path
import mmio8_report as r
from test_mmio8_power import window, activity


def fixture():
    rows = []; numbers = []
    for i, name in enumerate(list(r.LAYERS)+['extremes', 'rounding'], 1):
        w = window(); v = activity(); cycles = 100*i
        w.update(end_cycle=w['start_cycle']+cycles, cycles=cycles,
                 end_ns=str(Decimal(w['start_edge_ns'])+cycles*Decimal(w['period_ns'])))
        v.update(start_ns=w['start_ns'], end_ns=w['end_ns'], sha256='%064x' % i)
        duration = Decimal(w['end_ns'])-Decimal(w['start_ns'])
        row = dict(case=name, outputs=25344, task_window=w, activity=v, layout_sha256='%064x' % (100+i),
                   capture=dict(outputs=25344, saturated=i, capture_sha256='%064x' % (200+i)))
        rows.append(row)
        if name not in r.LAYERS: continue
        watts = Decimal(i)/1000
        numbers.append(dict(case=name, DMA_present=False, synthesis_summary_sha256='b'*64,
            gate_summary_sha256='c'*64, firmware_sha256='d'*64, layout_sha256=row['layout_sha256'],
            activity=copy.deepcopy(v), duration_ns=str(duration), reported_power_w=dict(total=str(watts), leakage='0'),
            derived_dynamic_w=str(watts), raw_reported_energy_j=str(watts*duration*Decimal('1e-9')),
            module_breakdown=None, sram_breakdown=None, warning_occurrences_by_artifact={},
            power_summary_sha256='%064x' % (300+i)))
    a = dict(scope='asic_rtl_functional', cpu_executed=True, asic_cpu_verified=True, global_FPGA_defined=False,
             reference=r.REFERENCE, DMA_present=False, cases=copy.deepcopy(rows), compile_receipt={'firmware_sha256': 'd'*64})
    g = dict(scope=r.power.gate_tools.SCOPE, cpu_executed=True, gate_simulation_verified=True, global_FPGA_defined=False,
             reference=r.REFERENCE, DMA_present=False, input_task_bytes_in_boot=0, cases=rows,
             synthesis_summary_sha256='b'*64, firmware_sha256='d'*64)
    s = dict(scope=r.power.synth.SCOPE, DMA_present=False, synthesis_completed=True,
             metrics=dict(period_ns='6.666666', RAMSP128X16=8, RAMSP4096X16=130))
    refs = {name: {'run': name, 'sha256': char*64} for name, char in [('asic', 'a'), ('synthesis', 'b'), ('gate', 'c')]}
    return a, g, s, refs, numbers


class Mmio8ReportTests(unittest.TestCase):
    def test_energy_preserves_first_valid_phase_and_duration_weighting(self):
        a, g, s, refs, n = fixture(); rows, totals = r.join_cases(a, g, s, refs, n)
        expected = sum(Decimal(x['raw_reported_energy_j']) for x in n)
        duration = sum(Decimal(x['duration_ns']) for x in n)
        self.assertEqual(Decimal(totals['raw_total_energy_j']), expected)
        self.assertEqual(Decimal(totals['raw_time_weighted_average_power_w']), expected/duration/Decimal('1e-9'))
        self.assertEqual(Decimal(rows[0]['duration_ns']), Decimal('665.666600'))
        self.assertNotEqual(Decimal(totals['raw_time_weighted_average_power_w']), Decimal('0.0065'))
        self.assertIsNone(totals['approved_energy_per_task_j'])
        self.assertTrue(all(not row['system_power_verified'] for row in rows))

    def test_partial_power_stays_null(self):
        a, g, s, refs, n = fixture(); rows, totals = r.join_cases(a, g, s, refs, n[:1])
        self.assertEqual(totals['power_layers'], 1); self.assertIsNone(totals['raw_total_energy_j'])
        self.assertIsNone(rows[1]['raw_average_power_w']); self.assertIsNotNone(rows[0]['raw_energy_j'])

    def test_dma_old_window_preload_incomplete_suite_and_wrong_macro_rejected(self):
        for target, key, value in [('a', 'DMA_present', True), ('g', 'scope', 'dma16_whole_soc_mapped_functional_without_SDF'),
                                  ('a', 'reference', 'old_BEGIN'), ('g', 'input_task_bytes_in_boot', 46976)]:
            a, g, s, refs, n = fixture(); {'a': a, 'g': g}[target][key] = value
            with self.subTest(target=target, key=key), self.assertRaises(ValueError): r.join_cases(a, g, s, refs, n)
        a, g, s, refs, n = fixture(); s['metrics']['RAMSP128X16'] = 32
        with self.assertRaises(ValueError): r.join_cases(a, g, s, refs, n)
        a, g, s, refs, n = fixture(); g['cases'].pop()
        with self.assertRaises(ValueError): r.join_cases(a, g, s, refs, n)
        a, g, s, refs, n = fixture(); a['cases'][0]['task_window']['boundary'] = 'BEGIN_response'
        with self.assertRaises(ValueError): r.join_cases(a, g, s, refs, n)

    def test_saturation_and_capture_in_directed_cases_are_compared_too(self):
        a, g, s, refs, n = fixture(); g['cases'][-1]['capture']['saturated'] += 1
        with self.assertRaisesRegex(ValueError, 'output or saturation'): r.join_cases(a, g, s, refs, n)
        a, g, s, refs, n = fixture(); g['cases'][-2]['capture']['capture_sha256'] = 'f'*64
        with self.assertRaises(ValueError): r.join_cases(a, g, s, refs, n)

    def test_power_identity_phase_and_duplicate_guards(self):
        for key in ('synthesis_summary_sha256', 'gate_summary_sha256', 'firmware_sha256', 'layout_sha256'):
            a, g, s, refs, n = fixture(); n[0][key] = 'f'*64
            with self.subTest(key=key), self.assertRaises(ValueError): r.join_cases(a, g, s, refs, n)
        a, g, s, refs, n = fixture(); n[0]['duration_ns'] = '666.666600'
        with self.assertRaises(ValueError): r.join_cases(a, g, s, refs, n)
        a, g, s, refs, n = fixture()
        with self.assertRaises(ValueError): r.join_cases(a, g, s, refs, n+[n[0]])
        g['cases'][0]['task_window']['start_phase_ns'] = '0'
        with self.assertRaises(ValueError): r.join_cases(a, g, s, refs, n)

    def test_reference_exports_have_own_title_receipt_and_empty_missing_numbers(self):
        a, g, s, refs, n = fixture(); rows, totals = r.join_cases(a, g, s, refs, [])
        report = dict(cases=rows, aggregate=totals, references=refs, architecture_label='原8路MMIO同源对照',
                      receipt_schema='mmio8-source-evidence-export-receipt-v1',
                      batch=dict(status='reference_suite_only', tasks=0, outputs=0), unverified=['synthetic fixture'], history=[])
        with tempfile.TemporaryDirectory() as d:
            out = Path(d)/'report'; r.common.write_outputs(report, out)
            title = (out/'report_zh.md').read_text(encoding='utf8').splitlines()[0]
            self.assertIn('原8路MMIO', title); self.assertNotIn('DMA16', title)
            receipt = json.loads((out/'receipt.json').read_text())
            self.assertEqual(receipt['schema'], report['receipt_schema'])
            for name, digest in receipt['artifacts'].items(): self.assertEqual(r.sha(out/name), digest)
            with (out/'tasks.csv').open(encoding='utf-8-sig', newline='') as stream:
                values = list(csv.DictReader(stream))
            self.assertEqual(len(values), 12); self.assertEqual(values[0]['raw_energy_j'], '')
            with self.assertRaises(ValueError): r.common.write_outputs(report, out)

    def test_request_scope_and_python36(self):
        with self.assertRaises(ValueError): r.build(dict(schema='dma16-report-request-v1'))
        with self.assertRaises(ValueError): r.build(dict(schema='mmio8-source-report-request-v1', batch={}))
        ast.parse(Path(r.__file__).read_text(encoding='utf8'), feature_version=6)


if __name__ == '__main__': unittest.main()
