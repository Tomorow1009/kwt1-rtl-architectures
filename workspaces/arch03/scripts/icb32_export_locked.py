"""Run the prepared report exporter once while owning the existing team lock.

Operation tool only, Python 3.6. Never clears an existing lock or retries an
output directory. Interrupted live children retain the lock for inspection.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import subprocess


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(value, indent=2)+'\n')
    os.replace(str(temp), str(path))


def require(ok, message):
    if not ok:
        raise ValueError(message)


def release_own_lock(lock, expected, child):
    if child is not None and child.poll() is None:
        return False
    if not lock.is_dir() or sorted(p.name for p in lock.iterdir()) != ['owner.json']:
        return False
    owner = read(lock/'owner.json')
    if any(owner.get(k) != expected[k] for k in ('pid', 'host', 'bundle', 'session')):
        return False
    (lock/'owner.json').unlink(); lock.rmdir()
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', required=True, type=Path)
    parser.add_argument('--manifest-sha256', required=True)
    parser.add_argument('--session', required=True)
    args = parser.parse_args()
    require(re.fullmatch('[A-Za-z0-9_-]{1,40}', args.session), 'Invalid operation session')
    package = args.package.resolve(); manifest = package/'manifest.json'
    require(sha(manifest) == args.manifest_sha256, 'Report package identity changed')
    files = read(manifest)['files']
    require(all(sha(package/name) == digest for name, digest in files.items()), 'Report package file changed')
    launch = read(package/'launch.json'); runtime = Path(launch['cwd']).resolve()
    cfg = read(runtime/'handoff/team/server_config.json'); root = Path(cfg['server_root']).resolve()
    runtime.relative_to(root); package.relative_to(root)
    argv = launch['argv']
    require(len(argv) == 6 and argv[:3] == ['python3', str(package/'icb32_report.py'), '--request'] and
            argv[4] == '--output', 'Unreviewed report command')
    request = Path(argv[3]).resolve(); output = Path(argv[5]).resolve()
    request.relative_to(runtime/'runs'); output.relative_to(runtime/'runs')
    state_path = request.parent/'state.json'; queue = read(state_path)
    require(queue['status'] == 'reports_ready_review_required', 'Original queue is not complete')
    original = request.parent/'report_request.json'
    require(sha(original) == queue['report_request_sha256'], 'Original report request changed')
    reviewed = read(request)
    require(reviewed['original_request_sha256'] == queue['report_request_sha256'] and
            reviewed.get('delivery_sdc') and reviewed.get('history'), 'Reviewed request is incomplete')
    require(not output.exists(), 'Report output already exists; never retry in place')
    control = runtime/'runs'/args.session
    require(not control.exists(), 'Operation session already exists; inspect it instead')
    updates = launch['environment_updates']
    require(updates == {'PYTHONPATH': str(runtime/'workspaces/arch03/scripts')}, 'Unreviewed runtime imports')
    before = {str(p): sha(p) for p in (manifest, request, original)}
    owner = dict(pid=os.getpid(), host=socket.gethostname(), bundle=str(runtime),
                 session=args.session, stage='icb32_report', started=datetime.datetime.now().isoformat())
    lock = root/'.arch02_team_lock'; child = None; state = None
    lock.mkdir()  # Atomic; an existing/stale/foreign lock is never removed.
    try:
        save(lock/'owner.json', owner)
        control.mkdir(); state = dict(status='running', owner=owner, inputs_sha256=before,
            exporter_package=str(package), wrapper_sha256=sha(__file__), output=str(output))
        save(control/'state.json', state)
        env = dict(os.environ); env.update(updates)
        with (control/'report.log').open('x') as log:
            child = subprocess.Popen(argv, cwd=str(runtime), env=env, stdout=log, stderr=subprocess.STDOUT)
            owner.update(child_pid=child.pid, log=str(control/'report.log'))
            save(lock/'owner.json', owner); state['child_pid'] = child.pid
            save(control/'state.json', state)
            print('ICB32_REPORT_CHILD', child.pid, str(control/'report.log'), flush=True)
            code = child.wait()
        require(code == 0, 'Report failed; preserve output and log, exit '+str(code))
        require(all(sha(Path(p)) == digest for p, digest in before.items()), 'Report inputs changed')
        state.update(status='reports_ready_review_required', finished=datetime.datetime.now().isoformat(),
            receipt_sha256=sha(output/'receipt.json'), report_sha256=sha(output/'report.json'))
        save(control/'state.json', state)
        print('ICB32_LOCKED_REPORT_COMPLETE', state['report_sha256'], flush=True)
    except BaseException as error:
        if state is not None:
            state.update(status='failed_or_interrupted', error=repr(error),
                         finished=datetime.datetime.now().isoformat())
            save(control/'state.json', state)
        raise
    finally:
        released = release_own_lock(lock, owner, child)
        if state is not None:
            state['own_lock_released'] = released
            save(control/'state.json', state)


if __name__ == '__main__':
    main()
