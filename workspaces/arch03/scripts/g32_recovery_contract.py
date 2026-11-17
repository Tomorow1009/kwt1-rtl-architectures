"""Join an immutable failed initial queue with its completed pin-query recovery."""
import json
from pathlib import Path
from partition_synth_contract import require,digest
from g32_qualification_recovery import predecessor,PRIOR_ORDER,ORDER,SCHEMA


def read(p):return json.loads(Path(p).read_text())


def recovered_initial(initial,initial_sha,recovery,recovery_sha,alive):
    initial=Path(initial).absolute();recovery=Path(recovery).absolute();bundle=initial.parent.parent
    prior=predecessor(dict(queue=str(initial),state_sha256=initial_sha),bundle,alive)
    require(recovery.parent==initial.parent and recovery!=initial and recovery.resolve()==recovery,
            'Recovery must be a distinct own queue')
    state_path=recovery/'state.json'
    require(digest(state_path)==recovery_sha,'Recovery state identity changed')
    state=read(state_path)
    require(state.get('schema')==SCHEMA and state.get('status')=='qualification_recovered_gate_power_pending' and
            state.get('finished') and type(state.get('pid')) is int and not alive(state['pid']),
            'Recovery must have completed and exited')
    require([x['stage'] for x in state['completed']]==list(ORDER),'All three recovery stages required')
    request_path=recovery/'request.json';request=read(request_path);original=read(initial/'request.json')
    require(request.get('schema')==SCHEMA and request.get('predecessor')==state.get('predecessor')==
            dict(queue=str(initial),state_sha256=initial_sha),'Recovery predecessor changed')
    require(original.get('schema')=='g32-qualification-v1' and original.get('bundle')==str(bundle) and
            original.get('bundle_manifest_sha256')==digest(bundle/'manifest.json') and
            original.get('queue_sha256')==digest(bundle/'workspaces/arch03/scripts/g32_qualification.py'),
            'Original production identity changed')
    for key in ('bundle','bundle_manifest_sha256','platform','dataset','float_archive',
                'float_archive_sha256','baseline','runtime_root'):
        require(request.get(key)==original.get(key),'Recovery configuration changed: '+key)
    ops=Path(request['operations_root']);manifest_path=ops/'manifest.json'
    require(ops.resolve()==ops and digest(manifest_path)==request['operations_manifest_sha256'],
            'Recovery operations manifest changed')
    inputs=dict(prior['inputs']);inputs[str(manifest_path)]=digest(manifest_path)
    for name,want in read(manifest_path)['files'].items():
        require(Path(name).name==name and digest(ops/name)==want,'Recovery operations file changed')
        inputs[str(ops/name)]=want
    require(request['queue_sha256']==digest(ops/'g32_qualification_recovery.py'),
            'Recovery coordinator identity changed')
    original_code=(bundle/'workspaces/arch03/scripts/g32_icg_timing.py').read_text()
    require(original_code.count('name == E')==2 and original_code.count('name == TE')==1 and
            (ops/'g32_icg_timing_pt2022.py').read_text()==original_code.replace(
                'name == E','full_name =~ */E').replace('name == TE','full_name =~ */TE'),
            'Recovery exceeded the three pin-query corrections')
    require(read(recovery/'predecessor_proof.json')==prior,'Stored predecessor evidence changed')
    refs=dict(prior['references'])
    for row in state['completed']:
        name=row['stage'];run=recovery.with_name(recovery.name+'_'+name)/('g32_'+name);ref=row['reference']
        require(ref['run']==str(run) and run.resolve()==run and digest(run/'summary.json')==ref['sha256'],
                'Recovery stage path or summary changed')
        local=read(run.parent/'state.json')['stages']['g32_'+name]
        require(local.get('status')=='passed' and local.get('finished') and local.get('run')==str(run) and
                local.get('summary_sha256')==ref['sha256'],'Recovery stage not passed')
        refs[name]=ref
        for p in (run/'summary.json',run.parent/'state.json'):inputs[str(p)]=digest(p)
    children=sorted((recovery/'process_ledger').glob('child_*.json'))
    require(children,'Missing recovery process ledger')
    for p in children:
        child=read(p)
        require(child.get('driver_pid')==state['pid'] and child.get('bundle')==str(bundle) and
                child.get('session')==recovery.name and child.get('status')=='exited' and
                child.get('wait_completed') is True and child.get('returncode')==0 and
                child.get('call_status')=='passed' and type(child.get('pid')) is int and not alive(child['pid']),
                'Recovery child incomplete or live')
        inputs[str(p)]=digest(p)
    runtime=Path(request['runtime_root']);launch_path=runtime/(recovery.name+'_launch.json');launch=read(launch_path)
    require(launch['pid']==state['pid'] and launch['request_sha256']==digest(request_path)==
            digest(runtime/(recovery.name+'_request.json')) and launch['initial_state_sha256']==initial_sha and
            launch['operations_manifest_sha256']==request['operations_manifest_sha256'] and
            launch['bundle_manifest_sha256']==request['bundle_manifest_sha256'],
            'Recovery launch identity changed')
    for p in (state_path,request_path,recovery/'predecessor_proof.json',launch_path):inputs[str(p)]=digest(p)
    require(list(refs)==list(PRIOR_ORDER)+list(ORDER) and all(digest(p)==h for p,h in inputs.items()),
            'Joined evidence changed during read')
    prior.update(references=refs,inputs=inputs,qualification_recovery=dict(queue=str(recovery),
        state_sha256=recovery_sha,state=state,operations_manifest_sha256=request['operations_manifest_sha256']),
        archive_implies_acceptance=False)
    return prior
