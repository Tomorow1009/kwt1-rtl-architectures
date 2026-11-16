"""Validate only a freshly linked/mapped C80 partition identity for gate/PPA."""
import hashlib
import json
from pathlib import Path
import re

from partition_synth_contract import require,digest,canonical,area_attribution
from c80_paths import allowed_run
import c80_partition_synth as mapping
import t80_synth as reports
from timing_contract import validate_period

ROOT=Path(__file__).resolve().parents[3]
SCOPE='c80_partitioned_whole_soc_task_mode'


def read(path):return json.loads(Path(path).read_text())


def verify_synthesis(run,expected,cfg):
    run=allowed_run(run,cfg,'C80 synthesis')
    require(re.fullmatch('[a-f0-9]{64}',expected or '') and digest(run/'summary.json')==expected,'C80 summary changed')
    report=read(run/'summary.json');state=read(run.parent/'state.json')['stages']['c80_synth']
    require(state['status']=='passed' and state['summary_sha256']==expected and report['scope']==SCOPE and
        report['synthesis_completed'] is True and report['old_linked_ddc_reused'] is False and
        report['block_cache_reused'] is False,'Not a completed fresh C80 partition synthesis')
    link=report['link_report'];depth=report['transaction_metadata_depth']
    require(depth==2 and link['transaction_metadata_depth']==depth and link['row_lanes']==5 and
        link['schema']=='arch03-c80-fresh-link-v1' and link['old_linked_ddc_reused'] is False and
        link['original_fabric_parameters_modified'] is False,'Wrong C80 link/depth/fabric identity')
    require(report['project_limit_mm2']==1.0 and report['area_summary']['project_budget_mm2']==1.0,
        'C80 must retain 1.00 mm2 budget')
    for name,want in report['artifacts'].items():
        require(Path(name).name==name and digest(run/name)==want,'Changed C80 artifact '+name)
    traced={}
    for receipt in ('source_inputs.json','synthesis_inputs.json'):
        for name,want in read(run/receipt).items():
            require(digest(Path(name))==want and (name not in traced or traced[name]==want),'Changed/conflicting C80 input '+name)
            traced[name]=want
    require((run/'task_mode.sdc').read_text()==reports.constraints(),'C80 top timing assumptions changed')
    reports.require_loop_free_timing((run/'check_timing.rpt').read_text());validate_period(report['metrics']['period_ns'])
    require(int(report['metrics']['RAMSP128X16'])==92 and int(report['metrics']['RAMSP4096X16'])==128 and
        float(report['metrics']['lf_period_ns'])==66,'C80 macro/clock count changed')
    fresh=run/'fresh_link'
    require(digest(fresh/'linked.ddc')==link['linked_ddc_sha256'] and read(fresh/'link_receipt.json')==link,
        'C80 fresh linked design receipt differs')
    require(mapping.verify_budget_origin(Path(report['boundary_origin']['origin']),fresh)==report['boundary_origin'],
        'C80 measured boundary environment changed')
    required={'workspaces/arch03/rtl/'+n for n in ('arch03_c80_accel.sv','arch03_p80_transport.sv',
        'arch03_icb_arb2_queued.sv','arch03_n1_systolic5x16.sv','arch03_n1_linear16x5.sv',
        'arch03_n1_requantize.sv','arch03_c80_decoder.sv')}
    source_bundle=run.parents[2]
    source_manifest=read(source_bundle/'manifest.json')['files'];current_manifest=read(ROOT/'manifest.json')['files']
    hardware={}
    for name,want in traced.items():
        try:relative=Path(name).resolve().relative_to(source_bundle).as_posix()
        except ValueError:continue
        if relative.startswith(('workspaces/arch03/rtl/','workspaces/arch02/rtl/','workspaces/arch02/arch02/rtl/')):
            hardware[relative]=want
    require(required<=set(hardware),'Missing traced C80 hardware')
    for name,want in hardware.items():
        require(source_manifest.get(name)==want and current_manifest.get(name)==want and digest(ROOT/name)==want,
            'Gate/PPA package hardware differs from mapped C80: '+name)
    proof=read(run/'child_identity.json')
    require(set(proof)==set(mapping.BLOCKS),'Incomplete fixed-child proof')
    for block in ('shared_sram','accelerator','cpu_soc'):
        directory=run/'blocks'/block;cache=read(directory/'cache.json');fp=report['block_fingerprints'][block]
        require(cache['schema']=='arch03-c80-partition-cache-v1' and cache['status']=='mapped' and cache['fingerprint']==fp and
            fp['sha256']==hashlib.sha256(canonical(fp['identity'])).hexdigest() and
            fp['identity']['parameters']['stage']=='C80' and fp['identity']['parameters']['transaction_metadata_depth']==depth,
            'Changed C80 block fingerprint')
        for name,want in cache['artifacts'].items():
            require(Path(name).name==name and digest(directory/name)==want,'Changed C80 mapped block '+name)
    for block in mapping.BLOCKS:
        for stage,path in (('cpu',run/'blocks/cpu_soc'/(block+'_after_cpu.v')),('top',run/(block+'_after_link.v'))):
            require(mapping.templates.same_blocks(run/'blocks'/block/'mapped.v',path)==proof[block][stage],
                'C80 child changed during CPU/top mapping')
    area=reports.area_inventory((run/'leaf_area.tsv').read_text(),report['metrics']['area'])
    require(area_attribution(area)==read(run/'partition_area.json'),'C80 area attribution changed')
    reports.area_basis(run);reports.verify_top_sysmem((run/'mapped.v').read_text())
    for name in ('sysmem_ports.tsv','mapped_sysmem_ports.tsv'):reports.verify_ports((run/name).read_text())
    require({p.name:digest(p) for p in (run/'libs').glob('*.db')}==
        {p.name:digest(p) for p in (fresh/'libs').glob('*.db')},'C80 final libraries differ from fresh link')
    return report,area
