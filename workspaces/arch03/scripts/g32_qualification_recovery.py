"""Resume G32 after the installed PT rejected the pin 'name' attribute.

The original failed queue is immutable. Its four completed stages retain
their identities; only the pin-query correction, own ICG check, first20 and
precision run here. This is not a new hardware configuration or acceptance.
"""
import argparse
import datetime
import json
import os
from pathlib import Path
import re
import shutil

import server_run as common
import g32_paths as paths
from n1_process import ProcessLedger,atomic_save
from partition_synth_contract import require,digest

SCHEMA='g32-qualification-pin-query-recovery-v1'
PRIOR_ORDER=('soc','sequence','contention','synth')
ORDER=('icg','batch20','precision')


def read(p):return json.loads(Path(p).read_text())
def now():return datetime.datetime.now().isoformat()


def predecessor(reference,bundle,alive):
    queue=Path(reference['queue']).absolute();bundle=Path(bundle).absolute()
    require(queue.parent==bundle/'runs' and queue.resolve()==queue,'Wrong predecessor scope')
    p=queue/'state.json'
    require(digest(p)==reference['state_sha256'],'Failed predecessor changed')
    state=read(p)
    require(state.get('status')=='failed' and state.get('stage')=='icg' and state.get('finished') and
            type(state.get('pid')) is int and not alive(state['pid']),
            'Require exited predecessor failed at ICG query')
    require([x['stage'] for x in state['completed']]==list(PRIOR_ORDER),'Wrong completed predecessor stages')
    refs={};inputs={str(p):reference['state_sha256']}
    for row in state['completed']:
        name=row['stage'];run=queue.with_name(queue.name+'_'+name)/('g32_'+name);ref=row['reference']
        require(ref['run']==str(run) and run.resolve()==run and digest(run/'summary.json')==ref['sha256'],
                'Predecessor successful stage changed')
        local=read(run.parent/'state.json')['stages']['g32_'+name]
        require(local.get('status')=='passed' and local.get('finished') and local.get('run')==str(run) and
                local.get('summary_sha256')==ref['sha256'],'Incomplete predecessor stage')
        refs[name]=ref;inputs[str(run/'summary.json')]=ref['sha256']
        inputs[str(run.parent/'state.json')]=digest(run.parent/'state.json')
    failed=queue.with_name(queue.name+'_icg')/'g32_icg';log=failed/'clock_gating.log'
    require(state.get('error')=='Tool failed '+str(log)+' exit=1','Unexpected original ICG failure')
    local=read(failed.parent/'state.json')['stages']['g32_icg']
    require(local.get('status')=='failed' and local.get('finished') and local.get('run')==str(failed),
            'Missing original failed ICG receipt')
    errors=[line.strip() for line in log.read_text().splitlines() if line.startswith('Error:')]
    allowed={"Error: Unknown attribute 'name'. (FLT-005)",
             'Error: while parsing filter expression:',
             'Error: G32_CLOCK_GATING_ABORT ICG enable pin mismatch'}
    require(set(errors)==allowed,'Recovery is limited to the observed PT pin attribute failure')
    require(not queue.with_name(queue.name+'_batch20').exists() and
            not queue.with_name(queue.name+'_precision').exists(),'Old batch already started')
    for p in (log,failed.parent/'state.json',queue/'request.json'):inputs[str(p)]=digest(p)
    children=sorted((queue/'process_ledger').glob('child_*.json'))
    require(len(children)>=5,'Missing original hardware child ledger')
    for i,p in enumerate(children):
        child=read(p);last=i==len(children)-1
        require(child.get('driver_pid')==state['pid'] and child.get('bundle')==str(bundle) and
                child.get('session')==queue.name and child.get('status')=='exited' and
                child.get('wait_completed') is True and type(child.get('pid')) is int and
                not alive(child['pid']) and child.get('returncode')==(1 if last else 0) and
                child.get('call_status')==('failed' if last else 'passed'),
                'Original child still active or unexpected failure')
        if last:require(child.get('log')==str(log),'Last child was not the failed ICG query')
        inputs[str(p)]=digest(p)
    require(all(digest(p)==h for p,h in inputs.items()),'Predecessor changed during identity check')
    return dict(queue=str(queue),role='initial',state=state,references=refs,inputs=inputs,
                original_failure_preserved=True,stage_accepted=False)


def operations(request):
    root=Path(request['operations_root']).absolute();p=root/'manifest.json'
    require(root.resolve()==root and digest(p)==request['operations_manifest_sha256'],'Operations identity changed')
    manifest=read(p)
    for name,want in manifest['files'].items():
        require(Path(name).name==name and digest(root/name)==want,'Operations file changed')
    import g32_icg_timing_pt2022 as fixed
    require(Path(__file__).resolve()==root/Path(__file__).name and
            Path(fixed.__file__).resolve()==root/'g32_icg_timing_pt2022.py','Wrong recovery modules')
    original=(common.ROOT/'workspaces/arch03/scripts/g32_icg_timing.py').read_text()
    expected=original.replace('name == E','full_name =~ */E').replace('name == TE','full_name =~ */TE')
    require(original.count('name == E')==2 and original.count('name == TE')==1 and
            Path(fixed.__file__).read_text()==expected,'Only the three PT pin queries may change')
    return fixed


def dispatch(name,cfg,run,request,refs,call):
    if name=='icg':
        fixed=operations(request);s=refs['synth']
        return fixed.audit(cfg,run,Path(s['run']),s['sha256'],call)
    if name=='batch20':
        from g32_batch import verify
        return verify(cfg,run,Path(request['platform']),Path(request['dataset']),call)
    require(name=='precision','Unknown recovery stage')
    from g32_precision_join import verify
    batch=refs['batch20']
    return verify(cfg,run,Path(batch['run']),batch['sha256'],Path(request['float_archive']),
                  request['float_archive_sha256'],Path(request['dataset']))


def run_stage(name,cfg,queue,state,ledger,request,refs):
    session=queue.with_name(queue.name+'_'+name);run=session/('g32_'+name)
    require(not session.exists(),'Preserve previous recovery output')
    need=int((3 if name=='batch20' else 1)*1024**3*1.2)+2*1024**3
    require(shutil.disk_usage(str(common.ROOT)).free>=need,'Insufficient recovery storage margin')
    run.mkdir(parents=True);ledger.register_stage_session(session)
    paths.allowed_run(run,cfg,'G32 recovery output')
    row=dict(status='running',pid=os.getpid(),started=now(),run=str(run),coordinator=str(queue))
    local=dict(schema=SCHEMA,stages={'g32_'+name:row})
    atomic_save(session/'state.json',local)
    state.update(status='running',stage=name,current_run=str(run));atomic_save(queue/'state.json',state)
    try:
        report=dispatch(name,cfg,run,request,refs,ledger.call)
        common.inputs();paths.recheck(cfg);operations(request);ledger.check_owner()
        common.save(run/'summary.json',report)
        row.update(status='passed',summary_sha256=digest(run/'summary.json'))
    except BaseException as error:
        row.update(status='failed',error=str(error));raise
    finally:
        row['finished']=now();atomic_save(session/'state.json',local)
    ref=dict(run=str(run),sha256=row['summary_sha256']);state['completed'].append(dict(stage=name,reference=ref))
    atomic_save(queue/'state.json',state)
    print('G32_RECOVERY_STAGE_READY',name,ref['sha256'],flush=True)
    return ref


def execute(request,queue):
    require(request['schema']==SCHEMA and request['bundle']==str(common.ROOT) and
            digest(common.ROOT/'manifest.json')==request['bundle_manifest_sha256'],'Wrong frozen G32 bundle')
    require(digest(__file__)==request['queue_sha256'],'Recovery coordinator changed')
    operations(request)
    cfg=paths.configure(read(common.ROOT/'handoff/team/server_config.json'),common.ROOT,
        request['runtime_root'],request['bundle_manifest_sha256'],[])
    common.inputs()
    prior=predecessor(request['predecessor'],common.ROOT,lambda pid:Path('/proc/%d'%pid).exists())
    original=read(Path(prior['queue'])/'request.json')
    require(original['schema']=='g32-qualification-v1' and original['bundle']==str(common.ROOT) and
            original['bundle_manifest_sha256']==request['bundle_manifest_sha256'] and
            original['queue_sha256']==digest(common.ROOT/'workspaces/arch03/scripts/g32_qualification.py'),
            'Original queue hardware/source identity changed')
    for key in ('platform','dataset','float_archive','float_archive_sha256','baseline','runtime_root'):
        require(request[key]==original[key],'Recovery must retain original configuration '+key)
    from g32_validation import verify_synthesis,require_clear_constraints
    refs=dict(prior['references']);s=refs['synth'];report,_=verify_synthesis(s['run'],s['sha256'],cfg)
    require_clear_constraints(s['run'],report)
    from g32_precision_recovery import numeric_runtime
    numerical=numeric_runtime()
    require(not queue.exists(),'Never resume or overwrite a recovery queue')
    queue.mkdir(parents=True);atomic_save(queue/'request.json',request);atomic_save(queue/'predecessor_proof.json',prior)
    state=dict(schema=SCHEMA,status='acquiring_lock',pid=os.getpid(),started=now(),completed=[],
        predecessor=request['predecessor'],numerical_runtime=numerical,stage_accepted=False,full100_allowed=False)
    atomic_save(queue/'state.json',state)
    ledger=ProcessLedger(common,Path(cfg['server_root'])/'.arch02_team_lock',queue)
    try:
        from g32_lock_wait import acquire_wait
        acquire_wait(ledger);ledger.initialize()
        for name in ORDER:
            if name=='batch20':
                from g32_qualification import admit_batch
                state['batch_admission']=admit_batch(refs,request);atomic_save(queue/'state.json',state)
            refs[name]=run_stage(name,cfg,queue,state,ledger,request,refs)
        require(all(digest(p)==h for p,h in prior['inputs'].items()),'Original evidence changed during recovery')
        state.update(status='qualification_recovered_gate_power_pending',current_run=None,finished=now())
    except BaseException as error:
        state.update(status='failed',error=str(error),finished=now());raise
    finally:
        try:
            if ledger.acquired:ledger.release()
        except BaseException as error:
            state.update(status='failed',error='Lock release failed: '+str(error),finished=now());raise
        finally:atomic_save(queue/'state.json',state)


def main():
    p=argparse.ArgumentParser();p.add_argument('--request',required=True,type=Path)
    p.add_argument('--request-sha256',required=True);p.add_argument('--session',required=True);a=p.parse_args()
    require(re.fullmatch('[A-Za-z0-9_-]{1,40}',a.session),'Invalid recovery session')
    require(digest(a.request)==a.request_sha256,'Recovery request changed')
    execute(read(a.request),common.ROOT/'runs'/a.session)


if __name__=='__main__':main()
