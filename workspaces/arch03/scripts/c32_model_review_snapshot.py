"""Join this C32 netlist's completed reports and unknown-net review.

Reads existing evidence only. No EDA, activity assignments, source writes or
automatic acceptance. Conservative area includes all unresolved ownership.
"""
import argparse
from decimal import Decimal
import json
from pathlib import Path

from partition_synth_contract import digest, require
from c32_report import stage
from c32_review_contract import report_identity, synthesis_identity
from mmio8_timing_objects import no_clock, disabled_arcs, jtag_cases
import mmio8_timing_objects as timing_parser


def snapshot(request):
    inputs={}

    def read(path,expected=None):
        path=Path(path);actual=digest(path)
        require(expected is None or actual==expected,'Changed review evidence: '+str(path))
        require(str(path) not in inputs or inputs[str(path)]==actual,'Evidence changed during review')
        inputs[str(path)]=actual
        return json.loads(path.read_text())

    def artifact(run,summary,name):
        path=Path(run)/name;want=summary['artifacts'][name]
        require(digest(path)==want,'Changed review artifact: '+str(path));inputs[str(path)]=want
        return path.read_text()

    require(request['schema']=='c32-model-review-request-v1','Wrong C32 review request')
    report=read(request['report']['path'],request['report']['sha256']);report_identity(report,'C32')
    for key in ('asic14','gate14_without_SDF','final240','activity12','power12_numbers',
                'internal20_precision_verified','fixed12_precision_verified'):
        require(report['verification'][key] is True,'Incomplete C32 verification: '+key)
    sr=report['references']['synthesis'];srun=Path(sr['run'])
    synth=read(srun/'summary.json',sr['sha256']);synthesis_identity(synth,'C32')
    metrics=report['timing_metrics']
    require(metrics==synth['metrics'] and Decimal(str(metrics['period_ns']))==Decimal('6.666666') and
            Decimal(str(metrics['max']))>=0 and Decimal(str(metrics['min']))>=0 and int(metrics['latches'])==0,
            'C32 timing or structure does not meet declared conditions')
    require(report['drc_inventory']['explicit_no_violations'] and
            report['drc_inventory']['extraction_complete'] and
            report['drc_inventory']['violation_record_count']==0,'Unresolved C32 constraints')
    require(report['area']==synth['area_summary'] and report['area']['units']=='um^2' and
            Decimal(str(report['area']['conservative_budget_mm2']))<=Decimal('1.00'),
            'C32 conservative area exceeds the fixed project limit')
    sdc=artifact(srun,synth,'mapped.sdc');static_jtag=jtag_cases(sdc)
    timed=[]
    for ref in report['power_references']:
        run=Path(ref['run']);power=stage(ref,'c32_power');read(run/'summary.json',ref['sha256'])
        require(power['synthesis_summary_sha256']==sr['sha256'] and
                power['activity_summary_sha256']==report['activity_reference']['sha256'],
                'Mixed C32 power configuration')
        clocks=no_clock(artifact(run,power,'timing_check.rpt'))
        arcs=disabled_arcs(artifact(run,power,'disabled_timing.rpt'))
        require(not clocks['groups'].get('unreviewed',0),'Unexplained unclocked C32 pin')
        require(set(arcs['flag_counts'])<=set('cCdp'),'Unexplained user/loop/false/mode disabled arc')
        actual=power['power_clock']['measured']
        require(set(actual)=={'hf_period_ns','lf_period_ns'} and
                Decimal(actual['hf_period_ns'])==Decimal('6.666666') and
                Decimal(actual['lf_period_ns'])==Decimal('66'),'Wrong actual PT clock')
        timed.append(dict(case=power['case'],no_clock=clocks,disabled_arcs=arcs,actual_clocks=actual))
    require([r['case'] for r in timed]==['layer_%02d'%i for i in range(1,13)],'Incomplete/duplicate C32 power set')
    ref=request['connections'];linked=read(ref['path'],ref['sha256']);directory=Path(ref['path']).parent
    state=read(directory.parent/'state.json')
    require(state['status']=='connections_collected_review_required' and
            state['stages'][directory.name]['status']=='passed' and
            state['stages'][directory.name]['summary_sha256']==ref['sha256'] and linked['name']=='C32',
            'Incomplete C32 linked-net review')
    require(linked['input_files'][str(srun/'mapped.v')]==report['netlist_sha256'],
            'Unknown-net review used a different mapped netlist')
    proof=directory/'unknown_connections.tsv';require(digest(proof)==linked['proof_sha256'],'Changed linked-net proof')
    inputs[str(proof)]=linked['proof_sha256']
    ends={tuple(line.split('\t')[2:]) for line in proof.read_text().splitlines() if line.startswith('endpoint\t')}
    critical=[]
    for endpoint,kind,direction,reference in sorted(ends):
        pin=endpoint.rsplit('/',1)[-1]
        if direction in ('in','inout') and (pin in ('CK','CKN','CLK','CP','CPN','RDN','SDN') or
            'CLKLAN' in reference or (reference.startswith('RAMSP') and
            (pin in ('CEN','GWEN','RET1N') or pin.startswith('WEN[')))):
            critical.append(endpoint)
    alias=read(request['aliases']['path'],request['aliases']['sha256'])
    require(alias['inputs_sha256'][ref['path']]==ref['sha256'] and
            alias['complete_target_count']==len(linked['unresolved']) and
            not alias['counts'].get('requires_further_review',0),'Unclassified unknown names')
    for path,want in alias['inputs_sha256'].items():
        require(digest(path)==want,'Changed alias input');inputs[path]=want
    require(not critical,'Unknown explicit clock/reset/ICG/SRAM control endpoint')
    require(all(digest(path)==want for path,want in inputs.items()),'Review input changed')
    return dict(schema='c32-model-review-snapshot-v1',status='facts_joined_manual_conclusion_required',
        inputs_sha256=inputs,source_sha256=digest(__file__),
        parser_sha256=digest(timing_parser.__file__),
        timing_metrics=metrics,static_jtag_cases=static_jtag,power_timing_scope=timed,
        project_conservative_area_mm2=report['area']['conservative_budget_mm2'],
        partition_area=report['synthesis_route']['partition_area'],aggregate=report['aggregate'],
        unknown_review=dict(targets=linked['targets'],resolved=linked['resolved'],
            classified_missing_names=alias['complete_target_count'],alias_counts=alias['counts'],
            unique_leaf_endpoints=len(ends),unknown_explicit_control_pins=critical,
            all_unknowns_waived=False,driver_internal_power_exempted=False),
        stage_accepted=False,system_power_verified=False,physical_signoff=False,
        no_new_eda=True,source_modified=False,
        limits=['Declared stable task mode, static JTAG and pre-layout library/activity models only',
            'Known unknown residence remains part of the recorded PT policy, not a physical error bound',
            'No official600, SDF, extracted parasitics or post-layout signoff'])


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--request',type=Path,required=True)
    p.add_argument('--request-sha256',required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();require(digest(a.request)==a.request_sha256,'Changed snapshot request')
    require(not a.output.exists(),'Preserve previous snapshot');result=snapshot(json.loads(a.request.read_text()))
    require(digest(a.request)==a.request_sha256,'Request changed during snapshot')
    with a.output.open('x') as f:json.dump(result,f,indent=2,sort_keys=True);f.write('\n')
    print('C32_REVIEW_FACTS_JOINED',digest(a.output),'stage_accepted=false',flush=True)
