"""Archive completed B0 native-SAIF compiler cache, then start single-lock P80 sweep05.

Only 40 regular cache files are unlinked after complete archive verification.
T80 desktop, old-eight-lane data, sources, logs, executables and results stay.
"""
import datetime,hashlib,json,os,shutil,subprocess,sys,tarfile
from pathlib import Path

ROOT=Path('/tmp/s4_21usr_p80_20261116_0315')
SERVER=Path('/storage2/2026contest/server4/s4_21usr/Desktop/IC')
BUNDLE=SERVER/'light-light126-undergrad-d2-20261109/bundles/light-light126-systolic-b-v3-20261112_114355-cede0e139a01e'
RUN=BUNDLE/'runs/systolic_b_power_final01_activity12'
STAGE=RUN/'systolic_b_saif'
CACHE=STAGE/'csrc'
LOCK=SERVER/'.arch02_team_lock'


def digest(stream):
    h=hashlib.sha256()
    for block in iter(lambda:stream.read(1024**2),b''):h.update(block)
    return h.hexdigest()


def sha(path):
    with Path(path).open('rb') as f:return digest(f)


def save(path,value):
    temporary=path.with_suffix('.pending')
    with temporary.open('w') as f:
        json.dump(value,f,indent=2,sort_keys=True);f.write('\n');f.flush();os.fsync(f.fileno())
    temporary.replace(path)


def idle():
    assert not LOCK.exists(),'Preserve existing shared lock'
    names=subprocess.check_output(['ps','-u',str(os.getuid()),'-o','comm=']).decode().splitlines()
    assert not any(n.strip() in ('dc_shell','dc_shell-xg-t','common_shell_ex','pt_shell','vcs','vcs1','vcs2','simv') for n in names),'Existing own EDA'
    prefix=str(CACHE)+'/'
    for proc in Path('/proc').iterdir():
        if not proc.name.isdigit() or proc.name==str(os.getpid()):continue
        try:
            if proc.stat().st_uid!=os.getuid():continue
            paths=[proc/'cwd']+list((proc/'fd').iterdir())
            for p in paths:
                try:target=str(p.resolve())
                except OSError:continue
                assert target!=str(CACHE) and not target.startswith(prefix),'Cache is open by '+proc.name
            assert prefix not in (proc/'maps').read_text(),'Cache is mapped by '+proc.name
        except (FileNotFoundError,ProcessLookupError,PermissionError):continue


def main():
    assert CACHE.resolve()==CACHE and CACHE.stat().st_uid==os.getuid()
    assert 'T80_Delivery_20261113' not in CACHE.parts and BUNDLE.name=='light-light126-systolic-b-v3-20261112_114355-cede0e139a01e'
    prior=json.loads((ROOT/'p80_sweep04.json').read_text())
    assert prior['status']=='starting' and not prior['completed']
    assert 'No space left on device' in (ROOT/'p80_sweep04.launcher.log').read_text()
    state=json.loads((RUN/'state.json').read_text())['stages']['systolic_b_saif']
    assert state['status']=='passed' and sha(STAGE/'summary.json')==state['summary_sha256']
    report=json.loads((STAGE/'summary.json').read_text())
    assert report['status']=='B_native_saif_function_and_complete_windows_passed'
    assert len(report['cases'])==12 and report['source_netlist_unchanged'] is True
    gate=Path(report['gate_run']);gate.relative_to(BUNDLE)
    assert sha(gate/'summary.json')==report['gate_summary_sha256']
    assert sha(gate/'source_inputs.json')==report['source_inputs_sha256']
    frozen={str(p):sha(p) for p in (RUN/'state.json',STAGE/'summary.json',STAGE/'simv',gate/'summary.json',gate/'source_inputs.json')}
    contract={'files':json.loads((gate/'source_inputs.json').read_text())}
    unchanged={str(p):(p.stat().st_dev,p.stat().st_ino,p.stat().st_size,p.stat().st_mtime_ns,p.stat().st_ctime_ns) for p in STAGE.iterdir() if p.is_file()}
    assert not any(str(name).startswith('csrc/') for name in report['artifacts'])
    assert not any(str(name).startswith(str(CACHE)+'/') for name in contract['files'])
    assert all(sha(name)==want for name,want in contract['files'].items())
    idle()
    files={}
    for p in CACHE.rglob('*'):
        if not p.is_file() or p.is_symlink():continue
        assert p.resolve()==p and p.stat().st_uid==os.getuid()
        files[p.relative_to(CACHE).as_posix()]=dict(bytes=p.stat().st_size,sha256=sha(p),inode=p.stat().st_ino)
    assert len(files)==40 and sum(x['bytes'] for x in files.values())==80788435,'Candidate changed'
    archive=ROOT/'b0_saif_csrc_20261116.tar.gz'
    receipt=ROOT/'b0_saif_csrc_20261116.receipt.json'
    durable=STAGE/'csrc_regular_files_20261116_p80.tar.gz'
    assert not any(p.exists() for p in (archive,receipt,durable))
    with tarfile.open(str(archive),'x:gz',compresslevel=6) as tar:
        for name in sorted(files):tar.add(str(CACHE/name),arcname=name,recursive=False)
    with archive.open('rb') as f:os.fsync(f.fileno())
    seen=set()
    with tarfile.open(str(archive),'r:gz') as tar:
        for member in tar:
            assert member.isfile() and member.name in files and member.name not in seen
            assert member.size==files[member.name]['bytes']
            with tar.extractfile(member) as f:assert digest(f)==files[member.name]['sha256']
            seen.add(member.name)
    assert seen==set(files)
    assert archive.stat().st_size+2*1024**2<sum(x['bytes'] for x in files.values()),'Archive cannot recover useful space'
    info=dict(schema='p80-b0-cache-lossless-archive-v1',source=str(CACHE),files=files,
        archive=str(archive),archive_sha256=sha(archive),archive_bytes=archive.stat().st_size,
        verified_members=True,frozen_results=frozen,removed=[],protected_T80_modified=False,old8_modified=False)
    save(receipt,info);idle()
    for name,row in files.items():
        p=CACHE/name
        assert p.resolve()==p and p.stat().st_ino==row['inode'] and sha(p)==row['sha256']
    assert all(sha(name)==want for name,want in frozen.items())
    for name,row in sorted(files.items(),key=lambda pair:-pair[1]['bytes']):
        p=CACHE/name
        assert not LOCK.exists() and p.resolve()==p and not p.is_symlink() and p.stat().st_ino==row['inode']
        p.unlink();info['removed'].append(name);save(receipt,info)
    with archive.open('rb') as source,durable.open('xb') as dest:
        shutil.copyfileobj(source,dest);dest.flush();os.fsync(dest.fileno())
    assert sha(durable)==info['archive_sha256']
    assert all(sha(name)==want for name,want in frozen.items())
    assert all(sha(name)==want for name,want in contract['files'].items())
    assert all((Path(name).stat().st_dev,Path(name).stat().st_ino,Path(name).stat().st_size,Path(name).stat().st_mtime_ns,Path(name).stat().st_ctime_ns)==stamp for name,stamp in unchanged.items())
    info.update(persistent_archive=str(durable),persistent_verified=True,
        free_bytes=shutil.disk_usage(str(SERVER)).free,finished=datetime.datetime.now().isoformat())
    save(receipt,info)
    print('P80_CACHE_ARCHIVED',len(files),info['archive_sha256'],'FREE',info['free_bytes'],flush=True)
    path=ROOT/'p80_sweep05_controller.py'
    assert sha(path)=='6473175d150bd33df198650b476829601458dba93062ff6e8202e2f0421f971e'
    assert not (ROOT/'p80_sweep05.json').exists()
    idle()
    with (ROOT/'p80_sweep05.launcher.log').open('x') as log:
        child=subprocess.Popen([sys.executable,'-B','-u',str(path)],cwd=str(ROOT),stdin=subprocess.DEVNULL,
            stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    save(ROOT/'p80_sweep05_launch_receipt.json',dict(pid=child.pid,script_sha256=sha(path),
        cache_receipt_sha256=sha(receipt),prior_failed_queue_preserved=True))
    print('P80_SWEEP05_LAUNCHED',child.pid,flush=True)


if __name__=='__main__':main()
