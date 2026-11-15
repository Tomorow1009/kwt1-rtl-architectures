import tempfile
from pathlib import Path
import unittest
import tkinter
import s0_partition_synth as s


class S0MappingTests(unittest.TestCase):
    def test_native_clock_precision_restoration_retains_boundary_constraints(self):
        native='hf_clk\t6.666666031\t0\t3.3333330155\nlf_clk\t66\t0\t33\n'
        raw='set_input_delay -clock hf_clk 1.76543 [get_ports cmd]\ncreate_clock [get_ports clk] -name "hf_clk" -period 6.66667 -waveform {0 3.33333}\ncreate_clock -name lf_clk -period 66 -waveform {0 33} [get_ports lf]\nset_clock_uncertainty 0.1 [get_clocks hf_clk]\n'
        exact=s.restore_clock_precision(raw,native)
        self.assertEqual(exact.replace('6.666666031','6.66667').replace('3.3333330155','3.33333'),raw)
        self.assertEqual(s.restore_clock_precision(exact,native),exact)
        for bad in (raw.replace('6.66667','7.0'),raw+raw,raw.replace('-name "hf_clk"','-name unknown'),raw.replace('-waveform {0 3.33333}','')):
            with self.assertRaises(ValueError):s.restore_clock_precision(bad,native)
        with self.assertRaises(ValueError):s.restore_clock_precision(raw,native.replace('6.666666031','6.667'))

    def test_dc_startup_version_retains_build_and_rejects_ambiguity(self):
        self.assertEqual(s.tool_version_from_banner('Version T-2022.03-SP5-5 for linux64'), 'T-2022.03-SP5-5')
        self.assertEqual(s.tool_version_from_banner('Version Q-2020.03-SP2\nVersion Q-2020.03-SP2'), 'Q-2020.03-SP2')
        for bad in ('dc_shell version - T-2022.03-SP5-5', 'Version T-2022.03-SP5\nVersion T-2022.03-SP5-5'):
            with self.assertRaises(ValueError): s.tool_version_from_banner(bad)

    def test_child_compare_checks_connection_changes_and_duplicate_definitions(self):
        with tempfile.TemporaryDirectory() as d:
            a=Path(d)/'a.v';b=Path(d)/'b.v'
            text='module foo (a,b); input a; output b; BUF g (.A(a),.Z(b)); endmodule'
            a.write_text(text);b.write_text('// changed timestamp\n'+text.replace(';',';\n'))
            self.assertTrue(s.same_blocks(a,b)['equal_tokens'])
            b.write_text(text.replace('.A(a)','.A(b)'))
            with self.assertRaises(ValueError):s.same_blocks(a,b)
            with self.assertRaises(ValueError):s.module_tokens(text+'\n'+text)

    def test_escaped_identifiers_are_not_merged_by_whitespace_normalization(self):
        self.assertNotEqual(s.module_tokens('module a (a); wire \\x.y ; endmodule'),
                            s.module_tokens('module a (a); wire \\x .y; endmodule'))

    def test_final_link_reloads_three_ddcs_without_compiling_or_fixing_nets(self):
        with tempfile.TemporaryDirectory() as d:
            run=Path(d);(run/'libs').mkdir();origin=run/'original';(origin/'libs').mkdir(parents=True)
            for name in ('standard.db','small.db','large.db'):
                (run/'libs'/name).touch();(origin/'libs'/name).touch()
            text=s.top_script(origin,run,{'standard_library_member':'standard.db'})
            active='\n'.join(x for x in text.splitlines() if not x.lstrip().startswith('#'))
            self.assertNotIn('compile ',active)
            self.assertNotIn('set_fix_multiple_port_nets',active)
            self.assertIn('cpu_soc/mapped.ddc',active)
            self.assertIn('accelerator/mapped.ddc',active)
            self.assertIn('shared_sram/mapped.ddc',active)
            self.assertIn('s0_export u_arch03_accel accelerator_after_link.v',active)
            self.assertIn('report_timing -through $pins -delay_type min',active)
            self.assertIn('write -format ddc -hierarchy -output mapped.ddc',active)
            self.assertIn('{'+str(origin/'libs'/'standard.db')+'}',active)
            self.assertNotIn('{'+str(run/'libs'/'standard.db')+'}',active)
            self.assertEqual(tkinter.Tcl().call('info','complete',text),1)

    def test_blocks_use_baseline_context_and_cpu_preserves_them(self):
        text=s.block_script(Path('/old'),Path('/new'),'accelerator','arch03_t80_accel')
        self.assertIn('/old/linked.ddc',text)
        self.assertIn('/new/characterization/accelerator.characterized.tcl',text)
        self.assertNotIn('create_clock',text)
        self.assertNotIn('set_false_path',text)
        self.assertIn('!= 92',text)
        cpu=s.cpu_script(Path('/old'),Path('/new'))
        self.assertLess(cpu.index('set_dont_touch [get_cells [lindex $pair 0]] true'),cpu.index('compile -map_effort high'))
        self.assertIn('accelerator_after_cpu.v',cpu)
        for generated in (text,cpu):self.assertEqual(tkinter.Tcl().call('info','complete',generated),1)

    def test_characterization_requires_both_complete_unique_boundaries(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'inventory.tsv'
            rows='accelerator\ttop/u_arch03_accel\tarch03_t80_accel\t50\t60\nshared_sram\ttop/u_arch03_shared\tshared\t32\t32\n'
            p.write_text(rows);self.assertEqual(len(s.characterize_inventory(p)),2)
            p.write_text(rows.splitlines()[0]+'\n')
            with self.assertRaises(ValueError):s.characterize_inventory(p)
            p.write_text(rows+rows)
            with self.assertRaises(ValueError):s.characterize_inventory(p)


if __name__=='__main__':unittest.main()
