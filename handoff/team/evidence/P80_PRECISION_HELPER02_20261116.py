"""Wait for synthesis02, then own precision and final-netlist reports.

One unchanged shared lock covers all new stages. Existing queue, mappings,
T80 desktop and old eight-lane evidence are read-only. No automatic acceptance.
"""
import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT=Path('/tmp/s4_21usr_p80_20261116_0315')
BUNDLE=ROOT/'light-light126-p80-1023646'
SYNTH_BUNDLE=ROOT/'light-light126-p80-7430bb6'
SYNTH_MANIFEST='f3406e930f048a73f344736f8b10c2c91651a4b1f43ad3e9b79ebdf785e5ad1a'
CPU_BUNDLE=ROOT/'light-light126-p80-e139032'
CPU_MANIFEST='c5429439f979357154736a30a2024a8c84fd615b545a2d8974b7ead52ecc52c8'
PAYLOAD_SHA='ca268afa2d21023324c6fb0d28d8e9ed0f34711a4a67c55cb1fae778e07b421e'
SERVER=Path('/storage2/2026contest/server4/s4_21usr/Desktop/IC')
DATASET=SERVER/'hex_short_all'
ARCHIVE=Path('/tmp/s4_21usr_n1_20261113_0210/n1_precision_inputs_20261113_0840/n1-recovered-float100-20261113.zip')
ARCHIVE_SHA='5df11251821d2d36e85e07c8a171195d9d2ed2d4084a979519d23f6df7d683e2'
NUMPY=Path('/tmp/s4_21usr_n1_20261113_0210/n1_numpy1195_20261113_0905')
NUMPY_RECEIPT='c1fe14065d6919ff337f2cbf53551f94941acc35d04d3cadabca311fe742eacd'
QUALIFICATION=SERVER/'light-light126-undergrad-d2-20261109/bundles/light-light126-systolic-b-v3-20261112_114355-ced0e139a01e/runs/systolic_b_r4_crosscheck02/native_saif_r4_crosscheck'
QUALIFICATION_SHA='a0a9bc6280e7fe5f35b666535157700aac1d9c0b4490873b6199ba9b5c662d26'
sys.path.insert(0,str(BUNDLE/'workspaces/arch03/scripts'))
import server_run as common
import p80_paths as paths
import p80_finish as finish
from n1_process import ProcessLedger,atomic_save
from partition_synth_contract import require
from p80_validation import verify_synthesis


def read(path):return json.loads(Path(path).read_text())
def now():return datetime.datetime.now().isoformat()


def terminal_mapping():
    """Only wait on the pinned original controller; never restart it."""
    deadline=time.monotonic()+12*3600
    while True:
        wait=read(ROOT/'p80_synth02_wait.json')
        require(wait['controller_sha256']=='f0ce45ad205f6d87be57529998616d0e5397760c64c8972303ab3e665e6b456e',
            'Synthesis controller identity changed')
        require(wait['status'] in ('waiting_functional02','launching_synthesis','synthesis_completed_review_pending'),
            'Synthesis predecessor failed; preserve all evidence')
        require(time.monotonic()<deadline,'Predecessor timeout; no new EDA dispatched')
        if wait['status']=='synthesis_completed_review_pending' and not (Path('/proc')/str(wait['pid'])).exists():break
        time.sleep(15)
    q=read(ROOT/'p80_selected_synth02.json')
    run=SYNTH_BUNDLE/'runs/p80_synth_d2_02/p80_synth'
    require(q['status']=='synthesis_completed_review_pending' and q['selected_depth']==2 and
        q['run']==str(run) and common.sha(run/'summary.json')==q['summary_sha256'],
        'Synthesis02 summary identity differs')
    return dict(run=str(run),sha256=q['summary_sha256'])


def precision_stage(cfg,queue,state,ledger,batch):
    session=queue.with_name(queue.name+'_precision');run=session/'p80_precision'
    require(not session.exists(),'Preserve previous precision stage')
    run.mkdir(parents=True);ledger.register_stage_session(session);paths.allowed_run(run,cfg)
    common.save(run/'runtime_storage_receipt.json',paths.receipt(cfg))
    row=dict(status='running',pid=os.getpid(),started=now(),run=str(run),shared_lock_reacquired=False)
    stage=dict(schema='p80-independent-stage-v1',stages={'p80_precision':row})
    atomic_save(session/'state.json',stage)
    state.update(status='running',stage='precision',current_run=str(run));atomic_save(queue/'state.json',state)
    try:
        from p80_precision_join import verify
        report=verify(cfg,run,Path(batch['run']),batch['sha256'],ARCHIVE,ARCHIVE_SHA,DATASET)
        common.inputs();paths.recheck(cfg);ledger.check_owner()
        common.save(run/'summary.json',report)
        row.update(status='passed',summary_sha256=common.sha(run/'summary.json'))
    except BaseException as error:
        row.update(status='failed',error=str(error));raise
    finally:
        row['finished']=now();atomic_save(session/'state.json',stage)
    ref=dict(run=str(run),sha256=row['summary_sha256'])
    state['completed'].append(dict(stage='precision',reference=ref));atomic_save(queue/'state.json',state)
    print('P80_FRESH_FLOAT20_JOIN_PASS',ref['sha256'],flush=True)


def main():
    require(common.ROOT==BUNDLE,'Wrong operations package')
    require(common.sha(ROOT/'payload_4cf35b6.json')==PAYLOAD_SHA,'Wrong source overlay')
    prepared=read(ROOT/'light-light126-p80-4cf35b6.prepared.json')
    require(prepared['bundle']==str(BUNDLE) and prepared['source_preserved'] is True,'Wrong prepared bundle')
    manifest=prepared['manifest_sha256']
    cfg=paths.configure(read(BUNDLE/'handoff/team/server_config.json'),BUNDLE,ROOT,manifest,
        [(SYNTH_BUNDLE,SYNTH_MANIFEST),(CPU_BUNDLE,CPU_MANIFEST)])
    common.inputs()
    control=ROOT/'p80_final_followup01.json';require(not control.exists(),'Preserve prior followup')
    waiting=dict(status='waiting_synthesis02',pid=os.getpid(),started=now(),
        source_sha256=common.sha(Path(__file__)),operations_manifest_sha256=manifest,
        stage_accepted=False,protected_T80_modified=False,old8_modified=False)
    atomic_save(control,waiting)
    try:
        synthesis=terminal_mapping()
        mapped,_=verify_synthesis(synthesis['run'],synthesis['sha256'],cfg)
        require(mapped['setup_hold_nonnegative'] is True and
            mapped['area_summary']['conservative_budget_mm2']<=1.0,'Actual P80 timing/area not qualified')
        print('P80_SYNTHESIS_NUMBERS',mapped['metrics'],mapped['area_summary']['conservative_budget_mm2'],flush=True)
        functional=read(ROOT/'p80_functional_d2_02.json')
        require(functional['status']=='completed' and functional['current'] is None and len(functional['completed'])==3,
            'Own functional queue incomplete')
        item=functional['completed'][-1];batch_run=CPU_BUNDLE/'runs/p80_d2_batch20_02/p80_batch20'
        require(item['stage']=='batch20' and item['run']==str(batch_run) and
            common.sha(batch_run/'summary.json')==item['summary_sha256'],'Wrong own batch20')
        batch=dict(run=str(batch_run),sha256=item['summary_sha256'])
        require(common.sha(ARCHIVE)==ARCHIVE_SHA and common.sha(NUMPY/'receipt.json')==NUMPY_RECEIPT,
            'Precision source/runtime changed')
        os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['OMP_NUM_THREADS']='1';sys.path.insert(0,str(NUMPY))
        import numpy
        require(numpy.__version__=='1.19.5' and Path(numpy.__file__).resolve()==NUMPY/'numpy/__init__.py',
            'Wrong explicit numerical runtime')
        from p80_saif import qualification
        qualification(QUALIFICATION,QUALIFICATION_SHA,cfg)
        require(shutil.disk_usage(str(ROOT)).free>=20*1024**3,'Insufficient full-window storage')
        commands=subprocess.check_output(['ps','-u',str(os.getuid()),'-o','comm=']).decode().splitlines()
        require(not any(x.strip() in ('dc_shell','dc_shell-xg-t','common_shell_ex','pt_shell','vcs','simv') for x in commands),
            'Another EDA task is active')
        queue=BUNDLE/'runs/p80_finish01';require(not queue.exists(),'Preserve previous finish queue')
        request=dict(schema='p80-final-netlist-finish-v1',bundle=str(BUNDLE),bundle_manifest_sha256=manifest,
            runtime_root=str(ROOT),runtime_evidence=[[str(SYNTH_BUNDLE),SYNTH_MANIFEST],[str(CPU_BUNDLE),CPU_MANIFEST]],
            queue_sha256=common.sha(Path(finish.__file__)),synthesis=synthesis,
            qualification=dict(run=str(QUALIFICATION),sha256=QUALIFICATION_SHA),batch=batch,
            numeric_runtime=dict(root=str(NUMPY),receipt_sha256=NUMPY_RECEIPT,archive=str(ARCHIVE),archive_sha256=ARCHIVE_SHA))
        queue.mkdir(parents=True);atomic_save(queue/'request.json',request)
        state=dict(status='acquiring_lock',pid=os.getpid(),started=now(),completed=[],synthesis=synthesis,
            controller_sha256=common.sha(Path(__file__)),stage_accepted=False,c80_started=False,full100_allowed=False)
        atomic_save(queue/'state.json',state)
        ledger=ProcessLedger(common,SERVER/'.arch02_team_lock',queue)
        try:
            ledger.acquire();ledger.initialize()
            waiting.update(status='running',queue=str(queue));atomic_save(control,waiting)
            precision_stage(cfg,queue,state,ledger,batch)
            finish.sequence(cfg,queue,state,ledger,request)
            require(len(state['completed'])==18,'Incomplete own precision and final-netlist reports')
            state.update(status='reports_ready_review_required',current_run=None)
        except BaseException as error:
            state.update(status='failed',error=str(error));raise
        finally:
            try:
                if ledger.acquired:ledger.release()
            finally:
                state['finished']=now();atomic_save(queue/'state.json',state)
        waiting.update(status='reports_ready_review_required',queue_state_sha256=common.sha(queue/'state.json'))
    except BaseException as error:
        waiting.update(status='failed',error=str(error));raise
    finally:
        waiting['finished']=now();atomic_save(control,waiting)


if __name__=='__main__':main()
