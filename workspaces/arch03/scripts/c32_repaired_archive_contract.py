"""Join original RTL evidence with a separately proven equivalent-cell repair.

The ordinary same-netlist archive contract stays strict. This explicit route
requires independent synthesis verification and the new netlist's own PPA.
"""
from pathlib import Path

import c32_archive_contract as original
from c32_review_contract import route_identity
from partition_synth_contract import require, digest

SCHEMA='arch03-c32-equivalent-repair-runtime-copy-v1'
read=original.read


def joined_repair(initial,finish,synthesis):
    require(initial['role']=='initial' and finish['role']=='finish', 'Wrong repaired queue roles')
    iq,fq=Path(initial['queue']),Path(finish['queue'])
    require(iq.parents[2]==fq.parents[2] and iq.parent!=fq.parent,
            'Repaired queues must be distinct bundles in one runtime')
    ref=finish['state']['synthesis'];path=Path(ref['run'])/'summary.json'
    require(digest(path)==ref['sha256'] and read(path)==synthesis, 'Repaired summary changed')
    require(route_identity(synthesis) and synthesis.get('mapped_repair'), 'Not an explicit equivalent repair')
    prior=initial['references']['synth'];p=synthesis['mapped_repair']
    require(p['original_run']==prior['run'] and p['original_summary_sha256']==prior['sha256'] and
            ref!=prior and Path(ref['run']).parents[1]==fq.parent,
            'Repaired netlist does not derive from this RTL qualification')
    inputs=dict(initial['inputs'],**finish['inputs']);inputs[str(path)]=ref['sha256']
    return dict(schema='c32-repaired-queue-join-v1',initial=initial,finish=finish,synthesis=ref,
        mapped_repair=p,inputs=inputs,reused_only_unchanged_RTL_function_precision=True,
        old_gate_or_power_reused=False,archive_implies_acceptance=False)


def exported_report(run,expected_sha,proof):
    run=Path(run).absolute();path=run/'report.json'
    require(digest(path)==expected_sha,'Repaired export changed')
    report=read(path);receipt=read(run/'receipt.json')
    require(report.get('schema')=='arch03-c32-evidence-export-v1' and report.get('stage')=='C32' and
            report.get('layout_id')==0x00100006 and report.get('numeric_format')=='0x000e0c20' and
            receipt.get('schema')=='arch03-c32-export-receipt-v1', 'Not a repaired C32 layout6 export')
    require(run.parents[1]==Path(proof['finish']['queue']).parent and run.name=='c32_report' and
            run.resolve()==run, 'Repaired export outside its final bundle')
    a,f=proof['initial']['references'],proof['finish']['references']
    require(report['references']==dict(asic=a['soc'],synthesis=proof['synthesis'],gate=f['gate']) and
            report['activity_reference']==f['saif'] and report['power_references']==[f['power_'+n] for n in original.LAYERS] and
            report['batch_reference']==a['batch20'], 'Repaired export used another netlist, batch or activity')
    require(route_identity(report['synthesis_route']) and
            report['synthesis_route']['mapped_repair']==proof['mapped_repair'], 'Repaired export changed mapping route')
    p=Path(a['precision']['run'])/'summary.json'
    require(digest(p)==a['precision']['sha256'],'Original precision changed')
    precision=read(p)
    require(precision.get('fresh_float_reference_verified') is True and
            report['precision_reference']==precision['reference'], 'Repaired export changed precision')
    require(receipt.get('artifacts',{}).get('report.json')==expected_sha,'Repaired export receipt differs')
    inputs={str(path):expected_sha,str(run/'receipt.json'):digest(run/'receipt.json')}
    for name,want in receipt['artifacts'].items():
        require(Path(name).name==name and digest(run/name)==want,'Repaired export artifact changed')
        inputs[str(run/name)]=want
    return dict(inputs=inputs,report=str(run),report_sha256=expected_sha,stage_accepted=False,
                source_modified=False,archive_implies_acceptance=False)


def evidence(req,bundle):
    """Called only after c32_paths.configure verifies all registered bundles."""
    from c32_validation import verify_synthesis,require_clear_constraints
    from c32_paths import configure
    cfg=configure(read(bundle/'handoff/team/server_config.json'),bundle,req['runtime_root'],
        req['bundle_manifest_sha256'],req['runtime_evidence'])
    registered={str(bundle):req['bundle_manifest_sha256']}
    registered.update({str(Path(p)):h for p,h in req['runtime_evidence']})
    proofs={}
    for role in ('initial','finish'):
        ref=req[role];queue=Path(ref['queue']).absolute();owner=queue.parents[1]
        require(queue.parent.name=='runs' and queue.resolve()==queue and str(owner) in registered,
                'Unregistered repaired queue bundle')
        require((role=='finish')==(owner==bundle),'Wrong repaired initial/finish bundle roles')
        proof=original.completed_queue(queue,ref['state_sha256'],lambda pid:Path('/proc/%d'%pid).exists(),role)
        request=read(queue/'request.json');script='c32_qualification.py' if role=='initial' else 'c32_finish.py'
        schema='c32-qualification-v1' if role=='initial' else 'c32-final-netlist-finish-v1'
        require(request['schema']==schema and request['bundle']==str(owner) and
            request['bundle_manifest_sha256']==registered[str(owner)] and
            request['queue_sha256']==digest(owner/'workspaces/arch03/scripts'/script), 'Repaired queue source identity changed')
        if role=='finish':
            require(request['synthesis']==proof['state']['synthesis'],'Finish synthesis differs')
            recovery=request.get('lock_storage_recovery')
            if recovery:
                previous=Path(recovery['predecessor']['queue']);old=read(previous/'state.json')
                require(previous!=queue and previous.parent==queue.parent and
                    digest(previous/'state.json')==recovery['predecessor']['state_sha256'] and
                    old['status']=='failed' and old['completed']==[] and
                    not Path('/proc/%d'%old['pid']).exists() and recovery['original_lock_unchanged'] is True and
                    recovery['partial_lock_not_removed'] is True, 'Lock retry predecessor differs')
                driver=Path(req['lock_wait_driver'])
                require(driver.parent==Path(req['runtime_root']) and driver.resolve()==driver and
                    digest(driver)==recovery['source_sha256'], 'Lock retry driver changed')
                proof['inputs'][str(driver)]=recovery['source_sha256']
                proof['inputs'][str(previous/'state.json')]=recovery['predecessor']['state_sha256']
        proof['inputs'][str(queue/'request.json')]=digest(queue/'request.json');proofs[role]=proof
    ref=proofs['finish']['state']['synthesis'];synthesis,_=verify_synthesis(ref['run'],ref['sha256'],cfg)
    require_clear_constraints(ref['run'],synthesis)
    joined=joined_repair(proofs['initial'],proofs['finish'],synthesis)
    exported=exported_report(req['report_run'],req['report_sha256'],joined)
    return dict(queues=joined,export=exported,archive_implies_acceptance=False)
