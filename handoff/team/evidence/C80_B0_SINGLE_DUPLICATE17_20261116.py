"""Free one archived B0 duplicate while C80 waits for shared-lock storage.

The original exporter and query remain untouched. Require the exact query to
have no child, no created session and no lock; no own EDA may be active. This
explicit recovery differs from cleanup16, which requires an exited exporter.
Only one pinned old B0 DRC report can be removed, never a waveform or source.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys

sys.dont_write_bytecode = True
ROOT = Path('/tmp/s4_21usr_c80_20261116_1245')
BUNDLE = ROOT/'light-light126-c80-74f3ae7'
BASE = ROOT/'ops-b0-cleanup16-c8c730d/C80_B0_DUPLICATES_CLEANUP16_20261116.py'
BASE_SHA = '0e98728332e0ba048142231f414322dc3aaf21e287b3bde0bc4121124c976441'
OUT = ROOT/'b0_archived_single_duplicate17'
REL = ('bundles/light-light126-systolic-b-v3-20261112_114355-ced0e139a01e/runs/'
       'systolic_b_v3_drc05/systolic_b_synth/mapped_probe_inventory.tsv')
TARGET_SHA = '33ca05a13919cae83825c8d3c3737710f661d684c6ea7c9321a00edb5369a601'
TARGET_BYTES = 268811341
EXPORT_SHA = '4c001bb4603a52b3c6f24d95566442bc59c48ee9709e37cbd224b0982331048a'


def need(ok, message):
    if not ok: raise ValueError(message)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(4*1024**2), b''): h.update(chunk)
    return h.hexdigest()


def read(path): return json.loads(Path(path).read_text())


def check_wait(row, process, command, children, lock_exists, session_exists, log):
    need(row.get('source_sha256') == EXPORT_SHA and row.get('pid') == 59705 and
         row.get('status') == 'querying_own_mapped_connections' and not row.get('finished'),
         'Exporter is not the original waiting query owner')
    need(process.get('pid') == 134382 and process.get('driver_pid') == row['pid'] and
         command == process.get('command'), 'Query process identity changed')
    need(not children.strip() and not lock_exists and not session_exists and
         log.rstrip().endswith('WAIT_INITIAL_SHARED_LOCK_STORAGE'),
         'Query is not childless and waiting before original lock acquisition')


def waiting():
    c = ROOT/'c80_export_review02';row = read(c/'state.json');process = read(c/'connections_process.json')
    proc = Path('/proc/134382')
    cmd = proc.joinpath('cmdline').read_bytes().rstrip(b'\0').decode().split('\0')
    expected = ['/bin/python3', '-B', '-u', str(BUNDLE/'workspaces/arch03/scripts/c80_unknown_connections.py'),
                '--request', str(c/'connection_request.json'), '--request-sha256',
                '5bd35c5bc0e9840cdc8471e93af96ffc1dfce0c926d2070bd195d7ef2e8ed580']
    need(cmd == expected, 'Wrong query command')
    need(sha(ROOT/'ops-export02-00e0810/C80_EXPORT_REVIEW02_20261116.py') == EXPORT_SHA,
         'Exporter source changed')
    owner = Path('/proc/59705')
    need(owner.joinpath('cmdline').read_bytes().rstrip(b'\0').decode().split('\0') ==
         ['/bin/python3', '-B', '-u', str(ROOT/'ops-export02-00e0810/C80_EXPORT_REVIEW02_20261116.py')],
         'Exporter process changed')
    check_wait(row, process, cmd, proc.joinpath('task/134382/children').read_text(),
               Path('/storage2/2026contest/server4/s4_21usr/Desktop/IC/.arch02_team_lock').exists(),
               (BUNDLE/'runs/c80_unknown_connections02').exists(), (c/'connections.log').read_text())
    # Kernel start-time identity protects against numeric PID reuse during checks.
    return dict(export_state_sha256=sha(c/'state.json'), process_sha256=sha(c/'connections_process.json'),
                exporter_start=owner.joinpath('stat').read_text().rsplit(')', 1)[1].split()[19],
                query_start=proc.joinpath('stat').read_text().rsplit(')', 1)[1].split()[19])


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    result = importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result


def main():
    need(os.name == 'posix' and not OUT.exists() and sha(BASE) == BASE_SHA, 'Wrong or repeated recovery')
    base = load('cleanup16_dependency', BASE)
    need(sha(base.PREFLIGHT) == base.PREFLIGHT_SHA and sha(base.PROOF) == base.PROOF_SHA, 'Proof changed')
    checked = load('preflight15_dependency', base.PREFLIGHT)
    mf = read(BUNDLE/'manifest.json')['files']
    need(sha(BUNDLE/'manifest.json') == base.MANIFEST_SHA, 'Frozen bundle changed')
    for name in ('n1_archive_runtime.py', 'n1_paths.py', 'partition_synth_contract.py'):
        rel = 'workspaces/arch03/scripts/'+name
        need(sha(BUNDLE/rel) == mf[rel], 'Changed process-inspection dependency')
    sys.path.insert(0, str(BUNDLE/'workspaces/arch03/scripts'))
    import n1_archive_runtime as archive
    proof = read(base.PROOF);rows = [x for x in proof['files'] if x['path'] == REL]
    need(len(rows) == 1 and rows[0]['sha256'] == TARGET_SHA and rows[0]['bytes'] == TARGET_BYTES and
         proof['archive_sha256'] == checked.ARCHIVE_SHA and
         proof['all_archive_members_previously_readback_verified'] == 63653 and
         proof['all_archive_bytes_previously_readback_verified'] == 7006124866, 'Wrong single duplicate proof')
    row = rows[0];target = checked.PROJECT/checked.candidate_name(REL)
    need(target.resolve() == target and checked.PROJECT in target.parents, 'Target outside exact project')
    fixed = {checked.BACKUP/'manifest.json': checked.MANIFEST_SHA,
             checked.BACKUP/'receipt.json': checked.RECEIPT_SHA,
             checked.BACKUP/'completed-evidence.tar.gz': checked.ARCHIVE_SHA,
             checked.PRIOR: checked.PRIOR_SHA, base.PROOF: base.PROOF_SHA}
    before = {str(p): checked.stamp(p) for p in fixed};wait = waiting()
    lock = checked.PROJECT.parent/'.arch02_team_lock'
    base.idle(archive, lock, [target])
    need(all(sha(p) == h and checked.stamp(p) == before[str(p)] for p, h in fixed.items()),
         'Retained complete backup or readback proof changed')
    need(checked.stamp(target) == row['stamp'] and sha(target) == TARGET_SHA and
         checked.stamp(target) == row['stamp'], 'Duplicate changed')
    processes = base.idle(archive, lock, [target]);need(waiting() == wait, 'Waiting query changed')
    need(all(checked.stamp(p) == before[str(p)] for p in fixed), 'Backup changed before removal')
    OUT.mkdir(mode=0o700)
    record = dict(status='intent_verified_single_duplicate', source_sha256=sha(__file__),
                  target=str(target), bytes=TARGET_BYTES, sha256=TARGET_SHA, archive=str(checked.BACKUP/'completed-evidence.tar.gz'),
                  archive_sha256=checked.ARCHIVE_SHA, proof_sha256=base.PROOF_SHA,
                  original_query=wait, process_observation=processes,
                  free_before=shutil.disk_usage(str(checked.PROJECT)).free,
                  protected_T80_modified=False, old8_modified=False, p80_modified=False,
                  live_c80_modified=False, original_queue_restarted=False)
    archive.save(OUT/'intent.json', record)
    need(waiting() == wait and not lock.exists() and checked.stamp(target) == row['stamp'],
         'Final query or target state changed')
    target.unlink();archive.sync_dir(target.parent)
    need(not target.exists() and all(checked.stamp(p) == before[str(p)] for p in fixed), 'Post-removal mismatch')
    record.update(status='single_verified_duplicate_removed_backup_retained', finished=archive.now(),
                  free_after=shutil.disk_usage(str(checked.PROJECT)).free, remaining_original_candidates=17)
    archive.save(OUT/'receipt.json', record)
    print('B0_SINGLE17_COMPLETE', TARGET_BYTES, sha(OUT/'receipt.json'), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute-single-verified-duplicate', action='store_true', required=True)
    parser.parse_args();main()
