"""Reference synthesis contracts; fixtures are not ASIC/STA evidence."""
import ast
import json
import tempfile
import unittest
from pathlib import Path
import tkinter
import mmio8_synth as m
import dma16_synth as d
from test_dma16_synth import inventory, total, top, write_library_receipts, constraint_interpreter


def rows8():
    return [r for r in inventory() if 'RAMSP128X16_' not in r or
            int(r.split('\t')[0].rsplit('_', 1)[1]) < 8]


def reports(run):
    rows = rows8(); write_library_receipts(run)
    (run/'metrics.txt').write_text('period_ns 6.666666\nlf_period_ns 66\nRAMSP128X16 8\nRAMSP4096X16 130\nmax 0.01\nmin 0.02\nlatches 0\n')
    (run/'area.rpt').write_text('Total cell area: %.9f\n' % total(rows))
    (run/'leaf_area.tsv').write_text('\n'.join(rows))
    for name in ('sysmem_ports.tsv', 'linked_sysmem_ports.tsv', 'mapped_sysmem_ports.tsv'):
        (run/name).write_text('\n'.join('%s\t%s' % item for item in d.sysmem_bits().items()))
    for name in ('mapped.ddc', 'mapped.sdc', 'constraints.rpt', 'timing_max.rpt', 'timing_min.rpt',
                 'check_design_mapped.rpt', 'references_mapped.rpt', 'qor.rpt', 'hierarchy.rpt'):
        (run/name).write_text('OFFLINE_FIXTURE_NOT_EDA_EVIDENCE')
    (run/'mapped.v').write_text(top())
    (run/'check_timing.rpt').write_text('Information: Checking loops...\n')


class Mmio8SynthesisTests(unittest.TestCase):
    def test_reference_uses_original_core_without_dma_engine(self):
        names = [p.name for p in m.source_list()]
        self.assertIn('arch02_linear.sv', names)
        self.assertIn('arch03_icb_accel.sv', names)
        self.assertFalse(any('dma16' in n or 'linear16' in n for n in names))
        self.assertEqual(len(names), len(set(names)))

    def test_same_actual_io_delays_and_clock_constraints(self):
        self.assertEqual(m.constraints().replace('ARCH03_MMIO8_SOURCE_SYSMEM_PORTS',
                                                'ARCH03_DMA16_SYSMEM_PORTS'), d.constraints())
        t, inputs, outputs = constraint_interpreter(); t.eval(m.constraints())
        for kind, variable in [('in', 'input_delays'), ('out', 'output_delays')]:
            rows = [t.splitlist(r) for r in t.splitlist(t.getvar(variable))]
            wanted = {p for p, direction in d.sysmem_bits().items() if direction == kind}
            for bound, value in [('-max', '1.0'), ('-min', '0.0')]:
                matches = [r for r in rows if r[0] == bound and r[3] == 'hf_clk']
                self.assertEqual(len(matches), 1)
                self.assertEqual(matches[0][1], value)
                self.assertTrue(wanted <= set(t.splitlist(matches[0][4])))

    def test_fresh_link_and_mapping_guards_reject_dma16_inventory(self):
        with tempfile.TemporaryDirectory() as directory:
            run = Path(directory); (run/'libs').mkdir()
            for n in ('small.db', 'big.db'): (run/'libs'/n).touch()
            scripts = [m.link_script('std.db', ['small.db', 'big.db'], m.source_list(), ['.']),
                       m.script(run, {'standard_library_member': 'std.db'})]
            for script in scripts:
                self.assertEqual(tkinter.Tcl().call('info', 'complete', script), 1)
                self.assertIn('[sizeof_collection $m128] != 8', script)
                self.assertIn('*/u_arch03_accel/* RAMSP128X16 8', script)
                self.assertNotIn('RAMSP128X16 32', script)
                self.assertNotIn('set_clock_groups', script)
                self.assertNotIn('set_multicycle_path', script)
            self.assertIn('!= 138', scripts[1]); self.assertNotIn('!= 162', scripts[1])
            self.assertIn(m.SYNTH_MARKER, scripts[1])
            self.assertEqual(scripts[1].count('set_false_path -from [get_ports lfextclk] -to $sync0'), 1)
            self.assertIn('analyze -format sverilog -define SYNTHESIS', scripts[0])
            (run/'linked.ddc').touch()
            with self.assertRaisesRegex(ValueError, 'fresh run'):
                m.synth({}, run, Path('nonexistent_platform'), lambda *a: self.fail('Tool called'))

    def test_area_counts_routing_and_rejects_wrong_macro_ownership(self):
        rows = rows8(); a = m.area_inventory('\n'.join(rows), total(rows))
        self.assertEqual(a['macro_count'], 138)
        self.assertEqual(a['groups']['accelerator']['sram_count'], 10)
        self.assertEqual(a['physical_sram_bytes'], 1042*1024)
        self.assertEqual(a['groups']['platform_other']['standard_cell_area'], 21)
        expected = (37+a['groups']['accelerator']['sram_area'])/1e6
        self.assertAlmostEqual(a['conservative_budget_mm2'], expected)
        self.assertFalse(a['scoring_area_verified'])
        for bad in [inventory(), rows[1:], [r.replace('/u_arch03_shared/', '/fixed_bus/') for r in rows],
                    [r for r in rows if r != 'top/u_arch03_accel/reg\tDFF\t4\tlib/DFF']]:
            with self.subTest(bad=len(bad)), self.assertRaises(ValueError):
                m.area_inventory('\n'.join(bad), total(bad))

    def test_report_collection_is_not_acceptance_and_requires_artifacts(self):
        with tempfile.TemporaryDirectory() as directory:
            run = Path(directory); reports(run)
            result = m.collect_reports(run, {}, {}, m.SYNTH_MARKER)
            self.assertTrue(result['setup_hold_nonnegative'])
            for flag in ('DMA_present', 'timing_verified', 'scoring_area_verified',
                         'gate_simulation_verified', 'system_power_verified', 'physical_signoff'):
                self.assertFalse(result[flag])
            (run/'metrics.txt').write_text((run/'metrics.txt').read_text().replace('max 0.01', 'max -0.01'))
            self.assertFalse(m.collect_reports(run, {}, {}, m.SYNTH_MARKER)['setup_hold_nonnegative'])
            for name in ('hierarchy.rpt', 'linked_sysmem_ports.tsv', 'check_timing.rpt'):
                original = (run/name).read_text(); (run/name).unlink()
                with self.subTest(name=name), self.assertRaises((ValueError, FileNotFoundError)):
                    m.collect_reports(run, {}, {}, m.SYNTH_MARKER)
                (run/name).write_text(original)

    def test_feedback_and_changed_inputs_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            run = Path(directory); reports(run)
            p = run/'check_timing.rpt'; original = p.read_text()
            p.write_text(original+'Warning: Timing loops detected. (TIM-209)\n')
            with self.assertRaises(ValueError): m.collect_reports(run, {}, {}, m.SYNTH_MARKER)
            p.write_text(original)
            before = {str(run/'mapped.v'): d.sha(run/'mapped.v')}
            (run/'mapped.v').write_text(top()+'// changed')
            with self.assertRaisesRegex(ValueError, 'input changed'):
                m.collect_reports(run, {}, before, m.SYNTH_MARKER)

    def test_python36_grammar(self):
        ast.parse(Path(m.__file__).read_text(), feature_version=(3, 6))


if __name__ == '__main__':
    unittest.main()
