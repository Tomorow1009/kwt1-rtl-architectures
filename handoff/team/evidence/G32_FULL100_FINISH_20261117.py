"""Finish the approved full100 addendum after its queue has completed.

No hardware runs, source cleanup, lock clearing or frozen-release mutations.
This driver lives outside the runtime being copied. Existing report/archive
contracts perform the detailed identity and completion checks.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import time

ROOT = Path('/tmp/s4_21usr_g32_20261117_1530')
BUNDLE = ROOT/'light-light126-g32-full100-398a58b'
OPS = Path('/tmp/s4_21usr_g32_full100_ops_20261117_1605')
DEPS = Path('/tmp/s4_21usr_g32_full100_deps_20261117_1610')
CONTROL = Path('/tmp/s4_21usr_g32_full100_finish01_20261117')
MIGRATION = Path('/tmp/s4_21usr_r4_l05_xzmigrate01_20261117/state.json')
BACKUPS = Path('/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109/backups')
OPS_SHA = '331f238efe8150ca9a8ade11439f4185658c35d88f320192dddedc2264322941'
CAPACITY_SHA = '2b591b8f32b583f03b11720d87b5029c64229bb56dc6fe4a86572512b504efcf'
MANIFEST_SHA = '1577690aba585e473c7d0174ebca95618edc032e1184cf99a6d350bfa75d9052'


def need(ok, message):
    if not ok: raise ValueError(message)


def read(path): return json.loads(Path(path).read_text())


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for raw in iter(lambda: f.read(4*1024**2), b''): h.update(raw)
    return h.hexdigest()


def save(path, value):
    path = Path(path)
    temporary = path.with_name(path.name+'.tmp')
    with temporary.open('w') as f:
        json.dump(value, f, sort_keys=True, indent=2, allow_nan=False)
        f.write('\n'); f.flush(); os.fsync(f.fileno())
    os.replace(str(temporary), str(path))


def main():
    sys.dont_write_bytecode = True
    need(Path.cwd() != ROOT and ROOT not in Path.cwd().parents, 'Operate outside copied runtime')
    need(not CONTROL.exists(), 'Preserve previous finish attempts')
    terminal = BUNDLE/'runs/full100_02/state.json'
    queue = read(terminal)
    need(queue['status'] == 'full100_and_precision_passed_archive_pending' and
         queue.get('finished') and queue.get('current_run') is None and
         not Path('/proc/%d' % queue['pid']).exists(), 'Full100 queue must finish and exit first')
    need(sha(OPS/'manifest.json') == OPS_SHA, 'Postprocess manifest changed')
    for name, digest in read(OPS/'manifest.json')['files'].items():
        need(Path(name).name == name and sha(OPS/name) == digest, 'Postprocess file changed')
    need(sha(DEPS/'g32_archive_capacity.py') == CAPACITY_SHA, 'Archive capacity helper changed')
    need(sha(BUNDLE/'manifest.json') == MANIFEST_SHA, 'Runtime identity changed')
    sys.path[:0] = [str(OPS), str(DEPS), str(BUNDLE/'workspaces/arch03/scripts')]
    import g32_full100_report as report
    import g32_full100_archive as archive
    CONTROL.mkdir(mode=0o700)
    state = dict(schema='g32-full100-finish-v1', status='reporting', pid=os.getpid(),
        started=datetime.datetime.now().isoformat(), script_sha256=sha(__file__),
        frozen_release_modified=False, source_deleted=False, old8_modified=False, T80_modified=False)
    save(CONTROL/'state.json', state)
    try:
        target = BACKUPS/('g32-runtime-'+datetime.datetime.now().strftime('%Y%m%d_%H%M')+'-full10001')
        request = dict(schema='arch03-g32-full100-runtime-copy-v1', runtime_root=str(ROOT),
            bundle=str(BUNDLE), bundle_manifest_sha256=MANIFEST_SHA, runtime_evidence=[],
            queue=str(terminal.parent), state_sha256=sha(terminal), destination=str(target),
            storage_profile='copy_only_512MiB')
        save(CONTROL/'request.json', request)
        state['request_sha256'] = sha(CONTROL/'request.json')
        state['destination'] = str(target)
        save(CONTROL/'state.json', state)
        output = ROOT/'full100_export01'
        result = report.export(request, OPS/'G32_BASELINE_CONCLUSION.json', output)
        state.update(status='waiting_for_durable_L05', report=str(output),
                     report_sha256=sha(output/'report.json'), report_receipt_sha256=sha(output/'receipt.json'))
        save(CONTROL/'state.json', state)
        print('FULL100_REPORT_COMPLETE', result['tasks'], result['failed'], flush=True)
        while True:
            migration = read(MIGRATION)
            need(not migration['status'].startswith('failed'), 'L05 migration failed; preserve all sources')
            if migration['status'] == 'durable_xz_verified_original_gzip_copy_retained':
                if not Path('/proc/%d' % migration['pid']).exists(): break
            time.sleep(5)
        durable = Path(migration['durable_archive'])
        need(migration['full_durable_readback_verified'] and durable.is_file() and
             durable.stat().st_size == migration['durable_archive_bytes'] and
             sha(durable) == migration['durable_archive_sha256'], 'Durable L05 identity changed')
        snapshot = ROOT/'closure_snapshot01'
        need(not snapshot.exists(), 'Preserve old closure snapshots')
        snapshot.mkdir(mode=0o700)
        for directory, label in ((OPS, 'postprocess_tools'), (DEPS, 'postprocess_dependencies')):
            dest = snapshot/label; dest.mkdir()
            for file in directory.iterdir():
                need(file.is_file() and not file.is_symlink(), 'Only regular postprocess inputs')
                shutil.copy2(str(file), str(dest/file.name))
                need(sha(file) == sha(dest/file.name), 'Closure snapshot copy differs')
        for source, name in ((Path(__file__), 'finish.py'), (CONTROL/'request.json', 'request.json'),
                             (MIGRATION, 'l05_migration_state.json'),
                             (durable.parent/'receipt.json', 'l05_durable_receipt.json')):
            shutil.copy2(str(source), str(snapshot/name))
            need(sha(source) == sha(snapshot/name), 'Closure snapshot differs')
        files = {p.relative_to(snapshot).as_posix(): sha(p) for p in snapshot.rglob('*') if p.is_file()}
        save(snapshot/'manifest.json', dict(schema='g32-full100-closure-snapshot-v1', files=files,
            report_sha256=state['report_sha256'], request_sha256=state['request_sha256']))
        state.update(status='archiving_copy_only', closure_manifest_sha256=sha(snapshot/'manifest.json'))
        save(CONTROL/'state.json', state)
        receipt = archive.archive(request)
        state.update(status='full100_report_and_durable_archive_verified',
            finished=datetime.datetime.now().isoformat(), archive_sha256=receipt['archive_sha256'],
            archive_bytes=receipt['archive_bytes'], archive_receipt_sha256=sha(target/'receipt.json'),
            archive_manifest_sha256=sha(target/'manifest.json'), member_counts=receipt['member_counts'])
        save(CONTROL/'state.json', state)
        save(target/'full100_finish_receipt.json', state)
        print('G32_FULL100_FINISH_PASS', state['archive_sha256'], state['archive_bytes'], flush=True)
    except BaseException as error:
        state.update(status='failed_sources_preserved', error=str(error), finished=datetime.datetime.now().isoformat())
        save(CONTROL/'state.json', state)
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--wait', action='store_true')
    args = parser.parse_args()
    if args.wait:
        need(sha(BUNDLE/'manifest.json') == MANIFEST_SHA, 'Wrong full100 queue bundle')
        print('WAIT_FOR_EXISTING_FULL100_QUEUE', flush=True)
        while True:
            pending = read(BUNDLE/'runs/full100_02/state.json')
            need(pending['pid'] == 98932 and pending['full100_authorized'] is True and
                 pending['samples'] == 100 and pending['tasks'] == 1200,
                 'Waiting queue identity changed')
            need(pending['status'] in ('running', 'full100_and_precision_passed_archive_pending'),
                 'Full100 did not pass; do not run reporting/archive')
            if pending['status'] == 'full100_and_precision_passed_archive_pending' and not Path('/proc/98932').exists():
                break
            time.sleep(5)
    main()
