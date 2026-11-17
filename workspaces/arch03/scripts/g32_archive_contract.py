"""Read-only identity of both completed G32 queues and their own export.

Copying evidence never grants acceptance, deletes a source, or includes old8
as a new result. G32 qualification/precision and final PPA are separate queues.
"""
import json
from pathlib import Path
import re
from partition_synth_contract import require,digest
from g32_qualification import ORDER as INITIAL_ORDER
from g32_finish import ORDER as FINISH_ORDER,LAYERS


def read(path):return json.loads(Path(path).read_text())


def completed_queue(queue,expected_sha,owner_alive,role):
    require(role in ('initial','finish'),'Explicit G32 queue role required')
    order=INITIAL_ORDER if role=='initial' else FINISH_ORDER
    expected_status='qualification_ready_gate_power_pending' if role=='initial' else 'reports_ready_review_required'
    queue=Path(queue).absolute();path=queue/'state.json'
    require(re.fullmatch('[a-f0-9]{64}',expected_sha or '') and digest(path)==expected_sha,
            'G32 archive queue identity changed')
    state=read(path)
    require(state.get('status')==expected_status and state.get('finished') and
            type(state.get('pid')) is int and not owner_alive(state['pid']),
            'G32 archive requires a terminal exited queue')
    rows=state.get('completed',[])
    require([r['stage'] for r in rows]==list(order),'G32 archive requires every stage in order')
    require(queue.parent.name=='runs' and re.fullmatch('[A-Za-z0-9_-]{1,40}',queue.name),
            'Invalid G32 queue path')
    refs={};inputs={str(path):expected_sha}
    for row in rows:
        name=row['stage'];kind='power' if name.startswith('power_') else name
        run=queue.with_name(queue.name+'_'+name)/('g32_'+kind);ref=row['reference']
        require(Path(ref['run']).absolute()==run and run.resolve()==run,
                'G32 archive stage path differs from completed queue')
        summary=run/'summary.json';stage_path=run.parent/'state.json'
        require(digest(summary)==ref['sha256'],'G32 archive stage summary changed')
        receipt=read(stage_path)['stages']['g32_'+kind]
        require(receipt.get('status')=='passed' and receipt.get('finished') and
                receipt.get('summary_sha256')==ref['sha256'] and receipt.get('run')==str(run),
                'Incomplete G32 stage receipt')
        inputs[str(stage_path)]=digest(stage_path);inputs[str(summary)]=ref['sha256'];refs[name]=ref
    require(digest(path)==expected_sha,'G32 queue changed during archive preflight')
    return dict(queue=str(queue),role=role,state=state,references=refs,inputs=inputs,
                stage_accepted=False,archive_implies_acceptance=False)


def joined_queues(initial,finish):
    require(initial['role']=='initial' and finish['role']=='finish' and
            Path(initial['queue']).parent==Path(finish['queue']).parent and
            initial['queue']!=finish['queue'],'G32 requires distinct own initial and finish queues')
    require(finish['state']['synthesis']==initial['references']['synth'],
            'G32 finish did not use this qualification netlist')
    refs=initial['references'];synth=refs['synth'];icg=refs['icg']
    sp=Path(synth['run'])/'summary.json';gp=Path(icg['run'])/'summary.json'
    require(digest(sp)==synth['sha256'] and digest(gp)==icg['sha256'],
            'G32 clock-gating or synthesis summary changed')
    s,g=read(sp),read(gp)
    require(g.get('schema')=='g32-clock-gating-timing-v1' and
            g.get('synthesis_summary_sha256')==synth['sha256'] and
            g.get('netlist_sha256')==s.get('artifacts',{}).get('mapped.v') and
            g.get('actual_g32_cells')==s.get('icg_mapping',{}).get('actual_g32_cells') and
            type(g.get('actual_g32_cells')) is int and g['actual_g32_cells']>0 and
            g.get('static_TE_zero') is True and g.get('enable_path_setup_hold_nonnegative') is True and
            g.get('setup_slack_ns',-1)>=0 and g.get('hold_slack_ns',-1)>=0,
            'G32 archive requires own-netlist complete clock-gating checks')
    return dict(initial=initial,finish=finish,
                inputs=dict(initial['inputs'],**finish['inputs']),archive_implies_acceptance=False)


def exported_report(run,expected_sha,proof):
    run=Path(run).absolute();path=run/'report.json'
    require(digest(path)==expected_sha,'G32 archive export changed')
    report=read(path);receipt=read(run/'receipt.json')
    require(report.get('schema')=='arch03-g32-evidence-export-v1' and report.get('stage')=='G32' and
            report.get('layout_id')==0x00100006 and report.get('numeric_format')=='0x000e0c20' and
            receipt.get('schema')=='arch03-g32-export-receipt-v1','Not a G32 layout6 export')
    require(run.parents[1]==Path(proof['initial']['queue']).parent and run.name=='g32_report' and
            run.resolve()==run,'G32 export outside completed queue bundle')
    initial=proof['initial']['references'];finish=proof['finish']['references']
    require(report['references']['asic']==initial['soc'] and report['references']['synthesis']==initial['synth'] and
            report['references']['gate']==finish['gate'] and report['activity_reference']==finish['saif'] and
            report['power_references']==[finish['power_'+n] for n in LAYERS] and
            report['batch_reference']==initial['batch20'],
            'G32 export combines another netlist, batch or queue')
    p=Path(initial['precision']['run'])/'summary.json'
    require(digest(p)==initial['precision']['sha256'],'G32 precision changed')
    precision=read(p)
    require(precision.get('fresh_float_reference_verified') is True and
            report.get('precision_reference')==precision.get('reference'),
            'G32 export precision differs from completed initial queue')
    require(receipt.get('artifacts',{}).get('report.json')==expected_sha,'G32 export receipt differs')
    inputs={str(path):expected_sha,str(run/'receipt.json'):digest(run/'receipt.json')}
    for name,want in receipt['artifacts'].items():
        require(Path(name).name==name and digest(run/name)==want,'G32 export artifact changed')
        inputs[str(run/name)]=want
    return dict(inputs=inputs,report=str(run),report_sha256=expected_sha,
                stage_accepted=False,source_modified=False,archive_implies_acceptance=False)
