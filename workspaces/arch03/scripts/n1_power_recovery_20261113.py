"""Continue only the ten unstarted N1 powers; preserve the failed original queue."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path('/tmp/s4_21usr_n1_20261113_0210')
BUNDLE = ROOT/'light-light126-n1-v4-20261113_045945-0f62e4120790'
OPS = ROOT/'light-light126-n1-precisionops02-20261113_090845'
QUEUE = BUNDLE/'runs/n1_acceptance01'
QUEUEOPS = ROOT/'light-light126-n1-queueops-20261113_091833'
REQUEST_SHA = '53028caf11703f75c159e19de43627f12cf7a63cde6e14b886c71937a424b944'
STATE_SHA = '4fe0eaf9d00d31293e99d3ee1f27ac945b1bedb014e0023aeb834d09d1ce2f2d'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text())
def require(ok, message):
    if not ok:raise ValueError(message)


def validate_prefix(state):
    require(state['status'] == 'failed' and state['current'] == 'power03'
            and state['child_pid'] is None and state['n2_allowed'] is False,
            'Original queue is not the expected terminal failure')
    require([(r['label'], r['stage']) for r in state['completed']] ==
            [('precision', 'n1_precision'), ('power01', 'n1_power'), ('power02', 'n1_power')],
            'Unexpected original completed prefix')


def main():
    require(sha(QUEUEOPS/'request.json') == REQUEST_SHA, 'Original request changed')
    require(read(QUEUE/'request.json') == read(QUEUEOPS/'request.json'), 'Saved request differs semantically')
    require(sha(QUEUE/'state.json') == STATE_SHA, 'Original failed state changed')
    old = read(QUEUE/'state.json');validate_prefix(old)
    require(not Path('/proc/%d' % old['pid']).exists(), 'Original queue is still alive')
    require(sha(QUEUEOPS/'n1_acceptance_queue.py') ==
            'c211b117ad1c9e117e989c66543f9bbd2a8b2ed2680772b47fa3a8e1e3ac5ef2', 'Queue tool changed')
    req = read(QUEUE/'request.json')
    sys.path[:0] = [str(QUEUEOPS), str(BUNDLE/'workspaces/arch03/scripts')]
    import n1_acceptance_queue as q
    require(q.common.ROOT == BUNDLE, 'Wrong frozen bundle imported')
    cfg = q.n1_paths.configure(read(BUNDLE/'handoff/team/server_config.json'), BUNDLE,
        req['runtime_root'], req['bundle_manifest_sha256'],
        [(req['synthesis_bundle'], req['synthesis_bundle_manifest_sha256'])])
    q.common.inputs()
    activity = q.observed_activity(req)
    require(activity == old['activity_reference'], 'Original activity reference changed')
    for row in old['completed']:
        actual, summary = q.stage_reference(row['reference']['run'], row['stage'])
        require(actual == row['reference'], 'Original passed child changed')
        if row['stage'] == 'n1_power':
            require(summary['case'] == 'layer_'+row['label'][-2:], 'Wrong prefix power case')
    for i in range(3, 13):
        require(not (BUNDLE/'runs'/('n1_acceptance02_p%02d' % i)).exists(), 'Preserve existing recovery session')
    require(sha(OPS/'manifest.json') == req['precision_operations_manifest_sha256'], 'Precision tools changed')
    for name, meta in read(OPS/'manifest.json')['files'].items():
        require(sha(OPS/name) == meta['sha256'], 'Precision member changed')
    output = OPS/'power_recovery01';output.mkdir()
    state = dict(schema='n1-power-recovery-v1', status='starting', pid=os.getpid(), started=q.now(),
        original_queue=str(QUEUE), original_state_sha256=STATE_SHA, original_request_sha256=REQUEST_SHA,
        runner_sha256=sha(__file__), completed=old['completed'], child_pid=None,
        activity_reference=activity, n2_allowed=False, system_power_verified=False)
    q.atomic_save(output/'state.json', state)
    lock = Path(cfg['server_root'])/'.arch02_team_lock'
    try:
        for i in range(3, 13):
            require(sha(QUEUE/'state.json') == STATE_SHA, 'Original state changed during recovery')
            require(q.observed_activity(req) == activity, 'Activity changed during recovery')
            session = 'n1_acceptance02_p%02d' % i
            cmd = [sys.executable, '-B', '-u', str(BUNDLE/'workspaces/arch03/scripts/n1_server.py'),
                'power', '--session', session, '--runtime-root', req['runtime_root'],
                '--runtime-manifest-sha256', req['bundle_manifest_sha256'],
                '--runtime-evidence', req['synthesis_bundle'], req['synthesis_bundle_manifest_sha256'],
                '--saif-activity-run', activity['run'], '--saif-activity-sha256', activity['sha256'],
                '--cases', 'layer_%02d' % i]
            q.run_child(cmd, output, state, 'power%02d' % i, BUNDLE/'runs'/session/'n1_power', 'n1_power', lock)
        state.update(status='numbers_ready_independent_review_required', finished=q.now())
    except BaseException as exc:
        state.update(status='failed', error=str(exc), finished=q.now())
        raise
    finally:
        q.atomic_save(output/'state.json', state)
    print('N1_RECOVERY_COMPLETE; original_failure_preserved; N2_allowed=false', flush=True)


if __name__ == '__main__':main()
