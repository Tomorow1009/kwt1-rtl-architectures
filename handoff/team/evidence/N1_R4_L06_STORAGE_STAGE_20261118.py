"""Stage R4 L06 losslessly; retain its original shared gzip.

Reclaim only two /tmp XZ duplicates already fully preserved on shared storage.
All original gzip copies and all durable archives remain. No N1/T80/old8 delete.
The staged L06 XZ requires a separate verified migration step. This staging
step is read-only toward shared storage and never creates or bypasses its lock.
"""
import datetime, gzip, hashlib, importlib.util, json, lzma, os, shutil, sys, time
from pathlib import Path
sys.dont_write_bytecode=True
PROJECT=Path('/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109')
CONTROL=Path('/tmp/s4_21usr_n1_closeout_20261117_2355')
OUT=Path('/tmp/s4_21usr_n1_r4_l06_stage_20261118')
BASE=PROJECT/'bundles/light-light126-systolic-b-v3-20261112_114355-ced0e139a01e/runs/r4_waves_lossless_archive02'
SOURCE=BASE/'layer_06.vcd.gz'
RECEIPT=BASE/'layer_06.vcd.json'
RECEIPT_SHA='2e2e38a866a0b90978b1379018e2bd762a0673b7c7b4beb2c353d9d0f3838359'
KEEP={4:'c6962b18892f8bd0b3561224c2e8219ebbd2e791305e90a797a502fb7593d053',
      5:'5a661ac0fce451fa51c2c2f50ad6e7f6ca2ca2f117038c5ad2b8218e91b46491'}
HELPER=Path('/tmp/s4_21usr_c80_20261116_1245/ops-b0-cleanup16-c8c730d/C80_B0_DUPLICATES_CLEANUP16_20261116.py')
CHUNK=4*1024**2
RESERVE=512*1024**2
MAX_OUTPUT=4*1024**3


def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(CHUNK),b''):h.update(b)
    return h.hexdigest()


def read(p):return json.loads(Path(p).read_text())
def load(name,p):
    spec=importlib.util.spec_from_file_location(name,str(p));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def stamp(p):
    assert p.resolve()==p and not p.is_symlink() and p.is_file() and p.stat().st_uid==os.getuid()
    s=p.stat();return [s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns]


def main():
    assert not OUT.exists() and sha(HELPER)=='0e98728332e0ba048142231f414322dc3aaf21e287b3bde0bc4121124c976441'
    assert sha(RECEIPT)==RECEIPT_SHA
    ref=read(RECEIPT);source_stamp=stamp(SOURCE)
    assert ref['status']=='lossless_archived_raw_removed' and ref['archive']==str(SOURCE)
    assert ref['archive_bytes']==7430640268 and ref['original_bytes']==12210217662
    assert ref['restored_sha256']==ref['original_sha256'] and ref['restored_bytes']==ref['original_bytes']
    assert sha(SOURCE)==ref['archive_sha256'] and stamp(SOURCE)==source_stamp
    base=load('n1_l06_idle',HELPER)
    assert sha(base.BUNDLE/'manifest.json')==base.MANIFEST_SHA
    mf=read(base.BUNDLE/'manifest.json')['files']
    for n in ('n1_archive_runtime.py','n1_paths.py','partition_synth_contract.py'):
        rel='workspaces/arch03/scripts/'+n;assert sha(base.BUNDLE/rel)==mf[rel]
    sys.path.insert(0,str(base.BUNDLE/'workspaces/arch03/scripts'));import n1_archive_runtime as archive
    duplicates=[];fixed={RECEIPT:RECEIPT_SHA};fixed_stamps={str(RECEIPT):stamp(RECEIPT)}
    for n,want in sorted(KEEP.items()):
        dest=PROJECT/('backups/r4-l%02d-xz-20261117'%n);receipt=dest/'receipt.json'
        assert sha(receipt)==want
        r=read(receipt);durable=Path(r['durable_archive'])
        original=Path('/tmp/s4_21usr_r4_l%02d_xzstage_20261117'%n)/('layer_%02d.vcd.xz'%n)
        assert r['status']=='durable_xz_verified_original_gzip_copy_retained' and r['full_durable_readback_verified']
        assert durable==dest/('layer_%02d.vcd.xz'%n) and r['durable_archive_bytes']==original.stat().st_size
        assert r['restored_sha256']==r['staging']['raw_sha256'] and r['restored_bytes']==r['staging']['raw_bytes']
        before=stamp(original);keep_stamp=stamp(durable)
        assert sha(original)==sha(durable)==r['durable_archive_sha256']
        assert stamp(original)==before and stamp(durable)==keep_stamp
        fixed[receipt]=want;fixed[durable]=r['durable_archive_sha256']
        fixed_stamps[str(receipt)]=stamp(receipt);fixed_stamps[str(durable)]=keep_stamp
        duplicates.append(dict(path=str(original),stamp=before,sha256=r['durable_archive_sha256'],
            bytes=r['durable_archive_bytes'],durable=str(durable),durable_receipt_sha256=want))
    assert sum(r['bytes'] for r in duplicates)==5491982376
    lock=PROJECT.parent/'.arch02_team_lock'
    observation=base.idle(archive,lock,[SOURCE]+[Path(r['path']) for r in duplicates])
    assert all(stamp(p)==fixed_stamps[str(p)] for p in fixed)
    OUT.mkdir(mode=0o700)
    state=dict(schema='n1-r4-l06-space-staging-v1',status='verified_duplicate_cleanup',pid=os.getpid(),
        started=archive.now(),source_script_sha256=sha(__file__),source=str(SOURCE),source_stamp=source_stamp,
        source_reference=ref,source_receipt_sha256=RECEIPT_SHA,source_modified=False,source_deleted=False,
        T80_modified=False,old8_modified=False,N1_modified=False,duplicates=duplicates,removed_duplicates=0,
        durable_duplicates_unchanged=True,process_observation=observation,exact_original_gzip_copy_created=False,
        shared_storage_read_only=True,shared_lock_not_created=True)
    archive.save(OUT/'state.json',state)
    try:
        with (OUT/'duplicate_removal.jsonl').open('x') as log:
            for row in duplicates:
                p=Path(row['path']);uses=archive.no_open_users([p],copy_only=True)
                assert not lock.exists(), 'Another team operation started; preserve remaining temporary copies'
                assert uses['inaccessible_owned_processes']==observation['inaccessible_owned_processes']
                assert all(stamp(q)==fixed_stamps[str(q)] for q in fixed)
                assert stamp(p)==row['stamp'] and sha(p)==row['sha256']
                log.write(json.dumps(dict(action='remove_verified_tmp_duplicate',**row))+'\n');log.flush();os.fsync(log.fileno())
                p.unlink();archive.sync_dir(p.parent);state['removed_duplicates']+=1
                archive.save(OUT/'state.json',state)
        assert shutil.disk_usage('/tmp').free>=MAX_OUTPUT+RESERVE
        state.update(status='compressing_l06_xz',compression_preset=0,reserve_bytes=RESERVE,
            maximum_output_bytes=MAX_OUTPUT,free_tmp=shutil.disk_usage('/tmp').free)
        archive.save(OUT/'state.json',state);os.nice(15)
        xz=OUT/'layer_06.vcd.xz';h=hashlib.sha256();count=0;last=0;started=time.monotonic()
        with gzip.open(str(SOURCE),'rb') as src,xz.open('xb') as file:
            with lzma.LZMAFile(file,'w',preset=0) as dest:
                for data in iter(lambda:src.read(CHUNK),b''):
                    assert shutil.disk_usage('/tmp').free>=RESERVE+2*CHUNK and file.tell()<MAX_OUTPUT
                    dest.write(data);h.update(data);count+=len(data)
                    if count-last>=256*1024**2:
                        state.update(raw_bytes_processed=count,elapsed_seconds=time.monotonic()-started,xz_bytes=file.tell())
                        archive.save(OUT/'state.json',state);last=count
            file.flush();os.fsync(file.fileno())
        assert count==ref['original_bytes'] and h.hexdigest()==ref['original_sha256']
        assert xz.stat().st_size<=MAX_OUTPUT
        state.update(status='independent_xz_readback',compression_seconds=time.monotonic()-started,
            xz_bytes=xz.stat().st_size,xz_sha256=sha(xz));archive.save(OUT/'state.json',state)
        h=hashlib.sha256();count=0
        with lzma.open(str(xz),'rb') as f:
            for data in iter(lambda:f.read(CHUNK),b''):h.update(data);count+=len(data)
        assert count==ref['original_bytes'] and h.hexdigest()==ref['original_sha256']
        assert stamp(SOURCE)==source_stamp and sha(RECEIPT)==RECEIPT_SHA
        assert all(stamp(p)==fixed_stamps[str(p)] for p in fixed)
        state.update(status='fully_verified_staging_original_retained',finished=archive.now(),
            full_xz_readback_verified=True,raw_sha256=h.hexdigest(),raw_bytes=count,
            potential_shared_saved_bytes=ref['archive_bytes']-xz.stat().st_size)
        archive.save(OUT/'state.json',state)
        print('N1_R4_L06_STAGE_VERIFIED',xz.stat().st_size,state['potential_shared_saved_bytes'],sha(OUT/'state.json'),flush=True)
    except BaseException as error:
        state.update(status='failed_preserved',error=str(error),finished=archive.now())
        archive.save(OUT/'state.json',state);raise


if __name__=='__main__':main()
