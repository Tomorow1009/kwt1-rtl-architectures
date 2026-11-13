"""N1 whole-system pre-layout power using qualified native-SAIF activity.

Retains raw tool output, X settings and unknown residence counts. Numerical
checks and complete annotation do not approve unknown-state/model impact.
"""
import json
from decimal import Decimal
from pathlib import Path
from server_run import sha,save
from icb32_power import stream_sha,window_values,quiet_absence_checks,collect_reports
import icb32_power as original
from native_saif_crosscheck import script as native_script,extract_reports as native_extract_reports
from native_saif_activity import audit
from native_saif_replay import verify_inputs
from t64_saif import qualification,LAYERS
from t64_gate import verify_synthesis
from t64_synth import macro_guard
from soc_power import power_databases,power_invocation,tcl_path
from icb32_delivery_sdc import restore_clock
from t64_paths import allowed_run



def extract_reports(run):
    # The generic numerical parser's named physical profile is shared only
    # because both configurations retain 92 small and 128 reused SRAM macros.
    # It grants no B source, waveform, result, timing, or power acceptance.
    result=native_extract_reports(run,'systolic_b')
    expected={'itcm':32,'dtcm':32,'shared':64,'accelerator':92}
    if result['sram']['cell_count']!=220 or result['sram']['counts']!=expected:
        raise ValueError('N1 SRAM model/power inventory is incomplete')
    result.update(schema='arch03-t64-power-numbers-v1',numeric_format='0x000e0c20',
        sram_inventory_contract='N1_60_X_plus_32_W_plus_128_reused_macros',
        system_power_verified=False)
    return result


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
        error "N1 power clock differs from the frozen exact task period"
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
        raise ValueError('Original N1 SDC changed')
    text,change=restore_clock(original_sdc.read_bytes().decode('ascii'),summary['metrics']['period_ns'])
    target=run/'mapped.precise.sdc'
    with target.open('xb') as stream:stream.write(text.encode('ascii'))
    receipt=dict(original_sdc_sha256=sha(original_sdc),imported_sdc_sha256=sha(target),
        imported_period_ns='6.666666',imported_lf_period_ns='66',clock_change=change,
        original_sdc_modified=False,other_constraints_unchanged=True)
    save(run/'power_clock_input.json',receipt)
    return target,receipt


def estimate(cfg,run,activity_run,activity_sha,case,call):
    run,activity_run=Path(run),allowed_run(activity_run,cfg,'N1 SAIF evidence')
    allowed_run(run,cfg,'N1 power output')
    if case not in LAYERS:raise ValueError('N1 power needs a performance layer')
    if sha(activity_run/'summary.json')!=activity_sha:raise ValueError('N1 SAIF receipt digest mismatch')
    report=json.loads((activity_run/'summary.json').read_text())
    state=json.loads((activity_run.parent/'state.json').read_text())['stages']['t64_saif']
    if (state.get('status')!='passed' or state.get('summary_sha256')!=activity_sha or
        report.get('status')!='T64_native_saif_function_and_complete_windows_passed' or
        report.get('schema')!='arch03-t64-native-saif-v1' or report.get('numeric_format')!='0x000e0c20' or
        len(report.get('cases',[]))!=12 or {r['case'] for r in report['cases']}!=set(LAYERS)):
        raise ValueError('No completed N1 full-window native SAIF')
    qualification(report['qualification_run'],report['qualification_summary_sha256'],cfg)
    matches=[row for row in report['cases'] if row['case']==case]
    if len(matches)!=1:raise ValueError('Missing/duplicate N1 activity case')
    row=matches[0];saif=activity_run/row['activity']['file']
    activity=audit(saif,row['task_window'])
    if activity!=row['activity']:raise ValueError('N1 SAIF changed since capture')
    # Only this case's large activity needs rereading, while all small scripts,
    # outputs and receipts remain bound by the immutable capture summary.
    verify_inputs({str(activity_run/name):value for name,value in report['artifacts'].items()
                   if not name.endswith('.saif') or name==saif.name})
    synthesis=Path(report['synthesis_run'])
    verify_synthesis(synthesis,report['synthesis_summary_sha256'],cfg)
    precise_sdc,clock=precise_clock(synthesis,run)
    tcl=run/'t64_power.tcl'
    tcl.write_text(script(cfg,synthesis,saif,row['task_window'],activity['strip_path'],precise_sdc))
    command,environment=power_invocation(cfg,tcl);save(run/'power_environment.json',environment)
    tracked=[tcl,precise_sdc,run/'power_clock_input.json',run/'power_environment.json',synthesis/'mapped.v',synthesis/'mapped.sdc',
        synthesis/'summary.json',activity_run/'summary.json']+power_databases(synthesis)
    tracked += [Path(__file__).with_name(name) for name in ('t64_power.py','t64_paths.py','t64_saif.py','t64_gate.py')]
    before={str(p):sha(p) for p in tracked};save(run/'source_inputs.json',before)
    text=call(command,run,'power.log');components=collect_reports(run,before,text)
    measured=dict(line.split() for line in (run/'power_clock.txt').read_text().splitlines())
    if (set(measured)!={'hf_period_ns','lf_period_ns'} or
        Decimal(measured['hf_period_ns'])!=Decimal('6.666666') or
        Decimal(measured['lf_period_ns'])!=Decimal('66')):
        raise ValueError('Actual PT clock receipt differs')
    clock['measured']=measured
    numeric=extract_reports(run)
    mapping=numeric['sources']
    for table in (mapping,mapping['static_probability']):
        isolated=numeric['isolated_defaults']['count']
        if table['default']!=isolated or table['exact_mapping']+table['implied']+isolated!=table['total']:
            raise ValueError('N1 activity has a gap outside independently proven unconnected declarations')
    duration=window_values(row['task_window'])[2]
    numeric['duration_ns']=duration
    numeric['average_power_w']=numeric['reported_power_w']['total']
    numeric['energy_j']=str(Decimal(numeric['average_power_w'])*Decimal(duration)*Decimal('1e-9'))
    save(run/'numbers.json',numeric)
    verify_inputs(before)
    if stream_sha(saif)!=activity['sha256']:raise ValueError('N1 SAIF changed during PT')
    verify_synthesis(synthesis,report['synthesis_summary_sha256'],cfg)
    return dict(status='reports_and_numbers_ready_unknown_impact_review_required',
        schema='arch03-t64-native-saif-power-v1',numeric_format='0x000e0c20',layout_id=0x00100004,
        scope='t64_whole_soc_native_saif_pre_layout_power',case=case,
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
