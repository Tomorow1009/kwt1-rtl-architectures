"""A new C32 finish queue after a terminal ENOSPC failure before any child.

Only lock acquisition waits. Original lock, ledger, stage implementations,
mapped netlist and frozen bundle remain unchanged. No old queue is restarted.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path('/tmp/s4_21usr_c32_20261116_2010')
BUNDLE=ROOT/'light-light126-c32-repair-5828804'
PREVIOUS='c32_finish_repair03'
NAME='c32_finish_repair04'
SYNTH_SHA='78268481a2fc203ae27102239ac9cdfcf83fdac3fef40dd08c8e1e2e2ef878e5'


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())


def acquire_wait(ledger,acquire,sleep=time.sleep):
    while True:
        if ledger.lock.exists():
            print('WAIT_EXISTING_ORIGINAL_LOCK',flush=True);sleep(5);continue
        try:return acquire()
        except OSError as error:
            if error.errno==17 and ledger.lock.exists():
                sleep(5);continue
            if error.errno!=28 or ledger.lock.exists():raise
            print('WAIT_ORIGINAL_LOCK_STORAGE',flush=True);sleep(5)


def predecessor():
    p=BUNDLE/'runs'/PREVIOUS/'state.json';state=read(p)
    launch=read(ROOT/(PREVIOUS+'_launch.json'));request=ROOT/(PREVIOUS+'_request.json')
    assert state['status']=='failed' and state.get('finished') and state['completed']==[]
    assert state['pid']==launch['pid'] and not Path('/proc/%d'%state['pid']).exists()
    assert '[Errno 28] No space left on device' in state['error'] and '.arch02_team_lock' in state['error']
    assert not list((p.parent/'process_ledger').glob('child_*.json'))
    assert sha(request)==launch['request_sha256']==sha(p.parent/'request.json')
    req=read(request)
    assert req['bundle']==str(BUNDLE) and sha(BUNDLE/'manifest.json')==req['bundle_manifest_sha256']
    assert req['synthesis']==state['synthesis']==launch['synthesis']
    assert req['synthesis']['sha256']==SYNTH_SHA
    assert sha(Path(req['synthesis']['run'])/'summary.json')==SYNTH_SHA
    return req,dict(queue=str(p.parent),state_sha256=sha(p),request_sha256=sha(request),
                    zero_completed_stages=True,zero_started_children=True,old_queue_restarted=False)


def worker(request_path,expected):
    assert sha(request_path)==expected
    req=read(request_path);old,proof=predecessor()
    recovery=req.pop('lock_storage_recovery')
    assert recovery==dict(source_sha256=sha(__file__),predecessor=proof,wait_seconds=5,
        original_lock_unchanged=True,partial_lock_not_removed=True)
    assert req==old
    sys.path.insert(0,str(BUNDLE/'workspaces/arch03/scripts'))
    import c32_finish as finish
    assert sha(finish.__file__)==req['queue_sha256']
    OriginalLedger=finish.ProcessLedger
    class WaitingLedger(OriginalLedger):
        def acquire(self):return acquire_wait(self,super().acquire)
    finish.ProcessLedger=WaitingLedger
    # Preserve the wrapper identity inside the copied request and queue.
    req['lock_storage_recovery']=recovery
    finish.execute(req,BUNDLE/'runs'/NAME)


def launch():
    req,proof=predecessor();req['lock_storage_recovery']=dict(source_sha256=sha(__file__),
        predecessor=proof,wait_seconds=5,original_lock_unchanged=True,partial_lock_not_removed=True)
    rp=ROOT/(NAME+'_request.json');lp=ROOT/(NAME+'.log');receipt=ROOT/(NAME+'_launch.json')
    assert not any(p.exists() for p in (rp,lp,receipt,BUNDLE/'runs'/NAME))
    with rp.open('x') as f:json.dump(req,f,indent=2,sort_keys=True);f.write('\n')
    command=[sys.executable,'-B',str(Path(__file__).resolve()),'--worker','--request',str(rp),'--request-sha256',sha(rp)]
    with lp.open('x') as log:
        child=subprocess.Popen(command,cwd=str(ROOT),stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    value=dict(pid=child.pid,started=datetime.datetime.now().isoformat(),command=command,source_sha256=sha(__file__),
        manifest_sha256=req['bundle_manifest_sha256'],request_sha256=sha(rp),synthesis=req['synthesis'],
        predecessor=proof,stage_accepted=False,old_gate_power_reused=False,old_queue_restarted=False)
    with receipt.open('x') as f:json.dump(value,f,indent=2,sort_keys=True);f.write('\n')
    print('C32_FINISH04_LAUNCHED',child.pid,value['started'],flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group(required=True)
    g.add_argument('--launch',action='store_true');g.add_argument('--worker',action='store_true')
    p.add_argument('--request',type=Path);p.add_argument('--request-sha256');a=p.parse_args()
    if a.launch:launch()
    else:worker(a.request,a.request_sha256)
