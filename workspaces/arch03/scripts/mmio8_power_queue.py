"""Serial remaining-layer power from immutable existing MMIO8 gate activity.

External operation tool, Python 3.6 stdlib. Never reruns a predecessor, creates
VCDs, clears team locks or edits a runtime input. Child server_run owns the lock.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def require(ok, message):
    if not ok:
        raise ValueError(message)


def save(path, value):
    path = Path(path)
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')
    os.replace(str(temp), str(path))


def predecessor(run, pid, started):
    state = read(run.parent/'state.json')['stages']['mmio8_power']
    require(state['pid'] == pid and state['started'] == started, 'Predecessor identity changed')
    require(state['status'] in ('running', 'passed'), 'Predecessor failed; inspect preserved run')
    if state['status'] == 'running':
        require((Path('/proc')/str(pid)/'cmdline').is_file(), 'Predecessor disappeared')
        return None
    digest = sha(run/'summary.json')
    require(digest == state['summary_sha256'], 'Predecessor receipt changed')
    return digest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request', required=True, type=Path)
    args = parser.parse_args()
    request = read(args.request)
    bundle = Path(request['bundle']).resolve()
    gate = Path(request['gate_run']).resolve()
    output = Path(request['output']).resolve()
    require(sha(bundle/'manifest.json') == request['manifest_sha256'], 'Bundle changed')
    require(sha(gate/'summary.json') == request['gate_summary_sha256'], 'Gate changed')
    cfg = read(bundle/'handoff/team/server_config.json')
    root = Path(cfg['server_root']).resolve()
    for path in (bundle, gate, output):
        path.relative_to(root)
    lock = root/'.arch02_team_lock'
    runner = bundle/'workspaces/arch03/scripts/server_run.py'
    sys.path.insert(0, str(runner.parent))
    import server_run
    from mmio8_power_numbers import extract
    require(server_run.ROOT == bundle, 'Wrong imported runtime')
    server_run.inputs()
    cases = request['cases']
    require(cases == ['layer_%02d'%n for n in range(3, 13)], 'Expected remaining L03-L12 only')
    sessions = ['mmio8_fullpower_l%02d_v1'%n for n in range(3, 13)]
    require(all(not (bundle/'runs'/n).exists() for n in sessions), 'Do not repeat a recorded child')
    output.mkdir(parents=True, exist_ok=False)
    state = dict(status='waiting_predecessor', pid=os.getpid(),
                 started=datetime.datetime.now().isoformat(), completed=[],
                 request_sha256=sha(args.request), runner_sha256=sha(__file__),
                 system_power_verified=False)
    save(output/'state.json', state)
    try:
        pred = request['predecessor']
        pred_run = Path(pred['run'])
        while predecessor(pred_run, pred['pid'], pred['started']) is None:
            time.sleep(20)
        pred_sha = sha(pred_run/'summary.json')
        prior = read(pred_run/'summary.json')
        require(prior['gate_summary_sha256'] == request['gate_summary_sha256'], 'Predecessor gate mismatch')
        save(output/'layer_02_numbers.json', extract(pred_run, pred_sha))
        state['predecessor_summary_sha256'] = pred_sha
        for case, session in zip(cases, sessions):
            while lock.exists() or shutil.disk_usage(str(bundle)).free < 4*2**30:
                state.update(status='waiting_lock_or_space', next_case=case,
                             free_bytes=shutil.disk_usage(str(bundle)).free)
                save(output/'state.json', state)
                time.sleep(20)
            require(sha(bundle/'manifest.json') == request['manifest_sha256'], 'Bundle changed')
            require(not (bundle/'runs'/session).exists(), 'Child already exists; no retry')
            argv = [sys.executable, str(runner), 'mmio8_power', '--session', session,
                    '--gate-run', str(gate), '--gate-summary-sha256', request['gate_summary_sha256'],
                    '--cases', case]
            state.update(status='running', case=case, session=session)
            save(output/'state.json', state)
            with (output/(session+'.log')).open('x') as log:
                child = subprocess.Popen(argv, cwd=str(bundle), stdout=log, stderr=subprocess.STDOUT)
                state['child_pid'] = child.pid
                save(output/'state.json', state)
                code = child.wait()
            require(code == 0, 'Child failed; preserve '+session)
            run = bundle/'runs'/session/'mmio8_power'
            stage = read(run.parent/'state.json')['stages']['mmio8_power']
            require(stage['status'] == 'passed', 'Child has not passed')
            digest = stage['summary_sha256']
            values = extract(run, digest)
            numeric = output/(case+'_numbers.json')
            save(numeric, values)
            state['completed'].append(dict(case=case, run=str(run), summary_sha256=digest,
                numbers_sha256=sha(numeric), raw_average_power_w=values['reported_power_w']['total'],
                raw_energy_j=values['raw_reported_energy_j'], duration_ns=values['duration_ns']))
            save(output/'state.json', state)
            print('MMIO8_POWER_DONE', case, digest, flush=True)
        state.update(status='reports_ready_review_required', finished=datetime.datetime.now().isoformat())
    except Exception as error:
        state.update(status='failed', error=str(error), finished=datetime.datetime.now().isoformat())
        save(output/'state.json', state)
        raise
    save(output/'state.json', state)
    print('MMIO8_POWER_QUEUE_COMPLETE system_power_verified=false', flush=True)


if __name__ == '__main__':
    main()
