"""Serial T64 remainder with one unchanged shared lock for the entire queue.

Reuses only the explicitly identified ASIC14. Each new stage keeps its own
state and artifacts; every EDA child is reaped by the coordinator's ledger.
No hardware, firmware, validation threshold or sample scope changes here.
"""
import argparse
import datetime
import os
from pathlib import Path
import re
import shutil
import sys

import server_run as common
import t64_paths as paths
from n1_process import ProcessLedger, atomic_save
from t64_precision_join import require, read


def now():return datetime.datetime.now().isoformat()


def completed(run, name, expected=None):
    run=Path(run);digest=common.sha(run/'summary.json')
    row=read(run.parent/'state.json')['stages'][name]
    require(row['status']=='passed' and row['summary_sha256']==digest and
            (expected is None or expected==digest),'Incomplete or changed stage '+name)
    return dict(run=str(run),sha256=digest)


def validate_prior(request,cfg):
    ref=request['asic'];run=paths.allowed_run(ref['run'],cfg,'Prior ASIC14')
    completed(run,'t64_soc',ref['sha256'])
    result=read(run/'summary.json')
    expected={'extremes','rounding'}|{'layer_%02d'%i for i in range(1,13)}
    require(result.get('asic_cpu_verified') is True and len(result['cases'])==14 and
            {r['case'] for r in result['cases']}==expected and
            all(r['outputs']==r['total_outputs']==25344 for r in result['cases']),
            'Prior ASIC14 scope is incomplete')
    old=read(run.parents[2]/'manifest.json')['files'];new=common.inputs()['files']
    allowed={'workspaces/arch03/scripts/'+n for n in
             ('n1_process.py','transport_report_stage.py','t64_singlelock_queue.py')}
    require({k:v for k,v in old.items() if k not in allowed}==
            {k:v for k,v in new.items() if k not in allowed},
            'Prior ASIC hardware, firmware, data or verifier changed')
    return ref


def dispatch(name,cfg,run,request,refs,call):
    platform=Path(request['platform']);layers=['layer_%02d'%i for i in range(1,13)]
    if name=='batch20':
        from t64_batch import verify
        return verify(cfg,run,platform,Path(request['dataset']),call)
    if name=='contention':
        from t64_contention import verify
        return verify(cfg,run,platform,['layer_01'],call,None)
    if name=='sequence':
        from t64_sequence_soc import verify
        return verify(cfg,run,platform,['layer_01','rounding'],call,None)
    if name=='synth':
        from t64_synth import synth
        common.vendor(cfg,run)
        return synth(cfg,run,platform,call)
    if name in ('gate','timing_audit','drc_audit','structure'):
        ref=refs['synth'];source=Path(ref['run'])
        if name=='gate':
            from t64_gate import verify
            return verify(cfg,run,source,ref['sha256'],['extremes','rounding']+layers,call,(),None)
        if name=='timing_audit':
            from t64_timing_audit import audit
            return audit(cfg,run,source,ref['sha256'],call)
        if name=='drc_audit':
            from t64_drc_audit import audit
            return audit(cfg,run,source,ref['sha256'],call)
        from t64_structure import audit
        paths.allowed_run(source,cfg,'T64 structural synthesis')
        return audit(source,ref['sha256'])
    if name=='saif':
        from t64_saif import verify
        ref=refs['gate']
        return verify(cfg,run,Path(ref['run']),ref['sha256'],Path(request['qualification_run']),
                      request['qualification_sha256'],layers,call)
    if name=='power':
        from t64_power import estimate
        ref=refs['saif']
        return estimate(cfg,run,Path(ref['run']),ref['sha256'],refs['power_layer'],call)
    require(name=='precision','Unexpected stage')
    import t64_precision as numeric
    import t64_precision_join as join
    ref=refs['batch20'];batch_run=Path(ref['run'])
    completed(batch_run,'t64_batch20',ref['sha256'])
    result=numeric._audit(Path(request['archive']),request['archive_sha256'],Path(request['dataset']),run/'float20')
    require(result['status']=='passed' and result['internal_precision_verified'],'Fresh FLOAT audit failed')
    batch=join.audit_batch(batch_run,read(batch_run/'summary.json'))
    float_ref=dict(run=str(run/'float20'),sha256=common.sha(run/'float20/summary.json'),
                   source_mode=numeric.SOURCE_MODE,archive_sha256=request['archive_sha256'])
    report=join.audit_precision(float_ref,batch)
    report.update(schema='arch03-t64-first20-precision-join-v1',batch=batch,
                  auditor_sha256=common.sha(Path(join.__file__)),timing_verified=False,
                  system_power_verified=False,operations=dict(mode='frozen_singlelock_bundle',
                  bundle_manifest_sha256=request['bundle_manifest_sha256'],
                  coordinator_sha256=common.sha(Path(__file__))))
    completed(batch_run,'t64_batch20',ref['sha256'])
    return report


def run_stage(name,suffix,cfg,queue,state,ledger,request,refs):
    session=queue.with_name(queue.name+'_'+suffix);run=session/('t64_'+name)
    require(not session.exists(),'Preserve existing stage '+str(session))
    estimated=(4 if name in ('synth','saif') else 1)*1024**3
    required=int(estimated*1.2)+2*1024**3;free=shutil.disk_usage(str(common.ROOT)).free
    require(free>=required,'Insufficient stage space: free=%d required=%d'%(free,required))
    run.mkdir(parents=True)
    ledger.register_stage_session(session)
    paths.allowed_run(run,cfg,'T64 output')
    common.save(run/'runtime_storage_receipt.json',paths.receipt(cfg))
    common.save(run/'storage_preflight.json',dict(free_bytes=free,required_bytes=required,
                estimated_stage_bytes=estimated,margin=1.2,reserve_bytes=2*1024**3))
    row=dict(status='running',pid=os.getpid(),started=now(),run=str(run),
             coordinator=str(queue),shared_lock_reacquired=False)
    stage_state=dict(schema='arch03-t64-server-state-v1',stages={'t64_'+name:row})
    atomic_save(session/'state.json',stage_state)
    state.update(status='running',stage='t64_'+name,current_run=str(run),child_pid=None)
    atomic_save(queue/'state.json',state)
    try:
        report=dispatch(name,cfg,run,request,refs,ledger.call)
        common.inputs();paths.recheck(cfg);ledger.check_owner()
        report['runtime_storage']=dict(receipt_sha256=common.sha(run/'runtime_storage_receipt.json'),
            durable_archive_required=True,temporary_storage_is_final_delivery=False)
        common.save(run/'summary.json',report)
        row.update(status='passed',summary_sha256=common.sha(run/'summary.json'))
    except BaseException as exc:
        row.update(status='failed',error=str(exc));raise
    finally:
        row['finished']=now();atomic_save(session/'state.json',stage_state)
    ref=completed(run,'t64_'+name)
    if name=='batch20':state['batch_reference']=ref
    else:state['completed'].append(dict(stage='t64_'+name,reference=ref))
    atomic_save(queue/'state.json',state)
    print('T64_SINGLELOCK_STAGE_PASS',name,ref['sha256'],flush=True)
    if name=='synth':print('T64_SYNTH_INITIAL',report.get('metrics'),flush=True)
    return ref


def execute(request,queue):
    require(request['schema']=='t64-singlelock-remainder-v1','Wrong queue request schema')
    require(str(common.ROOT)==request['bundle'] and
            common.sha(common.ROOT/'manifest.json')==request['bundle_manifest_sha256'],'Wrong frozen bundle')
    require(common.sha(Path(__file__))==request['queue_sha256'],'Queue source changed')
    cfg=paths.configure(read(common.ROOT/'handoff/team/server_config.json'),common.ROOT,
                        Path(request['runtime_root']),request['bundle_manifest_sha256'],request['runtime_evidence'])
    files=common.inputs()['files']
    import n1_process
    for module in (n1_process,sys.modules[__name__]):
        source=Path(module.__file__).resolve()
        require(source.is_relative_to(common.ROOT) if hasattr(source,'is_relative_to') else
                common.ROOT in source.parents,'Unfrozen queue module')
        require(files.get(source.relative_to(common.ROOT).as_posix())==common.sha(source),'Queue dependency changed')
    asic=validate_prior(request,cfg)
    require(common.sha(Path(request['archive']))==request['archive_sha256'],'FLOAT source changed')
    require(Path(request['numpy_root']).is_dir(),'Missing numerical runtime')
    os.environ['OPENBLAS_NUM_THREADS']='1';sys.path.insert(0,request['numpy_root'])
    import numpy
    require(numpy.__version__=='1.19.5','Unexpected tested NumPy version')
    from t64_saif import qualification
    qualification(Path(request['qualification_run']),request['qualification_sha256'],cfg)
    require(not queue.exists(),'Preserve existing queue')
    queue.mkdir(parents=True)
    atomic_save(queue/'request.json',request)
    state=dict(status='acquiring_lock',pid=os.getpid(),started=now(),completed=[],child_pid=None,
               full100_allowed=False,g64_started=False,asic_reference=asic)
    atomic_save(queue/'state.json',state)
    ledger=ProcessLedger(common,Path(cfg['server_root'])/'.arch02_team_lock',queue)
    try:
        ledger.acquire();ledger.initialize()
        refs={}
        for name in ('batch20','contention','sequence','synth','gate','saif','timing_audit','drc_audit','structure'):
            refs[name]=run_stage(name,name,cfg,queue,state,ledger,request,refs)
        for i in range(1,13):
            refs['power_layer']='layer_%02d'%i
            run_stage('power','p%02d'%i,cfg,queue,state,ledger,request,refs)
        run_stage('precision','precision',cfg,queue,state,ledger,request,refs)
        state.update(status='reports_ready_review_required',finished=now(),current_run=None)
    except BaseException as exc:
        state.update(status='failed',error=str(exc),finished=now());raise
    finally:
        try:
            if ledger.acquired:ledger.release()
        except BaseException as exc:
            state.update(status='failed',error='Lock release failed: '+str(exc),finished=now());raise
        finally:atomic_save(queue/'state.json',state)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request',required=True,type=Path)
    parser.add_argument('--request-sha256',required=True)
    parser.add_argument('--session',required=True)
    args=parser.parse_args()
    require(re.fullmatch('[A-Za-z0-9_-]{1,40}',args.session),'Invalid fresh queue session')
    require(common.sha(args.request)==args.request_sha256,'Queue request changed')
    execute(read(args.request),common.ROOT/'runs'/args.session)


if __name__=='__main__':main()
