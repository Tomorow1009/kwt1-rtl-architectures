"""Finish one C80 final netlist serially under one unchanged team lock.

Only starts after mapping is terminal and independently validated. No old queue
is resumed, no synthesis is repeated, and a failed stage stops successors.
"""
import argparse
import datetime
import json
import os
from pathlib import Path
import re
import shutil

import server_run as common
import c80_paths as paths
from n1_process import ProcessLedger,atomic_save
from partition_synth_contract import require
from c80_validation import verify_synthesis

LAYERS=tuple('layer_%02d'%i for i in range(1,13))
ORDER=('structure','gate','saif','timing_audit','drc_audit')+tuple('power_'+n for n in LAYERS)


def read(path):return json.loads(Path(path).read_text())
def now():return datetime.datetime.now().isoformat()


def dispatch(name,cfg,run,request,refs,call):
    synthesis=Path(request['synthesis']['run']);want=request['synthesis']['sha256']
    if name=='structure':
        from c80_structure import audit
        return audit(synthesis,want,cfg)
    if name=='gate':
        from c80_gate import verify
        return verify(cfg,run,synthesis,want,['extremes','rounding']+list(LAYERS),call)
    if name=='saif':
        from c80_saif import verify
        ref=refs['gate'];method=request['qualification']
        return verify(cfg,run,Path(ref['run']),ref['sha256'],Path(method['run']),method['sha256'],list(LAYERS),call)
    if name=='timing_audit':
        from c80_timing_audit import audit
        return audit(cfg,run,synthesis,want,call)
    if name=='drc_audit':
        from c80_drc_audit import audit
        return audit(cfg,run,synthesis,want,call)
    require(name.startswith('power_') and name[6:] in LAYERS,'Unexpected C80 finish stage')
    from c80_power import estimate
    ref=refs['saif']
    return estimate(cfg,run,Path(ref['run']),ref['sha256'],name[6:],call)


def run_stage(name,cfg,queue,state,ledger,request,refs):
    kind='power' if name.startswith('power_') else name
    session=queue.with_name(queue.name+'_'+name);run=session/('c80_'+kind)
    require(not session.exists(),'Preserve existing C80 stage '+str(session))
    free=shutil.disk_usage(str(common.ROOT)).free
    required=int((4 if kind=='saif' else 1)*1024**3*1.2)+2*1024**3
    require(free>=required,'Insufficient C80 runtime space before '+name)
    run.mkdir(parents=True);ledger.register_stage_session(session)
    paths.allowed_run(run,cfg,'C80 output')
    common.save(run/'runtime_storage_receipt.json',paths.receipt(cfg))
    common.save(run/'storage_preflight.json',dict(free_bytes=free,required_bytes=required,margin=1.2))
    row=dict(status='running',pid=os.getpid(),started=now(),run=str(run),
        coordinator=str(queue),shared_lock_reacquired=False)
    stage_state=dict(schema='c80-independent-stage-v1',stages={'c80_'+kind:row})
    atomic_save(session/'state.json',stage_state)
    state.update(status='running',stage=name,current_run=str(run));atomic_save(queue/'state.json',state)
    try:
        report=dispatch(name,cfg,run,request,refs,ledger.call)
        common.inputs();paths.recheck(cfg);ledger.check_owner()
        report['synthesis_route']='C80 new partitioned final netlist; no historical gate or power PASS reused'
        common.save(run/'summary.json',report)
        row.update(status='passed',summary_sha256=common.sha(run/'summary.json'))
    except BaseException as exc:
        row.update(status='failed',error=str(exc));raise
    finally:
        row['finished']=now();atomic_save(session/'state.json',stage_state)
    ref=dict(run=str(run),sha256=row['summary_sha256'])
    state['completed'].append(dict(stage=name,reference=ref));atomic_save(queue/'state.json',state)
    print('C80_FINISH_STAGE_REPORTS_READY',name,ref['sha256'],flush=True)
    return ref


def sequence(cfg,queue,state,ledger,request):
    refs={}
    for name in ORDER:
        refs[name]=run_stage(name,cfg,queue,state,ledger,request,refs)
    return refs


def execute(request,queue):
    require(request['schema']=='c80-final-netlist-finish-v1','Wrong C80 finish request')
    require(str(common.ROOT)==request['bundle'] and common.sha(common.ROOT/'manifest.json')==
            request['bundle_manifest_sha256'],'Wrong frozen operations bundle')
    require(common.sha(Path(__file__))==request['queue_sha256'],'C80 finish source changed')
    cfg=paths.configure(read(common.ROOT/'handoff/team/server_config.json'),common.ROOT,
        Path(request['runtime_root']),request['bundle_manifest_sha256'],request['runtime_evidence'])
    common.inputs()
    synthesis=request['synthesis'];report,_=verify_synthesis(synthesis['run'],synthesis['sha256'],cfg)
    require(report['scope']=='c80_partitioned_whole_soc_task_mode','Cannot use old T80 netlist')
    require(report['setup_hold_nonnegative'] is True and report['area_summary']['conservative_budget_mm2']<=1.0,
        'Resolve actual C80 timing/area before final validation queue')
    from c80_saif import qualification
    method=request['qualification'];qualification(Path(method['run']),method['sha256'],cfg)
    require(not queue.exists(),'Preserve existing C80 finish session')
    queue.mkdir(parents=True)
    atomic_save(queue/'request.json',request)
    state=dict(status='acquiring_lock',pid=os.getpid(),started=now(),completed=[],
        synthesis=synthesis,stage_accepted=False,c32_started=False,full100_allowed=False)
    atomic_save(queue/'state.json',state)
    ledger=ProcessLedger(common,Path(cfg['server_root'])/'.arch02_team_lock',queue)
    try:
        ledger.acquire();ledger.initialize()
        sequence(cfg,queue,state,ledger,request)
        state.update(status='reports_ready_review_required',current_run=None,finished=now())
    except BaseException as exc:
        state.update(status='failed',error=str(exc),finished=now());raise
    finally:
        try:
            if ledger.acquired:ledger.release()
        except BaseException as exc:
            state.update(status='failed',error='Lock release failed: '+str(exc),finished=now());raise
        finally:atomic_save(queue/'state.json',state)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--request',required=True,type=Path)
    p.add_argument('--request-sha256',required=True)
    p.add_argument('--session',required=True)
    a=p.parse_args()
    require(re.fullmatch('[A-Za-z0-9_-]{1,40}',a.session),'Invalid new C80 finish session')
    require(common.sha(a.request)==a.request_sha256,'C80 finish request changed')
    execute(read(a.request),common.ROOT/'runs'/a.session)


if __name__=='__main__':main()
