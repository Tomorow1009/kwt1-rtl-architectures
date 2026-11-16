"""Export and review only the completed corrected C32 initial03/finish02 chain.

No dispatcher or retry. Explicit terminal identities are required. Existing
simulation, SAIF and PT results are read; one mapped connectivity query uses
the original team lock. This tool does not grant acceptance or freeze C32.
"""
import argparse
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path('/tmp/s4_21usr_c32_20261116_2010')
BUNDLE=ROOT/'light-light126-c32-91135f6'
MANIFEST='d877234086f471acb3c7f4ea0c69bb280606d6bbb45fdd212e8bf30366b316c7'
PAYLOAD='bc73ccd413657fd527628be76f5973de10f8cc30705580c3d5970ccbaed143bc'
INITIAL=BUNDLE/'runs/c32_initial03'
FINAL=BUNDLE/'runs/c32_finish02'
CONTROL=ROOT/'c32_export_review02'
SCRIPTS=BUNDLE/'workspaces/arch03/scripts'


def read(path):return json.loads(Path(path).read_text())
def now():return datetime.datetime.now().isoformat()
def alive(pid):return Path('/proc/%d'%pid).exists()


def save_new(path,value):
    with Path(path).open('x') as stream:
        json.dump(value,stream,indent=2,sort_keys=True);stream.write('\n')
        stream.flush();os.fsync(stream.fileno())


def make_request(proof):
    """Bind the report to the resolved own chain, including a separate retry."""
    from c32_archive_contract import joined_queues,LAYERS
    from partition_synth_contract import require,digest
    joined_queues(proof['initial'],proof['finish'])
    initial=proof['initial'];finish=proof['finish'];a=initial['references'];f=finish['references']
    path=Path(a['precision']['run'])/'summary.json'
    require(digest(path)==a['precision']['sha256'],'Changed C32 precision join')
    precision=read(path)
    require(precision.get('fresh_float_reference_verified') is True and
            precision.get('batch',{}).get('batch_summary_sha256')==a['batch20']['sha256'] and
            precision.get('reference') is not None,'Precision must join this C32 batch')
    require(all(digest(path)==want for path,want in proof['inputs'].items()),'C32 chain changed')
    history=[dict(initial_queue=initial['queue'],finish_queue=finish['queue'],
        inputs_sha256=proof['inputs'],precision_join=a['precision'],
        structure=f['structure'],timing=f['timing_audit'],drc=f['drc_audit'],
        own_sequence=a['sequence'],own_contention=a['contention'],
        prior_hardware_results_reused=False,formal_samples=20,full100_started=False)]
    if initial.get('precision_recovery'):
        history.append(dict(precision_recovery=initial['precision_recovery'],
            original_failed_state_preserved=True,original_failure=initial['state']['error']))
    return dict(schema='arch03-c32-report-request-v1',asic=a['soc'],batch=a['batch20'],
        precision=precision['reference'],synthesis=a['synth'],gate=f['gate'],activity=f['saif'],
        power=[f['power_'+layer] for layer in LAYERS],history=history)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--initial-state-sha256',required=True)
    parser.add_argument('--finish-state-sha256',required=True)
    args=parser.parse_args()
    sys.path.insert(0,str(SCRIPTS))
    import server_run as common
    import c32_paths as paths
    import c32_archive_contract as contract
    from c32_precision_recovery import numeric_runtime
    from n1_process import atomic_save
    from partition_synth_contract import require,digest
    require(common.ROOT==BUNDLE and digest(BUNDLE/'manifest.json')==MANIFEST,'Wrong corrected C32 bundle')
    require(digest(ROOT/'payload_91135f6.json')==PAYLOAD,'Changed payload')
    require(read(ROOT/'payload_91135f6.json')['source_commit']=='91135f61c97c980039793c6637d0a06888638df0','Wrong source')
    cfg=paths.configure(read(BUNDLE/'handoff/team/server_config.json'),BUNDLE,ROOT,MANIFEST,[])
    common.inputs();runtime=numeric_runtime()
    initial=contract.completed_queue(INITIAL,args.initial_state_sha256,alive,'initial')
    finish=contract.completed_queue(FINAL,args.finish_state_sha256,alive,'finish')
    for role,queue,proof in (('initial',INITIAL,initial),('finish',FINAL,finish)):
        request=read(queue/'request.json');script='c32_'+('qualification' if role=='initial' else 'finish')
        require(request.get('schema')==('c32-qualification-v1' if role=='initial' else 'c32-final-netlist-finish-v1'),
                'Wrong queue schema')
        require(request['bundle']==str(BUNDLE) and request['bundle_manifest_sha256']==MANIFEST and
                request['queue_sha256']==digest(SCRIPTS/(script+'.py')) and not request.get('runtime_evidence'),
                'C32 queue source or configuration mismatch')
        launch=read(ROOT/(queue.name+'_launch.json'))
        require(launch['pid']==proof['state']['pid'] and launch['manifest_sha256']==MANIFEST and
                digest(queue/'request.json')==launch['request_sha256'], 'Queue differs from explicit launch')
        proof['inputs'][str(queue/'request.json')]=digest(queue/'request.json')
        proof['inputs'][str(ROOT/(queue.name+'_launch.json'))]=digest(ROOT/(queue.name+'_launch.json'))
    proof=contract.joined_queues(initial,finish)
    from c32_validation import verify_synthesis
    sr=initial['references']['synth'];verify_synthesis(sr['run'],sr['sha256'],cfg)
    require(not CONTROL.exists(),'Preserve prior export attempt')
    os.environ['PYTHONPATH']=os.pathsep.join((str(SCRIPTS),runtime['root']))
    os.environ['PYTHONDONTWRITEBYTECODE']='1'
    CONTROL.mkdir(mode=0o700)
    state=dict(status='validated_completed_own_queues',pid=os.getpid(),started=now(),source_sha256=digest(__file__),
        initial_state_sha256=args.initial_state_sha256,finish_state_sha256=args.finish_state_sha256,
        numerical_runtime=runtime,stage_accepted=False,c32_b_started=False,g32_started=False,
        protected_T80_modified=False,old8_modified=False)
    atomic_save(CONTROL/'state.json',state)

    def run(name,command):
        save_new(CONTROL/(name+'_command.json'),command)
        with (CONTROL/(name+'.log')).open('x') as log:
            child=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT)
            save_new(CONTROL/(name+'_process.json'),dict(pid=child.pid,driver_pid=os.getpid(),started=now(),command=command))
            try:code=child.wait()
            finally:
                while child.poll() is None:
                    try:child.wait()
                    except BaseException:continue
        save_new(CONTROL/(name+'_exit.json'),dict(returncode=code,wait_completed=True,finished=now()))
        require(code==0,name+' failed; preserve this attempt')

    try:
        report_request=make_request(proof)
        save_new(CONTROL/'chain_proof.json',proof)
        request=CONTROL/'report_request.json';save_new(request,report_request)
        output=BUNDLE/'runs/c32_report01/c32_report'
        state['status']='exporting';atomic_save(CONTROL/'state.json',state)
        run('export',[sys.executable,'-B','-u',str(SCRIPTS/'c32_report.py'),'--request',str(request),
            '--output',str(output),'--runtime-root',str(ROOT),'--runtime-manifest-sha256',MANIFEST])
        report_path=output/'report.json';report_sha=digest(report_path);report=read(report_path)
        contract.exported_report(output,report_sha,proof)
        state.update(status='collecting_existing_activity',report=str(report_path),report_sha256=report_sha)
        atomic_save(CONTROL/'state.json',state)
        inventory=BUNDLE/'runs/c32_unknown_inventory01'
        run('inventory',[sys.executable,'-B','-u',str(SCRIPTS/'c32_saif_unknown_inventory.py'),
            '--report',str(report_path),'--report-sha256',report_sha,'--scope-root',str(ROOT),'--output',str(inventory)])
        unknown=read(inventory/'summary.json');unknown_sha=digest(inventory/'summary.json')
        require(unknown['full12_collected'] and unknown['full_unknown_inventory_complete'] and
                unknown['report_sha256']==report_sha and unknown['netlist_sha256']==report['netlist_sha256'],
                'Incomplete C32 unknown-state inventory')
        request=CONTROL/'connection_request.json'
        save_new(request,dict(transport_stage='C32',session='c32_unknown_connections01',
            review_bundle_manifest_sha256=MANIFEST,runtime_root=str(ROOT),bundle_manifest_sha256=MANIFEST,
            runtime_evidence=[],jobs=[dict(name='C32',synthesis=sr,
                unknown_inventories=[dict(run=str(inventory),sha256=unknown_sha)])],
            preparation_sha256=digest(__file__),report_sha256=report_sha,stage_accepted=False))
        state['status']='querying_own_mapped_connections';atomic_save(CONTROL/'state.json',state)
        run('connections',[sys.executable,'-B','-u',str(SCRIPTS/'c32_unknown_connections.py'),
            '--request',str(request),'--request-sha256',digest(request)])
        linked=BUNDLE/'runs/c32_unknown_connections01/c32_unknown_c32/summary.json';aliases=CONTROL/'aliases.json'
        run('aliases',[sys.executable,'-B','-u',str(SCRIPTS/'saif_unknown_alias_review.py'),
            '--summary',str(linked),'--sha256',digest(linked),'--output',str(aliases)])
        request=CONTROL/'snapshot_request.json'
        save_new(request,dict(schema='c32-model-review-request-v1',report=dict(path=str(report_path),sha256=report_sha),
            connections=dict(path=str(linked),sha256=digest(linked)),aliases=dict(path=str(aliases),sha256=digest(aliases))))
        snapshot=CONTROL/'model_review_snapshot.json'
        run('snapshot',[sys.executable,'-B','-u',str(SCRIPTS/'c32_model_review_snapshot.py'),
            '--request',str(request),'--request-sha256',digest(request),'--output',str(snapshot)])
        require(all(digest(path)==want for path,want in proof['inputs'].items()) and digest(report_path)==report_sha,
                'Frozen evidence changed during export')
        paths.recheck(cfg);common.inputs()
        state.update(status='facts_joined_manual_conclusion_required',snapshot=str(snapshot),snapshot_sha256=digest(snapshot),
            unknown_inventory_sha256=unknown_sha,connections_sha256=digest(linked))
        print('C32_EXPORT_REVIEW_FACTS_READY',digest(snapshot),'stage_accepted=false',flush=True)
    except BaseException as error:
        state.update(status='failed_preserved',error=str(error));raise
    finally:
        state['finished']=now();atomic_save(CONTROL/'state.json',state)


if __name__=='__main__':main()
