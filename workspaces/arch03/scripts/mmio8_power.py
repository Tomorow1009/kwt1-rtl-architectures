"""Original-MMIO8 mapped power over its actual first-source-VALID window.

The reference may issue VALID one ns after a clock edge. Preserve that exact
event interval; conservative integer cycle rounding is for throughput only.
Never reuse the old BEGIN-window VCD or a DMA16 netlist. Python 3.6.
"""
import json
import re
from decimal import Decimal
from pathlib import Path
import dma16_power as shared
import mmio8_gate as gate_tools
import mmio8_synth as synth
import soc_power
from server_run import sha, save
from soc_synth import require_tool_marker
from timing_contract import CLOCK_PERIOD_NS

MARKER = 'ARCH03_MMIO8_SOURCE_POWER_REPORTS_READY system_power_verified=false DMA_present=false'
SCOPE = 'mmio8_source_whole_soc_gate_activity_pre_layout_power'
BOUNDARY = 'first_source_valid_to_last_output_write_response_with_drain_proof'
REQUIRED = shared.REQUIRED


def window_values(window):
    if window.get('boundary') != BOUNDARY or window.get('total_useful_data_region_bytes') != 191616:
        raise ValueError('Original-MMIO8 complete source-loading window required')
    start, end, edge, phase, period = [Decimal(str(window[k])) for k in
        ('start_ns', 'end_ns', 'start_edge_ns', 'start_phase_ns', 'period_ns')]
    cycles = window['cycles']; tolerance = Decimal('0.000002')
    if (type(cycles) is not int or cycles <= 0 or
            not all(n.is_finite() for n in (start, end, edge, phase, period)) or
            period != Decimal(CLOCK_PERIOD_NS) or not 0 <= edge <= start < end or not 0 <= phase < period or
            abs(start-edge-phase) > tolerance or abs(end-edge-cycles*period) > tolerance or
            window['end_cycle']-window['start_cycle'] != cycles):
        raise ValueError('MMIO8 exact event/clock phase duration mismatch')
    if window.get('successful_data_region_icb_transactions') != dict(source_read_acks=11744,
            input_write_acks=11744, input_read_acks=23488, output_write_acks=25344):
        raise ValueError('MMIO8 source/shared/output transaction evidence differs')
    return str(start), str(end), str(end-start)


def script(cfg, synthesis, vcd, window):
    start, end, _ = window_values(window)
    # Use the same commands/modeling assumptions as DMA16. Keep the exact event
    # times here instead of passing rounded cycles to the older template guard.
    text = r'''
proc mmio8_power_reports {} {
    set_app_var sh_continue_on_error false
    set_app_var power_enable_analysis true
    set_app_var power_analysis_mode averaged
    set_app_var link_path [list * @LIBS@]
    read_verilog @NETLIST@
    current_design e203_soc_top
    if {![link_design]} {error "MMIO8 source whole-SoC power link failed"}
    read_sdc @SDC@
    @MACROS@
    @PORTS@
    @COMPONENTS@
    set memories [get_cells -hierarchical -filter "ref_name == RAMSP128X16 || ref_name == RAMSP4096X16"]
    if {[sizeof_collection $memories] != 138} {error "MMIO8 power SRAM count mismatch"}
    redirect units.rpt {report_units}
    redirect timing_check.rpt {check_timing -verbose}
    redirect disabled_timing.rpt {report_disable_timing -nosplit}
    redirect clocks.rpt {report_clock}
    set settings [open power_settings.rpt w]
    foreach name {power_analysis_mode power_x_transition_derate_factor power_include_initial_x_transitions} {
        puts $settings "$name [get_app_var $name]"
    }
    close $settings
    read_vcd -zero_delay -strip_path tb_top/u_e203_soc_top -time {@START@ @END@} @VCD@
    redirect activity_coverage_before.rpt {report_switching_activity -coverage -hierarchy}
    redirect activity_unannotated_before.rpt {report_switching_activity -list_not_annotated -show_pin}
    update_power
    redirect power.rpt {report_power -nosplit -significant_digits 8}
    redirect power_verbose.rpt {report_power -verbose -nosplit -significant_digits 8}
    redirect power_with_boundary_nets.rpt {report_power -verbose -include_boundary_nets -nosplit -significant_digits 8}
    redirect power_hierarchy.rpt {report_power -hierarchy -levels 30 -nosplit -significant_digits 8}
    redirect power_sram.rpt {report_power -cell_power -nosplit -significant_digits 8 $memories}
    redirect activity_coverage_after.rpt {report_switching_activity -coverage -hierarchy}
    redirect activity_unannotated_after.rpt {report_switching_activity -list_not_annotated -show_pin}
    redirect activity_sources.rpt {report_switching_activity -hierarchy -include_mapping_types}
    puts "@MARKER@"
}
if {[catch {mmio8_power_reports} message]} {
    puts stderr "Error: MMIO8_SOURCE_POWER_ABORT $message"
    exit 1
}
quit
'''
    inventory = shared.component_inventory_script().replace('dma_arbiter', 'source_arbiter').replace(
        'dma_router', 'source_router').replace('DMA16', 'MMIO8 source')
    values = dict(LIBS=' '.join(soc_power.tcl_path(p) for p in soc_power.power_databases(synthesis)),
        NETLIST=soc_power.tcl_path(synthesis/'mapped.v'), SDC=soc_power.tcl_path(synthesis/'mapped.sdc'),
        VCD=soc_power.tcl_path(vcd), START=start, END=end, MACROS=shared.quiet_absence_checks(synth.macro_guard()),
        PORTS=synth.shared.port_guard('power_sysmem_ports.tsv'), COMPONENTS=inventory, MARKER=MARKER)
    for key, value in values.items():
        text = text.replace('@'+key+'@', value)
    return text


def audit_header(path):
    result = gate_tools.fabric_activity.audit_header(path)
    result['status'] = 'mmio8_source_declarations_verified'
    return result


def validate_activity(activity, window):
    start, end, duration = window_values(window)
    if activity.get('status') != 'scope_and_window_verified' or activity.get('scope') != 'tb_top.u_e203_soc_top':
        raise ValueError('MMIO8 power requires audited mapped whole-SoC activity')
    if any(abs(Decimal(a)-Decimal(str(b))) > Decimal('0.000002') for a, b in
           ((start, activity['start_ns']), (end, activity['end_ns']))):
        raise ValueError('MMIO8 exact event activity interval mismatch')
    for key in ('active_value_records', 'unknown_value_records'):
        if type(activity.get(key)) is not int or activity[key] < 0:
            raise ValueError('Invalid MMIO8 explicit activity record counts')
    if not 0 <= activity['unknown_value_records'] <= activity['active_value_records'] or not activity['active_value_records']:
        raise ValueError('MMIO8 inconsistent unknown activity')
    for key in ('component_declarations', 'component_value_records'):
        values = activity.get(key, {})
        if set(values) != {'cpu', 'itcm', 'dtcm', 'accelerator', 'shared', 'interconnect'} or any(
                type(n) is not int or n <= 0 for n in values.values()):
            raise ValueError('Incomplete MMIO8 system activity '+key)
    header = activity.get('mmio8_source_header', {})
    if header.get('status') != 'mmio8_source_declarations_verified' or header.get('source_port_bits') != 106:
        raise ValueError('Missing MMIO8 source/fabric declaration evidence')
    if not re.fullmatch('[a-f0-9]{64}', activity.get('sha256', '')) or activity.get('bytes', 0) <= 0:
        raise ValueError('Missing MMIO8 VCD identity')
    return duration


def gate_activity(gate, expected_sha, case, cfg):
    gate = Path(gate).resolve(); gate.relative_to(Path(cfg['server_root']).resolve())
    if not re.fullmatch('[a-f0-9]{64}', expected_sha) or sha(gate/'summary.json') != expected_sha:
        raise ValueError('MMIO8 gate summary digest mismatch')
    report = json.loads((gate/'summary.json').read_text())
    state = json.loads((gate.parent/'state.json').read_text()).get('stages', {}).get('mmio8_gate', {})
    if (state.get('status') != 'passed' or state.get('summary_sha256') != expected_sha or
            report.get('scope') != gate_tools.SCOPE or report.get('DMA_present') is not False or
            report.get('gate_simulation_verified') is not True or report.get('cpu_executed') is not True):
        raise ValueError('Original MMIO8 source gate verification required')
    for key in ('firmware_sha256', 'source_inputs_sha256'):
        if not re.fullmatch('[a-f0-9]{64}', report.get(key, '')):
            raise ValueError('Incomplete MMIO8 gate provenance '+key)
    if sha(gate/'source_inputs.json') != report['source_inputs_sha256']:
        raise ValueError('MMIO8 gate source receipt changed')
    rows = [row for row in report['cases'] if row['case'] == case]
    if len(rows) != 1 or rows[0].get('outputs') != 25344 or not re.fullmatch('[a-f0-9]{64}', rows[0].get('layout_sha256', '')):
        raise ValueError('Missing/duplicate MMIO8 gate case or output/layout evidence')
    row = rows[0]; activity = row.get('activity', {}); duration = validate_activity(activity, row['task_window'])
    filename = activity['file']
    if Path(filename).name != filename or not filename.endswith('.vcd'):
        raise ValueError('Unsafe MMIO8 VCD filename')
    vcd = gate/filename
    if shared.stream_sha(vcd) != activity['sha256'] or vcd.stat().st_size != activity['bytes'] or audit_header(vcd) != activity['mmio8_source_header']:
        raise ValueError('MMIO8 VCD/header changed')
    gate_tools.soc.check_frozen(json.loads((gate/'source_inputs.json').read_text()))
    synthesis = Path(report['synthesis_run'])
    gate_tools.verify_synthesis(synthesis, report['synthesis_summary_sha256'], cfg)
    return report, row, vcd, synthesis, duration


def collect_reports(run, before, text):
    require_tool_marker(text, MARKER)
    for name in REQUIRED:
        if not (run/name).is_file() or not (run/name).stat().st_size:
            raise ValueError('Missing MMIO8 power report '+name)
    synth.shared.verify_ports((run/'power_sysmem_ports.tsv').read_text())
    components = {}
    for line in (run/'power_component_inventory.tsv').read_text().splitlines():
        fields = line.split('\t')
        if len(fields) != 2 or fields[0] in components or not fields[1].isdigit() or int(fields[1]) <= 0:
            raise ValueError('Invalid MMIO8 power component inventory')
        components[fields[0]] = int(fields[1])
    if set(components) != {'accelerator', 'source_arbiter', 'source_router', 'shared', 'itcm', 'dtcm', 'platform_other'}:
        raise ValueError('Incomplete MMIO8 power components')
    settings = (run/'power_settings.rpt').read_text()
    for key in ('power_analysis_mode', 'power_x_transition_derate_factor', 'power_include_initial_x_transitions'):
        if len(re.findall(r'(?m)^'+key+r'\s+\S+\s*$', settings)) != 1:
            raise ValueError('Missing/ambiguous MMIO8 power setting '+key)
    gate_tools.soc.check_frozen(before)
    return components


def estimate(cfg, run, gate, expected_sha, case, call):
    run = Path(run)
    if not Path(soc_power.PT_SHELL).is_file():
        raise ValueError('Pinned PrimeTime executable missing')
    if any((run/name).exists() for name in ('power.log', 'power.rpt', 'summary.json')):
        raise ValueError('MMIO8 power requires a fresh run')
    report, row, vcd, synthesis, duration = gate_activity(gate, expected_sha, case, cfg)
    tcl = run/'mmio8_power.tcl'; tcl.write_text(script(cfg, synthesis, vcd, row['task_window']))
    command, environment = soc_power.power_invocation(cfg, tcl)
    env_file = run/'power_environment.json'; save(env_file, environment)
    tracked = [tcl, env_file, synthesis/'mapped.v', synthesis/'mapped.sdc', synthesis/'summary.json',
               Path(gate)/'summary.json', Path(gate)/'source_inputs.json']+soc_power.power_databases(synthesis)
    tracked += [Path(__file__).with_name(n) for n in ('mmio8_power.py', 'mmio8_gate.py', 'mmio8_synth.py',
                'dma16_power.py', 'soc_power.py', 'dma16_activity.py', 'dma16_synth.py')]
    before = {str(p): sha(p) for p in tracked}; save(run/'source_inputs.json', before)
    text = call(command, run, 'power.log'); components = collect_reports(run, before, text)
    gate_activity(gate, expected_sha, case, cfg)
    return dict(status='reports_ready_review_required', scope=SCOPE, DMA_present=False,
        system_power_verified=False, timing_verified=False, physical_signoff=False,
        gate_run=str(gate), gate_summary_sha256=expected_sha, case=case,
        firmware_sha256=report['firmware_sha256'], layout_sha256=row['layout_sha256'],
        synthesis_run=str(synthesis), synthesis_summary_sha256=report['synthesis_summary_sha256'],
        task_window=row['task_window'], duration_ns=duration, activity=row['activity'],
        tool=soc_power.PT_SHELL, tool_environment=environment,
        analysis='averaged; zero-delay mapped activity; exact source-valid event; no extracted parasitics',
        component_leaf_counts=components, power_w=None, energy_j=None,
        required_reviews=['Actual units and row/module sums; no DMA16/old-BEGIN power substitution',
            'All tool warnings, disabled arcs and no_clock objects',
            'All 138 SRAMs and platform; actual activity mapping, unknown and static objects',
            'Actual X settings, conditional macro leakage, internal power and model units',
            'Pre-layout wire/clock assumptions; boundary nets separate; all twelve layers'],
        artifacts={p.name: sha(p) for p in run.iterdir() if p.is_file()})
