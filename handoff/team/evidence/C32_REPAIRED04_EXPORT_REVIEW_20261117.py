"""Join unchanged C32 RTL qualification to its own equivalent repaired netlist.

Uses new gate14, SAIF12 and PT12. Preserves every failed mapping and old report.
No automatic acceptance, old-netlist activity reuse, or hardware-stage advance.
"""
import argparse
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path('/tmp/s4_21usr_c32_20261116_2010')
BUNDLE=ROOT/'light-light126-c32-repair-5828804'
OLD=ROOT/'light-light126-c32-91135f6'
OLD_SHA='d877234086f471acb3c7f4ea0c69bb280606d6bbb45fdd212e8bf30366b316c7'
INITIAL_SHA='37e1279f0c165b6fb50493c4d87edb2a994e159a90e22e48b92c41ef8ab500c0'
SCRIPTS=BUNDLE/'workspaces/arch03/scripts'
CONTROL=ROOT/'c32_repaired_export_review03'


def read(path):return json.loads(Path(path).read_text())
def now():return datetime.datetime.now().isoformat()
def alive(pid):return Path('/proc/%d'%pid).exists()


def save_new(path,value):
    with Path(path).open('x') as stream:
        json.dump(value,stream,indent=2,sort_keys=True);stream.write('\n')
        stream.flush();os.fsync(stream.fileno())


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--finish-state-sha256',required=True)
    args=parser.parse_args()
    sys.path.insert(0,str(SCRIPTS))
    import server_run as common
    import c32_paths as paths
    from c32_archive_contract import completed_queue,LAYERS
    from c32_validation import verify_synthesis,require_clear_constraints
    from c32_precision_recovery import numeric_runtime
    from n1_process import atomic_save
    from partition_synth_contract import require,digest
    launch=read(ROOT/'c32_repair03_launch.json');manifest=launch['manifest_sha256']
    require(launch['bundle']==str(BUNDLE) and launch['source_commit']=='58288044bfbbe344fafc7550647bfc5c29eef0a7' and
        digest(BUNDLE/'manifest.json')==manifest and common.ROOT==BUNDLE,'Changed repaired operations identity')
    evidence=[[str(OLD),OLD_SHA]]
    cfg=paths.configure(read(BUNDLE/'handoff/team/server_config.json'),BUNDLE,ROOT,manifest,evidence)
    common.inputs();runtime=numeric_runtime()
    initial=completed_queue(OLD/'runs/c32_initial03',INITIAL_SHA,alive,'initial')
    final=completed_queue(BUNDLE/'runs/c32_finish_repair04',args.finish_state_sha256,alive,'finish')
    a,f=initial['references'],final['references'];sr=final['state']['synthesis']
    synthesis,_=verify_synthesis(sr['run'],sr['sha256'],cfg)
    require_clear_constraints(sr['run'],synthesis)
    repair=synthesis['mapped_repair']
    require(repair['original_run']==a['synth']['run'] and repair['original_summary_sha256']==a['synth']['sha256'] and
        repair['rtl_modified'] is False and repair['topology_changed'] is False and
        repair['inherited_gate_pass'] is False and synthesis['repair_identity']['all_other_verilog_tokens_identical'],
        'Repair cannot inherit a different hardware qualification')
    q=BUNDLE/'runs/c32_finish_repair04';qr=read(q/'request.json')
    fl=read(ROOT/'c32_finish_repair04_launch.json')
    require(qr['synthesis']==sr and qr['bundle']==str(BUNDLE) and qr['runtime_evidence']==evidence and
        qr['queue_sha256']==digest(SCRIPTS/'c32_finish.py') and qr['bundle_manifest_sha256']==manifest and
        digest(q/'request.json')==fl['request_sha256'] and fl['pid']==final['state']['pid'],
        'Final queue does not bind this repaired netlist')
    recovery=qr['lock_storage_recovery'];driver=ROOT/'c32_finish04_driver.py'
    predecessor=Path(recovery['predecessor']['queue'])/'state.json';failed=read(predecessor)
    require(digest(driver)==recovery['source_sha256']==fl['source_sha256'] and
        digest(predecessor)==recovery['predecessor']['state_sha256'] and
        predecessor.parent==BUNDLE/'runs/c32_finish_repair03' and
        failed['status']=='failed' and failed['completed']==[] and not alive(failed['pid']) and
        '[Errno 28]' in failed['error'] and recovery['original_lock_unchanged'] is True and
        recovery['partial_lock_not_removed'] is True,'Wrong lock-storage recovery identity')
    precision=read(Path(a['precision']['run'])/'summary.json')
    require(digest(Path(a['precision']['run'])/'summary.json')==a['precision']['sha256'] and
        precision['fresh_float_reference_verified'] and precision['batch']['batch_summary_sha256']==a['batch20']['sha256'],
        'Unchanged RTL batch/precision identity mismatch')
    inputs=dict(initial['inputs'],**final['inputs'])
    inputs[str(driver)]=digest(driver);inputs[str(predecessor)]=digest(predecessor)
    for p in (Path(sr['run'])/'summary.json',Path(sr['run'])/'repair_provenance.json',
        Path(sr['run'])/'repair_identity.json',q/'request.json',ROOT/'c32_repair03_launch.json',
        ROOT/'c32_finish_repair04_launch.json'):
        inputs[str(p)]=digest(p)
    proof=dict(schema='c32-equivalent-repair-chain-v1',initial=initial,finish=final,
        repaired_synthesis=sr,mapped_repair=repair,inputs=inputs,
        reused_only_unchanged_RTL_function_precision=True,old_gate_or_power_reused=False,stage_accepted=False)
    require(not CONTROL.exists(),'Preserve prior repaired export')
    os.environ['PYTHONPATH']=os.pathsep.join((str(SCRIPTS),runtime['root']))
    os.environ['PYTHONDONTWRITEBYTECODE']='1';CONTROL.mkdir(mode=0o700)
    state=dict(status='validated_repaired_chain',pid=os.getpid(),started=now(),source_sha256=digest(__file__),
        stage_accepted=False,protected_T80_modified=False,old8_modified=False)
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
        save_new(CONTROL/'chain_proof.json',proof)
        request=CONTROL/'report_request.json'
        save_new(request,dict(schema='arch03-c32-report-request-v1',asic=a['soc'],batch=a['batch20'],
            precision=precision['reference'],synthesis=sr,gate=f['gate'],activity=f['saif'],
            power=[f['power_'+layer] for layer in LAYERS],history=[dict(repair_proof=str(CONTROL/'chain_proof.json'),
                repair_proof_sha256=digest(CONTROL/'chain_proof.json'),own_sequence=a['sequence'],own_contention=a['contention'],
                reused_unchanged_C32_RTL_qualification=True,old_final_netlist_results_reused=False)]))
        output=BUNDLE/'runs/c32_report_repair03/c32_report'
        state['status']='exporting';atomic_save(CONTROL/'state.json',state)
        run('export',[sys.executable,'-B','-u',str(SCRIPTS/'c32_report.py'),'--request',str(request),
            '--output',str(output),'--runtime-root',str(ROOT),'--runtime-manifest-sha256',manifest,
            '--runtime-evidence',str(OLD),OLD_SHA])
        report_path=output/'report.json';report_sha=digest(report_path);report=read(report_path)
        require(report['references']==dict(asic=a['soc'],synthesis=sr,gate=f['gate']) and
            report['activity_reference']==f['saif'] and report['batch_reference']==a['batch20'] and
            report['power_references']==[f['power_'+layer] for layer in LAYERS], 'Export changed the repaired chain')
        state.update(status='collecting_new_activity',report=str(report_path),report_sha256=report_sha)
        atomic_save(CONTROL/'state.json',state)
        inventory=BUNDLE/'runs/c32_unknown_inventory_repair03'
        run('inventory',[sys.executable,'-B','-u',str(SCRIPTS/'c32_saif_unknown_inventory.py'),
            '--report',str(report_path),'--report-sha256',report_sha,'--scope-root',str(ROOT),'--output',str(inventory)])
        unknown=read(inventory/'summary.json');unknown_sha=digest(inventory/'summary.json')
        require(unknown['full12_collected'] and unknown['full_unknown_inventory_complete'] and
            unknown['report_sha256']==report_sha and unknown['netlist_sha256']==report['netlist_sha256'],
            'Incomplete repaired unknown-state inventory')
        request=CONTROL/'connection_request.json'
        save_new(request,dict(transport_stage='C32',session='c32_connections_repair03',
            review_bundle_manifest_sha256=manifest,runtime_root=str(ROOT),bundle_manifest_sha256=manifest,
            runtime_evidence=evidence,jobs=[dict(name='C32',synthesis=sr,
                unknown_inventories=[dict(run=str(inventory),sha256=unknown_sha)])],
            preparation_sha256=digest(__file__),report_sha256=report_sha,stage_accepted=False))
        state['status']='querying_repaired_connections';atomic_save(CONTROL/'state.json',state)
        run('connections',[sys.executable,'-B','-u',str(SCRIPTS/'c32_unknown_connections.py'),
            '--request',str(request),'--request-sha256',digest(request)])
        linked=BUNDLE/'runs/c32_connections_repair03/c32_unknown_c32/summary.json';aliases=CONTROL/'aliases.json'
        run('aliases',[sys.executable,'-B','-u',str(SCRIPTS/'saif_unknown_alias_review.py'),
            '--summary',str(linked),'--sha256',digest(linked),'--output',str(aliases)])
        request=CONTROL/'snapshot_request.json'
        save_new(request,dict(schema='c32-model-review-request-v1',report=dict(path=str(report_path),sha256=report_sha),
            connections=dict(path=str(linked),sha256=digest(linked)),aliases=dict(path=str(aliases),sha256=digest(aliases))))
        snapshot=CONTROL/'model_review_snapshot.json'
        run('snapshot',[sys.executable,'-B','-u',str(SCRIPTS/'c32_model_review_snapshot.py'),
            '--request',str(request),'--request-sha256',digest(request),'--output',str(snapshot)])
        require(all(digest(p)==h for p,h in inputs.items()),'Repaired chain changed during export')
        paths.recheck(cfg);common.inputs()
        state.update(status='facts_joined_manual_conclusion_required',snapshot=str(snapshot),snapshot_sha256=digest(snapshot),
            unknown_inventory_sha256=unknown_sha,connections_sha256=digest(linked))
        print('C32_REPAIRED_REVIEW_FACTS_READY',digest(snapshot),'stage_accepted=false',flush=True)
    except BaseException as error:
        state.update(status='failed_preserved',error=str(error));raise
    finally:
        state['finished']=now();atomic_save(CONTROL/'state.json',state)


if __name__=='__main__':main()
