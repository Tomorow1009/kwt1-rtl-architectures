import unittest
from pathlib import Path
import tkinter
import s0_partition_synth as mapping
import s0_recovery as recovery


class RecoveryTests(unittest.TestCase):
    def test_only_absent_cell_optimization_directives_removed_not_delays(self):
        timing='set_input_delay 1.23 [get_ports cmd]\nset_output_delay 2.3 [get_ports rsp]\n'
        raw=timing+'set_map_only [get_cells U2055]\nset_map_only [get_cells U2048]\n'
        clean,cells=mapping.remove_mapped_only_directives(raw)
        self.assertEqual(clean,timing)
        self.assertEqual(cells,['U2055','U2048'])
        for bad in ('set_map_only [get_cells *]\n','set_map_only [get_cells U1]; set_false_path -from A\n',
                    'set_map_only [get_cells U1]\nset_map_only [get_cells U1]\n'):
            with self.assertRaises(ValueError):mapping.remove_mapped_only_directives(bad)

    def test_only_observed_errors_and_completed_seed_outputs_eligible(self):
        log=''.join("Warning: Can't find object '%s' in design 'arch03_t80_accel'. (UID-95)\n"%x+
                    "Error: Value for list 'object_list' must have 1 elements. (CMD-036)\n" for x in recovery.CELLS)
        log+='S0_BLOCK_MAPPED accelerator\n'
        recovery.allowed_error_log(log)
        for bad in (log+'Error: other\n',log.replace('U2048','U2049'),
                    log.replace('S0_BLOCK_MAPPED accelerator',''),log+'S0_BLOCK_MAPPED accelerator\n'):
            with self.assertRaises(ValueError):recovery.allowed_error_log(bad)

    def test_seed_is_recompiled_after_original_rtl_absence_check(self):
        script=mapping.block_script(Path('/original'),Path('/new'),'accelerator','arch03_t80_accel',
                                    recovery.CELLS,Path('/failed/mapped.ddc'))
        self.assertEqual(tkinter.Tcl().call('info','complete',script),1)
        self.assertLess(script.index('get_cells -quiet U2055'),script.index('/failed/mapped.ddc'))
        self.assertLess(script.index('get_cells -quiet U2048'),script.index('remove_design -all'))
        self.assertLess(script.index('remove_design -all'),script.index('/failed/mapped.ddc'))
        self.assertNotIn('compile -map_effort high',script)
        self.assertIn('set_fix_hold [all_clocks]\ncompile -incremental_mapping -map_effort high',script)
        self.assertIn('if {![link]} {error "Recovery seed unresolved"}',script)
        self.assertIn('report_timing -delay_type min',script)

    def test_cpu_and_probe_load_all_ddcs_into_one_container(self):
        for script in (mapping.cpu_script(Path('/original'),Path('/new')),
                       mapping.ddc_link_probe_script(Path('/original'),Path('/new'),Path('/seed'))):
            self.assertEqual(tkinter.Tcl().call('info','complete',script),1)
            self.assertNotIn('read_ddc ',script)
            self.assertEqual(script.count('read_file -format ddc -single_file s0_designs '),3)
            self.assertIn('if {![link]}',script)
        probe=mapping.ddc_link_probe_script(Path('/original'),Path('/new'),Path('/seed'))
        self.assertNotIn('compile ',probe)
        self.assertIn('accelerator_probe.v',probe)
        self.assertIn('shared_sram_probe.v',probe)


if __name__=='__main__':unittest.main()
