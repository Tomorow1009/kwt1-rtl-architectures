"""Collect this C80 chain after the original finish controller has exited.

No synthesis or simulation is repeated. The sole mapped-connectivity query
uses the existing team lock. No acceptance, archive, cleanup or C32 dispatch.
"""
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path('/tmp/s4_21usr_c80_20261116_1245')
BUNDLE=ROOT/'light-light126-c80-74f3ae7'
MANIFEST='d0f18e4a6aa8a928df37d4347f1a8853c448e823f0685a83c5b710732e5e7a59'
OPS=ROOT/'ops-followup-9eda887'
OPS_RECEIPT='508d4f70bbb8f886a59533bf09727ddd4122bcf5e2276336e062d0c62893acb2'
PREDECESSOR=OPS/'C80_FINAL_FOLLOWUP01_20261116.py'
PREDECESSOR_SHA='62c6114e559b0dac3686e3c9e7d039e200a052735b6fd43e8afa9f787e79181b'
INITIAL=BUNDLE/'runs/c80_initial02'
INITIAL_REQUEST='49db1e2183bf38924af74a3223a088c811e1ccb94a2f25c3d98cc82ab922a9be'
FINAL=BUNDLE/'runs/c80_finish01'
CONTROL=ROOT/'c80_export_review01'
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
    from c80_archive_contract import joined_queues,LAYERS
    from partition_synth_contract import require,digest
    joined_queues(proof['initial'],proof['finish'])
    initial=proof['initial'];finish=proof['finish'];a=initial['references'];f=finish['references']
    path=Path(a['precision']['run'])/'summary.json'
    require(digest(path)==a['precision']['sha256'],'Changed C80 precision join')
    precision=read(path)
    require(precision.get('fresh_float_reference_verified') is True and
            precision.get('batch',{}).get('batch_summary_sha256')==a['batch20']['sha256'] and
            precision.get('reference') is not None,'Precision must join this C80 batch')
    require(all(digest(path)==want for path,want in proof['inputs'].items()),'C80 chain changed')
    history=[dict(initial_queue=initial['queue'],finish_queue=finish['queue'],
        inputs_sha256=proof['inputs'],precision_join=a['precision'],
        structure=f['structure'],timing=f['timing_audit'],drc=f['drc_audit'],
        own_sequence=a['sequence'],own_contention=a['contention'],
        prior_hardware_results_reused=False,formal_samples=20,full100_started=False)]
    if initial.get('precision_recovery'):
        history.append(dict(precision_recovery=initial['precision_recovery'],
            original_failed_state_preserved=True,original_failure=initial['state']['error']))
    return dict(schema='arch03-c80-report-request-v1',asic=a['soc'],batch=a['batch20'],
        precision=precision['reference'],synthesis=a['synth'],gate=f['gate'],activity=f['saif'],
        power=[f['power_'+layer] for layer in LAYERS],history=history)


def main():
    sys.path[:0]=[str(OPS),str(SCRIPTS)]
    import server_run as common
    import c80_paths as paths
    import c80_archive_contract as contract
    import c80_precision_recovery as retry
    from n1_process import atomic_save
    from partition_synth_contract import require,digest
    require(common.ROOT==BUNDLE and digest(BUNDLE/'manifest.json')==MANIFEST,'Wrong frozen C80 bundle')
    require(digest(OPS/'import_receipt.json')==OPS_RECEIPT and digest(PREDECESSOR)==PREDECESSOR_SHA,
            'Changed independent followup tools')
    before=read(OPS/'import_receipt.json')['loaded_dependencies']
    require(all(digest(path)==want for path,want in before.items()),'Changed imported followup dependency')
    common.inputs();runtime=retry.numeric_runtime()
    # Every child gets the same already-verified NumPy and original frozen tools.
    # This changes this process environment only, not a live predecessor or shell.
    os.environ['PYTHONPATH']=os.pathsep.join((str(OPS),str(SCRIPTS),runtime['root']))
    os.environ['PYTHONDONTWRITEBYTECODE']='1'
    CONTROL.mkdir()
    state=dict(status='waiting_original_finish',pid=os.getpid(),started=now(),source_sha256=digest(__file__),
        numerical_runtime=runtime,stage_accepted=False,c32_started=False,protected_T80_modified=False,old8_modified=False)
    atomic_save(CONTROL/'state.json',state)

    def run(name,command):
        save_new(CONTROL/(name+'_command.json'),command)
        with (CONTROL/(name+'.log')).open('x') as log:
            child=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT)
            save_new(CONTROL/(name+'_process.json'),dict(pid=child.pid,driver_pid=os.getpid(),started=now(),command=command))
            code=child.wait()
        save_new(CONTROL/(name+'_exit.json'),dict(returncode=code,wait_completed=True,finished=now()))
        require(code==0,name+' failed; preserve this attempt')

    try:
        deadline=time.monotonic()+24*3600
        while True:
            require(digest(PREDECESSOR)==PREDECESSOR_SHA,'Followup source changed')
            previous=read(ROOT/'c80_followup01.json');active=alive(previous['pid'])
            require(previous['pid']==314678 and previous['source_sha256']==PREDECESSOR_SHA and
                    previous['status'] in ('waiting_original_initial02','recovering_precision_only',
                        'finishing_final_netlist','reports_ready_independent_review_pending'),
                    'C80 followup failed or identity changed; no review dispatched')
            if active:
                require(str(PREDECESSOR).encode() in
                        (Path('/proc')/str(previous['pid'])/'cmdline').read_bytes().split(b'\0'),
                        'Followup PID reused')
            if previous['status']=='reports_ready_independent_review_pending' and not active:break
            require(active and time.monotonic()<deadline,'Followup absent or wait timed out')
            time.sleep(20)
        previous_sha=digest(ROOT/'c80_followup01.json')
        require(digest(INITIAL/'request.json')==INITIAL_REQUEST and previous['finish_queue']==str(FINAL),
                'Wrong original C80 queues')
        ihash=previous['predecessor_state_sha256'];fhash=previous['finish_state_sha256']
        if previous.get('precision_recovery'):
            initial=contract.recovered_initial(INITIAL,ihash,previous['precision_recovery'],alive)
        else:initial=contract.completed_queue(INITIAL,ihash,alive,'initial')
        finish=contract.completed_queue(FINAL,fhash,alive,'finish')
        for role,queue in (('initial',INITIAL),('finish',FINAL)):
            request=read(queue/'request.json');script='c80_'+('qualification' if role=='initial' else 'finish')
            require(request.get('schema')==('c80-qualification-v1' if role=='initial' else 'c80-final-netlist-finish-v1'),
                    'Wrong C80 queue schema')
            require(request['bundle']==str(BUNDLE) and request['bundle_manifest_sha256']==MANIFEST and
                    request['queue_sha256']==digest(SCRIPTS/(script+'.py')) and not request.get('runtime_evidence'),
                    'C80 queue changed bundle or tool')
            target=initial if role=='initial' else finish
            target['inputs'][str(queue/'request.json')]=digest(queue/'request.json')
        proof=contract.joined_queues(initial,finish)
        cfg=paths.configure(read(BUNDLE/'handoff/team/server_config.json'),BUNDLE,ROOT,MANIFEST,[])
        from c80_validation import verify_synthesis
        sr=initial['references']['synth'];verify_synthesis(sr['run'],sr['sha256'],cfg)
        report_request=make_request(proof);save_new(CONTROL/'chain_proof.json',proof)
        request=CONTROL/'report_request.json';save_new(request,report_request)
        output=BUNDLE/'runs/c80_report01/c80_report'
        state['status']='exporting';atomic_save(CONTROL/'state.json',state)
        run('export',[sys.executable,'-B','-u',str(SCRIPTS/'c80_report.py'),'--request',str(request),
            '--output',str(output),'--runtime-root',str(ROOT),'--runtime-manifest-sha256',MANIFEST])
        report_path=output/'report.json';report_sha=digest(report_path);report=read(report_path)
        contract.exported_report(output,report_sha,proof)
        state.update(status='collecting_existing_activity',report=str(report_path),report_sha256=report_sha)
        atomic_save(CONTROL/'state.json',state)
        inventory=BUNDLE/'runs/c80_unknown_inventory01'
        run('inventory',[sys.executable,'-B','-u',str(SCRIPTS/'c80_saif_unknown_inventory.py'),
            '--report',str(report_path),'--report-sha256',report_sha,'--scope-root',str(ROOT),'--output',str(inventory)])
        unknown=read(inventory/'summary.json');unknown_sha=digest(inventory/'summary.json')
        require(unknown['full12_collected'] and unknown['full_unknown_inventory_complete'] and
                unknown['report_sha256']==report_sha and unknown['netlist_sha256']==report['netlist_sha256'],
                'Incomplete C80 unknown-state inventory')
        request=CONTROL/'connection_request.json'
        save_new(request,dict(transport_stage='C80',session='c80_unknown_connections01',
            review_bundle_manifest_sha256=MANIFEST,runtime_root=str(ROOT),bundle_manifest_sha256=MANIFEST,
            runtime_evidence=[],jobs=[dict(name='C80',synthesis=sr,
                unknown_inventories=[dict(run=str(inventory),sha256=unknown_sha)])],
            preparation_sha256=digest(__file__),report_sha256=report_sha,stage_accepted=False))
        state['status']='querying_own_mapped_connections';atomic_save(CONTROL/'state.json',state)
        run('connections',[sys.executable,'-B','-u',str(SCRIPTS/'c80_unknown_connections.py'),
            '--request',str(request),'--request-sha256',digest(request)])
        linked=BUNDLE/'runs/c80_unknown_connections01/c80_unknown_c80/summary.json';aliases=CONTROL/'aliases.json'
        run('aliases',[sys.executable,'-B','-u',str(SCRIPTS/'saif_unknown_alias_review.py'),
            '--summary',str(linked),'--sha256',digest(linked),'--output',str(aliases)])
        request=CONTROL/'snapshot_request.json'
        save_new(request,dict(schema='c80-model-review-request-v1',report=dict(path=str(report_path),sha256=report_sha),
            connections=dict(path=str(linked),sha256=digest(linked)),aliases=dict(path=str(aliases),sha256=digest(aliases))))
        snapshot=CONTROL/'model_review_snapshot.json'
        run('snapshot',[sys.executable,'-B','-u',str(OPS/'c80_model_review_snapshot.py'),
            '--request',str(request),'--request-sha256',digest(request),'--output',str(snapshot)])
        require(all(digest(path)==want for path,want in dict(before,**proof['inputs']).items()) and
                digest(ROOT/'c80_followup01.json')==previous_sha and digest(report_path)==report_sha,
                'Frozen evidence changed during export')
        paths.recheck(cfg);common.inputs()
        state.update(status='facts_joined_manual_conclusion_required',snapshot=str(snapshot),snapshot_sha256=digest(snapshot),
            unknown_inventory_sha256=unknown_sha,connections_sha256=digest(linked),predecessor_state_sha256=previous_sha)
        print('C80_EXPORT_REVIEW_FACTS_READY',digest(snapshot),'stage_accepted=false',flush=True)
    except BaseException as error:
        state.update(status='failed_preserved',error=str(error));raise
    finally:
        state['finished']=now();atomic_save(CONTROL/'state.json',state)


if __name__=='__main__':main()
