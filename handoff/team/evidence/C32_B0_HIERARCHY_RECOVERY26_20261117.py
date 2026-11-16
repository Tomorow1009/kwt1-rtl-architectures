"""Remove one exact durably archived B0 hierarchy-report duplicate.

The running C32 connection query continues to wait for the original team lock.
No queue restart, source/netlist/activity/summary/backup removal or lock change.
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
ROOT = Path('/tmp/s4_21usr_c32_20261116_2010')
OUT = ROOT/'b0_archived_hierarchy26'
HELPER = Path('/tmp/s4_21usr_c80_20261116_1245/ops-b0-cleanup16-c8c730d/C80_B0_DUPLICATES_CLEANUP16_20261116.py')
HELPER_SHA = '0e98728332e0ba048142231f414322dc3aaf21e287b3bde0bc4121124c976441'
NAME = 'bundles/light-light126-systolic-b-v3-20261112_114355-ced0e139a01e/runs/systolic_b_v3_drc04/systolic_b_synth/hierarchy.rpt'
SIZE = 7851420


def need(ok, message):
    if not ok: raise ValueError(message)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(4*1024**2), b''): h.update(chunk)
    return h.hexdigest()


def read(path): return json.loads(Path(path).read_text())


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    module = importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def waiting():
    state = read(ROOT/'c32_export_review03/state.json')
    proc = read(ROOT/'c32_export_review03/connections_process.json')
    need(state['pid'] == 36287 and state['status'] == 'querying_own_mapped_connections'
         and proc['pid'] == 46872 and Path('/proc/36287').exists() and Path('/proc/46872').exists(),
         'Expected live connection query changed; inspect instead of cleaning')
    need(not (ROOT/'light-light126-c32-91135f6/runs/c32_unknown_connections01').exists(),
         'Query has already acquired its lock; no cleanup needed')


def main():
    need(os.name == 'posix' and ROOT.resolve() == ROOT and not OUT.exists(), 'Wrong/repeated recovery26')
    need(sha(HELPER) == HELPER_SHA, 'Idle helper changed')
    base = load('recovery26_idle', HELPER)
    need(sha(base.PREFLIGHT) == base.PREFLIGHT_SHA, 'Archive helper changed')
    checked = load('recovery26_archive', base.PREFLIGHT)
    need(sha(base.BUNDLE/'manifest.json') == base.MANIFEST_SHA, 'Helper bundle changed')
    index = read(base.BUNDLE/'manifest.json')['files']
    for name in ('n1_archive_runtime.py', 'n1_paths.py', 'partition_synth_contract.py'):
        rel = 'workspaces/arch03/scripts/'+name
        need(sha(base.BUNDLE/rel) == index[rel], 'Process inspection helper changed')
    sys.path.insert(0, str(base.BUNDLE/'workspaces/arch03/scripts'))
    import n1_archive_runtime as archive
    project = checked.PROJECT;lock = project.parent/'.arch02_team_lock'
    fixed = {checked.BACKUP/'manifest.json': checked.MANIFEST_SHA,
             checked.BACKUP/'receipt.json': checked.RECEIPT_SHA,
             checked.BACKUP/'completed-evidence.tar.gz': checked.ARCHIVE_SHA,
             checked.PRIOR: checked.PRIOR_SHA, HELPER: HELPER_SHA}
    stamps = {str(p): checked.stamp(p) for p in fixed}
    need(all(sha(p) == want and checked.stamp(p) == stamps[str(p)] for p, want in fixed.items()), 'Archive identity changed')
    prior = read(checked.PRIOR)
    need(prior['archive_sha256'] == checked.ARCHIVE_SHA and
         prior['all_archive_members_readback_verified'] == 63653 and
         prior['all_archive_bytes_readback_verified'] == 7006124866, 'Missing full archive readback proof')
    manifest = read(checked.BACKUP/'manifest.json')
    need(manifest['source_root'] == str(project), 'Wrong archive source')
    rows = {r['path']: r for r in manifest['files']}
    need(len(rows) == len(manifest['files']) and rows[NAME]['bytes'] == SIZE, 'Wrong exact report')
    p = project/NAME;stamp = checked.stamp(p)
    need(p.resolve() == p and project in p.parents and stamp['bytes'] == SIZE and
         sha(p) == rows[NAME]['sha256'] and checked.stamp(p) == stamp, 'Duplicate differs from archive')
    waiting();observation = base.idle(archive, lock, [p]);waiting()
    OUT.mkdir(mode=0o700)
    state = dict(status='verified_remove_intent',path=NAME,bytes=SIZE,sha256=rows[NAME]['sha256'],
        stamp=stamp,source_sha256=sha(__file__),archive=str(checked.BACKUP/'completed-evidence.tar.gz'),
        archive_sha256=checked.ARCHIVE_SHA,readback_proof_sha256=checked.PRIOR_SHA,
        process_observation=observation,free_before=shutil.disk_usage(str(project)).free,
        protected_T80_modified=False,old8_modified=False,p80_modified=False,c80_modified=False,
        backup_modified=False,source_or_netlist_modified=False,queue_restarted=False,
        restore='Restore this exact hierarchy.rpt member from the retained verified archive into a fresh path and verify size/SHA.')
    archive.save(OUT/'intent.json',state)
    base.idle(archive,lock,[p]);waiting()
    need(all(checked.stamp(q) == stamps[str(q)] for q in fixed) and checked.stamp(p) == stamp and
         sha(p) == rows[NAME]['sha256'] and not lock.exists(), 'Source, backup or lock changed before removal')
    p.unlink();archive.sync_dir(p.parent)
    need(not p.exists() and all(checked.stamp(q) == stamps[str(q)] for q in fixed), 'Post-remove check failed')
    state.update(status='verified_duplicate_removed_archive_retained',removed_files=1,removed_bytes=SIZE,
                 finished=archive.now(),free_after=shutil.disk_usage(str(project)).free)
    archive.save(OUT/'state.json',state)
    print('RECOVERY26_COMPLETE',SIZE,sha(OUT/'state.json'),flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser();parser.add_argument('--execute-one-archived-hierarchy', action='store_true', required=True)
    parser.parse_args();main()
