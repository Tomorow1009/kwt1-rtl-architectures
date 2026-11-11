"""Wait for one named B synthesis, then run new B diagnostics serially.

Does not restart synthesis, clear locks, resume old queues, delete artifacts,
approve PPA, or launch final1200 before a separate freeze decision.
"""
import argparse
import datetime
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
from server_run import ROOT,sha,save,inputs


def read(path):return json.loads(Path(path).read_text())


def predecessor(run,pid,started):
    state=read(run.parent/'state.json')['stages']['systolic_b_synth']
    if state['pid']!=pid or state['started']!=started:raise ValueError('Synthesis identity changed')
    if state['status']=='running':
        command=(Path('/proc')/str(pid)/'cmdline').read_bytes().split(b'\0')
        if b'systolic_b_synth' not in command or run.parent.name.encode() not in command:
            raise ValueError('Predecessor PID no longer names the selected synthesis')
        return None
    if state['status']!='passed':raise ValueError('Synthesis failed/stopped; no replacement job launched')
    digest=sha(run/'summary.json')
    if state['summary_sha256']!=digest:raise ValueError('Synthesis summary changed')
    summary=read(run/'summary.json')
    if not summary.get('synthesis_completed') or summary['scope']!='systolic_b_whole_soc_task_mode_preliminary_synthesis':
        raise ValueError('Wrong synthesis scope')
    return digest


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--synth-run',required=True,type=Path)
    parser.add_argument('--synth-pid',required=True,type=int)
    parser.add_argument('--synth-started',required=True)
    parser.add_argument('--bundle-manifest-sha256',required=True)
    parser.add_argument('--session',required=True)
    a=parser.parse_args()
    if not re.fullmatch('[A-Za-z0-9_-]{1,40}',a.session):raise ValueError('Invalid new queue session')
    if sha(ROOT/'manifest.json')!=a.bundle_manifest_sha256:raise ValueError('Wrong bundle')
    inputs();cfg=read(ROOT/'handoff/team/server_config.json')
    synthesis=a.synth_run.resolve();synthesis.relative_to(Path(cfg['server_root']).resolve())
    output=ROOT/'runs'/(a.session+'_queue');output.mkdir(parents=True,exist_ok=False)
    state=dict(status='waiting_synthesis',pid=os.getpid(),started=datetime.datetime.now().isoformat(),
        runner_sha256=sha(Path(__file__)),bundle_manifest_sha256=a.bundle_manifest_sha256,
        synthesis_run=str(synthesis),synthesis_pid=a.synth_pid,synthesis_started=a.synth_started,
        completed=[],optional_failures=[],final1200_started=False)
    save(output/'state.json',state)
    try:
        while True:
            digest=predecessor(synthesis,a.synth_pid,a.synth_started)
            if digest:break
            time.sleep(30)
        from systolic_b_gate import verify_synthesis
        report,_=verify_synthesis(synthesis,digest,cfg)
        if not report['setup_hold_nonnegative'] or not report['area_summary']['conservative_budget_within_2mm2']:
            raise ValueError('Preliminary timing/area failed; review before scheduling B gate')
        state['synthesis_summary_sha256']=digest
        common=['--synth-run',str(synthesis),'--synth-summary-sha256',digest]
        stages=[('systolic_b_sequence','sequence',[],False),
                ('systolic_b_contention','contention',['--cases','layer_01','extremes'],False),
                ('systolic_b_saif_probe','saif_probe',common,True),
                ('systolic_b_timing_audit','timing',common,False),
                ('systolic_b_gate','gate14',common,False)]
        lock=Path(cfg['server_root'])/'.arch02_team_lock'
        for stage,suffix,extra,optional in stages:
            session=a.session+'_'+suffix
            if (ROOT/'runs'/session).exists():raise ValueError('Successor already exists; never retry in place')
            state.update(status='waiting_lock',next_stage=stage);save(output/'state.json',state)
            while lock.exists():time.sleep(30)
            inputs()
            if shutil.disk_usage(str(ROOT)).free<8*1024**3:raise ValueError('Insufficient diagnostic/gate disk reserve')
            command=[sys.executable,str(ROOT/'workspaces/arch03/scripts/server_run.py'),stage,'--session',session]+extra
            state.update(status='running',stage=stage,command=command);save(output/'state.json',state)
            with (output/(suffix+'_launcher.log')).open('w') as log:
                child=subprocess.Popen(command,cwd=str(ROOT),stdout=log,stderr=subprocess.STDOUT)
                state['child_pid']=child.pid;save(output/'state.json',state);rc=child.wait()
            run=ROOT/'runs'/session/stage
            result=read(run.parent/'state.json')['stages'][stage] if (run.parent/'state.json').exists() else {}
            if rc or result.get('status')!='passed':
                failure=dict(stage=stage,returncode=rc,state=result)
                if not optional:raise ValueError('Required B validation failed: '+json.dumps(failure))
                state['optional_failures'].append(failure)
            else:
                if sha(run/'summary.json')!=result['summary_sha256']:raise ValueError('Child summary hash changed')
                state['completed'].append(dict(stage=stage,run=str(run),summary_sha256=result['summary_sha256']))
            state['child_pid']=None;save(output/'state.json',state)
        state.update(status='validation_complete_review_required',finished=datetime.datetime.now().isoformat(),
            timing_verified=False,system_power_verified=False,final1200_started=False)
        save(output/'state.json',state)
        print('B_VALIDATION_QUEUE_COMPLETE review_required=true',flush=True)
    except Exception as error:
        state.update(status='failed',error=str(error),finished=datetime.datetime.now().isoformat())
        save(output/'state.json',state);raise


if __name__=='__main__':main()
