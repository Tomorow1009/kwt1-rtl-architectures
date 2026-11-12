"""B whole-system pre-layout power using qualified native-SAIF activity.

Retains raw tool output, X settings and unknown residence counts. Numerical
checks and complete annotation do not approve unknown-state/model impact.
"""
import json
from decimal import Decimal
from pathlib import Path
from server_run import sha,save
from icb32_power import stream_sha,window_values,quiet_absence_checks,collect_reports
import icb32_power as original
from native_saif_crosscheck import script as native_script,extract_reports
from native_saif_activity import audit
from native_saif_replay import verify_inputs
from systolic_b_saif import qualification,LAYERS
from systolic_b_gate import verify_synthesis
from systolic_b_synth import macro_guard
from soc_power import power_databases,power_invocation,tcl_path
from icb32_delivery_sdc import restore_clock


def script(cfg,synthesis,saif,window,strip_path,precise_sdc):
    text=native_script(cfg,synthesis,saif,window,strip_path)
    old=quiet_absence_checks(original.macro_guard())
    if text.count(old)!=1 or text.count('!= 224')!=1:raise ValueError('Original power macro guard changed')
    text=text.replace(old,quiet_absence_checks(macro_guard())).replace('!= 224','!= 220')
    original_sdc='read_sdc '+tcl_path(synthesis/'mapped.sdc')
    if text.count(original_sdc)!=1:raise ValueError('Power SDC import changed')
    exact=r'''
    set hf_period [get_attribute [get_clocks hf_clk] period]
    set lf_period [get_attribute [get_clocks lf_clk] period]
    if {abs($hf_period-6.666666)>1e-12 || abs($lf_period-66.0)>1e-12} {
        error "B power clock differs from the frozen exact task period"
    }
    set clock_file [open power_clock.txt w]
    puts $clock_file "hf_period_ns [format %.12f $hf_period]"
    puts $clock_file "lf_period_ns [format %.12f $lf_period]"
    close $clock_file
'''
    return text.replace(original_sdc,'read_sdc '+tcl_path(precise_sdc)+exact)


def precise_clock(synthesis,run):
    summary=json.loads((synthesis/'summary.json').read_text())
    original_sdc=synthesis/'mapped.sdc'
    if sha(original_sdc)!=summary['artifacts']['mapped.sdc']:
        raise ValueError('Original B SDC changed')
    text,change=restore_clock(original_sdc.read_bytes().decode('ascii'),summary['metrics']['period_ns'])
    target=run/'mapped.precise.sdc'
    with target.open('xb') as stream:stream.write(text.encode('ascii'))
    receipt=dict(original_sdc_sha256=sha(original_sdc),imported_sdc_sha256=sha(target),
        imported_period_ns='6.666666',imported_lf_period_ns='66',clock_change=change,
        original_sdc_modified=False,other_constraints_unchanged=True)
    save(run/'power_clock_input.json',receipt)
    return target,receipt


def estimate(cfg,run,activity_run,activity_sha,case,call):
    run,activity_run=Path(run),Path(activity_run).resolve()
    activity_run.relative_to(Path(cfg['server_root']).resolve())
    if case not in LAYERS:raise ValueError('B power needs a performance layer')
    if sha(activity_run/'summary.json')!=activity_sha:raise ValueError('B SAIF receipt digest mismatch')
    report=json.loads((activity_run/'summary.json').read_text())
    state=json.loads((activity_run.parent/'state.json').read_text())['stages']['systolic_b_saif']
    if (state.get('status')!='passed' or state.get('summary_sha256')!=activity_sha or
        report.get('status')!='B_native_saif_function_and_complete_windows_passed'):
        raise ValueError('No completed B full-window native SAIF')
    qualification(report['qualification_run'],report['qualification_summary_sha256'],cfg)
    matches=[row for row in report['cases'] if row['case']==case]
    if len(matches)!=1:raise ValueError('Missing/duplicate B activity case')
    row=matches[0];saif=activity_run/row['activity']['file']
    activity=audit(saif,row['task_window'])
    if activity!=row['activity']:raise ValueError('B SAIF changed since capture')
    # Only this case's large activity needs rereading, while all small scripts,
    # outputs and receipts remain bound by the immutable capture summary.
    verify_inputs({str(activity_run/name):value for name,value in report['artifacts'].items()
                   if not name.endswith('.saif') or name==saif.name})
    synthesis=Path(report['synthesis_run'])
    verify_synthesis(synthesis,report['synthesis_summary_sha256'],cfg)
    precise_sdc,clock=precise_clock(synthesis,run)
    tcl=run/'systolic_b_power.tcl'
    tcl.write_text(script(cfg,synthesis,saif,row['task_window'],activity['strip_path'],precise_sdc))
    command,environment=power_invocation(cfg,tcl);save(run/'power_environment.json',environment)
    tracked=[tcl,precise_sdc,run/'power_clock_input.json',run/'power_environment.json',synthesis/'mapped.v',synthesis/'mapped.sdc',
        synthesis/'summary.json',activity_run/'summary.json']+power_databases(synthesis)
    before={str(p):sha(p) for p in tracked};save(run/'source_inputs.json',before)
    text=call(command,run,'power.log');components=collect_reports(run,before,text)
    measured=dict(line.split() for line in (run/'power_clock.txt').read_text().splitlines())
    if (set(measured)!={'hf_period_ns','lf_period_ns'} or
        Decimal(measured['hf_period_ns'])!=Decimal('6.666666') or
        Decimal(measured['lf_period_ns'])!=Decimal('66')):
        raise ValueError('Actual PT clock receipt differs')
    clock['measured']=measured
    numeric=extract_reports(run,'systolic_b')
    mapping=numeric['sources']
    for table in (mapping,mapping['static_probability']):
        if table['exact_mapping']+table['implied']!=table['total']:
            raise ValueError('B activity uses default/propagated/unannotated values; inspect reports')
    duration=window_values(row['task_window'])[2]
    numeric['duration_ns']=duration
    numeric['average_power_w']=numeric['reported_power_w']['total']
    numeric['energy_j']=str(Decimal(numeric['average_power_w'])*Decimal(duration)*Decimal('1e-9'))
    save(run/'numbers.json',numeric)
    verify_inputs(before)
    if stream_sha(saif)!=activity['sha256']:raise ValueError('B SAIF changed during PT')
    verify_synthesis(synthesis,report['synthesis_summary_sha256'],cfg)
    return dict(status='reports_and_numbers_ready_unknown_impact_review_required',
        scope='systolic_b_whole_soc_native_saif_pre_layout_power',case=case,
        activity_run=str(activity_run),activity_summary_sha256=activity_sha,activity=activity,
        gate_run=report['gate_run'],gate_summary_sha256=report['gate_summary_sha256'],
        synthesis_run=str(synthesis),synthesis_summary_sha256=report['synthesis_summary_sha256'],
        firmware_sha256=report['firmware_sha256'],layout_sha256=row['layout_sha256'],
        codec_sha256=row['codec_sha256'],task_window=row['task_window'],duration_ns=duration,
        qualification_summary_sha256=report['qualification_summary_sha256'],
        component_leaf_counts=components,numbers=numeric,power_clock=clock,
        system_power_verified=False,timing_verified=False,physical_signoff=False,
        required_reviews=['Unknown-state influence and macro model/activity coverage',
            'Stable task-mode clock/disabled arcs/IO conditions',
            'Pre-layout model without extracted parasitics; official area attribution'],
        artifacts={p.name:stream_sha(p) for p in run.iterdir() if p.is_file()})
