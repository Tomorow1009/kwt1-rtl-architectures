"""Stage a fully verified XZ copy of R4 L03 in /tmp, preserving original gzip.

Read-only toward all shared evidence. No unlink, rename, or overwrite of any
shared file. A later separate decision is required for durable migration.
One low-priority CPU, bounded streaming buffers, complete gzip-copy and raw
VCD hashes, independent XZ readback, and retained failure artifacts.
"""
import argparse
import datetime
import gzip
import hashlib
import json
import lzma
import os
from pathlib import Path
import shutil
import time

BASE=Path('/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109/bundles/light-light126-systolic-b-v3-20261112_114355-ced0e139a01e/runs/r4_waves_lossless_archive02')
PROBE=Path('/tmp/s4_21usr_c32_storageprobe_20261117/result.json')
OUT=Path('/tmp/s4_21usr_r4_l03_xzstage_20261117')
CHUNK=4*1024**2
RESERVE=12*1024**3


def need(ok,message):
    if not ok:raise ValueError(message)


def now():return datetime.datetime.now().isoformat()
def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for data in iter(lambda:f.read(CHUNK),b''):h.update(data)
    return h.hexdigest()


def stamp(path):
    s=Path(path).lstat()
    return (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)


def save(value):
    pending=OUT/'state.pending'
    with pending.open('w') as stream:
        json.dump(value,stream,indent=2,sort_keys=True);stream.write('\n')
        stream.flush();os.fsync(stream.fileno())
    os.replace(str(pending),str(OUT/'state.json'))


def main(probe_sha):
    os.nice(15)
    need(sha(PROBE)==probe_sha,'Read-only feasibility receipt changed')
    probe=json.loads(PROBE.read_text());source=BASE/'layer_03.vcd.gz';receipt=BASE/'layer_03.vcd.json'
    ref=json.loads(receipt.read_text());start=stamp(source);receipt_sha=sha(receipt)
    need(BASE.resolve()==BASE and source.is_file() and not source.is_symlink() and
         source.stat().st_uid==os.getuid(),'Unexpected R4 source')
    need(probe['archive']==str(source) and probe['reference']==ref and
         probe['receipt_sha256']==receipt_sha and len(probe['samples'])==3 and
         all(x['xz3']['roundtrip_identical'] for x in probe['samples']), 'Wrong feasibility source')
    need(ref['status']=='lossless_archived_raw_removed' and ref['archive']==str(source) and
         source.stat().st_size==ref['archive_bytes'] and
         ref['restored_bytes']==ref['original_bytes'] and ref['restored_sha256']==ref['original_sha256'],
         'Incomplete original archive proof')
    need(shutil.disk_usage('/tmp').free>=ref['archive_bytes']+ref['original_bytes']+RESERVE,
         'Need worst-case staged files plus 12GiB reserve')
    need(not OUT.exists(),'Preserve previous XZ staging attempts');OUT.mkdir(mode=0o700)
    state=dict(schema='r4-l03-lossless-xz-staging-v1',status='copying_original_gzip',started=now(),
        pid=os.getpid(),source=str(source),source_stamp=list(start),source_reference=ref,
        source_receipt_sha256=receipt_sha,probe_sha256=probe_sha,source_script_sha256=sha(__file__),
        source_modified=False,source_deleted=False,durable_migration_completed=False,
        original_gzip_kept=True,nice_increment=15,reserve_bytes=RESERVE)
    save(state)

    def unchanged():
        need(stamp(source)==start and sha(receipt)==receipt_sha,'Original R4 archive changed')

    def capacity():
        need(shutil.disk_usage('/tmp').free>=RESERVE,'Keep remaining runtime space reserve')

    try:
        backup=OUT/'original_layer_03.vcd.gz';h=hashlib.sha256();count=0
        with source.open('rb') as src,backup.open('xb') as dest:
            for data in iter(lambda:src.read(CHUNK),b''):
                capacity();dest.write(data);h.update(data);count+=len(data)
            dest.flush();os.fsync(dest.fileno())
        need(count==ref['archive_bytes'] and h.hexdigest()==ref['archive_sha256'],
             'Original gzip does not match its full archive hash')
        need(sha(backup)==ref['archive_sha256'],'Staged gzip independent readback mismatch');unchanged()
        state.update(status='compressing_xz',gzip_copy_sha256=h.hexdigest(),gzip_copy_bytes=count,
                     gzip_copy_verified=True,compression_started=now());save(state)
        xz=OUT/'layer_03.vcd.xz';h=hashlib.sha256();count=0;last=0;start_time=time.monotonic()
        with gzip.open(str(backup),'rb') as src,xz.open('xb') as file:
            with lzma.LZMAFile(file,'w',preset=3) as dest:
                for data in iter(lambda:src.read(CHUNK),b''):
                    capacity();dest.write(data);h.update(data);count+=len(data)
                    if count-last>=256*1024**2:
                        state.update(raw_bytes_processed=count,elapsed_seconds=time.monotonic()-start_time)
                        save(state);last=count
            file.flush();os.fsync(file.fileno())
        need(count==ref['original_bytes'] and h.hexdigest()==ref['original_sha256'],
             'Full original VCD did not match original readback proof')
        state.update(status='independent_xz_readback',raw_bytes_processed=count,
            xz_bytes=xz.stat().st_size,compression_seconds=time.monotonic()-start_time);save(state)
        h=hashlib.sha256();count=0
        with lzma.open(str(xz),'rb') as stream:
            for data in iter(lambda:stream.read(CHUNK),b''):h.update(data);count+=len(data)
        need(count==ref['original_bytes'] and h.hexdigest()==ref['original_sha256'],
             'Independent full XZ readback differs');unchanged()
        state.update(status='fully_verified_staging_original_retained',finished=now(),
            xz_sha256=sha(xz),xz_bytes=xz.stat().st_size,raw_sha256=h.hexdigest(),raw_bytes=count,
            full_xz_readback_verified=True,potential_saved_bytes=ref['archive_bytes']-xz.stat().st_size)
        save(state)
        print('R4_L03_XZ_STAGED',state['xz_bytes'],state['potential_saved_bytes'],sha(OUT/'state.json'),flush=True)
    except BaseException as error:
        state.update(status='failed_original_preserved',error=str(error),finished=now());save(state);raise


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--probe-sha256',required=True);a=p.parse_args();main(a.probe_sha256)
