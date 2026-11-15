"""Archive completed R4 contention compiler cache then launch corrected S0 mapping.

The fixed R4 run is completed. T80, old-eight-lane and source inputs are excluded.
Symlinks and directories stay in place. Archive is verified before any unlink.
"""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import tarfile


def digest(stream):
    h = hashlib.sha256()
    for block in iter(lambda: stream.read(1024*1024), b''):
        h.update(block)
    return h.hexdigest()


def sha(p):
    with p.open('rb') as f:
        return digest(f)


def idle(lock):
    assert not lock.exists(), 'Existing team lock'
    rows = subprocess.check_output(['ps', '-u', 's4_21usr', '-o', 'comm=']).decode().splitlines()
    assert not any(x.strip() in ('dc_shell', 'pt_shell', 'simv', 'vcs', 'vcs1', 'vcs2') for x in rows)


def main():
    root = Path('/storage2/2026contest/server4/s4_21usr/Desktop/IC')
    run = root/'light-light126-undergrad-d2-20261109/bundles/light-light126-icb32-r4-20261111_011258-49759e108719/runs/icb32_r4_contention01'
    cache = run/'icb32_contention/csrc'
    ops = Path('/tmp/s4_21usr_t80_20261115_1830/ops-0bf4af3')
    lock = root/'.arch02_team_lock'
    cap = ops.parent/'light-light126-t80-s0-c6aa1e2/runs/s0_cap04'
    capstate = json.loads((cap/'state.json').read_text())['stages']['t80_capability']
    assert capstate['status'] == 'passed'
    assert sha(cap/'t80_s0_capability/summary.json') == capstate['summary_sha256']
    assert not (ops.parent/'light-light126-t80-s0-0bf4af3/runs/s0_synth02').exists()
    idle(lock)
    assert cache.resolve() == cache and cache.stat().st_uid == os.getuid()
    stage = json.loads((run/'state.json').read_text())['stages']['icb32_contention']
    # State and its actual summary, plus immutability checks below, pin this run.
    assert stage['status'] == 'passed'
    assert sha(cache.parent/'summary.json') == stage['summary_sha256']
    frozen = {str(p): sha(p) for p in (run/'state.json', cache.parent/'summary.json')}
    rows = {}
    for p in cache.rglob('*'):
        if p.is_symlink() or not p.is_file():
            continue
        assert p.resolve() == p and p.stat().st_uid == os.getuid()
        name = p.relative_to(cache).as_posix()
        assert '..' not in Path(name).parts
        rows[name] = dict(bytes=p.stat().st_size, sha256=sha(p), inode=p.stat().st_ino)
    assert rows and sum(x['bytes'] for x in rows.values()) < 100*1024**2
    archive = ops/'r4_contention_csrc_regular_files.tar.gz'
    receipt = ops/'r4_contention_csrc_archive_receipt.json'
    assert not archive.exists() and not receipt.exists()
    with tarfile.open(str(archive), 'x:gz', compresslevel=6) as f:
        for name in sorted(rows):
            f.add(str(cache/name), arcname=name, recursive=False)
    with archive.open('rb') as f:
        os.fsync(f.fileno())
    seen = set()
    with tarfile.open(str(archive), 'r:gz') as f:
        for member in f:
            assert member.isfile() and member.name in rows and member.name not in seen
            row = rows[member.name]
            assert member.size == row['bytes']
            with f.extractfile(member) as content:
                assert digest(content) == row['sha256']
            seen.add(member.name)
    assert seen == set(rows)
    archive_hash = sha(archive)
    data = dict(source=str(cache), regular_files=rows, archive=str(archive),
                archive_sha256=archive_hash, archive_bytes=archive.stat().st_size,
                all_archive_members_verified=True, original_state=frozen,
                symlinks_untouched=True, results_untouched=True, removed=[])
    with receipt.open('x') as f:
        json.dump(data, f, indent=2)
        f.flush(); os.fsync(f.fileno())
    idle(lock)
    for name, row in rows.items():
        p = cache/name
        assert p.resolve() == p and p.stat().st_ino == row['inode'] and sha(p) == row['sha256']
    for path, expected_hash in frozen.items():
        assert sha(Path(path)) == expected_hash
    for name in sorted(rows):
        assert not lock.exists()
        p = cache/name
        assert p.resolve() == p and p.stat().st_ino == rows[name]['inode']
        p.unlink()
        data['removed'].append(name)
        receipt.write_text(json.dumps(data, indent=2)+'\n')
    final_archive = cache.parent/'csrc_regular_files_20261115.tar.gz'
    assert not final_archive.exists()
    if shutil.disk_usage(str(root)).free > archive.stat().st_size + 2*1024**2:
        with archive.open('rb') as src, final_archive.open('xb') as dest:
            shutil.copyfileobj(src, dest)
            dest.flush(); os.fsync(dest.fileno())
        assert sha(final_archive) == archive_hash
        data['persistent_archive'] = str(final_archive)
    for path, expected_hash in frozen.items():
        assert sha(Path(path)) == expected_hash
    data['free_bytes'] = shutil.disk_usage(str(root)).free
    receipt.write_text(json.dumps(data, indent=2)+'\n')
    print('S0_R4_CACHE_ARCHIVED', len(rows), 'BYTES', sum(x['bytes'] for x in rows.values()),
          'ARCHIVE', archive_hash, 'PERSISTENT', data.get('persistent_archive'),
          'FREE', data['free_bytes'], flush=True)

    bundle = ops.parent/'light-light126-t80-s0-0bf4af3'
    origin = root/'light-light126-undergrad-d2-20261109/bundles/light-light126-t80-v4-9196556-delta03/runs/t80_finish02_synth/t80_synth'
    with (ops/'s0_synth02.log').open('x') as log:
        child = subprocess.Popen(['python3', '-B', str(bundle/'workspaces/arch03/scripts/s0_server.py'),
            'synth', '--session', 's0_synth02', '--origin', str(origin), '--runtime-root', str(ops.parent),
            '--runtime-manifest-sha256', '93be0a4c5e6e16ebe575d73fa7249e2002c0e1a0db41c371f47302236a2d7475'],
            cwd=str(ops), stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    with (ops/'s0_synth02_launcher.json').open('x') as f:
        json.dump(dict(pid=child.pid, launcher_sha256=sha(Path(__file__)), prior_archive=sha(receipt)), f)
    print('S0_SYNTH02_PID', child.pid, flush=True)


if __name__ == '__main__':
    main()
