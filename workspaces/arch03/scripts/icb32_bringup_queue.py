"""Wait for the existing serial queue, then run new ASIC14 and synthesis.

Never clear a lock, modify a predecessor, or retry a recorded stage. The wait
process consumes no EDA license. Each child uses the original shared team lock.
This queue stops after reports; it cannot approve timing/area or freeze RTL.
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
from server_run import ROOT,sha,save,inputs


def predecessor_done(directory,expected):
    directory=Path(directory)
    if sha(directory/'plan.json')!=expected:raise ValueError('Predecessor plan changed')
    plan=json.loads((directory/'plan.json').read_text())
    done=directory/'done.json'
    if not done.exists():return False
    result=json.loads(done.read_text())
    if result.get('plan_sha256')!=expected or result.get('completed')!=len(plan['commands']):
        raise ValueError('Predecessor completion is partial or for another plan')
    return True


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--session',required=True)
    parser.add_argument('--predecessor',required=True,type=Path)
    parser.add_argument('--predecessor-plan-sha256',required=True)
    parser.add_argument('--predecessor-pid',required=True,type=int)
    args=parser.parse_args()
    if not re.fullmatch('[A-Za-z0-9_-]{1,48}',args.session):raise ValueError('Invalid session')
    if not re.fullmatch('[a-f0-9]{64}',args.predecessor_plan_sha256):raise ValueError('Invalid predecessor digest')
    manifest=inputs();cfg=json.loads((ROOT/'handoff/team/server_config.json').read_text())
    predecessor=args.predecessor.resolve();predecessor.relative_to(Path(cfg['server_root']).resolve())
    output=ROOT/'runs'/(args.session+'_queue');output.mkdir(parents=True,exist_ok=False)
    lock=Path(cfg['server_root'])/'.arch02_team_lock'
    record=dict(status='waiting_predecessor',pid=os.getpid(),source_commit=manifest['source_commit'],
        started=datetime.datetime.now().isoformat(),predecessor=str(predecessor),
        predecessor_plan_sha256=args.predecessor_plan_sha256,predecessor_pid=args.predecessor_pid,
        session=args.session,completed=[],runner_sha256=sha(Path(__file__)))
    save(output/'state.json',record);missing=0
    try:
        while not predecessor_done(predecessor,args.predecessor_plan_sha256):
            proc=Path('/proc')/str(args.predecessor_pid)/'cmdline'
            if proc.exists():
                command=proc.read_bytes().replace(b'\0',b' ').decode('utf8',errors='replace')
                if str(predecessor/'runner.py') not in command:raise ValueError('Predecessor PID identity changed')
                missing=0
            else:missing+=1
            if missing>=3:raise ValueError('Predecessor exited without a complete receipt; inspect preserved failure')
            time.sleep(20)
        while lock.exists():
            record['status']='waiting_team_lock';save(output/'state.json',record)
            time.sleep(20)
        # The child atomically acquires the lock. A competing owner winning the
        # race makes this queue fail; it never removes that owner's directory.
        for stage in ('icb32_soc','icb32_synth'):
            inputs();record.update(status='running',stage=stage)
            save(output/'state.json',record)
            command=[sys.executable,str(ROOT/'workspaces/arch03/scripts/server_run.py'),stage,'--session',args.session]
            save(output/(stage+'_command.json'),command)
            with (output/(stage+'.log')).open('x') as log:
                child=subprocess.Popen(command,cwd=str(ROOT),stdout=log,stderr=subprocess.STDOUT)
                record['child_pid']=child.pid;save(output/'state.json',record)
                code=child.wait()
            if code:raise RuntimeError(stage+' failed; exit '+str(code))
            state=json.loads((ROOT/'runs'/args.session/'state.json').read_text())['stages'][stage]
            summary=ROOT/'runs'/args.session/stage/'summary.json'
            if state['status']!='passed' or sha(summary)!=state['summary_sha256']:
                raise ValueError('Child did not publish a valid stage receipt')
            record['completed'].append(dict(stage=stage,summary_sha256=state['summary_sha256']))
            save(output/'state.json',record)
        record.update(status='reports_ready_review_required',finished=datetime.datetime.now().isoformat(),
                      timing_verified=False,system_power_verified=False)
    except Exception as error:
        record.update(status='failed',error=str(error),finished=datetime.datetime.now().isoformat())
        save(output/'state.json',record);raise
    save(output/'state.json',record)
    print('ICB32_BRINGUP_QUEUE_COMPLETE reports_require_review=true',flush=True)


if __name__=='__main__':main()
