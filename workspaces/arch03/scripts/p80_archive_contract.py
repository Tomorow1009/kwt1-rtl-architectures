"""Read-only contract for backing up a completed P80 queue and its export.

This does not archive, delete, promote acceptance or interpret other stages'
PASS. P80 stage directories differ from the historical T80 queue layout.
"""
import json
from pathlib import Path
import re

from partition_synth_contract import require, digest
from p80_finish import ORDER as FINISH_ORDER, LAYERS
ORDER=('precision',)+FINISH_ORDER


def read(path):return json.loads(Path(path).read_text())


def completed_queue(queue,expected_sha,owner_alive):
    queue=Path(queue).absolute();path=queue/'state.json'
    require(re.fullmatch('[a-f0-9]{64}',expected_sha or '') and digest(path)==expected_sha,
            'P80 archive queue identity changed')
    state=read(path)
    require(state.get('status')=='reports_ready_review_required' and state.get('finished') and
            type(state.get('pid')) is int and not owner_alive(state['pid']),
            'P80 archive requires a terminal exited queue')
    rows=state.get('completed',[])
    require([row['stage'] for row in rows]==list(ORDER),'P80 archive requires all 18 stages in order')
    require(queue.parent.name=='runs' and re.fullmatch('[A-Za-z0-9_-]{1,40}',queue.name),
            'Invalid P80 queue path')
    references={};identities={str(path):expected_sha}
    for row in rows:
        name=row['stage'];kind='power' if name.startswith('power_') else name
        run=queue.with_name(queue.name+'_'+name)/('p80_'+kind)
        reference=row['reference']
        require(Path(reference['run']).absolute()==run and run.resolve()==run,
                'P80 archive stage path differs from the completed queue')
        summary=run/'summary.json';stage_path=run.parent/'state.json'
        require(digest(summary)==reference['sha256'],'P80 archive stage summary changed')
        receipt=read(stage_path)['stages']['p80_'+kind]
        require(receipt.get('status')=='passed' and receipt.get('finished') and
                receipt.get('summary_sha256')==reference['sha256'] and receipt.get('run')==str(run),
                'P80 archive stage receipt is incomplete')
        identities[str(stage_path)]=digest(stage_path);identities[str(summary)]=reference['sha256']
        references[name]=reference
    require(digest(path)==expected_sha,'P80 queue changed during archive preflight')
    return dict(queue=str(queue),state=state,references=references,inputs=identities,
                stage_accepted=False,archive_implies_acceptance=False)


def exported_report(run,expected_sha,proof):
    run=Path(run).absolute();path=run/'report.json'
    require(digest(path)==expected_sha,'P80 archive export identity changed')
    report=read(path);receipt=read(run/'receipt.json')
    require(report.get('schema')=='arch03-p80-evidence-export-v1' and report.get('stage')=='P80' and
            receipt.get('schema')=='arch03-p80-export-receipt-v1','Not an P80 evidence export')
    require(run.parents[1]==Path(proof['queue']).parent and run.name=='p80_report' and
            run.resolve()==run,'P80 export is outside the completed queue bundle')
    refs=proof['references']
    require(report['references']['synthesis']==proof['state']['synthesis'] and
            report['references']['gate']==refs['gate'] and report['activity_reference']==refs['saif'] and
            report['power_references']==[refs['power_'+name] for name in LAYERS],
            'P80 export combines another netlist or queue')
    precision_path=Path(refs['precision']['run'])/'summary.json'
    require(digest(precision_path)==refs['precision']['sha256'], 'P80 precision changed before export archive')
    precision=read(precision_path)
    require(precision.get('fresh_float_reference_verified') is True and
            report.get('precision_reference')==precision.get('reference'),
            'P80 export precision is not from this completed queue')
    require(receipt.get('artifacts',{}).get('report.json')==expected_sha,
            'P80 export receipt does not bind the report')
    identities={str(path):expected_sha,str(run/'receipt.json'):digest(run/'receipt.json')}
    for name,want in receipt['artifacts'].items():
        require(Path(name).name==name and digest(run/name)==want,'P80 export artifact changed')
        identities[str(run/name)]=want
    return dict(inputs=identities,report=str(run),report_sha256=expected_sha,
                stage_accepted=False,source_modified=False,archive_implies_acceptance=False)
