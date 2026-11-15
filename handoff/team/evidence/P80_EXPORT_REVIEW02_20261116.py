"""Collect this P80 queue's reports after it naturally releases its lock.

Only the final connectivity query uses DC, under the existing shared lock.
No synthesis, new simulation, acceptance, cleanup or next hardware stage.
"""
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path('/tmp/s4_21usr_p80_20261116_0315')
BUNDLE=ROOT/'light-light126-p80-4cf35b6'
MANIFEST='b8981502f271542300ec6139553be939bffb0d7f14c2cd00d0fda616ba59c6d1'
FIXED=ROOT/'light-light126-p80-142fae2'
FIXED_MANIFEST='7017da04075aea98b7a9dfe414e41621d3974fb43709d542d42ac6b0f43920fc'
PREDECESSOR=ROOT/'p80_final_combined02_controller.py'
PREDECESSOR_SHA='f9566e5f768ddd6977022a835a7e3f5e899d9a8600a4ce90c7645efb4ab0b21a'
CONTROL=ROOT/'p80_export_review02'
QUEUE=BUNDLE/'runs/p80_finish02'
SCRIPTS=BUNDLE/'workspaces/arch03/scripts'
sys.path.insert(0,str(SCRIPTS))
import server_run as common
import p80_paths as paths
import p80_finish as finish
from partition_synth_contract import require
from n1_process import atomic_save


def sha(path):return common.sha(Path(path))
def read(path):return json.loads(Path(path).read_text())
def now():return datetime.datetime.now().isoformat()


def save_new(path,value):
    with Path(path).open('x') as stream:
        json.dump(value,stream,indent=2,sort_keys=True);stream.write('\n');stream.flush();os.fsync(stream.fileno())


def completed(queue):
    require(queue['status']=='reports_ready_review_required' and queue.get('finished'),
        'P80 final queue incomplete')
    require([item['stage'] for item in queue['completed']]==['precision']+list(finish.ORDER),
        'Incomplete, repeated or reordered P80 final stages')
    return {item['stage']:item['reference'] for item in queue['completed']}


def wait_original():
    deadline=time.monotonic()+24*3600
    while True:
        require(sha(PREDECESSOR)==PREDECESSOR_SHA,'Predecessor source changed')
        state=read(ROOT/'p80_final_combined02.json')
        require(state['source_sha256']==PREDECESSOR_SHA and state['status'] in
            ('waiting_synthesis02','running','reports_ready_review_required'),
            'Original P80 final queue failed; do not dispatch successors')
        pidpath=Path('/proc')/str(state['pid']);active=pidpath.exists()
        if active:
            require(str(PREDECESSOR).encode() in (pidpath/'cmdline').read_bytes().split(b'\0'),
                'Predecessor PID was reused')
        if state['status']=='reports_ready_review_required' and not active:return state
        require(active and time.monotonic()<deadline,'Predecessor missing or timed out')
        time.sleep(20)


def run(name,command):
    save_new(CONTROL/(name+'_command.json'),command)
    with (CONTROL/(name+'.log')).open('x') as log:
        child=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT)
        save_new(CONTROL/(name+'_process.json'),dict(pid=child.pid,started=now(),command=command))
        code=child.wait()
    save_new(CONTROL/(name+'_exit.json'),dict(returncode=code,finished=now()))
    require(code==0,name+' failed; preserve this attempt')


def main():
    require(common.ROOT==BUNDLE and sha(BUNDLE/'manifest.json')==MANIFEST,'Wrong P80 operations bundle')
    common.inputs();CONTROL.mkdir()
    state=dict(status='waiting_original_finish',pid=os.getpid(),started=now(),source_sha256=sha(__file__),
        stage_accepted=False,c80_started=False,protected_T80_modified=False,old8_modified=False)
    atomic_save(CONTROL/'state.json',state)
    try:
        previous=wait_original();qsha=sha(QUEUE/'state.json');queue=read(QUEUE/'state.json');refs=completed(queue)
        require(previous['queue_state_sha256']==qsha,'Queue changed after final controller exit')
        req=read(QUEUE/'request.json');evidence=req['runtime_evidence']
        require([str(FIXED),FIXED_MANIFEST] in evidence,'Own fixed14 bundle is not registered')
        cfg=paths.configure(read(BUNDLE/'handoff/team/server_config.json'),BUNDLE,ROOT,MANIFEST,evidence)
        from p80_report import stage
        from p80_validation import verify_synthesis
        verify_synthesis(req['synthesis']['run'],req['synthesis']['sha256'],cfg)
        for name,ref in refs.items():
            paths.allowed_run(ref['run'],cfg)
            stage(ref,'p80_'+('power' if name.startswith('power_') else name))
        sweep=read(ROOT/'p80_sweep05.json')
        require(sweep['status']=='completed' and sweep['current'] is None and
            {r['depth'] for r in sweep['completed']}=={2,4,8} and len(sweep['completed'])==3,
            'Original P80 depth14 sweep incomplete')
        row=next(r for r in sweep['completed'] if r['depth']==2)
        require(row['session']=='p80_fixed_d2_05' and row['cases']==14,'Wrong selected fixed ASIC14')
        asic=dict(run=str(FIXED/'runs/p80_fixed_d2_05/p80_soc'),sha256=row['summary_sha256'])
        stage(asic,'p80_soc')
        joined=stage(refs['precision'],'p80_precision')
        require(joined['fresh_float_reference_verified'] and joined['transaction_metadata_depth']==2,
            'Own P80 first20 FLOAT join incomplete')
        functional=read(ROOT/'p80_functional_d2_02.json')
        require(functional['status']=='completed' and functional['current'] is None and
            [item['stage'] for item in functional['completed']]==['sequence','contention','batch20'],
            'Own P80 recovery, contention or first20 incomplete')
        diagnostic=[]
        for item in functional['completed']:
            ref=dict(run=item['run'],sha256=item['summary_sha256'])
            paths.allowed_run(ref['run'],cfg);stage(ref,'p80_'+item['stage'])
            if item['stage']=='batch20':require(ref==req['batch'],'Different own batch20')
            else:diagnostic.append(dict(stage=item['stage'],reference=ref))
        report_request=dict(schema='arch03-p80-report-request-v1',asic=asic,batch=req['batch'],
            precision=joined['reference'],synthesis=req['synthesis'],gate=refs['gate'],activity=refs['saif'],
            power=[refs['power_'+layer] for layer in finish.LAYERS],
            history=[dict(queue=str(QUEUE),state_sha256=qsha,precision_join=refs['precision'],
                structure=refs['structure'],timing=refs['timing_audit'],drc=refs['drc_audit']),
                dict(depth_sweep=str(ROOT/'p80_sweep05.json'),sha256=sha(ROOT/'p80_sweep05.json'),
                    selection='Smallest depth with measured throughput within one percent; own area/timing reviewed separately'),
                dict(own_diagnostics=diagnostic,functional_queue_sha256=sha(ROOT/'p80_functional_d2_02.json')),
                dict(failed_synthesis=str(ROOT/'light-light126-p80-8543440/runs/p80_synth_d2_01'),
                    reason='Exported driving-library alias could not resolve; failed maps not reused'),
                dict(prior_hardware_results_reused=False,formal_samples=20,full100_started=False)])
        paths.recheck(cfg);require(sha(QUEUE/'state.json')==qsha,'Final state changed during preparation')
        request=CONTROL/'report_request.json';save_new(request,report_request)
        output=BUNDLE/'runs/p80_report02/p80_report'
        cmd=[sys.executable,'-B','-u',str(SCRIPTS/'p80_report.py'),'--request',str(request),'--output',str(output),
             '--runtime-root',str(ROOT),'--runtime-manifest-sha256',MANIFEST]
        for bundle,digest in evidence:cmd+=['--runtime-evidence',str(bundle),digest]
        state['status']='exporting';atomic_save(CONTROL/'state.json',state);run('export',cmd)
        report_path=output/'report.json';report_sha=sha(report_path);report=read(report_path)
        state.update(status='collecting_existing_activity',report=str(report_path),report_sha256=report_sha)
        atomic_save(CONTROL/'state.json',state)
        inventory=BUNDLE/'runs/p80_unknown_inventory02'
        run('inventory',[sys.executable,'-B','-u',str(SCRIPTS/'b0_saif_unknown_inventory.py'),
            '--report',str(report_path),'--report-sha256',report_sha,'--scope-root',str(ROOT),'--output',str(inventory)])
        unknown=read(inventory/'summary.json');unknown_sha=sha(inventory/'summary.json')
        require(unknown['full12_collected'] and unknown['full_unknown_inventory_complete'] and
            unknown['report_sha256']==report_sha and unknown['netlist_sha256']==report['netlist_sha256'],
            'Incomplete own unknown-state inventory')
        connection_request=dict(transport_stage='P80',session='p80_unknown_connections02',
            review_bundle_manifest_sha256=MANIFEST,runtime_root=str(ROOT),bundle_manifest_sha256=MANIFEST,
            runtime_evidence=evidence,jobs=[dict(name='P80',synthesis=req['synthesis'],
                unknown_inventories=[dict(run=str(inventory),sha256=unknown_sha)])],
            preparation_sha256=sha(__file__),report_sha256=report_sha,stage_accepted=False)
        request=CONTROL/'connection_request.json';save_new(request,connection_request)
        state['status']='querying_own_mapped_connections';atomic_save(CONTROL/'state.json',state)
        run('connections',[sys.executable,'-B','-u',str(SCRIPTS/'saif_unknown_connections.py'),
            '--request',str(request),'--request-sha256',sha(request)])
        linked=BUNDLE/'runs/p80_unknown_connections02/p80_unknown_p80/summary.json'
        aliases=CONTROL/'aliases.json'
        run('aliases',[sys.executable,'-B','-u',str(SCRIPTS/'saif_unknown_alias_review.py'),
            '--summary',str(linked),'--sha256',sha(linked),'--output',str(aliases)])
        snapshot_request=CONTROL/'snapshot_request.json'
        save_new(snapshot_request,dict(schema='p80-model-review-request-v1',
            report=dict(path=str(report_path),sha256=report_sha),
            connections=dict(path=str(linked),sha256=sha(linked)),aliases=dict(path=str(aliases),sha256=sha(aliases))))
        snapshot=CONTROL/'model_review_snapshot.json'
        run('snapshot',[sys.executable,'-B','-u',str(SCRIPTS/'p80_model_review_snapshot.py'),
            '--request',str(snapshot_request),'--request-sha256',sha(snapshot_request),'--output',str(snapshot)])
        require(sha(QUEUE/'state.json')==qsha and sha(report_path)==report_sha,'Frozen evidence changed')
        paths.recheck(cfg);common.inputs()
        state.update(status='facts_joined_manual_conclusion_required',snapshot=str(snapshot),snapshot_sha256=sha(snapshot),
            unknown_inventory_sha256=unknown_sha,connections_sha256=sha(linked),queue_state_sha256=qsha)
        print('P80_EXPORT_REVIEW_FACTS_READY',sha(snapshot),'stage_accepted=false',flush=True)
    except BaseException as error:
        state.update(status='failed_preserved',error=str(error));raise
    finally:
        state['finished']=now();atomic_save(CONTROL/'state.json',state)


if __name__=='__main__':main()
