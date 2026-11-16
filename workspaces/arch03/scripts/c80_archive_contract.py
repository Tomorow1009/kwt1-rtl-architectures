"""Read-only identity of both completed C80 queues and their own export.

Copying evidence never grants acceptance, deletes a source, or includes old8
as a new result. C80 qualification/precision and final PPA are separate queues.
"""
import json
from pathlib import Path
import re
from partition_synth_contract import require,digest
from c80_qualification import ORDER as INITIAL_ORDER
from c80_finish import ORDER as FINISH_ORDER,LAYERS


def read(path):return json.loads(Path(path).read_text())


def completed_queue(queue,expected_sha,owner_alive,role):
    require(role in ('initial','finish'),'Explicit C80 queue role required')
    order=INITIAL_ORDER if role=='initial' else FINISH_ORDER
    expected_status='qualification_ready_gate_power_pending' if role=='initial' else 'reports_ready_review_required'
    queue=Path(queue).absolute();path=queue/'state.json'
    require(re.fullmatch('[a-f0-9]{64}',expected_sha or '') and digest(path)==expected_sha,
            'C80 archive queue identity changed')
    state=read(path)
    require(state.get('status')==expected_status and state.get('finished') and
            type(state.get('pid')) is int and not owner_alive(state['pid']),
            'C80 archive requires a terminal exited queue')
    rows=state.get('completed',[])
    require([r['stage'] for r in rows]==list(order),'C80 archive requires every stage in order')
    require(queue.parent.name=='runs' and re.fullmatch('[A-Za-z0-9_-]{1,40}',queue.name),
            'Invalid C80 queue path')
    refs={};inputs={str(path):expected_sha}
    for row in rows:
        name=row['stage'];kind='power' if name.startswith('power_') else name
        run=queue.with_name(queue.name+'_'+name)/('c80_'+kind);ref=row['reference']
        require(Path(ref['run']).absolute()==run and run.resolve()==run,
                'C80 archive stage path differs from completed queue')
        summary=run/'summary.json';stage_path=run.parent/'state.json'
        require(digest(summary)==ref['sha256'],'C80 archive stage summary changed')
        receipt=read(stage_path)['stages']['c80_'+kind]
        require(receipt.get('status')=='passed' and receipt.get('finished') and
                receipt.get('summary_sha256')==ref['sha256'] and receipt.get('run')==str(run),
                'Incomplete C80 stage receipt')
        inputs[str(stage_path)]=digest(stage_path);inputs[str(summary)]=ref['sha256'];refs[name]=ref
    require(digest(path)==expected_sha,'C80 queue changed during archive preflight')
    return dict(queue=str(queue),role=role,state=state,references=refs,inputs=inputs,
                stage_accepted=False,archive_implies_acceptance=False)


def joined_queues(initial,finish):
    require(initial['role']=='initial' and finish['role']=='finish' and
            Path(initial['queue']).parent==Path(finish['queue']).parent and
            initial['queue']!=finish['queue'],'C80 requires distinct own initial and finish queues')
    require(finish['state']['synthesis']==initial['references']['synth'],
            'C80 finish did not use this qualification netlist')
    return dict(initial=initial,finish=finish,
                inputs=dict(initial['inputs'],**finish['inputs']),archive_implies_acceptance=False)


def exported_report(run,expected_sha,proof):
    run=Path(run).absolute();path=run/'report.json'
    require(digest(path)==expected_sha,'C80 archive export changed')
    report=read(path);receipt=read(run/'receipt.json')
    require(report.get('schema')=='arch03-c80-evidence-export-v1' and report.get('stage')=='C80' and
            report.get('layout_id')==0x00100006 and report.get('numeric_format')=='0x000e0c20' and
            receipt.get('schema')=='arch03-c80-export-receipt-v1','Not a C80 layout6 export')
    require(run.parents[1]==Path(proof['initial']['queue']).parent and run.name=='c80_report' and
            run.resolve()==run,'C80 export outside completed queue bundle')
    initial=proof['initial']['references'];finish=proof['finish']['references']
    require(report['references']['asic']==initial['soc'] and report['references']['synthesis']==initial['synth'] and
            report['references']['gate']==finish['gate'] and report['activity_reference']==finish['saif'] and
            report['power_references']==[finish['power_'+n] for n in LAYERS] and
            report['batch_reference']==initial['batch20'],
            'C80 export combines another netlist, batch or queue')
    p=Path(initial['precision']['run'])/'summary.json'
    require(digest(p)==initial['precision']['sha256'],'C80 precision changed')
    precision=read(p)
    require(precision.get('fresh_float_reference_verified') is True and
            report.get('precision_reference')==precision.get('reference'),
            'C80 export precision differs from completed initial queue')
    require(receipt.get('artifacts',{}).get('report.json')==expected_sha,'C80 export receipt differs')
    inputs={str(path):expected_sha,str(run/'receipt.json'):digest(run/'receipt.json')}
    for name,want in receipt['artifacts'].items():
        require(Path(name).name==name and digest(run/name)==want,'C80 export artifact changed')
        inputs[str(run/name)]=want
    return dict(inputs=inputs,report=str(run),report_sha256=expected_sha,
                stage_accepted=False,source_modified=False,archive_implies_acceptance=False)
