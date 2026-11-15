"""Own fresh P80 mapping plus final checks under one original team lock.

The earlier ENOSPC happened before mapping. Preserve all prior attempts and
reuse only the completed unchanged-hardware CPU measurements, never old maps.
"""
import datetime
from fractions import Fraction
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT=Path('/tmp/s4_21usr_p80_20261116_0315')
BUNDLE=ROOT/'light-light126-p80-4cf35b6'
MANIFEST='b8981502f271542300ec6139553be939bffb0d7f14c2cd00d0fda616ba59c6d1'
FIXED=ROOT/'light-light126-p80-142fae2'
FIXED_SHA='7017da04075aea98b7a9dfe414e41621d3974fb43709d542d42ac6b0f43920fc'
CPU=ROOT/'light-light126-p80-e139032'
CPU_SHA='c5429439f979357154736a30a2024a8c84fd615b545a2d8974b7ead52ecc52c8'
BUDGET=Path('/tmp/s4_21usr_t80_20261115_1830/light-light126-t80-s0-a5f138e/runs/s0_synth08/t80_s0_synth')
HELPER=ROOT/'p80_final_followup01_controller.py'
HELPER_SHA='e25435bf74ff0a582a0956a6e1892a65163999af8dffbc177e501b2f83d257e7'
sys.path.insert(0,str(BUNDLE/'workspaces/arch03/scripts'))
import server_run as common
import p80_paths as paths
import p80_finish as finish
from n1_process import ProcessLedger,atomic_save
from partition_synth_contract import require
from p80_validation import verify_synthesis


def read(path):return json.loads(Path(path).read_text())
def now():return datetime.datetime.now().isoformat()


def selected_depth():
    from p80_depth_selection import summarize
    sweep=read(ROOT/'p80_sweep05.json')
    require(sweep['status']=='completed' and sweep['current'] is None and
        len(sweep['completed'])==3 and {x['depth'] for x in sweep['completed']}=={2,4,8},'Incomplete depth comparison')
    rows=[]
    for item in sweep['completed']:
        require(item['session']=='p80_fixed_d%d_05'%item['depth'] and item['cases']==14,'Wrong own fixed14')
        rows.append(summarize(FIXED/'runs'/item['session']/'p80_soc',item['summary_sha256']))
    for row in rows:
        require(len(row['cases'])==12,'Incomplete fixed performance tasks')
        for left,right in zip(rows[0]['cases'],row['cases']):
            require(all(left[k]==right[k] for k in ('case','encoded_bytes','codec_sha256','layout_sha256','capture_sha256')),
                'Depth sweep mixed data or outputs')
        for source,want in row['hardware'].items():
            require(common.sha(BUNDLE/Path(source).relative_to(FIXED))==want,'Current hardware differs from CPU evidence')
    best=min(row['cycles_sum'] for row in rows)
    selected=min(row['depth'] for row in rows if Fraction(best,row['cycles_sum'])>=Fraction(99,100))
    require(selected==2,'This frozen firmware requires selected depth2')
    return rows


def map_stage(cfg,queue,state,ledger):
    session=BUNDLE/'runs/p80_synth_d2_03';run=session/'p80_synth'
    require(not session.exists(),'Preserve previous mapping session');run.mkdir(parents=True)
    ledger.register_stage_session(session);paths.allowed_run(run,cfg)
    common.save(session/'runtime_storage_receipt.json',paths.receipt(cfg))
    row=dict(status='running',pid=os.getpid(),started=now(),run=str(run),coordinator=str(queue),shared_lock_reacquired=False)
    stage=dict(schema='arch03-p80-eda-state-v1',stages={'p80_synth':row})
    atomic_save(session/'state.json',stage)
    state.update(status='running',stage='synthesis',current_run=str(run));atomic_save(queue/'state.json',state)
    try:
        from p80_partition_synth import execute
        report=execute(cfg,run,Path('/storage2/2026contest/server4/s4_21usr/Desktop/e203_hbirdv2-master'),
            BUNDLE/'firmware',BUDGET,ledger.call)
        common.inputs();paths.recheck(cfg);ledger.check_owner()
        report['temporary_storage_is_final_delivery']=False;common.save(run/'summary.json',report)
        row.update(status='passed',summary_sha256=common.sha(run/'summary.json'))
    except BaseException as error:
        row.update(status='failed',error=str(error));raise
    finally:
        row['finished']=now();atomic_save(session/'state.json',stage)
    ref=dict(run=str(run),sha256=row['summary_sha256'])
    state['synthesis']=ref;atomic_save(queue/'state.json',state)
    print('P80_FRESH_SYNTHESIS_NUMBERS',report['metrics'],report['area_summary']['conservative_budget_mm2'],flush=True)
    checked,_=verify_synthesis(run,ref['sha256'],cfg)
    require(checked['setup_hold_nonnegative'] is True and checked['area_summary']['conservative_budget_mm2']<=1.0,
        'Own actual P80 timing or conservative area not qualified')
    return ref


def main():
    require(common.ROOT==BUNDLE and common.sha(BUNDLE/'manifest.json')==MANIFEST,'Wrong frozen operations bundle')
    require(common.sha(HELPER)==HELPER_SHA,'Changed precision-stage helper')
    spec=importlib.util.spec_from_file_location('p80_original_precision_stage',str(HELPER))
    helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
    require(helper.BUNDLE==BUNDLE,'Precision helper package differs')
    cfg=paths.configure(read(BUNDLE/'handoff/team/server_config.json'),BUNDLE,ROOT,MANIFEST,[(CPU,CPU_SHA),(FIXED,FIXED_SHA)])
    common.inputs()
    old=read(ROOT/'p80_synth02_wait.json')
    require(old['status']=='failed' and 'No space left on device' in old['error'] and
        not (Path('/proc')/str(old['pid'])).exists(),'Original synthesis waiter has not failed/exited as recorded')
    for path in (ROOT/'p80_final_followup01.json',ROOT/'p80_export_review01/state.json'):
        previous=read(path)
        require(previous['status'].startswith('failed') and not (Path('/proc')/str(previous['pid'])).exists(),
            'Prior successor still active; never overlap queues')
    performance=selected_depth()
    functional=read(ROOT/'p80_functional_d2_02.json')
    require(functional['status']=='completed' and functional['current'] is None and
        [item['stage'] for item in functional['completed']]==['sequence','contention','batch20'],
        'Own completed CPU diagnostics and first20 required')
    for item in functional['completed']:
        run=CPU/('runs/p80_d2_'+item['stage']+'_02')/('p80_'+item['stage'])
        require(item['run']==str(run) and common.sha(run/'summary.json')==item['summary_sha256'],'Changed CPU stage')
        receipt=read(run.parent/'state.json')['stages']['p80_'+item['stage']]
        require(receipt['status']=='passed' and receipt['summary_sha256']==item['summary_sha256'],'Unfinished CPU stage')
    batch=dict(run=item['run'],sha256=item['summary_sha256']);result=read(Path(batch['run'])/'summary.json')
    require(result['tasks']==240 and result['checked_outputs']==result['checked_totals']==6082560 and result['failed']==0,
        'Actual first20 incomplete')
    require(common.sha(helper.ARCHIVE)==helper.ARCHIVE_SHA and common.sha(helper.NUMPY/'receipt.json')==helper.NUMPY_RECEIPT,
        'Changed FLOAT or explicit numerical runtime')
    os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['OMP_NUM_THREADS']='1';sys.path.insert(0,str(helper.NUMPY))
    import numpy
    require(numpy.__version__=='1.19.5' and Path(numpy.__file__).resolve()==helper.NUMPY/'numpy/__init__.py','Wrong NumPy')
    from p80_saif import qualification
    qualification(helper.QUALIFICATION,helper.QUALIFICATION_SHA,cfg)
    require(shutil.disk_usage(str(ROOT)).free>=20*1024**3,'Insufficient private runtime storage')
    names=subprocess.check_output(['ps','-u',str(os.getuid()),'-o','comm=']).decode().splitlines()
    require(not any(n.strip() in ('dc_shell','dc_shell-xg-t','common_shell_ex','pt_shell','vcs','simv') for n in names),
        'Other own-account EDA is running')
    queue=BUNDLE/'runs/p80_finish02';control=ROOT/'p80_final_combined02.json'
    require(not queue.exists() and not control.exists(),'Preserve earlier combined queue');queue.mkdir(parents=True)
    state=dict(status='acquiring_lock',pid=os.getpid(),started=now(),completed=[],stage_accepted=False,c80_started=False,
        full100_allowed=False,controller_sha256=common.sha(__file__),source_sha256=common.sha(__file__))
    atomic_save(queue/'state.json',state);atomic_save(control,state)
    common.save(queue/'intent.json',dict(performance_candidates=performance,batch=batch,
        old_failed_attempts_preserved=True,source_sha256=common.sha(__file__),own_shared_lock_acquisitions=1))
    ledger=ProcessLedger(common,Path(cfg['server_root'])/'.arch02_team_lock',queue)
    try:
        ledger.acquire();ledger.initialize();state['status']='running';atomic_save(control,state)
        synthesis=map_stage(cfg,queue,state,ledger)
        request=dict(schema='p80-final-netlist-finish-v1',bundle=str(BUNDLE),bundle_manifest_sha256=MANIFEST,
            runtime_root=str(ROOT),runtime_evidence=[[str(CPU),CPU_SHA],[str(FIXED),FIXED_SHA]],
            queue_sha256=common.sha(finish.__file__),synthesis=synthesis,batch=batch,
            qualification=dict(run=str(helper.QUALIFICATION),sha256=helper.QUALIFICATION_SHA))
        atomic_save(queue/'request.json',request)
        helper.precision_stage(cfg,queue,state,ledger,batch)
        finish.sequence(cfg,queue,state,ledger,request)
        require(len(state['completed'])==18,'Incomplete own final checks')
        state.update(status='reports_ready_review_required',current_run=None)
    except BaseException as error:
        state.update(status='failed',error=str(error));raise
    finally:
        try:
            if ledger.acquired:ledger.release()
        finally:
            state['finished']=now();atomic_save(queue/'state.json',state)
            copy=dict(state);copy['queue_state_sha256']=common.sha(queue/'state.json');atomic_save(control,copy)


if __name__=='__main__':main()
