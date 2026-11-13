"""Immutable T64 stages under the existing shared team lock; Python 3.6."""
import argparse
import datetime
import json
import os
from pathlib import Path
import re
import shutil
import socket
import server_run as common
import t64_paths
import n1_process
from n1_process import ProcessLedger


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('stage', choices=('status', 'soc', 'build', 'batch20', 'synth', 'contention', 'sequence', 'gate', 'timing_audit', 'drc_audit', 'structure', 'saif', 'power'))
    p.add_argument('--session', required=True)
    p.add_argument('--platform', type=Path, default=Path('/storage2/2026contest/server4/s4_21usr/Desktop/e203_hbirdv2-master'))
    p.add_argument('--cases', nargs='+', default=['extremes', 'rounding'] + ['layer_%02d' % n for n in range(1, 13)])
    p.add_argument('--dataset', type=Path)
    p.add_argument('--firmware-root', type=Path)
    p.add_argument('--synth-run', type=Path)
    p.add_argument('--synth-summary-sha256')
    p.add_argument('--gate-run', type=Path)
    p.add_argument('--gate-summary-sha256')
    p.add_argument('--saif-qualification-run', type=Path)
    p.add_argument('--saif-qualification-sha256')
    p.add_argument('--saif-activity-run', type=Path)
    p.add_argument('--saif-activity-sha256')
    p.add_argument('--runtime-root',type=Path)
    p.add_argument('--runtime-manifest-sha256')
    p.add_argument('--runtime-evidence',nargs=2,action='append',default=[],metavar=('BUNDLE','MANIFEST_SHA256'),
                   help='Explicit same-private-root sibling bundle identity; may be repeated')
    a = p.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', a.session):
        raise ValueError('Invalid unique T64 session')
    if len(a.cases) != len(set(a.cases)):
        raise ValueError('Duplicate cases would overwrite evidence')
    cfg = json.loads((common.ROOT/'handoff/team/server_config.json').read_text())
    cfg = t64_paths.configure(cfg,common.ROOT,a.runtime_root,a.runtime_manifest_sha256,a.runtime_evidence)
    session = common.ROOT/'runs'/a.session
    lock = Path(cfg['server_root'])/'.arch02_team_lock'
    if a.stage == 'status':
        print((session/'state.json').read_text() if (session/'state.json').exists() else 'SESSION_NOT_STARTED')
        if lock.exists():
            print('TEAM_LOCK', (lock/'owner.json').read_text() if (lock/'owner.json').is_file() else 'incomplete lock')
        print('FREE_BYTES', shutil.disk_usage(str(common.ROOT)).free)
        return
    if session.exists():
        raise ValueError('N1 uses a fresh session for each stage; preserve all previous artifacts')
    if a.stage == 'batch20' and a.dataset is None:
        raise ValueError('Batch needs the explicit pinned DATA100 directory')
    if a.firmware_root is not None and a.stage not in ('soc', 'build', 'gate', 'contention', 'sequence'):
        raise ValueError('Firmware override only supports CPU compile/run')
    for selected, path, digest, allowed in (
        ('synthesis', a.synth_run, a.synth_summary_sha256, ('gate', 'timing_audit', 'drc_audit', 'structure')),
        ('gate', a.gate_run, a.gate_summary_sha256, ('saif',)),
        ('SAIF qualification', a.saif_qualification_run, a.saif_qualification_sha256, ('saif',)),
        ('SAIF activity', a.saif_activity_run, a.saif_activity_sha256, ('power',))):
        if a.stage in allowed:
            if path is None or digest is None or not re.fullmatch('[a-f0-9]{64}', digest):
                raise ValueError('Stage needs explicit %s directory and SHA256' % selected)
        elif path is not None or digest is not None:
            raise ValueError('Unexpected %s selection for stage' % selected)
    if a.stage == 'power' and len(a.cases) != 1:
        raise ValueError('Each N1 power stage covers exactly one fixed performance task')
    packaged = common.inputs()
    process_relative = 'workspaces/arch03/scripts/n1_process.py'
    process_file = common.ROOT/process_relative
    if (Path(n1_process.__file__).resolve() != process_file.resolve() or
            packaged['files'].get(process_relative) != common.sha(process_file)):
        raise ValueError('N1 process ledger dependency is absent or differs from this frozen bundle')
    t64_paths.recheck(cfg)
    # Per-stage budget, 20% growth margin plus 2 GiB shared-server reserve.
    # The 240-task runner additionally budgets all remaining case artifacts.
    expected_gib = 4 if a.stage in ('synth', 'saif') else 1
    required_bytes = int(expected_gib*1024**3*1.2) + 2*1024**3
    free_bytes = shutil.disk_usage(str(common.ROOT)).free
    if free_bytes < required_bytes:
        raise ValueError('Insufficient stage space: free=%d required=%d' % (free_bytes, required_bytes))
    processes = ProcessLedger(common,lock,session)
    processes.acquire()  # Initial owner only; later child updates are stage-local.
    try:
        stage_name = 't64_' + a.stage
        run = session/stage_name
        run.mkdir(parents=True, exist_ok=False)
        if cfg.get('runtime_roots'):
            t64_paths.allowed_run(run,cfg,'N1 output')
            common.save(run/'runtime_storage_receipt.json',t64_paths.receipt(cfg))
        processes.initialize()
        common.save(run/'storage_preflight.json',dict(free_bytes=free_bytes,required_bytes=required_bytes,estimated_stage_bytes=expected_gib*1024**3,margin=1.2,reserve_bytes=2*1024**3))
        record = dict(status='running', pid=os.getpid(), started=datetime.datetime.now().isoformat(), run=str(run))
        state = dict(schema='arch03-t64-server-state-v1', stages={stage_name: record})
        common.save(session/'state.json', state)
        try:
            if a.stage in ('soc', 'build'):
                from t64_soc import verify
                report = verify(cfg, run, a.platform, a.cases, processes.call, firmware=a.firmware_root, compile_only=a.stage == 'build')
            elif a.stage == 'contention':
                from t64_contention import verify
                report = verify(cfg, run, a.platform, a.cases, processes.call, a.firmware_root)
            elif a.stage == 'sequence':
                from t64_sequence_soc import verify
                report = verify(cfg, run, a.platform, a.cases, processes.call, a.firmware_root)
            elif a.stage == 'batch20':
                from t64_batch import verify
                report = verify(cfg, run, a.platform, a.dataset, processes.call)
            elif a.stage == 'gate':
                from t64_gate import verify
                report = verify(cfg, run, a.synth_run, a.synth_summary_sha256, a.cases, processes.call, (), a.firmware_root)
            elif a.stage == 'timing_audit':
                from t64_timing_audit import audit
                report = audit(cfg, run, a.synth_run, a.synth_summary_sha256, processes.call)
            elif a.stage == 'drc_audit':
                from t64_drc_audit import audit
                report = audit(cfg, run, a.synth_run, a.synth_summary_sha256, processes.call)
            elif a.stage == 'structure':
                from t64_structure import audit
                t64_paths.allowed_run(a.synth_run,cfg,'N1 structural synthesis')
                report = audit(a.synth_run,a.synth_summary_sha256)
            elif a.stage == 'saif':
                from t64_saif import verify
                report = verify(cfg, run, a.gate_run, a.gate_summary_sha256, a.saif_qualification_run, a.saif_qualification_sha256, a.cases, processes.call)
            elif a.stage == 'power':
                from t64_power import estimate
                report = estimate(cfg, run, a.saif_activity_run, a.saif_activity_sha256, a.cases[0], processes.call)
            else:
                from t64_synth import synth
                common.vendor(cfg, run)
                report = synth(cfg, run, a.platform, processes.call)
            common.inputs()
            t64_paths.recheck(cfg)
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
        print('ARCH03_T64_STAGE_PASS', a.stage, run, flush=True)
    finally:
        processes.release()


if __name__ == '__main__':
    main()
