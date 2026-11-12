"""Immutable N1 stages under the existing shared team lock; Python 3.6."""
import argparse
import datetime
import json
import os
from pathlib import Path
import re
import shutil
import socket
import server_run as common


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('stage', choices=('status', 'soc', 'build', 'batch', 'synth', 'contention', 'sequence', 'gate', 'timing_audit', 'saif', 'power'))
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
    a = p.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', a.session):
        raise ValueError('Invalid unique N1 session')
    if len(a.cases) != len(set(a.cases)):
        raise ValueError('Duplicate cases would overwrite evidence')
    cfg = json.loads((common.ROOT/'handoff/team/server_config.json').read_text())
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
    if a.stage == 'batch' and a.dataset is None:
        raise ValueError('Batch needs the explicit pinned DATA100 directory')
    if a.firmware_root is not None and a.stage not in ('soc', 'build', 'contention', 'sequence', 'gate'):
        raise ValueError('Firmware override only supports CPU compile/run')
    for selected, path, digest, allowed in (
        ('synthesis', a.synth_run, a.synth_summary_sha256, ('gate', 'timing_audit')),
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
    common.inputs()
    # Per-stage budget, 20% growth margin plus 2 GiB shared-server reserve.
    # The 1200-task runner additionally budgets all remaining case artifacts.
    expected_gib = 4 if a.stage in ('synth', 'saif') else 1
    required_bytes = int(expected_gib*1024**3*1.2) + 2*1024**3
    free_bytes = shutil.disk_usage(str(common.ROOT)).free
    if free_bytes < required_bytes:
        raise ValueError('Insufficient stage space: free=%d required=%d' % (free_bytes, required_bytes))
    lock.mkdir()  # Never clear, steal, or infer ownership of a pre-existing lock.
    common.LOCK = lock
    owner = dict(pid=os.getpid(), host=socket.gethostname(), bundle=str(common.ROOT), session=a.session)
    common.save(lock/'owner.json', owner)
    try:
        stage_name = 'n1_' + a.stage
        run = session/stage_name
        run.mkdir(parents=True, exist_ok=False)
        common.save(run/'storage_preflight.json',dict(free_bytes=free_bytes,required_bytes=required_bytes,estimated_stage_bytes=expected_gib*1024**3,margin=1.2,reserve_bytes=2*1024**3))
        record = dict(status='running', pid=os.getpid(), started=datetime.datetime.now().isoformat(), run=str(run))
        state = dict(schema='arch03-n1-server-state-v1', stages={stage_name: record})
        common.save(session/'state.json', state)
        try:
            if a.stage in ('soc', 'build'):
                from n1_soc import verify
                report = verify(cfg, run, a.platform, a.cases, common.call, firmware=a.firmware_root, compile_only=a.stage == 'build')
            elif a.stage == 'contention':
                from n1_contention import verify
                report = verify(cfg, run, a.platform, a.cases, common.call, a.firmware_root)
            elif a.stage == 'sequence':
                from n1_sequence_soc import verify
                report = verify(cfg, run, a.platform, a.cases, common.call, a.firmware_root)
            elif a.stage == 'batch':
                from n1_batch import verify
                report = verify(cfg, run, a.platform, a.dataset, common.call)
            elif a.stage == 'gate':
                from n1_gate import verify
                report = verify(cfg, run, a.synth_run, a.synth_summary_sha256, a.cases, common.call, (), a.firmware_root)
            elif a.stage == 'timing_audit':
                from n1_timing_audit import audit
                report = audit(cfg, run, a.synth_run, a.synth_summary_sha256, common.call)
            elif a.stage == 'saif':
                from n1_saif import verify
                report = verify(cfg, run, a.gate_run, a.gate_summary_sha256, a.saif_qualification_run, a.saif_qualification_sha256, a.cases, common.call)
            elif a.stage == 'power':
                from n1_power import estimate
                report = estimate(cfg, run, a.saif_activity_run, a.saif_activity_sha256, a.cases[0], common.call)
            else:
                from n1_synth import synth
                common.vendor(cfg, run)
                report = synth(cfg, run, a.platform, common.call)
            common.inputs()
            common.save(run/'summary.json', report)
            record.update(status='passed', summary_sha256=common.sha(run/'summary.json'))
        except BaseException as exc:
            record.update(status='failed', error=str(exc))
            raise
        finally:
            record['finished'] = datetime.datetime.now().isoformat()
            common.save(session/'state.json', state)
        print('ARCH03_N1_STAGE_PASS', a.stage, run, flush=True)
    finally:
        current = json.loads((lock/'owner.json').read_text())
        if (common.ACTIVE_CHILD is None or common.ACTIVE_CHILD.poll() is not None) and all(current.get(k) == owner[k] for k in ('pid', 'host', 'bundle', 'session')):
            (lock/'owner.json').unlink()
            lock.rmdir()


if __name__ == '__main__':
    main()
