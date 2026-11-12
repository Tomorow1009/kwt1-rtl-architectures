"""Archive pinned R4 L01 through a private, separate /tmp filesystem.

One gzip6 worker, no EDA. The old R4 summary/state and original archive01 stay
untouched. A fully restored/hash-verified and fsynced /tmp archive precedes any
explicitly requested raw removal. Failed return copies retain that complete
archive; --resume-copy never deletes raw data or failed copy attempts.
"""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import uuid

import archive_r4_l01 as frozen

TMP_PARENT = Path('/tmp')
ACCOUNT = 's4_21usr'
OUTPUT_NAME = 'r4_l01_archive02'
SCHEMA = 'arch03-r4-l01-separate-tmp-archive-v1'
require = frozen.require


def account():
    import pwd
    return pwd.getpwuid(frozen._uid()).pw_name


def device(path):
    return Path(path).stat().st_dev


def validate_tmp(path, context, create):
    path = Path(path)
    require(account() == ACCOUNT, 'Wrong production account')
    require(path.is_absolute() and path.parent == TMP_PARENT and
            re.fullmatch(r's4_21usr-r4-l01-[A-Za-z0-9][A-Za-z0-9_.-]{5,96}', path.name),
            'Use a unique /tmp/s4_21usr-r4-l01-... direct directory')
    frozen.checked_path(path, TMP_PARENT, exists=not create)
    if create:
        require(not path.exists(), 'Temporary directory exists; no in-place retry')
        path.mkdir(mode=0o700)
        frozen.sync_directory(TMP_PARENT)
    info = path.stat()
    require(stat.S_ISDIR(info.st_mode) and info.st_uid == frozen._uid() and
            stat.S_IMODE(info.st_mode) == 0o700 and not path.is_symlink(),
            'Temporary directory must be owned, private 0700 and not a symlink')
    require(device(path) != device(context['source'].parent) and
            device(path) != device(context['base'] / 'runs'),
            'Temporary filesystem must differ from source and final storage')
    return path


def output_path(context, output, fresh):
    output = Path(output)
    require(output == context['base'] / 'runs' / OUTPUT_NAME,
            'Final archive must use the new bundle runs/r4_l01_archive02 directory')
    frozen.checked_path(output, context['base'], exists=not fresh)
    if fresh:
        require(not output.exists(), 'Output directory exists; use explicit resume-copy')
        output.mkdir(mode=0o700)
        frozen.sync_directory(output.parent)
    info = output.stat()
    require(stat.S_ISDIR(info.st_mode) and info.st_uid == frozen._uid() and
            stat.S_IMODE(info.st_mode) == 0o700, 'Final directory must be owned/private')
    require(device(output) == device(context['source'].parent),
            'Final archive must return to the original storage filesystem')
    return output


def persist(record):
    """The separate filesystem is authoritative until verified return completes."""
    tmp = Path(record['temporary_directory'])
    frozen.save(tmp / 'receipt.json', record)
    frozen.sync_directory(tmp)
    try:
        output = Path(record['output_directory'])
        frozen.save(output / 'receipt.json', record)
        frozen.sync_directory(output)
    except OSError as error:
        # Storage can be full already. Never lose the only complete receipt by
        # insisting its mirror be written on the exhausted filesystem.
        record['storage_receipt_error'] = str(error)
        frozen.save(tmp / 'receipt.json', record)
        frozen.sync_directory(tmp)


def restore_proof(path, expected):
    before = frozen.stamp(path)
    restored, count = hashlib.sha256(), 0
    with gzip.open(str(path), 'rb') as source:
        for block in iter(lambda: source.read(frozen.CHUNK), b''):
            count += len(block)
            require(count <= expected['bytes'], 'Restoration exceeds pinned raw byte count')
            restored.update(block)
    require(count == expected['bytes'] and restored.hexdigest() == expected['sha256'],
            'Complete decompression SHA/byte proof failed')
    require(frozen.stamp(path) == before, 'Temporary archive changed during restoration')
    return dict(restored_bytes=count, restored_sha256=restored.hexdigest())


def return_budget(output, archive_bytes):
    needed = (archive_bytes * 6 + 4) // 5 + frozen.RESERVE_BYTES
    return dict(free_bytes=shutil.disk_usage(str(output)).free,
                required_bytes=needed, factor='1.2', reserve_bytes=frozen.RESERVE_BYTES)


def allocated_bytes(info):
    require(hasattr(info, 'st_blocks'), 'Actual allocated raw blocks are unavailable')
    return info.st_blocks * 512


def history(context):
    """Can be checked after raw removal; no edits or simulated old PASS."""
    for key in ('summary', 'state'):
        frozen.checked_path(context[key], context['bundles'])
        frozen.owned_file(context[key])
    require(frozen.digest(context['summary']) == frozen.SUMMARY_SHA and
            frozen.digest(context['state']) == context['state_sha256'],
            'Original R4 summary/state changed')


def recovery_context(base, record):
    base = Path(base)
    require(base.is_absolute() and base.resolve() == base and base.is_dir(), 'Invalid bundle')
    bundles = base.parent
    source = frozen.checked_path(bundles / frozen.SOURCE_RELATIVE, bundles, exists=False)
    summary = frozen.owned_file(source.parent / 'summary.json')
    state = frozen.owned_file(source.parent.parent / 'state.json')
    require(frozen.digest(summary) == frozen.SUMMARY_SHA, 'Wrong pinned R4 summary')
    report = json.loads(summary.read_text(encoding='utf8'))
    matches = [row for row in report['cases'] if row['case'] == 'layer_01']
    require(report['status'] == 'passed' and len(matches) == 1, 'Wrong original R4 case')
    expected = matches[0]['activity']
    require(str(source) == record['source'] and expected['bytes'] == record['original_bytes'] and
            expected['sha256'] == record['original_sha256'] and expected['file'] == 'layer_01.vcd',
            'Recovery does not match pinned R4 raw identity')
    stage = json.loads(state.read_text(encoding='utf8'))['stages']['icb32_gate']
    require(stage['status'] == 'passed' and stage['summary_sha256'] == frozen.SUMMARY_SHA,
            'Original R4 stage is not pinned passed')
    context = dict(base=base, bundles=bundles, source=source, summary=summary, state=state,
                   state_sha256=record['state_sha256'], expected=expected)
    history(context)
    return context


def verify_tmp_archive(record):
    path = Path(record['temporary_archive'])
    tmp = Path(record['temporary_directory'])
    require(path == tmp / 'layer_01.vcd.gz' and record.get('complete_tmp_archive_verified') is True,
            'No complete verified temporary archive')
    frozen.checked_path(path, tmp)
    frozen.owned_file(path)
    require(path.stat().st_size == record['archive_bytes'] and
            frozen.digest(path) == record['archive_sha256'], 'Verified temporary gzip changed')
    return path


def copy_back(context, record):
    """Never removes raw. Copy attempts are unique; interrupted copies persist."""
    tmp_archive = verify_tmp_archive(record)
    output = output_path(context, Path(record['output_directory']), fresh=False)
    final = output / 'layer_01.vcd.gz'
    history(context)
    if final.exists():
        frozen.checked_path(final, context['base'])
        frozen.owned_file(final)
        require(final.stat().st_size == record['archive_bytes'] and
                frozen.digest(final) == record['archive_sha256'], 'Existing final gzip is different')
        with final.open('r+b') as stream:
            os.fsync(stream.fileno())
        frozen.sync_directory(output)
    else:
        budget = return_budget(output, record['archive_bytes'])
        record['return_budget'] = budget
        if budget['free_bytes'] < budget['required_bytes']:
            record.update(status='verified_tmp_waiting_for_return_space', finished_utc=frozen.now())
            persist(record)
            return record
        partial = output / ('layer_01.vcd.gz.copy-' + uuid.uuid4().hex + '.partial')
        record.setdefault('copy_attempts', []).append(str(partial))
        record.update(status='return_copy_in_progress_tmp_complete', current_copy=str(partial))
        persist(record)
        before = frozen.stamp(tmp_archive)
        copied, count = hashlib.sha256(), 0
        with tmp_archive.open('rb') as source, partial.open('xb') as destination:
            for block in iter(lambda: source.read(frozen.CHUNK), b''):
                frozen.chunk_guard(output, len(block))
                destination.write(block)
                copied.update(block);count += len(block)
                frozen.chunk_guard(output)
            destination.flush();os.fsync(destination.fileno())
        require(frozen.stamp(tmp_archive) == before and count == record['archive_bytes'] and
                copied.hexdigest() == record['archive_sha256'], 'Return copy stream differs')
        frozen.owned_file(partial)
        copied_stamp = frozen.stamp(partial)
        require(partial.stat().st_size == count and frozen.digest(partial) == record['archive_sha256'],
                'Complete stored return copy SHA differs')
        require(frozen.stamp(partial) == copied_stamp, 'Return copy changed during hash proof')
        history(context);frozen.unused([partial, tmp_archive])
        require(frozen.stamp(partial) == copied_stamp and frozen.stamp(tmp_archive) == before,
                'Verified return copy or temporary gzip changed')
        os.link(str(partial), str(final))
        frozen.sync_directory(output)
        partial.unlink()  # Same-inode duplicate, after final hardlink is durable.
        frozen.sync_directory(output)
    # The final inode is on storage2, fully copied, hashed and fsynced. Only now
    # is removal of the *temporary* complete archive allowed.
    record.update(status='returned_archive_verified_tmp_retained', final_archive=str(final),
                  final_archive_sha256=frozen.digest(final), final_archive_bytes=final.stat().st_size,
                  final_return_verified=True)
    require(record['final_archive_sha256'] == record['archive_sha256'], 'Final archive changed')
    persist(record)
    history(context)
    frozen.unused([tmp_archive, final])
    verify_tmp_archive(record)
    frozen.owned_file(final)
    require(frozen.digest(final) == record['archive_sha256'], 'Final archive changed before tmp cleanup')
    tmp_archive.unlink()
    frozen.sync_directory(tmp_archive.parent)
    record.update(status='completed_returned_archive', temporary_archive_removed=True,
                  finished_utc=frozen.now(), final_free_bytes=shutil.disk_usage(str(output)).free)
    persist(record)
    return record


def archive(context, output, temporary, remove=False):
    source, expected = context['source'], context['expected']
    frozen.recheck(context);frozen.unused([source])
    # Validate output before allocating any scratch directory.
    require(Path(output) == context['base'] / 'runs' / OUTPUT_NAME and not Path(output).exists(),
            'Use new runs/r4_l01_archive02; existing outputs are never overwritten')
    tmp = validate_tmp(temporary, context, create=True)
    output = output_path(context, output, fresh=True)
    partial, complete = tmp / 'layer_01.vcd.gz.partial', tmp / 'layer_01.vcd.gz'
    record = dict(schema=SCHEMA, status='checking_original_retained', source=str(source),
        output_directory=str(output), temporary_directory=str(tmp), temporary_archive=str(complete),
        temporary_partial=str(partial), recovery_command='python3 -B archive_r4_l01_staged.py --temporary-directory '+str(tmp)+' --resume-copy',
        original_bytes=expected['bytes'], original_sha256=expected['sha256'],
        summary_sha256=frozen.SUMMARY_SHA, state_sha256=context['state_sha256'],
        source_stamp=list(context['source_stamp']), compression='gzip', level=frozen.LEVEL,
        workers=1, pid=os.getpid(), started_utc=frozen.now(), original_removed=False,
        complete_tmp_archive_verified=False, final_return_verified=False, temporary_archive_removed=False,
        remove_verified_raw_requested=bool(remove), historical_summary_state_modified=False,
        non_EDA_maintenance=True, current_bundle=str(context['base']),
        temporary_device=device(tmp), storage_device=device(output))
    persist(record)
    try:
        required = (expected['bytes'] * 6 + 4) // 5 + frozen.RESERVE_BYTES
        free = shutil.disk_usage(str(tmp)).free
        record.update(tmp_budget=dict(free_bytes=free, required_bytes=required,
                      basis='1.2 times complete uncompressed size plus 2GiB; no optimistic compression estimate'))
        persist(record)
        require(free >= required, 'Insufficient separate temporary filesystem budget')
        frozen.recheck(context)
        record['status'] = 'compressing_to_separate_tmp_original_retained';persist(record)
        streamed, count = hashlib.sha256(), 0
        with source.open('rb') as original, partial.open('xb') as destination:
            require(frozen.stamp(source) == context['source_stamp'], 'Original changed before compression')
            with gzip.GzipFile(filename=source.name, fileobj=destination, mode='wb',
                               compresslevel=frozen.LEVEL, mtime=0) as packed:
                for block in iter(lambda: original.read(frozen.CHUNK), b''):
                    frozen.chunk_guard(tmp, len(block))
                    packed.write(block);streamed.update(block);count += len(block)
                    frozen.chunk_guard(tmp)
            destination.flush();os.fsync(destination.fileno())
        require(count == expected['bytes'] and streamed.hexdigest() == expected['sha256'],
                'Complete source stream SHA/bytes differ from frozen R4')
        frozen.recheck(context)
        proof = restore_proof(partial, expected)
        sha = frozen.digest(partial)
        frozen.recheck(context);frozen.unused([source, partial])
        os.link(str(partial), str(complete));frozen.sync_directory(tmp)
        partial.unlink();frozen.sync_directory(tmp)
        record.update(proof)
        record.update(status='complete_tmp_verified_original_retained', complete_tmp_archive_verified=True,
                      streamed_source_sha256=streamed.hexdigest(), streamed_source_bytes=count,
                      archive_sha256=sha, archive_bytes=complete.stat().st_size,
                      complete_tmp_archive_stamp=list(frozen.stamp(complete)))
        persist(record)
        if remove:
            frozen.recheck(context);verify_tmp_archive(record)
            frozen.unused([source, complete]);frozen.recheck(context)
            info = source.stat()
            require(info.st_nlink == 1, 'Raw has other hardlinks; reclaim cannot be assumed')
            reclaim = allocated_bytes(info)
            budget = return_budget(output, record['archive_bytes'])
            budget['raw_allocated_bytes_reclaimable'] = reclaim
            budget['free_plus_raw_reclaim'] = budget['free_bytes'] + reclaim
            record['before_raw_removal_budget'] = budget
            if budget['free_plus_raw_reclaim'] < budget['required_bytes']:
                record.update(status='verified_tmp_and_raw_retained_insufficient_return_budget', finished_utc=frozen.now())
                persist(record)
                return record
            record.update(status='verified_tmp_raw_removal_intent', raw_removal_intent_utc=frozen.now())
            persist(record)
            frozen.recheck(context)
            require(source.stat().st_nlink == 1, 'Raw hardlink count changed before removal')
            source.unlink()
            record.update(original_removed=True, restore_required_for_original_path=True,
                          raw_allocated_bytes_released=reclaim, status='raw_removed_tmp_complete')
            frozen.sync_directory(source.parent)
            persist(record)
        return copy_back(context, record)
    except BaseException as error:
        record.update(status='failed_tmp_preservation_review_required', error=str(error),
                      source_exists=source.exists(), temporary_complete_exists=complete.exists(),
                      temporary_partial_exists=partial.exists(), finished_utc=frozen.now())
        persist(record)
        raise


def resume_copy(base, temporary):
    # Validate path before opening even its receipt. Device/ownership checks are
    # repeated below with the pinned historical context.
    tmp = Path(temporary)
    require(tmp.parent == TMP_PARENT and re.fullmatch(r's4_21usr-r4-l01-[A-Za-z0-9][A-Za-z0-9_.-]{5,96}', tmp.name),
            'Invalid recovery directory')
    frozen.checked_path(tmp, TMP_PARENT)
    info = tmp.stat()
    require(account() == ACCOUNT and info.st_uid == frozen._uid() and
            stat.S_ISDIR(info.st_mode) and stat.S_IMODE(info.st_mode) == 0o700,
            'Recovery directory must be owned and private 0700')
    frozen.owned_file(tmp / 'receipt.json')
    record = json.loads((tmp / 'receipt.json').read_text(encoding='utf8'))
    require(record['schema'] == SCHEMA and record['current_bundle'] == str(base) and
            record['temporary_directory'] == str(tmp), 'Recovery receipt belongs to another run')
    context = recovery_context(base, record)
    validate_tmp(tmp, context, create=False)
    output = output_path(context, Path(record['output_directory']), fresh=False)
    record['source_present_at_resume'] = context['source'].exists()
    if not record['source_present_at_resume']:
        require(record.get('complete_tmp_archive_verified') is True and
                record.get('remove_verified_raw_requested') is True and record.get('raw_removal_intent_utc'),
                'Original absent without this run durable verified-removal intent')
        if not record.get('original_removed'):
            record.update(original_removed=True, restore_required_for_original_path=True,
                          source_absence_reconciled_after_durable_removal_intent=True)
    try:
        # A crash may occur after fsynced final publication and tmp unlink but
        # before the last receipt write. Require the already-recorded final
        # proof and independently hash that stored inode; never delete raw.
        if not Path(record['temporary_archive']).exists():
            final = output / 'layer_01.vcd.gz'
            require(record.get('final_return_verified') is True, 'Temporary complete archive is missing')
            frozen.checked_path(final, context['base']);frozen.owned_file(final)
            require(final.stat().st_size == record['archive_bytes'] and
                    frozen.digest(final) == record['archive_sha256'], 'Published final archive is missing/changed')
            with final.open('r+b') as stream:os.fsync(stream.fileno())
            frozen.sync_directory(output);history(context)
            record.update(status='completed_returned_archive', temporary_archive_removed=True,
                          completed_receipt_reconciled=True, finished_utc=frozen.now(),
                          resume_copy_requested=True, pid=os.getpid())
            persist(record)
            return record
        verify_tmp_archive(record)
        restore_proof(Path(record['temporary_archive']), context['expected'])
        record.update(resume_copy_requested=True, resume_utc=frozen.now(), pid=os.getpid())
        persist(record)
        return copy_back(context, record)
    except BaseException as error:
        record.update(status='failed_resume_tmp_preserved', error=str(error), finished_utc=frozen.now())
        persist(record)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--temporary-directory', required=True, type=Path)
    parser.add_argument('--output', type=Path, default=Path('runs') / OUTPUT_NAME)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument('--remove-verified-raw', action='store_true')
    modes.add_argument('--resume-copy', action='store_true')
    args = parser.parse_args()
    require(os.name == 'posix', 'Linux ownership, fsync, fuser, nice and ionice required')
    base = Path.cwd()
    os.nice(19)
    subprocess.check_call(['/bin/ionice', '-c', '3', '-p', str(os.getpid())])
    if args.resume_copy:
        result = resume_copy(base, args.temporary_directory)
    else:
        output = args.output if args.output.is_absolute() else base / args.output
        result = archive(frozen.frozen_context(base), output, args.temporary_directory, args.remove_verified_raw)
    print('R4_L01_STAGED_ARCHIVE', result['status'], 'tmp='+str(args.temporary_directory), flush=True)
    return 0 if result['status'] == 'completed_returned_archive' else 3


if __name__ == '__main__':
    sys.exit(main())
