"""Launch only the new C80 qualification queue, with pinned source/data paths.

Run explicitly from the visible competition-server terminal after transfer.
This file does not run on import. Protected Desktop/T80 and old8 are untouched.
"""
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT=Path('/tmp/s4_21usr_c80_20261116_1245')
BUNDLE=ROOT/'light-light126-c80-74f3ae7'
MANIFEST='d0f18e4a6aa8a928df37d4347f1a8853c448e823f0685a83c5b710732e5e7a59'
PAYLOAD='37f628a694c031547ce30bac9f764e7f0b353b787bf6be6a232a0a6cfe7055ac'
QUEUE_SHA='f04f6f4644faf26832c7e757db0a5e98f3e30e2eb844bee7816bdad17aca5500'
SERVER=Path('/storage2/2026contest/server4/s4_21usr/Desktop/IC')
BUDGET=Path('/tmp/s4_21usr_t80_20261115_1830/light-light126-t80-s0-a5f138e/runs/s0_synth08/t80_s0_synth')
BASELINE=Path('/tmp/s4_21usr_p80_20261116_0315/light-light126-p80-1023646/runs/p80_report05/p80_report/report.json')
BASELINE_SHA='a5821699ef4551bfdfb485c7c3b9bae3e07f0fb0b27ca984ed58f3d0a6ace5ce'
FLOAT=Path('/tmp/s4_21usr_n1_20261113_0210/n1_precision_inputs_20261113_0840/n1-recovered-float100-20261113.zip')
FLOAT_SHA='5df11251821d2d36e85e07c8a171195d9d2ed2d4084a979519d23f6df7d683e2'
INVENTORY='ae052bc1e543930abece8202a5b1439dcbd50dd4f5d7d09fb8f049eb30eeb997'


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(4*1024**2),b''):h.update(b)
    return h.hexdigest()


def main():
    sys.path.insert(0,str(BUNDLE/'workspaces/arch03/scripts'))
    import server_run as common
    import c80_paths
    import c80_qualification
    assert common.ROOT==BUNDLE
    assert sha(BUNDLE/'manifest.json')==MANIFEST
    assert sha(ROOT/'payload_74f3ae7.json')==PAYLOAD
    assert sha(c80_qualification.__file__)==QUEUE_SHA
    cfg=c80_paths.configure(json.loads((BUNDLE/'handoff/team/server_config.json').read_text()),
        BUNDLE,ROOT,MANIFEST,[])
    common.inputs()
    assert not (SERVER/'.arch02_team_lock').exists(),'Do not remove or override a collaboration lock'
    active=[]
    for p in Path('/proc').iterdir():
        if not p.name.isdigit() or int(p.name)==os.getpid():continue
        try:
            if p.stat().st_uid!=os.getuid():continue
            cmd=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')
            if any(token in cmd for token in ('/dc_shell','/pt_shell','/simv','c80_qualification.py','p80_final_combined')):
                active.append(dict(pid=int(p.name),command=cmd))
        except (FileNotFoundError,ProcessLookupError):pass
    assert not active,'Existing own EDA/queue remains active: '+repr(active)
    free=shutil.disk_usage(str(ROOT)).free
    assert free>=18*1024**3,'Need synthesis/first20 runtime margin before launch'
    assert sha(BUDGET/'summary.json')=='e77fac98d9ab9032e431e8bcfe7d0e3d42f33d8b28222d37ceb48777c9bd4916'
    assert sha(BASELINE)==BASELINE_SHA
    dataset=SERVER/'hex_short_all'
    assert sha(dataset/'SHA256_FILES.json')==INVENTORY
    assert sha(FLOAT)==FLOAT_SHA
    session='c80_initial02'
    assert not (BUNDLE/'runs'/session).exists()
    request=ROOT/(session+'_request.json');receipt=ROOT/(session+'_launch.json');log=ROOT/(session+'.log')
    assert not any(p.exists() for p in (request,receipt,log))
    value=dict(schema='c80-qualification-v1',bundle=str(BUNDLE),bundle_manifest_sha256=MANIFEST,
        runtime_root=str(ROOT),runtime_evidence=[],queue_sha256=QUEUE_SHA,
        platform=str(SERVER.parent/'e203_hbirdv2-master'),dataset=str(dataset),budget_origin=str(BUDGET),
        baseline=dict(path=str(BASELINE),sha256=BASELINE_SHA),float_archive=str(FLOAT),float_archive_sha256=FLOAT_SHA)
    with request.open('x') as f:json.dump(value,f,indent=2,sort_keys=True);f.write('\n')
    command=[sys.executable,'-B',str(BUNDLE/'workspaces/arch03/scripts/c80_qualification.py'),
        '--request',str(request),'--request-sha256',sha(request),'--session',session]
    with log.open('xb') as stream:
        child=subprocess.Popen(command,cwd=str(BUNDLE),stdin=subprocess.DEVNULL,
            stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
    time.sleep(1)
    observed=dict(schema='c80-initial-qualification-launch-v1',pid=child.pid,
        started=datetime.datetime.now().isoformat(),poll=child.poll(),command=command,
        session=session,queue=str(BUNDLE/'runs'/session),log=str(log),runtime_free_bytes=free,
        shared_free_bytes=shutil.disk_usage(str(SERVER)).free,
        manifest_sha256=MANIFEST,payload_sha256=PAYLOAD,request_sha256=sha(request),
        launch_script_sha256=sha(__file__),protected_T80_modified=False,old8_modified=False,
        stage_accepted=False,c32_started=False)
    with receipt.open('x') as f:json.dump(observed,f,indent=2,sort_keys=True);f.write('\n')
    assert observed['poll'] is None,'New queue exited immediately; preserve log and inspect'
    print('C80_INITIAL01_LAUNCHED',json.dumps(observed,sort_keys=True),flush=True)


if __name__=='__main__':main()
