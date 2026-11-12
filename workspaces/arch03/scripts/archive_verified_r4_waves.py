"""Preserve R4 L03-L12 losslessly while reclaiming duplicate raw storage.

Storage maintenance only: two low-priority workers, no EDA or input edits.
Every raw removal follows source and decompressed SHA checks and a persisted
receipt. Failed copies retain the original. L01 and the separate L02 pilot
are explicitly excluded. Restore the gzip to its recorded source path and
check original_sha256 before another raw-wave-dependent historical audit.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import datetime
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

R4 = 'light-light126-icb32-r4-20261111_011258-49759e108719'
SUMMARY_SHA = '95113a35bf2941e985d8d1b8cbad7d88c0d56f07d3c1f533f0fcf549fb2efc7f'
CHUNK = 8 * 1024**2


def digest(path):
    value = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(CHUNK), b''):
            value.update(block)
    return value.hexdigest()


def save(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + '.tmp')
    with temporary.open('w') as stream:
        json.dump(value, stream, indent=2)
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


def stamp(path):
    st = path.stat()
    return st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns


def unused(paths):
    code = subprocess.call(['fuser'] + [str(p) for p in paths],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if code != 1:
        raise ValueError('File in use or fuser check failed')


def archive_one(source, expected, destination, remove, guard=True):
    source, destination = Path(source), Path(destination)
    if source.is_symlink() or not source.is_file() or source.stat().st_uid != os.getuid():
        raise ValueError('Source must be an owned regular file')
    if source.stat().st_size != expected['bytes'] or source.name != expected['file']:
        raise ValueError('Source identity/size differs')
    before = stamp(source)
    unused([source])
    if guard and shutil.disk_usage(str(destination.parent)).free < 32 * 1024**3:
        raise ValueError('Insufficient shared space for two conservative copy workers')
    receipt = destination.with_suffix('.json')
    if destination.exists() or receipt.exists():
        raise ValueError('Preserve existing archive/receipt; no retry in place')
    record = dict(status='compressing_original_retained', source=str(source),
                  archive=str(destination), original_bytes=expected['bytes'],
                  original_sha256=expected['sha256'], started=datetime.datetime.now().isoformat(),
                  original_removed=False, restore_required_for_original_path=False)
    save(receipt, record)
    try:
        raw_sha = hashlib.sha256()
        with source.open('rb') as src, destination.open('xb') as out:
            with gzip.GzipFile(filename=source.name, fileobj=out, mode='wb',
                               compresslevel=1, mtime=0) as packed:
                for block in iter(lambda: src.read(CHUNK), b''):
                    if guard and shutil.disk_usage(str(destination.parent)).free < 2 * 1024**3:
                        raise ValueError('Shared disk reserve reached; original retained')
                    raw_sha.update(block)
                    packed.write(block)
            out.flush()
            os.fsync(out.fileno())
        if raw_sha.hexdigest() != expected['sha256'] or stamp(source) != before:
            raise ValueError('Source differs from frozen R4 activity')
        restored_sha, restored_bytes = hashlib.sha256(), 0
        with gzip.open(str(destination), 'rb') as stream:
            for block in iter(lambda: stream.read(CHUNK), b''):
                restored_sha.update(block)
                restored_bytes += len(block)
        if restored_sha.hexdigest() != expected['sha256'] or restored_bytes != expected['bytes']:
            raise ValueError('Lossless restoration proof failed')
        record.update(status='lossless_verified_original_retained',
                      archive_bytes=destination.stat().st_size,
                      archive_sha256=digest(destination),
                      restored_sha256=restored_sha.hexdigest(), restored_bytes=restored_bytes)
        save(receipt, record)
        if remove:
            unused([source, destination])
            if stamp(source) != before or source.is_symlink():
                raise ValueError('Source changed before duplicate removal')
            source.unlink()
            record.update(status='lossless_archived_raw_removed', original_removed=True,
                          restore_required_for_original_path=True)
        record['finished'] = datetime.datetime.now().isoformat()
        save(receipt, record)
        return record
    except BaseException as error:
        record.update(status='failed_review_required', error=str(error),
                      source_exists=source.exists(), finished=datetime.datetime.now().isoformat())
        save(receipt, record)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--remove-verified-raw', action='store_true')
    args = parser.parse_args()
    base = Path.cwd().resolve()
    bundles = base.parent
    origin = (bundles / R4 / 'runs/icb32_r4_gate01/icb32_gate').resolve()
    origin.relative_to(bundles)
    summary = origin / 'summary.json'
    if digest(summary) != SUMMARY_SHA:
        raise ValueError('Wrong frozen R4 gate summary')
    state = json.loads((origin.parent / 'state.json').read_text())['stages']['icb32_gate']
    if state['status'] != 'passed' or state['summary_sha256'] != SUMMARY_SHA:
        raise ValueError('R4 gate stage is not the pinned pass')
    rows = {row['case']: row for row in json.loads(summary.read_text())['cases']}
    output = args.output.resolve()
    output.relative_to(base / 'runs')
    output.mkdir(exist_ok=False)
    os.nice(19)
    subprocess.check_call(['/bin/ionice', '-c', '3', '-p', str(os.getpid())])
    run = dict(status='running', pid=os.getpid(), workers=2, summary_sha256=SUMMARY_SHA,
               started=datetime.datetime.now().isoformat(), completed=[], errors=[],
               remove_verified_raw=args.remove_verified_raw, L01_L02_untouched=True)
    save(output / 'state.json', run)
    with ThreadPoolExecutor(max_workers=2) as pool:
        pending = {}
        for number in range(3, 13):
            name = 'layer_%02d' % number
            source = origin / (name + '.vcd')
            if source.resolve().parent != origin or rows[name]['activity']['file'] != source.name:
                raise ValueError('R4 source escaped the exact directory')
            future = pool.submit(archive_one, source, rows[name]['activity'],
                                 output / (name + '.vcd.gz'), args.remove_verified_raw)
            pending[future] = name
        for future in as_completed(pending):
            name = pending[future]
            try:
                result = future.result()
                run['completed'].append(dict(case=name, receipt=name+'.vcd.json',
                    bytes_saved=result['original_bytes']-result['archive_bytes']
                    if result['original_removed'] else 0))
            except Exception as error:
                run['errors'].append(dict(case=name, error=str(error)))
            save(output / 'state.json', run)
    run.update(status='passed' if not run['errors'] else 'failed_review_required',
               finished=datetime.datetime.now().isoformat())
    save(output / 'state.json', run)
    print('R4_LOSSLESS_ARCHIVE', run['status'], len(run['completed']), flush=True)


if __name__ == '__main__':
    main()
