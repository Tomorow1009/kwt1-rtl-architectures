"""Launch an existing guarded copy tool only after P80 export has exited.

Prepared locally, not automatically deployed. No deletion, EDA or acceptance.
The original runtime, desktop T80 and old8 are never destinations.
"""
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path('/tmp/s4_21usr_p80_20261116_0315')
BUNDLE = ROOT/'light-light126-p80-1023646'
MANIFEST = '402c08165610ed18bdd772cddd3d527570fd62bdaa6ff820e0ad19b5d7082bcd'
BACKUPS = Path('/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109/backups')
QUEUE = BUNDLE/'runs/p80_finish05'
EXPORT = ROOT/'p80_export_review05/state.json'


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(4*1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def require(ok, message):
    if not ok:
        raise ValueError(message)


def save_new(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


def preflight():
    require(sha(BUNDLE/'manifest.json') == MANIFEST, 'Operations package changed')
    export = read(EXPORT)
    require(export['status'] == 'facts_joined_manual_conclusion_required' and
            export.get('finished') and not Path('/proc/%d' % export['pid']).exists(),
            'Original exporter must finish and exit before copying')
    parent = read(ROOT/'p80_final_combined05.json')
    require(parent['status'] == 'reports_ready_review_required' and
            not Path('/proc/%d' % parent['pid']).exists(), 'Original queue owner is still active')
    require(sha(QUEUE/'state.json') == export['queue_state_sha256'] == parent['queue_state_sha256'],
            'Queue identity differs between original owner and exporter')
    require(sha(export['snapshot']) == export['snapshot_sha256'], 'Model snapshot changed')
    require(sha(export['report']) == export['report_sha256'], 'Report changed')
    request = read(QUEUE/'request.json')
    require(request['bundle'] == str(BUNDLE) and request['runtime_root'] == str(ROOT) and
            request['bundle_manifest_sha256'] == MANIFEST, 'Wrong completed runtime')
    return export, request


def launch():
    export, previous = preflight()
    stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M')
    control = Path('/tmp')/('s4_21usr_p80_archive_' + stamp)
    target = BACKUPS/('p80-runtime-' + stamp)
    require(not control.exists() and not target.exists(), 'Keep earlier copy attempts')
    source = BUNDLE/'workspaces/arch03/scripts/p80_archive_runtime.py'
    require(sha(source) == read(BUNDLE/'manifest.json')['files'][
            'workspaces/arch03/scripts/p80_archive_runtime.py'], 'Archive tool not frozen in package')
    require(Path.cwd() != ROOT and ROOT not in Path.cwd().parents, 'Start outside source runtime')
    control.mkdir(mode=0o700)
    request = dict(schema='arch03-p80-runtime-copy-v1', runtime_root=str(ROOT),
        bundle=str(BUNDLE), bundle_manifest_sha256=MANIFEST,
        runtime_evidence=previous['runtime_evidence'], queue=str(QUEUE),
        queue_state_sha256=export['queue_state_sha256'],
        report_run=str(Path(export['report']).parent), report_sha256=export['report_sha256'],
        destination=str(target))
    path = control/'request.json'; save_new(path, request)
    preflight()
    command = [sys.executable, '-B', '-u', str(source), '--request', str(path),
               '--request-sha256', sha(path)]
    save_new(control/'launch.json', dict(command=command, source_sha256=sha(source),
        launcher_sha256=sha(__file__), exporter_state_sha256=sha(EXPORT),
        copy_only=True, source_deleted=False, stage_accepted=False))
    with (control/'archive.log').open('x') as log:
        child = subprocess.Popen(command, cwd='/tmp', stdin=subprocess.DEVNULL,
            stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    save_new(control/'process.json', dict(pid=child.pid, destination=str(target),
        command=command, started=datetime.datetime.now().isoformat()))
    print('P80_COPY_ONLY_STARTED', child.pid, str(control), str(target), flush=True)


if __name__ == '__main__':
    launch()
