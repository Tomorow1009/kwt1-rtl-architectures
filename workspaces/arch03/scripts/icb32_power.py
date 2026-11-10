"""ICB32 mapped full-task PrimeTime reports, never automatic power acceptance.

The immutable icb32_gate summary is the activity authority. New source loading
and its waits are included; the external PC/source model is outside SoC power.
Python 3.6 standard library only. Existing soc_power.py remains unchanged.
"""
import hashlib
import json
import re
from decimal import Decimal
from pathlib import Path
import soc_power
from soc_synth import require_tool_marker
from icb32_synth import macro_guard, port_guard, verify_ports, replace_once
from icb32_activity import audit_header
from timing_contract import CLOCK_PERIOD_NS
from server_run import sha, save

MARKER = 'ARCH03_ICB32_POWER_REPORTS_READY system_power_verified=false'
GATE_SCOPE = 'icb32_whole_soc_mapped_functional_without_SDF'
POWER_SCOPE = 'icb32_whole_soc_gate_activity_pre_layout_power'
BOUNDARY = 'first_source_valid_to_final_write_response_ack_with_drain_proof'
LAYERS = tuple('layer_%02d' % n for n in range(1, 13))
REQUIRED = ('units.rpt', 'power.rpt', 'power_verbose.rpt', 'power_with_boundary_nets.rpt',
            'power_settings.rpt', 'power_hierarchy.rpt', 'power_sram.rpt',
            'activity_coverage_before.rpt', 'activity_coverage_after.rpt',
            'activity_unannotated_before.rpt', 'activity_unannotated_after.rpt',
            'activity_sources.rpt', 'timing_check.rpt', 'disabled_timing.rpt', 'clocks.rpt',
            'power_sysmem_ports.tsv', 'power_component_inventory.tsv')


def stream_sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(4*1024*1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def window_values(window):
    encoded=window.get('encoded_bytes')
    if (type(encoded) is not int or not 32<=encoded<=47008 or encoded%4 or
            window.get('boundary') != BOUNDARY or window.get('transfer_bytes') != encoded*2+50688 or
            window.get('transfer_transactions') != encoded//2+12672 or
            Decimal(str(window['period_ns'])) != Decimal(CLOCK_PERIOD_NS)):
        raise ValueError('Power requires the complete ICB32 compressed-source/shared-write/output task window')
    values = soc_power.window_values(window)
    start, end, cycles = (int(window[k]) for k in ('start_cycle', 'end_cycle', 'cycles'))
    if start < 0 or end-start != cycles or int(window['finished_cycle']) < end or cycles<window['transfer_transactions']:
        raise ValueError('ICB32 cycle/drain proof mismatch')
    finished = Decimal(str(window['finished_ns']))
    if not finished.is_finite() or finished < Decimal(values[1]):
        raise ValueError('ICB32 completion proof precedes final output response')
    return values


def component_inventory_script():
    return r'''
# Disjoint LEAF counts verify inclusion of both added and reused hardware.
# Detailed power remains in hierarchy/SRAM reports; don't add nested totals.
array set component_counts {accelerator 0 dma_arbiter 0 dma_router 0 shared 0 itcm 0 dtcm 0 platform_other 0}
foreach_in_collection cell [get_cells -hierarchical -filter "is_hierarchical == false"] {
    set path [get_object_name $cell]
    set category platform_other
    foreach {token label} {
        u_e203_itcm_gnrl_ram itcm u_e203_dtcm_gnrl_ram dtcm
        u_arch03_shared shared u_arch03_accel accelerator
        u_arch03_arb dma_arbiter u_arch03_router dma_router
    } {
        if {[lsearch -exact [lrange [split $path /] 0 end-1] $token] >= 0} {set category $label;break}
    }
    incr component_counts($category)
}
set inventory_file [open power_component_inventory.tsv w]
foreach category [lsort [array names component_counts]] {
    if {$component_counts($category) <= 0} {error "Missing ICB32 power component $category"}
    puts $inventory_file "$category\t$component_counts($category)"
}
close $inventory_file
'''


def quiet_absence_checks(guard):
    # PT T-2022.03 emits SEL-005 for an empty non-quiet get_cells result,
    # even when sizeof_collection correctly returns zero. Only the query
    # asserting that functional memory is ABSENT may legitimately be empty.
    # Required macro counts and the explicit nonempty-forbidden check remain.
    return replace_once(guard,
        '[get_cells -hierarchical -filter "ref_name =~ $forbidden*"]',
        '[get_cells -quiet -hierarchical -filter "ref_name =~ $forbidden*"]')


def script(cfg, synthesis, vcd, window):
    window_values(window)
    text = soc_power.script(cfg, synthesis, vcd, window)
    text = replace_once(text, 'proc arch03_power_reports {} {',
                        'proc arch03_power_reports {} {\n    set_app_var sh_continue_on_error false')
    text = replace_once(text, '!= 138', '!= 224')
    # Installed PT T-2022.03-SP5-1 command manuals: retain the actual
    # no_clock objects and disabled-arc reasons, not only warning totals.
    text = replace_once(text, 'redirect timing_check.rpt {check_timing}',
                        'redirect timing_check.rpt {check_timing -verbose}\n'
                        '    redirect disabled_timing.rpt {report_disable_timing -nosplit}')
    text = replace_once(text, 'redirect units.rpt', quiet_absence_checks(macro_guard())+port_guard('power_sysmem_ports.tsv')+
                        component_inventory_script()+'\n    redirect units.rpt')
    text = replace_once(text, 'ARCH03_SYSTEM_POWER_REPORTS_READY system_power_verified=false', MARKER)
    return text


def verify_synthesis(synthesis, expected_sha, cfg):
    # The gate runner owns the same immutable-source/platform/library check.
    # Never fall back to the old 138-macro/asic_synth verifier.
    from icb32_gate import verify_synthesis as verify
    return verify(synthesis, expected_sha, cfg)


def validate_activity(activity, window):
    if activity.get('status') != 'scope_and_window_verified' or activity.get('scope') != 'tb_top.u_e203_soc_top':
        raise ValueError('ICB32 power requires audited whole-SoC gate activity')
    start, end, duration = window_values(window)
    if any(abs(Decimal(a)-Decimal(str(b))) > Decimal('0.000002') for a, b in
           ((start, activity['start_ns']), (end, activity['end_ns']))):
        raise ValueError('ICB32 activity interval differs from first-valid/last-ACK window')
    for key in ('active_value_records', 'unknown_value_records'):
        if type(activity.get(key)) is not int or activity[key] < 0:
            raise ValueError('Missing/invalid explicit activity value counts')
    if not 0 <= activity['unknown_value_records'] <= activity['active_value_records'] or not activity['active_value_records']:
        raise ValueError('Inconsistent unknown value record count')
    for group in ('component_declarations', 'component_value_records'):
        counts = activity.get(group, {})
        if set(counts) != {'cpu', 'itcm', 'dtcm', 'accelerator', 'shared', 'interconnect'} or any(
                type(n) is not int or n <= 0 for n in counts.values()):
            raise ValueError('Incomplete whole-system activity '+group)
    header = activity.get('icb32_header', {})
    if header.get('status') != 'icb32_declarations_verified' or header.get('source_port_bits') != 106:
        raise ValueError('Missing ICB32 source/fabric declaration audit')
    if not re.fullmatch('[a-f0-9]{64}', activity.get('sha256', '')) or activity.get('bytes', 0) <= 0:
        raise ValueError('Invalid audited VCD identity')
    return duration


def gate_activity(gate, expected_sha, case, cfg):
    gate = Path(gate).resolve(); gate.relative_to(Path(cfg['server_root']).resolve())
    summary_path = gate/'summary.json'
    if not re.fullmatch('[a-f0-9]{64}', expected_sha) or sha(summary_path) != expected_sha:
        raise ValueError('ICB32 gate summary digest mismatch')
    report = json.loads(summary_path.read_text())
    state = json.loads((gate.parent/'state.json').read_text())['stages']['icb32_gate']
    if (state['status'] != 'passed' or state['summary_sha256'] != expected_sha or
            report.get('gate_simulation_verified') is not True or report.get('cpu_executed') is not True or
            report.get('scope') != GATE_SCOPE):
        raise ValueError('ICB32 mapped CPU gate stage has not passed')
    for key in ('firmware_sha256', 'source_inputs_sha256'):
        if not re.fullmatch('[a-f0-9]{64}', report.get(key, '')):
            raise ValueError('Missing immutable gate provenance '+key)
    if sha(gate/'source_inputs.json') != report['source_inputs_sha256']:
        raise ValueError('Gate source input receipt changed')
    rows = [row for row in report['cases'] if row['case'] == case]
    if len(rows) != 1:
        raise ValueError('Missing/duplicate ICB32 gate case')
    row = rows[0]
    if row.get('outputs') != 25344 or not re.fullmatch('[a-f0-9]{64}', row.get('layout_sha256', '')):
        raise ValueError('ICB32 gate output/layout evidence missing')
    activity = row.get('activity', {}); duration = validate_activity(activity, row['task_window'])
    filename = activity['file']
    if Path(filename).name != filename or not filename.endswith('.vcd'):
        raise ValueError('Unsafe ICB32 activity filename')
    vcd = gate/filename
    if stream_sha(vcd) != activity['sha256'] or vcd.stat().st_size != activity['bytes']:
        raise ValueError('ICB32 gate activity changed')
    if audit_header(vcd) != activity['icb32_header']:
        raise ValueError('ICB32 activity header proof changed')
    for name, digest in json.loads((gate/'source_inputs.json').read_text()).items():
        if sha(Path(name)) != digest:
            raise ValueError('ICB32 gate simulation input changed')
    synthesis = Path(report['synthesis_run'])
    verify_synthesis(synthesis, report['synthesis_summary_sha256'], cfg)
    return report, row, vcd, synthesis, duration


def collect_reports(run, before, text):
    require_tool_marker(text, MARKER)
    for name in REQUIRED:
        if not (run/name).is_file() or not (run/name).stat().st_size:
            raise ValueError('Missing ICB32 power artifact '+name)
    verify_ports((run/'power_sysmem_ports.tsv').read_text())
    components = {}
    for line in (run/'power_component_inventory.tsv').read_text().splitlines():
        values = line.split('\t')
        if len(values) != 2 or values[0] in components or not values[1].isdigit() or int(values[1]) <= 0:
            raise ValueError('Malformed/empty power component inventory')
        components[values[0]] = int(values[1])
    if set(components) != {'accelerator', 'dma_arbiter', 'dma_router', 'shared', 'itcm', 'dtcm', 'platform_other'}:
        raise ValueError('Incomplete ICB32 power component inventory')
    settings = (run/'power_settings.rpt').read_text()
    for setting in ('power_analysis_mode', 'power_x_transition_derate_factor', 'power_include_initial_x_transitions'):
        if len(re.findall(r'(?m)^'+setting+r'\s+\S+\s*$', settings)) != 1:
            raise ValueError('Missing/ambiguous actual PrimeTime setting '+setting)
    for name, digest in before.items():
        if sha(Path(name)) != digest:
            raise ValueError('ICB32 power input changed')
    return components


def estimate(cfg, run, gate, expected_sha, case, call):
    run = Path(run)
    if not Path(soc_power.PT_SHELL).is_file():
        raise ValueError('Pinned PrimeTime executable missing')
    if any((run/name).exists() for name in ('power.log', 'power.rpt', 'summary.json')):
        raise ValueError('ICB32 power requires a fresh run directory')
    report, row, vcd, synthesis, duration = gate_activity(gate, expected_sha, case, cfg)
    tcl = run/'icb32_power.tcl'; tcl.write_text(script(cfg, synthesis, vcd, row['task_window']))
    command, environment = soc_power.power_invocation(cfg, tcl)
    environment_file = run/'power_environment.json'; save(environment_file, environment)
    tracked = [tcl, environment_file, synthesis/'mapped.v', synthesis/'mapped.sdc', synthesis/'summary.json',
               Path(gate)/'summary.json', Path(gate)/'source_inputs.json', Path(__file__),
               Path(__file__).with_name('soc_power.py'), Path(__file__).with_name('icb32_activity.py')]
    tracked += soc_power.power_databases(synthesis)
    before = {str(p): sha(p) for p in tracked}; save(run/'source_inputs.json', before)
    text = call(command, run, 'power.log')
    components = collect_reports(run, before, text)
    gate_activity(gate, expected_sha, case, cfg)
    return dict(status='reports_ready_review_required', scope=POWER_SCOPE,
                system_power_verified=False, timing_verified=False, physical_signoff=False,
                gate_run=str(gate), gate_summary_sha256=expected_sha, case=case,
                firmware_sha256=report['firmware_sha256'], layout_sha256=row['layout_sha256'],
                synthesis_run=str(synthesis), synthesis_summary_sha256=report['synthesis_summary_sha256'],
                task_window=row['task_window'], duration_ns=duration, activity=row['activity'],
                tool=soc_power.PT_SHELL, tool_environment=environment,
                analysis='averaged; zero-delay gate activity; no extracted parasitics',
                component_leaf_counts=components, power_w=None, energy_j=None,
                numerical_power_status='Await actual units, component sums, annotation, X and macro-model review; no missing contribution set to zero',
                required_reviews=['PT-063 absent in the actual run; all tool errors/warnings and license completion',
                    'Actual report units: standard-cell leakage uW versus SRAM mW converted by this link',
                    'Both SRAM internal-power models and four conditional leakage groups/rails; cell_leakage_power=0 is not zero leakage',
                    'All mapped/unmapped/default/propagated activity sources; toggle-limit coverage is not mapping coverage',
                    'Unknown value records and actual X-transition/initial-X settings; static nodes need explanation',
                    'CPU, TCMs, DMA/core, arb/router, shared SRAM and remaining platform included without overlapping sums',
                    'External source model excluded; input boundary-net-inclusive total separately reported',
                    'No extracted wire parasitics/physical clock tree; output load and source clock assumptions',
                    'Same frozen configuration for all 12 performance layers; integrate each exact full-task interval'],
                artifacts={p.name: sha(p) for p in run.iterdir() if p.is_file()})


def summarize_twelve(reports):
    """Review queue for the 12 actual reports, not a fabricated power result."""
    if len(reports) != 12 or {r.get('case') for r in reports} != set(LAYERS):
        raise ValueError('Require each of the 12 performance layers exactly once')
    for key in ('gate_summary_sha256', 'synthesis_summary_sha256', 'firmware_sha256'):
        values = {r.get(key) for r in reports}
        if len(values) != 1 or not re.fullmatch('[a-f0-9]{64}', next(iter(values)) or ''):
            raise ValueError('Mixed/missing frozen configuration '+key)
    rows = []
    for report in sorted(reports, key=lambda r: r['case']):
        if report.get('scope') != POWER_SCOPE or report.get('status') != 'reports_ready_review_required':
            raise ValueError('Unreviewed or wrong ICB32 power report scope')
        duration = validate_activity(report['activity'], report['task_window'])
        if Decimal(str(report['duration_ns'])) != Decimal(duration):
            raise ValueError('Power report duration mismatch')
        if not re.fullmatch('[a-f0-9]{64}', report.get('layout_sha256', '')):
            raise ValueError('Missing layer layout binding')
        if set(REQUIRED)-set(report.get('artifacts', {})):
            raise ValueError('Missing required layer power report artifacts')
        rows.append(dict(case=report['case'], cycles=report['task_window']['cycles'], duration_ns=duration,
                         layout_sha256=report['layout_sha256'], activity_sha256=report['activity']['sha256'],
                         unknown_value_records=report['activity']['unknown_value_records'],
                         power_w=None, energy_j=None, system_power_verified=False))
    return dict(status='twelve_layer_reports_ready_review_required', cases=rows,
                gate_summary_sha256=reports[0]['gate_summary_sha256'],
                synthesis_summary_sha256=reports[0]['synthesis_summary_sha256'],
                firmware_sha256=reports[0]['firmware_sha256'], system_power_verified=False,
                total_energy_j=None, total_average_power_w=None,
                aggregation_rule='After review: sum individual task energies; total average power=sum(E)/sum(duration), never average unequal-duration powers',
                incomplete_reason='Report collection does not establish units, annotation, unknown values, macro or interconnect power completeness')
