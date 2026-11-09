import unittest
import tempfile
import json
from pathlib import Path
from soc_synth import area_inventory,constraints,script,require_tool_marker,recover_reports,sha,mapped_exceptions,output_constraints


def inventory():
    rows=[]
    for path,kind,count in [('u_e203_itcm_gnrl_ram','RAMSP4096X16',32),
                            ('u_e203_dtcm_gnrl_ram','RAMSP4096X16',32),
                            ('u_arch03_shared','RAMSP4096X16',64),
                            ('u_arch03_accel','RAMSP4096X16',2),
                            ('u_arch03_accel','RAMSP128X16',8)]:
        rows.extend('top/%s/%s_%d\t%s\t100\tlib/%s'%(path,kind,i,kind,kind) for i in range(count))
    rows.append('top/cpu_reg\tDFF\t2\tlib/DFF')
    rows.append('top/u_arch03_accel/control_reg\tDFF\t2\tlib/DFF')
    return rows


class SocSynthTests(unittest.TestCase):
    def test_output_budgets_cover_every_port_once_in_its_reviewed_domain(self):
        import tkinter
        interp=tkinter.Tcl()
        interp.eval(r'''
proc get_ports {args} {set name [lindex $args end]; if {[lsearch -exact $::ports $name] < 0} {return {}}; return $name}
proc all_outputs {} {return $::ports}
proc sizeof_collection {ports} {llength $ports}
proc add_to_collection {ports port} {concat $ports $port}
proc remove_from_collection {ports removed} {set result {}; foreach p $ports {if {[lsearch -exact $removed $p] < 0} {lappend result $p}}; return $result}
proc get_object_name {ports} {return $ports}
proc set_output_delay {args} {lappend ::delays $args}
proc puts {args} {}
''')
        # Server netlist character 23 is ASCII 111 ('o'), not ASCII 48 ('0').
        lf=('io_pads_aon_pmu_padrst_o_oval','io_pads_aon_pmu_vddpaden_oval','lfxoscen')
        hf=('gpio_output','uart_output','hfclk_output')
        interp.setvar('ports',lf+hf);interp.setvar('delays','');interp.eval(output_constraints())
        rows=[interp.splitlist(row) for row in interp.splitlist(interp.getvar('delays'))]
        for kind,value in (('-max','1.0'),('-min','0.0')):
            selected=[r for r in rows if r[0]==kind]
            self.assertEqual(len(selected),2)
            domains={r[3]:set(interp.splitlist(r[4])) for r in selected}
            self.assertEqual(domains,{'hf_clk':set(hf),'lf_clk':set(lf)})
            self.assertTrue(all(r[1]==value for r in selected))
        interp.setvar('ports',lf[1:]+hf)
        with self.assertRaisesRegex(tkinter.TclError,'Missing/ambiguous LF control output'):
            interp.eval(output_constraints())

    def test_cdc_exceptions_only_reach_four_first_stage_timer_pins(self):
        import tkinter
        interp=tkinter.Tcl()
        interp.eval(r'''
proc get_pins {args} {if {[lindex $args end] eq "__arch03_no_such_pin__"} {return {}}; return $::candidates}
proc get_ports {name} {return $name}
proc get_object_name {pin} {return $pin}
proc sizeof_collection {pins} {llength $pins}
proc add_to_collection {pins pin} {lappend pins $pin;return $pins}
proc foreach_in_collection {name pins body} {foreach pin $pins {uplevel 1 [list set $name $pin]; uplevel 1 $body}}
proc set_false_path {args} {set ::exception $args}
proc puts {args} {}
''')
        pins=['top/u_perips_apb_pwm/u_tim%d/u_in_stage/r_ls_clk_sync_reg[%d]/D'%(timer,stage)
              for timer in range(4) for stage in range(3)]
        pins+=['top/other/u_tim0/u_in_stage/r_ls_clk_sync_reg[0]/D']
        interp.setvar('candidates',tuple(pins));interp.eval(mapped_exceptions())
        actual=interp.splitlist(interp.getvar('exception'))
        self.assertEqual(actual[0:3],('-from','lfextclk','-to'))
        self.assertEqual(set(interp.splitlist(actual[3])),set(pins[::3][:-1]))
        interp.setvar('candidates',tuple(pins[1:]))
        with self.assertRaisesRegex(tkinter.TclError,'Expected four reviewed'):interp.eval(mapped_exceptions())

    def test_recovery_preserves_failed_run_and_negative_timing_and_rejects_changed_sources(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);old=root/'old';current=root/'current'
            origin=old/'runs/failed/asic_synth';origin.mkdir(parents=True)
            files=['workspaces/arch03/scripts/'+n for n in ('install_platform.py','technology_binding.py',
                    'memory_technology.py','timing_contract.py')]
            files+=['workspaces/arch03/technology_bindings.json','workspaces/arch03/memory_technology.json',
                    'workspaces/arch03/rtl/example.sv']
            for bundle in (old,current):
                for name in files:
                    path=bundle/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text('original')
                (bundle/'manifest.json').write_text(json.dumps({'source_commit':'original_commit',
                    'files':{name:sha(bundle/name) for name in files}}))
            state={'stages':{'asic_synth':{'status':'failed','error':'Whole-SoC report collection incomplete'}}}
            (origin.parent/'state.json').write_text(json.dumps(state))
            marker='ARCH03_SOC_SYNTH_REPORTS_READY timing_verified=false scoring_area_verified=false'
            (origin/'soc_synth.log').write_text('puts "'+marker+'"\n'+marker+'\n')
            (origin/'dc_link.log').write_text('ARCH03_ASIC_LINK_READY whole_soc=true synthesis_verified=false timing_verified=false\n')
            (origin/'task_mode.sdc').write_text(constraints())
            (origin/'metrics.txt').write_text('period_ns 6.666666\nlf_period_ns 66\nRAMSP128X16 8\nRAMSP4096X16 130\nmax -1.77\nmin -0.09\n')
            (origin/'area.rpt').write_text('Total cell area: 13804\n')
            (origin/'leaf_area.tsv').write_text('\n'.join(inventory()))
            (origin/'source_inputs.json').write_text(json.dumps({str(old/files[-1]):sha(old/files[-1])}))
            for name in ('mapped.v','mapped.ddc','mapped.sdc','check_timing.rpt','constraints.rpt','timing_max.rpt','timing_min.rpt'):
                (origin/name).write_text('original tool artifact')
            (origin/'libs').mkdir()
            for name in ('standard.db','small.db','large.db'):(origin/'libs'/name).write_text(name)
            before={str(p):sha(p) for p in old.rglob('*') if p.is_file()}
            run=current/'runs/recovery/asic_synth';run.mkdir(parents=True)
            result=recover_reports({'server_root':str(root)},run,origin,current)
            self.assertTrue(result['synthesis_completed'])
            self.assertFalse(result['setup_hold_nonnegative'])
            self.assertFalse(result['timing_verified'])
            self.assertFalse(result['report_recovery']['synthesis_reexecuted'])
            self.assertEqual(before,{str(p):sha(p) for p in old.rglob('*') if p.is_file()})
            for name in (files[-2],files[-1]):
                (current/name).write_text('changed')
                with self.assertRaises(ValueError):recover_reports({'server_root':str(root)},run,origin,current)
                (current/name).write_text('original')
            (old/files[-1]).write_text('changed original')
            with self.assertRaises(ValueError):recover_reports({'server_root':str(root)},run,origin,current)

    def test_echoed_proc_marker_is_not_execution_and_errors_still_fail(self):
        marker='ARCH03_TEST_REPORT_READY'
        echo='proc collect {} {\n    puts "'+marker+'"\n}\n'
        require_tool_marker(echo+marker+'\n',marker)
        for bad in (echo,marker+'\n'+marker,echo+marker+'\nError: invalid constraints'):
            with self.assertRaises(ValueError):require_tool_marker(bad,marker)

    def test_constraint_error_stops_tcl_before_compile(self):
        try:
            import tkinter
        except ImportError:
            self.skipTest('Tcl interpreter unavailable')
        interp=tkinter.Tcl()
        interp.eval(r'''
set compiled 0
set sh_continue_on_error true
proc set_app_var {name value} {set ::$name $value}
proc read_ddc {args} {}
proc current_design {args} {}
proc link {} {return 1}
proc get_cells {args} {return [lrepeat 138 cell]}
proc sizeof_collection {c} {llength $c}
proc set_dont_touch {args} {}
proc create_clock {args} {}
proc set_clock_uncertainty {args} {}
proc all_clocks {} {return {hf_clk lf_clk}}
proc get_ports {args} {return {}}
proc source {path} {
    if {[catch {uplevel 1 $::test_sdc} message]} {
        if {!$::sh_continue_on_error} {error $message}
    }
}
proc compile {args} {set ::compiled 1}
proc puts {args} {set ::last_message $args}
proc exit {code} {error "TASK_EXIT $code"}
proc quit {} {error UNEXPECTED_QUIT}
''')
        interp.setvar('test_sdc',constraints())
        with tempfile.TemporaryDirectory() as directory:
            run=Path(directory);(run/'libs').mkdir()
            for name in ('small.db','large.db'):(run/'libs'/name).touch()
            generated=script(run,{'standard_library_member':'standard.db'})
            self.assertEqual(interp.call('info','complete',generated),1)
            with self.assertRaisesRegex(tkinter.TclError,'TASK_EXIT 1'):interp.eval(generated)
        self.assertEqual(int(interp.getvar('compiled')),0)
        self.assertFalse(interp.getboolean(interp.getvar('sh_continue_on_error')))
        self.assertIn('Missing task-mode port io_pads_aon_erst_n_i_ival',str(interp.getvar('last_message')))

    def test_partition_counts_area_once_and_does_not_decide_scoring(self):
        result=area_inventory('\n'.join(inventory()),13804)
        self.assertEqual(result['whole_system_library_area'],13804)
        self.assertEqual(result['groups']['accelerator']['sram_count'],10)
        self.assertEqual(result['groups']['shared']['sram_area'],6400)
        self.assertEqual(result['groups']['accelerator']['standard_cell_area'],2)
        self.assertIsNone(result['official_scoring_area'])
        self.assertFalse(result['scoring_area_verified'])

    def test_missing_duplicate_reassigned_and_invalid_areas_fail(self):
        rows=inventory()
        for bad in (rows[:-3],rows+[rows[0]],
                    [r.replace('u_arch03_shared','unclassified') for r in rows],
                    [rows[0].replace('\t100\t','\tnan\t')]+rows[1:],
                    [rows[0].replace('\t100\t','\t0\t')]+rows[1:]):
            with self.assertRaises(ValueError):area_inventory('\n'.join(bad),13804)
        with self.assertRaises(ValueError):area_inventory('\n'.join(rows),12000)

    def test_constraints_keep_cross_clock_paths_and_strict_frequency(self):
        commands='\n'.join(s for s in constraints().splitlines() if not s.lstrip().startswith('#'))
        self.assertIn('-period 6.666666 ',commands)
        self.assertIn('-period 66.0',commands)
        for forbidden in ('set_false_path','set_multicycle_path','set_clock_groups'):
            self.assertNotIn(forbidden,commands)
        self.assertIn('Missing/ambiguous clock mode pin',commands)
        self.assertIn('io_pads_aon_erst_n_i_ival 1',commands)
        self.assertIn('io_pads_aon_pmu_dwakeup_n_i_ival 1',commands)
        self.assertIn('io_pads_jtag_TCK_i_ival 0',commands)

    def test_virtual_constants_are_separate_and_cannot_hide_unmapped_cells(self):
        base=inventory()
        virtual='top/const0\t**logic_0**\t0\tbuiltin_logic_constant'
        result=area_inventory('\n'.join(base+[virtual]),13804)
        self.assertEqual(result['groups']['platform_other']['virtual_constant_count'],1)
        self.assertEqual(result['groups']['platform_other']['standard_cell_count'],1)
        self.assertEqual(result['whole_system_library_area'],13804)
        for bad in (virtual.replace('logic_0','logic_x'),virtual.replace('\t0\t','\t1\t'),
                    virtual.replace('\t0\t','\tnan\t'),virtual.replace('builtin_logic_constant','lib/FAKE'),
                    'top/unknown\tUNKNOWN\t2\tbuiltin_logic_constant'):
            with self.assertRaises(ValueError):area_inventory('\n'.join(base+[bad]),13804)


if __name__=='__main__':unittest.main()
