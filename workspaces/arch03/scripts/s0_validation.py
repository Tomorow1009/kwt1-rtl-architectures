"""Validate S0 provenance before reusing unchanged T80 gate/SAIF/PT engines.

This is a different synthesis identity, not inheritance of the old netlist PASS.
"""
import json
from pathlib import Path
import re
from partition_synth_contract import require, digest, reusable, area_attribution
from t80_paths import allowed_run
import t80_synth
import s0_partition_synth as mapping

SCOPE='s0_t80_partitioned_whole_soc_task_mode'


def read(path): return json.loads(Path(path).read_text())


def verify_synthesis(run, expected, cfg):
    run=allowed_run(run,cfg,'S0 synthesis')
    require(re.fullmatch('[a-f0-9]{64}',expected or '') and digest(run/'summary.json')==expected,
            'S0 summary identity changed')
    report=read(run/'summary.json');state=read(run.parent/'state.json')['stages']['t80_synth']
    require(state['status']=='passed' and state['summary_sha256']==expected and
            report['scope']==SCOPE and report['synthesis_completed'] is True,
            'S0 final top report collection incomplete')
    require(report['project_limit_mm2']==1.0 and report['area_summary']['project_budget_mm2']==1.0 and
            report['link_report']['scope']=='s0_three_ddc_link' and report['link_report']['row_lanes']==5,
            'Wrong S0 hardware/area contract')
    for name,want in report['artifacts'].items():mapping.checked_file(run/name,want)
    for receipt in ('source_inputs.json','synthesis_inputs.json'):
        for name,want in read(run/receipt).items():mapping.checked_file(name,want)
    require((run/'task_mode.sdc').read_text()==t80_synth.constraints(),'S0 top constraints changed')
    t80_synth.require_loop_free_timing((run/'check_timing.rpt').read_text())
    from timing_contract import validate_period
    validate_period(report['metrics']['period_ns'])
    require(int(report['metrics']['RAMSP128X16'])==92 and int(report['metrics']['RAMSP4096X16'])==128 and
            float(report['metrics']['lf_period_ns'])==66,'S0 SRAM/clocks changed')
    origin=Path(report['link_report']['origin'])
    fresh=mapping.verify_origin(origin,mapping.ROOT)
    require(fresh==read(run/'origin_identity.json'),'Original T80 environment changed')
    proof=read(run/'child_identity.json')
    require(set(proof)==set(mapping.BLOCKS),'Incomplete fixed-child proof')
    for block in ('shared_sram','accelerator','cpu_soc'):
        directory=run/'blocks'/block
        reusable(read(directory/'cache.json'),report['link_report']['block_fingerprints'][block],directory)
    for block in mapping.BLOCKS:
        independent=run/'blocks'/block/'mapped.v'
        for stage,observed in (('cpu',run/'blocks/cpu_soc'/(block+'_after_cpu.v')),
                              ('top',run/(block+'_after_link.v'))):
            row=proof[block][stage]
            require(row['equal_tokens'] is True and row['module_count']>0 and
                    row['expected_sha256']==digest(independent) and row['observed_sha256']==digest(observed),
                    'S0 child-netlist proof changed')
    area=t80_synth.area_inventory((run/'leaf_area.tsv').read_text(),report['metrics']['area'])
    attribution=area_attribution(area)
    require(attribution==read(run/'partition_area.json'),'S0 project/physical area attribution changed')
    t80_synth.area_basis(run)
    t80_synth.verify_top_sysmem((run/'mapped.v').read_text())
    for name in ('sysmem_ports.tsv','mapped_sysmem_ports.tsv'):t80_synth.verify_ports((run/name).read_text())
    original_db={p.name:digest(p) for p in (origin/'libs').glob('*.db')}
    new_db={p.name:digest(p) for p in (run/'libs').glob('*.db')}
    require(new_db==original_db and len(new_db)==3,'S0 linked library bytes changed')
    return report,area
