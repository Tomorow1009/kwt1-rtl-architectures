"""Read-only contract for backing up a completed S0 queue and its export.

This does not archive, delete, promote acceptance or interpret other stages'
PASS. S0 stage directories differ from the historical T80 queue layout.
"""
import json
from pathlib import Path
import re

from partition_synth_contract import require, digest
from s0_finish import ORDER, LAYERS


def read(path):return json.loads(Path(path).read_text())


def completed_queue(queue,expected_sha,owner_alive):
    queue=Path(queue).absolute();path=queue/'state.json'
    require(re.fullmatch('[a-f0-9]{64}',expected_sha or '') and digest(path)==expected_sha,
            'S0 archive queue identity changed')
    state=read(path)
    require(state.get('status')=='reports_ready_review_required' and state.get('finished') and
            type(state.get('pid')) is int and not owner_alive(state['pid']),
            'S0 archive requires a terminal exited queue')
    rows=state.get('completed',[])
    require([row['stage'] for row in rows]==list(ORDER),'S0 archive requires all 17 stages in order')
    require(queue.parent.name=='runs' and re.fullmatch('[A-Za-z0-9_-]{1,40}',queue.name),
            'Invalid S0 queue path')
    references={};identities={str(path):expected_sha}
    for row in rows:
        name=row['stage'];kind='power' if name.startswith('power_') else name
        run=queue.with_name(queue.name+'_'+name)/('t80_s0_'+kind)
        reference=row['reference']
        require(Path(reference['run']).absolute()==run and run.resolve()==run,
                'S0 archive stage path differs from the completed queue')
        summary=run/'summary.json';stage_path=run.parent/'state.json'
        require(digest(summary)==reference['sha256'],'S0 archive stage summary changed')
        receipt=read(stage_path)['stages']['t80_'+kind]
        require(receipt.get('status')=='passed' and receipt.get('finished') and
                receipt.get('summary_sha256')==reference['sha256'] and receipt.get('run')==str(run),
                'S0 archive stage receipt is incomplete')
        identities[str(stage_path)]=digest(stage_path);identities[str(summary)]=reference['sha256']
        references[name]=reference
    require(digest(path)==expected_sha,'S0 queue changed during archive preflight')
    return dict(queue=str(queue),state=state,references=references,inputs=identities,
                stage_accepted=False,archive_implies_acceptance=False)


def exported_report(run,expected_sha,proof):
    run=Path(run).absolute();path=run/'report.json'
    require(digest(path)==expected_sha,'S0 archive export identity changed')
    report=read(path);receipt=read(run/'receipt.json')
    require(report.get('schema')=='arch03-s0-evidence-export-v1' and report.get('stage')=='S0' and
            receipt.get('schema')=='arch03-s0-export-receipt-v1','Not an S0 evidence export')
    require(run.parents[1]==Path(proof['queue']).parent and run.name=='t80_s0_report' and
            run.resolve()==run,'S0 export is outside the completed queue bundle')
    refs=proof['references']
    require(report['references']['synthesis']==proof['state']['synthesis'] and
            report['references']['gate']==refs['gate'] and report['activity_reference']==refs['saif'] and
            report['power_references']==[refs['power_'+name] for name in LAYERS],
            'S0 export combines another netlist or queue')
    require(receipt.get('artifacts',{}).get('report.json')==expected_sha,
            'S0 export receipt does not bind the report')
    identities={str(path):expected_sha,str(run/'receipt.json'):digest(run/'receipt.json')}
    for name,want in receipt['artifacts'].items():
        require(Path(name).name==name and digest(run/name)==want,'S0 export artifact changed')
        identities[str(run/name)]=want
    return dict(inputs=identities,report=str(run),report_sha256=expected_sha,
                stage_accepted=False,source_modified=False,archive_implies_acceptance=False)
