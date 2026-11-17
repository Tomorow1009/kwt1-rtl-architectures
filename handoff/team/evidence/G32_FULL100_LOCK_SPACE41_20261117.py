"""Free exactly nine already archived B0 CSV duplicates, then fresh G32 run.

No source, log, summary, backup, old8, desktop T80 or frozen G32 file is removed.
Archive identity, completed B0 batch, no users and every duplicate are checked.
Preserve failed full100_01; only start new full100_02 after lock-space recovery.
"""
import hashlib, importlib.util, json, os, re, shutil, subprocess, sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path('/tmp/s4_21usr_g32_20261117_1530')
BUNDLE=ROOT/'light-light126-g32-full100-398a58b'
OUT=ROOT/'lock_space41'
HELPER=Path('/tmp/s4_21usr_c80_20261116_1245/ops-b0-cleanup16-c8c730d/C80_B0_DUPLICATES_CLEANUP16_20261116.py')
HELPER_SHA='0e98728332e0ba048142231f414322dc3aaf21e287b3bde0bc4121124c976441'
PREFIX='bundles/light-light126-systolic-b-v3-20261112_114355-ced0e139a01e/runs/systolic_b_final02_final1200/systolic_b_batch/'


def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(4*1024**2),b''):h.update(b)
    return h.hexdigest()


def read(p):return json.loads(Path(p).read_text())
def load(name,p):
    spec=importlib.util.spec_from_file_location(name,str(p));m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m);return m


def failed():
    row=read(BUNDLE/'runs/full100_01/state.json')
    assert row['status']=='failed' and row['pid']==95634 and row['completed']==[] and row.get('finished')
    assert 'No space left on device' in row['error'] and '.arch02_team_lock' in row['error']
    assert not Path('/proc/95634').exists() and not (BUNDLE/'runs/full100_02').exists()


def main():
    assert not OUT.exists() and sha(HELPER)==HELPER_SHA
    base=load('space41_idle',HELPER)
    assert sha(base.PREFLIGHT)==base.PREFLIGHT_SHA
    checked=load('space41_backup',base.PREFLIGHT)
    assert sha(base.BUNDLE/'manifest.json')==base.MANIFEST_SHA
    deps=read(base.BUNDLE/'manifest.json')['files']
    for n in ('n1_archive_runtime.py','n1_paths.py','partition_synth_contract.py'):
        rel='workspaces/arch03/scripts/'+n;assert sha(base.BUNDLE/rel)==deps[rel]
    sys.path.insert(0,str(base.BUNDLE/'workspaces/arch03/scripts'))
    import n1_archive_runtime as archive
    project=checked.PROJECT;lock=project.parent/'.arch02_team_lock'
    fixed={checked.BACKUP/'manifest.json':checked.MANIFEST_SHA,
        checked.BACKUP/'receipt.json':checked.RECEIPT_SHA,
        checked.BACKUP/'completed-evidence.tar.gz':checked.ARCHIVE_SHA,
        checked.PRIOR:checked.PRIOR_SHA,HELPER:HELPER_SHA,
        BUNDLE/'manifest.json':'1577690aba585e473c7d0174ebca95618edc032e1184cf99a6d350bfa75d9052',
        ROOT/'full100_request.json':'e260f5fc1b4f2a4b1c475f711f4d046a42b83e766040519892e3bfccab7bbfd1'}
    index={r['path']:r for r in read(checked.BACKUP/'manifest.json')['files']}
    for n in (PREFIX+'summary.json',str(Path(PREFIX).parent/'state.json')):
        fixed[project/n]=index[n]['sha256']
    stamps={str(p):checked.stamp(p) for p in fixed}
    assert all(sha(p)==h and checked.stamp(p)==stamps[str(p)] for p,h in fixed.items())
    prior=read(checked.PRIOR)
    assert prior['archive_sha256']==checked.ARCHIVE_SHA and prior['all_archive_members_readback_verified']==63653
    batch=read(project/(PREFIX+'summary.json'))
    assert batch['status']=='passed' and batch['tasks']==1200 and batch['checked_outputs']==30412800 and batch['failed']==0
    rows=[];files=[]
    for n,r in sorted(index.items()):
        if not n.startswith(PREFIX) or not re.fullmatch(r'cases/sample_[0-9]{6}_layer_[0-9]{2}/task\.csv',n[len(PREFIX):]):continue
        p=project/n
        if not p.exists():continue
        stamp=checked.stamp(p)
        assert sha(p)==r['sha256'] and p.stat().st_size==r['bytes'] and checked.stamp(p)==stamp
        rows.append(dict(path=n,sha256=r['sha256'],bytes=r['bytes'],stamp=stamp));files.append(p)
    assert len(rows)==9 and sum(r['bytes'] for r in rows)==2898594
    failed();observation=base.idle(archive,lock,files)
    OUT.mkdir(mode=0o700)
    state=dict(status='verified_intent',files=rows,removed_files=0,removed_bytes=0,
        source_sha256=sha(__file__),archive_sha256=checked.ARCHIVE_SHA,
        archive=str(checked.BACKUP/'completed-evidence.tar.gz'),process_observation=observation,
        old8_modified=False,T80_modified=False,logs_modified=False,backups_modified=False,
        restore='Restore exactly the listed CSV members from the retained full B0 archive, verify SHA and bytes.')
    archive.save(OUT/'intent.json',state)
    try:
        with (OUT/'journal.jsonl').open('x') as log:
            for row,p in zip(rows,files):
                base.idle(archive,lock,files);failed()
                assert all(checked.stamp(q)==stamps[str(q)] for q in fixed)
                assert checked.stamp(p)==row['stamp'] and sha(p)==row['sha256']
                log.write(json.dumps(dict(action='remove_intent',**row))+'\n');log.flush();os.fsync(log.fileno())
                assert not lock.exists()
                p.unlink();archive.sync_dir(p.parent)
                state['removed_files']+=1;state['removed_bytes']+=row['bytes']
                log.write(json.dumps(dict(action='removed',path=row['path']))+'\n');log.flush();os.fsync(log.fileno())
        assert all(checked.stamp(q)==stamps[str(q)] for q in fixed)
        state.update(status='verified_duplicates_removed_archive_retained',finished=archive.now(),
            free_after=shutil.disk_usage(str(project)).free)
    except BaseException as e:
        state.update(status='failed_preserved',error=str(e));raise
    finally:archive.save(OUT/'state.json',state)
    env=dict(os.environ);env['PYTHONDONTWRITEBYTECODE']='1'
    req=ROOT/'full100_request.json'
    cmd=[sys.executable,'-B',str(BUNDLE/'workspaces/arch03/scripts/g32_full100_queue.py'),
        '--request',str(req),'--request-sha256',sha(req),'--session','full100_02']
    with (ROOT/'full100_02_driver.log').open('xb') as log:
        p=subprocess.Popen(cmd,cwd=str(BUNDLE),stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,
            env=env,start_new_session=True)
    archive.save(OUT/'launch.json',dict(pid=p.pid,command=cmd,recovery_sha256=sha(OUT/'state.json')))
    print('SPACE41_AND_FULL100_02',p.pid,state['removed_files'],state['removed_bytes'],state['free_after'],flush=True)
    print('RECOVERY_SHA',sha(OUT/'state.json'),flush=True)


if __name__=='__main__':main()
