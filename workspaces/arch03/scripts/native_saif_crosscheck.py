"""Compare frozen R4 L01 native-SAIF power against its existing VCD power.

Requires identical task window, libraries/netlist, settings, load-bearing
activity coverage and <=1% whole-system/main-module total-power difference. A pass only
qualifies the activity transport method; it does not approve unknown activity.
"""
import json
import re
from decimal import Decimal
from pathlib import Path
from server_run import sha,save
import icb32_power as power
import icb32_power_numbers as numbers
from dma16_power_activity_review import settings,sources
from native_saif_activity import audit
from native_saif_replay import verify_inputs
from soc_power import power_invocation,power_databases,tcl_path
from native_saif_isolated import tcl_inventory,review as review_annotation,comparable_sources


def script(cfg,synthesis,saif,window,strip_path):
    if strip_path not in ('tb_top/u_e203_soc_top','u_e203_soc_top'):
        raise ValueError('Unreviewed SAIF strip path')
    text=power.script(cfg,synthesis,saif,window)
    start,end,_=power.window_values(window)
    old='read_vcd -zero_delay -strip_path tb_top/u_e203_soc_top -time {%s %s} %s'%(start,end,tcl_path(saif))
    if text.count(old)!=1:raise ValueError('Original power activity command changed')
    text=text.replace(old,'read_saif -strip_path '+strip_path+' '+tcl_path(saif))
    marker='redirect activity_unannotated_before.rpt {report_switching_activity -list_not_annotated -show_pin}'
    if text.count(marker)!=1:raise ValueError('Annotation inventory insertion changed')
    return text.replace(marker,marker+'\n'+tcl_inventory())


def extract_reports(run,sram_profile='icb32'):
    run=Path(run)
    texts={name:(run/name).read_text(errors='replace') for name in power.REQUIRED}
    if any(re.search(r'(?im)^\s*(?:Error-|Error:|Fatal:)',text) for text in texts.values()):
        raise ValueError('Tool errors prevent SAIF cross-check')
    result=numbers.parse_power(texts['power_verbose.rpt'],texts['power.rpt'])
    verbose=numbers.parse_power(texts['power_verbose.rpt'],texts['power_verbose.rpt'])
    if result['reported_power_w']!=verbose['reported_power_w']:raise ValueError('Normal/verbose power mismatch')
    result['base_units']=numbers.parse_base_units(texts['units.rpt'])
    result['modules']=numbers.parse_hierarchy(texts['power_hierarchy.rpt'],result['reported_power_w'])['modules']
    result['sram']=numbers.parse_sram(texts['power_sram.rpt'],sram_profile)
    result['settings']=settings(texts['power_settings.rpt'])
    result['sources']=sources(texts['activity_sources.rpt'])
    result.update(review_annotation(run,result['sources'],texts['activity_unannotated_before.rpt'],texts['activity_unannotated_after.rpt']))
    return result


def compare(reference,native):
    if reference['base_units']!=native['base_units'] or reference['settings']!=native['settings']:
        raise ValueError('Native SAIF changed process units or X/analysis settings')
    mapping=comparable_sources(reference,native)
    if set(reference['modules'])!=set(native['modules']):raise ValueError('Native SAIF component set differs')
    rows={}
    for name in ['whole_soc']+sorted(reference['modules']):
        if name=='whole_soc':
            left=reference['reported_power_w'];right=native['reported_power_w']
        else:
            left=reference['modules'][name]['derived_power_w'];right=native['modules'][name]['derived_power_w']
        a,b=Decimal(left['total']),Decimal(right['total'])
        ratio=abs(b-a)/a if a else (Decimal(0) if b==0 else Decimal('Infinity'))
        rows[name]=dict(VCD_total_w=str(a),SAIF_total_w=str(b),relative_difference=str(ratio),
                        within_one_percent=bool(ratio<=Decimal('.01')),
                        VCD_components_w=left,SAIF_components_w=right)
    return dict(status='within_one_percent' if all(r['within_one_percent'] for r in rows.values()) else 'difference_requires_review',
        allowed_relative_difference='0.01',rows=rows,
        mapping_and_settings_equal=mapping['raw_mapping_equal'],mapping_review=mapping,
        load_bearing_mapping_and_settings_equal=True,passed=all(r['within_one_percent'] for r in rows.values()))


def verify(cfg,run,replay,replay_sha,baseline,baseline_sha,call):
    run,replay,baseline=map(Path,(run,replay,baseline))
    for path in (replay,baseline):path.resolve().relative_to(Path(cfg['server_root']).resolve())
    if sha(replay/'summary.json')!=replay_sha or sha(baseline/'summary.json')!=baseline_sha:
        raise ValueError('Cross-check input summary digest mismatch')
    replay_report=json.loads((replay/'summary.json').read_text())
    replay_state=json.loads((replay.parent/'state.json').read_text())['stages']['native_saif_r4_replay']
    if (replay_state.get('status')!='passed' or replay_state.get('summary_sha256')!=replay_sha or
        replay_report.get('status')!='R4_native_saif_replay_function_and_window_passed'):
        raise ValueError('Full-window native SAIF replay has not passed')
    verify_inputs({str(replay/name):digest for name,digest in replay_report['artifacts'].items()})
    # Existing extractor independently verifies frozen VCD power files/state.
    original=numbers.extract(baseline,baseline_sha)
    baseline_report=json.loads((baseline/'summary.json').read_text())
    for key in ('gate_summary_sha256','synthesis_summary_sha256','task_window'):
        if replay_report[key]!=baseline_report[key]:raise ValueError('R4 cross-check does not use identical '+key)
    if baseline_report['case']!='layer_01':raise ValueError('Only frozen R4 L01 is the pilot reference')
    synthesis=Path(replay_report['synthesis_run']);window=replay_report['task_window']
    saif=replay/replay_report['activity']['file']
    activity=audit(saif,window)
    if activity!=replay_report['activity']:raise ValueError('Native activity changed since replay')
    tcl=run/'native_saif_power.tcl';tcl.write_text(script(cfg,synthesis,saif,window,activity['strip_path']))
    cmd,environment=power_invocation(cfg,tcl);save(run/'power_environment.json',environment)
    tracked=[tcl,run/'power_environment.json',synthesis/'mapped.v',synthesis/'mapped.sdc',
        synthesis/'summary.json',replay/'summary.json',baseline/'summary.json']+power_databases(synthesis)
    before={str(p):sha(p) for p in tracked};save(run/'source_inputs.json',before)
    log=call(cmd,run,'power.log');components=power.collect_reports(run,before,log)
    if components!=baseline_report['component_leaf_counts']:raise ValueError('Power leaf inventory changed')
    reference=extract_reports(baseline);native=extract_reports(run)
    comparison=compare(reference,native);save(run/'comparison.json',comparison)
    save(run/'native_numbers.json',native)
    verify_inputs(before)
    if power.stream_sha(saif)!=activity['sha256']:raise ValueError('SAIF changed during PT')
    if not comparison['passed']:raise ValueError('SAIF/VCD differs by more than 1%; see preserved comparison.json')
    return dict(status='R4_SAIF_VCD_method_crosscheck_passed',
        replay_run=str(replay),replay_summary_sha256=replay_sha,
        reference_power_run=str(baseline),reference_power_summary_sha256=baseline_sha,
        gate_summary_sha256=replay_report['gate_summary_sha256'],
        synthesis_summary_sha256=replay_report['synthesis_summary_sha256'],
        task_window=window,comparison=comparison,activity=activity,
        activity_method_qualified=True,system_power_verified=False,physical_signoff=False,
        reference_power_w=original['reported_power_w'],
        remaining_review='Unknown activity impact, macro coverage and pre-layout modeling remain explicit',
        artifacts={p.name:power.stream_sha(p) for p in run.iterdir() if p.is_file()})
