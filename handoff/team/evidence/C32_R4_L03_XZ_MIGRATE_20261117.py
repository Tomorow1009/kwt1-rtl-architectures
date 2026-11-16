"""Migrate exactly one proven R4 L03 gzip to a complete durable XZ copy.

Default is read-only preflight. --migrate is a separate deliberate operation,
after full staging has exited. Preserve old receipts and the exact gzip copy
in /tmp. Hold the original team lock and reject observed source users and
unclassified protected processes. The three recorded desktop helper processes
are explicitly classified; their file descriptors remain unobservable, never
claimed inspected. Full staged byte copies are a separate prerequisite.
Never touch T80, old8, other R4 layers or frozen S0/P80/C80 files.
"""
import argparse
import datetime
import hashlib
import json
import lzma
import os
from pathlib import Path
import shutil
import sys

ROOT=Path('/tmp/s4_21usr_c32_20261116_2010')
BUNDLE=ROOT/'light-light126-c32-repair-5828804'
MANIFEST='321c38f06fe155e491bcb580703eb5fdc96755f4bf4876d7c5545c6ae3b0dd07'
PROJECT=Path('/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109')
BASE=PROJECT/'bundles/light-light126-systolic-b-v3-20261112_114355-ced0e139a01e/runs/r4_waves_lossless_archive02'
SOURCE=BASE/'layer_03.vcd.gz'
STAGE=Path('/tmp/s4_21usr_r4_l03_xzstage_20261117')
CONTROL=Path('/tmp/s4_21usr_r4_l03_xzmigrate02_20261117')
DEST=PROJECT/'backups/r4-l03-xz-20261117'
CHUNK=4*1024**2
SESSION_HELPERS={
    10519:('gnome-keyring-d','gnome-keyring-daemon','15432'),
    79103:('gnome-pty-helpe','gnome-pty-helper','139476165'),
    202972:('gnome-pty-helpe','gnome-pty-helper','130547063')}


def need(ok,message):
    if not ok:raise ValueError(message)


def read(p):return json.loads(Path(p).read_text())
def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for data in iter(lambda:stream.read(CHUNK),b''):h.update(data)
    return h.hexdigest()


def stamp(path):
    s=Path(path).lstat();return [s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns]


def usage_observation(archive,proc=Path('/proc'),uid=None):
    """Keep visibility limits explicit; no unrestricted permission-error skip.

The exact process identities were read on 2026-11-17 06:01:02.088142.
Unknown protected PIDs, changed identities or observed source users reject.
This observation alone never authorizes removing a source archive.
"""
    if uid is None:uid=os.getuid()
    result=archive.no_open_users([SOURCE],copy_only=True);classified=[]
    need(result['observed_open_runtime_uses']==0,'R4 archive is in observed use')
    for row in result['inaccessible_owned_processes']:
        pid=row['pid'];need(pid in SESSION_HELPERS and row['errno']==13,'Unclassified protected process')
        p=proc/str(pid);name,argv0,start=SESSION_HELPERS[pid]
        def ticks():return (p/'stat').read_text().rsplit(')',1)[1].split()[19]
        need(p.stat().st_uid==uid and ticks()==start and (p/'comm').read_text().strip()==name and
             (p/'cmdline').read_bytes().split(b'\0')[0].decode()==argv0 and ticks()==start,
             'Protected desktop helper identity changed')
        classified.append(dict(pid=pid,comm=name,argv0=argv0,start_ticks=start,
            descriptors_observed=False,classification='existing_desktop_session_helper'))
    result['classified_protected_session_helpers']=classified
    result['visibility_limit_preserved']=True
    result['observation_alone_authorizes_deletion']=False
    return result


def imports():
    sys.dont_write_bytecode=True;sys.path.insert(0,str(BUNDLE/'workspaces/arch03/scripts'))
    import c32_paths as paths
    import n1_archive_runtime as archive
    cfg=paths.configure(read(BUNDLE/'handoff/team/server_config.json'),BUNDLE,ROOT,MANIFEST,[])
    mf=read(BUNDLE/'manifest.json')['files']
    for module in (paths,archive,sys.modules['n1_paths']):
        p=Path(module.__file__).resolve();name=p.relative_to(BUNDLE).as_posix()
        need(sha(p)==mf[name],'Frozen archive helper changed')
    return cfg,archive


def verify(stage_sha):
    need(STAGE.resolve()==STAGE and STAGE.stat().st_uid==os.getuid() and
         sha(STAGE/'state.json')==stage_sha,'Staging identity changed')
    s=read(STAGE/'state.json');ref=s['source_reference']
    need(s['status']=='fully_verified_staging_original_retained' and
         s['source_script_sha256']=='1ab445bf8f621c84f40adb0db4e4fa43fbb5f18e660e13cd720a820b0c286f04' and
         s['gzip_copy_verified'] and s['full_xz_readback_verified'] and
         not s['source_modified'] and not s['source_deleted'] and not s['durable_migration_completed'] and
         not Path('/proc/%d'%s['pid']).exists(),'Only a fully completed, exited staging run qualifies')
    need(SOURCE.resolve()==SOURCE and not SOURCE.is_symlink() and SOURCE.stat().st_uid==os.getuid() and
         str(SOURCE)==s['source']==ref['archive'] and stamp(SOURCE)==s['source_stamp'] and
         SOURCE.stat().st_size==ref['archive_bytes']==7662823694 and SOURCE.stat().st_nlink==1,
         'Only the exact unchanged R4 L03 gzip is in scope')
    receipt=BASE/'layer_03.vcd.json'
    need(sha(receipt)==s['source_receipt_sha256'] and read(receipt)==ref,'Original R4 receipt changed')
    need(s['raw_bytes']==ref['original_bytes']==12584787471 and s['raw_sha256']==ref['original_sha256'],
         'Staged XZ does not preserve the original VCD')
    for file,size,want in (
        (SOURCE,ref['archive_bytes'],ref['archive_sha256']),
        (STAGE/'original_layer_03.vcd.gz',ref['archive_bytes'],ref['archive_sha256']),
        (STAGE/'layer_03.vcd.xz',s['xz_bytes'],s['xz_sha256'])):
        need(file.resolve()==file and not file.is_symlink() and file.stat().st_size==size and sha(file)==want,
             'Full source/staged copy byte identity failed')
    need(ref['archive_bytes']-s['xz_bytes']>=2*1024**3,'Migration must recover at least 2GiB')
    need(DEST.parent.resolve()==DEST.parent and DEST.parent.stat().st_uid==os.getuid() and
         DEST.parent.stat().st_dev==SOURCE.stat().st_dev!=STAGE.stat().st_dev and not DEST.exists(),
         'Fresh durable target on the original shared filesystem required')
    return s


def main(stage_sha,migrate):
    cfg,archive=imports();proof=verify(stage_sha)
    observation=usage_observation(archive)
    if not migrate:
        print('R4_L03_MIGRATION_PREFLIGHT',proof['xz_bytes'],proof['potential_saved_bytes'],
              json.dumps(observation,sort_keys=True),'NO_MUTATION',flush=True);return
    need(not CONTROL.exists(),'Preserve previous migration attempts')
    CONTROL.mkdir(mode=0o700)
    state=dict(schema='r4-l03-durable-xz-migration-v1',status='preflight',pid=os.getpid(),
        source=str(SOURCE),destination=str(DEST),stage_sha256=stage_sha,staging=proof,
        started=datetime.datetime.now().isoformat(),source_script_sha256=sha(__file__),
        source_deleted=False,source_gzip_copy=str(STAGE/'original_layer_03.vcd.gz'),
        raw_VCD_restorable_from_XZ=True,old_receipt_modified=False,old8_modified=False,T80_modified=False)
    archive.save(CONTROL/'state.json',state)
    # Fail without deleting anything if another job or ENOSPC prevents taking
    # the original shared lock. No stale-lock cleanup or automatic retry.
    lock,identity,owner=archive.acquire_lock(cfg,DEST.name)
    try:
        need(verify(stage_sha)==proof,'Staging or source changed while acquiring the lock')
        state['open_user_check']=usage_observation(archive)
        need(stamp(SOURCE)==proof['source_stamp'] and sha(STAGE/'state.json')==stage_sha,
             'Source or final staging receipt changed')
        archive.save(CONTROL/'before_delete.json',state)
        SOURCE.unlink();archive.sync_dir(BASE)
        state.update(status='copying_durable_xz',source_deleted=True)
        archive.save(CONTROL/'state.json',state)
        DEST.mkdir(mode=0o700);partial=DEST/'layer_03.vcd.xz.partial'
        need(shutil.disk_usage(str(DEST)).free>=proof['xz_bytes']+512*1024**2,
             'Shared space was consumed; exact gzip and XZ staged copies are preserved')
        h=hashlib.sha256();count=0
        with (STAGE/'layer_03.vcd.xz').open('rb') as src,partial.open('xb') as dest:
            for data in iter(lambda:src.read(CHUNK),b''):
                need(shutil.disk_usage(str(DEST)).free>=512*1024**2+len(data),'Keep shared reserve')
                need(dest.write(data)==len(data),'Short durable write');h.update(data);count+=len(data)
            dest.flush();os.fsync(dest.fileno())
        need(count==proof['xz_bytes'] and h.hexdigest()==proof['xz_sha256'] and
             sha(partial)==proof['xz_sha256'],'Durable XZ byte readback differs')
        h=hashlib.sha256();count=0
        with lzma.open(str(partial),'rb') as stream:
            for data in iter(lambda:stream.read(CHUNK),b''):h.update(data);count+=len(data)
        need(count==proof['raw_bytes'] and h.hexdigest()==proof['raw_sha256'],
             'Durable complete VCD restoration differs')
        need(sha(BASE/'layer_03.vcd.json')==proof['source_receipt_sha256'] and
             sha(STAGE/'state.json')==stage_sha,'Original evidence metadata changed')
        final=DEST/'layer_03.vcd.xz';os.rename(str(partial),str(final));archive.sync_dir(DEST)
        state.update(status='durable_xz_verified_original_gzip_copy_retained',finished=datetime.datetime.now().isoformat(),
            durable_archive=str(final),durable_archive_sha256=proof['xz_sha256'],
            durable_archive_bytes=proof['xz_bytes'],restored_sha256=h.hexdigest(),restored_bytes=count,
            full_durable_readback_verified=True,free_bytes=shutil.disk_usage(str(DEST)).free)
        archive.save(DEST/'receipt.json',state)
        with (DEST/'RESTORE.txt').open('x') as f:
            f.write('R4 layer_03 VCD is preserved byte-for-byte in layer_03.vcd.xz.\n')
            f.write('Decode XZ to a fresh .vcd path and verify receipt.json restored_sha256 and restored_bytes.\n')
            f.write('Original gzip metadata is not reproducible from XZ; its exact byte copy remains at '+str(STAGE/'original_layer_03.vcd.gz')+'.\n')
            f.write('Original shared gzip path: '+str(SOURCE)+'\nOriginal JSON receipts are preserved.\n')
            f.flush();os.fsync(f.fileno())
        archive.sync_dir(DEST);archive.save(CONTROL/'state.json',state)
        print('R4_L03_DURABLE_XZ_VERIFIED',sha(DEST/'receipt.json'),state['free_bytes'],flush=True)
    except BaseException as error:
        state.update(status='failed_staged_copies_preserved',error=str(error),finished=datetime.datetime.now().isoformat())
        archive.save(CONTROL/'state.json',state)
        # Never delete a partial copy or attempt broader cleanup on failure.
        raise
    finally:archive.release_lock(lock,identity,owner)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--stage-sha256',required=True)
    p.add_argument('--migrate',action='store_true');a=p.parse_args();main(a.stage_sha256,a.migrate)
