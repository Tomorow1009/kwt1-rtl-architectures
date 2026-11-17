"""Read-only completion and identity gate for G32 full100 evidence copying."""
import json
import math
from pathlib import Path
import re
from partition_synth_contract import require, digest

SCHEMA = 'arch03-g32-full100-runtime-copy-v1'
MANIFEST = '1577690aba585e473c7d0174ebca95618edc032e1184cf99a6d350bfa75d9052'


def read(p): return json.loads(Path(p).read_text())


def validate_scope(batch, precision):
    require(batch.get('schema') == 'arch03-g32-full100-batch-v6' and
        batch.get('status') == 'passed' and batch.get('samples') == 100 and
        batch.get('tasks') == 1200 and batch.get('checked_outputs') == 30412800 and
        batch.get('checked_totals') == 30412800 and batch.get('checked_saturation_flags') == 30412800 and
        batch.get('failed') == 0 and batch.get('compile_count') == 1 and
        batch.get('asic_cpu_verified') is True and batch.get('cpu_executed') is True and
        batch.get('global_FPGA_defined') is False and batch.get('row_lanes') == 2 and
        batch.get('transaction_metadata_depth') == 2 and batch.get('shift') == 10 and
        batch.get('layout_id') == 0x00100006 and batch.get('numeric_format_id') == 0x000e0c20,
        'Full100 archive requires its own complete ASIC/E203 batch')
    require(precision.get('schema') == 'arch03-g32-full100-precision-join-v1' and
        precision.get('status') == 'own_G32_ASIC1200_and_same_data_fresh_FLOAT_precision_verified' and
        precision.get('samples') == 100 and precision.get('tasks') == 1200 and
        precision.get('outputs') == precision.get('total_outputs') == 30412800 and
        precision.get('integer_bit_exact') is True and precision.get('fresh_float_reference_verified') is True and
        precision.get('float_reference_recomputed_in_precision_run') is True and
        precision.get('reference_error_metrics_reused_from_B0') is False and
        precision.get('official_precision_verified') is False and
        precision.get('internal_three_percent_layer_threshold_passed') is True,
        'Full100 archive requires its own fresh FLOAT precision join')
    for name in ('maximum_layer_nrmse_percent', 'maximum_task_nrmse_percent'):
        value = precision[name]
        require(type(value) in (int, float) and math.isfinite(value) and 0 <= value < 3,
                'Invalid internal precision result')
    layers = precision['layer_aggregate']
    require(len(layers) == 12 and all(r['tasks'] == 100 and r['within_limit'] for r in layers),
            'Incomplete full100 layer precision')


def evidence(req, bundle, owner_alive=None):
    if owner_alive is None: owner_alive = lambda pid: Path('/proc/%d' % pid).exists()
    bundle = Path(bundle).absolute()
    require(req['schema'] == SCHEMA and req['bundle_manifest_sha256'] == MANIFEST and
            digest(bundle/'manifest.json') == MANIFEST, 'Wrong isolated full100 bundle')
    queue = Path(req['queue']).absolute()
    require(queue == bundle/'runs/full100_02' and queue.resolve() == queue,
            'Only the explicitly approved new full100 queue is in scope')
    inputs = {}

    def checked(path, expected=None):
        path = Path(path)
        value = digest(path)
        require(expected is None or value == expected, 'Changed full100 evidence: '+str(path))
        inputs[str(path)] = value
        return read(path)

    state = checked(queue/'state.json', req['state_sha256'])
    require(state.get('schema') == 'arch03-g32-full100-queue-v1' and
        state.get('status') == 'full100_and_precision_passed_archive_pending' and
        state.get('finished') and state.get('current_run') is None and
        type(state.get('pid')) is int and not owner_alive(state['pid']) and
        state.get('full100_authorized') is True and state.get('hardware_changed') is False,
        'Full100 owner must have completed and exited')
    request = checked(queue/'request.json')
    require(request == checked(bundle.parent/'full100_request.json') and
        request['schema'] == 'arch03-g32-full100-queue-v1' and request['full100_authorized'] is True and
        request['bundle'] == str(bundle) and request['bundle_manifest_sha256'] == MANIFEST and
        request['queue_sha256'] == digest(bundle/'workspaces/arch03/scripts/g32_full100_queue.py'),
        'Full100 request or queue source changed')
    frozen = checked(queue/'frozen_copy.json')
    require(frozen['hardware_firmware_monitors_codec_unchanged'] is True and frozen['frozen_files'] == 1059,
            'Frozen hardware copy proof missing')
    original = Path(frozen['frozen_bundle'])/'manifest.json'
    original_manifest = checked(original, frozen['frozen_manifest_sha256'])
    manifest = checked(bundle/'manifest.json', MANIFEST)
    for rel, want in original_manifest['files'].items():
        require(manifest['files'][rel] == want == digest(bundle/rel), 'Changed frozen input '+rel)
    for rel in frozen['additional_tools']:
        require(digest(bundle/rel) == manifest['files'][rel], 'Changed full100 tool')
    rows = state['completed']
    require([r['stage'] for r in rows] == ['batch100', 'precision100'], 'Incomplete stage order')
    refs = {}
    reports = {}
    for row in rows:
        name = row['stage']; run = queue.with_name(queue.name+'_'+name)/('g32_'+name)
        ref = row['reference']
        require(ref == state['references'][name] and ref['run'] == str(run), 'Wrong stage path')
        reports[name] = checked(run/'summary.json', ref['sha256'])
        local = checked(run.parent/'state.json')['stages']['g32_'+name]
        require(local['status'] == 'passed' and local.get('finished') and
                local['summary_sha256'] == ref['sha256'], 'Stage has not completed')
        refs[name] = dict(ref)
    batch, precision = reports['batch100'], reports['precision100']
    validate_scope(batch, precision)
    require(precision['batch']['batch_summary_sha256'] == refs['batch100']['sha256'] and
        precision['batch_identity_sha256'] == batch['batch_identity_sha256'], 'Precision belongs to another batch')
    float_run = Path(refs['precision100']['run'])/'float100'
    require(Path(precision['reference']['run']).resolve() == float_run.resolve(), 'Wrong fresh FLOAT directory')
    numeric = checked(float_run/'summary.json', precision['reference']['sha256'])
    checked(float_run/'identity.json', numeric['identity_sha256'])
    require(numeric['status'] == 'passed' and numeric['samples'] == 100 and numeric['tasks'] == 1200 and
        numeric['outputs'] == 30412800 and numeric['integer_mismatches'] == numeric['hex_byte_mismatches'] == 0 and
        numeric['max_layer_nrmse_percent'] == precision['maximum_layer_nrmse_percent'] and
        numeric['max_task_nrmse_percent'] == precision['maximum_task_nrmse_percent'] and
        numeric['layer_aggregate'] == precision['layer_aggregate'], 'Fresh FLOAT artifact differs from join')
    run = Path(refs['batch100']['run'])
    identity = checked(run/'batch_identity.json', batch['batch_identity_sha256'])
    require(identity['tasks'] == 1200 and identity['samples'] == 100 and
        identity['expected_outputs'] == 30412800 and identity['global_FPGA_defined'] is False and
        identity['cold_task_boot'] is True and identity['cross_task_prefetch'] is False and
        identity['large_waveforms'] is False, 'Wrong cold-task contract')
    build = checked(run/'g32_build_contract.json', identity['build_contract_sha256'])
    from g32_soc import verify_frozen
    verify_frozen(build)
    expected_keys = ['sample_%03d_layer_%02d' % (s, l) for s in range(1, 101) for l in range(1, 13)]
    require([row['key'] for row in batch['cases']] == expected_keys, 'Missing/reordered task receipts')
    saturated = 0
    for row in batch['cases']:
        path = run/'cases'/row['key']/'receipt.json'
        require((run/row['receipt']).resolve() == path.resolve() and
                row['outputs'] == row['total_outputs'] == 25344, 'Wrong task capture scope')
        result = checked(path, row['receipt_sha256'])
        require(result['status'] == 'passed' and result['asic_cpu_verified'] is True and
            result['batch_identity_sha256'] == batch['batch_identity_sha256'] and
            result['capture']['total_checked'] is True and result['capture']['mismatches'] == 0 and
            result['capture']['capture_sha256'] == row['capture_sha256'] == digest(path.parent/'task.csv'),
            'Task capture identity differs')
        saturated += result['capture']['saturated']
    require(saturated == precision['saturation_count'], 'Saturation aggregate differs')
    children = sorted((queue/'process_ledger').glob('child_*.json'))
    require(len(children) == 1201, 'Expected one compile and 1200 actual CPU executions')
    for path in children:
        child = checked(path)
        require(child['driver_pid'] == state['pid'] and child['bundle'] == str(bundle) and
            child['session'] == queue.name and child['status'] == 'exited' and
            child['wait_completed'] is True and child['returncode'] == 0 and
            child['call_status'] == 'passed' and not owner_alive(child['pid']), 'Unreaped or failed child')
    failed = checked(bundle/'runs/full100_01/state.json')
    require(failed['status'] == 'failed' and failed['completed'] == [] and failed.get('finished') and
        'No space left on device' in failed['error'] and not owner_alive(failed['pid']),
        'Initial lock-space failure must remain unchanged and exited')
    require(all(digest(p) == h for p, h in inputs.items()), 'Evidence changed during archive admission')
    return dict(schema='arch03-g32-full100-archive-admission-v1', queue=str(queue),
        inputs=inputs, references=refs, samples=100, tasks=1200, checked_outputs=30412800,
        checked_totals=30412800, children_exited=len(children), prior_failure_preserved=True,
        hardware_changed=False, archive_implies_acceptance=False, official_precision_verified=False)
