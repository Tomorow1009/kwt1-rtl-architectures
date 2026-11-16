"""Recover only C32 FLOAT precision after a missing-NumPy predecessor failure.

The old five passed hardware stages and failed queue stay byte-identical.
No synthesis or RTL task is rerun. This entry requires the original driver and
all children to have exited, and takes the unchanged shared coordination lock.
"""
import argparse
import datetime
import json
import os
from pathlib import Path
import re
import sys

import server_run as common
import c32_paths as paths
import c32_qualification as qualification
from n1_process import ProcessLedger, atomic_save
from partition_synth_contract import require, digest

SCHEMA='c32-precision-only-recovery-v1'
ERROR="No module named 'numpy'"
NUMPY=Path('/tmp/s4_21usr_n1_20261113_0210/n1_numpy1195_20261113_0905')
NUMPY_RECEIPT='c1fe14065d6919ff337f2cbf53551f94941acc35d04d3cadabca311fe742eacd'


def read(path):return json.loads(Path(path).read_text())
def now():return datetime.datetime.now().isoformat()


def predecessor(ref,bundle,owner_alive):
    """Bind the exact failed C32 chain; never turn its state into a PASS."""
    queue=Path(ref['queue']).absolute();bundle=Path(bundle).absolute()
    require(queue.parent==bundle/'runs' and queue.resolve()==queue,'Predecessor outside C32 bundle')
    inputs={}
    def checked(path,want=None):
        actual=digest(path);require(want is None or actual==want,'Changed predecessor '+str(path))
        inputs[str(path)]=actual;return read(path)
    state=checked(queue/'state.json',ref['state_sha256'])
    request=checked(queue/'request.json',ref['request_sha256'])
    require(state.get('status')=='failed' and state.get('stage')=='precision' and
            state.get('error')==ERROR and state.get('finished') and
            type(state.get('pid')) is int and not owner_alive(state['pid']),
            'Require exited missing-NumPy failure at precision only')
    require(request.get('schema')=='c32-qualification-v1' and request.get('bundle')==str(bundle) and
            digest(bundle/'manifest.json')==request['bundle_manifest_sha256'] and
            digest(bundle/'workspaces/arch03/scripts/c32_qualification.py')==request['queue_sha256'],
            'Wrong original C32 qualification identity')
    rows=state.get('completed',[]);require([r['stage'] for r in rows]==list(qualification.ORDER[:-1]),
            'Require all five own C32 hardware stages before precision recovery')
    refs={}
    for row in rows:
        name=row['stage'];run=queue.with_name(queue.name+'_'+name)/('c32_'+name);stage=row['reference']
        require(stage['run']==str(run) and run.resolve()==run,'Wrong predecessor stage path')
        checked(run/'summary.json',stage['sha256'])
        receipt=checked(run.parent/'state.json')['stages']['c32_'+name]
        require(receipt.get('status')=='passed' and receipt.get('finished') and
                receipt.get('run')==str(run) and receipt.get('summary_sha256')==stage['sha256'],
                'Incomplete predecessor hardware stage')
        refs[name]=stage
    failed=queue.with_name(queue.name+'_precision')/'c32_precision'
    receipt=checked(failed.parent/'state.json')['stages']['c32_precision']
    require(receipt.get('status')=='failed' and receipt.get('error')==ERROR and
            receipt.get('finished') and receipt.get('run')==str(failed) and
            not (failed/'summary.json').exists() and not (failed/'float20').exists(),
            'Precision failure was not confined to the missing import')
    ledger=queue/'process_ledger';require(ledger.is_dir(),'Missing original child ledger')
    children=sorted(ledger.glob('child_*.json'));require(bool(children),'No original hardware children')
    for path in children:
        child=checked(path)
        require(child.get('driver_pid')==state['pid'] and child.get('bundle')==str(bundle) and
                child.get('session')==queue.name and child.get('status')=='exited' and
                child.get('wait_completed') is True and child.get('returncode')==0 and
                child.get('call_status')=='passed' and not owner_alive(child['pid']),
                'Original child still active or failed')
    for path,want in inputs.items():require(digest(path)==want,'Predecessor changed during audit')
    return dict(queue=str(queue),state=state,request=request,references=refs,inputs=inputs,
                original_failed_state_preserved=True,stage_accepted=False)


def numeric_runtime():
    require(digest(NUMPY/'receipt.json')==NUMPY_RECEIPT,'Pinned NumPy receipt changed')
    receipt=read(NUMPY/'receipt.json')
    require(receipt.get('numpy')=='1.19.5' and receipt.get('all_extracted_hashes_verified') is True and
            Path(receipt['module'])==NUMPY/'numpy/__init__.py','Wrong numerical runtime receipt')
    os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['OMP_NUM_THREADS']='1'
    sys.path.insert(0,str(NUMPY))
    import numpy
    require(numpy.__version__=='1.19.5' and Path(numpy.__file__).resolve()==NUMPY/'numpy/__init__.py',
            'Wrong actual NumPy module')
    return dict(root=str(NUMPY),receipt_sha256=NUMPY_RECEIPT,version=numpy.__version__,
                module_sha256=digest(numpy.__file__),global_environment_modified=False)


def execute(request,queue):
    require(request['schema']==SCHEMA and request['recovery_sha256']==digest(__file__),
            'Wrong C32 recovery source')
    require(request['bundle']==str(common.ROOT),'Wrong C32 recovery bundle')
    proof=predecessor(request['predecessor'],common.ROOT,lambda pid:Path('/proc/%d'%pid).exists())
    original=proof['request']
    cfg=paths.configure(read(common.ROOT/'handoff/team/server_config.json'),common.ROOT,
        Path(original['runtime_root']),original['bundle_manifest_sha256'],original.get('runtime_evidence',[]))
    common.inputs();runtime=numeric_runtime()
    from c32_validation import verify_synthesis
    synth=proof['references']['synth'];verify_synthesis(synth['run'],synth['sha256'],cfg)
    qualification.admit_batch(proof['references'],original)
    require(queue.parent==common.ROOT/'runs' and not queue.exists(),'Use a new precision recovery queue')
    queue.mkdir(parents=True);atomic_save(queue/'request.json',request)
    atomic_save(queue/'predecessor_proof.json',proof);atomic_save(queue/'numeric_runtime.json',runtime)
    state=dict(schema=SCHEMA,status='acquiring_lock',pid=os.getpid(),started=now(),completed=[],
        predecessor=request['predecessor'],stage_accepted=False,c32_b_started=False,g32_started=False,full100_allowed=False)
    atomic_save(queue/'state.json',state)
    ledger=ProcessLedger(common,Path(cfg['server_root'])/'.arch02_team_lock',queue)
    try:
        ledger.acquire();ledger.initialize()
        qualification.run_stage('precision',cfg,queue,state,ledger,original,proof['references'])
        require(predecessor(request['predecessor'],common.ROOT,
            lambda pid:Path('/proc/%d'%pid).exists())==proof,'Old evidence changed during recovery')
        state.update(status='precision_recovered_review_required',current_run=None,finished=now())
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
    require(re.fullmatch('[A-Za-z0-9_-]{1,40}',a.session),'Invalid recovery session')
    require(digest(a.request)==a.request_sha256,'Recovery request changed')
    execute(read(a.request),common.ROOT/'runs'/a.session)


if __name__=='__main__':main()
