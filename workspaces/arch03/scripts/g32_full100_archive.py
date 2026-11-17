"""Copy completed G32 full100 evidence to a fresh durable archive; never delete source.

Uses the existing tar writer/full readback and original team coordination lock.
Run from outside the source runtime after its queue and report have completed.
"""
import argparse
import json
import os
from pathlib import Path
import re
import shutil

import n1_archive_runtime as tar
import t80_archive_runtime as runtime_copy
import g32_paths as paths
import g32_full100_archive_contract as contract
import g32_archive_capacity as capacity

SCHEMA=contract.SCHEMA
BACKUPS=Path(paths.SERVER_ROOT)/'light-light126-undergrad-d2-20261109/backups'
need=paths.require


def read(path):return json.loads(Path(path).read_text())


def evidence(req,bundle):
    return contract.evidence(req,bundle)


def archive(req):
    need(req['schema']==SCHEMA,'Wrong G32 archive request')
    evidence_reader=evidence;contract_module=contract
    selected_capacity=capacity.policy(req)
    uid=paths._identity();root,_=paths._root(req['runtime_root'],uid)
    bundle=Path(req['bundle']).absolute()
    cfg=paths.configure(read(bundle/'handoff/team/server_config.json'),bundle,root,
                        req['bundle_manifest_sha256'],req['runtime_evidence'])
    need(Path.cwd()!=root and root not in Path.cwd().parents,'Run the archive tool from outside its source runtime')
    target=Path(req['destination']).absolute()
    need(paths._plain(target.parent)==BACKUPS and target.parent.stat().st_uid==uid and
         re.fullmatch(r'g32-runtime-[0-9]{8}_[0-9]{4}(?:-[A-Za-z0-9_-]+)?',target.name) and
         not target.exists() and not target.is_symlink(),'Fresh durable G32 backup directory required')
    need(target.parent.stat().st_dev!=root.stat().st_dev,'G32 backup must use a different durable filesystem')
    proof=evidence_reader(req,bundle)
    lock,identity,owner=tar.acquire_lock(cfg,target.name);created=False
    try:
        before=tar.no_open_users([root],copy_only=True)
        rows=runtime_copy.inventory(root,uid)
        size=tar.stream_archive(rows,tar.Sink())
        required=capacity.required_bytes(size,selected_capacity)
        free_before=shutil.disk_usage(str(target.parent)).free
        need(free_before>=required,'Need 1.2x compressed G32 archive plus declared reserve')
        need(runtime_copy.inventory(root,uid)==rows and evidence_reader(req,bundle)==proof,'G32 source changed during size check')
        target.mkdir(mode=0o700);created=True
        tar.save(target/'state.json',dict(status='copying',source_deleted=False))
        manifest=dict(schema=req['schema'],request=req,files=rows,evidence=proof,source_root=str(root),
            member_prefix=root.name,predicted_gzip_bytes=size,required_free_bytes=required,
            storage_policy=selected_capacity,free_bytes_before_copy=free_before,
            source_deleted=False,source_modified=False,archive_implies_acceptance=False,
            historical_runs_copied_without_promoting_acceptance=True,
            external_link_targets_copied=False,relocation_verified=False,
            tools={Path(m.__file__).name:paths.digest(m.__file__) for m in (tar,paths,contract,contract_module,runtime_copy,capacity)},
            archiver_sha256=paths.digest(__file__))
        tar.save(target/'manifest.json',manifest)
        partial=target/'runtime-evidence.tar.gz.partial'
        with partial.open('xb') as stream:
            written=tar.stream_archive(rows,capacity.Sink(stream,target,selected_capacity));stream.flush();os.fsync(stream.fileno())
        need(written==size==partial.stat().st_size,'G32 archive size changed')
        counts=tar.verify_archive(partial,rows);digest=paths.digest(partial)
        need(runtime_copy.inventory(root,uid)==rows and evidence_reader(req,bundle)==proof,'G32 source changed during copy')
        after=tar.no_open_users([root],copy_only=True);paths.recheck(cfg)
        final=target/'runtime-evidence.tar.gz';need(not final.exists(),'Preserve previous G32 archive')
        os.rename(str(partial),str(final));tar.sync_dir(target)
        receipt=dict(schema=req['schema'],status='verified_copy',finished=tar.now(),archive_sha256=digest,
            archive_bytes=size,member_counts=counts,manifest_sha256=paths.digest(target/'manifest.json'),
            storage_policy=selected_capacity,
            source_deleted=False,source_modified=False,all_members_readback_verified=True,
            source_before_after_identical=True,process_observation_before=before,
            process_observation_after=after,relocation_verified=False,archive_implies_acceptance=False)
        tar.save(target/'receipt.json',receipt)
        tar.save(target/'state.json',dict(status='verified_copy',finished=tar.now(),
            receipt_sha256=paths.digest(target/'receipt.json'),source_deleted=False))
        return receipt
    except BaseException as error:
        if created:
            try:tar.save(target/'state.json',dict(status='failed',error=str(error),source_deleted=False,partial_retained=True))
            except OSError:pass
        raise
    finally:tar.release_lock(lock,identity,owner)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--request',type=Path,required=True)
    p.add_argument('--request-sha256',required=True);a=p.parse_args()
    need(paths.digest(a.request)==a.request_sha256,'G32 archive request changed')
    result=archive(read(a.request))
    print('G32_FULL100_RUNTIME_COPY_VERIFIED',result['archive_sha256'],result['archive_bytes'],'source_deleted=false',flush=True)
