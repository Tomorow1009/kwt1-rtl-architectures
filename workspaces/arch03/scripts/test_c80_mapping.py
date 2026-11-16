"""Fail-closed boundary compatibility and fresh C80 mapping provenance tests."""
from pathlib import Path
import tempfile
import tkinter
import unittest

import c80_link
import c80_partition_synth as p


class C80MappingTests(unittest.TestCase):
    def test_fresh_link_contains_source_compile_and_bit_port_inventory(self):
        text=c80_link.link_script(Path('/new/std.db'),[Path('/new/a.db'),Path('/new/b.db')],
            [Path('/new/arch03_c80_accel.sv'),Path('/new/arch03_icb_arb2_queued.sv')],[Path('/new')])
        self.assertIn('analyze -format sverilog -define SYNTHESIS',text)
        self.assertIn('elaborate e203_soc_top',text)
        self.assertNotIn('read_ddc',text)
        self.assertNotIn('arch03_t80_accel',text)
        self.assertIn('linked_boundaries.tsv',text)
        self.assertIn('${block}.linked_ports.tsv',text)
        self.assertIn(c80_link.MARKER,text)
        self.assertEqual(tkinter.Tcl().call('info','complete',text),1)

    def test_budget_changes_selector_not_io_or_case_constraints(self):
        native='hf_clk\t6.666666031\t0\t3.3333330155\n'
        raw=('current_design {arch03_t80_accel}\n'
             'create_clock -name hf_clk -period 6.66667 -waveform {0 3.33333} [get_ports clk]\n'
             'set_input_delay -clock hf_clk 2.1432 [get_ports dma_rsp_valid]\n'
             'set_output_delay -clock hf_clk 1.128 [get_ports dma_cmd_valid]\n'
             'set_load 0.016 [get_ports dma_cmd_valid]\nset_case_analysis 0 [get_ports rst_n]\n'
             'set_map_only [get_cells U31]\n')
        out,removed=p.translated_budget(raw,native,'arch03_t80_accel','arch03_c80_accel_TRANSACTION_DEPTH4')
        self.assertEqual(removed,['U31'])
        self.assertIn('current_design arch03_c80_accel_TRANSACTION_DEPTH4',out)
        for line in raw.splitlines()[2:-1]:self.assertIn(line,out)
        for bad in (raw.replace('current_design {arch03_t80_accel}','current_design wrong'),
                    raw+'current_design arch03_t80_accel\n',raw+'set_false_path -from [get_cells arch03_t80_accel]\n'):
            with self.assertRaises(ValueError):p.translated_budget(bad,native,'arch03_t80_accel','arch03_c80_accel')

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
        text=p.characterization_script(Path('/old/s0'),Path('/new/c80'))
        self.assertIn('read_ddc {/old/s0/mapped.ddc}',text)
        self.assertIn('/new/c80/budget_libraries.tcl',text)
        self.assertIn('${block}.budget_ports.tsv',text)
        self.assertNotIn('compile ',text)
        self.assertNotIn('write -format ddc',text)
        self.assertEqual(tkinter.Tcl().call('info','complete',text),1)

    def test_exported_driving_library_is_rebound_without_changing_arc_or_delays(self):
        line=('set_driving_cell -rise -lib_cell NOR2V2_12TR40 -library ss_corner.db:ss_corner '
              '-pin ZN -from_pin A2 -input_transition_rise 0.26123 '
              '-input_transition_fall 0.231548 -no_design_rule [get_ports {cmd_addr[31]}]\n')
        tail='set_input_delay -clock hf_clk 1.256 [get_ports cmd_valid]\nset_load 0.03 [get_ports rsp_data]\n'
        text,rows=p.driving_library_budget(line+tail,Path('/new/libs/ss_corner.db'))
        self.assertTrue(text.endswith(line.replace('ss_corner.db:ss_corner','ss_corner')+tail))
        self.assertEqual(rows[0]['cell'],'NOR2V2_12TR40')
        self.assertEqual(rows[0]['from_pin'],'A2')
        self.assertIn('get_lib_cells -quiet ss_corner/NOR2V2_12TR40',text)
        self.assertIn('get_lib_pins -quiet ss_corner/NOR2V2_12TR40/ZN',text)
        self.assertEqual(tkinter.Tcl().call('info','complete',text),1)
        for bad in ('other.db:ss_corner','ss_corner.db:other','{ss_corner}',
                    '/unknown/ss_corner.db:ss_corner'):
            with self.assertRaises(ValueError):
                p.driving_library_budget(line.replace('ss_corner.db:ss_corner',bad),Path('/new/ss_corner.db'))
        with self.assertRaises(ValueError):p.driving_library_budget(tail,Path('/new/ss_corner.db'))

    def test_plain_driving_library_keeps_original_command(self):
        raw='set_driving_cell -lib_cell INV2 -library ss_corner -pin ZN -from_pin I [get_ports valid]\n'
        result,rows=p.driving_library_budget(raw,Path('/new/ss_corner.db'))
        self.assertTrue(result.endswith(raw))
        self.assertEqual(rows[0]['original_line'],rows[0]['effective_line'])

    def test_old_local_library_rebound_only_after_identical_bytes(self):
        with tempfile.TemporaryDirectory() as root:
            old=Path(root)/'old'/'ss_corner.db';new=Path(root)/'fresh'/'ss_corner.db'
            old.parent.mkdir();new.parent.mkdir();old.write_bytes(b'exact DB');new.write_bytes(b'exact DB')
            prefix='set_operating_conditions ss -library ss_corner.db:ss_corner\n'
            suffix='set_input_delay -clock hf_clk 1.234 [get_ports valid]\nset_load 0.03 [get_ports out]\n'
            raw=prefix+'set_local_link_library {'+old.as_posix()+'}\n'+suffix
            text,rows=p.local_link_library_budget(raw,new)
            self.assertEqual(text,prefix+'set_local_link_library '+p.tcl_path(new.resolve())+'\n'+suffix)
            self.assertEqual(len(rows),1);self.assertFalse(rows[0]['library_bytes_changed'])
            self.assertEqual(rows[0]['sha256'],p.digest(new))
            self.assertEqual(tkinter.Tcl().call('info','complete',text),1)
            new.write_bytes(b'different DB')
            with self.assertRaises(ValueError):p.local_link_library_budget(raw,new)

    def test_local_library_rejects_missing_duplicate_or_nonliteral_paths(self):
        with tempfile.TemporaryDirectory() as root:
            db=Path(root)/'ss_corner.db';db.write_bytes(b'exact DB')
            good='set_local_link_library {'+db.as_posix()+'}\n'
            for bad in ('',good+good,'set_local_link_library [list '+db.as_posix()+']\n',
                        good.replace(db.as_posix(),db.as_posix()+' /extra.db'),
                        good.replace(db.as_posix(),'$target_library'),
                        good.replace(db.as_posix(),'missing.db')):
                with self.subTest(bad=bad),self.assertRaises(ValueError):p.local_link_library_budget(bad,db)


if __name__=='__main__':unittest.main()
