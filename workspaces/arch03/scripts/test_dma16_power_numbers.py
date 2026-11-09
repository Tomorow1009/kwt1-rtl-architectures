"""Synthetic numerical fixtures only; never PPA acceptance evidence."""
import ast
from decimal import Decimal
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import dma16_power_numbers as p

UNITS = 'Dynamic_power_unit : 1 Watt\nLeakage_power_unit : 1 Watt\n'


def power():
    rows = ['Report : Averaged Power', 'Design : e203_soc_top']
    values = (0.001, 0.002, 0.0003, 0.0033)
    for name in p.GROUPS:
        row = values if name == 'memory' else (0, 0, 0, 0)
        rows.append(name+' '+' '.join('%.8e' % n for n in row)+' (100.00%)')
    for label, key in p.LABELS.items():
        value = dict(zip(('internal', 'switching', 'leakage', 'total'), values))[key]
        rows.append(label+' = %.8e (100.00%%)' % value)
    return '\n'.join(rows)+'\n'


class PowerNumberTests(unittest.TestCase):
    def test_precision_and_group_sums_are_preserved(self):
        result = p.parse_power(UNITS, power())
        self.assertEqual(Decimal(result['derived_dynamic_w']), Decimal('0.003'))
        self.assertEqual(result['reported_power_w']['total'], '3.30000000e-03')
        self.assertEqual(len(result['reported_group_power_w']), 7)

    def test_missing_duplicate_or_different_units_fail(self):
        for text in ('', UNITS+UNITS, UNITS.replace('1 Watt', '1e-3 Watt'),
                     UNITS.replace('Watt', 'mW'), UNITS.replace('Leakage_power_unit', 'unknown_unit')):
            with self.subTest(text=text), self.assertRaises(ValueError): p.parse_power(text, power())

    def test_incomplete_nonfinite_negative_duplicate_and_wrong_scope_fail(self):
        original = power()
        variants = [original.replace('memory ', 'missing '), original+original,
                    original+'extra 0.00000000e+00 0.00000000e+00 0.00000000e+00 0.00000000e+00 (0.00%)\n',
                    original.replace('3.30000000e-03', 'NaN'), original.replace('3.30000000e-03', '-3.30000000e-03'),
                    original.replace('3.30000000e-03', '0'), original.replace('3.30000000e-03', 'Infinity'),
                    original.replace('e203_soc_top', 'accelerator_only'), original.replace('Averaged Power', 'Peak Power')]
        for text in variants:
            with self.assertRaises(ValueError): p.parse_power(UNITS, text)

    def test_inconsistent_totals_and_categories_fail_beyond_print_rounding(self):
        for text in (power().replace('Total Power = 3.30000000e-03', 'Total Power = 3.40000000e-03'),
                     power().replace('memory 1.00000000e-03', 'memory 1.10000000e-03'),
                     power().replace('Cell Leakage Power = 3.00000000e-04', 'Cell Leakage Power = 3.10000000e-04')):
            with self.assertRaisesRegex(ValueError, 'sum mismatch'): p.parse_power(UNITS, text)
        p.check_sum(['1.00000000e-03', '2.00000000e-03'], '3.00000001e-03', 'print precision')
        with self.assertRaises(ValueError):
            p.check_sum(['1.00000000e-03', '2.00000000e-03'], '3.00000010e-03', 'changed')

    def test_actual_artifacts_bound_but_numbers_do_not_approve_power(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); run = root/'dma16_power'; run.mkdir()
            for name, text in (('units.rpt', UNITS), ('power.rpt', power()),
                               ('power.log', 'Warning: fixture activity requires review (PSW-208)\n')):
                (run/name).write_text(text)
            summary = dict(status='reports_ready_review_required', scope=p.POWER_SCOPE,
                artifacts={x.name: p.sha(x) for x in run.iterdir()}, activity={}, task_window={}, duration_ns='100',
                case='layer_01', synthesis_summary_sha256='a'*64, gate_summary_sha256='b'*64,
                firmware_sha256='c'*64, layout_sha256='d'*64, component_leaf_counts={'fixture_only': 1},
                required_reviews=['fixture model/activity coverage unresolved'])
            (run/'summary.json').write_text(json.dumps(summary)); digest = p.sha(run/'summary.json')
            (root/'state.json').write_text(json.dumps({'stages': {'dma16_power': {'status': 'passed', 'summary_sha256': digest}}}))
            with patch.object(p, 'validate_activity', return_value='100'):
                result = p.extract(run, digest)
                self.assertFalse(result['system_power_verified']); self.assertIsNone(result['approved_average_power_w'])
                self.assertIsNone(result['approved_energy_j'])
                self.assertEqual(Decimal(result['raw_reported_energy_j']), Decimal('3.3e-10'))
                self.assertEqual(result['warning_occurrences_by_artifact']['power.log']['PSW-208'], 1)
                with self.assertRaisesRegex(ValueError, 'digest'): p.extract(run, '0'*64)
                (run/'power.rpt').write_text(power()+'changed')
                with self.assertRaisesRegex(ValueError, 'Changed'): p.extract(run, digest)

    def test_python36_grammar(self):
        ast.parse(Path(p.__file__).read_text(), feature_version=(3, 6))


if __name__ == '__main__': unittest.main()
