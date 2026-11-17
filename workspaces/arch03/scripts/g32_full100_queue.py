"""Explicitly approved full100 addendum; frozen G32 hardware is unchanged.

Run only in a new manifest-pinned private bundle. The old bundle is read-only.
One ASIC compilation, 1200 cold CPU tasks, then fresh original FLOAT precision.
Uses the original team lock and child ledger; never resumes a partial batch.
"""
import argparse
import datetime
import json
import os
from pathlib import Path
import re
import sys

import server_run as common
import g32_paths as paths
from n1_process import ProcessLedger, atomic_save
from partition_synth_contract import require

SCHEMA = 'arch03-g32-full100-queue-v1'
FROZEN_MANIFEST = '3524e2726880684c1c5681ef90da3a1ca41d78daf20d0df5b648e633b6e42f4a'
FLOAT_SHA = '5df11251821d2d36e85e07c8a171195d9d2ed2d4084a979519d23f6df7d683e2'
ADDITIONS = tuple('workspaces/arch03/scripts/'+s for s in (
    'g32_full100_batch.py', 'g32_full100_float.py',
    'g32_full100_precision_join.py', 'g32_full100_queue.py'))


def read(path): return json.loads(Path(path).read_text())
def now(): return datetime.datetime.now().isoformat()


def frozen_copy(request):
    """Every original payload byte, including all firmware and monitors, matches."""
    old = Path(request['frozen_bundle']).resolve()
    require(old != common.ROOT and old not in common.ROOT.parents and
            common.ROOT not in old.parents, 'Full100 needs an independent root')
    require(common.sha(old/'manifest.json') == FROZEN_MANIFEST,
            'Frozen G32 manifest differs')
    manifest = read(old/'manifest.json'); current = common.inputs()
    require(set(current['files']) == set(manifest['files']) | set(ADDITIONS),
            'Only explicit full100 tools may be added')
    require(not set(ADDITIONS) & set(manifest['files']), 'Cannot replace frozen tools')
    for rel, digest in manifest['files'].items():
        require(current['files'][rel] == digest and common.sha(old/rel) == digest and
                common.sha(common.ROOT/rel) == digest, 'Frozen payload differs: '+rel)
    return dict(frozen_bundle=str(old), frozen_manifest_sha256=FROZEN_MANIFEST,
                frozen_files=len(manifest['files']), additional_tools=list(ADDITIONS),
                hardware_firmware_monitors_codec_unchanged=True)


def execute(request, queue):
    require(request['schema'] == SCHEMA and request['full100_authorized'] is True and
            request['samples'] == 100 and request['tasks'] == 1200,
            'Explicit full100 request required')
    require(request['bundle'] == str(common.ROOT) and
            request['queue_sha256'] == common.sha(Path(__file__)), 'Queue identity differs')
    cfg = paths.configure(read(common.ROOT/'handoff/team/server_config.json'), common.ROOT,
        Path(request['runtime_root']), request['bundle_manifest_sha256'])
    proof = frozen_copy(request)
    require(request['float_archive_sha256'] == FLOAT_SHA, 'Wrong recovered float source')
    # Establish NumPy before the long hardware job, not after it has finished.
    from g32_precision_recovery import numeric_runtime
    runtime = numeric_runtime()
    require(common.sha(Path(request['float_archive'])) == FLOAT_SHA, 'Float archive changed')
    import g32_full100_batch as batch
    require(not queue.exists(), 'Never resume or overwrite a prior full100 queue')
    queue.mkdir(parents=True)
    atomic_save(queue/'request.json', request)
    atomic_save(queue/'frozen_copy.json', proof)
    atomic_save(queue/'numeric_runtime.json', runtime)
    batch.storage_guard(queue, 1200)
    state = dict(schema=SCHEMA, status='acquiring_lock', pid=os.getpid(), started=now(),
        full100_authorized=True, samples=100, tasks=1200, expected_outputs=30412800,
        hardware_changed=False, completed=[], official_precision_verified=False)
    atomic_save(queue/'state.json', state)
    ledger = ProcessLedger(common, Path(cfg['server_root'])/'.arch02_team_lock', queue)
    refs = {}
    try:
        ledger.acquire(); ledger.initialize()
        for name in ('batch100', 'precision100'):
            session = queue.with_name(queue.name+'_'+name)
            run = session/('g32_'+name)
            require(not session.exists(), 'Preserve existing stage')
            run.mkdir(parents=True)
            ledger.register_stage_session(session)
            paths.allowed_run(run, cfg)
            common.save(run/'runtime_storage_receipt.json', paths.receipt(cfg))
            row = dict(status='running', pid=os.getpid(), started=now(), run=str(run))
            stage_state = dict(schema=SCHEMA, stages={'g32_'+name:row})
            atomic_save(session/'state.json', stage_state)
            state.update(status='running', stage=name, current_run=str(run))
            atomic_save(queue/'state.json', state)
            try:
                if name == 'batch100':
                    report = batch.verify(cfg, run, Path(request['platform']),
                        Path(request['dataset']), ledger.call)
                else:
                    from g32_full100_precision_join import verify
                    ref = refs['batch100']
                    report = verify(cfg, run, Path(ref['run']), ref['sha256'],
                        Path(request['float_archive']), FLOAT_SHA, Path(request['dataset']))
                require(frozen_copy(request) == proof, 'Frozen sources changed during run')
                paths.recheck(cfg); ledger.check_owner()
                common.save(run/'summary.json', report)
                row.update(status='passed', summary_sha256=common.sha(run/'summary.json'))
            except BaseException as error:
                row.update(status='failed', error=str(error)); raise
            finally:
                row['finished'] = now(); atomic_save(session/'state.json', stage_state)
            refs[name] = dict(run=str(run), sha256=row['summary_sha256'])
            state['completed'].append(dict(stage=name, reference=refs[name]))
            atomic_save(queue/'state.json', state)
            print('G32_FULL100_STAGE_PASS', name, refs[name]['sha256'], flush=True)
        state.update(status='full100_and_precision_passed_archive_pending',
            current_run=None, finished=now(), references=refs)
    except BaseException as error:
        state.update(status='failed', error=str(error), finished=now()); raise
    finally:
        try:
            if ledger.acquired: ledger.release()
        except BaseException as error:
            state.update(status='failed', error='Lock release: '+str(error), finished=now()); raise
        finally:
            atomic_save(queue/'state.json', state)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request', required=True, type=Path)
    parser.add_argument('--request-sha256', required=True)
    parser.add_argument('--session', required=True)
    args = parser.parse_args()
    require(re.fullmatch('[A-Za-z0-9_-]{1,40}', args.session), 'Invalid session')
    require(common.sha(args.request) == args.request_sha256, 'Request changed')
    execute(read(args.request), common.ROOT/'runs'/args.session)


if __name__ == '__main__': main()
