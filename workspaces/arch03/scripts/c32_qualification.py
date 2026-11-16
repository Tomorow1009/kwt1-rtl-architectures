"""C32 ASIC/mapping/first20 qualification under one original shared lock.

Every stage is new. Failure stops successors, accepted children are drained by
the existing process ledger, and no old queue or delivery path is modified.
This queue cannot freeze C32-A or start C32-B/G32.
"""
import argparse
import datetime
import json
import os
from pathlib import Path
import re
import shutil
import server_run as common
import c32_paths as paths
from n1_process import ProcessLedger, atomic_save
from partition_synth_contract import require

ORDER=('soc','sequence','contention','synth','batch20','precision')
LAYERS=tuple('layer_%02d'%i for i in range(1,13))

def now():return datetime.datetime.now().isoformat()
def read(path):return json.loads(Path(path).read_text())


def dispatch(name,cfg,run,request,refs,call):
    platform=Path(request['platform'])
    if name=='soc':
        from c32_soc import verify
        return verify(cfg,run,platform,['extremes','rounding']+list(LAYERS),call)
    if name=='sequence':
        from c32_sequence_soc import verify
        return verify(cfg,run,platform,['layer_01','rounding'],call)
    if name=='contention':
        from c32_contention import verify
        return verify(cfg,run,platform,['layer_01'],call)
    if name=='synth':
        from c32_partition_synth import execute
        return execute(cfg,run,platform,common.ROOT/'firmware',Path(request['budget_origin']),call)
    if name=='batch20':
        from c32_batch import verify
        return verify(cfg,run,platform,Path(request['dataset']),call)
    require(name=='precision','Unknown C32 qualification stage')
    from c32_precision_join import verify
    ref=refs['batch20']
    return verify(cfg,run,Path(ref['run']),ref['sha256'],Path(request['float_archive']),
                  request['float_archive_sha256'],Path(request['dataset']))


def compare_fixed12(ref,baseline):
    """Same logical data and complete windows, rather than encoded byte count."""
    path=Path(baseline['path'])
    require(common.sha(path)==baseline['sha256'],'C80 comparison report changed')
    old=read(path)
    require(old['schema']=='arch03-c80-evidence-export-v1' and old['stage']=='C80' and
            old['layout_id']==0x00100006 and old['transaction_metadata_depth']==2 and
            old['aggregate']['total_cycles']==847238,'Wrong frozen C80 performance baseline')
    run=Path(ref['run'])
    require(common.sha(run/'summary.json')==ref['sha256'],'C32 ASIC summary changed')
    actual=read(run/'summary.json')
    require(actual['asic_cpu_verified'] is True and actual['global_FPGA_defined'] is False,
            'Performance comparison requires real ASIC CPU')
    rows={row['case']:row for row in actual['cases']}
    require(len(actual['cases'])==14 and set(rows)=={'extremes','rounding'}|set(LAYERS),
            'C32 fixed14 incomplete')
    sources={row['case']:row for row in old['fixed12_precision']['cases']}
    encoded={row['case']:row for row in old['cases']}
    require(set(sources)==set(LAYERS),'Baseline fixed12 source identity incomplete')
    for name in LAYERS:
        layout_path=run/(name+'_data')/'layout_manifest.json'
        require(common.sha(layout_path)==rows[name]['layout_sha256'],'C32 source layout changed')
        layout=read(layout_path)
        require(layout['layout']==0x00100006 and layout['numeric_format_id']==0x000e0c20 and
                layout['source_layout_sha256']==sources[name]['source_layout_sha256'] and
                layout['source_sha256']==sources[name]['source_hex_sha256'],
                'C32 and C80 performance samples differ')
        require(rows[name]['codec_sha256']==encoded[name]['codec_sha256'] and
                rows[name]['task_window']['encoded_bytes']==encoded[name]['encoded_bytes'],
                'C32 changed the frozen C80 encoding file or complete length')
    total=sum(rows[name]['task_window']['cycles'] for name in LAYERS)
    # C32-A measures array reduction. The plan does not require it to beat
    # C80 before its own PPA; only the optional C32-B must not slow C32-A.
    return dict(c32_fixed12_total_cycles=total,c80_fixed12_total_cycles=847238,
                same_logical_fixed12=True,same_encoded_fixed12=True,
                complete_cycles_ratio=total/847238.,stage_accepted=False)


def admit_batch(refs,request):
    """Reject an invalid candidate before the long batch; no final acceptance."""
    ref=refs['synth']
    require(common.sha(Path(ref['run'])/'summary.json')==ref['sha256'],'Synthesis summary changed')
    synth=read(Path(ref['run'])/'summary.json')
    require(synth['setup_hold_nonnegative'] is True and
            synth['area_summary']['conservative_budget_mm2']<=1.0,
            'C32 requires corrected timing/area before first20')
    result=compare_fixed12(refs['soc'],request['baseline'])
    result['numerical_timing_area_gate']=True
    return result


def run_stage(name,cfg,queue,state,ledger,request,refs):
    session=queue.with_name(queue.name+'_'+name);run=session/('c32_'+name)
    require(not session.exists(),'Never resume or overwrite qualification evidence')
    required=int((12 if name=='synth' else 3 if name=='batch20' else 1)*1024**3*1.2)+2*1024**3
    free=shutil.disk_usage(str(common.ROOT)).free
    require(free>=required,'Insufficient C32 storage with reserve')
    run.mkdir(parents=True);ledger.register_stage_session(session)
    paths.allowed_run(run,cfg,'C32 qualification output')
    common.save(session/'runtime_storage_receipt.json',paths.receipt(cfg))
    row=dict(status='running',pid=os.getpid(),started=now(),run=str(run),coordinator=str(queue))
    local=dict(schema='c32-independent-stage-v1',stages={'c32_'+name:row})
    atomic_save(session/'state.json',local)
    state.update(status='running',stage=name,current_run=str(run));atomic_save(queue/'state.json',state)
    try:
        report=dispatch(name,cfg,run,request,refs,ledger.call)
        common.inputs();paths.recheck(cfg);ledger.check_owner()
        common.save(run/'summary.json',report)
        row.update(status='passed',summary_sha256=common.sha(run/'summary.json'))
    except BaseException as error:
        row.update(status='failed',error=str(error));raise
    finally:
        row['finished']=now();atomic_save(session/'state.json',local)
    ref=dict(run=str(run),sha256=row['summary_sha256'])
    state['completed'].append(dict(stage=name,reference=ref));atomic_save(queue/'state.json',state)
    print('C32_QUALIFICATION_STAGE_READY',name,ref['sha256'],flush=True)
    return ref


def sequence(cfg,queue,state,ledger,request):
    refs={}
    for name in ORDER:
        if name=='batch20':
            from c32_validation import verify_synthesis
            s=refs['synth'];verify_synthesis(Path(s['run']),s['sha256'],cfg)
            state['batch_admission']=admit_batch(refs,request)
            atomic_save(queue/'state.json',state)
        refs[name]=run_stage(name,cfg,queue,state,ledger,request,refs)
        if name=='soc':
            state['performance_comparison']=compare_fixed12(refs['soc'],request['baseline'])
            atomic_save(queue/'state.json',state)
    return refs


def execute(request,queue):
    require(request['schema']=='c32-qualification-v1','Wrong qualification request')
    require(str(common.ROOT)==request['bundle'] and common.sha(common.ROOT/'manifest.json')==
            request['bundle_manifest_sha256'],'Wrong frozen C32 bundle')
    require(common.sha(Path(__file__))==request['queue_sha256'],'C32 qualification script changed')
    cfg=paths.configure(read(common.ROOT/'handoff/team/server_config.json'),common.ROOT,
        Path(request['runtime_root']),request['bundle_manifest_sha256'],request.get('runtime_evidence',[]))
    common.inputs()
    require(Path(request['dataset']).is_dir() and Path(request['float_archive']).is_file(),
            'Missing same-data inputs')
    require(re.fullmatch('[a-f0-9]{64}',request['float_archive_sha256']), 'Explicit FLOAT hash required')
    # Verify the existing private numerical runtime before any long hardware
    # stage, rather than discovering a missing NumPy import after the batch.
    from c32_precision_recovery import numeric_runtime
    numerical_runtime=numeric_runtime()
    require(not queue.exists(),'Preserve original queue')
    queue.mkdir(parents=True);atomic_save(queue/'request.json',request)
    state=dict(status='acquiring_lock',pid=os.getpid(),started=now(),completed=[],
               numerical_runtime=numerical_runtime,stage_accepted=False,
               c32_b_started=False,g32_started=False,full100_allowed=False)
    atomic_save(queue/'state.json',state)
    ledger=ProcessLedger(common,Path(cfg['server_root'])/'.arch02_team_lock',queue)
    try:
        ledger.acquire();ledger.initialize()
        sequence(cfg,queue,state,ledger,request)
        state.update(status='qualification_ready_gate_power_pending',current_run=None,finished=now())
    except BaseException as error:
        state.update(status='failed',error=str(error),finished=now());raise
    finally:
        try:
            if ledger.acquired:ledger.release()
        except BaseException as error:
            state.update(status='failed',error='Lock release failed: '+str(error),finished=now());raise
        finally:atomic_save(queue/'state.json',state)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--request',required=True,type=Path);p.add_argument('--request-sha256',required=True)
    p.add_argument('--session',required=True);a=p.parse_args()
    require(re.fullmatch('[A-Za-z0-9_-]{1,40}',a.session),'Invalid fresh queue name')
    require(common.sha(a.request)==a.request_sha256,'Request changed')
    execute(read(a.request),common.ROOT/'runs'/a.session)


if __name__=='__main__':main()
