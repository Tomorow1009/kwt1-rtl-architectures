"""Start the explicit PT query recovery, keeping failed initial01 untouched."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT=Path('/tmp/s4_21usr_g32_20261117_0810')
BUNDLE=ROOT/'light-light126-g32-0e16994'
MANIFEST='3524e2726880684c1c5681ef90da3a1ca41d78daf20d0df5b648e633b6e42f4a'
INITIAL_SHA='de797dab25bccd50134556e363bb074ebe94a22650965495f4e9820cda9d4df5'


def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser();p.add_argument('--ops-manifest-sha256',required=True);a=p.parse_args()
    ops=Path(__file__).resolve().parent
    assert sha(ops/'manifest.json')==a.ops_manifest_sha256
    for n,h in read(ops/'manifest.json')['files'].items():assert Path(n).name==n and sha(ops/n)==h
    assert sha(BUNDLE/'manifest.json')==MANIFEST
    prior=BUNDLE/'runs/g32_initial01'
    assert sha(prior/'state.json')==INITIAL_SHA
    state=read(prior/'state.json');launch=read(ROOT/'g32_initial01_process.json')
    assert state['status']=='failed' and state['stage']=='icg' and state['pid']==launch['pid']==202586
    assert not Path('/proc/202586').exists()
    assert sha(ROOT/'g32_initial01_request.json')==launch['request_sha256']
    assert read(prior/'request.json')==read(ROOT/'g32_initial01_request.json')
    assert shutil.disk_usage(str(ROOT)).free>=6*1024**3
    session='g32_recovery01';request=ROOT/(session+'_request.json');receipt=ROOT/(session+'_launch.json');log=ROOT/(session+'.log')
    assert not any(x.exists() for x in (request,receipt,log,BUNDLE/'runs'/session))
    queue=ops/'g32_qualification_recovery.py';value=read(prior/'request.json')
    value.update(schema='g32-qualification-pin-query-recovery-v1',queue_sha256=sha(queue),
        operations_root=str(ops),operations_manifest_sha256=a.ops_manifest_sha256,
        predecessor=dict(queue=str(prior),state_sha256=INITIAL_SHA))
    with request.open('x') as f:json.dump(value,f,indent=2,sort_keys=True);f.write('\n')
    command=[sys.executable,'-B','-u',str(queue),'--request',str(request),'--request-sha256',sha(request),'--session',session]
    environment=os.environ.copy();environment['PYTHONPATH']=str(BUNDLE/'workspaces/arch03/scripts')
    environment['PYTHONDONTWRITEBYTECODE']='1'
    with log.open('xb') as f:
        child=subprocess.Popen(command,cwd=str(BUNDLE),env=environment,stdin=subprocess.DEVNULL,
            stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
    result=dict(pid=child.pid,started=datetime.datetime.now().isoformat(),command=command,
        request_sha256=sha(request),operations_manifest_sha256=a.ops_manifest_sha256,
        bundle_manifest_sha256=MANIFEST,source_sha256=sha(__file__),initial_state_sha256=INITIAL_SHA,
        original_external_request_sha256=launch['request_sha256'],
        original_internal_request_sha256=sha(prior/'request.json'),
        prior_successful_stages_rerun=False,production_bundle_modified=False,full100_allowed=False,stage_accepted=False)
    with receipt.open('x') as f:json.dump(result,f,indent=2,sort_keys=True);f.write('\n')
    print('G32_RECOVERY01_STARTED',json.dumps(result,sort_keys=True),flush=True)


if __name__=='__main__':main()
