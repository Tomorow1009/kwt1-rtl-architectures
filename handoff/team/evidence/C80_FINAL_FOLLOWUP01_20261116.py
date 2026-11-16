"""Wait for the original C80 queue; recover precision only if needed; finish PPA.

No live source changes, job restarts, old-queue state edits or automatic freeze.
This file is deployed beside the separately pinned recovery tools, outside the
frozen hardware bundle. All new stages still use its original team lock.
"""
import datetime
import json
import os
from pathlib import Path
import shutil
import sys
import time

ROOT=Path('/tmp/s4_21usr_c80_20261116_1245')
BUNDLE=ROOT/'light-light126-c80-74f3ae7'
MANIFEST='d0f18e4a6aa8a928df37d4347f1a8853c448e823f0685a83c5b710732e5e7a59'
INITIAL=BUNDLE/'runs/c80_initial02'
INITIAL_REQUEST='49db1e2183bf38924af74a3223a088c811e1ccb94a2f25c3d98cc82ab922a9bae'
INITIAL_PID=279630
QUALIFICATION=Path('/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109/bundles/light-light126-systolic-b-v3-20261112_114355-ced0e139a01e/runs/systolic_b_r4_crosscheck02/native_saif_r4_crosscheck')
QUALIFICATION_SHA='a0a9bc6280e7fe5f35b666535157700aac1d9c0b4490873b6199ba9b5c662d26'


def read(path):return json.loads(Path(path).read_text())
def alive(pid):return Path('/proc/%d'%pid).exists()
def now():return datetime.datetime.now().isoformat()


def main():
    ops=Path(__file__).resolve().parent
    sys.path[:0]=[str(ops),str(BUNDLE/'workspaces/arch03/scripts')]
    import server_run as common
    import c80_paths as paths
    import c80_finish as finish
    import c80_precision_recovery as retry
    import c80_archive_contract as contract
    from n1_process import atomic_save
    from partition_synth_contract import require,digest
    require(common.ROOT==BUNDLE and digest(BUNDLE/'manifest.json')==MANIFEST,'Wrong frozen C80 bundle')
    # The delivery bootstrap verifies these independently pinned operation bytes.
    payload=read(ops/'payload.json');before={}
    for name,item in payload['files'].items():
        require(Path(name).name==name and digest(ops/name)==item['sha256'],'Changed followup tool')
        before[str(ops/name)]=item['sha256']
    require(Path(__file__).name in payload['files'],'Followup missing from tool manifest')
    require(digest(INITIAL/'request.json')==INITIAL_REQUEST,'Original initial request differs')
    request=read(INITIAL/'request.json')
    cfg=paths.configure(read(BUNDLE/'handoff/team/server_config.json'),BUNDLE,ROOT,MANIFEST,[])
    common.inputs();runtime=retry.numeric_runtime()
    from c80_saif import qualification
    qualification(QUALIFICATION,QUALIFICATION_SHA,cfg)
    control=ROOT/'c80_followup01.json';recovery=BUNDLE/'runs/c80_precision03';final=BUNDLE/'runs/c80_finish01'
    require(not any(p.exists() for p in (control,recovery,final)),'Preserve existing followup sessions')
    state=dict(status='waiting_original_initial02',pid=os.getpid(),started=now(),
        predecessor=str(INITIAL),predecessor_pid=INITIAL_PID,source_sha256=digest(__file__),
        numerical_runtime=runtime,operation_sources=before,stage_accepted=False,c32_started=False)
    atomic_save(control,state)
    try:
        deadline=time.monotonic()+12*3600
        while True:
            prior=read(INITIAL/'state.json')
            require(prior['pid']==INITIAL_PID and digest(INITIAL/'request.json')==INITIAL_REQUEST,
                    'Original queue identity changed')
            if prior['status'] not in ('running','acquiring_lock') and not alive(INITIAL_PID):break
            require(time.monotonic()<deadline,'Original queue wait timed out; no new jobs launched')
            time.sleep(15)
        state['predecessor_state_sha256']=digest(INITIAL/'state.json');atomic_save(control,state)
        for path,want in before.items():require(digest(path)==want,'Followup tool changed during wait')
        require(not (Path(cfg['server_root'])/'.arch02_team_lock').exists(),'Team lock remains; do not override')
        require(shutil.disk_usage(str(ROOT)).free>=8*1024**3,'Insufficient runtime margin')
        if prior['status']=='failed':
            ref=dict(queue=str(INITIAL),state_sha256=digest(INITIAL/'state.json'),request_sha256=INITIAL_REQUEST)
            retry.predecessor(ref,BUNDLE,alive)  # Reject all failures except the exact missing import.
            state['status']='recovering_precision_only';atomic_save(control,state)
            value=dict(schema=retry.SCHEMA,bundle=str(BUNDLE),recovery_sha256=digest(retry.__file__),predecessor=ref)
            retry.execute(value,recovery)
            actual=read(recovery/'state.json');require(actual['status']=='precision_recovered_review_required',
                'Precision retry did not complete')
            refs={r['stage']:r['reference'] for r in prior['completed']}
            refs['precision']=actual['completed'][0]['reference']
            state['precision_recovery']=dict(queue=str(recovery),state_sha256=digest(recovery/'state.json'),
                                            request_sha256=digest(recovery/'request.json'))
        else:
            proof=contract.completed_queue(INITIAL,digest(INITIAL/'state.json'),alive,'initial')
            refs=proof['references']
        state.update(status='finishing_final_netlist',initial_references=refs);atomic_save(control,state)
        value=dict(schema='c80-final-netlist-finish-v1',bundle=str(BUNDLE),bundle_manifest_sha256=MANIFEST,
            runtime_root=str(ROOT),runtime_evidence=[],queue_sha256=digest(finish.__file__),synthesis=refs['synth'],
            qualification=dict(run=str(QUALIFICATION),sha256=QUALIFICATION_SHA))
        finish.execute(value,final)
        actual=read(final/'state.json')
        require(actual['status']=='reports_ready_review_required','C80 final queue did not complete')
        state.update(status='reports_ready_independent_review_pending',finish_queue=str(final),
                     finish_state_sha256=digest(final/'state.json'))
    except BaseException as error:
        state.update(status='failed',error=str(error));raise
    finally:
        state['finished']=now();atomic_save(control,state)


if __name__=='__main__':main()
