"""Recover lock metadata space from 1200 durably archived B0 task.log copies.

Keep B0 summaries, sources, netlists, archive and all N1/T80/old8 files.
Recheck complete archive identity and individually read back every selected log.
Temporarily pause only the identified R4 L05 lock waiter, then resume it.
"""
import hashlib, importlib.util, json, os, re, shutil, signal, sys, tarfile, time
from pathlib import Path
sys.dont_write_bytecode = True
CONTROL = Path('/tmp/s4_21usr_n1_closeout_20261117_2355')
OUT = CONTROL/'bootstrap42'
HELPER = Path('/tmp/s4_21usr_c80_20261116_1245/ops-b0-cleanup16-c8c730d/C80_B0_DUPLICATES_CLEANUP16_20261116.py')
HELPER_SHA = '0e98728332e0ba048142231f414322dc3aaf21e287b3bde0bc4121124c976441'
PREFIX = 'bundles/light-light126-systolic-b-v3-20261112_114355-ced0e139a01e/runs/systolic_b_final02_final1200/systolic_b_batch/'
MIGRATE = Path('/tmp/s4_21usr_g32_l05_migrateops_20261117/migrate.py')
MIGRATE_SHA = '3160a0a4a2e240d10f2f2884d4a3c37233244175ff6d50a6fe1f7080afa5d4e7'


def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda: f.read(4*1024**2), b''): h.update(b)
    return h.hexdigest()


def read(p): return json.loads(Path(p).read_text())
def load(name, p):
    spec = importlib.util.spec_from_file_location(name, str(p))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


def main():
    assert not OUT.exists() and sha(HELPER) == HELPER_SHA
    base = load('bootstrap42_idle', HELPER)
    assert sha(base.PREFLIGHT) == base.PREFLIGHT_SHA
    checked = load('bootstrap42_backup', base.PREFLIGHT)
    assert sha(base.BUNDLE/'manifest.json') == base.MANIFEST_SHA
    deps = read(base.BUNDLE/'manifest.json')['files']
    for name in ('n1_archive_runtime.py', 'n1_paths.py', 'partition_synth_contract.py'):
        rel = 'workspaces/arch03/scripts/'+name
        assert sha(base.BUNDLE/rel) == deps[rel]
    sys.path.insert(0, str(base.BUNDLE/'workspaces/arch03/scripts'))
    import n1_archive_runtime as archive
    project = checked.PROJECT; lock = project.parent/'.arch02_team_lock'
    fixed = {checked.BACKUP/'manifest.json': checked.MANIFEST_SHA,
             checked.BACKUP/'receipt.json': checked.RECEIPT_SHA,
             checked.BACKUP/'completed-evidence.tar.gz': checked.ARCHIVE_SHA,
             checked.PRIOR: checked.PRIOR_SHA}
    stamps = {str(p): checked.stamp(p) for p in fixed}
    assert all(sha(p) == h and checked.stamp(p) == stamps[str(p)] for p, h in fixed.items())
    prior = read(checked.PRIOR)
    assert prior['all_archive_members_readback_verified'] == 63653
    assert prior['all_archive_bytes_readback_verified'] == 7006124866
    index = {r['path']: r for r in read(checked.BACKUP/'manifest.json')['files']}
    summary = project/(PREFIX+'summary.json')
    assert sha(summary) == index[PREFIX+'summary.json']['sha256']
    batch = read(summary)
    assert batch['status'] == 'passed' and batch['tasks'] == 1200 and batch['failed'] == 0
    assert batch['checked_outputs'] == 30412800
    selected = {n: r for n, r in index.items() if n.startswith(PREFIX) and
                re.fullmatch(r'cases/sample_[0-9]{6}_layer_[0-9]{2}/task\.log', n[len(PREFIX):])}
    assert len(selected) == 1200 and sum(r['bytes'] for r in selected.values()) == 2759700
    seen = set()
    with tarfile.open(str(checked.BACKUP/'completed-evidence.tar.gz'), 'r|gz') as tar:
        for member in tar:
            if member.name not in selected: continue
            row = selected[member.name]
            assert member.isfile() and member.name not in seen and member.size == row['bytes']
            data = tar.extractfile(member).read()
            assert len(data) == row['bytes'] and hashlib.sha256(data).hexdigest() == row['sha256']
            seen.add(member.name)
    assert seen == set(selected)
    rows = []
    for n, r in sorted(selected.items()):
        p = project/n; stamp = checked.stamp(p)
        assert str(p.resolve()).startswith(str(project)+'/')
        assert stamp['bytes'] == r['bytes'] and sha(p) == r['sha256'] and checked.stamp(p) == stamp
        rows.append(dict(path=n, bytes=r['bytes'], sha256=r['sha256'], stamp=stamp))
    proc = Path('/proc/130462'); resume = read(CONTROL/'l05_resume.json')
    def identity():
        assert proc.stat().st_uid == os.getuid()
        assert (proc/'stat').read_text().rsplit(')', 1)[1].split()[19] == resume['start_ticks']
        assert str(MIGRATE).encode() in (proc/'cmdline').read_bytes().split(b'\0')
        assert sha(MIGRATE) == MIGRATE_SHA
    identity()
    assert read('/tmp/s4_21usr_r4_l05_xzmigrate01_20261117/state.json')['status'] == 'waiting_for_team_lock'
    assert not lock.exists()
    OUT.mkdir(mode=0o700)
    state = dict(status='verified_before_pause', files=rows, removed_files=0, removed_bytes=0,
        source_sha256=sha(__file__), archive_sha256=checked.ARCHIVE_SHA,
        archive=str(checked.BACKUP/'completed-evidence.tar.gz'), T80_modified=False, old8_modified=False,
        N1_modified=False, summaries_modified=False, sources_modified=False, backup_modified=False,
        restore='Extract exactly the recorded task.log members from the unchanged complete B0 archive into a new directory; verify bytes/SHA before restoring original paths.')
    archive.save(OUT/'intent.json', state)
    os.kill(130462, signal.SIGSTOP)
    try:
        for _ in range(50):
            if (proc/'stat').read_text().rsplit(')', 1)[1].split()[0] == 'T': break
            time.sleep(.02)
        identity(); assert (proc/'stat').read_text().rsplit(')', 1)[1].split()[0] == 'T'
        assert not lock.exists()
        state['process_observation'] = base.idle(archive, lock, [project/r['path'] for r in rows])
        assert all(checked.stamp(p) == stamps[str(p)] for p in fixed)
        with (OUT/'journal.jsonl').open('x') as log:
            for row in rows:
                p = project/row['path']
                assert not lock.exists() and checked.stamp(p) == row['stamp'] and sha(p) == row['sha256']
                log.write(json.dumps(dict(action='remove_intent', **row))+'\n'); log.flush(); os.fsync(log.fileno())
                p.unlink(); archive.sync_dir(p.parent)
                state['removed_files'] += 1; state['removed_bytes'] += row['bytes']
                log.write(json.dumps(dict(action='removed', path=row['path']))+'\n'); log.flush(); os.fsync(log.fileno())
        assert all(checked.stamp(p) == stamps[str(p)] for p in fixed)
        state.update(status='verified_duplicates_removed_archive_retained', finished=archive.now(),
                     free_after=shutil.disk_usage(str(project)).free)
    except BaseException as error:
        state.update(status='failed_preserved', error=str(error)); raise
    finally:
        identity(); os.kill(130462, signal.SIGCONT)
        state['same_l05_waiter_resumed'] = True
        archive.save(OUT/'state.json', state)
    print('N1_BOOTSTRAP42_COMPLETE', state['removed_files'], state['removed_bytes'], state['free_after'], sha(OUT/'state.json'), flush=True)


if __name__ == '__main__': main()
