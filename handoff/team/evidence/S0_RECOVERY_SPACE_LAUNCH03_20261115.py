"""Start one new S0 incremental recovery; old failed run and deliveries stay read-only."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import shutil
import tarfile

ROOT=Path('/tmp/s4_21usr_t80_20261115_1830')
BUNDLE=ROOT/'light-light126-t80-s0-a5ce90a'
OPS=ROOT/'ops-a5ce90a'
MANIFEST='6d40f4d67fc94a3b10fe3e1ece27076cf7affc33297602078721397165ca8d78'
OLD=ROOT/'light-light126-t80-s0-05c923f'
OLD_MANIFEST='4473686ec4bb1b67edd4741fbf171a89788465140b8a1e7d3a9944f4847e7ff2'
STATE='83a9b896cb541a0631f7888ea796a10a5dcd7fe863b2fdeb91756a57e0e3783d'
SERVER=Path('/storage2/2026contest/server4/s4_21usr/Desktop/IC')


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(4*1024**2),b''):h.update(block)
    return h.hexdigest()


def save(path,value):
    with Path(path).open('x') as f:
        json.dump(value,f,indent=2,sort_keys=True);f.write('\n');f.flush();os.fsync(f.fileno())


def archive_cache():
    """Archive only the selected, passed N1 contention compiler cache."""
    prior=json.loads((BUNDLE/'runs/s0_synth04/state.json').read_text())['stages']['t80_synth']
    assert prior['pid']==120765 and prior['status']=='failed' and 'No space left on device' in prior['error']
    assert not Path('/proc/120765').exists()
    run=SERVER/'light-light126-undergrad-d2-20261109/bundles/light-light126-n1-v4-20261113_013211-9305c6948c76/runs/n1_contention_01'
    stage=run/'n1_contention';cache=stage/'csrc'
    assert cache.resolve()==cache and cache.stat().st_uid==os.getuid()
    state=json.loads((run/'state.json').read_text())['stages']['n1_contention']
    assert state['status']=='passed' and sha(stage/'summary.json')==state['summary_sha256']
    summary=json.loads((stage/'summary.json').read_text())
    assert not any('csrc' in Path(name).parts for name in summary.get('artifacts',{}))
    protected={str(p):sha(p) for p in (run/'state.json',stage/'summary.json')}
    files={}
    for p in cache.rglob('*'):
        if p.is_symlink() or not p.is_file():continue
        assert p.resolve()==p and p.stat().st_uid==os.getuid()
        p.relative_to(cache)
        files[p.relative_to(cache).as_posix()]=dict(bytes=p.stat().st_size,sha256=sha(p),inode=p.stat().st_ino)
    assert len(files)==35 and sum(x['bytes'] for x in files.values())==10651781,'Candidate changed'
    archive=OPS/'n1_contention_csrc_regular_files_20261115.tar.gz'
    receipt=OPS/'n1_contention_csrc_archive_receipt.json'
    durable=stage/'csrc_regular_files_20261115.tar.gz'
    assert not archive.exists() and not receipt.exists() and not durable.exists()
    with tarfile.open(str(archive),'x:gz',compresslevel=6) as packed:
        for name in sorted(files):packed.add(str(cache/name),arcname=name,recursive=False)
    seen=set()
    with tarfile.open(str(archive),'r:gz') as packed:
        for member in packed:
            assert member.isfile() and member.name in files and member.name not in seen
            row=files[member.name];assert member.size==row['bytes']
            with packed.extractfile(member) as f:
                h=hashlib.sha256()
                for part in iter(lambda:f.read(1024**2),b''):h.update(part)
                assert h.hexdigest()==row['sha256']
            seen.add(member.name)
    assert seen==set(files)
    data=dict(source=str(cache),files=files,archive=str(archive),archive_sha256=sha(archive),
        archive_bytes=archive.stat().st_size,all_members_readback_verified=True,
        protected_results=protected,removed=[],protected_t80_written=False,old8_written=False)
    save(receipt,data)
    assert not (SERVER/'.arch02_team_lock').exists()
    rows=subprocess.check_output(['ps','-u','s4_21usr','-o','comm=']).decode().splitlines()
    assert not any(x.strip() in ('dc_shell','common_shell_ex','pt_shell','vcs','vcs1','vcs2','simv') for x in rows)
    for name,row in files.items():
        p=cache/name
        assert p.resolve()==p and p.stat().st_ino==row['inode'] and sha(p)==row['sha256']
    for name,want in protected.items():assert sha(name)==want
    for name in sorted(files):
        p=cache/name
        assert not (SERVER/'.arch02_team_lock').exists() and p.resolve()==p and p.stat().st_ino==files[name]['inode']
        p.unlink();data['removed'].append(name)
        receipt.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
    # Original result/log/source files and all symlinks/directories remain.
    with archive.open('rb') as src,durable.open('xb') as dst:
        shutil.copyfileobj(src,dst);dst.flush();os.fsync(dst.fileno())
    assert sha(durable)==data['archive_sha256']
    for name,want in protected.items():assert sha(name)==want
    data.update(persistent_archive=str(durable),free_bytes=shutil.disk_usage(str(SERVER)).free)
    receipt.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
    print('N1_COMPILER_CACHE_ARCHIVED',len(files),data['archive_sha256'],'FREE',data['free_bytes'],flush=True)


def main():
    assert sha(BUNDLE/'manifest.json')==MANIFEST
    assert sha(OLD/'manifest.json')==OLD_MANIFEST
    sys.path.insert(0,str(BUNDLE/'workspaces/arch03/scripts'))
    import s0_recovery,t80_paths
    from n1_process import ProcessLedger
    cfg=t80_paths.configure(json.loads((BUNDLE/'handoff/team/server_config.json').read_text()),
        BUNDLE,ROOT,MANIFEST,[(str(OLD),OLD_MANIFEST)])
    failed=OLD/'runs/s0_synth03/t80_s0_synth'
    t80_paths.allowed_run(failed,cfg,'S0 failed seed')
    seed=s0_recovery.verify_seed(failed,STATE)
    assert not (SERVER/'.arch02_team_lock').exists(),'Existing owner; preserve lock'
    commands=subprocess.check_output(['ps','-u','s4_21usr','-o','comm=']).decode().splitlines()
    assert not any(x.strip() in ('dc_shell','common_shell_ex','pt_shell','simv','vcs','vcs1','vcs2') for x in commands),'Existing EDA'
    assert not (BUNDLE/'runs/s0_synth05').exists(),'Preserve earlier attempt'
    origin=SERVER/'light-light126-undergrad-d2-20261109/bundles/light-light126-t80-v4-9196556-delta03/runs/t80_finish02_synth/t80_synth'
    command=[sys.executable,'-B','-u',str(BUNDLE/'workspaces/arch03/scripts/s0_server.py'),
        'synth','--session','s0_synth05','--origin',str(origin),'--runtime-root',str(ROOT),
        '--runtime-manifest-sha256',MANIFEST,'--runtime-evidence',str(OLD),OLD_MANIFEST,
        '--recovery-run',str(failed),'--recovery-state-sha256',STATE]
    archive_cache()
    control=OPS/'s0_synth05_launch';control.mkdir()
    save(control/'seed.json',seed);save(control/'command.json',command)
    child=None
    with (control/'driver.log').open('x') as log:
        try:
            child=subprocess.Popen(command,cwd=str(OPS),stdin=subprocess.DEVNULL,
                stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            save(control/'launch.json',dict(pid=child.pid,started=datetime.datetime.now().isoformat(),
                command_sha256=sha(control/'command.json'),launcher_sha256=sha(__file__),
                seed_receipt_sha256=sha(control/'seed.json'),failed_state_sha256=STATE,
                original_failure_unchanged=True,protected_desktop_written=False,old8_written=False))
        except BaseException:
            if child is not None:ProcessLedger.drain(None,child)
            raise
    print('S0_RECOVERY_STARTED',child.pid,str(control),flush=True)


if __name__=='__main__':main()
