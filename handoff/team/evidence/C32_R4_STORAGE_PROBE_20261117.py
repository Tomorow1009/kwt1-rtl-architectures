"""Read-only compression feasibility samples of archived R4 L03.

No source/receipt/archive changes or deletion. This is not full archive
verification: sample roundtrips cannot authorize removal of the old gzip.
"""
import datetime
import gzip
import hashlib
import json
import lzma
import os
from pathlib import Path
import time
import zlib

BASE=Path('/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109/bundles/light-light126-systolic-b-v3-20261112_114355-ced0e139a01e/runs/r4_waves_lossless_archive02')
OUT=Path('/tmp/s4_21usr_c32_storageprobe_20261117')
SIZE=64*1024**2


def main():
    os.nice(15)
    archive=BASE/'layer_03.vcd.gz';receipt=BASE/'layer_03.vcd.json'
    original=archive.stat();raw=receipt.read_bytes();ref=json.loads(raw.decode())
    assert BASE.resolve()==BASE and archive.is_file() and not archive.is_symlink()
    assert original.st_uid==os.getuid() and ref['archive']==str(archive)
    assert ref['status']=='lossless_archived_raw_removed' and original.st_size==ref['archive_bytes']
    assert not OUT.exists();OUT.mkdir(mode=0o700)
    result=dict(schema='r4-compression-sample-feasibility-v1',started=datetime.datetime.now().isoformat(),
        pid=os.getpid(),archive=str(archive),receipt_sha256=hashlib.sha256(raw).hexdigest(),
        reference=ref,samples=[],source_modified=False,source_deleted=False,
        full_archive_verified=False,removal_authorized_by_this_probe=False)
    pos=0
    with gzip.open(str(archive),'rb') as stream:
        for offset in (64*1024**2,256*1024**2,1024*1024**2):
            while pos<offset:
                data=stream.read(min(4*1024**2,offset-pos));assert data;pos+=len(data)
            data=stream.read(SIZE);assert len(data)==SIZE;pos+=len(data)
            row=dict(offset=offset,bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
            for name,encode,decode in (
                ('gzip6',lambda x:zlib.compress(x,6),zlib.decompress),
                ('xz3',lambda x:lzma.compress(x,preset=3),lzma.decompress)):
                start=time.monotonic();coded=encode(data);seconds=time.monotonic()-start
                assert decode(coded)==data
                row[name]=dict(bytes=len(coded),seconds=seconds,roundtrip_identical=True)
            result['samples'].append(row);print('SAMPLE',json.dumps(row,sort_keys=True),flush=True)
    after=archive.stat()
    assert (after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns)==(
        original.st_ino,original.st_size,original.st_mtime_ns,original.st_ctime_ns)
    assert receipt.read_bytes()==raw
    result['finished']=datetime.datetime.now().isoformat()
    with (OUT/'result.json').open('x') as f:
        json.dump(result,f,indent=2,sort_keys=True);f.write('\n');f.flush();os.fsync(f.fileno())
    print('READONLY_PROBE_COMPLETE',hashlib.sha256((OUT/'result.json').read_bytes()).hexdigest(),flush=True)


if __name__=='__main__':main()
