"""Copy the completed G32 evidence and exact auxiliary tools, never delete source."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT=Path('/tmp/s4_21usr_g32_20261117_0810')
BUNDLE=ROOT/'light-light126-g32-0e16994'
MANIFEST='3524e2726880684c1c5681ef90da3a1ca41d78daf20d0df5b648e633b6e42f4a'
INITIAL_SHA='de797dab25bccd50134556e363bb074ebe94a22650965495f4e9820cda9d4df5'
NATIVE_SHA='add21a6f755ae86cc1496886ff16aa8c03ddbef2d521db02ee09c4dc3cc979c1'
OPS=Path('/tmp/s4_21usr_g32_ops_20261117_0938')
SOURCES={
    '/tmp/s4_21usr_g32_ops_20261117_0845':'86f015d5d33e689dc0bbb668e79976ab81ad637b9b45bf95ededb228e9cfbf26',
    '/tmp/s4_21usr_g32_recoveryops_20261117_0922':'4fa594b4db319a998890275724efacbf9e080fa607c2e1919d9782d8e3a1cbcd',
    '/tmp/s4_21usr_g32_recoveryops_20261117_0933':'cfc31793de02b5795d272f84e3f7cb537a02ad10749d9628fb92a3d368ba02bd',
    str(OPS):'f614bef8b387b3943914cd7cd7407934bac2ba47396be15f95e789d1b07d21d4',
    '/tmp/s4_21usr_g32_reviewops_20261117_0948':'df1007b0ad6852b1d9f47bc5d3599715f739fe816271cc07136fa64444f9917c'}


def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def alive(pid):return Path('/proc/%d'%pid).exists()


def save(p,d):
    with Path(p).open('x') as f:
        json.dump(d,f,sort_keys=True,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())


def tools_manifest(root,expected):
    root=Path(root);assert root.resolve()==root and root.stat().st_uid==os.getuid()
    assert sha(root/'manifest.json')==expected
    files={'manifest.json':expected}
    for name,want in read(root/'manifest.json')['files'].items():
        p=root/name
        assert Path(name).name==name and p.resolve()==p and not p.is_symlink() and p.is_file()
        assert p.stat().st_uid==os.getuid() and sha(p)==want
        files[name]=want
    return files


def main():
    p=argparse.ArgumentParser();p.add_argument('--recovery-state-sha256',required=True)
    p.add_argument('--finish-state-sha256',required=True);p.add_argument('--report-sha256',required=True)
    p.add_argument('--export-state-sha256',required=True);p.add_argument('--launcher-manifest-sha256',required=True)
    p.add_argument('--name',required=True);a=p.parse_args()
    assert re.fullmatch('g32-runtime-[0-9]{8}_[0-9]{4}-[A-Za-z0-9_-]+',a.name)
    own=Path(__file__).resolve().parent;sources=dict(SOURCES,**{str(own):a.launcher_manifest_sha256})
    inventories={path:tools_manifest(path,want) for path,want in sources.items()}
    assert sha(BUNDLE/'manifest.json')==MANIFEST
    sys.path[:0]=[str(OPS),str(BUNDLE/'workspaces/arch03/scripts')]
    import g32_archive_runtime as archive
    from g32_recovery_contract import recovered_initial
    from g32_archive_contract import completed_queue,joined_queues,exported_report
    initial=BUNDLE/'runs/g32_initial01';recovery=BUNDLE/'runs/g32_recovery01';finish=BUNDLE/'runs/g32_finish01'
    prior=recovered_initial(initial,INITIAL_SHA,recovery,a.recovery_state_sha256,alive)
    final=completed_queue(finish,a.finish_state_sha256,alive,'finish')
    joined=joined_queues(prior,final);report=BUNDLE/'runs/g32_report01/g32_report'
    exported_report(report,a.report_sha256,joined)
    control=ROOT/'g32_export_review01';s=read(control/'state.json')
    assert sha(control/'state.json')==a.export_state_sha256 and not alive(s['pid'])
    assert s['status']=='facts_joined_manual_conclusion_required' and s['finished']
    assert s['report_sha256']==a.report_sha256 and sha(s['snapshot'])==s['snapshot_sha256']
    for child_path in control.glob('*_process.json'):
        child=read(child_path);assert not alive(child['pid'])
        exit_path=child_path.with_name(child_path.name.replace('_process.json','_exit.json'));v=read(exit_path)
        assert v['returncode']==0 and v['wait_completed'] is True
    native=ROOT/'g32_icg_native_review01.json';assert sha(native)==NATIVE_SHA
    assert read(native)['netlist_sha256']==read(report/'report.json')['netlist_sha256']
    lock=Path('/storage2/2026contest/server4/s4_21usr/Desktop/IC/.arch02_team_lock')
    assert not lock.exists(),'Preserve the current team lock'
    destination=archive.BACKUPS/a.name;work=Path('/tmp')/('s4_21usr_'+a.name.replace('-','_'))
    snapshot=ROOT/'completed_operations_snapshot01'
    assert not destination.exists() and not work.exists() and not snapshot.exists()
    request=dict(schema=archive.SCHEMA,runtime_root=str(ROOT),bundle=str(BUNDLE),bundle_manifest_sha256=MANIFEST,
        runtime_evidence=[],initial=dict(queue=str(initial),state_sha256=INITIAL_SHA),
        qualification_recovery=dict(queue=str(recovery),state_sha256=a.recovery_state_sha256),
        finish=dict(queue=str(finish),state_sha256=a.finish_state_sha256),report_run=str(report),
        report_sha256=a.report_sha256,destination=str(destination),storage_profile='copy_only_512MiB')
    archive.evidence(request,BUNDLE)
    # Auxiliary code is outside the frozen production bundle. Include exact
    # copies in the final runtime archive so /tmp operations are not its only copy.
    snapshot.mkdir(mode=0o700);copied={}
    for path,files in inventories.items():
        src=Path(path);dest=snapshot/src.name;dest.mkdir(mode=0o700)
        for name,want in files.items():
            assert sha(src/name)==want
            with (dest/name).open('xb') as f:
                f.write((src/name).read_bytes());f.flush();os.fsync(f.fileno())
            assert sha(dest/name)==sha(src/name)==want
            copied[str((dest/name).relative_to(snapshot))]=want
    save(snapshot/'receipt.json',dict(schema='g32-completed-operations-copy-v1',files=copied,
        originals_modified=False,failed_attempt_sources_preserved=True,production_bundle_modified=False))
    work.mkdir(mode=0o700);request_path=work/'request.json';save(request_path,request)
    environment=os.environ.copy();environment['PYTHONPATH']=os.pathsep.join((str(OPS),str(BUNDLE/'workspaces/arch03/scripts')))
    environment['PYTHONDONTWRITEBYTECODE']='1'
    command=[sys.executable,'-B','-u',str(Path(archive.__file__)),'--request',str(request_path),
        '--request-sha256',sha(request_path)]
    with (work/'archive.log').open('xb') as f:
        child=subprocess.Popen(command,cwd=str(work),env=environment,stdin=subprocess.DEVNULL,
            stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
    result=dict(pid=child.pid,started=datetime.datetime.now().isoformat(),request_sha256=sha(request_path),
        command=command,source_sha256=sha(__file__),destination=str(destination),control=str(work),
        operations_snapshot_receipt_sha256=sha(snapshot/'receipt.json'),source_deleted=False,
        archive_implies_acceptance=False,old8_modified=False,T80_modified=False)
    save(work/'launch.json',result);print('G32_ARCHIVE_STARTED',json.dumps(result,sort_keys=True),flush=True)


if __name__=='__main__':main()
