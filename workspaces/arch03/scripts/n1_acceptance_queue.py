"""Finish only N1: observe its existing SAIF, then precision and power12.

Never restart SAIF, retry failed children, clear a lock, or authorize N2.
Each actual stage owns the original team lock. This observer owns no EDA
resource while waiting and records every child before proceeding.
"""
import argparse
import datetime
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

import n1_paths
from n1_process import atomic_save, ProcessLedger
import server_run as common


def require(ok, message):
    if not ok:raise ValueError(message)


def read(path):return json.loads(Path(path).read_text())
def now():return datetime.datetime.now().isoformat()


def stage_reference(run, kind):
    run = Path(run)
    record = read(run.parent/'state.json')['stages'][kind]
    digest = common.sha(run/'summary.json')
    require(record['status'] == 'passed' and record['summary_sha256'] == digest,
            'Child has no matching completed stage: '+str(run))
    return dict(run=str(run), sha256=digest), read(run/'summary.json')


def observed_activity(request):
    run = Path(request['activity_run'])
    state = read(run.parent/'state.json')['stages']['n1_saif']
    require(state['pid'] == request['activity_pid'] and state['started'] == request['activity_started']
            and state['run'] == str(run), 'Observed SAIF job identity changed')
    require(state['status'] in ('running', 'passed'), 'Original SAIF failed; do not restart')
    if state['status'] == 'running':return None
    ref, summary = stage_reference(run, 'n1_saif')
    require(summary['schema'] == 'arch03-n1-native-saif-v1'
            and summary['status'] == 'N1_native_saif_function_and_complete_windows_passed'
            and summary['gate_summary_sha256'] == request['gate_summary_sha256']
            and summary['synthesis_summary_sha256'] == request['synthesis_summary_sha256']
            and len(summary['cases']) == 12
            and {v['case'] for v in summary['cases']} == {'layer_%02d'%i for i in range(1, 13)},
            'Completed SAIF differs from the fixed N1 configuration')
    return ref


def run_child(command, output, state, label, run, kind, lock):
    require(not Path(run).parent.exists(), 'Preserve existing child session: '+str(run))
    state.update(status='waiting_lock', child_pid=None, current=label)
    atomic_save(output/'state.json', state)
    while lock.exists():time.sleep(20)
    state.update(status='launching', command=command)
    atomic_save(output/'state.json', state)
    child = None
    with (output/(label+'.driver.log')).open('x') as log:
        try:
            child = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT)
            state.update(status='running', child_pid=child.pid)
            atomic_save(output/'state.json', state)
        finally:
            if child is not None:
                code, interruptions = ProcessLedger.drain(None, child)
                state['child_pid'] = None
                if interruptions:raise interruptions[0]
    require(child is not None and code == 0, 'N1 child failed; preserve '+str(run))
    ref, summary = stage_reference(run, kind)
    if kind == 'n1_precision':
        require(summary.get('status') == 'passed' and summary.get('internal_precision_verified') is True
                and summary.get('tasks') == 1200, 'N1 precision did not pass')
    state['completed'].append(dict(stage=kind, label=label, reference=ref))
    atomic_save(output/'state.json', state)
    print('N1_ACCEPTANCE_CHILD_COMPLETE', label, ref['sha256'], flush=True)
    return ref


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--request', required=True, type=Path)
    p.add_argument('--request-sha256', required=True)
    p.add_argument('--session', required=True)
    a = p.parse_args()
    require(re.fullmatch('[A-Za-z0-9_-]{1,45}', a.session), 'Invalid queue session')
    require(common.sha(a.request) == a.request_sha256, 'Queue request changed')
    req = read(a.request)
    require(req['schema'] == 'arch03-n1-acceptance-continuation-v1'
            and req['runner_sha256'] == common.sha(Path(__file__)), 'Wrong queue source/schema')
    require(str(common.ROOT) == req['bundle'], 'Queue imported wrong frozen bundle')
    cfg = read(common.ROOT/'handoff/team/server_config.json')
    cfg = n1_paths.configure(cfg, common.ROOT, req['runtime_root'], req['bundle_manifest_sha256'],
                             [(req['synthesis_bundle'], req['synthesis_bundle_manifest_sha256'])])
    require(Path(req['activity_run']).parent.parent == common.ROOT/'runs', 'Wrong SAIF runtime')
    common.inputs()
    observed_activity(req)  # Reject a failed/replaced original before creating queue output.
    ops = Path(req['precision_operations'])
    require(common.sha(ops/'manifest.json') == req['precision_operations_manifest_sha256'], 'Precision OPS changed')
    for name, meta in read(ops/'manifest.json')['files'].items():
        require(common.sha(ops/name) == meta['sha256'], 'Precision OPS member changed')
    output = common.ROOT/'runs'/a.session
    output.mkdir(exist_ok=False)
    atomic_save(output/'request.json', req)
    state = dict(schema='arch03-n1-acceptance-queue-state-v1', status='waiting_original_saif', pid=os.getpid(),
                 started=now(), request_sha256=a.request_sha256, completed=[], child_pid=None,
                 n2_allowed=False, system_power_verified=False)
    atomic_save(output/'state.json', state)
    lock = Path(cfg['server_root'])/'.arch02_team_lock'
    try:
        activity = observed_activity(req)
        while activity is None:
            time.sleep(20)
            require(common.sha(a.request) == a.request_sha256, 'Queue request changed while waiting')
            activity = observed_activity(req)
        state['activity_reference'] = activity
        atomic_save(output/'state.json', state)
        bootstrap = ('import os,sys;os.environ["OPENBLAS_NUM_THREADS"]="1";sys.path[:0]='+
            repr([req['numpy_root'], str(ops/'scripts'), str(common.ROOT/'workspaces/arch03/scripts')])+
            ';import n1_precision_stage as s;s.main()')
        precision_session = a.session+'_precision'
        command = [sys.executable, '-B', '-u', '-c', bootstrap, '--session', precision_session,
            '--runtime-root', req['runtime_root'], '--runtime-manifest-sha256', req['bundle_manifest_sha256'],
            '--operations-manifest-sha256', req['precision_operations_manifest_sha256'],
            '--archive', req['archive'], '--archive-sha256', req['archive_sha256'], '--dataset', req['dataset']]
        run_child(command, output, state, 'precision', common.ROOT/'runs'/precision_session/'n1_precision', 'n1_precision', lock)
        for i in range(1, 13):
            require(common.sha(a.request) == a.request_sha256, 'Queue request changed before power')
            require(observed_activity(req) == activity, 'SAIF reference changed before power')
            session = a.session+'_p%02d'%i
            command = [sys.executable, '-B', '-u', str(common.ROOT/'workspaces/arch03/scripts/n1_server.py'),
                'power', '--session', session, '--runtime-root', req['runtime_root'],
                '--runtime-manifest-sha256', req['bundle_manifest_sha256'],
                '--runtime-evidence', req['synthesis_bundle'], req['synthesis_bundle_manifest_sha256'],
                '--saif-activity-run', activity['run'], '--saif-activity-sha256', activity['sha256'],
                '--cases', 'layer_%02d'%i]
            run_child(command, output, state, 'power%02d'%i, common.ROOT/'runs'/session/'n1_power', 'n1_power', lock)
        state.update(status='numbers_ready_independent_review_required', finished=now())
    except BaseException as exc:
        state.update(status='failed', error=str(exc), finished=now())
        raise
    finally:
        atomic_save(output/'state.json', state)
    print('N1_ACCEPTANCE_QUEUE_COMPLETE independent_review_required=true N2_allowed=false', flush=True)


if __name__ == '__main__':main()
