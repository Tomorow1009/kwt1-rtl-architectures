"""Synthetic numerical fixtures only; never PPA acceptance evidence."""
import ast
from decimal import Decimal
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import dma16_power_numbers as p

UNITS = 'Dynamic Power Units = 1 W\nLeakage Power Units = 1 W\n'
BASE_UNITS = ('Report : units\nDesign : e203_soc_top\nCapacitive_load_unit : 1e-12 Farad\n'
              'Time_unit : 1e-09 Second\nVoltage_unit : 1 Volt\n')


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


def hierarchy():
    # Shape follows the installed PT hierarchy; synthetic values are not PPA.
    header = 'Report : Averaged Power\nDesign : e203_soc_top\nHierarchy Power Power Power Power %\n'
    def row(indent, name, factor, reference=True):
        values = [Decimal('0.0001')*factor, Decimal('0.0002')*factor,
                  Decimal('0.00003')*factor, Decimal('0.00033')*factor]
        return ' '*indent+name+(' (fixture)' if reference else '')+' '+' '.join('%.2e' % v for v in values)+' 0.0\n'
    return (header+row(0, 'e203_soc_top', 10, False)+row(2, 'soc', 10)+
            row(4, 'u_e203_cpu_top', 3)+row(6, 'u_e203_itcm_ram', 1)+row(6, 'u_e203_dtcm_ram', 1)+
            ''.join(row(4, name, 1) for name in ('u_arch03_accel', 'u_arch03_shared', 'u_arch03_arb', 'u_arch03_router')))


def sram():
    rows = ['Design : e203_soc_top', '-cell_power']
    for token, count in (('u_e203_itcm_gnrl_ram', 32), ('u_e203_dtcm_gnrl_ram', 32),
                         ('u_arch03_shared', 64), ('u_arch03_accel', 34)):
        for index in range(count):
            rows.append('soc/%s/bank%d/memory 1.00000000e-06 2.00000000e-06 3.00000000e-07 3.30000000e-06 (0.01%%) a' % (token, index))
    return '\n'.join(rows)+'\n'


class PowerNumberTests(unittest.TestCase):
    def test_module_sums_exclude_nested_cpu_tcm_and_keep_rounding(self):
        totals = p.parse_power(UNITS, power())['reported_power_w']
        result = p.parse_hierarchy(hierarchy(), totals)
        self.assertEqual(len(result['modules']), 8)
        self.assertEqual(Decimal(result['modules']['cpu_excluding_tcm']['derived_power_w']['total']), Decimal('0.00033'))
        self.assertEqual(Decimal(result['modules']['platform_other']['derived_power_w']['total']), Decimal('0.00099'))
        self.assertGreater(Decimal(result['modules']['cpu_excluding_tcm']['rounding_bound_w']['total']), 0)
        for key in p.KEYS:
            self.assertEqual(sum(Decimal(r['derived_power_w'][key]) for r in result['modules'].values()), Decimal(totals[key]))
        self.assertEqual(p.hierarchy_rounding('0.000'), 0)

    def test_hierarchy_missing_duplicate_nested_bad_sum_and_wrong_root_fail(self):
        totals = p.parse_power(UNITS, power())['reported_power_w']; text = hierarchy()
        bad = [text.replace('u_arch03_arb', 'missing_arb'), text.replace('soc (fixture)', 'e203_soc_top'),
               text+'    u_arch03_arb (fixture) 1.00e-04 2.00e-04 3.00e-05 3.30e-04 0.0\n',
               text.replace('    u_arch03_router', '      u_arch03_router'),
               text.replace('3.30e-04', '9.30e-04'), text.replace('3.30e-03', '3.80e-03'),
               text.replace('3.30e-04', 'NaN'), text.replace('e203_soc_top', 'wrong_top'),
               text.replace('      u_e203_itcm_ram', '    u_e203_itcm_ram'),
               text.replace('      u_e203_dtcm_ram', '        u_e203_dtcm_ram')]
        for value in bad:
            with self.subTest(value=value), self.assertRaises(ValueError): p.parse_hierarchy(value, totals)

    def test_actual_signed_clock_gate_internal_contribution_is_retained(self):
        totals = p.parse_power(UNITS, power())['reported_power_w']
        signed = hierarchy()+'      u_clkgate (fixture) -6.9e-06 1.55e-04 4.53e-09 1.48e-04 0.7\n'
        result = p.parse_hierarchy(signed, totals)
        self.assertEqual(result['negative_internal_rows'][0]['reported_internal_w'], '-6.9e-06')
        self.assertEqual(p.hierarchy_rounding('-6.9e-06'), Decimal('0.05e-06'))
        self.assertEqual(result['modules']['platform_other']['derived_power_w']['total'], '0.00099000000')
        with self.assertRaises(ValueError):
            p.parse_hierarchy(signed.replace('1.55e-04', '-1.55e-04'), totals)

    def test_sram_counts_values_and_blackboxes_are_explicit(self):
        result = p.parse_sram(sram())
        self.assertEqual(result['cell_count'], 162)
        self.assertEqual(result['counts']['accelerator'], 34)
        self.assertEqual(Decimal(result['summed_cell_power_w']['accelerator']['total']), Decimal('0.0001122'))
        original = sram(); last = original.splitlines()[-1]
        for bad in (original.replace(last+'\n', ''), original+last+'\n', original.replace(' a\n', ' b\n'),
                    original.replace('u_arch03_shared', 'unowned'), original.replace('3.30000000e-06', '4.30000000e-06'),
                    original.replace('3.30000000e-06', 'NaN')):
            with self.assertRaises(ValueError): p.parse_sram(bad)

    def test_precision_and_group_sums_are_preserved(self):
        result = p.parse_power(UNITS, power())
        self.assertEqual(Decimal(result['derived_dynamic_w']), Decimal('0.003'))
        self.assertEqual(result['reported_power_w']['total'], '3.30000000e-03')
        self.assertEqual(len(result['reported_group_power_w']), 7)

    def test_missing_duplicate_or_different_units_fail(self):
        for text in ('', BASE_UNITS, UNITS+UNITS, UNITS.replace('1 W', '1e-3 W'),
                     UNITS.replace(' W', ' mW'), UNITS.replace('Leakage Power Units', 'unknown_unit'),
                     'Dynamic_power_unit : 1 Watt\nLeakage_power_unit : 1 Watt\n'):
            with self.subTest(text=text), self.assertRaises(ValueError): p.parse_power(text, power())

    def test_base_units_come_from_report_units_and_power_units_from_verbose(self):
        self.assertEqual(p.parse_base_units(BASE_UNITS)['Time_unit'], '1e-09 Second')
        for bad in (UNITS, BASE_UNITS+BASE_UNITS, BASE_UNITS.replace('1e-09', '1e-12'),
                    BASE_UNITS.replace('Farad', 'pf'), BASE_UNITS.replace('e203_soc_top', 'other')):
            with self.assertRaises(ValueError): p.parse_base_units(bad)

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

    def test_actual_binary32_display_roundtrip_has_a_bounded_recorded_residual(self):
        terms = ['1.20398494e-04', '1.81365778e-07', '4.60310002e-05']
        result = p.check_sum(terms, '1.66610858e-04', 'observed old SRAM row, format only')
        self.assertEqual(Decimal(result['residual_w']), Decimal('1.978e-12'))
        self.assertEqual(result['numerical_basis'], 'decimal_display_plus_exact_binary32_roundtrip_half_ulp')
        self.assertLess(Decimal(result['bound_w']), Decimal('1e-10'))
        with self.assertRaises(ValueError): p.check_sum(terms, '1.66610858e-03', 'changed exponent')
        with self.assertRaises(ValueError): p.observed_binary32_rounding('1.20398495e-04')
        self.assertEqual(p.rounding('0.00000000e+00'), 0)

    def test_actual_artifacts_bound_but_numbers_do_not_approve_power(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); run = root/'dma16_power'; run.mkdir()
            for name, text in (('units.rpt', BASE_UNITS), ('power.rpt', power()), ('power_verbose.rpt', UNITS+power()),
                               ('power_hierarchy.rpt', hierarchy()), ('power_sram.rpt', sram()),
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
