"""Own P80 d2 recovery, CPU contention and first20, under one original lock.

Preserves the failed mapping, all frozen inputs and protected deliveries.
No mapping, power claim, cleanup, or next hardware stage is performed here.
"""
import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT=Path('/tmp/s4_21usr_p80_20261116_0315')
BUNDLE=ROOT/'light-light126-p80-e139032'
MANIFEST='c5429439f979357154736a30a2024a8c84fd615b545a2d8974b7ead52ecc52c8'
DATASET=Path('/storage2/2026contest/server4/s4_21usr/Desktop/IC/hex_short_all')
PLATFORM=DATASET.parent.parent/'e203_hbirdv2-master'
sys.path.insert(0,str(BUNDLE/'workspaces/arch03/scripts'))
import server_run as common
import p80_paths
from n1_process import ProcessLedger,atomic_save
from partition_synth_contract import require


def main():
    require(common.ROOT==BUNDLE,'Wrong operations package')
    cfg=p80_paths.configure(json.loads((BUNDLE/'handoff/team/server_config.json').read_text()),
        BUNDLE,ROOT,MANIFEST)
    common.inputs()
    old=json.loads((ROOT/'p80_selected_synth01.json').read_text())
    require(old['status']=='failed' and old.get('finished'),'Original mapping has not finished')
    require(not (Path('/proc')/str(old['pid'])).exists(),'Old mapping owner still present')
    require(shutil.disk_usage(str(ROOT)).free>8*1024**3,'Insufficient functional space')
    processes=subprocess.check_output(['ps','-u',str(os.getuid()),'-o','comm=']).decode().splitlines()
    require(not any(p.strip() in ('dc_shell','dc_shell-xg-t','common_shell_ex','pt_shell','vcs','simv')
        for p in processes),'Another account EDA task is active')
    lock=Path(cfg['server_root'])/'.arch02_team_lock'
    require(not lock.exists(),'Existing shared lock; never clear it')
    session=BUNDLE/'runs/p80_functional_d2_02'
    require(not session.exists(),'Preserve previous functional attempt')
    queue=ROOT/'p80_functional_d2_02.json'
    require(not queue.exists(),'Preserve previous functional queue')
    state=dict(schema='p80-d2-functional-queue-v1',pid=os.getpid(),status='starting',
        started=datetime.datetime.now().isoformat(),completed=[],current=None,
        bundle=str(BUNDLE),manifest_sha256=MANIFEST,controller_sha256=common.sha(Path(__file__)),
        protected_T80_modified=False,old8_modified=False,stage_accepted=False)
    atomic_save(queue,state)
    ledger=ProcessLedger(common,lock,session)
    try:
        ledger.acquire()
        try:
            session.mkdir(parents=True);ledger.initialize()
            for kind in ('sequence','contention','batch20'):
                target=BUNDLE/('runs/p80_d2_'+kind+'_02')
                require(not target.exists(),'Preserve stage '+kind)
                target.mkdir();ledger.register_stage_session(target)
                run=target/('p80_'+kind);run.mkdir()
                p80_paths.allowed_run(run,cfg)
                common.save(run/'runtime_storage_receipt.json',p80_paths.receipt(cfg))
                record=dict(status='running',pid=os.getpid(),run=str(run),
                    started=datetime.datetime.now().isoformat())
                stage=dict(schema='arch03-p80-server-state-v1',stages={'p80_'+kind:record})
                state.update(status='running',current=kind);atomic_save(queue,state)
                common.save(target/'state.json',stage)
                try:
                    if kind=='sequence':
                        from p80_sequence_soc import verify
                        report=verify(cfg,run,PLATFORM,['layer_01','rounding'],ledger.call)
                    elif kind=='contention':
                        from p80_contention import verify
                        report=verify(cfg,run,PLATFORM,['layer_01'],ledger.call)
                    else:
                        from p80_batch import verify
                        report=verify(cfg,run,PLATFORM,DATASET,ledger.call)
                    common.inputs();p80_paths.recheck(cfg)
                    report['runtime_storage']=dict(receipt_sha256=common.sha(run/'runtime_storage_receipt.json'),
                        durable_archive_required=True,temporary_storage_is_final_delivery=False)
                    common.save(run/'summary.json',report)
                    record.update(status='passed',summary_sha256=common.sha(run/'summary.json'))
                except BaseException as error:
                    record.update(status='failed',error=str(error));raise
                finally:
                    record['finished']=datetime.datetime.now().isoformat()
                    common.save(target/'state.json',stage)
                state['completed'].append(dict(stage=kind,run=str(run),summary_sha256=record['summary_sha256']))
                atomic_save(queue,state)
                print('P80_D2_FUNCTIONAL_STAGE_PASS',kind,str(run),flush=True)
            state.update(status='completed',current=None)
        finally:ledger.release()
    except BaseException as error:
        state.update(status='failed',error=str(error));raise
    finally:
        state['finished']=datetime.datetime.now().isoformat();atomic_save(queue,state)


if __name__=='__main__':main()
