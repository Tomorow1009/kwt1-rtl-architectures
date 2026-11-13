"""Continue T80 after a terminal failed queue, without rerunning a passed gate.

Only for an explicitly verified private runtime clone. The original queue,
gate, synthesis and shared lock remain unchanged. No T64/G64 and no parallel EDA.
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
import server_run as common
import t80_paths
from n1_process import atomic_save, ProcessLedger


def need(ok,message):
    if not ok:raise ValueError(message)


def read(path):return json.loads(Path(path).read_text())


def pid_present(pid):return Path('/proc/%d'%pid).exists()


def verify_tool_only_clone(old,req):
    if old['bundle_manifest_sha256']==req['bundle_manifest_sha256']:return
    source=Path(old['bundle']);target=Path(req['bundle'])
    need(common.sha(source/'manifest.json')==old['bundle_manifest_sha256'],'Original manifest changed')
    need(common.sha(target/'manifest.json')==req['bundle_manifest_sha256'],'New manifest changed')
    a=read(source/'manifest.json')['files'];b=read(target/'manifest.json')['files']
    need(set(a)==set(b),'Tool-only clone changed file set')
    allowed={'workspaces/arch03/scripts/'+n for n in ('t80_window.py','t80_saif.py','t80_power.py',
        'native_saif_replay.py','native_saif_activity.py','native_saif_crosscheck.py','icb32_power.py')}
    changed={n for n in a if a[n]!=b[n]}
    need(changed and changed<=allowed,'Continuation changed non-activity source')
    for name in a:
        need(common.sha(source/name)==a[name] and common.sha(target/name)==b[name],
             'Tool-only clone file mismatch '+name)


def reference(run,stage):
    run=Path(run);row=read(run.parent/'state.json')['stages'][stage]
    digest=common.sha(run/'summary.json')
    need(row['status']=='passed' and row['summary_sha256']==digest,'Incomplete child '+stage)
    return dict(run=str(run),sha256=digest)


def original(req):
    q=Path(req['original_queue']);f=q/'state.json'
    need(common.sha(f)==req['original_queue_sha256'],'Original queue state changed')
    s=read(f)
    need(s['status']=='failed' and s.get('child_pid') is None,'Original queue must have failed and drained')
    need(not pid_present(s['pid']),'Original queue PID still exists; inspect before continuing')
    old=read(q/'request.json')
    verify_tool_only_clone(old,req)
    expected=['t80_contention','t80_sequence','t80_synth','t80_timing_audit','t80_drc_audit','t80_structure','t80_gate']
    need([r['stage'] for r in s['completed']]==expected,'Only resume immediately after completed gate14')
    for item in s['completed']:
        need(reference(item['reference']['run'],item['stage'])==item['reference'],'Prior child changed')
    need(reference(s['batch_reference']['run'],'t80_batch20')==s['batch_reference'],'Original batch changed')
    return s,old


def child(command,run,stage,output,state,lock):
    run=Path(run);need(not run.parent.exists(),'Preserve previous child '+str(run))
    state.update(status='waiting_lock',stage=stage,child_pid=None)
    atomic_save(output/'state.json',state)
    while lock.exists():time.sleep(20)
    p=None
    with (output/(run.parent.name+'.log')).open('x') as log:
        try:
            p=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT)
            state.update(status='running',child_pid=p.pid);atomic_save(output/'state.json',state)
        finally:
            if p is not None:
                code,errors=ProcessLedger.drain(None,p);state['child_pid']=None
                if errors:raise errors[0]
    need(p is not None and code==0,'Evidence child failed; preserve '+str(run))
    ref=reference(run,stage);state['completed'].append(dict(stage=stage,reference=ref))
    atomic_save(output/'state.json',state)
    print('T80_RESUME_STAGE_PASS',stage,ref['sha256'],flush=True)
    return ref


def execute(req,session):
    need(req['schema']=='t80-priority-evidence-resume-v1','Wrong continuation request')
    need(str(common.ROOT)==req['bundle'],'Wrong runtime import')
    need(common.sha(Path(__file__))==req['runner_sha256'],'Continuation operator changed')
    cfg=t80_paths.configure(read(common.ROOT/'handoff/team/server_config.json'),common.ROOT,
                            req['runtime_root'],req['bundle_manifest_sha256'])
    common.inputs();old,old_req=original(req)
    (common.ROOT/'runs').mkdir(exist_ok=True)
    output=common.ROOT/'runs'/session;output.mkdir(exist_ok=False)
    request=dict(old_req,**req);atomic_save(output/'request.json',request)
    state=dict(status='starting',pid=os.getpid(),child_pid=None,started=datetime.datetime.now().isoformat(),
               completed=list(old['completed']),batch_reference=old['batch_reference'],
               full100_allowed=False,t64_started=False,g64_allowed=False,original_queue=str(req['original_queue']))
    atomic_save(output/'state.json',state)
    lock=Path(cfg['server_root'])/'.arch02_team_lock'
    flags=['--runtime-root',req['runtime_root'],'--runtime-manifest-sha256',req['bundle_manifest_sha256']]
    try:
        def stage(name,suffix,args):
            label=session+'_'+suffix
            cmd=[sys.executable,'-B','-u',str(common.ROOT/'workspaces/arch03/scripts/t80_server.py'),name,
                 '--session',label]+flags+args
            return child(cmd,common.ROOT/'runs'/label/('t80_'+name),'t80_'+name,output,state,lock)
        gate=old['completed'][-1]['reference']
        activity=stage('saif','saif',['--gate-run',gate['run'],'--gate-summary-sha256',gate['sha256'],
            '--saif-qualification-run',old_req['qualification_run'],
            '--saif-qualification-sha256',old_req['qualification_sha256'],
            '--cases']+['layer_%02d'%i for i in range(1,13)])
        for i in range(1,13):
            stage('power','p%02d'%i,['--saif-activity-run',activity['run'],
                '--saif-activity-sha256',activity['sha256'],'--cases','layer_%02d'%i])
        # Invoke the already-frozen precision operator with an explicit runtime
        # configuration; its execute() retains the original lock and identity checks.
        label=session+'_precision';batch=old['batch_reference']
        bootstrap='import os,sys;os.environ["OPENBLAS_NUM_THREADS"]="1";sys.path[:0]='+repr([
            old_req['numpy_root'],str(Path(old_req['operations'])/'scripts'),
            str(common.ROOT/'workspaces/arch03/scripts')])+';import t80_precision_stage as p;'
        bootstrap+='c=p.t80_paths.configure(p.join.read(p.common.ROOT/"handoff/team/server_config.json"),p.common.ROOT,'+repr(req['runtime_root'])+','+repr(req['bundle_manifest_sha256'])+');'
        bootstrap+='o=p.operations_identity('+repr(old_req['operations_manifest_sha256'])+');p.execute(c,p.common.ROOT/"runs"/'+repr(label)+',p.Path('+repr(old_req['archive'])+'),'+repr(old_req['archive_sha256'])+',p.Path('+repr(old_req['dataset'])+'),p.Path('+repr(batch['run'])+'),'+repr(batch['sha256'])+',o)'
        child([sys.executable,'-B','-u','-c',bootstrap],common.ROOT/'runs'/label/'t80_precision',
              't80_precision',output,state,lock)
        state.update(status='reports_ready_review_required',finished=datetime.datetime.now().isoformat())
    except BaseException as exc:
        state.update(status='failed',error=str(exc),finished=datetime.datetime.now().isoformat());raise
    finally:atomic_save(output/'state.json',state)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--request',required=True,type=Path)
    p.add_argument('--request-sha256',required=True);p.add_argument('--session',required=True)
    a=p.parse_args();need(re.fullmatch('[A-Za-z0-9_-]{1,40}',a.session),'Invalid session')
    need(common.sha(a.request)==a.request_sha256,'Request changed');execute(read(a.request),a.session)


if __name__=='__main__':main()
