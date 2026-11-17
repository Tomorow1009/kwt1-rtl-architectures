"""Replace exactly the verified R4 L06 gzip with lossless durable XZ.

Requires an exited, fully verified staging run and pinned staging receipt.
Raw VCD bytes are preserved; original gzip container bytes are not retained.
Keep original JSON, the full staged XZ, failures, T80, N1 and all old8 evidence.
"""
import argparse, hashlib, importlib.util, json, lzma, os, shutil, sys
from pathlib import Path
sys.dont_write_bytecode=True
PROJECT=Path('/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109')
CONTROL=Path('/tmp/s4_21usr_n1_closeout_20261117_2355/l06_migrate01')
STAGE=Path('/tmp/s4_21usr_n1_r4_l06_stage03_20261118')
SOURCE=PROJECT/'bundles/light-light126-systolic-b-v3-20261112_114355-ced0e139a01e/runs/r4_waves_lossless_archive02/layer_06.vcd.gz'
DEST=PROJECT/'backups/r4-l06-xz-20261118'
HELPER=Path('/tmp/s4_21usr_c80_20261116_1245/ops-b0-cleanup16-c8c730d/C80_B0_DUPLICATES_CLEANUP16_20261116.py')
STAGE_SCRIPT_SHA='5cc9d3d7d3992e00768071d490de3e65e681fa6deaf08df8f8afcc37f90ae772'
CHUNK=4*1024**2
RESERVE=512*1024**2


def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(CHUNK),b''):h.update(b)
    return h.hexdigest()


def read(p):return json.loads(Path(p).read_text())
def stamp(p):
    assert p.resolve()==p and not p.is_symlink() and p.is_file() and p.stat().st_uid==os.getuid()
    s=p.stat();return [s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns]


def raw_identity(p):
    h=hashlib.sha256();count=0
    with lzma.open(str(p),'rb') as f:
        for b in iter(lambda:f.read(CHUNK),b''):h.update(b);count+=len(b)
    return h.hexdigest(),count


def migrate_locked(stage_sha,archive,obs):
    assert not CONTROL.exists() and not DEST.exists()
    assert STAGE.resolve()==STAGE and STAGE.stat().st_uid==os.getuid()
    assert sha(STAGE/'state.json')==stage_sha
    s=read(STAGE/'state.json');ref=s['source_reference'];xz=STAGE/'layer_06.vcd.xz'
    assert s['status']=='fully_verified_staging_original_retained' and s['full_xz_readback_verified']
    assert s['source_script_sha256']==STAGE_SCRIPT_SHA and not Path('/proc/%d'%s['pid']).exists()
    assert not s['source_modified'] and not s['source_deleted'] and not s['exact_original_gzip_copy_created']
    assert s['source']==str(SOURCE)==ref['archive'] and ref['archive_bytes']==7430640268 and ref['original_bytes']==12210217662
    receipt=SOURCE.with_suffix('.json')
    assert sha(receipt)==s['source_receipt_sha256'] and read(receipt)==ref
    assert stamp(SOURCE)==s['source_stamp'] and SOURCE.stat().st_size==ref['archive_bytes'] and SOURCE.stat().st_nlink==1
    stamp(xz)
    assert sha(SOURCE)==ref['archive_sha256'] and sha(xz)==s['xz_sha256'] and xz.stat().st_size==s['xz_bytes']
    assert raw_identity(xz)==(s['raw_sha256'],s['raw_bytes'])==(ref['original_sha256'],ref['original_bytes'])
    assert DEST.parent.resolve()==DEST.parent and DEST.parent.stat().st_uid==os.getuid()
    assert DEST.parent.stat().st_dev==SOURCE.stat().st_dev!=STAGE.stat().st_dev
    assert ref['archive_bytes']-s['xz_bytes']>=2*1024**3
    CONTROL.mkdir(mode=0o700)
    state=dict(schema='n1-r4-l06-durable-migration-v1',status='preflight',pid=os.getpid(),
        started=archive.now(),script_sha256=sha(__file__),stage_sha256=stage_sha,staging=s,
        source=str(SOURCE),destination=str(DEST),source_deleted=False,staged_xz_retained=True,
        original_gzip_container_retained=False,raw_VCD_preserved=True,original_json_retained=True,
        T80_modified=False,old8_modified=False,N1_modified=False,process_observation=obs)
    archive.save(CONTROL/'state.json',state)
    try:
        assert sha(STAGE/'state.json')==stage_sha and stamp(SOURCE)==s['source_stamp']
        uses=archive.no_open_users([SOURCE,xz],copy_only=True)
        assert uses['inaccessible_owned_processes']==obs['inaccessible_owned_processes']
        assert sha(receipt)==s['source_receipt_sha256'] and sha(xz)==s['xz_sha256']
        archive.save(CONTROL/'before_delete.json',state)
        SOURCE.unlink();archive.sync_dir(SOURCE.parent)
        state.update(status='copying_durable_xz',source_deleted=True);archive.save(CONTROL/'state.json',state)
        assert shutil.disk_usage(str(DEST.parent)).free>=s['xz_bytes']+RESERVE
        DEST.mkdir(mode=0o700);partial=DEST/'layer_06.vcd.xz.partial';h=hashlib.sha256();count=0
        with xz.open('rb') as src,partial.open('xb') as dst:
            for b in iter(lambda:src.read(CHUNK),b''):
                assert shutil.disk_usage(str(DEST)).free>=RESERVE+len(b)
                assert dst.write(b)==len(b);h.update(b);count+=len(b)
            dst.flush();os.fsync(dst.fileno())
        assert count==s['xz_bytes'] and h.hexdigest()==s['xz_sha256'] and sha(partial)==s['xz_sha256']
        assert raw_identity(partial)==(ref['original_sha256'],ref['original_bytes'])
        assert sha(receipt)==s['source_receipt_sha256'] and sha(STAGE/'state.json')==stage_sha
        final=DEST/'layer_06.vcd.xz';os.rename(str(partial),str(final));archive.sync_dir(DEST)
        state.update(status='durable_xz_verified_staged_xz_retained',finished=archive.now(),
            durable_archive=str(final),durable_archive_sha256=s['xz_sha256'],durable_archive_bytes=count,
            full_durable_readback_verified=True,restored_bytes=ref['original_bytes'],restored_sha256=ref['original_sha256'],
            free_bytes=shutil.disk_usage(str(DEST)).free)
        archive.save(DEST/'receipt.json',state)
        with (DEST/'RESTORE.txt').open('x') as f:
            f.write('Decode layer_06.vcd.xz to a NEW VCD file and verify receipt.json restored_sha256 and restored_bytes.\n')
            f.write('Original raw VCD bytes are identical. Original gzip container bytes are not retained or claimed reproducible.\n')
            f.write('Original JSON receipts remain unchanged. Staged complete XZ remains at '+str(xz)+'.\n')
            f.flush();os.fsync(f.fileno())
        archive.sync_dir(DEST);archive.save(CONTROL/'state.json',state)
        print('N1_L06_DURABLE_VERIFIED',sha(DEST/'receipt.json'),state['free_bytes'],flush=True)
    except BaseException as error:
        state.update(status='failed_staged_xz_preserved',error=str(error),finished=archive.now())
        archive.save(CONTROL/'state.json',state);raise


def main(stage_sha):
    assert not CONTROL.exists() and not DEST.exists()
    assert sha(STAGE/'state.json')==stage_sha
    s=read(STAGE/'state.json')
    assert s['status']=='fully_verified_staging_original_retained' and s['full_xz_readback_verified']
    assert s['source_script_sha256']==STAGE_SCRIPT_SHA and not Path('/proc/%d'%s['pid']).exists()
    assert sha(HELPER)=='0e98728332e0ba048142231f414322dc3aaf21e287b3bde0bc4121124c976441'
    spec=importlib.util.spec_from_file_location('l06_migrate_idle',str(HELPER));base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
    assert sha(base.BUNDLE/'manifest.json')==base.MANIFEST_SHA
    mf=read(base.BUNDLE/'manifest.json')['files']
    for n in ('n1_archive_runtime.py','n1_paths.py','partition_synth_contract.py'):
        rel='workspaces/arch03/scripts/'+n;assert sha(base.BUNDLE/rel)==mf[rel]
    sys.path.insert(0,str(base.BUNDLE/'workspaces/arch03/scripts'));import n1_archive_runtime as archive
    lock=PROJECT.parent/'.arch02_team_lock';obs=base.idle(archive,lock,[SOURCE,STAGE/'layer_06.vcd.xz'])
    cfg=dict(server_root=str(PROJECT.parent),runtime_roots=[dict(bundle=str(STAGE))])
    lk,identity,owner=archive.acquire_lock(cfg,'n1-r4-l06-durable-migration')
    try:migrate_locked(stage_sha,archive,obs)
    finally:archive.release_lock(lk,identity,owner)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--stage-sha256',required=True);a=p.parse_args();main(a.stage_sha256)
