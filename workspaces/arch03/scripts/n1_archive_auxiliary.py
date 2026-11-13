"""Explicit N1 auxiliary evidence archive; no source deletion or bundle registration.

plan: bounded metadata only; identities: bounded read-only content identities;
archive: requires each reviewed tree SHA, the original shared lock, and full
roundtrip verification. All modes refuse an occupied team lock. Python 3.6.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import socket
import stat
import sys
import time
import uuid

sys.dont_write_bytecode = True
import n1_archive_runtime as base
import n1_paths as paths

SCHEMA = 'arch03-n1-auxiliary-archive-v1'
REQUEST_SCHEMA = 'arch03-n1-auxiliary-archive-request-v1'
RUNTIME = Path('/tmp/s4_21usr_n1_20261113_0210')
OPERATIONS = Path(paths.SERVER_ROOT)/'light-light126-undergrad-d2-20261109/operations'
HELPER_SHA = 'fe02e6774de23bdccf4cc817823de1728bbfdac08110ebb76c423617265df616'
PATHS_SHA = 'fe301e1e5f87852103c537b8191c7064f1b8c44a8979f1977901bf26ed16e39d'
ALLOW = {
    'b0_control_l01_20261113_0403': 'directory',
    'n1_batch01_lock_recovery_0452': 'directory',
    'zip8_20261113_051340': 'directory',
    'retained_ops_upload_20261113_0428.zip': 'regular',
    'duplicate_ops_zip_receipt_0428.json': 'regular',
    'light-light126-n1-reviewops-20261113_0313-1f86fc70d41e': 'directory',
    'light-light126-n1-controlops-20261113_035653-3165fb3cab28': 'directory',
    'light-light126-n1-archiveops-20261113_033430-0f3a46d3f3fb': 'directory',
    'light-light126-n1-archiveops-3b5cf866b337': 'directory',
    'light-light126-n1-evidenceops-20261113_0640': 'directory',
    'b0_control_l02_l12_20261113_0640': 'directory',
    'light-light126-n1-precisionops-20261113_0840': 'directory',
    'light-light126-n1-precisionops02-20261113_090845': 'directory',
    'light-light126-n1-queueops-20261113_091833': 'directory',
    'n1_precision_inputs_20261113_0840': 'directory',
    'n1_numpy1195_20261113_0905': 'directory',
}
MAX_ENTRIES = 10000
MAX_BYTES = 2*1024**3
MAX_FILE = 512*1024**2
MAX_DEPTH = 12
SCAN_SECONDS = 60
PLAN_SECONDS = 30
require = paths.require


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)+'\n').encode('utf8')


def dependencies():
    require(paths.digest(Path(base.__file__)) == HELPER_SHA, 'Frozen archive helper SHA differs')
    require(paths.digest(Path(paths.__file__)) == PATHS_SHA, 'Frozen path validator SHA differs')
    return {str(Path(p).resolve()): paths.digest(Path(p)) for p in (__file__, base.__file__, paths.__file__)}


def lock_path():
    return Path(paths.SERVER_ROOT)/'.arch02_team_lock'


def idle_lock():
    lock = lock_path()
    require(not lock.exists() and not lock.is_symlink(), 'Original team lock is occupied; no archive or scan')


def destination(path, root, uid):
    path = Path(path).absolute()
    parent = paths._plain(path.parent)
    require(parent == OPERATIONS and re.fullmatch('n1-aux-archive-[0-9]{8}_[0-9]{4}(?:-[A-Za-z0-9_-]+)?', path.name),
            'Auxiliary destination must be a new fixed project operations directory')
    require(paths._stat(parent).st_uid == uid and parent.is_dir(), 'Destination parent owner/type differs')
    require(not path.exists() and not path.is_symlink(), 'Auxiliary destination already exists')
    require(paths._stat(parent).st_dev != paths._stat(root).st_dev, 'Destination must be durable shared storage')
    return path


def validate(request, need_identities=False):
    require(set(request) == {'schema', 'runtime_root', 'destination', 'entries'} and
            request['schema'] == REQUEST_SCHEMA, 'Unknown auxiliary request schema or keys')
    require(Path(request['runtime_root']) == RUNTIME, 'Only the exact existing N1 private root is allowed')
    uid = paths._identity(); root, _ = paths._root(RUNTIME, uid)
    target = destination(request['destination'], root, uid)
    entries = request['entries']
    require(isinstance(entries, list) and 0 < len(entries) <= len(ALLOW), 'Explicit bounded entry list required')
    names = []
    for entry in entries:
        require(isinstance(entry, dict) and set(entry) == {'name', 'tree_sha256'}, 'Each entry needs name and reviewed tree_sha256')
        name = entry['name']; digest = entry['tree_sha256']
        require(isinstance(name, str) and name in ALLOW and name not in names, 'Entry is unlisted, duplicate or traversing')
        require((digest is None and not need_identities) or
                (isinstance(digest, str) and re.fullmatch('[a-f0-9]{64}', digest)), 'Reviewed per-entry tree SHA required')
        names.append(name)
    return root, target, uid, names


def scan(root, names, uid, hashes):
    """Only selected trees; lstat/scandir never follow links or enumerate /tmp."""
    paths._root(root, uid)
    started = time.monotonic(); limit = SCAN_SECONDS if hashes else PLAN_SECONDS
    pending = [root/name for name in reversed(names)]; rows = []; discovered = len(pending); size = 0
    while pending:
        require(time.monotonic()-started < limit, 'Bounded scan time exceeded; incomplete, not an identity')
        source = pending.pop(); before = base.stamp(source); value = source.lstat()
        require(value.st_uid == uid and paths._stat(source).st_uid == uid, 'Auxiliary source has another owner')
        require(not stat.S_ISLNK(value.st_mode) and not stat.S_ISLNK(paths._stat(source).st_mode), 'Auxiliary symlink refused')
        paths._owned(source, root, uid)
        member = source.relative_to(root).as_posix()
        require('\\' not in member and all(ord(c) >= 32 for c in member), 'Ambiguous auxiliary member name')
        require(len(source.relative_to(root).parts) <= MAX_DEPTH, 'Auxiliary tree depth exceeded')
        row = dict(source=str(source), member=member, stamp=before, mode=stat.S_IMODE(value.st_mode),
                   uid=value.st_uid, gid=value.st_gid, mtime_ns=value.st_mtime_ns)
        if stat.S_ISDIR(value.st_mode):
            row.update(kind='directory', bytes=0, sha256=hashlib.sha256(b'').hexdigest() if hashes else None)
            children = []
            with os.scandir(str(source)) as stream:
                for child in stream:
                    discovered += 1
                    require(discovered <= MAX_ENTRIES, 'Auxiliary entry limit exceeded; incomplete scan')
                    require(time.monotonic()-started < limit, 'Bounded scan time exceeded')
                    children.append(Path(child.path))
            pending.extend(reversed(sorted(children)))
        elif stat.S_ISREG(value.st_mode):
            require(value.st_size <= MAX_FILE, 'Unexpected large auxiliary file')
            size += value.st_size
            require(size <= MAX_BYTES, 'Auxiliary total byte limit exceeded')
            digest = None
            if hashes:
                descriptor = os.open(str(source), os.O_RDONLY|getattr(os, 'O_NOFOLLOW', 0))
                with os.fdopen(descriptor, 'rb') as stream:
                    opened = os.fstat(stream.fileno())
                    require([opened.st_dev, opened.st_ino] == before[:2], 'Source replaced before content read')
                    measured = hashlib.sha256(); total = 0
                    for block in iter(lambda: stream.read(base.CHUNK), b''):
                        require(time.monotonic()-started < limit, 'Bounded content read time exceeded')
                        total += len(block); require(total <= value.st_size, 'Source grew during content read')
                        measured.update(block)
                    require(total == value.st_size, 'Source truncated during content read')
                    digest = measured.hexdigest()
            row.update(kind='regular', bytes=value.st_size, sha256=digest)
        else:
            raise ValueError('Special auxiliary file refused')
        if source.parent == root:
            require(row['kind'] == ALLOW[source.name], 'Allowlisted source type changed')
        require(base.stamp(source) == before, 'Auxiliary source changed during scan')
        rows.append(row)
    require(time.monotonic()-started < limit, 'Bounded scan time exceeded')
    return sorted(rows, key=lambda row: row['member'])


def tree_identities(rows, names):
    return {name: hashlib.sha256(encoded([row for row in rows if row['member'] == name or
                                         row['member'].startswith(name+'/')])).hexdigest() for name in names}


def acquire(request):
    lock = lock_path(); lock.mkdir()
    stamp = base.stamp(lock)
    owner = dict(schema=SCHEMA, pid=os.getpid(), host=socket.gethostname(), token=uuid.uuid4().hex,
                 session=Path(request['destination']).name, source_root=request['runtime_root'], started=base.now())
    raw = encoded(owner)
    try:
        with (lock/'owner.json').open('xb') as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        base.sync_dir(lock)
    except BaseException:
        # Only our newly created, unchanged and still empty coordination directory.
        if base.stamp(lock)[:2] == stamp[:2] and not any(lock.iterdir()):
            lock.rmdir()
        raise
    return lock, stamp[:2], base.stamp(lock/'owner.json')[:2], raw


def check_lock(identity):
    lock, directory, owner_file, raw = identity
    require(base.stamp(lock)[:2] == directory and base.stamp(lock/'owner.json')[:2] == owner_file and
            (lock/'owner.json').read_bytes() == raw and {p.name for p in lock.iterdir()} == {'owner.json'},
            'Auxiliary archive lock ownership changed; retain for manual review')


def release(identity):
    check_lock(identity)
    lock = identity[0]
    (lock/'owner.json').unlink(); lock.rmdir()  # our own lock metadata only


def process(request, mode):
    require(mode in ('plan', 'identities', 'archive'), 'Unknown auxiliary mode')
    tools = dependencies(); root, target, uid, names = validate(request, mode == 'archive')
    idle_lock(); roots = [root/name for name in names]
    if mode != 'archive':
        if mode == 'identities': base.no_open_users(roots)
        rows = scan(root, names, uid, mode == 'identities')
        if mode == 'identities':
            require(scan(root, names, uid, False) == [dict(row, sha256=None) for row in rows], 'Sources changed after identity scan')
            base.no_open_users(roots)
        idle_lock()
        return dict(schema=SCHEMA, mode=mode, status='bounded_read_only_plan' if mode == 'plan' else 'identities_ready_for_review',
                    source_modified=False, source_deleted=False, archive_created=False, complete=True,
                    selected_names=names, files=rows, regular_bytes=sum(row['bytes'] for row in rows),
                    tree_sha256=tree_identities(rows, names) if mode == 'identities' else None,
                    free_shared_bytes=shutil.disk_usage(str(OPERATIONS)).free,
                    required_bytes=None, budget='Actual gzip bytes C required: ceil(1.2*C)+2GiB; metadata is not compression proof',
                    limits=dict(entries=MAX_ENTRIES, bytes=MAX_BYTES, per_file=MAX_FILE, depth=MAX_DEPTH,
                                seconds=SCAN_SECONDS if mode == 'identities' else PLAN_SECONDS), tools=tools)
    identity = acquire(request); created = False
    try:
        check_lock(identity)
        before_users = base.no_open_users(roots); rows = scan(root, names, uid, True)
        actual = tree_identities(rows, names)
        require(actual == {e['name']: e['tree_sha256'] for e in request['entries']}, 'Reviewed auxiliary tree identity differs')
        predicted = base.stream_archive(rows, base.Sink())
        required = (predicted*6+4)//5+base.RESERVE
        require(shutil.disk_usage(str(OPERATIONS)).free >= required, 'Auxiliary archive needs 20% margin plus 2GiB')
        require(scan(root, names, uid, True) == rows, 'Auxiliary source changed during exact budget')
        base.no_open_users(roots)
        check_lock(identity)
        target.mkdir(mode=0o700); created = True; base.sync_dir(target.parent)
        base.save(target/'state.json', dict(schema=SCHEMA, status='archiving', source_deleted=False))
        manifest = dict(schema=SCHEMA, request=request, request_canonical_sha256=hashlib.sha256(encoded(request)).hexdigest(),
                        files=rows, tree_sha256=actual, tools=tools, original_paths_unchanged=True,
                        source_deleted=False, archive_implies_acceptance=False,
                        space=dict(exact_gzip_bytes=predicted, required_bytes=required, margin=1.2, reserve_bytes=base.RESERVE))
        base.save(target/'manifest.json', manifest)
        base.save(target/'recovery_index.json', dict(schema=SCHEMA, files='manifest.json: files[].source -> files[].member',
            original_paths_unchanged=True, source_receipts_unchanged=True, relocated_verifier_verified=False,
            clean_directory_reproduction_verified=False, restore_only_to_new_empty_directory=True))
        partial = target/'auxiliary-evidence.tar.gz.partial'
        with partial.open('xb') as stream:
            size = base.stream_archive(rows, base.Sink(stream, target)); stream.flush(); os.fsync(stream.fileno())
        require(size == predicted and partial.stat().st_size == predicted, 'Deterministic auxiliary archive size changed')
        counts = base.verify_archive(partial, rows); archive_sha = paths.digest(partial)
        require(scan(root, names, uid, True) == rows, 'Auxiliary source changed during archive verification')
        after_users = base.no_open_users(roots)
        require(dependencies() == tools, 'Auxiliary archive tools changed')
        check_lock(identity)
        final = target/'auxiliary-evidence.tar.gz'; require(not final.exists(), 'Archive output exists')
        os.rename(str(partial), str(final)); base.sync_dir(target)
        receipt = dict(schema=SCHEMA, status='verified', finished=base.now(), source_modified=False, source_deleted=False,
                       selected_names=names, archive_bytes=size, archive_sha256=archive_sha, member_counts=counts,
                       manifest_sha256=paths.digest(target/'manifest.json'), recovery_index_sha256=paths.digest(target/'recovery_index.json'),
                       source_before_after_identical=True, full_member_sha_and_bytes_verified=True,
                       no_open_users_before=before_users, no_open_users_after=after_users,
                       source_temp_cleanup_authorized=False, relocated_verifier_verified=False, hardware_acceptance=False)
        base.save(target/'receipt.json', receipt)
        base.save(target/'state.json', dict(schema=SCHEMA, status='verified', receipt_sha256=paths.digest(target/'receipt.json')))
        return receipt
    except BaseException as error:
        if created:
            try:
                base.save(target/'state.json', dict(schema=SCHEMA, status='failed', error=str(error),
                    source_deleted=False, partial_and_source_preserved=True, full_verification=False))
            except OSError:
                pass
        raise
    finally:
        release(identity)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', required=True, choices=('plan', 'identities', 'archive'))
    parser.add_argument('--request', type=Path, required=True)
    parser.add_argument('--request-sha256', required=True)
    args = parser.parse_args()
    paths._plain(args.request.absolute())
    require(args.request.stat().st_size <= 1024**2, 'Request exceeds 1MiB')
    raw = args.request.read_bytes()
    require(re.fullmatch('[a-f0-9]{64}', args.request_sha256) and
            hashlib.sha256(raw).hexdigest() == args.request_sha256, 'Explicit request SHA differs')
    result = process(json.loads(raw.decode('utf8')), args.mode)
    result['request_file_sha256'] = args.request_sha256
    print(json.dumps(result, indent=2, sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
