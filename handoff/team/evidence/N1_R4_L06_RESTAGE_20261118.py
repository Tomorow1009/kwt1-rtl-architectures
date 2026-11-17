"""Restage the unchanged R4 L06 using measured preset3 compression.

Remove only the explicitly stopped, unaccepted preset0 temporary output after
pinning its hash and verifying the complete original shared gzip still exists.
No shared-storage mutation, T80/old8/N1 deletion, or hardware run.
"""
import argparse, gzip, hashlib, importlib.util, json, lzma, os, shutil, sys, time
from pathlib import Path
sys.dont_write_bytecode=True
C=Path('/tmp/s4_21usr_n1_closeout_20261117_2355')
OLD=Path('/tmp/s4_21usr_n1_r4_l06_stage_20261118')
OUT=Path('/tmp/s4_21usr_n1_r4_l06_stage03_20261118')
PROJECT=Path('/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109')
SOURCE=PROJECT/'bundles/light-light126-systolic-b-v3-20261112_114355-ced0e139a01e/runs/r4_waves_lossless_archive02/layer_06.vcd.gz'
RECEIPT_SHA='2e2e38a866a0b90978b1379018e2bd762a0673b7c7b4beb2c353d9d0f3838359'
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
def stamp(p):
    assert p.resolve()==p and not p.is_symlink() and p.is_file() and p.stat().st_uid==os.getuid()
    s=p.stat();return [s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns]


def main(prior_sha):
    os.nice(15)
    assert not OUT.exists() and sha(OLD/'state.json')==prior_sha
    previous=read(OLD/'state.json');stop=read(C/'l06_stage02_stop.json')
    assert previous['status']=='failed_preserved' and previous['pid']==stop['pid']==99444
    assert previous['source_script_sha256']=='df134866251d2d8747dd5faf3844beba379fa20d2bf39f2f8999c2c6249eb5fe'
    assert not Path('/proc/99444').exists() and not previous['source_deleted'] and not previous['source_modified']
    assert previous['removed_duplicates']==2 and previous['compression_preset']==0
    assert previous['source']==str(SOURCE)
    ref=previous['source_reference'];receipt=SOURCE.with_suffix('.json')
    assert sha(receipt)==RECEIPT_SHA and read(receipt)==ref
    assert ref['archive_bytes']==7430640268 and ref['original_bytes']==12210217662
    source_stamp=stamp(SOURCE);assert source_stamp==previous['source_stamp'] and sha(SOURCE)==ref['archive_sha256']
    partial=OLD/'layer_06.vcd.xz';partial_stamp=stamp(partial);partial_sha=sha(partial)
    assert 0<partial.stat().st_size<=MAX_OUTPUT+CHUNK and stamp(partial)==partial_stamp
    assert sha(HELPER)=='0e98728332e0ba048142231f414322dc3aaf21e287b3bde0bc4121124c976441'
    spec=importlib.util.spec_from_file_location('n1_restage_idle',str(HELPER));base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
    assert sha(base.BUNDLE/'manifest.json')==base.MANIFEST_SHA
    mf=read(base.BUNDLE/'manifest.json')['files']
    for n in ('n1_archive_runtime.py','n1_paths.py','partition_synth_contract.py'):
        rel='workspaces/arch03/scripts/'+n;assert sha(base.BUNDLE/rel)==mf[rel]
    sys.path.insert(0,str(base.BUNDLE/'workspaces/arch03/scripts'));import n1_archive_runtime as archive
    lock=PROJECT.parent/'.arch02_team_lock';observation=base.idle(archive,lock,[partial,SOURCE])
    OUT.mkdir(mode=0o700)
    disposition=dict(schema='n1-rejected-preset0-output-disposition-v1',prior_state_sha256=prior_sha,
        stop_receipt_sha256=sha(C/'l06_stage02_stop.json'),path=str(partial),stamp=partial_stamp,
        bytes=partial_stamp[2],sha256=partial_sha,source=str(SOURCE),source_sha256=ref['archive_sha256'],
        source_complete_and_unchanged=True,retained_failed_state=str(OLD/'state.json'),
        rejected_output_was_never_accepted_or_archived=True,process_observation=observation)
    archive.save(OUT/'disposal_intent.json',disposition)
    assert sha(OLD/'state.json')==prior_sha and stamp(SOURCE)==source_stamp and stamp(partial)==partial_stamp
    base.idle(archive,lock,[partial,SOURCE]);assert not lock.exists()
    partial.unlink();archive.sync_dir(partial.parent)
    disposition['removed']=True;archive.save(OUT/'disposal_receipt.json',disposition)
    assert shutil.disk_usage('/tmp').free>=MAX_OUTPUT+RESERVE
    state=dict(schema='n1-r4-l06-preset3-staging-v1',status='compressing_l06_xz',pid=os.getpid(),
        started=archive.now(),source_script_sha256=sha(__file__),source=str(SOURCE),source_stamp=source_stamp,
        source_reference=ref,source_receipt_sha256=RECEIPT_SHA,source_modified=False,source_deleted=False,
        T80_modified=False,old8_modified=False,N1_modified=False,shared_storage_read_only=True,
        exact_original_gzip_copy_created=False,compression_preset=3,reserve_bytes=RESERVE,
        maximum_output_bytes=MAX_OUTPUT,prior_failed_state_sha256=prior_sha)
    archive.save(OUT/'state.json',state)
    try:
        xz=OUT/'layer_06.vcd.xz';h=hashlib.sha256();count=0;last=0;started=time.monotonic()
        with gzip.open(str(SOURCE),'rb') as src,xz.open('xb') as file:
            with lzma.LZMAFile(file,'w',preset=3) as dest:
                for data in iter(lambda:src.read(CHUNK),b''):
                    assert shutil.disk_usage('/tmp').free>=RESERVE+2*CHUNK and file.tell()<MAX_OUTPUT
                    dest.write(data);h.update(data);count+=len(data)
                    if count-last>=256*1024**2:
                        state.update(raw_bytes_processed=count,xz_bytes=file.tell(),elapsed_seconds=time.monotonic()-started)
                        archive.save(OUT/'state.json',state);last=count
            file.flush();os.fsync(file.fileno())
        assert count==ref['original_bytes'] and h.hexdigest()==ref['original_sha256']
        state.update(status='independent_xz_readback',xz_bytes=xz.stat().st_size,xz_sha256=sha(xz),
            compression_seconds=time.monotonic()-started);archive.save(OUT/'state.json',state)
        h=hashlib.sha256();count=0
        with lzma.open(str(xz),'rb') as f:
            for data in iter(lambda:f.read(CHUNK),b''):h.update(data);count+=len(data)
        assert count==ref['original_bytes'] and h.hexdigest()==ref['original_sha256']
        assert stamp(SOURCE)==source_stamp and sha(receipt)==RECEIPT_SHA
        state.update(status='fully_verified_staging_original_retained',finished=archive.now(),
            full_xz_readback_verified=True,raw_sha256=h.hexdigest(),raw_bytes=count,
            potential_shared_saved_bytes=ref['archive_bytes']-xz.stat().st_size)
        archive.save(OUT/'state.json',state)
        print('N1_L06_PRESET3_VERIFIED',xz.stat().st_size,state['potential_shared_saved_bytes'],sha(OUT/'state.json'),flush=True)
    except BaseException as error:
        state.update(status='failed_preserved',error=str(error),finished=archive.now());archive.save(OUT/'state.json',state);raise


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--prior-state-sha256',required=True);a=p.parse_args();main(a.prior_state_sha256)
