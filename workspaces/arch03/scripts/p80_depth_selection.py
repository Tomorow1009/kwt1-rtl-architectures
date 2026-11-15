"""Select the smallest area-qualified P80 depth within 1% of best throughput.

This is a candidate decision, not complete stage acceptance. Formal 240-task,
recovery, gate and power evidence still belongs to the selected configuration.
"""
import argparse
from fractions import Fraction
import json
from pathlib import Path

from partition_synth_contract import require,digest
from p80_window import window_values
from p80_soc import verify_frozen

LAYERS=tuple('layer_%02d'%i for i in range(1,13))


def summarize(run,expected):
    run=Path(run).resolve();require(digest(run/'summary.json')==expected,'Changed P80 performance summary')
    report=json.loads((run/'summary.json').read_text())
    state=json.loads((run.parent/'state.json').read_text())['stages']['p80_soc']
    require(state['status']=='passed' and state['summary_sha256']==expected and
        report['scope']=='asic_rtl_functional' and report['status']=='passed' and
        report['cpu_executed'] is True and report['global_FPGA_defined'] is False,'Require actual ASIC/E203 P80 measurements')
    build_path=run/'p80_build_contract.json'
    require(digest(build_path)==report['build_contract_sha256'],'Changed P80 build')
    build=json.loads(build_path.read_text());verify_frozen(build)
    depth=build['transaction_metadata_depth'];require(depth in (2,4,8),'Unreviewed depth')
    cases={r['case']:r for r in report['cases']}
    require(len(cases)==len(report['cases']) and set(LAYERS)<=set(cases),'Missing or duplicate fixed performance layer')
    rows=[]
    for name in LAYERS:
        row=cases[name];w=row['task_window'];window_values(w)
        require(row['total_outputs']==row['outputs']==25344 and row['capture']['total_checked'] is True and
            row['capture']['mismatches']==0 and row['irq_proof']['enabled'] is True,'Incomplete P80 numeric/IRQ proof')
        require(row['passive_metrics']['measured']['metadata_depth']==depth,'Depth does not match passive hardware measurement')
        require(digest(run/(name+'.log'))==row['log_sha256'] and
            digest(run/(name+'_data/codec.json'))==row['codec_sha256'] and
            digest(run/(name+'_data/layout_manifest.json'))==row['layout_sha256'],'Changed case data/log')
        rows.append(dict(case=name,cycles=w['cycles'],encoded_bytes=w['encoded_bytes'],
            codec_sha256=row['codec_sha256'],layout_sha256=row['layout_sha256'],
            capture_sha256=row['capture']['capture_sha256'],
            metadata_peak=row['passive_metrics']['measured']['metadata_peak']))
    return dict(depth=depth,cycles_sum=sum(r['cycles'] for r in rows),cases=rows,run=str(run),summary_sha256=expected,
        hardware={p:h for p,h in build['files'].items() if p in build['roles']['rtl']},
        source_build_sha256=digest(build_path))


def choose(candidates,area_qualified_depths):
    require(len(candidates)==3 and {r['depth'] for r in candidates}=={2,4,8},'Measure all three metadata depths')
    require(set(area_qualified_depths)<={2,4,8} and len(set(area_qualified_depths))==len(area_qualified_depths),
        'Invalid area-qualified depth set')
    reference=candidates[0]
    for row in candidates:
        require(len(row['cases'])==12 and tuple(c['case'] for c in row['cases'])==LAYERS,'Fixed twelve-layer order changed')
        require(row['cycles_sum']==sum(c['cycles'] for c in row['cases']) and row['cycles_sum']>0,'Invalid cycle sum')
        for a,b in zip(reference['cases'],row['cases']):
            require(all(a[k]==b[k] for k in ('case','encoded_bytes','codec_sha256','layout_sha256','capture_sha256')),
                'Depth comparison changed data, layout or integer results')
    # Source paths differ across immutable packages; match the exact hardware
    # content multiset, whose accepted depth is separately bound in installation.
    hashes=sorted(reference.get('hardware',{}).values());require(hashes,'Missing RTL source identities')
    require(all(sorted(r.get('hardware',{}).values())==hashes for r in candidates),'Depth candidates changed RTL bytes')
    eligible=[r for r in candidates if r['depth'] in area_qualified_depths]
    require(eligible,'No area-qualified candidate; do not silently waive 1.00 mm2')
    best=min(r['cycles_sum'] for r in eligible)
    near=[r for r in eligible if Fraction(best,r['cycles_sum'])>=Fraction(99,100)]
    selected=min(near,key=lambda r:r['depth'])
    return dict(selected_depth=selected['depth'],best_cycles_sum=best,selected_cycles_sum=selected['cycles_sum'],
        selected_task_per_second=150000000.*12/selected['cycles_sum'],
        throughput_fraction_of_best=str(Fraction(best,selected['cycles_sum'])),
        candidate_selection_only=True,stage_accepted=False,
        outstanding_acceptance=['selected-depth ASIC14/recovery/contention/240','same-netlist gate14/SAIF12/PT12','strict timing and complete area review'])


if __name__=='__main__':
    raise SystemExit('Import summarize/choose in the audited stage-report entry; area qualification must use actual mapped evidence.')
