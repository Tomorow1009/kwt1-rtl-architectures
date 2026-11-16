"""Launch only the new C32-A queue after exact bundle verification.

This is executed explicitly in the visible server terminal. Historical
directories are read-only inputs; there is no cleanup or old queue resume.
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
PAYLOAD='bc73ccd413657fd527628be76f5973de10f8cc30705580c3d5970ccbaed143bc'
SERVER=Path('/storage2/2026contest/server4/s4_21usr/Desktop/IC')
BUDGET=Path('/tmp/s4_21usr_t80_20261115_1830/light-light126-t80-s0-a5f138e/runs/s0_synth08/t80_s0_synth')
BASELINE=Path('/tmp/s4_21usr_c80_20261116_1245/light-light126-c80-74f3ae7/runs/c80_report02/c80_report/report.json')
BASELINE_SHA='46d13e9cbfac0730bec8eb7ea0b7927a9612462cf4b5cd056402c06155711cf4'
FLOAT=Path('/tmp/s4_21usr_n1_20261113_0210/n1_precision_inputs_20261113_0840/n1-recovered-float100-20261113.zip')
FLOAT_SHA='5df11251821d2d36e85e07c8a171195d9d2ed2d4084a979519d23f6df7d683e2'
INVENTORY='ae052bc1e543930abece8202a5b1439dcbd50dd4f5d7d09fb8f049eb30eeb997'


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(4*1024**2),b''):h.update(block)
    return h.hexdigest()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--manifest-sha256',required=True)
    args=parser.parse_args()
    prior=ROOT/'light-light126-c32-61246bb/runs/c32_initial02/state.json'
    assert sha(prior)=='0acf9538cd1faa74d4b63f273f6053a4f42eb79fc4800e09cb9d4663a9b3b1e9'
    stopped=json.loads(prior.read_text())
    assert stopped['status']=='failed' and stopped['pid']==205526 and stopped['stage']=='contention'
    assert [x['stage'] for x in stopped['completed']]==['soc','sequence']
    assert stopped.get('finished') and not Path('/proc/205526').exists()
    # All EDA outputs are in private /tmp. Validate actual NFS metadata writes
    # instead of requiring an arbitrary 64 MiB unused on the shared volume.
    probe=SERVER/'light-light126-undergrad-d2-20261109/c32_lock_metadata_probe_20261116_2210'
    proof=ROOT/'c32_initial03_metadata_probe.json'
    assert not probe.exists() and not proof.exists()
    before=shutil.disk_usage(str(SERVER)).free;created=False;identity=None
    result=dict(status='probing',shared_free_before=before,bytes=32768,queue_started=False)
    try:
        probe.mkdir(mode=0o700);created=True;s=probe.lstat();identity=(s.st_dev,s.st_ino,s.st_uid)
        assert probe.resolve()==probe and s.st_uid==os.getuid()
        f=probe/'probe.bin';raw=(b'C32 lock metadata probe\n'*2048)[:32768]
        with f.open('xb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
        assert f.read_bytes()==raw
        fd=os.open(str(probe),os.O_RDONLY|getattr(os,'O_DIRECTORY',0))
        try:os.fsync(fd)
        finally:os.close(fd)
        result.update(status='actual_shared_metadata_write_verified',sha256=hashlib.sha256(raw).hexdigest())
    except BaseException as exc:
        result.update(status='metadata_probe_failed_no_queue',error=str(exc));raise
    finally:
        if created:
            s=probe.lstat();assert (s.st_dev,s.st_ino,s.st_uid)==identity and probe.resolve()==probe
            f=probe/'probe.bin'
            if f.exists():
                assert f.is_file() and not f.is_symlink() and f.stat().st_uid==os.getuid();f.unlink()
            assert not any(probe.iterdir());probe.rmdir()
        result['shared_free_after']=shutil.disk_usage(str(SERVER)).free
        with proof.open('x') as stream:json.dump(result,stream,indent=2,sort_keys=True);stream.write('\n')
    assert result['status']=='actual_shared_metadata_write_verified'
    sys.path.insert(0,str(BUNDLE/'workspaces/arch03/scripts'))
    import server_run as common
    import c32_paths
    import c32_qualification
    from c32_precision_recovery import numeric_runtime
    assert common.ROOT==BUNDLE
    assert sha(BUNDLE/'manifest.json')==args.manifest_sha256
    assert sha(ROOT/'payload_91135f6.json')==PAYLOAD
    payload=json.loads((ROOT/'payload_91135f6.json').read_text())
    assert payload['source_commit']=='91135f61c97c980039793c6637d0a06888638df0'
    queue_sha=payload['files']['workspaces/arch03/scripts/c32_qualification.py']['sha256']
    assert sha(c32_qualification.__file__)==queue_sha
    prepared=json.loads((ROOT/'light-light126-c32-91135f6.prepared.json').read_text())
    assert prepared['manifest_sha256']==args.manifest_sha256 and prepared['source_preserved'] is True
    cfg=c32_paths.configure(json.loads((BUNDLE/'handoff/team/server_config.json').read_text()),
        BUNDLE,ROOT,args.manifest_sha256,[])
    common.inputs()
    assert not (SERVER/'.arch02_team_lock').exists(),'Existing collaboration lock; do not remove'
    active=[]
    for p in Path('/proc').iterdir():
        if not p.name.isdigit() or int(p.name)==os.getpid():continue
        try:
            if p.stat().st_uid!=os.getuid():continue
            cmd=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')
            if any(token in cmd for token in ('/dc_shell','/pt_shell','/simv',
                'c80_qualification.py','c80_finish.py','c32_qualification.py','c32_finish.py')):
                active.append(dict(pid=int(p.name),command=cmd))
        except (FileNotFoundError,ProcessLookupError,PermissionError):pass
    assert not active,'Existing own EDA/queue: '+repr(active)
    free=shutil.disk_usage(str(ROOT)).free
    assert free>=18*1024**3,'Insufficient private space with runtime margin'
    assert sha(BUDGET/'summary.json')=='e77fac98d9ab9032e431e8bcfe7d0e3d42f33d8b28222d37ceb48777c9bd4916'
    assert sha(BASELINE)==BASELINE_SHA
    dataset=SERVER/'hex_short_all'
    assert sha(dataset/'SHA256_FILES.json')==INVENTORY
    assert sha(FLOAT)==FLOAT_SHA
    numpy=numeric_runtime()
    session='c32_initial03'
    assert not (BUNDLE/'runs'/session).exists()
    request=ROOT/(session+'_request.json');receipt=ROOT/(session+'_launch.json');log=ROOT/(session+'.log')
    assert not any(p.exists() for p in (request,receipt,log))
    value=dict(schema='c32-qualification-v1',bundle=str(BUNDLE),bundle_manifest_sha256=args.manifest_sha256,
        runtime_root=str(ROOT),runtime_evidence=[],queue_sha256=queue_sha,
        platform=str(SERVER.parent/'e203_hbirdv2-master'),dataset=str(dataset),budget_origin=str(BUDGET),
        baseline=dict(path=str(BASELINE),sha256=BASELINE_SHA),float_archive=str(FLOAT),float_archive_sha256=FLOAT_SHA)
    with request.open('x') as stream:json.dump(value,stream,indent=2,sort_keys=True);stream.write('\n')
    command=[sys.executable,'-B',str(BUNDLE/'workspaces/arch03/scripts/c32_qualification.py'),
        '--request',str(request),'--request-sha256',sha(request),'--session',session]
    with log.open('xb') as stream:
        child=subprocess.Popen(command,cwd=str(BUNDLE),stdin=subprocess.DEVNULL,
            stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
    time.sleep(1)
    observed=dict(schema='c32-initial-qualification-launch-v1',pid=child.pid,
        started=datetime.datetime.now().isoformat(),poll=child.poll(),command=command,
        session=session,queue=str(BUNDLE/'runs'/session),log=str(log),runtime_free_bytes=free,
        shared_free_bytes=shutil.disk_usage(str(SERVER)).free,numerical_runtime=numpy,
        manifest_sha256=args.manifest_sha256,payload_sha256=PAYLOAD,request_sha256=sha(request),
        launch_script_sha256=sha(__file__),protected_T80_modified=False,old8_modified=False,
        stage_accepted=False,c32_b_started=False,g32_started=False)
    with receipt.open('x') as stream:json.dump(observed,stream,indent=2,sort_keys=True);stream.write('\n')
    assert observed['poll'] is None,'Queue exited immediately; preserve log and inspect'
    print('C32_INITIAL03_LAUNCHED',json.dumps(observed,sort_keys=True),flush=True)


if __name__=='__main__':main()
