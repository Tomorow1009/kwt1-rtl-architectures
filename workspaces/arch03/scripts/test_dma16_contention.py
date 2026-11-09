"""Evidence rejection tests; synthetic reports are not hardware acceptance."""
import ast
import copy
from pathlib import Path
import unittest
from unittest.mock import patch
import dma16_contention as c
import build_dma16_contention as b


def report():
    return dict(status='passed', scope='asic_rtl_functional', cpu_executed=True, global_FPGA_defined=False,
                cases=[dict(case='layer_01', outputs=25344, irq_proof=dict(enabled=False),
                    bus_metrics=dict(full_task_counts_verified=True, contention=dict(competing_cycles=100,
                        cpu_grants=50, dma_grants=47904, competing_cpu_grants=20, competing_dma_grants=30)))])


def firmware():
    return dict(benchmark=b.BENCHMARK, scratch=dict(b.SCRATCH), performance_firmware=False,
                configuration=dict(benchmark=b.BENCHMARK, mode=1, prefetch=1, irq_enabled=False),
                source_sha256={'workspaces/arch03/sw/main_dma16_contention.c': 'a'*64,
                               'workspaces/arch03/scripts/build_dma16_contention.py': 'b'*64})


class ContentionTests(unittest.TestCase):
    def test_no_idle_cpu_or_one_sided_service_claims(self):
        c.check_evidence(report(), ['layer_01'])
        for field in ('competing_cycles', 'cpu_grants', 'dma_grants', 'competing_cpu_grants', 'competing_dma_grants'):
            for value in (0, -1, True, None):
                changed = report(); changed['cases'][0]['bus_metrics']['contention'][field] = value
                with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                    c.check_evidence(changed, ['layer_01'])

    def test_actual_asic_complete_task_and_selected_cases_required(self):
        for field, value in (('status', 'running'), ('cpu_executed', False), ('global_FPGA_defined', True),
                             ('scope', 'pin_mock')):
            changed = report(); changed[field] = value
            with self.assertRaises(ValueError): c.check_evidence(changed, ['layer_01'])
        for names in ([], ['layer_01', 'layer_01'], ['rounding'], ['layer_01', 'rounding']):
            with self.assertRaises(ValueError): c.check_evidence(report(), names)
        changed = report(); changed['cases'].append(copy.deepcopy(changed['cases'][0]))
        with self.assertRaises(ValueError): c.check_evidence(changed, ['layer_01'])
        for field, value in (('outputs', 25343), ('irq_proof', dict(enabled=True)),
                             ('bus_metrics', dict(full_task_counts_verified=False, contention={}))):
            changed = report(); changed['cases'][0][field] = value
            with self.assertRaises(ValueError): c.check_evidence(changed, ['layer_01'])

    def test_performance_firmware_cannot_be_relabelled_as_contention(self):
        with patch.object(c, 'verify_dma_firmware', return_value=(firmware(), {})):
            c.verify_firmware(Path('fixture'))
        variants = []
        for field, value in (('benchmark', None), ('performance_firmware', True), ('scratch', {})):
            fw = firmware(); fw[field] = value; variants.append(fw)
        fw = firmware(); fw['configuration']['irq_enabled'] = True; variants.append(fw)
        fw = firmware(); fw['source_sha256'] = {'workspaces/arch03/sw/main_dma16.c': 'c'*64}; variants.append(fw)
        for fw in variants:
            with patch.object(c, 'verify_dma_firmware', return_value=(fw, {})), self.assertRaises(ValueError):
                c.verify_firmware(Path('fixture'))

    def test_scratch_is_aligned_and_disjoint_from_task_and_mailbox(self):
        lo, size = b.SCRATCH['address'], b.SCRATCH['bytes']
        self.assertEqual(lo % 4, 0); self.assertEqual(size, 32*4)
        self.assertTrue(0xa0000000 <= lo < lo+size <= 0xa0080000)
        for start, length in ((0xa0000000, 46976), (0xa000c000, 50688), (0xa001f000, 128)):
            self.assertTrue(lo+size <= start or lo >= start+length)

    def test_python36_and_no_existing_performance_source_edit(self):
        for module in (c, b): ast.parse(Path(module.__file__).read_text(), feature_version=(3, 6))
        self.assertNotIn('main_dma16.c', Path(b.__file__).read_text())


if __name__ == '__main__': unittest.main()
