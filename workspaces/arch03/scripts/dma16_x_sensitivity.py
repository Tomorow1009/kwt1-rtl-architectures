"""Separate full-window PT X-model sensitivity; never a physical error bound.

Each point uses a fresh PT process and the same immutable gate VCD/netlist/libs.
The frozen default estimate is not replaced by the smallest diagnostic result.
"""
from decimal import Decimal
from pathlib import Path
import re
import dma16_power as power
import dma16_power_numbers as numbers
import dma16_power_activity_review as annotation
from server_run import sha, save

POINTS = {'zero': ('0', 'false'), 'frozen': ('0.5', 'false'),
          'one': ('1', 'false'), 'initial': ('0.5', 'true')}
SCOPE = 'dma16_full_window_x_model_sensitivity_diagnostic'


def point_settings(point):
    numbers.require(point in POINTS, 'Unknown diagnostic X point')
    factor, initial = POINTS[point]
    return dict(zip(annotation.SETTINGS, ('averaged', factor, initial)))


def script(cfg, synthesis, vcd, window, point):
    actual = point_settings(point)
    text = power.script(cfg, synthesis, vcd, window)
    anchor = 'set_app_var power_analysis_mode averaged'
    insert = anchor+'\n'+''.join('    set_app_var '+name+' '+actual[name]+'\n'
                                  for name in annotation.SETTINGS[1:])
    # Set BOTH model choices before reading the VCD, not after annotation.
    return power.replace_once(text, anchor, insert)


def numeric_reports(run, duration, point):
    run = Path(run); expected = point_settings(point)
    names = ('units.rpt', 'power.rpt', 'power_verbose.rpt', 'power_with_boundary_nets.rpt',
             'power_hierarchy.rpt', 'power_sram.rpt', 'power_settings.rpt', 'activity_sources.rpt',
             'activity_unannotated_before.rpt', 'activity_unannotated_after.rpt', 'power.log')
    texts = {name: (run/name).read_text(errors='replace') for name in names}
    numbers.require(not any(re.search(r'(?im)^\s*(?:Error-|Error:|Fatal:)', text) for text in texts.values()),
                    'Actual sensitivity tool errors require review')
    settings = annotation.settings(texts['power_settings.rpt'])
    numbers.require(settings == expected, 'Requested/actual sensitivity settings differ')
    values = numbers.parse_power(texts['power_verbose.rpt'], texts['power.rpt'])
    verbose = numbers.parse_power(texts['power_verbose.rpt'], texts['power_verbose.rpt'])
    numbers.require(values['reported_power_w'] == verbose['reported_power_w'] and
                    values['reported_group_power_w'] == verbose['reported_group_power_w'],
                    'Sensitivity normal/verbose reports disagree')
    values['base_units'] = numbers.parse_base_units(texts['units.rpt'])
    values['module_breakdown'] = numbers.parse_hierarchy(texts['power_hierarchy.rpt'], values['reported_power_w'])
    values['sram_breakdown'] = numbers.parse_sram(texts['power_sram.rpt'])
    values['boundary_inclusive'] = numbers.parse_boundary_power(texts['power_with_boundary_nets.rpt'], values)
    mapping = annotation.sources(texts['activity_sources.rpt'])
    for row in (mapping, mapping['static_probability']):
        numbers.require(row['exact_mapping']+row['implied'] == row['total'],
                        'Other sensitivity activity sources require review')
    unannotated = {phase: annotation.empty_unannotated(texts['activity_unannotated_'+phase+'.rpt'])
                   for phase in ('before', 'after')}
    numbers.require(all(row['overview']['total'] == mapping['total'] for row in unannotated.values()),
                    'Sensitivity annotation design size differs')
    ns = Decimal(duration)
    numbers.require(ns.is_finite() and ns > 0, 'Invalid sensitivity duration')
    energy = lambda total: str(numbers.number(total)*ns*Decimal('1e-9'))
    values['boundary_inclusive']['raw_reported_energy_j'] = energy(values['boundary_inclusive']['reported_power_w']['total'])
    values.update(schema='dma16_x_sensitivity_numbers_v1', point=point, actual_settings=settings,
                  mapping=mapping, unannotated=unannotated, duration_ns=str(ns),
                  raw_reported_energy_j=energy(values['reported_power_w']['total']),
                  system_power_verified=False, physical_error_bound=False,
                  replaces_frozen_estimate=False)
    return values


def estimate(cfg, run, gate, expected_sha, case, call, point):
    point_settings(point); run = Path(run); gate = Path(gate)
    numbers.require(Path(power.soc_power.PT_SHELL).is_file(), 'Pinned PrimeTime executable missing')
    numbers.require(not any((run/name).exists() for name in ('power.log', 'summary.json', 'numbers.json')),
                    'Use a fresh sensitivity run')
    report, row, vcd, synthesis, duration = power.gate_activity(gate, expected_sha, case, cfg)
    tcl = run/'x_sensitivity.tcl'; tcl.write_text(script(cfg, synthesis, vcd, row['task_window'], point))
    command, environment = power.soc_power.power_invocation(cfg, tcl)
    env_file = run/'power_environment.json'; save(env_file, environment)
    tracked = [tcl, env_file, synthesis/'mapped.v', synthesis/'mapped.sdc', synthesis/'summary.json',
               gate/'summary.json', gate/'source_inputs.json', Path(__file__), Path(power.__file__),
               Path(numbers.__file__), Path(annotation.__file__), Path(power.soc_power.__file__)]
    tracked += power.soc_power.power_databases(synthesis)
    before = {str(p): sha(p) for p in tracked}; save(run/'source_inputs.json', before)
    text = call(command, run, 'power.log')
    components = power.collect_reports(run, before, text)
    warnings = {}
    for path in run.iterdir():
        if path.suffix not in ('.rpt', '.log'): continue
        raw = path.read_text(errors='replace')
        numbers.require(not re.search(r'(?im)^\s*(?:Error-|Error:|Fatal:)', raw), 'Sensitivity artifact tool error')
        codes = re.findall(r'(?m)^\s*Warning:.*\(([A-Z]+-[0-9]+)\)\s*$', raw)
        if codes: warnings[path.name] = {code: codes.count(code) for code in sorted(set(codes))}
    numbers.require(not ({code for counts in warnings.values() for code in counts}-{'PSW-208', 'PTE-003'}),
                    'Additional sensitivity warning codes require review')
    values = numeric_reports(run, duration, point); save(run/'numbers.json', values)
    power.gate_activity(gate, expected_sha, case, cfg)
    for path, digest in before.items(): numbers.require(sha(Path(path)) == digest, 'Sensitivity input changed')
    return dict(status='diagnostic_reports_ready_review_required', scope=SCOPE, point=point,
                actual_settings=values['actual_settings'], system_power_verified=False, physical_signoff=False,
                physical_error_bound=False, replaces_frozen_estimate=False,
                gate_run=str(gate), gate_summary_sha256=expected_sha, case=case,
                synthesis_summary_sha256=report['synthesis_summary_sha256'],
                firmware_sha256=report['firmware_sha256'], layout_sha256=row['layout_sha256'],
                task_window=row['task_window'], duration_ns=duration, activity=row['activity'],
                component_leaf_counts=components, warning_occurrences_by_artifact=warnings,
                tool=power.soc_power.PT_SHELL, tool_environment=environment,
                analysis='Fresh PT process; same full VCD, mapped SoC, libraries and zero-delay pre-layout assumptions',
                limits=['This tests selected PT X-model choices, not all physical initial states.',
                        'Do not select the smallest result as the frozen score.',
                        'Known accepted MAC values do not waive idle/system unknown activity.'],
                artifacts={p.name: sha(p) for p in run.iterdir() if p.is_file()})
