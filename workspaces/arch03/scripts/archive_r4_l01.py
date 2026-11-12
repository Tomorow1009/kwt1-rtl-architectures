"""Losslessly archive ONLY the pinned R4 L01 waveform, one low-priority worker.

No EDA is run and historical summary/state files are never edited.  The CLI
accepts no source override.  A 64 MiB prefix compressed in memory is only a
space estimate; removal requires the full source and full restored hashes.
Failed attempts retain the raw source and any .partial archive for review.
"""
import argparse
import datetime
import gzip
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess

R4 = 'light-light126-icb32-r4-20261111_011258-49759e108719'
SUMMARY_SHA = '95113a35bf2941e985d8d1b8cbad7d88c0d56f07d3c1f533f0fcf549fb2efc7f'
SOURCE_RELATIVE = Path(R4)/'runs/icb32_r4_gate01/icb32_gate/layer_01.vcd'
CHUNK = 8*1024**2
SAMPLE_BYTES = 64*1024**2
RESERVE_BYTES = 2*1024**3
LEVEL = 6


def now():
    return datetime.datetime.utcnow().isoformat()+'Z'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def _uid():
    return os.getuid()


def digest(path):
    value = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(CHUNK), b''):
            value.update(block)
    return value.hexdigest()


def stamp(path):
    value = Path(path).stat()
    return (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns,
            value.st_ctime_ns, value.st_uid, value.st_mode)


def owned_file(path):
    path = Path(path)
    require(not path.is_symlink(), 'Symlink file refused: '+str(path))
    value = path.stat()
    require(stat.S_ISREG(value.st_mode) and value.st_uid == _uid(),
            'Expected an owned regular file: '+str(path))
    return path


def checked_path(path, root, exists=True):
    """Reject lexical escapes and every symlink below the fixed parent."""
    path, root = Path(path), Path(root)
    require(root.is_absolute() and root.resolve() == root and not root.is_symlink(), 'Unsafe path root')
    relative = path.relative_to(root)
    require('..' not in relative.parts, 'Parent traversal refused')
    cursor = root
    for part in relative.parts:
        cursor = cursor/part
        require(not cursor.is_symlink(), 'Symlink path component refused: '+str(cursor))
    require(path.resolve(strict=exists) == path, 'Resolved path differs from fixed path')
    return path


def save(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix+'.tmp')
    with temporary.open('w', encoding='utf8') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n');stream.flush();os.fsync(stream.fileno())
    os.replace(str(temporary), str(path))


def sync_directory(path):
    if os.name == 'posix':
        descriptor = os.open(str(path), os.O_RDONLY | getattr(os, 'O_DIRECTORY', 0))
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)


def unused(paths):
    result = subprocess.run(['fuser', '--']+[str(path) for path in paths],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    require(result.returncode == 1, 'File in use or fuser check failed')


def frozen_context(base):
    base = Path(base)
    require(base.is_absolute() and base.resolve() == base and base.is_dir(), 'Invalid current bundle')
    bundles = base.parent
    source = checked_path(bundles/SOURCE_RELATIVE, bundles)
    summary = owned_file(checked_path(source.parent/'summary.json', bundles))
    state = owned_file(checked_path(source.parent.parent/'state.json', bundles))
    require(digest(summary) == SUMMARY_SHA, 'Wrong pinned R4 gate summary')
    report = json.loads(summary.read_text(encoding='utf8'))
    require(report.get('status') == 'passed', 'Original R4 gate summary is not passed')
    stage = json.loads(state.read_text(encoding='utf8'))['stages']['icb32_gate']
    require(stage['status'] == 'passed' and stage['summary_sha256'] == SUMMARY_SHA,
            'R4 stage is not the pinned pass')
    matches = [row for row in report['cases'] if row['case'] == 'layer_01']
    require(len(matches) == 1, 'Missing/duplicate pinned R4 L01 case')
    expected = matches[0]['activity']
    require(expected['file'] == 'layer_01.vcd' and type(expected['bytes']) is int and expected['bytes'] > 0 and
            re.fullmatch('[0-9a-f]{64}', expected['sha256']), 'Invalid frozen L01 activity identity')
    owned_file(source)
    require(source.stat().st_size == expected['bytes'], 'L01 source byte count changed')
    return dict(base=base, bundles=bundles, source=source, summary=summary, state=state,
                summary_stamp=stamp(summary), state_stamp=stamp(state),
                state_sha256=digest(state), expected=dict(expected), source_stamp=stamp(source))


def recheck(context):
    source = context['source']
    require(source == context['bundles']/SOURCE_RELATIVE, 'Source is not the exact pinned R4 L01 path')
    for key in ('source', 'summary', 'state'):
        checked_path(context[key], context['bundles'])
        owned_file(context[key])
        require(stamp(context[key]) == context[key+'_stamp'], 'Frozen '+key+' changed')
    require(digest(context['summary']) == SUMMARY_SHA and digest(context['state']) == context['state_sha256'],
            'Original summary/state content changed')


def memory_estimate(source, expected_bytes):
    before = stamp(source)
    with Path(source).open('rb') as stream:
        sample = stream.read(SAMPLE_BYTES)
    require(sample and len(sample) == min(SAMPLE_BYTES, expected_bytes) and stamp(source) == before,
            'Source changed during sample read')
    output = io.BytesIO()
    with gzip.GzipFile(filename=Path(source).name, fileobj=output, mode='wb', compresslevel=LEVEL, mtime=0) as packed:
        packed.write(sample)
    packed_bytes = len(output.getvalue())
    estimate = math.ceil(expected_bytes*packed_bytes/len(sample))
    return dict(sample_bytes=len(sample), sample_compressed_bytes=packed_bytes,
                sample_sha256=hashlib.sha256(sample).hexdigest(), sample_mode='first_64MiB_only',
                estimated_archive_bytes=estimate, required_free_bytes=math.ceil(estimate*1.2)+RESERVE_BYTES,
                headroom_factor=1.2, reserve_bytes=RESERVE_BYTES,
                scope='budget_estimate_only_not_lossless_or_final_size_proof')


def chunk_guard(directory, incoming=0):
    free = shutil.disk_usage(str(directory)).free
    # Reserve the entire next uncompressed chunk plus worst-case deflate/header
    # overhead, so this process itself cannot consume the 2 GiB reserve.
    allowance = incoming + incoming//1000 + 65536 if incoming else 0
    require(free >= RESERVE_BYTES+allowance, '2 GiB reserve reached; raw and partial archive retained')
    return free


def archive(context, output, remove=False):
    """Caller supplies only a fresh direct child of this bundle's runs directory."""
    source, expected = context['source'], context['expected']
    output = Path(output)
    require(output.parent == context['base']/'runs', 'Archive output must be a direct child of current runs')
    checked_path(output.parent, context['base'])
    checked_path(output, context['base'], exists=False)
    require(not output.exists(), 'Archive run exists; no retries or overwrites in place')
    recheck(context)
    unused([source])
    output.mkdir(mode=0o700)
    partial, final = output/'layer_01.vcd.gz.partial', output/'layer_01.vcd.gz'
    receipt = output/'receipt.json'
    record = dict(schema='arch03-r4-l01-lossless-archive-v1', status='checking_original_retained',
        source=str(source), archive=str(final), partial_archive=str(partial),
        original_bytes=expected['bytes'], original_sha256=expected['sha256'],
        summary_sha256=SUMMARY_SHA, state_sha256=context['state_sha256'],
        source_stamp=list(context['source_stamp']), compression='gzip', level=LEVEL,
        workers=1, pid=os.getpid(), started_utc=now(), original_removed=False,
        restore_required_for_original_path=False, remove_verified_raw_requested=bool(remove),
        historical_summary_state_modified=False, non_EDA_maintenance=True)
    save(receipt, record)
    try:
        estimate = memory_estimate(source, expected['bytes'])
        free = shutil.disk_usage(str(output)).free
        record.update(budget=estimate, preflight_free_bytes=free)
        save(receipt, record)
        require(free >= estimate['required_free_bytes'], 'Insufficient space for 1.2x estimate plus 2 GiB reserve')
        recheck(context)
        actual_source_sha = digest(source)
        require(actual_source_sha == expected['sha256'], 'Actual source SHA differs from frozen R4 L01')
        recheck(context);unused([source])
        record.update(status='compressing_original_retained', source_sha256_verified=actual_source_sha)
        save(receipt, record)
        streamed_sha, streamed_bytes = hashlib.sha256(), 0
        with source.open('rb') as src, partial.open('xb') as out:
            require(stamp(source) == context['source_stamp'], 'Source changed before compression')
            with gzip.GzipFile(filename=source.name, fileobj=out, mode='wb', compresslevel=LEVEL, mtime=0) as packed:
                for block in iter(lambda: src.read(CHUNK), b''):
                    chunk_guard(output, len(block))
                    streamed_sha.update(block);streamed_bytes += len(block);packed.write(block)
                    chunk_guard(output)
            out.flush();os.fsync(out.fileno())
        require(streamed_sha.hexdigest() == expected['sha256'] and streamed_bytes == expected['bytes'],
                'Streamed original hash/length differs')
        recheck(context)
        owned_file(partial)
        compressed_stamp = stamp(partial)
        restored_sha, restored_bytes = hashlib.sha256(), 0
        with gzip.open(str(partial), 'rb') as stream:
            for block in iter(lambda: stream.read(CHUNK), b''):
                chunk_guard(output)
                restored_sha.update(block);restored_bytes += len(block)
        require(restored_sha.hexdigest() == expected['sha256'] and restored_bytes == expected['bytes'],
                'Complete decompression hash/length proof failed')
        archive_sha = digest(partial)
        require(stamp(partial) == compressed_stamp, 'Archive changed during restoration proof')
        recheck(context);unused([source, partial])
        # Hard-link publication is atomic and fails if final already exists.
        # It never overwrites another artifact and uses no second data copy.
        os.link(str(partial), str(final))
        partial.unlink();sync_directory(output)
        final_stamp = stamp(final)
        record.update(status='lossless_verified_original_retained',
            archive_bytes=final.stat().st_size, archive_sha256=archive_sha,
            streamed_source_sha256=streamed_sha.hexdigest(), streamed_source_bytes=streamed_bytes,
            restored_sha256=restored_sha.hexdigest(), restored_bytes=restored_bytes,
            restoration_scope='complete gzip stream in memory chunks; no temporary restored disk file',
            archive_stamp=list(final_stamp))
        save(receipt, record);sync_directory(output)
        if remove:
            recheck(context)
            checked_path(final, context['base']);owned_file(final)
            require(stamp(final) == final_stamp, 'Verified archive changed before raw removal')
            unused([source, final])
            recheck(context)
            require(stamp(final) == final_stamp, 'Verified archive changed after fuser check')
            source.unlink()
            record.update(status='lossless_archived_raw_removed', original_removed=True,
                          restore_required_for_original_path=True,
                          bytes_reclaimed_from_duplicate_raw=expected['bytes'])
            sync_directory(source.parent)
        record.update(finished_utc=now(), final_free_bytes=shutil.disk_usage(str(output)).free)
        save(receipt, record);sync_directory(output)
        return record
    except BaseException as error:
        record.update(status='failed_review_required', error=str(error),
                      source_exists=source.exists(), partial_exists=partial.exists(),
                      archive_exists=final.exists(), finished_utc=now())
        save(receipt, record)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--remove-verified-raw', action='store_true')
    args = parser.parse_args()
    require(os.name == 'posix', 'Production archival requires Linux ownership, fuser, nice and ionice')
    base = Path.cwd()
    context = frozen_context(base)
    output = args.output if args.output.is_absolute() else base/args.output
    require(output.parent == base/'runs', 'Use one new direct child of this bundle runs directory')
    os.nice(19)
    subprocess.check_call(['/bin/ionice', '-c', '3', '-p', str(os.getpid())])
    result = archive(context, output, args.remove_verified_raw)
    print('R4_L01_LOSSLESS_ARCHIVE', result['status'], 'source='+str(context['source']), flush=True)


if __name__ == '__main__':
    main()
