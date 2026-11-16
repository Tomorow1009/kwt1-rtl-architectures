"""C32 functional stages in fresh private runs under the unchanged team lock.

Mapping/activity stages are deliberately absent until their own C32 build
contracts exist. This entry cannot dispatch a T80 gate/PPA job accidentally.
"""
import argparse
import datetime
import json
import os
from pathlib import Path
import re
import shutil
import server_run as common
import c32_paths
import n1_process
from n1_process import ProcessLedger

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('stage',choices=('status','soc','build','sequence','contention','batch20'))
    p.add_argument('--session',required=True)
    p.add_argument('--platform',type=Path,default=Path('/storage2/2026contest/server4/s4_21usr/Desktop/e203_hbirdv2-master'))
    p.add_argument('--cases',nargs='+',default=['extremes','rounding']+['layer_%02d'%n for n in range(1,13)])
    p.add_argument('--dataset',type=Path);p.add_argument('--firmware-root',type=Path)
    p.add_argument('--runtime-root',type=Path,required=True)
    p.add_argument('--runtime-manifest-sha256',required=True)
    p.add_argument('--runtime-evidence',nargs=2,action='append',default=[])
    a=p.parse_args()
    if not re.fullmatch('[A-Za-z0-9_-]{1,64}',a.session) or len(set(a.cases))!=len(a.cases):
        raise ValueError('Invalid unique session/case selection')
    cfg=c32_paths.configure(json.loads((common.ROOT/'handoff/team/server_config.json').read_text()),
        common.ROOT,a.runtime_root,a.runtime_manifest_sha256,a.runtime_evidence)
    session=common.ROOT/'runs'/a.session;lock=Path(cfg['server_root'])/'.arch02_team_lock'
    if a.stage=='status':
        print((session/'state.json').read_text() if (session/'state.json').exists() else 'SESSION_NOT_STARTED')
        if lock.exists():print('TEAM_LOCK',(lock/'owner.json').read_text() if (lock/'owner.json').exists() else 'incomplete lock')
        print('FREE_BYTES',shutil.disk_usage(str(common.ROOT)).free);return
    if session.exists():raise ValueError('Preserve all old artifacts; use a fresh session')
    if a.stage=='batch20' and a.dataset is None:
        raise ValueError('Formal batch needs pinned first20 inventory')
    packaged=common.inputs();dep='workspaces/arch03/scripts/n1_process.py'
    if Path(n1_process.__file__).resolve()!=(common.ROOT/dep).resolve() or packaged['files'].get(dep)!=common.sha(common.ROOT/dep):
        raise ValueError('Changed process ledger')
    free=shutil.disk_usage(str(common.ROOT)).free;required=int(1024**3*1.2)+2*1024**3
    if free<required:raise ValueError('Insufficient functional-run storage with margin/reserve')
    processes=ProcessLedger(common,lock,session);processes.acquire()
    try:
        run=session/('c32_'+a.stage);run.mkdir(parents=True,exist_ok=False)
        c32_paths.allowed_run(run,cfg,'C32 output');processes.initialize()
        common.save(run/'runtime_storage_receipt.json',c32_paths.receipt(cfg))
        record=dict(status='running',pid=os.getpid(),started=datetime.datetime.now().isoformat(),run=str(run))
        state=dict(schema='arch03-c32-server-state-v1',stages={'c32_'+a.stage:record})
        common.save(session/'state.json',state)
        try:
            if a.stage in ('soc','build'):
                from c32_soc import verify
                report=verify(cfg,run,a.platform,a.cases,processes.call,firmware=a.firmware_root,compile_only=a.stage=='build')
            elif a.stage=='sequence':
                from c32_sequence_soc import verify
                report=verify(cfg,run,a.platform,a.cases,processes.call,a.firmware_root)
            elif a.stage=='contention':
                from c32_contention import verify
                report=verify(cfg,run,a.platform,a.cases,processes.call,a.firmware_root)
            else:
                from c32_batch import verify
                report=verify(cfg,run,a.platform,a.dataset,processes.call,a.firmware_root)
            common.inputs();c32_paths.recheck(cfg)
            report['runtime_storage']=dict(receipt_sha256=common.sha(run/'runtime_storage_receipt.json'),
                durable_archive_required=True,temporary_storage_is_final_delivery=False)
            common.save(run/'summary.json',report)
            record.update(status='passed',summary_sha256=common.sha(run/'summary.json'))
        except BaseException as error:
            record.update(status='failed',error=str(error));raise
        finally:
            record['finished']=datetime.datetime.now().isoformat();common.save(session/'state.json',state)
        print('ARCH03_C32_STAGE_PASS',a.stage,str(run),flush=True)
    finally:processes.release()

if __name__=='__main__':main()
