"""Read-only proof for 18 exact B0 duplicates already in a durable archive.

No unlink, rename, lock change, EDA launch, source write or cleanup authorization.
The R4 method qualification, T80, old eight-lane data and P80 are excluded.
Any later cleanup must independently establish idle processes and recheck hashes.
"""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import time

PROJECT = Path('/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109')
BACKUP = PROJECT/'backups/systolic-b-20261112_2320'
ROOT = Path('/tmp/s4_21usr_c80_20261116_1245')
OUT = ROOT/'b0_archived_reports_saif_preflight15'
PREFIX = 'bundles/light-light126-systolic-b-v3-20261112_114355-ced0e139a01e/runs/'
MANIFEST_SHA = '443a49be5abd11b5ab8d5c5bef744ae1c6cef5908ffd933041d06e086193aea9'
RECEIPT_SHA = 'b798a588f09cc18edc1239df988f6e2779a16e86989e2e88aca8a30acb29f5ee'
ARCHIVE_SHA = 'dbfd6e93ea6257995e61e6fce8bff0aaf0d0f9d47c0d33cc38d6ce08ea536a50'
PRIOR = Path('/tmp/s4_21usr_p80_20261116_0315/b0_archived_batch_preflight12/verified_candidates.json')
PRIOR_SHA = 'fbb98604283fcac8285dc817f554dd7bcccee37f85faba07d9fefe72906e9bd8'


def need(value, message):
    if not value:
        raise ValueError(message)


def candidates():
    reports = [PREFIX+'systolic_b_v3_drc%02d/systolic_b_synth/' % n+leaf
               for n in (4, 5) for leaf in ('mapped_probe_inventory.tsv', 'area_inventory.json', 'leaf_area.tsv')]
    waves = [PREFIX+'systolic_b_power_final01_activity12/systolic_b_saif/layer_%02d.saif' % n
             for n in range(1, 13)]
    return tuple(reports+waves)


def candidate_name(name):
    p = PurePosixPath(name)
    need(not p.is_absolute() and '..' not in p.parts and p.as_posix() == name and name in candidates(),
         'Outside the exact 18 B0 duplicate files')
    return name


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(4*1024**2), b''):
            h.update(chunk)
    return h.hexdigest()


def stamp(path):
    p = Path(path)
    need(p.resolve() == p and not p.is_symlink(), 'Symlink or noncanonical evidence path')
    s = p.stat()
    need(stat.S_ISREG(s.st_mode) and s.st_uid == os.getuid(), 'Expected an owned regular file')
    return dict(device=s.st_dev, inode=s.st_ino, bytes=s.st_size, mtime_ns=s.st_mtime_ns,
                ctime_ns=s.st_ctime_ns, uid=s.st_uid, mode=s.st_mode)


def main():
    need(os.name == 'posix' and ROOT.is_dir() and ROOT.resolve() == ROOT and
         ROOT.stat().st_uid == os.getuid(), 'Run only in the existing private C80 environment')
    need(not OUT.exists(), 'Preserve previous read-only proof')
    os.nice(19)
    fixed = {BACKUP/'manifest.json': MANIFEST_SHA, BACKUP/'receipt.json': RECEIPT_SHA,
             BACKUP/'completed-evidence.tar.gz': ARCHIVE_SHA, PRIOR: PRIOR_SHA}
    before = {str(p): stamp(p) for p in fixed}
    for p, want in fixed.items():
        need(sha(p) == want and stamp(p) == before[str(p)], 'Changed archived evidence')
    prior = json.loads(PRIOR.read_text())
    need(prior['archive_sha256'] == ARCHIVE_SHA and
         prior['all_archive_members_readback_verified'] == 63653 and
         prior['all_archive_bytes_readback_verified'] == 7006124866,
         'Missing exact full-archive readback proof')
    manifest = json.loads((BACKUP/'manifest.json').read_text())
    need(manifest['source_root'] == str(PROJECT), 'Wrong archived project')
    index = {row['path']: row for row in manifest['files']}
    need(len(index) == len(manifest['files']), 'Duplicate archive path')
    rows = []
    for name in candidates():
        candidate_name(name)
        archived = index[name]
        p = PROJECT/name
        old = stamp(p)
        digest = sha(p)
        need(old['bytes'] == archived['bytes'] and digest == archived['sha256'] and stamp(p) == old,
             'Archived duplicate no longer matches source: '+name)
        rows.append(dict(path=name, bytes=old['bytes'], sha256=digest, stamp=old))
    need(all(stamp(PROJECT/r['path']) == r['stamp'] for r in rows) and
         all(stamp(p) == before[str(p)] for p in fixed), 'Evidence changed during read-only check')
    result = dict(schema='c80-b0-reports-saif-duplicates-readonly-v1',
        observed_unix=time.time(), source_root=str(PROJECT), archive=str(BACKUP/'completed-evidence.tar.gz'),
        archive_sha256=ARCHIVE_SHA, archive_manifest_sha256=MANIFEST_SHA,
        full_archive_readback_proof=str(PRIOR), full_archive_readback_proof_sha256=PRIOR_SHA,
        all_archive_members_previously_readback_verified=63653,
        all_archive_bytes_previously_readback_verified=7006124866,
        archive_bytes_freshly_hashed=before[str(BACKUP/'completed-evidence.tar.gz')]['bytes'],
        files=rows, candidate_files=len(rows), candidate_bytes=sum(r['bytes'] for r in rows),
        script_sha256=sha(__file__), process_idle_verified=False, cleanup_permitted=False,
        source_modified=False, source_deleted=False, backup_modified=False,
        protected_T80_modified=False, old8_modified=False, p80_modified=False,
        qualification_files_included=False,
        note='Read-only proof only; final B0 activity12 and six superseded DRC reports. '
             'All summaries, power reports, source, netlists, logs and R4 qualification remain outside scope.')
    OUT.mkdir(mode=0o700)
    p = OUT/'verified_candidates.json'
    with p.open('x') as f:
        json.dump(result, f, indent=2, sort_keys=True)
        f.write('\n')
        f.flush()
        os.fsync(f.fileno())
    print('B0_DUPLICATES_READONLY',len(rows),result['candidate_bytes'],sha(p),flush=True)


if __name__ == '__main__':
    main()
