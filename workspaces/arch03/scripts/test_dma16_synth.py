"""Offline contract tests; no EDA run or synthetic timing acceptance."""
import ast
import json
import tempfile
import unittest
from pathlib import Path
import tkinter
import dma16_synth as d
from install_dma16 import FIELDS, MASTER_OUTPUTS


def top(ansi=False):
    ports = []
    for name, (direction, width) in sorted(d.SYSMEM.items()):
        ports.append('%s wire %ssysmem_icb_%s' % ('input' if direction == 'in' else 'output',
                     '' if width == 1 else '[%d:0] ' % (width-1), name))
    if ansi:
        return 'module e203_soc_top(\n'+',\n'.join(ports)+'\n); endmodule\n'
    return 'module e203_soc_top();\n'+';\n'.join(ports)+';\nendmodule\n'


def inventory():
    areas = json.loads(d.METADATA.read_text())['cells']
    roots = dict(itcm='u_e203_itcm_gnrl_ram', dtcm='u_e203_dtcm_gnrl_ram',
                 shared='u_arch03_shared', accelerator='u_arch03_accel')
    rows = []
    for (owner, ref), count in d.MACROS.items():
        rows.extend('top/%s/%s_%d\t%s\t%.8f\tlib/%s' %
                    (roots[owner], ref, i, ref, areas[ref]['area'], ref) for i in range(count))
    for path, area in [('cpu', 10), ('u_e203_itcm_gnrl_ram', 2), ('u_e203_dtcm_gnrl_ram', 3),
                       ('u_arch03_accel', 4), ('u_arch03_arb', 5), ('u_arch03_router', 6), ('u_arch03_shared', 7)]:
        rows.append('top/%s/reg\tDFF\t%d\tlib/DFF' % (path, area))
    return rows


def total(rows):
    return sum(float(line.split('\t')[2]) for line in rows)


def write_library_receipts(run):
    (run/'technology_verification.json').write_text(json.dumps(
        {'library_sha256': d.load_bindings()['library_sha256']}))
    memory = json.loads(d.METADATA.read_text())['cells']
    (run/'memory_library_verification.json').write_text(json.dumps([
        dict(cell=cell, sha256=spec['sha256'], library_area=spec['area']) for cell, spec in memory.items()]))


def constraint_interpreter():
    t = tkinter.Tcl()
    t.eval(r'''
proc get_ports {args} {
    set query [lindex $args end];set result {}
    if {$query eq "sysmem_icb_*"} {
        foreach p $::ports {if {[string first sysmem_icb_ $p] == 0} {lappend result $p}}
    } else {foreach p $query {if {[lsearch -exact $::ports $p] >= 0} {lappend result $p}}}
    return $result
}
proc all_inputs {} {return $::inputs}
proc all_outputs {} {return $::outputs}
proc sizeof_collection {c} {llength $c}
proc remove_from_collection {ports removed} {
    set result {}; foreach p $ports {if {[lsearch -exact $removed $p] < 0} {lappend result $p}};return $result
}
proc add_to_collection {ports port} {concat $ports $port}
proc get_object_name {p} {return $p}
proc get_attribute {p a} {return $::directions($p)}
proc foreach_in_collection {name collection body} {
    foreach item $collection {uplevel 1 [list set $name $item];uplevel 1 $body}
}
proc get_pins {args} {return {mode_pin}}
proc get_clocks {args} {return {hf_clk lf_clk}}
proc all_clocks {} {return {hf_clk lf_clk}}
proc create_clock {args} {lappend ::clocks $args}
proc set_clock_uncertainty {args} {}
proc set_case_analysis {args} {}
proc set_input_delay {args} {lappend ::input_delays $args}
proc set_output_delay {args} {lappend ::output_delays $args}
proc set_input_transition {args} {set ::transition $args}
proc set_load {args} {set ::load $args}
proc open {args} {return report_sink}
proc close {args} {}
proc puts {args} {}
''')
    # Existing output names come from the independently captured server fixture.
    old = json.loads((Path(__file__).with_name('test_fixtures')/'e203_soc_top_outputs.json').read_text())['outputs']
    inputs = ['hfextclk', 'lfextclk', 'io_pads_aon_erst_n_i_ival', 'io_pads_aon_pmu_dwakeup_n_i_ival',
              'io_pads_bootrom_n_i_ival']+['io_pads_dbgmode%d_n_i_ival' % n for n in range(3)]+[
              'io_pads_jtag_%s_i_ival' % n for n in ('TCK', 'TMS', 'TDI')]
    bits = d.sysmem_bits()
    inputs += [p for p in bits if bits[p] == 'in']
    outputs = old+[p for p in bits if bits[p] == 'out']
    t.setvar('inputs', tuple(inputs)); t.setvar('outputs', tuple(outputs)); t.setvar('ports', tuple(inputs+outputs))
    directions = []
    for p in inputs+outputs:
        directions += [p, 'in' if p in inputs else 'out']
    t.setvar('direction_list', tuple(directions)); t.eval('array set directions $::direction_list')
    for var in ('input_delays', 'output_delays', 'clocks'):
        t.setvar(var, '')
    return t, inputs, outputs


class Dma16SynthesisTests(unittest.TestCase):
    def test_installer_matches_independent_sysmem_contract(self):
        actual = {name: ('out' if name in MASTER_OUTPUTS else 'in', width) for name, width in FIELDS}
        self.assertEqual(actual, d.SYSMEM)
        self.assertEqual(len(d.sysmem_bits()), 106)

    def test_prior_netlist_is_rejected_before_install_or_tool_call(self):
        with tempfile.TemporaryDirectory() as directory:
            run = Path(directory); (run/'linked.ddc').write_text('old architecture netlist')
            def forbidden_call(*args):
                self.fail('Tool call must not run for a stale directory')
            with self.assertRaisesRegex(ValueError, 'fresh run'):
                d.synth({}, run, Path('not_a_platform'), forbidden_call)

    def test_all_sysmem_bits_receive_same_hf_budgets(self):
        t, inputs, outputs = constraint_interpreter()
        t.eval(d.constraints())
        # This second call detects stale Tcl arrays left from the SDC guard.
        t.eval(d.port_guard('mapped_sysmem_ports.tsv'))
        for kind in ('in', 'out'):
            var = 'input_delays' if kind == 'in' else 'output_delays'
            records = [t.splitlist(r) for r in t.splitlist(t.getvar(var))]
            wanted = {p for p, direction in d.sysmem_bits().items() if direction == kind}
            for bound, value in (('-max', '1.0'), ('-min', '0.0')):
                hit = [r for r in records if r[0] == bound and r[3] == 'hf_clk']
                self.assertEqual(len(hit), 1)
                self.assertEqual(hit[0][1], value)
                self.assertTrue(wanted <= set(t.splitlist(hit[0][4])))
        self.assertEqual(t.splitlist(t.getvar('transition'))[0], '0.1')
        self.assertEqual(t.splitlist(t.getvar('load'))[0], '0.01')

    def test_missing_wrong_direction_and_untimed_sysmem_bits_rejected(self):
        bit = 'sysmem_icb_rsp_rdata[17]'
        for fault in ('missing', 'direction', 'untimed'):
            t, inputs, outputs = constraint_interpreter()
            if fault == 'missing':
                t.setvar('ports', tuple(p for p in inputs+outputs if p != bit))
            elif fault == 'direction':
                t.setvar('directions('+bit+')', 'out')
            else:
                t.setvar('inputs', tuple(p for p in inputs if p != bit))
            with self.subTest(fault=fault), self.assertRaises(tkinter.TclError):
                t.eval(d.constraints())

    def test_ansi_and_mapped_headers_require_real_port_widths_and_directions(self):
        for ansi in (False, True):
            text = top(ansi)
            d.verify_top_sysmem(text)
            for bad in (text.replace('[31:0] sysmem_icb_rsp_rdata', '[30:0] sysmem_icb_rsp_rdata'),
                        text.replace('[31:0] sysmem_icb_rsp_rdata', '[32:1] sysmem_icb_rsp_rdata'),
                        text.replace('input wire sysmem_icb_cmd_ready', 'output wire sysmem_icb_cmd_ready'),
                        text.replace('sysmem_icb_rsp_err', 'old_zero_rsp_err')):
                with self.assertRaises(ValueError):
                    d.verify_top_sysmem(bad)

    def test_actual_installer_patch_is_accepted_as_ansi(self):
        from install_dma16 import patch_soc
        original = 'module e203_soc_top(input hfextclk);\nwire sysmem_icb_cmd_valid;\nwire sysmem_icb_cmd_ready;\n'
        old = dict(cmd_valid='sysmem_icb_cmd_valid', cmd_ready='sysmem_icb_cmd_ready', cmd_addr='', cmd_read='',
                   cmd_wdata='', cmd_wmask='', rsp_valid='sysmem_icb_cmd_valid', rsp_ready='sysmem_icb_cmd_ready',
                   rsp_rdata="32'b0", rsp_err="1'b0")
        original += 'subsystem u('+','.join('.sysmem_icb_%s(%s)' % p for p in old.items())+');\nendmodule'
        d.verify_top_sysmem(patch_soc(original))

    def test_area_counts_all_new_logic_and_reports_reused_macros(self):
        rows = inventory(); result = d.area_inventory('\n'.join(rows), total(rows))
        self.assertEqual(result['physical_sram_bytes'], 1048*1024)
        self.assertEqual(result['macro_count'], 162)
        self.assertEqual(result['groups']['accelerator']['sram_count'], 34)
        self.assertEqual(result['groups']['dma_arbiter']['standard_cell_area'], 5)
        self.assertEqual(result['groups']['dma_router']['standard_cell_area'], 6)
        self.assertAlmostEqual(result['conservative_budget_library_area']-result['known_added_library_area'], 15)
        self.assertIsNone(result['official_scoring_area_mm2'])
        self.assertFalse(result['scoring_area_verified'])

    def test_area_rejects_old_macro_count_missing_added_logic_and_fake_area(self):
        rows = inventory()
        bad_cases = [rows+[rows[0]], rows[1:],
                     [r for r in rows if '/u_arch03_arb/' not in r],
                     [r.replace('/u_arch03_router/', '/fixed_bus/') for r in rows],
                     [r.replace('/u_arch03_shared/', '/fixed_shared/') for r in rows],
                     [rows[0].replace('27517.31680000', '1.0')]+rows[1:],
                     [rows[0].replace('27517.31680000', 'nan')]+rows[1:]]
        for bad in bad_cases:
            with self.assertRaises(ValueError):
                d.area_inventory('\n'.join(bad), total(rows))

    def test_area_units_only_reused_for_identical_library_fingerprints(self):
        with tempfile.TemporaryDirectory() as directory:
            run = Path(directory); write_library_receipts(run)
            basis = d.area_basis(run)
            self.assertFalse(basis['prior_macro_counts_reused'])
            self.assertEqual(basis['units'], 'um^2')
            (run/'technology_verification.json').write_text(json.dumps({'library_sha256': 'bad'}))
            with self.assertRaisesRegex(ValueError, 'different standard library'):
                d.area_basis(run)
            write_library_receipts(run)
            path = run/'memory_library_verification.json'; data = json.loads(path.read_text())
            data[0]['sha256'] = 'wrong'; path.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, 'fingerprint mismatch'):
                d.area_basis(run)

    def test_negative_slack_never_becomes_timing_acceptance(self):
        with tempfile.TemporaryDirectory() as directory:
            run = Path(directory); write_library_receipts(run); rows = inventory()
            (run/'metrics.txt').write_text('period_ns 6.666666\nlf_period_ns 66\nRAMSP128X16 32\nRAMSP4096X16 130\nmax -0.7\nmin 0.01\nlatches 0\n')
            (run/'area.rpt').write_text('Total cell area: %.9f\n' % total(rows))
            (run/'leaf_area.tsv').write_text('\n'.join(rows))
            for name in ('mapped_sysmem_ports.tsv', 'sysmem_ports.tsv'):
                (run/name).write_text('\n'.join('%s\t%s' % p for p in d.sysmem_bits().items()))
            for name in ('mapped.ddc', 'mapped.sdc', 'check_timing.rpt', 'constraints.rpt', 'timing_max.rpt',
                         'timing_min.rpt', 'check_design_mapped.rpt', 'references_mapped.rpt', 'qor.rpt',
                         'hierarchy.rpt', 'mapped_probe_inventory.tsv'):
                (run/name).write_text('synthetic test artifact, not tool evidence')
            (run/'check_timing.rpt').write_text('Information: Checking loops...\n')
            (run/'mapped.v').write_text(top())
            result = d.collect_reports(run, {}, {}, d.SYNTH_MARKER)
            self.assertEqual(result['status'], 'reports_ready_review_required')
            self.assertFalse(result['setup_hold_nonnegative'])
            for flag in ('timing_verified', 'scoring_area_verified', 'gate_simulation_verified', 'system_power_verified'):
                self.assertFalse(result[flag])
            before = {str(run/'mapped.v'): d.sha(run/'mapped.v')}
            (run/'mapped.v').write_text(top()+'// changed')
            with self.assertRaisesRegex(ValueError, 'input changed'):
                d.collect_reports(run, {}, before, d.SYNTH_MARKER)

    def test_link_failure_aborts_before_elaboration(self):
        t = tkinter.Tcl()
        t.eval(r'''
set search_path {};set elaborated 0
proc set_app_var {name value} {set ::$name $value}
proc define_design_lib {args} {}
proc analyze {args} {error "injected analyze failure"}
proc elaborate {args} {set ::elaborated 1}
proc puts {args} {set ::message $args}
proc exit {code} {error "TASK_EXIT $code"}
proc quit {} {error UNEXPECTED_QUIT}
''')
        generated = d.link_script('std.db', ['small.db', 'big.db'], ['new.sv'], ['.'])
        with self.assertRaisesRegex(tkinter.TclError, 'TASK_EXIT 1'):
            t.eval(generated)
        self.assertEqual(int(t.getvar('elaborated')), 0)
        self.assertFalse(t.getboolean(t.getvar('sh_continue_on_error')))

    def test_generated_mapping_uses_new_inventory_and_only_existing_exceptions(self):
        with tempfile.TemporaryDirectory() as directory:
            run = Path(directory); (run/'libs').mkdir()
            for name in ('small.db', 'big.db'):
                (run/'libs'/name).touch()
            script = d.script(run, {'standard_library_member': 'std.db'})
            self.assertEqual(tkinter.Tcl().call('info', 'complete', script), 1)
            self.assertIn('!= 162', script)
            self.assertNotIn('!= 138', script)
            self.assertEqual(script.count('set_false_path -from [get_ports lfextclk] -to $sync0'), 1)
            self.assertEqual(script.count('set_dont_touch $memories true'), 1)
            self.assertNotIn('set_clock_groups', script)
            self.assertNotIn('set_multicycle_path', script)
            self.assertIn(d.SYNTH_MARKER, script)
        self.assertNotIn('set_false_path', d.constraints())
        self.assertIn('-period 6.666666 ', d.constraints())

    def test_marker_must_be_executed_and_no_tool_errors(self):
        echo = 'puts "'+d.SYNTH_MARKER+'"\n'
        d.soc_synth.require_tool_marker(echo+d.SYNTH_MARKER, d.SYNTH_MARKER)
        for bad in (echo, echo+d.SYNTH_MARKER+'\nError: fail', d.SYNTH_MARKER+'\n'+d.SYNTH_MARKER):
            with self.assertRaises(ValueError):
                d.soc_synth.require_tool_marker(bad, d.SYNTH_MARKER)

    def test_positive_slack_cannot_hide_a_broken_feedback_arc(self):
        header = "Information: Checking loops...\n"
        self.assertFalse(d.require_loop_free_timing(header)['strict_timing_verified'])
        for report in ('', 'setup 0.001 hold 0.002',
                       header+'Warning: Timing loops detected. (TIM-209)',
                       header+'* loop breakpoint', header+'warning (TIM-209)'):
            with self.assertRaises(ValueError):
                d.require_loop_free_timing(report)

    def test_server_python36_grammar(self):
        ast.parse(Path(d.__file__).read_text(), feature_version=(3, 6))


if __name__ == '__main__':
    unittest.main()
