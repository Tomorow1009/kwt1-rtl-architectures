"""Preserve frozen inputs; start T64 stages without GUI delays between jobs."""
from pathlib import Path
import datetime,hashlib,json,os,subprocess,sys

ROOT=Path('/tmp/s4_21usr_t64_20261115_1510')
BUNDLE=ROOT/'light-light126-t64-resume-b9155b4'
OPS=ROOT/'ops-b9155b4'
PROJECT=Path('/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109')
MANIFEST='c80e6f3355832f6a072cc25353c94f5e8825e49ca274b82510361b8201170804'
OPS_MANIFEST='6f0874cbcd5bd2ac3cc98f06de9aaf9188599f57c85a41fc401a30af77f9de78'
sys.path[:0]=[str(OPS/'scripts'),str(BUNDLE/'workspaces/arch03/scripts')]
import t64_finish_queue as queue
import t64_paths,t64_saif
from n1_process import atomic_save

def file_sha(path):
    value=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(4*1024**2),b''):value.update(block)
    return value.hexdigest()

def read(path):return json.loads(Path(path).read_text())

def main():
    assert queue.common.ROOT==BUNDLE
    assert file_sha(BUNDLE/'manifest.json')==MANIFEST
    cfg=t64_paths.configure(read(BUNDLE/'handoff/team/server_config.json'),BUNDLE,ROOT,MANIFEST)
    queue.common.inputs();queue.operations_identity(OPS_MANIFEST)
    lock=Path(cfg['server_root'])/'.arch02_team_lock';assert not lock.exists()
    control=BUNDLE/'runs/t64_start01'
    for name in ('t64_start01','t64_soc03','t64_batch20_01','t64_finish01'):
        assert not (BUNDLE/'runs'/name).exists(), 'Preserve existing session '+name
    archive=Path('/tmp/s4_21usr_n1_20261113_0210/n1_precision_inputs_20261113_0840/n1-recovered-float100-20261113.zip')
    archive_sha='5df11251821d2d36e85e07c8a171195d9d2ed2d4084a979519d23f6df7d683e2'
    assert file_sha(archive)==archive_sha
    numpy=Path('/tmp/s4_21usr_n1_20261113_0210/n1_numpy1195_20261113_0905');assert numpy.is_dir()
    qualification=PROJECT/'bundles/light-light126-systolic-b-v3-20261112_114355-ced0e139a01e/runs/systolic_b_r4_crosscheck02/native_saif_r4_crosscheck'
    qualification_sha='a0a9bc6280e7fe5f35b666535157700aac1d9c0b4490873b6199ba9b5c662d26'
    t64_saif.qualification(qualification,qualification_sha,cfg)
    control.mkdir(parents=True)
    state=dict(status='preparing_shared_lock_space',pid=os.getpid(),completed=[],child_pid=None,
               script_sha256=file_sha(__file__),started=datetime.datetime.now().isoformat(),full100_allowed=False)
    atomic_save(control/'state.json',state)
    try:
        # Keep both original T64 input paths and identical bytes; remove only
        # duplicate inode storage. These source packages have never run jobs.
        old=PROJECT/'bundles/light-light126-t64-v4-65d2507-delta01'
        keep=old.with_name('light-light126-t64-v4-65d2507-fix02')
        assert old.resolve()==old and keep.resolve()==keep and not (old/'runs').exists()
        a=read(old/'manifest.json');b=read(keep/'manifest.json')
        assert file_sha(keep/'manifest.json')=='6632a4f266d48f50fd8a9e542cb6e03f05653d7ade3153903b38c3282c3339c1'
        changes=[]
        for name,digest in a['files'].items():
            if not name.startswith(('firmware/','firmware_contention/','firmware_sequence/')):continue
            p=old/name;q=keep/name
            assert p.resolve()==p and q.resolve()==q and p.is_file() and q.is_file()
            assert file_sha(p)==digest==b['files'][name]==file_sha(q)
            stat=p.stat();assert stat.st_uid==q.stat().st_uid==os.getuid() and stat.st_dev==q.stat().st_dev
            if stat.st_nlink!=1 or stat.st_size<65536:continue
            changes.append(dict(path=str(p),retained_identical_path=str(q),sha256=digest,
                                bytes=stat.st_size,allocated_bytes=stat.st_blocks*512))
        assert changes
        atomic_save(control/'firmware_dedup_prepared.json',dict(files=changes,all_paths_and_bytes_retained=True))
        for row in changes:
            p=Path(row['path']);q=Path(row['retained_identical_path']);temp=p.with_name(p.name+'.t64_storage_link')
            assert not temp.exists() and file_sha(p)==row['sha256']==file_sha(q)
            os.link(str(q),str(temp));assert file_sha(temp)==row['sha256'];os.replace(str(temp),str(p))
            assert p.stat().st_ino==q.stat().st_ino and file_sha(p)==row['sha256']
        atomic_save(control/'firmware_dedup_complete.json',dict(files=changes,all_paths_and_bytes_retained=True,
                    reclaimed_duplicate_bytes=sum(x['allocated_bytes'] for x in changes)))
        runtime=['--runtime-root',str(ROOT),'--runtime-manifest-sha256',MANIFEST]
        script=str(BUNDLE/'workspaces/arch03/scripts/t64_server.py')
        def start(stage,session,extra=()):
            command=[sys.executable,'-B','-u',script,stage,'--session',session]+runtime+list(extra)
            return queue.run_child(command,BUNDLE/'runs'/session/('t64_'+stage),
                                   't64_'+stage,control,state,lock)
        soc=start('soc','t64_soc03')
        dataset=PROJECT.parent/'hex_short_all'
        batch=start('batch20','t64_batch20_01',['--dataset',str(dataset)])
        record=read(Path(batch['run']).parent/'state.json')['stages']['t64_batch20']
        request=dict(schema='t64-complete-current-stage-v1',bundle=str(BUNDLE),bundle_manifest_sha256=MANIFEST,
                     runtime_root=str(ROOT),operations=str(OPS),operations_manifest_sha256=OPS_MANIFEST,
                     queue_sha256=file_sha(OPS/'scripts/t64_finish_queue.py'),batch_run=batch['run'],
                     batch_pid=record['pid'],batch_started=record['started'],dataset=str(dataset),
                     archive=str(archive),archive_sha256=archive_sha,numpy_root=str(numpy),
                     qualification_run=str(qualification),qualification_sha256=qualification_sha)
        atomic_save(control/'finish_request.json',request)
        state.update(status='remaining_evidence',soc_reference=soc,batch_reference=batch)
        atomic_save(control/'state.json',state)
        queue.execute(request,BUNDLE/'runs/t64_finish01')
        state.update(status='reports_ready_review_required',finished=datetime.datetime.now().isoformat())
    except BaseException as error:
        state.update(status='failed',error=str(error),finished=datetime.datetime.now().isoformat());raise
    finally:atomic_save(control/'state.json',state)

if __name__=='__main__':main()
