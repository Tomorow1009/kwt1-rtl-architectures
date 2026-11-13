"""Archive idle, explicitly registered N1 runtime bundles; never delete source.

Preserves every regular file, empty directory and symbolic-link target as an
archive member. Links are not followed, external vendor targets are not copied,
and no extraction or relocated-verifier claim is made. Python 3.6 standard lib.
"""
import argparse
import datetime
import errno
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import socket
import stat
import sys
import tarfile
import uuid

sys.dont_write_bytecode=True
import n1_paths as paths

SCHEMA='arch03-n1-runtime-archive-v1'
BACKUPS=Path(paths.SERVER_ROOT)/'light-light126-undergrad-d2-20261109/backups'
PROC_ROOT=Path('/proc')
RESERVE=2*1024**3
CHUNK=4*1024**2
require=paths.require


def now():return datetime.datetime.utcnow().isoformat()+'Z'


def stamp(path):
    value=Path(path).lstat()
    return [value.st_dev,value.st_ino,value.st_size,value.st_mtime_ns,value.st_ctime_ns,
            value.st_uid,value.st_gid,value.st_mode,value.st_nlink]


def sync_dir(path):
    descriptor=os.open(str(path),os.O_RDONLY|getattr(os,'O_DIRECTORY',0))
    try:os.fsync(descriptor)
    finally:os.close(descriptor)


def save(path,value):
    path=Path(path);temporary=path.with_name(path.name+'.next-'+uuid.uuid4().hex)
    with temporary.open('x',encoding='utf8') as stream:
        json.dump(value,stream,indent=2,sort_keys=True,allow_nan=False)
        stream.write('\n');stream.flush();os.fsync(stream.fileno())
    os.replace(str(temporary),str(path));sync_dir(path.parent)


def _under(path,roots):
    return any(path==root or root in path.parents for root in roots)


def no_open_users(roots,copy_only=False):
    """One /proc sweep of this private-directory owner's actual open uses.

    Covers descriptors, mapped files, cwd and executables. The account-private
    0700 roots exclude ordinary other-account users. Strict mode fails on
    unreadable processes. Copy-only mode records protected processes as unknown;
    it does NOT prove idle and cannot authorize deleting or moving any source.
    Complete before/after file identities and archive readback are still required.
    """
    uid=paths._identity();uses=[];inspected=0;inaccessible=[]
    for process in PROC_ROOT.iterdir():
        if not process.name.isdigit():continue
        try:
            if process.stat().st_uid!=uid:continue
            inspected+=1
            links=[process/'cwd',process/'exe']+list((process/'fd').iterdir())
            for link in links:
                try:target=os.readlink(str(link))
                except OSError as error:
                    if error.errno in (errno.ENOENT,errno.ESRCH):continue
                    raise
                target=target[:-10] if target.endswith(' (deleted)') else target
                if target.startswith('/') and _under(Path(target),roots):
                    uses.append(dict(pid=int(process.name),kind=link.name,path=target))
            for line in (process/'maps').read_text().splitlines():
                fields=line.split(None,5)
                if len(fields)==6 and fields[5].startswith('/'):
                    target=fields[5][:-10] if fields[5].endswith(' (deleted)') else fields[5]
                    if _under(Path(target),roots):uses.append(dict(pid=int(process.name),kind='mapped',path=target))
        except OSError as error:
            if error.errno in (errno.ENOENT,errno.ESRCH):continue
            if copy_only and error.errno in (errno.EACCES,errno.EPERM):
                inaccessible.append(dict(pid=int(process.name),errno=error.errno,
                    visibility='protected_process_not_inspected'))
                continue
            raise ValueError('Cannot prove runtime idle: '+str(error))
    require(not uses,'Runtime files are still in use: '+json.dumps(uses[:20],sort_keys=True))
    return dict(owned_processes_seen=inspected,owned_processes_inspected=inspected-len(inaccessible),
        observed_open_runtime_uses=0,inaccessible_owned_processes=inaccessible,
        all_owned_processes_observed=not inaccessible,idle_proven=not inaccessible,
        copy_only=copy_only,source_deletion_authorized=False,
        scope='accessible own-account /proc fd/cwd/exe/maps; private0700 source; shared team lock held')


def auxiliary_receipts(bundles,bindings):
    """Explicitly pin only the known completed B0 read-only inventory receipts.

    This is an archive-terminal classification, never an N1 stage or power PASS.
    Unknown sessions still need their normal N1 terminal state.
    """
    require(isinstance(bindings,list),'Auxiliary run bindings must be a list')
    uid=paths._identity();records={}
    for binding in bindings:
        require(isinstance(binding,dict) and set(binding)=={'run','receipt_sha256'},
            'Auxiliary binding requires only run and receipt_sha256')
        run=Path(binding['run']);expected=binding['receipt_sha256']
        require(run.is_absolute() and run.parent.name=='runs' and run.parent.parent in bundles,
            'Auxiliary run must be a direct session of a registered bundle')
        require(isinstance(expected,str) and re.fullmatch('[a-f0-9]{64}',expected),
            'Explicit auxiliary receipt SHA256 is required')
        run=paths._owned(run,run.parent.parent,uid)
        require(run.is_dir() and run not in records,'Duplicate or non-directory auxiliary run')
        state=run/'state.json'
        require(not state.exists() and not state.is_symlink(),'Auxiliary binding cannot override an N1 state')
        receipt=paths._owned(run/'inventory.json',run.parent.parent,uid)
        require(stat.S_ISREG(receipt.lstat().st_mode) and paths.digest(receipt)==expected,
            'Auxiliary receipt SHA256 differs')
        value=json.loads(receipt.read_text())
        require(value.get('schema')=='b0-read-only-power-review-inventory-v1' and
            value.get('status') in ('inventory_rejected','read_only_inventory_collected_review_required') and
            value.get('system_power_verified') is False,'Unknown auxiliary receipt schema or terminal status')
        if value['status']=='inventory_rejected':
            require(isinstance(value.get('error'),str) and value['error'].strip(),
                'Rejected auxiliary inventory lacks its error')
        else:
            require(all(value.get(name) is True for name in
                ('no_eda_or_simulation_started','no_files_written','no_large_wave_read')),
                'Auxiliary inventory lacks explicit read-only evidence')
        require(paths.digest(receipt)==expected,'Auxiliary receipt changed while reading')
        records[run]=dict(bundle=run.parent.parent.name,session=run.name,
            kind='auxiliary_read_only_inventory',receipt='inventory.json',receipt_sha256=expected,
            receipt_schema=value['schema'],status=value['status'],system_power_verified=False,
            acceptance_not_inferred_from_archive=True)
    return records


def completed_queue(session,state,request_binding=None):
    """Archive the serial observer's own terminal schema, without granting PASS."""
    require(state.get('status') in ('numbers_ready_independent_review_required','failed') and
        state.get('finished') and state.get('child_pid') is None and
        state.get('n2_allowed') is False and state.get('system_power_verified') is False,
        'N1 continuation queue has not safely ended')
    request_path=paths._plain(session/'request.json')
    request=json.loads(request_path.read_text())
    copy_digest=paths.digest(request_path)
    original_request=None
    if copy_digest!=state.get('request_sha256'):
        # The observer preserves a canonical atomic_save copy but pins the
        # original CLI file's bytes. An explicit original identity must prove
        # both the original hash and complete JSON equality; never waive it.
        require(isinstance(request_binding,dict) and
            set(request_binding)=={'session','request','sha256'} and
            request_binding['session']==str(session),
            'Queue request digest changed; explicit original binding required')
        require(request_binding['sha256']==state.get('request_sha256'),
            'Queue original binding differs from recorded request SHA')
        source=paths._owned(Path(request_binding['request']),session.parent.parent.parent,paths._identity())
        require(source.is_file() and paths.digest(source)==request_binding['sha256'],
            'Queue original request bytes changed')
        require(json.loads(source.read_text())==request,
            'Queue copied request content differs from pinned original')
        original_request=dict(path=str(source),sha256=request_binding['sha256'],
            copied_request_sha256=copy_digest,parsed_JSON_identical=True)
    elif request_binding is not None:
        require(request_binding.get('session')==str(session) and
            request_binding.get('sha256')==copy_digest and
            paths.digest(paths._owned(Path(request_binding['request']),session.parent.parent.parent,paths._identity()))==copy_digest,
            'Unnecessary queue request binding has a different identity')
    require(request.get('schema')=='arch03-n1-acceptance-continuation-v1' and
        request.get('bundle')==str(session.parent.parent),'Queue bundle/schema differs')
    rows=state.get('completed')
    require(isinstance(rows,list) and len(rows)<=13,'Invalid queue completed prefix')
    expected=[('precision','n1_precision')]+[('power%02d'%i,'n1_power') for i in range(1,13)]
    for index,row in enumerate(rows):
        label,kind=expected[index]
        require(row.get('label')==label and row.get('stage')==kind,'Queue completed order differs')
        suffix='_precision' if index==0 else '_p%02d'%index
        run=session.parent/(session.name+suffix)/kind
        ref=row.get('reference',{})
        require(ref.get('run')==str(run),'Queue child escaped its session')
        summary=paths._plain(run/'summary.json')
        child=json.loads(paths._plain(run.parent/'state.json').read_text())
        record=child.get('stages',{}).get(kind,{})
        require(child.get('schema')=='arch03-n1-server-state-v1' and
            record.get('status')=='passed' and record.get('finished') and
            record.get('summary_sha256')==ref.get('sha256')==paths.digest(summary),
            'Queue completed child identity differs')
    if state['status']=='numbers_ready_independent_review_required':
        require(len(rows)==13,'Completed queue lacks precision or power layers')
    else:
        require(isinstance(state.get('error'),str) and state['error'].strip(),'Failed queue lacks reason')
    return dict(bundle=session.parent.parent.name,session=session.name,kind='serial_observer_queue',
        status=state['status'],completed_children=len(rows),state_sha256=paths.digest(session/'state.json'),
        request_sha256=state['request_sha256'],original_request_binding=original_request,
        copied_request_sha256=copy_digest,system_power_verified=False,
        acceptance_not_inferred_from_archive=True)


def terminal_states(bundles,bindings=None,queue_bindings=None):
    auxiliary=auxiliary_receipts(bundles,[] if bindings is None else bindings)
    queue_bindings=[] if queue_bindings is None else queue_bindings
    require(isinstance(queue_bindings,list),'Queue request bindings must be a list')
    requests={}
    for item in queue_bindings:
        require(isinstance(item,dict) and set(item)=={'session','request','sha256'},'Invalid queue request binding')
        session=Path(item['session'])
        require(session.parent.name=='runs' and session.parent.parent in bundles and
            session not in requests,'Unregistered or duplicate queue request binding')
        requests[session]=item
    records=[];consumed=set();used_requests=set()
    for bundle in bundles:
        runs=bundle/'runs'
        # lstat before exists/iterdir: even a dangling symlink is an unsafe root.
        try:runs_stat=runs.lstat()
        except FileNotFoundError:continue
        require(not stat.S_ISLNK(runs_stat.st_mode) and stat.S_ISDIR(runs_stat.st_mode),
            'Runtime runs root must be a real directory: '+str(runs))
        runs=paths._owned(runs,bundle,paths._identity())
        for session in sorted(runs.iterdir()):
            if session.is_symlink():continue  # inventoried verbatim, never followed
            if not session.is_dir():continue
            state_path=session/'state.json'
            if session in auxiliary:
                records.append(auxiliary[session]);consumed.add(session);continue
            require(not state_path.is_symlink() and state_path.is_file(),'Session lacks terminal state: '+str(session))
            state=json.loads(state_path.read_text())
            if state.get('schema')=='arch03-n1-acceptance-queue-state-v1':
                records.append(completed_queue(session,state,requests.get(session)))
                if session in requests:used_requests.add(session)
                continue
            require(state.get('schema')=='arch03-n1-server-state-v1' and state.get('stages'),
                'Unknown runtime session state: '+str(session))
            for stage,row in state['stages'].items():
                require(re.fullmatch('n1_[a-z0-9_]+',stage) and row.get('status') in ('passed','failed','stopped','cancelled') and
                    row.get('finished'),'Runtime stage has not ended: '+str(session)+'/'+stage)
                if row['status']=='passed':
                    summary=paths._plain(session/stage/'summary.json')
                    require(stat.S_ISREG(summary.lstat().st_mode) and paths.digest(summary)==row['summary_sha256'],
                        'Terminal stage summary changed')
                records.append(dict(bundle=bundle.name,session=session.name,stage=stage,status=row['status'],
                    state_sha256=paths.digest(state_path),summary_sha256=row.get('summary_sha256'),
                    acceptance_not_inferred_from_archive=True))
    require(consumed==set(auxiliary),'Unused auxiliary run binding')
    require(used_requests==set(requests),'Unused queue request binding')
    return records


def link_class(path,target,bundles):
    # Lexical normalization only: do not resolve or open the target.
    joined=target if os.path.isabs(target) else os.path.join(str(path.parent),target)
    absolute=Path(os.path.normpath(joined))
    if _under(absolute,bundles):return 'registered_runtime_reference'
    if absolute.as_posix().startswith(('/storage1/admin_public_dir/','/eda/')):return 'external_vendor_reference_not_copied'
    return 'external_or_unresolved_reference_not_copied'


def inventory(cfg):
    paths.recheck(cfg);uid=paths._identity();rows=[]
    bundles=[Path(row['bundle']) for row in cfg['runtime_roots']]
    for bundle in bundles:
        pending=[bundle]
        while pending:
            path=pending.pop();before=stamp(path);value=path.lstat()
            require(value.st_uid==uid,'Other-owner runtime artifact: '+str(path))
            member=path.relative_to(bundle.parent).as_posix()
            member.encode('utf8')  # unsupported filesystem names must stop, not disappear
            row=dict(source=str(path),member=member,stamp=before,mode=stat.S_IMODE(value.st_mode),
                uid=value.st_uid,gid=value.st_gid,mtime_ns=value.st_mtime_ns)
            if stat.S_ISDIR(value.st_mode):
                row.update(kind='directory',bytes=0,sha256=hashlib.sha256(b'').hexdigest())
                pending.extend(reversed(sorted(path.iterdir())))
            elif stat.S_ISREG(value.st_mode):
                row.update(kind='regular',bytes=value.st_size,sha256=paths.digest(path))
            elif stat.S_ISLNK(value.st_mode):
                target=os.readlink(str(path));raw=target.encode('utf8')
                require(os.fsencode(target)==raw,'Non-UTF8 symlink target cannot be safely expressed')
                row.update(kind='symlink',target=target,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),
                    link_class=link_class(path,target,bundles),target_content_archived=False)
            else:raise ValueError('Special runtime artifact cannot be safely archived: '+str(path))
            require(stamp(path)==before,'Runtime artifact changed while hashing: '+str(path))
            rows.append(row)
    require(len({row['member'] for row in rows})==len(rows),'Duplicate archive member')
    return sorted(rows,key=lambda row:row['member'])


class Sink:
    def __init__(self,stream=None,directory=None):
        self.stream=stream;self.directory=directory;self.count=0;self.next_guard=0
    def write(self,raw):
        if self.stream is not None:
            if self.count>=self.next_guard:
                free=shutil.disk_usage(str(self.directory)).free
                require(free>=RESERVE+CHUNK+len(raw),'Shared reserve reached; source and partial archive retained')
                self.next_guard=self.count+CHUNK
            self.stream.write(raw)
        self.count+=len(raw);return len(raw)
    def flush(self):
        if self.stream is not None:self.stream.flush()
    def tell(self):return self.count


class CheckedReader:
    def __init__(self,stream):self.stream=stream;self.hash=hashlib.sha256();self.count=0
    def read(self,count):
        raw=self.stream.read(count);self.hash.update(raw);self.count+=len(raw);return raw


def stream_archive(rows,sink):
    """Deterministic gzip count/write, never tar.add's implicit symlink handling."""
    with gzip.GzipFile(filename='',fileobj=sink,mode='wb',compresslevel=1,mtime=0) as packed:
        with tarfile.open(fileobj=packed,mode='w|',format=tarfile.PAX_FORMAT) as archive:
            for index,row in enumerate(rows,1):
                source=Path(row['source']);require(stamp(source)==row['stamp'],'Source changed before archive member')
                member=tarfile.TarInfo(row['member']);member.mode=row['mode'];member.uid=row['uid'];member.gid=row['gid']
                member.mtime=row['mtime_ns']//1000000000
                if row['kind']=='regular':
                    member.type=tarfile.REGTYPE;member.size=row['bytes']
                    descriptor=os.open(str(source),os.O_RDONLY|getattr(os,'O_NOFOLLOW',0))
                    with os.fdopen(descriptor,'rb') as stream:
                        current=os.fstat(stream.fileno())
                        require([current.st_dev,current.st_ino]==row['stamp'][:2],'Source regular file identity changed')
                        reader=CheckedReader(stream);archive.addfile(member,reader)
                        require(reader.count==row['bytes'] and reader.hash.hexdigest()==row['sha256'],'Source bytes changed during archive')
                elif row['kind']=='directory':member.type=tarfile.DIRTYPE;archive.addfile(member)
                else:
                    require(os.readlink(str(source))==row['target'],'Symlink target changed during archive')
                    member.type=tarfile.SYMTYPE;member.linkname=row['target'];archive.addfile(member)
                require(stamp(source)==row['stamp'],'Source metadata changed during archive')
                if index%1000==0:
                    print('N1_ARCHIVE_STREAM', 'count' if sink.stream is None else 'write',
                          'members',index,'gzip_bytes',sink.count,flush=True)
    return sink.count


def verify_archive(path,rows):
    expected={row['member']:row for row in rows};counts=dict(regular=0,directory=0,symlink=0)
    with tarfile.open(str(path),'r:gz') as archive:
        for member in archive:
            name=member.name.rstrip('/') if member.isdir() else member.name
            require(name in expected,'Extra/duplicate archive member')
            row=expected.pop(name)
            require(member.uid==row['uid'] and member.gid==row['gid'] and member.mode==row['mode'] and
                member.mtime==row['mtime_ns']//1000000000,'Archive metadata mismatch')
            if row['kind']=='regular':
                require(member.isfile() and member.size==row['bytes'],'Archive regular file size/type mismatch')
                value=hashlib.sha256();size=0
                with archive.extractfile(member) as stream:
                    for block in iter(lambda:stream.read(CHUNK),b''):value.update(block);size+=len(block)
                require(size==row['bytes'] and value.hexdigest()==row['sha256'],'Archive restored SHA/bytes mismatch')
            elif row['kind']=='directory':require(member.isdir(),'Archive directory mismatch')
            else:
                require(member.issym() and member.linkname==row['target'] and
                    hashlib.sha256(member.linkname.encode('utf8')).hexdigest()==row['sha256'],'Archive symlink mismatch')
            counts[row['kind']]+=1
        # tar stops at its end marker before gzip necessarily checks CRC/ISIZE.
        # Drain the gzip reader to EOF and permit only tar's zero padding.
        for tail in iter(lambda:archive.fileobj.read(CHUNK),b''):
            require(not any(tail),'Nonzero trailing archive data')
    require(not expected,'Missing archive members')
    return counts


def destination(path,root,uid):
    path=Path(path).absolute();parent=paths._plain(path.parent)
    require(parent==BACKUPS and re.fullmatch(r'n1-runtime-[0-9]{8}_[0-9]{4}(?:-[A-Za-z0-9_-]+)?',path.name),
        'Use a fresh fixed shared backups/n1-runtime-DATE_TIME directory')
    require(parent.stat().st_uid==uid and not path.exists() and not path.is_symlink(),'Backup destination exists or has wrong owner')
    require(parent.stat().st_dev!=root.stat().st_dev,'Backup must be on durable shared storage, not the runtime filesystem')
    return path


def acquire_lock(cfg,session):
    lock=Path(cfg['server_root'])/'.arch02_team_lock';lock.mkdir()
    identity=stamp(lock)[:2];owner=dict(pid=os.getpid(),host=socket.gethostname(),
        bundle=cfg['runtime_roots'][0]['bundle'],session=session,kind=SCHEMA,token=uuid.uuid4().hex,started_utc=now())
    try:save(lock/'owner.json',owner)
    except BaseException:
        # Only this newly created empty metadata lock; never source or backups.
        if stamp(lock)[:2]==identity and not any(lock.iterdir()):lock.rmdir()
        raise
    return lock,identity,owner


def release_lock(lock,identity,owner):
    require(stamp(lock)[:2]==identity and json.loads((lock/'owner.json').read_text())==owner,
        'Archive lock ownership changed; preserve it for review')
    (lock/'owner.json').unlink();lock.rmdir()  # release only own coordination metadata


def archive(request):
    tool_identity={str(Path(name).resolve()):paths.digest(Path(name)) for name in (__file__,paths.__file__)}
    uid=paths._identity();root,_=paths._root(request['runtime_root'],uid)
    ops=paths._owned(request['ops_bundle'],root,uid)
    require(ops.parent==root and re.fullmatch(paths.BUNDLE_NAME,ops.name),'Archive OPS must be a direct registered-root child')
    config_path=paths._plain(ops/'handoff/team/server_config.json');cfg=json.loads(config_path.read_text())
    cfg=paths.configure(cfg,ops,request['runtime_root'],request['ops_manifest_sha256'],request.get('evidence',[]))
    require(paths.digest(Path(paths.__file__))==json.loads((ops/'manifest.json').read_text())['files']['workspaces/arch03/scripts/n1_paths.py'],
        'Archiver path validator differs from pinned OPS validator')
    root=Path(request['runtime_root']);bundles=[Path(row['bundle']) for row in cfg['runtime_roots']]
    target=destination(request['destination'],root,paths._identity())
    lock,lock_identity,owner=acquire_lock(cfg,target.name);created=False
    try:
        auxiliary=request.get('auxiliary_runs',[]);queue_bindings=request.get('queue_request_bindings',[])
        copy_only=request.get('allow_incomplete_process_visibility_for_copy_only',False)
        require(type(copy_only) is bool,'Copy-only process visibility flag must be boolean')
        terminal=terminal_states(bundles,auxiliary,queue_bindings);before_uses=no_open_users(bundles,copy_only=copy_only);rows=inventory(cfg)
        print('N1_ARCHIVE_IDLE_INVENTORY',len(rows),'members','source_regular_bytes',
              sum(row['bytes'] for row in rows if row['kind']=='regular'),flush=True)
        predicted=stream_archive(rows,Sink())
        required=(predicted*6+4)//5+RESERVE;free=shutil.disk_usage(str(target.parent)).free
        require(free>=required,'Insufficient shared archive space: need 1.2x exact gzip bytes plus 2GiB')
        require(inventory(cfg)==rows and terminal_states(bundles,auxiliary,queue_bindings)==terminal,'Source changed during archive size preflight')
        no_open_users(bundles,copy_only=copy_only)
        target.mkdir(mode=0o700);created=True;sync_dir(target.parent)
        save(target/'state.json',dict(status='archiving',started_utc=now(),source_modified=False,source_deleted=False))
        manifest=dict(schema=SCHEMA,runtime_identity=paths.receipt(cfg),files=rows,terminal_states=terminal,
            request=request,tool_identity_sha256=tool_identity,
            source_regular_bytes=sum(row['bytes'] for row in rows if row['kind']=='regular'),
            space=dict(exact_gzip_bytes=predicted,required_bytes=required,free_bytes=free,margin=1.2,reserve_bytes=RESERVE),
            symlink_policy='Preserve link target text and hash; never follow or copy target content',
            source_modified=False,source_deleted=False,archive_implies_acceptance=False,
            external_libraries='Original references remain unchanged; only regular files physically within registered bundles are included')
        save(target/'manifest.json',manifest)
        mapping=dict(schema='arch03-n1-archive-recovery-index-v1',
            original_paths_unchanged=True,source_receipts_unchanged=True,
            bundle_prefixes=[dict(original=row['bundle'],archive_member_prefix=Path(row['bundle']).name,
                                 manifest_sha256=row['manifest_sha256']) for row in cfg['runtime_roots']],
            original_path_to_member_manifest='manifest.json: files[].source -> files[].member',
            relocated_verifier_verified=False,clean_directory_reproduction_verified=False,
            instructions='Use a NEW empty restore directory. Verify all member types/bytes/SHA first. Do not automatically create or follow archived symlinks. Original absolute paths are an index, not authority to overwrite those paths. External dependency targets and any relocation must be reviewed separately.')
        save(target/'recovery_index.json',mapping)
        partial=target/'runtime-evidence.tar.gz.partial'
        with partial.open('xb') as stream:
            size=stream_archive(rows,Sink(stream,target));stream.flush();os.fsync(stream.fileno())
        require(size==predicted and partial.stat().st_size==predicted,'Deterministic gzip byte estimate changed')
        counts=verify_archive(partial,rows);archive_sha=paths.digest(partial)
        require(inventory(cfg)==rows and terminal_states(bundles,auxiliary,queue_bindings)==terminal,'Source changed during archive verification')
        after_uses=no_open_users(bundles,copy_only=copy_only);paths.recheck(cfg)
        require(all(paths.digest(Path(name))==value for name,value in tool_identity.items()),'Archiver tools changed during execution')
        final=target/'runtime-evidence.tar.gz';require(not final.exists(),'Archive final name exists')
        os.rename(str(partial),str(final));sync_dir(target)
        receipt=dict(schema=SCHEMA,status='verified',finished_utc=now(),source_modified=False,source_deleted=False,
            source_temp_cleanup_authorized=False,archive_bytes=size,archive_sha256=archive_sha,member_counts=counts,
            source_regular_bytes=manifest['source_regular_bytes'],manifest_sha256=paths.digest(target/'manifest.json'),
            recovery_index_sha256=paths.digest(target/'recovery_index.json'),open_users_before=before_uses,open_users_after=after_uses,
            source_before_after_sha_and_metadata_identical=True,all_archive_members_stream_read_and_verified=True,
            regular_contents_verified=True,symlink_targets_verified_without_following=True,
            relocated_verifier_verified=False,clean_directory_reproduction_verified=False,
            archiver_sha256=tool_identity[str(Path(__file__).resolve())],validator_sha256=tool_identity[str(Path(paths.__file__).resolve())])
        save(target/'receipt.json',receipt)
        save(target/'state.json',dict(status='verified',receipt_sha256=paths.digest(target/'receipt.json'),finished_utc=now()))
        return receipt
    except BaseException as error:
        if created:
            try:save(target/'state.json',dict(status='failed',error=str(error),source_modification_by_archiver=False,
                source_before_after_unchanged_verified=False,source_deleted=False,
                partial_and_source_preserved=True,relocated_verifier_verified=False,finished_utc=now()))
            except OSError:pass
        raise
    finally:release_lock(lock,lock_identity,owner)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--request',type=Path,required=True)
    args=parser.parse_args();request=json.loads(args.request.read_text())
    result=archive(request)
    print('N1_RUNTIME_ARCHIVE_VERIFIED source_deleted=false relocation_verified=false',result['archive_sha256'],flush=True)
