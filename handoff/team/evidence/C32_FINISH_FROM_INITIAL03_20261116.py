"""Start only C32-A's own final-netlist queue after the explicit initial03 recovery queue exits.

No polling dispatcher, old-job resume, source modification, cleanup, or stage
acceptance. The caller must supply the observed terminal identity explicitly.
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
import time

ROOT=Path('/tmp/s4_21usr_c32_20261116_2010')
BUNDLE=ROOT/'light-light126-c32-91135f6'
INITIAL=BUNDLE/'runs/c32_initial03'
PAYLOAD='bc73ccd413657fd527628be76f5973de10f8cc30705580c3d5970ccbaed143bc'
METHOD=Path('/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109/bundles/light-light126-systolic-b-v3-20261112_114355-ced0e139a01e/runs/systolic_b_r4_crosscheck02/native_saif_r4_crosscheck')
METHOD_SHA='a0a9bc6280e7fe5f35b666535157700aac1d9c0b4490873b6199ba9b5c662d26'


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(4*1024**2),b''):h.update(block)
    return h.hexdigest()


def read(path):return json.loads(Path(path).read_text())


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--manifest-sha256',required=True)
    parser.add_argument('--initial-state-sha256',required=True)
    args=parser.parse_args()
    sys.path.insert(0,str(BUNDLE/'workspaces/arch03/scripts'))
    import server_run as common
    import c32_paths as paths
    import c32_finish as finish
    from c32_archive_contract import completed_queue
    from c32_saif import qualification
    from c32_validation import verify_synthesis
    assert common.ROOT==BUNDLE
    assert sha(BUNDLE/'manifest.json')==args.manifest_sha256
    assert sha(ROOT/'payload_91135f6.json')==PAYLOAD
    payload=read(ROOT/'payload_91135f6.json')
    assert payload['source_commit']=='91135f61c97c980039793c6637d0a06888638df0'
    queue_sha=payload['files']['workspaces/arch03/scripts/c32_finish.py']['sha256']
    assert sha(finish.__file__)==queue_sha
    cfg=paths.configure(read(BUNDLE/'handoff/team/server_config.json'),BUNDLE,ROOT,args.manifest_sha256,[])
    common.inputs()
    launch=read(ROOT/'c32_initial03_launch.json')
    assert launch['manifest_sha256']==args.manifest_sha256 and launch['payload_sha256']==PAYLOAD
    assert sha(ROOT/'c32_initial03_request.json')==launch['request_sha256']
    assert sha(INITIAL/'request.json')==launch['request_sha256']
    proof=completed_queue(INITIAL,args.initial_state_sha256,
                          lambda pid:Path('/proc/%d'%pid).exists(),'initial')
    assert proof['state']['pid']==launch['pid']
    initial_request=read(INITIAL/'request.json')
    assert initial_request['bundle_manifest_sha256']==args.manifest_sha256
    assert initial_request['queue_sha256']==payload['files']['workspaces/arch03/scripts/c32_qualification.py']['sha256']
    refs=proof['references']
    synthesis,_=verify_synthesis(refs['synth']['run'],refs['synth']['sha256'],cfg)
    assert synthesis['setup_hold_nonnegative'] is True
    assert synthesis['area_summary']['conservative_budget_mm2']<=1.0
    precision=read(Path(refs['precision']['run'])/'summary.json')
    assert precision['fresh_float_reference_verified'] is True
    qualification(METHOD,METHOD_SHA,cfg)
    assert not (Path(cfg['server_root'])/'.arch02_team_lock').exists(),'Existing team lock; do not remove'
    active=[]
    for p in Path('/proc').iterdir():
        if not p.name.isdigit() or int(p.name)==os.getpid():continue
        try:
            if p.stat().st_uid!=os.getuid():continue
            cmd=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')
            if any(token in cmd for token in ('/dc_shell','/pt_shell','/simv',
                'c32_qualification.py','c32_finish.py','c80_qualification.py','c80_finish.py')):
                active.append(dict(pid=int(p.name),command=cmd))
        except (FileNotFoundError,ProcessLookupError,PermissionError):pass
    assert not active,'Existing own EDA/queue: '+repr(active)
    assert shutil.disk_usage(str(ROOT)).free>=8*1024**3,'Insufficient runtime margin'
    session='c32_finish01'
    request=ROOT/(session+'_request.json');receipt=ROOT/(session+'_launch.json');log=ROOT/(session+'.log')
    assert not any(p.exists() for p in (request,receipt,log,BUNDLE/'runs'/session))
    value=dict(schema='c32-final-netlist-finish-v1',bundle=str(BUNDLE),
        bundle_manifest_sha256=args.manifest_sha256,runtime_root=str(ROOT),runtime_evidence=[],
        queue_sha256=queue_sha,synthesis=refs['synth'],qualification=dict(run=str(METHOD),sha256=METHOD_SHA))
    with request.open('x') as stream:json.dump(value,stream,indent=2,sort_keys=True);stream.write('\n')
    command=[sys.executable,'-B',str(BUNDLE/'workspaces/arch03/scripts/c32_finish.py'),
        '--request',str(request),'--request-sha256',sha(request),'--session',session]
    with log.open('xb') as stream:
        child=subprocess.Popen(command,cwd=str(BUNDLE),stdin=subprocess.DEVNULL,
            stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
    time.sleep(1)
    result=dict(schema='c32-finish01-launch-v1',pid=child.pid,poll=child.poll(),
        started=datetime.datetime.now().isoformat(),command=command,request_sha256=sha(request),
        manifest_sha256=args.manifest_sha256,initial_state_sha256=args.initial_state_sha256,
        initial_references=refs,launch_script_sha256=sha(__file__),stage_accepted=False,
        protected_T80_modified=False,old8_modified=False,c32_b_started=False,g32_started=False)
    with receipt.open('x') as stream:json.dump(result,stream,indent=2,sort_keys=True);stream.write('\n')
    assert child.poll() is None,'Finish queue exited immediately; preserve and inspect log'
    print('C32_FINISH01_LAUNCHED',json.dumps(result,sort_keys=True),flush=True)


if __name__=='__main__':main()
