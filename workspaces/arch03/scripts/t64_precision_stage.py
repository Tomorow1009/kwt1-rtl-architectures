"""Fresh first20 FLOAT and actual T64 ASIC join under the existing team lock."""
import argparse
import datetime
import json
import os
from pathlib import Path
import re
import shutil

import server_run as common
import t64_paths
import t64_precision as numeric
import t64_precision_join as join
from n1_process import ProcessLedger


def operations_identity(expected):
    root = Path(__file__).resolve().parent.parent
    path = root/'manifest.json'
    join.require(re.fullmatch('[a-f0-9]{64}', expected or '') and common.sha(path) == expected,
                 'T64 precision operations manifest changed')
    files = join.read(path)['files']
    join.require(set(files) == {'scripts/t64_precision_stage.py', 'scripts/t64_precision_join.py',
                               'scripts/t64_finish_queue.py'},
                 'Unexpected precision operations members')
    for relative, record in files.items():
        source = root/relative
        join.require(not source.is_symlink() and source.stat().st_size == record['bytes'] and
                     common.sha(source) == record['sha256'], 'Changed precision operator: '+relative)
    join.require(Path(join.__file__).resolve() == root/'scripts/t64_precision_join.py',
                 'Wrong precision join import')
    return dict(root=str(root), manifest_sha256=expected, files=files)


def execute(cfg, session, archive, archive_sha, dataset, batch_run, batch_sha, ops):
    session, batch_run = Path(session), Path(batch_run)
    join.require(not session.exists(), 'Preserve existing precision session')
    state = join.read(batch_run.parent/'state.json')['stages']['t64_batch20']
    join.require(state['status'] == 'passed' and
                 state['summary_sha256'] == batch_sha == common.sha(batch_run/'summary.json'),
                 'Complete matching T64 first20 batch required')
    ledger = ProcessLedger(common, Path(cfg['server_root'])/'.arch02_team_lock', session)
    ledger.acquire()
    try:
        session.mkdir()
        ledger.initialize()
        run = session/'t64_precision'
        run.mkdir()
        record = dict(status='running', pid=os.getpid(), started=datetime.datetime.now().isoformat(), run=str(run))
        state = dict(schema='arch03-t64-server-state-v1', stages={'t64_precision': record})
        common.save(session/'state.json', state)
        try:
            result = numeric._audit(archive, archive_sha, dataset, run/'float20')
            join.require(result['status'] == 'passed' and result['internal_precision_verified'],
                         'Fresh first20 FLOAT precision failed')
            batch = join.audit_batch(batch_run, join.read(batch_run/'summary.json'))
            ref = dict(run=str(run/'float20'), sha256=common.sha(run/'float20/summary.json'),
                       source_mode=numeric.SOURCE_MODE, archive_sha256=archive_sha)
            report = join.audit_precision(ref, batch)
            report.update(schema='arch03-t64-first20-precision-join-v1', batch=batch,
                          auditor_sha256=common.sha(Path(join.__file__)), timing_verified=False,
                          system_power_verified=False, operations=ops)
            common.inputs()
            t64_paths.recheck(cfg)
            join.require(common.sha(batch_run/'summary.json') == batch_sha and
                         operations_identity(ops['manifest_sha256']) == ops, 'Precision inputs changed')
            common.save(run/'summary.json', report)
            record.update(status='passed', summary_sha256=common.sha(run/'summary.json'))
        except BaseException as exc:
            record.update(status='failed', error=str(exc))
            raise
        finally:
            record['finished'] = datetime.datetime.now().isoformat()
            common.save(session/'state.json', state)
        print('T64_FIRST20_PRECISION_STAGE_PASS tasks=240 outputs=6082560', flush=True)
        return report
    finally:
        ledger.release()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('archive', 'dataset', 'batch-run'):
        p.add_argument('--'+name, type=Path, required=True)
    for name in ('session', 'archive-sha256', 'batch-sha256', 'operations-manifest-sha256'):
        p.add_argument('--'+name, required=True)
    p.add_argument('--runtime-root', type=Path)
    p.add_argument('--runtime-manifest-sha256')
    a = p.parse_args()
    join.require(re.fullmatch('[A-Za-z0-9_-]{1,64}', a.session), 'Invalid new T64 session')
    ops = operations_identity(a.operations_manifest_sha256)
    cfg = t64_paths.configure(join.read(common.ROOT/'handoff/team/server_config.json'), common.ROOT,
                             a.runtime_root, a.runtime_manifest_sha256)
    t64_paths.allowed_run(a.batch_run, cfg)
    packaged = common.inputs()
    for module in (numeric, __import__('n1_data'), __import__('n1_precision'), __import__('t64_soc')):
        path = Path(module.__file__).resolve()
        join.require(packaged['files'].get(path.relative_to(common.ROOT).as_posix()) == common.sha(path),
                     'Unfrozen precision dependency')
    join.require(shutil.disk_usage(str(common.ROOT)).free >= int(3.2*1024**3), 'Insufficient space')
    execute(cfg, common.ROOT/'runs'/a.session, a.archive, a.archive_sha256, a.dataset,
            a.batch_run, a.batch_sha256, ops)


if __name__ == '__main__':
    main()
