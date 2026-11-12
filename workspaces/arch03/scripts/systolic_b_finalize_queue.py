"""Serial post-freeze B validation, with no automatic freeze or acceptance.

Requires a separately reviewed, hash-bound freeze record and the completed
first validation queue. Prioritizes B's own1200 before optional SAIF power.
Never edits old runs, retries failed stages, clears locks or starts old queues.
"""
import argparse
import datetime
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from server_run import ROOT,inputs,save
from icb32_power import stream_sha as sha
from icb32_report import configuration_identity
from dma16_report import read
from systolic_b_report import stage,require

ACTIVITY_STAGES=('native_saif_r4_replay','native_saif_r4_crosscheck','systolic_b_saif','systolic_b_power')


def checked_operations(request,root):
    value=request['operations'];directory=Path(value['path']).resolve();directory.relative_to(root)
    manifest=directory/'manifest.json'
    require(sha(manifest)==value['sha256'],'Operations manifest changed')
    files=read(manifest)['files']
    require('systolic_b_ops.py' in files,'Missing operations runner')
    for name,digest in files.items():
        source=(directory/name).resolve();source.relative_to(directory)
        require(sha(source)==digest,'Operations source changed: '+name)
    return directory,value['sha256']


def activity_request(stage_name,extra):
    def value(flag):
        require(extra.count(flag)==1,'Missing/duplicate activity flag '+flag)
        index=extra.index(flag)+1;require(index<len(extra),'Missing activity value')
        return extra[index]
    def ref(run,digest):return dict(run=value(run),sha256=value(digest))
    result=dict(schema='systolic-b-activity-operation-v1',stage=stage_name)
    if stage_name=='native_saif_r4_replay':
        result.update(gate=ref('--gate-run','--gate-summary-sha256'),probe=ref('--native-probe-run','--native-probe-sha256'))
    elif stage_name=='native_saif_r4_crosscheck':
        result.update(replay=ref('--native-replay-run','--native-replay-sha256'),baseline_power=ref('--reference-power-run','--reference-power-sha256'))
    elif stage_name=='systolic_b_saif':
        result.update(gate=ref('--gate-run','--gate-summary-sha256'),qualification=ref('--saif-qualification-run','--saif-qualification-sha256'))
    elif stage_name=='systolic_b_power':
        result.update(activity=ref('--saif-activity-run','--saif-activity-sha256'),case=value('--cases'))
    else:raise ValueError('Unknown activity stage')
    return result


def preflight(request,cfg):
    require(request['schema']=='systolic-b-finalize-request-v1','Wrong finalization request')
    root=Path(cfg['server_root']).resolve()
    require(sha(ROOT/'manifest.json')==request['bundle_manifest_sha256'],'Wrong tool bundle')
    for key in ('asic','synthesis','gate','sequence','contention'):
        Path(request[key]['run']).resolve().relative_to(root)
    reports={key:stage(request[key],name) for key,name in (
        ('asic','systolic_b_soc'),('synthesis','systolic_b_synth'),('gate','systolic_b_gate'),
        ('sequence','systolic_b_sequence'),('contention','systolic_b_contention'))}
    a,s,g,q,c=[reports[k] for k in ('asic','synthesis','gate','sequence','contention')]
    names={'layer_%02d'%i for i in range(1,13)}|{'extremes','rounding'}
    require(a['asic_cpu_verified'] and len(a['cases'])==14 and g['gate_simulation_verified'] and
        len(g['cases'])==14 and g['cpu_executed'] and not g['sdf_annotated'] and
        {r['case'] for r in a['cases']}==names=={r['case'] for r in g['cases']}, 'Own ASIC/gate14 incomplete')
    require(q['no_reset_ABA_verified'] and q['actual_CPU_traps_verified'] and
        q['actual_driver_timeout_verified'] and q['outputs']==76032 and c['contention_verified'] and
        q['scope']=='systolic_b_asic_rtl_functional_sequence' and
        c['scope']=='systolic_b_asic_cpu_shared_contention_validation' and len(c['cases'])==2 and
        {r['case'] for r in c['cases']}=={'layer_01','extremes'},
        'Actual CPU recovery/contention incomplete')
    require(g['synthesis_summary_sha256']==request['synthesis']['sha256'] and
        g['firmware_sha256']==a['compile_receipt']['firmware_manifest_sha256'] and
        s['setup_hold_nonnegative'] and s['area_summary']['conservative_budget_within_2mm2'],
        'Frozen B synthesis/firmware or preliminary PPA mismatch')
    hardware=configuration_identity(request['asic']['run'])
    require(all(configuration_identity(request[key]['run'])==hardware for key in ('synthesis','sequence','contention')),
        'Frozen B production RTL differs between functional, diagnostic and synthesis runs')
    review=request['freeze_review'];p=Path(review['path']).resolve();p.relative_to(root)
    require(sha(p)==review['sha256'],'Freeze review changed')
    value=read(p)
    require(value['schema']=='systolic-b-freeze-review-v1' and value['eligible_for_final1200'] is True and
        value['task_mode_timing_verified'] is True and value['project_area_upper_bound_verified'] is True and
        value['references']=={key:request[key] for key in ('asic','synthesis','gate','sequence','contention')},
        'No separate scoped review of this exact B configuration')
    queue=request['predecessor_queue'];p=Path(queue['path']).resolve();p.relative_to(root)
    require(sha(p)==queue['sha256'] and read(p)['status']=='validation_complete_review_required',
        'Original validation queue has not completed or changed')
    from dma16_batch import index_legacy_dataset
    dataset=Path(request['dataset']).resolve();dataset.relative_to(root)
    require(len(index_legacy_dataset(dataset))==1200,'Wrong pinned final dataset')
    if request.get('native_probe'):
        from native_saif_replay import verify_probe
        verify_probe(request['native_probe']['run'],request['native_probe']['sha256'],cfg)
        require(request.get('R4_gate') and request.get('R4_power'),'Missing original R4 qualification references')
    if request.get('saif_qualification'):
        from systolic_b_saif import qualification
        qualified=request['saif_qualification'];qualification(qualified['run'],qualified['sha256'],cfg)
    if request.get('native_probe') or request.get('saif_qualification'):
        checked_operations(request,root)
    return reports


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--request',required=True,type=Path);p.add_argument('--request-sha256',required=True)
    p.add_argument('--session',required=True);a=p.parse_args()
    require(re.fullmatch('[A-Za-z0-9_-]{1,35}',a.session),'Invalid unique queue name')
    require(sha(a.request)==a.request_sha256,'Finalization request changed')
    request=read(a.request);cfg=read(ROOT/'handoff/team/server_config.json');inputs()
    preflight(request,cfg)
    output=ROOT/'runs'/(a.session+'_queue');output.mkdir(parents=True,exist_ok=False)
    save(output/'request.json',request)
    state=dict(status='ready',pid=os.getpid(),started=datetime.datetime.now().isoformat(),
        request_sha256=a.request_sha256,runner_sha256=sha(__file__),completed=[],optional_failures=[])
    save(output/'state.json',state)
    lock=Path(cfg['server_root'])/'.arch02_team_lock'

    def execute(stage_name,suffix,extra=()):
        session=a.session+'_'+suffix;run=ROOT/'runs'/session/stage_name
        require(not run.parent.exists(),'Child already exists; no retry in place: '+session)
        state.update(status='waiting_lock',stage=stage_name,session=session,child_pid=None)
        save(output/'state.json',state)
        while lock.exists():time.sleep(20)
        require(sha(a.request)==a.request_sha256,'Finalization request changed during queue')
        inputs()
        command=[sys.executable,str(ROOT/'workspaces/arch03/scripts/server_run.py'),
            stage_name,'--session',session]+list(extra)
        if stage_name in ACTIVITY_STAGES:
            operations,ops_sha=checked_operations(request,Path(cfg['server_root']).resolve())
            operation_file=output/(suffix+'_operation.json')
            require(not operation_file.exists(),'Activity request already exists; no retry')
            save(operation_file,activity_request(stage_name,list(extra)))
            command=[sys.executable,str(operations/'systolic_b_ops.py'),
                '--bundle',str(ROOT),'--bundle-sha256',request['bundle_manifest_sha256'],
                '--ops-sha256',ops_sha,'--stage',stage_name,'--session',session,
                '--request',str(operation_file),'--request-sha256',sha(operation_file)]
        state.update(status='running',command=command);save(output/'state.json',state)
        with (output/(suffix+'_launcher.log')).open('x') as log:
            child=subprocess.Popen(command,cwd=str(ROOT),stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT)
            state['child_pid']=child.pid;save(output/'state.json',state);code=child.wait()
        state['child_pid']=None
        require(code==0,'Child failed with preserved run: '+str(run))
        ref=dict(run=str(run),sha256=sha(run/'summary.json'));stage(ref,stage_name)
        state['completed'].append(dict(stage=stage_name,session=session,reference=ref))
        save(output/'state.json',state)
        print('B_FINALIZE_STEP_DONE',session,ref['sha256'],flush=True)
        return ref

    try:
        clean=execute('systolic_b_soc','clean14')
        require(configuration_identity(clean['run'])==configuration_identity(request['asic']['run']) and
            read(Path(clean['run'])/'summary.json')['compile_receipt']['firmware_manifest_sha256']==
            read(Path(request['gate']['run'])/'summary.json')['firmware_sha256'], 'Clean reproduction changed frozen hardware')
        batch=execute('systolic_b_batch','final1200',['--dataset',request['dataset']])
        report=dict(schema='systolic-b-report-request-v1',asic=clean,synthesis=request['synthesis'],
            gate=request['gate'],batch=batch,power=[],history=list(request.get('history',[])))
        if request.get('native_probe') or request.get('saif_qualification'):
            try:
                qualified=request.get('saif_qualification')
                if qualified is None:
                    g=request['R4_gate'];probe=request['native_probe'];original=request['R4_power']
                    replay=execute('native_saif_r4_replay','r4_saif',[
                        '--cases','layer_01','--gate-run',g['run'],'--gate-summary-sha256',g['sha256'],
                        '--native-probe-run',probe['run'],'--native-probe-sha256',probe['sha256']])
                    qualified=execute('native_saif_r4_crosscheck','r4_crosscheck',[
                        '--cases','layer_01','--native-replay-run',replay['run'],'--native-replay-sha256',replay['sha256'],
                        '--reference-power-run',original['run'],'--reference-power-sha256',original['sha256']])
                g=request['gate']
                activity=execute('systolic_b_saif','activity12',[
                    '--cases']+['layer_%02d'%i for i in range(1,13)]+[
                    '--gate-run',g['run'],'--gate-summary-sha256',g['sha256'],
                    '--saif-qualification-run',qualified['run'],'--saif-qualification-sha256',qualified['sha256']])
                report['activity']=activity
                for i in range(1,13):
                    report['power'].append(execute('systolic_b_power','power_l%02d'%i,[
                        '--cases','layer_%02d'%i,'--saif-activity-run',activity['run'],
                        '--saif-activity-sha256',activity['sha256']]))
            except Exception as error:
                failure=dict(stage=state.get('stage'),session=state.get('session'),error=str(error))
                state['optional_failures'].append(failure)
                report['history'].append(dict(status='failed',run=str(ROOT/'runs'/state['session']),
                    description='Native SAIF/power path stopped; no zero substitution: '+str(error)))
        else:
            state['optional_failures'].append(dict(stage='native_saif',error='No qualified tiny-probe reference; activity/power not started'))
        save(output/'report_request.json',report)
        state.update(status='reports_ready_review_required',finished=datetime.datetime.now().isoformat(),
            report_request_sha256=sha(output/'report_request.json'),system_power_verified=False,report_exported=False)
        save(output/'state.json',state)
        print('B_FINALIZE_QUEUE_COMPLETE review_required=true',flush=True)
    except Exception as error:
        state.update(status='failed',error=str(error),finished=datetime.datetime.now().isoformat())
        save(output/'state.json',state);raise


if __name__=='__main__':main()
