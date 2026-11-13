"""Export a completed T80/T64 queue under the original shared lock.

Uses the stage's own ASIC240, same-netlist PPA and fresh FLOAT join. No old
stage is run, no input is edited, and this export never grants G64 acceptance.
"""
import argparse
from collections import Counter
import importlib
import json
from pathlib import Path
import re


def require(value, message):
    if not value:
        raise ValueError(message)


def completed_references(state, stage):
    require(stage in ('T80', 'T64'), 'Unsupported transport stage')
    require(state['status'] == 'reports_ready_review_required' and state.get('child_pid') is None,
            'Wait for the original queue to finish successfully')
    prefix = stage.lower()+'_'
    expected = Counter({prefix+name:1 for name in
                        ('contention','sequence','synth','timing_audit','drc_audit','structure','gate','saif','precision')})
    expected[prefix+'power'] = 12
    require(Counter(row['stage'] for row in state['completed']) == expected,
            'Incomplete, repeated or unexpected queue stage set')
    grouped = {}
    for row in state['completed']:
        ref = row['reference']
        require(set(ref) == {'run','sha256'} and re.fullmatch('[a-f0-9]{64}', ref['sha256']),
                'Malformed completed stage identity')
        grouped.setdefault(row['stage'], []).append(ref)
    return grouped


def run(args):
    import server_run as common
    from n1_process import ProcessLedger, atomic_save, now
    name = args.stage.lower()
    paths = importlib.import_module(name+'_paths')
    report = importlib.import_module(name+'_report')
    precision = importlib.import_module(name+'_precision')
    queue_path = args.queue/'state.json'
    require(common.sha(queue_path) == args.queue_sha256, 'Queue state identity changed')
    queue = json.loads(queue_path.read_text())
    grouped = completed_references(queue, args.stage)
    request_path = args.queue/'request.json'
    original_request = json.loads(request_path.read_text())
    require(original_request['bundle'] == str(common.ROOT) and
            common.sha(common.ROOT/'manifest.json') == original_request['bundle_manifest_sha256'],
            'Original queue belongs to another runtime bundle')
    common.inputs()
    manifest = json.loads((common.ROOT/'manifest.json').read_text())
    require(manifest['architecture'] == 'arch03_'+name and
            manifest['row_lanes'] == {'T80':5,'T64':4}[args.stage], 'Wrong report bundle')
    cfg = paths.configure(json.loads((common.ROOT/'handoff/team/server_config.json').read_text()), common.ROOT,
                          args.runtime_root, args.runtime_manifest_sha256)
    paths.allowed_run(args.queue, cfg, 'Report queue')
    paths.allowed_run(args.asic_run, cfg, 'Report ASIC evidence')
    require(re.fullmatch('[A-Za-z0-9_-]{1,48}',args.session), 'Unsafe report session')
    session = common.ROOT/'runs'/args.session
    require(not session.exists(), 'Preserve previous report session')
    ledger = ProcessLedger(common,Path(cfg['server_root'])/'.arch02_team_lock',session)
    ledger.acquire()
    try:
        session.mkdir();ledger.initialize()
        output = session/(name+'_report')
        # The queue stage is an ASIC/FLOAT join; the exporter consumes its nested
        # fresh FLOAT audit, which has identity.json and the per-task SSE records.
        precision_stage_ref = grouped[name+'_precision'][0]
        joined = report.stage(precision_stage_ref, name+'_precision')
        require(joined.get('schema') == 'arch03-'+name+'-first20-precision-join-v1' and
                joined.get('fresh_float_reference_verified') is True and
                joined.get('tasks') == 240, 'Incomplete own-stage precision join')
        precision_ref = dict(joined['reference'], archive=original_request['archive'])
        require(precision_ref['source_mode'] == precision.SOURCE_MODE and
                precision_ref['archive_sha256'] == original_request['archive_sha256'],
                'Joined FLOAT provenance differs from the completed queue')
        request = dict(schema='arch03-'+name+'-report-request-v1',
                       asic=dict(run=str(args.asic_run),sha256=args.asic_sha256),
                       synthesis=grouped[name+'_synth'][0],gate=grouped[name+'_gate'][0],
                       activity=grouped[name+'_saif'][0],power=grouped[name+'_power'],
                       batch=queue['batch_reference'],precision=precision_ref,
                       history=[dict(queue=str(args.queue),state_sha256=args.queue_sha256,
                                     request_sha256=common.sha(request_path),
                                     precision_join_stage=precision_stage_ref)])
        atomic_save(session/'request.json',request)
        state = dict(status='exporting',stage=args.stage,started=now(),
                     queue_state_sha256=args.queue_sha256,source_sha256=common.sha(Path(__file__)),
                     system_power_verified=False,stage_accepted=False,g64_allowed=False)
        atomic_save(session/'state.json',state)
        try:
            result = report.build(request)
            result['request_sha256'] = common.sha(session/'request.json')
            report.write(result,output)
            state.update(status='exported_independent_review_required',
                         report_sha256=common.sha(output/'report.json'),
                         receipt_sha256=common.sha(output/'receipt.json'))
            atomic_save(session/'state.json',state)
            if args.unknown_inventory:
                import b0_saif_unknown_inventory as inventory
                state['status']='collecting_existing_unknown_activity';atomic_save(session/'state.json',state)
                inventory.collect(output/'report.json',state['report_sha256'],
                                  Path(cfg['server_root']),session/'unknown_inventory',inventory.LAYERS,
                                  path_validator=lambda path: paths.allowed_run(path,cfg,'Unknown inventory input'))
                state.update(status='report_and_unknown_inventory_ready_review_required',
                             unknown_inventory_sha256=common.sha(session/'unknown_inventory/summary.json'))
            require(common.sha(queue_path)==args.queue_sha256,'Original queue state changed during export')
            common.inputs();paths.recheck(cfg)
        except BaseException as exc:
            state.update(status='failed',error=str(exc));raise
        finally:
            state['finished']=now();atomic_save(session/'state.json',state)
    finally:
        ledger.release()
    print(args.stage+'_REPORT_READY stage_accepted=false G64_allowed=false',str(output),flush=True)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stage',choices=('T80','T64'),required=True)
    p.add_argument('--queue',type=Path,required=True)
    p.add_argument('--queue-sha256',required=True)
    p.add_argument('--asic-run',type=Path,required=True)
    p.add_argument('--asic-sha256',required=True)
    p.add_argument('--session',required=True)
    p.add_argument('--unknown-inventory',action='store_true')
    p.add_argument('--runtime-root',type=Path)
    p.add_argument('--runtime-manifest-sha256')
    run(p.parse_args())


if __name__=='__main__':main()
