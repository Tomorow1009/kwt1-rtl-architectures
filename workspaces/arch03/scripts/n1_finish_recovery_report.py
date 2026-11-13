"""Join the preserved N1 prefix and a completed recovery; never grant N2."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import traceback

ROOT = Path('/tmp/s4_21usr_n1_20261113_0210')
BUNDLE = ROOT/'light-light126-n1-v4-20261113_045945-0f62e4120790'
OPS = ROOT/'light-light126-n1-precisionops02-20261113_090845'
QUEUE = BUNDLE/'runs/n1_acceptance01'
QUEUEOPS = ROOT/'light-light126-n1-queueops-20261113_091833'
ORIGINAL_STATE = '4fe0eaf9d00d31293e99d3ee1f27ac945b1bedb014e0023aeb834d09d1ce2f2d'
ORIGINAL_REQUEST = '53028caf11703f75c159e19de43627f12cf7a63cde6e14b886c71937a424b944'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text())
def require(ok, message):
    if not ok:raise ValueError(message)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--template', type=Path, required=True)
    p.add_argument('--template-sha256', required=True)
    p.add_argument('--recovery', type=Path, required=True)
    p.add_argument('--recovery-sha256', required=True)
    a = p.parse_args()
    require(sha(a.template) == a.template_sha256, 'Report template changed')
    require(sha(QUEUEOPS/'request.json') == ORIGINAL_REQUEST, 'Original request changed')
    cfg = read(QUEUEOPS/'request.json')
    require(read(QUEUE/'request.json') == cfg, 'Original saved request differs')
    require(sha(QUEUE/'state.json') == ORIGINAL_STATE, 'Original failed state changed')
    old = read(QUEUE/'state.json')
    require(sha(a.recovery/'state.json') == a.recovery_sha256, 'Recovery state changed')
    state = read(a.recovery/'state.json')
    require(state['status'] == 'numbers_ready_independent_review_required'
            and state['child_pid'] is None and state['n2_allowed'] is False, 'Recovery not complete')
    require(not Path('/proc/%d' % state['pid']).exists(), 'Recovery driver still alive')
    expected = [('precision', 'n1_precision')] + [('power%02d' % i, 'n1_power') for i in range(1, 13)]
    require([(x['label'], x['stage']) for x in state['completed']] == expected, 'Incomplete/duplicate stage set')
    require(state['completed'][:3] == old['completed'], 'Original passed prefix replaced')
    require(state['activity_reference'] == old['activity_reference'], 'Activity reference changed')
    require(not (Path(read(BUNDLE/'handoff/team/server_config.json')['server_root'])/'.arch02_team_lock').exists(),
            'Another formal stage is running')
    require(sha(OPS/'manifest.json') == cfg['precision_operations_manifest_sha256'], 'Precision OPS changed')
    for name, meta in read(OPS/'manifest.json')['files'].items():
        require(sha(OPS/name) == meta['sha256'], 'Precision OPS member changed')
    os.environ['OPENBLAS_NUM_THREADS'] = '1'
    sys.path[:0] = [cfg['numpy_root'], str(OPS/'scripts'), str(QUEUEOPS), str(BUNDLE/'workspaces/arch03/scripts')]
    import n1_report as report
    import n1_acceptance_queue as q
    request = read(a.template)
    request['activity'] = state['activity_reference']
    request['precision'] = dict(state['completed'][0]['reference'], source_mode='exact_original_npz_members',
                                archive=cfg['archive'], archive_sha256=cfg['archive_sha256'])
    request['power'] = [x['reference'] for x in state['completed'][1:]]
    for row in state['completed']:
        require(q.stage_reference(row['reference']['run'], row['stage'])[0] == row['reference'],
                'Completed stage identity differs')
    request['queue_provenance'] = dict(original_queue=str(QUEUE), original_state_sha256=ORIGINAL_STATE,
        recovery=str(a.recovery), recovery_state_sha256=a.recovery_sha256, original_failure_preserved=True)
    output = OPS/'final_report01'
    control = OPS/'final_export_control02'
    require(not output.exists() and not control.exists(), 'Preserve existing report/control')
    control.mkdir()
    q.atomic_save(control/'request.json', request)
    record = dict(schema='n1-recovery-report-state-v1', status='exporting', pid=os.getpid(), started=q.now(),
        request_sha256=sha(control/'request.json'), tool_sha256=sha(__file__), n2_allowed=False)
    q.atomic_save(control/'state.json', record)
    try:
        result = report.build(request)
        result['request_sha256'] = record['request_sha256']
        report.write(result, output)
        record.update(status='exported_independent_review_required', report_sha256=sha(output/'report.json'),
                      receipt_sha256=sha(output/'receipt.json'), finished=q.now())
        q.atomic_save(control/'state.json', record)
        sys.path.insert(0, str(OPS/'review_tools_04825e4'))
        import b0_saif_unknown_inventory as inv
        require(sha(inv.__file__) == '0a30965e732d350886f61ff0a31a41cffd60148434524a80320dd33d9ba90d96',
                'Wrong N1 unknown inventory tool')
        record.update(status='collecting_existing_unknown_activity')
        q.atomic_save(control/'state.json', record)
        inventory = inv.collect(output/'report.json', record['report_sha256'], ROOT, OPS/'n1_unknown_review01', inv.LAYERS)
        record.update(status='report_and_unknown_inventory_ready_review_required', finished=q.now(),
            unknown_summary_sha256=sha(OPS/'n1_unknown_review01/summary.json'))
    except BaseException as exc:
        record.update(status='failed', error=str(exc), finished=q.now())
        traceback.print_exc()
        raise
    finally:
        q.atomic_save(control/'state.json', record)
    print('N1_REPORT_AND_UNKNOWN_READY N2_allowed=false', flush=True)


if __name__ == '__main__':main()
