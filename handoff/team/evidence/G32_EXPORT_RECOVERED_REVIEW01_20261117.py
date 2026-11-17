"""Export and review only the completed G32 initial01/recovery01/finish01 chain.

No dispatcher or retry. Explicit terminal identities are required. Existing
simulation, SAIF and PT results are read; one mapped connectivity query uses
the original team lock. This tool does not grant acceptance or freeze G32.
"""
import argparse
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path('/tmp/s4_21usr_g32_20261117_0810')
BUNDLE=ROOT/'light-light126-g32-0e16994'
MANIFEST='3524e2726880684c1c5681ef90da3a1ca41d78daf20d0df5b648e633b6e42f4a'
PAYLOAD='3c0a0f9156b6e40093bc5f9f5d91ae6cb5f95c207ba54e51bb2136a5bc44ab57'
INITIAL=BUNDLE/'runs/g32_initial01'
FINAL=BUNDLE/'runs/g32_finish01'
CONTROL=ROOT/'g32_export_review01'
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
    from g32_archive_contract import joined_queues,LAYERS
    from partition_synth_contract import require,digest
    joined_queues(proof['initial'],proof['finish'])
    initial=proof['initial'];finish=proof['finish'];a=initial['references'];f=finish['references']
    path=Path(a['precision']['run'])/'summary.json'
    require(digest(path)==a['precision']['sha256'],'Changed G32 precision join')
    precision=read(path)
    require(precision.get('fresh_float_reference_verified') is True and
            precision.get('batch',{}).get('batch_summary_sha256')==a['batch20']['sha256'] and
            precision.get('reference') is not None,'Precision must join this G32 batch')
    require(all(digest(path)==want for path,want in proof['inputs'].items()),'G32 chain changed')
    history=[dict(initial_queue=initial['queue'],finish_queue=finish['queue'],
        inputs_sha256=proof['inputs'],precision_join=a['precision'],
        structure=f['structure'],timing=f['timing_audit'],drc=f['drc_audit'],
        own_sequence=a['sequence'],own_contention=a['contention'],clock_gating=a['icg'],
        prior_hardware_results_reused=False,formal_samples=20,full100_started=False)]
    if initial.get('qualification_recovery'):
        history.append(dict(qualification_recovery=initial['qualification_recovery'],
            original_failed_state_preserved=True,original_failure=initial['state']['error']))
    return dict(schema='arch03-g32-report-request-v1',asic=a['soc'],batch=a['batch20'],
        precision=precision['reference'],synthesis=a['synth'],gate=f['gate'],activity=f['saif'],
        power=[f['power_'+layer] for layer in LAYERS],history=history)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--initial-state-sha256',required=True)
    parser.add_argument('--recovery-state-sha256',required=True)
    parser.add_argument('--finish-state-sha256',required=True)
    parser.add_argument('--ops-manifest-sha256',required=True)
    args=parser.parse_args()
    import hashlib
    ops=Path(__file__).resolve().parent
    local_sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
    assert local_sha(ops/'manifest.json')==args.ops_manifest_sha256
    for name,want in read(ops/'manifest.json')['files'].items():
        assert Path(name).name==name and local_sha(ops/name)==want
    sys.path.insert(0,str(SCRIPTS))
    import server_run as common
    import g32_paths as paths
    import g32_archive_contract as contract
    from g32_precision_recovery import numeric_runtime
    from n1_process import atomic_save
    from partition_synth_contract import require,digest
    require(common.ROOT==BUNDLE and digest(BUNDLE/'manifest.json')==MANIFEST,'Wrong corrected G32 bundle')
    require(digest(ROOT/'overlay.json')==PAYLOAD,'Changed payload')
    require(read(ROOT/'overlay.json')['source_commit']=='0e16994675bb15e53642017a88f6307da9af4a01','Wrong source')
    cfg=paths.configure(read(BUNDLE/'handoff/team/server_config.json'),BUNDLE,ROOT,MANIFEST,[])
    common.inputs();runtime=numeric_runtime()
    from g32_recovery_contract import recovered_initial
    initial=recovered_initial(INITIAL,args.initial_state_sha256,BUNDLE/'runs/g32_recovery01',
        args.recovery_state_sha256,alive)
    finish=contract.completed_queue(FINAL,args.finish_state_sha256,alive,'finish')
    for role,queue,proof in (('initial',INITIAL,initial),('finish',FINAL,finish)):
        request=read(queue/'request.json');script='g32_'+('qualification' if role=='initial' else 'finish')
        require(request.get('schema')==('g32-qualification-v1' if role=='initial' else 'g32-final-netlist-finish-v1'),
                'Wrong queue schema')
        require(request['bundle']==str(BUNDLE) and request['bundle_manifest_sha256']==MANIFEST and
                request['queue_sha256']==digest(SCRIPTS/(script+'.py')) and not request.get('runtime_evidence'),
                'G32 queue source or configuration mismatch')
        launch_path=ROOT/(queue.name+('_process.json' if role=='initial' else '_launch.json'))
        launch=read(launch_path)
        external_request=ROOT/(queue.name+'_request.json')
        require(launch['pid']==proof['state']['pid'] and launch.get('bundle_manifest_sha256',launch.get('manifest_sha256'))==MANIFEST and
                digest(external_request)==launch['request_sha256'] and read(external_request)==request,
                'Queue differs from explicit launch')
        proof['inputs'][str(external_request)]=digest(external_request)
        proof['inputs'][str(queue/'request.json')]=digest(queue/'request.json')
        proof['inputs'][str(launch_path)]=digest(launch_path)
    proof=contract.joined_queues(initial,finish)
    from g32_validation import verify_synthesis
    sr=initial['references']['synth'];verify_synthesis(sr['run'],sr['sha256'],cfg)
    require(not CONTROL.exists(),'Preserve prior export attempt')
    os.environ['PYTHONPATH']=os.pathsep.join((str(SCRIPTS),runtime['root']))
    os.environ['PYTHONDONTWRITEBYTECODE']='1'
    CONTROL.mkdir(mode=0o700)
    state=dict(status='validated_completed_own_queues',pid=os.getpid(),started=now(),source_sha256=digest(__file__),
        initial_state_sha256=args.initial_state_sha256,recovery_state_sha256=args.recovery_state_sha256,
        finish_state_sha256=args.finish_state_sha256,
        numerical_runtime=runtime,stage_accepted=False,full100_started=False,
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
        output=BUNDLE/'runs/g32_report01/g32_report'
        state['status']='exporting';atomic_save(CONTROL/'state.json',state)
        run('export',[sys.executable,'-B','-u',str(SCRIPTS/'g32_report.py'),'--request',str(request),
            '--output',str(output),'--runtime-root',str(ROOT),'--runtime-manifest-sha256',MANIFEST])
        report_path=output/'report.json';report_sha=digest(report_path);report=read(report_path)
        contract.exported_report(output,report_sha,proof)
        state.update(status='collecting_existing_activity',report=str(report_path),report_sha256=report_sha)
        atomic_save(CONTROL/'state.json',state)
        inventory=BUNDLE/'runs/g32_unknown_inventory01'
        run('inventory',[sys.executable,'-B','-u',str(SCRIPTS/'g32_saif_unknown_inventory.py'),
            '--report',str(report_path),'--report-sha256',report_sha,'--scope-root',str(ROOT),'--output',str(inventory)])
        unknown=read(inventory/'summary.json');unknown_sha=digest(inventory/'summary.json')
        require(unknown['full12_collected'] and unknown['full_unknown_inventory_complete'] and
                unknown['report_sha256']==report_sha and unknown['netlist_sha256']==report['netlist_sha256'],
                'Incomplete G32 unknown-state inventory')
        request=CONTROL/'connection_request.json'
        save_new(request,dict(transport_stage='G32',session='g32_unknown_connections01',
            review_bundle_manifest_sha256=MANIFEST,runtime_root=str(ROOT),bundle_manifest_sha256=MANIFEST,
            runtime_evidence=[],jobs=[dict(name='G32',synthesis=sr,
                unknown_inventories=[dict(run=str(inventory),sha256=unknown_sha)])],
            preparation_sha256=digest(__file__),report_sha256=report_sha,stage_accepted=False))
        state['status']='querying_own_mapped_connections';atomic_save(CONTROL/'state.json',state)
        run('connections',[sys.executable,'-B','-u',str(SCRIPTS/'g32_unknown_connections.py'),
            '--request',str(request),'--request-sha256',digest(request)])
        linked=BUNDLE/'runs/g32_unknown_connections01/g32_unknown_g32/summary.json';aliases=CONTROL/'aliases.json'
        run('aliases',[sys.executable,'-B','-u',str(SCRIPTS/'saif_unknown_alias_review.py'),
            '--summary',str(linked),'--sha256',digest(linked),'--output',str(aliases)])
        request=CONTROL/'snapshot_request.json'
        save_new(request,dict(schema='g32-model-review-request-v1',report=dict(path=str(report_path),sha256=report_sha),
            connections=dict(path=str(linked),sha256=digest(linked)),aliases=dict(path=str(aliases),sha256=digest(aliases))))
        snapshot=CONTROL/'model_review_snapshot.json'
        run('snapshot',[sys.executable,'-B','-u',str(SCRIPTS/'g32_model_review_snapshot.py'),
            '--request',str(request),'--request-sha256',digest(request),'--output',str(snapshot)])
        require(all(digest(path)==want for path,want in proof['inputs'].items()) and digest(report_path)==report_sha,
                'Frozen evidence changed during export')
        paths.recheck(cfg);common.inputs()
        state.update(status='facts_joined_manual_conclusion_required',snapshot=str(snapshot),snapshot_sha256=digest(snapshot),
            unknown_inventory_sha256=unknown_sha,connections_sha256=digest(linked))
        print('G32_EXPORT_REVIEW_FACTS_READY',digest(snapshot),'stage_accepted=false',flush=True)
    except BaseException as error:
        state.update(status='failed_preserved',error=str(error));raise
    finally:
        state['finished']=now();atomic_save(CONTROL/'state.json',state)


if __name__=='__main__':main()
