"""Fail-closed boundary compatibility and fresh P80 mapping provenance tests."""
from pathlib import Path
import tempfile
import tkinter
import unittest

import p80_link
import p80_partition_synth as p


class P80MappingTests(unittest.TestCase):
    def test_fresh_link_contains_source_compile_and_bit_port_inventory(self):
        text=p80_link.link_script(Path('/new/std.db'),[Path('/new/a.db'),Path('/new/b.db')],
            [Path('/new/arch03_p80_accel.sv'),Path('/new/arch03_icb_arb2_queued.sv')],[Path('/new')])
        self.assertIn('analyze -format sverilog -define SYNTHESIS',text)
        self.assertIn('elaborate e203_soc_top',text)
        self.assertNotIn('read_ddc',text)
        self.assertNotIn('arch03_t80_accel',text)
        self.assertIn('linked_boundaries.tsv',text)
        self.assertIn('${block}.linked_ports.tsv',text)
        self.assertIn(p80_link.MARKER,text)
        self.assertEqual(tkinter.Tcl().call('info','complete',text),1)

    def test_budget_changes_selector_not_io_or_case_constraints(self):
        native='hf_clk\t6.666666031\t0\t3.3333330155\n'
        raw=('current_design {arch03_t80_accel}\n'
             'create_clock -name hf_clk -period 6.66667 -waveform {0 3.33333} [get_ports clk]\n'
             'set_input_delay -clock hf_clk 2.1432 [get_ports dma_rsp_valid]\n'
             'set_output_delay -clock hf_clk 1.128 [get_ports dma_cmd_valid]\n'
             'set_load 0.016 [get_ports dma_cmd_valid]\nset_case_analysis 0 [get_ports rst_n]\n'
             'set_map_only [get_cells U31]\n')
        out,removed=p.translated_budget(raw,native,'arch03_t80_accel','arch03_p80_accel_TRANSACTION_DEPTH4')
        self.assertEqual(removed,['U31'])
        self.assertIn('current_design arch03_p80_accel_TRANSACTION_DEPTH4',out)
        for line in raw.splitlines()[2:-1]:self.assertIn(line,out)
        for bad in (raw.replace('current_design {arch03_t80_accel}','current_design wrong'),
                    raw+'current_design arch03_t80_accel\n',raw+'set_false_path -from [get_cells arch03_t80_accel]\n'):
            with self.assertRaises(ValueError):p.translated_budget(bad,native,'arch03_t80_accel','arch03_p80_accel')

    def test_bit_ports_reject_width_direction_and_duplicate_substitution(self):
        with tempfile.TemporaryDirectory() as root:
            a=Path(root)/'a';b=Path(root)/'b'
            a.write_text('a[0]\tin\na[1]\tin\nb\tout\n')
            b.write_text('a[0]\tinput\na[1]\tinput\nb\toutput\n')
            self.assertEqual(p.ports(a),p.ports(b))
            b.write_text('a[0]\tin\nb\tout\n');self.assertNotEqual(p.ports(a),p.ports(b))
            b.write_text('a[0]\tin\na[1]\tout\nb\tout\n');self.assertNotEqual(p.ports(a),p.ports(b))
            for bad in ('a\tin\na\tin\n','a\tunknown\n',''):
                b.write_text(bad)
                with self.assertRaises(ValueError):p.ports(b)

    def test_budget_probe_is_readonly_and_keeps_separate_libraries(self):
        text=p.characterization_script(Path('/old/s0'),Path('/new/p80'))
        self.assertIn('read_ddc {/old/s0/mapped.ddc}',text)
        self.assertIn('/new/p80/budget_libraries.tcl',text)
        self.assertIn('${block}.budget_ports.tsv',text)
        self.assertNotIn('compile ',text)
        self.assertNotIn('write -format ddc',text)
        self.assertEqual(tkinter.Tcl().call('info','complete',text),1)


if __name__=='__main__':unittest.main()
