"""Launch own final-netlist verification after G32 initial01 has passed/exited.

No old queue resume, mapping restart, source edit, deletion or acceptance.
Operations helpers live outside the frozen source bundle and are hash bound.
"""
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
INITIAL=BUNDLE/'runs/g32_initial01'
METHOD=Path('/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109/bundles/light-light126-systolic-b-v3-20261112_114355-ced0e139a01e/runs/systolic_b_r4_crosscheck02/native_saif_r4_crosscheck')
METHOD_SHA='a0a9bc6280e7fe5f35b666535157700aac1d9c0b4490873b6199ba9b5c662d26'


def read(path):return json.loads(Path(path).read_text())
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--initial-state-sha256',required=True)
    p.add_argument('--ops-manifest-sha256',required=True)
    a=p.parse_args();ops=Path(__file__).resolve().parent
    assert sha(ops/'manifest.json')==a.ops_manifest_sha256
    for name,want in read(ops/'manifest.json')['files'].items():
        assert Path(name).name==name and sha(ops/name)==want
    sys.path.insert(0,str(BUNDLE/'workspaces/arch03/scripts'))
    import server_run as common
    import g32_paths as paths
    import g32_finish as finish
    from g32_archive_contract import completed_queue
    from g32_qualification import admit_batch
    from g32_saif import qualification
    from g32_validation import verify_synthesis
    assert common.ROOT==BUNDLE and sha(BUNDLE/'manifest.json')==MANIFEST
    manifest=read(BUNDLE/'manifest.json')
    assert manifest['production_hardware_commit']=='0e16994675bb15e53642017a88f6307da9af4a01'
    assert sha(finish.__file__)==manifest['files']['workspaces/arch03/scripts/g32_finish.py']
    cfg=paths.configure(read(BUNDLE/'handoff/team/server_config.json'),BUNDLE,ROOT,MANIFEST,[])
    common.inputs()
    launch=read(ROOT/'g32_initial01_process.json')
    assert launch['bundle_manifest_sha256']==MANIFEST and launch['pid']==202586
    assert sha(ROOT/'g32_initial01_request.json')==sha(INITIAL/'request.json')==launch['request_sha256']
    initial_request=read(INITIAL/'request.json')
    assert initial_request['queue_sha256']==manifest['files']['workspaces/arch03/scripts/g32_qualification.py']
    proof=completed_queue(INITIAL,a.initial_state_sha256,lambda pid:Path('/proc/%d'%pid).exists(),'initial')
    assert proof['state']['pid']==launch['pid']
    refs=proof['references'];admit_batch(refs,initial_request)
    verify_synthesis(refs['synth']['run'],refs['synth']['sha256'],cfg)
    precision=read(Path(refs['precision']['run'])/'summary.json')
    assert precision['fresh_float_reference_verified'] is True
    qualification(METHOD,METHOD_SHA,cfg)
    assert not (Path(cfg['server_root'])/'.arch02_team_lock').exists(),'Existing team lock; preserve it'
    active=[]
    for proc in Path('/proc').iterdir():
        if not proc.name.isdigit() or int(proc.name)==os.getpid():continue
        try:
            if proc.stat().st_uid!=os.getuid():continue
            comm=(proc/'comm').read_text().strip();cmd=(proc/'cmdline').read_bytes()
            if comm in ('dc_shell','dc_shell-xg-t','common_shell_ex','pt_shell','vcs','vcs1','vcs2','simv') or any(
                token in cmd for token in (b'/g32_qualification.py\0',b'/g32_finish.py\0')):
                active.append(int(proc.name))
        except (FileNotFoundError,ProcessLookupError,PermissionError):pass
    assert not active,'Own EDA/queue remains live: '+repr(active)
    assert shutil.disk_usage(str(ROOT)).free>=8*1024**3
    session='g32_finish01';request=ROOT/(session+'_request.json');receipt=ROOT/(session+'_launch.json');log=ROOT/(session+'.log')
    assert not any(x.exists() for x in (request,receipt,log,BUNDLE/'runs'/session))
    value=dict(schema='g32-final-netlist-finish-v1',bundle=str(BUNDLE),bundle_manifest_sha256=MANIFEST,
        runtime_root=str(ROOT),runtime_evidence=[],queue_sha256=sha(finish.__file__),synthesis=refs['synth'],
        qualification=dict(run=str(METHOD),sha256=METHOD_SHA))
    with request.open('x') as stream:json.dump(value,stream,indent=2,sort_keys=True);stream.write('\n')
    command=[sys.executable,'-B',str(Path(finish.__file__)),'--request',str(request),
        '--request-sha256',sha(request),'--session',session]
    with log.open('xb') as stream:
        child=subprocess.Popen(command,cwd=str(BUNDLE),stdin=subprocess.DEVNULL,stdout=stream,
            stderr=subprocess.STDOUT,start_new_session=True)
    result=dict(schema='g32-finish01-launch-v1',pid=child.pid,started=datetime.datetime.now().isoformat(),
        command=command,request_sha256=sha(request),manifest_sha256=MANIFEST,
        initial_state_sha256=a.initial_state_sha256,initial_references=refs,launch_script_sha256=sha(__file__),
        operations_manifest_sha256=a.ops_manifest_sha256,stage_accepted=False,full100_started=False,
        protected_T80_modified=False,old8_modified=False)
    with receipt.open('x') as stream:json.dump(result,stream,indent=2,sort_keys=True);stream.write('\n')
    print('G32_FINISH01_STARTED',json.dumps(result,sort_keys=True),flush=True)


if __name__=='__main__':main()
