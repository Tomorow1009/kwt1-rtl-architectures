"""Copy a completed, explicitly pinned T64 runtime to durable storage.

Uses the verified N1 tar writer/readback primitives, not its N1 path or stage
authorization. No source file is moved or deleted; external links are not read.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat

import n1_archive_runtime as tar
import t64_paths as paths
from transport_report_stage import completed_references, verify_queue_path

need=paths.require
BACKUPS=Path(paths.SERVER_ROOT)/'light-light126-undergrad-d2-20261109/backups'


def read(path):return json.loads(Path(path).read_text())


def inventory(root,uid):
    rows=[];pending=[root]
    while pending:
        p=pending.pop();before=tar.stamp(p);s=p.lstat()
        need(s.st_uid==uid,'Other-owner runtime member: '+str(p))
        row=dict(source=str(p),member=p.relative_to(root.parent).as_posix(),stamp=before,
                 uid=s.st_uid,gid=s.st_gid,mode=stat.S_IMODE(s.st_mode),mtime_ns=s.st_mtime_ns)
        if stat.S_ISREG(s.st_mode):
            row.update(kind='regular',bytes=s.st_size,sha256=paths.digest(p))
        elif stat.S_ISDIR(s.st_mode):
            row.update(kind='directory',bytes=0,sha256=hashlib.sha256(b'').hexdigest())
            pending.extend(reversed(sorted(p.iterdir())))
        elif stat.S_ISLNK(s.st_mode):
            target=os.readlink(str(p));raw=target.encode('utf8')
            need(os.fsencode(target)==raw,'Non-UTF8 link target')
            row.update(kind='symlink',target=target,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),
                       target_content_archived=False)
        else:raise ValueError('Special runtime file cannot be archived: '+str(p))
        need(tar.stamp(p)==before,'Runtime member changed while hashing')
        rows.append(row)
    return sorted(rows,key=lambda r:r['member'])


def terminal_sessions(bundle,queue):
    result=[]
    for session in sorted((bundle/'runs').iterdir()):
        if not session.is_dir():continue
        need(not session.is_symlink(),'Symlink session requires separate review')
        f=session/'state.json';need(f.is_file() and not f.is_symlink(),'Session state missing')
        s=read(f)
        if session==queue:
            completed_references(s,'T64')
            need(s.get('finished') and not Path('/proc/%d'%s['pid']).exists(),'Queue process still present')
        elif s.get('stages'):
            for name,row in s['stages'].items():
                need(name.startswith('t64_') and row.get('finished') and
                     row.get('status') in ('passed','failed','stopped','cancelled'),'Nonterminal T64 stage')
                if row['status']=='passed':
                    need(paths.digest(session/name/'summary.json')==row['summary_sha256'],'Stage summary changed')
        else:
            need(s.get('finished') and s.get('status') in
                 ('report_and_unknown_inventory_ready_review_required','exported_independent_review_required','failed'),
                 'Unknown or active T64 session')
        result.append(dict(session=str(session),state_sha256=paths.digest(f)))
    return result


def archive(req):
    need(req['schema']=='t64-runtime-copy-v1','Wrong archive request')
    uid=paths._identity();root,_=paths._root(req['runtime_root'],uid)
    bundle=Path(req['bundle'])
    cfg=paths.configure(read(bundle/'handoff/team/server_config.json'),bundle,root,req['bundle_manifest_sha256'],req.get('runtime_evidence',()))
    queue=verify_queue_path(Path(req['queue']),bundle)
    need(paths.digest(queue/'state.json')==req['queue_state_sha256'],'Completed queue identity changed')
    target=Path(req['destination']).absolute()
    need(paths._plain(target.parent)==BACKUPS and target.parent.stat().st_uid==uid and
         re.fullmatch(r't64-runtime-[0-9]{8}_[0-9]{4}(?:-[A-Za-z0-9_-]+)?',target.name) and
         not target.exists() and not target.is_symlink(),'Fresh durable T64 backup directory required')
    need(target.parent.stat().st_dev!=root.stat().st_dev,'Backup must be on a different durable filesystem')
    # The generic lock owns only new metadata; release never touches other locks.
    lock,identity,owner=tar.acquire_lock(cfg,target.name)
    created=False
    try:
        states=terminal_sessions(bundle,queue)
        before=tar.no_open_users([root],copy_only=True)
        rows=inventory(root,uid)
        size=tar.stream_archive(rows,tar.Sink())
        required=(size*6+4)//5+tar.RESERVE
        need(shutil.disk_usage(str(target.parent)).free>=required,'Need 1.2x compressed archive plus 2 GiB reserve')
        need(inventory(root,uid)==rows and terminal_sessions(bundle,queue)==states,'Runtime changed during size check')
        target.mkdir(mode=0o700);created=True
        tar.save(target/'state.json',dict(status='copying',source_deleted=False))
        manifest=dict(schema=req['schema'],request=req,files=rows,terminal_sessions=states,
            source_deleted=False,source_modified=False,archive_implies_acceptance=False,
            tools={Path(m.__file__).name:paths.digest(m.__file__) for m in (tar,paths)},
            archiver_sha256=paths.digest(__file__),predicted_gzip_bytes=size,
            source_root=str(root),member_prefix=root.name,
            relocation_verified=False,external_link_targets_copied=False)
        tar.save(target/'manifest.json',manifest)
        partial=target/'runtime-evidence.tar.gz.partial'
        with partial.open('xb') as stream:
            written=tar.stream_archive(rows,tar.Sink(stream,target));stream.flush();os.fsync(stream.fileno())
        need(written==size==partial.stat().st_size,'Archive size changed')
        counts=tar.verify_archive(partial,rows)
        digest=paths.digest(partial)
        need(inventory(root,uid)==rows and terminal_sessions(bundle,queue)==states,'Source changed during copy')
        after=tar.no_open_users([root],copy_only=True);paths.recheck(cfg)
        final=target/'runtime-evidence.tar.gz';need(not final.exists(),'Archive destination exists')
        os.rename(str(partial),str(final));tar.sync_dir(target)
        receipt=dict(schema=req['schema'],status='verified_copy',finished=tar.now(),
            archive_sha256=digest,archive_bytes=size,member_counts=counts,
            manifest_sha256=paths.digest(target/'manifest.json'),source_deleted=False,source_modified=False,
            all_members_readback_verified=True,source_before_after_identical=True,
            process_observation_before=before,process_observation_after=after,
            relocation_verified=False,archive_implies_acceptance=False)
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
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--request',type=Path,required=True);p.add_argument('--request-sha256',required=True)
    a=p.parse_args();need(paths.digest(a.request)==a.request_sha256,'Archive request changed')
    result=archive(read(a.request))
    print('T64_RUNTIME_COPY_VERIFIED',result['archive_sha256'],result['archive_bytes'],'source_deleted=false',flush=True)
