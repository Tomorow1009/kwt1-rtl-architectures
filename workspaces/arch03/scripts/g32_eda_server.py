"""Independent G32 mapping/gate/activity stages, one shared-lock owner.

No automatic predecessor restart, no concurrent EDA and no mutation of frozen
inputs or protected delivery. Each requested stage occupies a fresh session.
"""
import argparse
import datetime
import json
import os
from pathlib import Path
import re
import shutil

import server_run as common
import g32_paths
from partition_synth_contract import require
from n1_process import ProcessLedger


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('stage',choices=('status','synth','gate','structure','timing_audit','drc_audit','saif','power','precision'))
    p.add_argument('--session',required=True)
    p.add_argument('--platform',type=Path,default=Path('/storage2/2026contest/server4/s4_21usr/Desktop/e203_hbirdv2-master'))
    p.add_argument('--firmware-root',type=Path)
    p.add_argument('--budget-origin',type=Path)
    for role in ('synth','gate','activity','qualification','batch'):
        p.add_argument('--'+role+'-run',type=Path);p.add_argument('--'+role+'-sha256')
    p.add_argument('--layer',choices=['layer_%02d'%i for i in range(1,13)])
    p.add_argument('--archive',type=Path);p.add_argument('--archive-sha256');p.add_argument('--dataset',type=Path)
    p.add_argument('--runtime-root',type=Path,required=True);p.add_argument('--runtime-manifest-sha256',required=True)
    p.add_argument('--runtime-evidence',nargs=2,action='append',default=[])
    a=p.parse_args();require(re.fullmatch('[A-Za-z0-9_-]{1,64}',a.session),'Invalid fresh session')
    cfg=g32_paths.configure(json.loads((common.ROOT/'handoff/team/server_config.json').read_text()),
        common.ROOT,a.runtime_root,a.runtime_manifest_sha256,a.runtime_evidence)
    lock=Path(cfg['server_root'])/'.arch02_team_lock';session=common.ROOT/'runs'/a.session
    if a.stage=='status':
        print((session/'state.json').read_text() if (session/'state.json').exists() else 'SESSION_NOT_STARTED')
        print('LOCK',lock.exists());print((lock/'owner.json').read_text() if (lock/'owner.json').exists() else '')
        print('FREE_BYTES',shutil.disk_usage(str(common.ROOT)).free);return
    require(not session.exists(),'Preserve previous attempt; use a new session')
    if a.stage=='synth':require(a.budget_origin is not None,'Explicit pinned S0 budget origin required')
    for role,stages in (('synth',('gate','structure','timing_audit','drc_audit')),
                        ('gate',('saif',)),('qualification',('saif',)),('activity',('power',)),('batch',('precision',))):
        if a.stage in stages:
            require(getattr(a,role+'_run') is not None and re.fullmatch('[a-f0-9]{64}',getattr(a,role+'_sha256') or ''),
                'Explicit '+role+' run and SHA256 required')
    if a.stage=='power':require(a.layer is not None,'Select one immutable activity layer')
    if a.stage=='precision':
        require(a.archive is not None and a.dataset is not None and re.fullmatch('[a-f0-9]{64}',a.archive_sha256 or ''),
            'Precision requires explicit same-data FLOAT archive, SHA256 and dataset')
    packaged=common.inputs()
    for name in ('g32_eda_server.py','g32_paths.py','g32_validation.py','g32_partition_synth.py','g32_link.py','n1_process.py'):
        relative='workspaces/arch03/scripts/'+name
        require(packaged['files'].get(relative)==common.sha(common.ROOT/relative),'Unfrozen G32 EDA dependency '+name)
    free=shutil.disk_usage(str(common.ROOT)).free
    required=int((12 if a.stage=='synth' else 4 if a.stage=='saif' else 1)*1024**3*1.2)+2*1024**3
    require(free>=required,'Insufficient space with 20% margin and 2 GiB reserve')
    ledger=ProcessLedger(common,lock,session);ledger.acquire()
    try:
        run=session/('g32_'+a.stage);run.mkdir(parents=True,exist_ok=False)
        ledger.initialize();g32_paths.allowed_run(run,cfg,'G32 EDA output')
        common.save(run/'runtime_storage_receipt.json',g32_paths.receipt(cfg))
        record=dict(status='running',pid=os.getpid(),started=datetime.datetime.now().isoformat(),run=str(run))
        state=dict(schema='arch03-g32-eda-state-v1',stages={'g32_'+a.stage:record});common.save(session/'state.json',state)
        try:
            layers=['layer_%02d'%i for i in range(1,13)]
            if a.stage=='synth':
                from g32_partition_synth import execute
                # Mapping needs an empty run. The lock/storage receipt is kept
                # at session scope, outside the immutable mapper's directory.
                (run/'runtime_storage_receipt.json').rename(session/'runtime_storage_receipt.json')
                report=execute(cfg,run,a.platform,a.firmware_root or common.ROOT/'firmware',a.budget_origin,ledger.call)
            elif a.stage=='gate':
                from g32_gate import verify
                report=verify(cfg,run,a.synth_run,a.synth_sha256,['extremes','rounding']+layers,ledger.call,firmware=a.firmware_root)
            elif a.stage=='structure':
                from g32_structure import audit
                report=audit(a.synth_run,a.synth_sha256,cfg)
            elif a.stage=='timing_audit':
                from g32_timing_audit import audit
                report=audit(cfg,run,a.synth_run,a.synth_sha256,ledger.call)
            elif a.stage=='drc_audit':
                from g32_drc_audit import audit
                report=audit(cfg,run,a.synth_run,a.synth_sha256,ledger.call)
            elif a.stage=='saif':
                from g32_saif import verify
                report=verify(cfg,run,a.gate_run,a.gate_sha256,a.qualification_run,a.qualification_sha256,layers,ledger.call)
            elif a.stage=='power':
                from g32_power import estimate
                report=estimate(cfg,run,a.activity_run,a.activity_sha256,a.layer,ledger.call)
            else:
                from g32_precision_join import verify
                report=verify(cfg,run,a.batch_run,a.batch_sha256,a.archive,a.archive_sha256,a.dataset)
            common.inputs();g32_paths.recheck(cfg)
            report['temporary_storage_is_final_delivery']=False
            common.save(run/'summary.json',report);record.update(status='passed',summary_sha256=common.sha(run/'summary.json'))
        except BaseException as error:
            record.update(status='failed',error=str(error));raise
        finally:
            record['finished']=datetime.datetime.now().isoformat();common.save(session/'state.json',state)
        print('G32_EDA_STAGE_PASS',a.stage,str(run),flush=True)
    finally:ledger.release()


if __name__=='__main__':main()
