"""Copy completed C80 evidence to a fresh durable archive; never delete source.

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
import c80_paths as paths
import c80_archive_contract as contract

SCHEMA='arch03-c80-runtime-copy-v1'
BACKUPS=Path(paths.SERVER_ROOT)/'light-light126-undergrad-d2-20261109/backups'
need=paths.require


def read(path):return json.loads(Path(path).read_text())


def evidence(req,bundle):
    proofs={}
    for role in ('initial','finish'):
        ref=req[role];queue=Path(ref['queue']).absolute()
        need(queue.parent==bundle/'runs' and queue.resolve()==queue,
             'C80 queue outside its frozen bundle')
        if role=='initial' and req.get('precision_recovery') is not None:
            proof=contract.recovered_initial(queue,ref['state_sha256'],req['precision_recovery'],
                lambda pid:Path('/proc/%d'%pid).exists())
        else:
            proof=contract.completed_queue(queue,ref['state_sha256'],
                lambda pid:Path('/proc/%d'%pid).exists(),role)
        request=read(queue/'request.json')
        schema='c80-qualification-v1' if role=='initial' else 'c80-final-netlist-finish-v1'
        script='c80_qualification.py' if role=='initial' else 'c80_finish.py'
        need(request.get('schema')==schema and request.get('bundle')==str(bundle) and
             request.get('bundle_manifest_sha256')==req['bundle_manifest_sha256'] and
             request.get('queue_sha256')==paths.digest(bundle/'workspaces/arch03/scripts'/script),
             'C80 queue launch identity changed')
        if role=='finish':
            need(request.get('synthesis')==proof['state']['synthesis'],
                 'C80 finish request used another synthesis')
        proof['inputs'][str(queue/'request.json')]=paths.digest(queue/'request.json')
        proofs[role]=proof
    joined=contract.joined_queues(proofs['initial'],proofs['finish'])
    report=contract.exported_report(req['report_run'],req['report_sha256'],joined)
    return dict(queues=joined,export=report,archive_implies_acceptance=False)


def archive(req):
    need(req['schema']==SCHEMA,'Wrong C80 archive request')
    uid=paths._identity();root,_=paths._root(req['runtime_root'],uid)
    bundle=Path(req['bundle']).absolute()
    cfg=paths.configure(read(bundle/'handoff/team/server_config.json'),bundle,root,
                        req['bundle_manifest_sha256'],req['runtime_evidence'])
    need(Path.cwd()!=root and root not in Path.cwd().parents,'Run the archive tool from outside its source runtime')
    target=Path(req['destination']).absolute()
    need(paths._plain(target.parent)==BACKUPS and target.parent.stat().st_uid==uid and
         re.fullmatch(r'c80-runtime-[0-9]{8}_[0-9]{4}(?:-[A-Za-z0-9_-]+)?',target.name) and
         not target.exists() and not target.is_symlink(),'Fresh durable C80 backup directory required')
    need(target.parent.stat().st_dev!=root.stat().st_dev,'C80 backup must use a different durable filesystem')
    proof=evidence(req,bundle)
    lock,identity,owner=tar.acquire_lock(cfg,target.name);created=False
    try:
        before=tar.no_open_users([root],copy_only=True)
        rows=runtime_copy.inventory(root,uid)
        size=tar.stream_archive(rows,tar.Sink())
        required=(size*6+4)//5+tar.RESERVE
        need(shutil.disk_usage(str(target.parent)).free>=required,'Need 1.2x compressed C80 archive plus reserve')
        need(runtime_copy.inventory(root,uid)==rows and evidence(req,bundle)==proof,'C80 source changed during size check')
        target.mkdir(mode=0o700);created=True
        tar.save(target/'state.json',dict(status='copying',source_deleted=False))
        manifest=dict(schema=SCHEMA,request=req,files=rows,evidence=proof,source_root=str(root),
            member_prefix=root.name,predicted_gzip_bytes=size,required_free_bytes=required,
            source_deleted=False,source_modified=False,archive_implies_acceptance=False,
            historical_runs_copied_without_promoting_acceptance=True,
            external_link_targets_copied=False,relocation_verified=False,
            tools={Path(m.__file__).name:paths.digest(m.__file__) for m in (tar,paths,contract,runtime_copy)},
            archiver_sha256=paths.digest(__file__))
        tar.save(target/'manifest.json',manifest)
        partial=target/'runtime-evidence.tar.gz.partial'
        with partial.open('xb') as stream:
            written=tar.stream_archive(rows,tar.Sink(stream,target));stream.flush();os.fsync(stream.fileno())
        need(written==size==partial.stat().st_size,'C80 archive size changed')
        counts=tar.verify_archive(partial,rows);digest=paths.digest(partial)
        need(runtime_copy.inventory(root,uid)==rows and evidence(req,bundle)==proof,'C80 source changed during copy')
        after=tar.no_open_users([root],copy_only=True);paths.recheck(cfg)
        final=target/'runtime-evidence.tar.gz';need(not final.exists(),'Preserve previous C80 archive')
        os.rename(str(partial),str(final));tar.sync_dir(target)
        receipt=dict(schema=SCHEMA,status='verified_copy',finished=tar.now(),archive_sha256=digest,
            archive_bytes=size,member_counts=counts,manifest_sha256=paths.digest(target/'manifest.json'),
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
    need(paths.digest(a.request)==a.request_sha256,'C80 archive request changed')
    result=archive(read(a.request))
    print('C80_RUNTIME_COPY_VERIFIED',result['archive_sha256'],result['archive_bytes'],'source_deleted=false',flush=True)
