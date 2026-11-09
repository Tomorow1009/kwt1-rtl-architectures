"""Synthetic numeric fixtures, never measured reference PPA."""
import ast
import json
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path
import mmio8_power_numbers as p
from test_dma16_power_numbers import UNITS, BASE_UNITS, power, hierarchy, sram
from test_mmio8_power import activity, window


def sram8():
    return '\n'.join(line for line in sram().splitlines() if 'u_arch03_accel/' not in line or
                     int(line.split('/bank')[1].split('/')[0]) < 10)+'\n'


class Mmio8PowerNumberTests(unittest.TestCase):
    def test_explicit_inventory_profiles_cannot_cross_accept(self):
        result = p.shared.parse_sram(sram8(), profile='mmio8_source')
        self.assertEqual(result['cell_count'], 138)
        self.assertEqual(result['counts']['accelerator'], 10)
        with self.assertRaises(ValueError): p.shared.parse_sram(sram8())
        with self.assertRaises(ValueError): p.shared.parse_sram(sram(), profile='mmio8_source')
        with self.assertRaises(ValueError): p.shared.parse_sram(sram8(), profile='arbitrary')
        self.assertEqual(p.shared.parse_sram(sram())['cell_count'], 162)

    def test_hierarchy_fabric_is_labeled_as_source_routing_without_DMA(self):
        totals = p.shared.parse_power(UNITS, power())['reported_power_w']
        result = p.parse_hierarchy(hierarchy(), totals)
        self.assertIn('source_arbiter', result['modules'])
        self.assertIn('source_router', result['inclusive_module_rows'])
        self.assertNotIn('dma_arbiter', result['modules'])
        for key in p.shared.KEYS:
            self.assertEqual(sum(Decimal(v['derived_power_w'][key]) for v in result['modules'].values()), Decimal(totals[key]))

    def test_actual_run_binding_exact_phase_energy_and_false_acceptance(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); run = root/'mmio8_power'; run.mkdir()
            for name, text in (('units.rpt', BASE_UNITS), ('power.rpt', power()),
                    ('power_verbose.rpt', UNITS+power()), ('power_hierarchy.rpt', hierarchy()),
                    ('power_sram.rpt', sram8()), ('power.log', 'Warning: fixture model review required (PSW-208)\n')):
                (run/name).write_text(text)
            report = dict(status='reports_ready_review_required', scope=p.SCOPE, DMA_present=False,
                artifacts={x.name: p.shared.sha(x) for x in run.iterdir()}, activity=activity(), task_window=window(),
                duration_ns='665.666600', case='layer_01', synthesis_summary_sha256='a'*64,
                gate_summary_sha256='b'*64, firmware_sha256='c'*64, layout_sha256='d'*64,
                component_leaf_counts={'fixture_only': 1}, required_reviews=['fixture is not actual EDA'])
            def write():
                (run/'summary.json').write_text(json.dumps(report)); digest = p.shared.sha(run/'summary.json')
                (root/'state.json').write_text(json.dumps({'stages': {'mmio8_power': {'status': 'passed', 'summary_sha256': digest}}}))
                return digest
            digest = write(); result = p.extract(run, digest)
            self.assertFalse(result['system_power_verified']); self.assertFalse(result['DMA_present'])
            self.assertIsNone(result['approved_average_power_w']); self.assertIsNone(result['approved_energy_j'])
            self.assertEqual(Decimal(result['raw_reported_energy_j']), Decimal('0.0033')*Decimal('665.666600e-9'))
            self.assertEqual(result['warning_occurrences_by_artifact']['power.log']['PSW-208'], 1)
            report['scope'] = p.shared.POWER_SCOPE
            with self.assertRaisesRegex(ValueError, 'new-source'): p.extract(run, write())
            report['scope'] = p.SCOPE; digest = write(); (run/'power.rpt').write_text('changed')
            with self.assertRaisesRegex(ValueError, 'Changed'): p.extract(run, digest)

    def test_python36(self):
        ast.parse(Path(p.__file__).read_text(), feature_version=(3, 6))


if __name__ == '__main__':
    unittest.main()
