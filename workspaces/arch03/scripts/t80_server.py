"""Independent T80 initial ASIC/synthesis stages under the existing shared team lock; Python 3.6."""
import argparse
import datetime
import json
import os
from pathlib import Path
import re
import shutil
import socket
import server_run as common
import t80_paths
import n1_process
from n1_process import ProcessLedger


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('stage', choices=('status', 'soc', 'build', 'synth', 'batch20'))
    p.add_argument('--session', required=True)
    p.add_argument('--platform', type=Path, default=Path('/storage2/2026contest/server4/s4_21usr/Desktop/e203_hbirdv2-master'))
    p.add_argument('--cases', nargs='+', default=['extremes', 'rounding'] + ['layer_%02d' % n for n in range(1, 13)])
    p.add_argument('--firmware-root', type=Path)
    p.add_argument('--dataset', type=Path)
    p.add_argument('--runtime-root',type=Path)
    p.add_argument('--runtime-manifest-sha256')
    p.add_argument('--runtime-evidence',nargs=2,action='append',default=[],metavar=('BUNDLE','MANIFEST_SHA256'),
                   help='Explicit same-private-root sibling bundle identity; may be repeated')
    a = p.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', a.session):
        raise ValueError('Invalid unique T80 session')
    if len(a.cases) != len(set(a.cases)):
        raise ValueError('Duplicate cases would overwrite evidence')
    cfg = json.loads((common.ROOT/'handoff/team/server_config.json').read_text())
    cfg = t80_paths.configure(cfg,common.ROOT,a.runtime_root,a.runtime_manifest_sha256,a.runtime_evidence)
    session = common.ROOT/'runs'/a.session
    lock = Path(cfg['server_root'])/'.arch02_team_lock'
    if a.stage == 'status':
        print((session/'state.json').read_text() if (session/'state.json').exists() else 'SESSION_NOT_STARTED')
        if lock.exists():
            print('TEAM_LOCK', (lock/'owner.json').read_text() if (lock/'owner.json').is_file() else 'incomplete lock')
        print('FREE_BYTES', shutil.disk_usage(str(common.ROOT)).free)
        return
    if session.exists():
        raise ValueError('T80 uses a fresh session for each stage; preserve all previous artifacts')
    if a.firmware_root is not None and a.stage not in ('soc','build'):
        raise ValueError('Firmware override only supports CPU compile/run')
    if a.stage == 'batch20' and a.dataset is None:
        raise ValueError('batch20 requires the pinned DATA100 source; only the first20 are executed')
    packaged = common.inputs()
    process_relative = 'workspaces/arch03/scripts/n1_process.py'
    process_file = common.ROOT/process_relative
    if (Path(n1_process.__file__).resolve() != process_file.resolve() or
            packaged['files'].get(process_relative) != common.sha(process_file)):
        raise ValueError('N1 process ledger dependency is absent or differs from this frozen bundle')
    t80_paths.recheck(cfg)
    # Per-stage budget, 20% growth margin plus 2 GiB shared-server reserve.
    # The 1200-task runner additionally budgets all remaining case artifacts.
    expected_gib = 4 if a.stage == 'synth' else 1
    required_bytes = int(expected_gib*1024**3*1.2) + 2*1024**3
    free_bytes = shutil.disk_usage(str(common.ROOT)).free
    if free_bytes < required_bytes:
        raise ValueError('Insufficient stage space: free=%d required=%d' % (free_bytes, required_bytes))
    processes = ProcessLedger(common,lock,session)
    processes.acquire()  # Initial owner only; later child updates are stage-local.
    try:
        stage_name = 't80_' + a.stage
        run = session/stage_name
        run.mkdir(parents=True, exist_ok=False)
        if cfg.get('runtime_roots'):
            t80_paths.allowed_run(run,cfg,'T80 output')
            common.save(run/'runtime_storage_receipt.json',t80_paths.receipt(cfg))
        processes.initialize()
        common.save(run/'storage_preflight.json',dict(free_bytes=free_bytes,required_bytes=required_bytes,estimated_stage_bytes=expected_gib*1024**3,margin=1.2,reserve_bytes=2*1024**3))
        record = dict(status='running', pid=os.getpid(), started=datetime.datetime.now().isoformat(), run=str(run))
        state = dict(schema='arch03-t80-server-state-v1', stages={stage_name: record})
        common.save(session/'state.json', state)
        try:
            if a.stage in ('soc', 'build'):
                from t80_soc import verify
                report = verify(cfg, run, a.platform, a.cases, processes.call, firmware=a.firmware_root, compile_only=a.stage == 'build')
            elif a.stage == 'batch20':
                from t80_batch import verify
                report = verify(cfg, run, a.platform, a.dataset, processes.call)
            else:
                from t80_synth import synth
                common.vendor(cfg, run)
                report = synth(cfg, run, a.platform, processes.call)
            common.inputs()
            t80_paths.recheck(cfg)
            if cfg.get('runtime_roots'):
                report['runtime_storage']=dict(receipt_sha256=common.sha(run/'runtime_storage_receipt.json'),
                    durable_archive_required=True,temporary_storage_is_final_delivery=False)
            common.save(run/'summary.json', report)
            record.update(status='passed', summary_sha256=common.sha(run/'summary.json'))
        except BaseException as exc:
            record.update(status='failed', error=str(exc))
            raise
        finally:
            record['finished'] = datetime.datetime.now().isoformat()
            common.save(session/'state.json', state)
        print('ARCH03_T80_STAGE_PASS', a.stage, run, flush=True)
    finally:
        processes.release()


if __name__ == '__main__':
    main()
