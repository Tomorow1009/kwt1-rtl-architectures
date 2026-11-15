"""Copy S0 evidence using the deployed verified archiver; no source deletion.

Run after existing review helpers exit, from a fresh operations directory
outside the source runtime. This copy does not grant stage acceptance.
"""
import datetime
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT=Path('/tmp/s4_21usr_t80_20261115_1830')
BUNDLE=ROOT/'light-light126-t80-s0-66b9496'
MANIFEST='2afb9a79e600e4bd1a0493699b50d463f7df8ebef666d99290cde2efbf0426b4'
OPS=ROOT/'ops-review-e516e4c'
BACKUPS=Path('/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109/backups')
REPORT_SHA='65c471298fe5109ed4f246df573422cbd9434e15c5f9f4d42ef4b5b9caa3f48c'
QUEUE_SHA='dc900c9d685a0c0d968b40581af040350818e632886b5ace2a60e5ed89a12ce0'

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def save(p,v):
    with Path(p).open('x') as f:
        json.dump(v,f,indent=2,sort_keys=True);f.write('\n');f.flush();os.fsync(f.fileno())

def main(expected_self):
    assert sha(__file__)==expected_self
    here=Path.cwd().resolve()
    assert here==Path(__file__).resolve().parent and ROOT not in here.parents and here!=ROOT
    assert here.parent==Path('/tmp') and here.name.startswith('s4_21usr_s0_copy_ops_')
    assert sha(BUNDLE/'manifest.json')==MANIFEST
    receipt=read(OPS/'receipt.json')
    assert receipt['source_commit']=='e516e4c' and receipt['base_manifest_sha256']==MANIFEST
    assert all(sha(OPS/n)==v for n,v in receipt['files'].items())
    refs={}
    for name in ('export','review'):
        control=ROOT/('ops-66b9496/s0_'+name+'01_control')
        identity=read(control/'identity.json');result=read(control/'result.json')
        assert not Path('/proc/%d'%identity['pid']).exists(),'Existing helper still active'
        refs[name]=dict(result=result,sha256=sha(control/'result.json'))
    assert refs['export']['result']['status']=='export_and_unknown_inventory_ready'
    review=refs['review']['result']
    assert review['status']=='facts_joined_manual_conclusion_required'
    assert sha(review['snapshot'])==review['snapshot_sha256']
    queue=BUNDLE/'runs/s0_finish03';launch=read(queue/'request.json')
    target=BACKUPS/('s0-runtime-'+datetime.datetime.now().strftime('%Y%m%d_%H%M'))
    assert not target.exists()
    request=dict(schema='arch03-s0-runtime-copy-v1',runtime_root=str(ROOT),bundle=str(BUNDLE),
        bundle_manifest_sha256=MANIFEST,runtime_evidence=launch['runtime_evidence'],
        queue=str(queue),queue_state_sha256=QUEUE_SHA,
        report_run=str(BUNDLE/'runs/s0_report01/t80_s0_report'),report_sha256=REPORT_SHA,
        destination=str(target))
    save(here/'request.json',request)
    save(here/'identity.json',dict(pid=os.getpid(),started=datetime.datetime.now().isoformat(),
        source_sha256=expected_self,review_sources=refs,destination=str(target),
        source_deleted=False,archive_implies_acceptance=False))
    sys.path[:0]=[str(OPS),str(BUNDLE/'workspaces/arch03/scripts')]
    import s0_archive_runtime
    assert Path(s0_archive_runtime.__file__).resolve()==OPS/'s0_archive_runtime.py'
    print('S0_COPY_ONLY_BEGIN',str(target),flush=True)
    try:
        result=s0_archive_runtime.archive(request)
        save(here/'result.json',result)
        print('S0_COPY_VERIFIED',result['archive_sha256'],result['archive_bytes'],flush=True)
    except BaseException as error:
        save(here/'failed.json',dict(error=str(error),source_deleted=False));raise

if __name__=='__main__':
    assert len(sys.argv)==2,'Pass this committed script SHA256'
    main(sys.argv[1])
