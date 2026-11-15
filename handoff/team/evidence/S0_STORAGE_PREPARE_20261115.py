"""Preserve paths/bytes of two unused T64 input packages; reclaim duplicates.

No T80, eight-lane, runs or results are candidates. Audit lives in new /tmp ops.
"""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    root = Path('/storage2/2026contest/server4/s4_21usr/Desktop/IC')
    bundles = root/'light-light126-undergrad-d2-20261109/bundles'
    old = bundles/'light-light126-t64-v4-65d2507-delta01'
    keep = bundles/'light-light126-t64-v4-65d2507-fix02'
    ops = Path('/tmp/s4_21usr_t80_20261115_1830/ops-c6aa1e2')
    lock = root/'.arch02_team_lock'
    assert not lock.exists()
    own = subprocess.check_output(['ps', '-u', 's4_21usr', '-o', 'comm=']).decode().splitlines()
    assert not any(x.strip() in ('dc_shell', 'pt_shell', 'simv', 'vcs', 'vcs1', 'vcs2') for x in own)
    assert sha(keep/'manifest.json') == '6632a4f266d48f50fd8a9e542cb6e03f05653d7ade3153903b38c3282c3339c1'
    for folder in (old, keep):
        assert folder.resolve() == folder and not (folder/'runs').exists()
        assert folder.stat().st_uid == os.getuid()
    a = json.loads((old/'manifest.json').read_text())['files']
    b = json.loads((keep/'manifest.json').read_text())['files']
    before = {str(p): sha(p) for p in (old/'manifest.json', keep/'manifest.json')}
    rows = []
    for name, value in sorted(a.items()):
        p, q = old/name, keep/name
        p.relative_to(old); q.relative_to(keep)
        assert p.resolve() == p and q.resolve() == q
        assert p.stat().st_uid == q.stat().st_uid == os.getuid()
        assert value == b[name] and sha(p) == sha(q) == value
        if p.stat().st_ino == q.stat().st_ino or p.stat().st_size < 4096:
            continue
        rows.append(dict(path=str(p), retained_source=str(q), sha256=value,
                         bytes=p.stat().st_size, prior_blocks_bytes=p.stat().st_blocks*512))
    with (ops/'s0_t64_dedup_prepared.json').open('x') as f:
        json.dump(dict(manifests=before, rows=rows), f, indent=2)
    done = []
    for row in sorted(rows, key=lambda v: v['bytes'], reverse=True):
        if shutil.disk_usage(str(root)).free >= 8*1024**2:
            break
        p, q = Path(row['path']), Path(row['retained_source'])
        tmp = old/'.s0-identical-input-link'
        assert not lock.exists() and not tmp.exists()
        assert sha(p) == sha(q) == row['sha256']
        os.link(str(q), str(tmp))
        os.replace(str(tmp), str(p))
        assert sha(p) == row['sha256'] and p.stat().st_size == row['bytes']
        assert p.stat().st_ino == q.stat().st_ino
        done.append(row)
    for path, expected in before.items():
        assert sha(Path(path)) == expected
    with (ops/'s0_t64_dedup_complete.json').open('x') as f:
        json.dump(dict(paths_and_bytes_preserved=True, rows=done,
                       free_bytes=shutil.disk_usage(str(root)).free), f, indent=2)
    print('S0_T64_INPUT_DUPLICATES_CONSOLIDATED', len(done),
          'FREE', shutil.disk_usage(str(root)).free, flush=True)


if __name__ == '__main__':
    main()
