"""Observe the existing T80 batch, then run only its remaining stages serially.

Each child owns the existing team lock. A failure is retained and stops this
queue; no stage is retried and no older queue or full100 batch is started.
"""
import argparse
import datetime
import os
from pathlib import Path
import re
import subprocess
import sys
import time

import server_run as common
from n1_process import atomic_save, ProcessLedger
from t80_precision_stage import operations_identity
from t80_precision_join import require, read


def completed(run, stage):
    run = Path(run)
    record = read(run.parent/'state.json')['stages'][stage]
    digest = common.sha(run/'summary.json')
    require(record['status'] == 'passed' and record['summary_sha256'] == digest,
            'Missing completed child identity: '+str(run))
    return dict(run=str(run), sha256=digest)


def observe_batch(request):
    run = Path(request['batch_run'])
    record = read(run.parent/'state.json')['stages']['t80_batch20']
    require(record['pid'] == request['batch_pid'] and record['started'] == request['batch_started']
            and record['run'] == str(run), 'Original T80 batch identity changed')
    require(record['status'] in ('running', 'passed'), 'Original T80 batch failed; do not restart')
    if record['status'] == 'running':
        return None
    ref = completed(run, 't80_batch20')
    result = read(run/'summary.json')
    require(result['schema'] == 'arch03-t80-first20-batch-v4' and result['tasks'] == 240 and
            result['checked_outputs'] == result['checked_totals'] == 6082560 and result['failed'] == 0,
            'Wrong T80 batch scope')
    return ref


def prior_contention(request):
    """Reuse only the completed, identical hardware/firmware contention run.

    The sole permitted bundle difference is the passive recovery observer.
    A changed DUT, installer, stimulus or firmware requires a fresh test.
    """
    prior = request.get('prior_contention')
    if prior is None:
        return None
    run = Path(prior['run']).resolve()
    ref = completed(run, 't80_contention')
    require(ref['sha256'] == prior['sha256'], 'Prior contention summary changed')
    old_bundle = run.parents[2]
    old = read(old_bundle/'manifest.json')['files']
    current = read(common.ROOT/'manifest.json')['files']
    observer = 'workspaces/arch03/tb/arch03_t80_sequence_monitor.svh'
    require(set(old) == set(current), 'Prior contention bundle file set changed')
    require({p: h for p, h in old.items() if p != observer} ==
            {p: h for p, h in current.items() if p != observer},
            'Prior contention hardware, firmware or tools changed')
    require(all(common.sha(old_bundle/p) == digest for p, digest in old.items()),
            'Prior contention bundle bytes changed')
    result = read(run/'summary.json')
    require(result.get('contention_verified') is True and result.get('cpu_executed') is True,
            'Prior run does not establish actual CPU contention')
    return ref


def run_child(command, run, stage, queue, state, lock):
    run = Path(run)
    require(not run.parent.exists(), 'Preserve existing stage '+str(run))
    state.update(status='waiting_lock', stage=stage, command=command, child_pid=None)
    atomic_save(queue/'state.json', state)
    while lock.exists():
        time.sleep(20)
    with (queue/(run.parent.name+'.log')).open('x') as log:
        child = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT)
        state.update(status='running', child_pid=child.pid)
        atomic_save(queue/'state.json', state)
        code, interruptions = ProcessLedger.drain(None, child)
    state['child_pid'] = None
    if interruptions:
        raise interruptions[0]
    require(code == 0, 'T80 child failed; preserve '+str(run))
    ref = completed(run, stage)
    state['completed'].append(dict(stage=stage, reference=ref))
    atomic_save(queue/'state.json', state)
    print('T80_QUEUE_STAGE_PASS', stage, ref['sha256'], flush=True)
    return ref


def execute(request, queue):
    require(request['schema'] == 't80-complete-current-stage-v1', 'Wrong T80 queue request schema')
    require(str(common.ROOT) == request['bundle'], 'Wrong frozen T80 bundle import')
    require(common.sha(common.ROOT/'manifest.json') == request['bundle_manifest_sha256'], 'Bundle changed')
    common.inputs()
    ops = operations_identity(request['operations_manifest_sha256'])
    require(request['queue_sha256'] == common.sha(Path(__file__)), 'Queue source changed')
    require(Path(request['operations']).resolve() == Path(ops['root']).resolve(), 'Wrong operations root')
    observe_batch(request)
    prior = prior_contention(request)
    queue.mkdir(parents=True, exist_ok=False)
    atomic_save(queue/'request.json', request)
    state = dict(status='waiting_existing_batch', pid=os.getpid(), started=datetime.datetime.now().isoformat(),
                 child_pid=None, completed=[], full100_allowed=False, t64_started=False)
    atomic_save(queue/'state.json', state)
    lock = Path(read(common.ROOT/'handoff/team/server_config.json')['server_root'])/'.arch02_team_lock'
    prefix = queue.name
    try:
        batch = observe_batch(request)
        while batch is None:
            time.sleep(20)
            batch = observe_batch(request)
        state['batch_reference'] = batch
        atomic_save(queue/'state.json', state)
        script = str(common.ROOT/'workspaces/arch03/scripts/t80_server.py')
        def stage(name, suffix, extra=()):
            session = prefix+'_'+suffix
            command = [sys.executable, '-B', '-u', script, name, '--session', session]+list(extra)
            return run_child(command, common.ROOT/'runs'/session/('t80_'+name), 't80_'+name, queue, state, lock)
        if prior is None:
            stage('contention', 'contention', ['--cases', 'layer_01'])
        else:
            state['completed'].append(dict(stage='t80_contention', reference=prior,
                                           reused_identical_hardware=True))
            atomic_save(queue/'state.json', state)
        stage('sequence', 'sequence', ['--cases', 'layer_01', 'rounding'])
        synthesis = stage('synth', 'synth')
        synth_args = ['--synth-run', synthesis['run'], '--synth-summary-sha256', synthesis['sha256']]
        for name in ('timing_audit', 'drc_audit', 'structure'):
            stage(name, name, synth_args)
        gate = stage('gate', 'gate', synth_args)
        layers = ['layer_%02d'%n for n in range(1, 13)]
        activity = stage('saif', 'saif', ['--gate-run', gate['run'], '--gate-summary-sha256', gate['sha256'],
            '--saif-qualification-run', request['qualification_run'],
            '--saif-qualification-sha256', request['qualification_sha256'], '--cases']+layers)
        for number, layer in enumerate(layers, 1):
            stage('power', 'p%02d'%number, ['--saif-activity-run', activity['run'],
                '--saif-activity-sha256', activity['sha256'], '--cases', layer])
        bootstrap = 'import os,sys;os.environ["OPENBLAS_NUM_THREADS"]="1";sys.path[:0]='+repr([
            request['numpy_root'], str(Path(ops['root'])/'scripts'), str(common.ROOT/'workspaces/arch03/scripts')])+\
            ';import t80_precision_stage as s;s.main()'
        session = prefix+'_precision'
        command = [sys.executable, '-B', '-u', '-c', bootstrap, '--session', session,
            '--operations-manifest-sha256', request['operations_manifest_sha256'],
            '--archive', request['archive'], '--archive-sha256', request['archive_sha256'],
            '--dataset', request['dataset'], '--batch-run', batch['run'], '--batch-sha256', batch['sha256']]
        run_child(command, common.ROOT/'runs'/session/'t80_precision', 't80_precision', queue, state, lock)
        state.update(status='reports_ready_review_required', finished=datetime.datetime.now().isoformat())
    except BaseException as exc:
        state.update(status='failed', error=str(exc), finished=datetime.datetime.now().isoformat())
        raise
    finally:
        atomic_save(queue/'state.json', state)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request', required=True, type=Path)
    parser.add_argument('--request-sha256', required=True)
    parser.add_argument('--session', required=True)
    args = parser.parse_args()
    require(re.fullmatch('[A-Za-z0-9_-]{1,40}', args.session), 'Invalid fresh queue session')
    require(common.sha(args.request) == args.request_sha256, 'Queue request changed')
    execute(read(args.request), common.ROOT/'runs'/args.session)


if __name__ == '__main__':
    main()
