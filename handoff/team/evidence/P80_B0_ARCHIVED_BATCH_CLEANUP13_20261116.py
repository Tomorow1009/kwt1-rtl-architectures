"""Remove only byte-identical generated B0 inputs after their durable backup.

Explicit later invocation only, after the original P80 queue/export both exit.
Holds the original team lock; never removes directories or backup members.
The earlier full-readback receipt is pinned, and archive/source hashes and
process use are freshly checked. Inaccessible own processes block deletion.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import sys

sys.dont_write_bytecode = True
ROOT = Path('/tmp/s4_21usr_p80_20261116_0315')
OPS = ROOT/'light-light126-p80-1023646'
OPS_MANIFEST_SHA = '402c08165610ed18bdd772cddd3d527570fd62bdaa6ff820e0ad19b5d7082bcd'
PROOF = ROOT/'b0_archived_batch_preflight12/verified_candidates.json'
PROOF_SHA = 'fbb98604283fcac8285dc817f554dd7bcccee37f85faba07d9fefe72906e9bd8'
PREFLIGHT = ROOT/'p80_b0_archived_batch_preflight12.py'
PREFLIGHT_SHA = 'b3eecb8d413edf8bb3be3afd1182806f73f54ad5725ce65ed23a20014b9f41e9'
OUT = ROOT/'b0_archived_batch_cleanup13'
RUN_REL = ('bundles/light-light126-systolic-b-v3-20261112_114355-ced0e139a01e/'
           'runs/systolic_b_final02_final1200/systolic_b_batch')


def need(ok, message):
    if not ok:
        raise ValueError(message)


def candidate_name(name):
    """Exact allowlist; no prefix-only authorization or directory deletion."""
    p = PurePosixPath(name)
    need(not p.is_absolute() and p.as_posix() == name and '..' not in p.parts,
         'Noncanonical candidate')
    prefix = RUN_REL+'/cases/'
    need(name.startswith(prefix), 'Outside completed B0 batch')
    rest = name[len(prefix):].split('/')
    need(len(rest) >= 2 and re.fullmatch(r'sample_\d{6}_layer_\d{2}', rest[0]),
         'Unexpected generated-input location')
    need(p.suffix in ('.hex', '.verilog', '.bin'), 'Protected evidence type')
    return name


def stopped():
    for filename, expected, status in (
        ('p80_final_combined05.json',
         '46e2a8fb416db99febbc9c2bb6ea09b619b515bb185711c2a3a9782277d11651',
         'reports_ready_review_required'),
        ('p80_export_review05/state.json',
         '952242ef4a1ea2b9ee5bcde89ec0cd4b4c48f2bd504a55ae8a3f1031a31fee4b',
         'facts_joined_manual_conclusion_required')):
        row = json.loads((ROOT/filename).read_text())
        need(row['source_sha256'] == expected and row['status'] == status and
             row.get('finished') and not Path('/proc/%d' % row['pid']).exists(),
             'Original P80 queue/export not naturally complete and exited')


def main():
    need(os.name == 'posix', 'Server-only cleanup')
    manifest_bytes = (OPS/'manifest.json').read_bytes()
    need(hashlib.sha256(manifest_bytes).hexdigest() == OPS_MANIFEST_SHA,
         'Operations bundle identity changed')
    packaged = json.loads(manifest_bytes)['files']
    for name in ('n1_archive_runtime.py', 'n1_paths.py', 'partition_synth_contract.py'):
        relative = 'workspaces/arch03/scripts/'+name
        need(hashlib.sha256((OPS/relative).read_bytes()).hexdigest() == packaged[relative],
             'Pinned cleanup dependency changed')
    sys.path.insert(0, str(OPS/'workspaces/arch03/scripts'))
    import n1_archive_runtime as archive
    from partition_synth_contract import digest as sha
    archive.paths._identity()
    need(sha(PREFLIGHT) == PREFLIGHT_SHA and sha(PROOF) == PROOF_SHA,
         'Preflight identity changed')
    spec = importlib.util.spec_from_file_location('b0_verified_readback', str(PREFLIGHT))
    checked = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checked)
    proof = json.loads(PROOF.read_text())
    need(proof['schema'] == 'p80-b0-archived-input-duplicates-readonly-v1' and
         proof['source_root'] == str(checked.PROJECT) and proof['source_batch'] == RUN_REL and
         proof['archive_sha256'] == checked.ARCHIVE_SHA and
         proof['all_archive_members_readback_verified'] == 63653 and
         proof['all_archive_bytes_readback_verified'] == 7006124866,
         'Not the verified completed B0 backup')
    rows = proof['files']
    names = [candidate_name(row['path']) for row in rows]
    need(len(names) == len(set(names)) == 49200 and
         sum(row['bytes'] for row in rows) == 2616732144,
         'Unexpected cleanup scope')
    stopped()
    need(not OUT.exists(), 'Preserve any previous cleanup attempt')
    cfg = dict(server_root=str(checked.PROJECT.parent),
               runtime_roots=[dict(bundle=str(OPS))])
    lock, identity, owner = archive.acquire_lock(cfg, 'p80-b0-duplicate-inputs13')
    state = None
    try:
        stopped()
        backup = checked.BACKUP
        frozen = {backup/'manifest.json': checked.MANIFEST_SHA,
                  backup/'receipt.json': checked.RECEIPT_SHA,
                  backup/'completed-evidence.tar.gz': checked.ARCHIVE_SHA}
        manifest = json.loads((backup/'manifest.json').read_text())
        inventory = {row['path']: row for row in manifest['files']}
        for name in (RUN_REL+'/summary.json',
                     str(PurePosixPath(RUN_REL).parent/'state.json')):
            frozen[checked.PROJECT/name] = inventory[name]['sha256']
        need(all(sha(p) == want for p, want in frozen.items()), 'Backup/terminal evidence changed')
        before = {str(p): checked.stamp(p) for p in frozen}
        source = checked.PROJECT/RUN_REL/'cases'
        processes = archive.no_open_users([source])
        for row in rows:
            p = checked.PROJECT/row['path']
            need(inventory[row['path']]['sha256'] == row['sha256'] and
                 inventory[row['path']]['bytes'] == row['bytes'] and
                 checked.stamp(p) == row['stamp'] and sha(p) == row['sha256'] and
                 checked.stamp(p) == row['stamp'], 'Current duplicate changed')
        archive.no_open_users([source])
        OUT.mkdir(mode=0o700)
        state = dict(status='removing_verified_duplicates', proof_sha256=PROOF_SHA,
                     script_sha256=sha(__file__), removed_files=0, removed_bytes=0,
                     free_before=shutil.disk_usage(str(checked.PROJECT)).free,
                     archive=str(backup/'completed-evidence.tar.gz'),
                     archive_sha256=checked.ARCHIVE_SHA, process_observation=processes,
                     backup_modified=False, protected_T80_modified=False, old8_modified=False,
                     restore='Restore named members into a new empty directory, verify hashes, then review original paths.')
        archive.save(OUT/'state.json', state)
        with (OUT/'removal_journal.jsonl').open('x') as journal:
            for i, row in enumerate(rows):
                if i % 1000 == 0:
                    need(archive.stamp(lock)[:2] == identity and
                         json.loads((lock/'owner.json').read_text()) == owner, 'Lock ownership changed')
                    archive.no_open_users([source])
                    need(all(checked.stamp(p) == before[str(p)] for p in frozen), 'Backup/evidence changed')
                p = checked.PROJECT/row['path']
                need(checked.stamp(p) == row['stamp'], 'Candidate identity changed')
                journal.write(json.dumps(dict(action='remove_intent', **row), sort_keys=True)+'\n')
                journal.flush(); os.fsync(journal.fileno())
                p.unlink()
                state['removed_files'] += 1
                state['removed_bytes'] += row['bytes']
                journal.write(json.dumps(dict(action='removed', path=row['path']))+'\n')
                journal.flush(); os.fsync(journal.fileno())
        for parent in sorted({(checked.PROJECT/row['path']).parent for row in rows}):
            archive.sync_dir(parent)
        need(all(not (checked.PROJECT/row['path']).exists() for row in rows),
             'A removed duplicate reappeared')
        need(all(checked.stamp(p) == before[str(p)] and sha(p) == want
                 for p, want in frozen.items()), 'Preserved backup/evidence changed')
        state.update(status='verified_duplicates_removed_backup_retained', finished=archive.now(),
                     free_after=shutil.disk_usage(str(checked.PROJECT)).free,
                     journal_sha256=sha(OUT/'removal_journal.jsonl'))
        archive.save(OUT/'state.json', state)
        print('B0_DUPLICATE_INPUT_CLEANUP_COMPLETE', state['removed_files'],
              state['removed_bytes'], state['free_after'], sha(OUT/'state.json'), flush=True)
    except BaseException as error:
        if state is not None:
            state.update(status='stopped_preserved', error=str(error), finished=archive.now())
            archive.save(OUT/'state.json', state)
        raise
    finally:
        archive.release_lock(lock, identity, owner)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute-verified-duplicate-cleanup', action='store_true', required=True)
    parser.parse_args()
    main()
