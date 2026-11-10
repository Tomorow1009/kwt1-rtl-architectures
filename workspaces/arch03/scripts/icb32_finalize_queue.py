"""Continue the existing gate job with serial power, ASIC14 and final1200.

This is an external operation tool: it never edits an immutable runtime bundle,
restarts a predecessor or clears a team lock. Numerical extraction preserves
review-required power status. The final report is prepared, not auto-approved.
Compatible with the competition server's Python 3.6 standard library.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def save(path, value):
    path=Path(path); temporary=path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
    os.replace(str(temporary),str(path))


def require(ok, message):
    if not ok: raise ValueError(message)


def gate_result(run, pid, started, synthesis_sha):
    """None while running; a bound immutable reference only after a full pass."""
    run=Path(run); state=read(run.parent/'state.json')['stages']['icb32_gate']
    require(state['pid']==pid and state['started']==started, 'Gate identity changed')
    require(state['status'] in ('running','passed'), 'Gate failed or stopped; preserve its run')
    if state['status']=='running': return None
    summary=run/'summary.json'; digest=sha(summary); report=read(summary)
    require(digest==state['summary_sha256'], 'Gate summary digest mismatch')
    require(report['synthesis_summary_sha256']==synthesis_sha, 'Gate synthesis changed')
    names={'layer_%02d'%n for n in range(1,13)}
    require(len(report['cases'])==14 and {x['case'] for x in report['cases']}==names|{'extremes','rounding'},
            'Gate did not complete all 14 cases')
    require(report['gate_simulation_verified'] is True and report['cpu_executed'] is True,
            'Gate did not verify actual mapped CPU execution')
    require(all(x.get('activity',{}).get('status')=='scope_and_window_verified'
                for x in report['cases'] if x['case'] in names), 'Missing full activity window')
    return dict(run=str(run.resolve()),sha256=digest)


def stage_result(bundle, session, stage):
    run=Path(bundle)/'runs'/session/stage
    state=read(run.parent/'state.json')['stages'][stage]
    require(state['status']=='passed' and sha(run/'summary.json')==state['summary_sha256'],
            'Child did not publish a valid receipt: '+stage)
    return dict(run=str(run),sha256=state['summary_sha256'])


def commands(bundle, prefix, gate, dataset):
    base=[sys.executable,str(Path(bundle)/'workspaces/arch03/scripts/server_run.py')]
    result=[]
    for n in range(1,13):
        session=prefix+'_power_l%02d'%n
        result.append(dict(stage='icb32_power',session=session,case='layer_%02d'%n,
            argv=base+['icb32_power','--session',session,'--gate-run',gate['run'],
                       '--gate-summary-sha256',gate['sha256'],'--cases','layer_%02d'%n]))
    for stage,suffix,extra in [('icb32_soc','_metrics14',[]),
                              ('icb32_batch','_final1200',['--dataset',str(dataset)])]:
        session=prefix+suffix
        result.append(dict(stage=stage,session=session,argv=base+[stage,'--session',session]+extra))
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('bundle','gate-run','dataset'):p.add_argument('--'+name,required=True,type=Path)
    for name in ('bundle-manifest-sha256','synthesis-summary-sha256','gate-started','session'):
        p.add_argument('--'+name,required=True)
    p.add_argument('--gate-pid',required=True,type=int)
    a=p.parse_args()
    require(re.fullmatch('[A-Za-z0-9_-]{1,40}',a.session),'Invalid queue session')
    for digest in (a.bundle_manifest_sha256,a.synthesis_summary_sha256):
        require(re.fullmatch('[a-f0-9]{64}',digest),'Invalid digest')
    bundle=a.bundle.resolve(); gate_run=a.gate_run.resolve(); dataset=a.dataset.resolve()
    require(sha(bundle/'manifest.json')==a.bundle_manifest_sha256,'Runtime package identity changed')
    cfg=read(bundle/'handoff/team/server_config.json'); server_root=Path(cfg['server_root']).resolve()
    for path in (bundle,gate_run,dataset):path.relative_to(server_root)
    lock=server_root/'.arch02_team_lock'; runner=bundle/'workspaces/arch03/scripts/server_run.py'
    sys.path.insert(0,str(runner.parent))
    import server_run
    from icb32_power_numbers import extract
    from dma16_batch import index_legacy_dataset
    require(server_run.ROOT==bundle,'Imported runtime from another bundle')
    server_run.inputs()
    require(len(index_legacy_dataset(dataset))==1200,'Wrong final dataset')
    output=bundle/'runs'/(a.session+'_queue'); output.mkdir(parents=True,exist_ok=False)
    state=dict(status='waiting_gate',pid=os.getpid(),started=datetime.datetime.now().isoformat(),
        runner_sha256=sha(__file__),bundle_manifest_sha256=a.bundle_manifest_sha256,
        gate_run=str(gate_run),gate_pid=a.gate_pid,gate_started=a.gate_started,
        synthesis_summary_sha256=a.synthesis_summary_sha256,dataset=str(dataset),completed=[])
    save(output/'state.json',state)
    try:
        missing=0
        while True:
            gate=gate_result(gate_run,a.gate_pid,a.gate_started,a.synthesis_summary_sha256)
            if gate is not None:break
            proc=Path('/proc')/str(a.gate_pid)/'cmdline'
            if proc.exists():
                args=proc.read_bytes().split(b'\0')
                require(b'icb32_gate' in args and gate_run.parent.name.encode() in args,
                        'Gate process identity changed')
                missing=0
            else:missing+=1
            require(missing<3,'Gate disappeared without completion; inspect preserved run')
            time.sleep(20)
        plan=commands(bundle,a.session,gate,dataset)
        require(all(not (bundle/'runs'/x['session']).exists() for x in plan),
                'A planned child session already exists; never retry it')
        save(output/'plan.json',dict(gate=gate,commands=plan))
        state['plan_sha256']=sha(output/'plan.json');state['gate']=gate
        for step in plan:
            while lock.exists():
                state.update(status='waiting_team_lock',next_stage=step['stage'],next_session=step['session'])
                save(output/'state.json',state);time.sleep(20)
            require(sha(bundle/'manifest.json')==a.bundle_manifest_sha256,'Package manifest changed')
            server_run.inputs()
            state.update(status='running',stage=step['stage'],session=step['session'])
            save(output/'state.json',state)
            with (output/(step['session']+'.log')).open('x') as log:
                child=subprocess.Popen(step['argv'],cwd=str(bundle),stdout=log,stderr=subprocess.STDOUT)
                state['child_pid']=child.pid;save(output/'state.json',state)
                code=child.wait()
            require(code==0,'Child failed, exit '+str(code)+': '+step['session'])
            ref=stage_result(bundle,step['session'],step['stage'])
            item=dict(stage=step['stage'],session=step['session'],reference=ref)
            if step['stage']=='icb32_power':
                values=extract(Path(ref['run']),ref['sha256'])
                numbers_file=output/(step['case']+'_numbers.json');save(numbers_file,values)
                item.update(case=step['case'],numbers_sha256=sha(numbers_file),
                    raw_average_power_w=values['reported_power_w']['total'],
                    raw_energy_j=values['raw_reported_energy_j'],system_power_verified=False)
            state['completed'].append(item);save(output/'state.json',state)
            print('ICB32_FINALIZE_STEP_DONE',step['session'],ref['sha256'],flush=True)
        gate_report=read(gate_run/'summary.json')
        refs={x['stage']:x['reference'] for x in state['completed'] if x['stage']!='icb32_power'}
        request=dict(schema='icb32-report-request-v1',asic=refs['icb32_soc'],gate=gate,
            synthesis=dict(run=gate_report['synthesis_run'],sha256=a.synthesis_summary_sha256),
            power=[x['reference'] for x in state['completed'] if x['stage']=='icb32_power'],
            batch=refs['icb32_batch'])
        save(output/'report_request.json',request)
        state.update(status='reports_ready_review_required',finished=datetime.datetime.now().isoformat(),
            system_power_verified=False,timing_verified=False,report_exported=False,
            report_request_sha256=sha(output/'report_request.json'))
    except Exception as error:
        state.update(status='failed',error=str(error),finished=datetime.datetime.now().isoformat())
        save(output/'state.json',state);raise
    save(output/'state.json',state)
    print('ICB32_FINALIZE_QUEUE_COMPLETE review_required=true',flush=True)


if __name__=='__main__':main()
