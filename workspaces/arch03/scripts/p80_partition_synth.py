"""Three freshly mapped P80 partitions with explicit boundary-budget provenance.

Only a measured S0 boundary environment is borrowed, after bit-exact port,
corner and library checks. No old linked/mapped design enters P80 mapping.
Final cross-boundary setup/hold comes from the new assembled whole-SoC DDC.
S0 helpers generate commands/reports; their marker names confer no S0 PASS.
"""
import json
from pathlib import Path
import re
import shutil
import time

import p80_link
import s0_partition_synth as templates
import t80_synth as reports
import soc_synth
from partition_synth_contract import require,digest,tcl_path,characterize_script,area_attribution,fingerprint,CORNER,PERIOD

ROOT=Path(__file__).resolve().parents[3]
S0_SUMMARY='e77fac98d9ab9032e431e8bcfe7d0e3d42f33d8b28222d37ceb48777c9bd4916'
S0_NETLIST='8ec59cc89847f18713e7504dc4d7e35eeb491432490209102764165d4409ff12'
BLOCKS=templates.BLOCKS


def save(path,value):
    Path(path).write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')


def verify_budget_origin(origin,new_link):
    origin=Path(origin).resolve();new_link=Path(new_link)
    require('T80_Delivery_20261113' not in origin.parts,'Protected desktop delivery is not a budget source')
    require(digest(origin/'summary.json')==S0_SUMMARY and digest(origin/'mapped.v')==S0_NETLIST,
        'Wrong frozen S0 boundary source')
    report=json.loads((origin/'summary.json').read_text())
    require(report['scope']=='s0_t80_partitioned_whole_soc_task_mode' and report['synthesis_completed'],
        'Not completed S0 partition mapping')
    state=json.loads((origin.parent/'state.json').read_text())['stages']['t80_synth']
    require(state['status']=='passed' and state['summary_sha256']==S0_SUMMARY,'S0 mapping state mismatch')
    for name,want in report['artifacts'].items():
        require(Path(name).name==name and digest(origin/name)==want,'Changed S0 budget artifact '+name)
    require((origin/'task_mode.sdc').read_text()==reports.constraints(),'Boundary source clock/IO constraints differ')
    # The memory DB serializer can embed timestamps. Check original Liberty
    # verification records, independently validated unit evidence and SS corner.
    for name in ('technology_verification.json','memory_library_verification.json'):
        require(json.loads((origin/name).read_text())==json.loads((new_link/name).read_text()),
                'P80/S0 technology verification differs: '+name)
    reports.area_basis(origin);reports.area_basis(new_link)
    return dict(origin=str(origin),summary_sha256=S0_SUMMARY,netlist_sha256=S0_NETLIST,
        mapped_ddc_sha256=digest(origin/'mapped.ddc'),boundary_environment_only=True,
        old_hardware_ddc_reused_for_mapping=False,
        artifacts={str(origin/n):h for n,h in report['artifacts'].items()})


def ports(path):
    result={}
    for line in Path(path).read_text().splitlines():
        fields=line.split('\t')
        require(len(fields)==2 and fields[0] not in result and fields[1] in ('in','out','inout','input','output'),
            'Invalid unique bit-port inventory')
        result[fields[0]]={'input':'in','output':'out'}.get(fields[1],fields[1])
    require(result,'Empty port inventory')
    return result


def translated_budget(raw,native,old_ref,new_ref):
    """Change the design selector only; retain all delay/load/case constraints."""
    require(all(re.fullmatch(r'[A-Za-z_][A-Za-z0-9_$]*',x) for x in (old_ref,new_ref)),
        'Invalid boundary reference name')
    exact=templates.restore_clock_precision(raw,native)
    clean,removed=templates.remove_mapped_only_directives(exact)
    seen=0;lines=[]
    for line in clean.splitlines(keepends=True):
        if re.match(r'^\s*current_design\b',line):
            match=re.fullmatch(r'([ \t]*current_design[ \t]+)(?:\{'+re.escape(old_ref)+r'\}|"'+re.escape(old_ref)+r'"|'+re.escape(old_ref)+r')([ \t]*(?:\r?\n)?)',line)
            require(match is not None,'Unknown exported current_design selector')
            line=match.group(1)+new_ref+match.group(2);seen+=1
        elif old_ref!=new_ref and not line.lstrip().startswith('#'):
            require(not re.search(r'(?<![\w$])'+re.escape(old_ref)+r'(?![\w$])',line),
                'Old design reference outside selector')
        lines.append(line)
    require(seen<=1,'Duplicate boundary design selector')
    return ''.join(lines),removed


def characterization_script(origin,run):
    script=characterize_script(origin/'mapped.ddc',run/'task_mode.sdc',run/'budget_libraries.tcl')
    extra=r'''set port_file [open ${block}.budget_ports.tsv w]
        foreach_in_collection port [get_ports *] {
            puts $port_file "[get_object_name $port]\t[get_attribute $port direction]"
        }
        close $port_file
        '''
    return reports.replace_once(script,'redirect ${block}.characterized_ports.rpt',
        extra+'redirect ${block}.characterized_ports.rpt')


def execute(cfg,run,platform,firmware,origin,call):
    run,origin=Path(run),Path(origin).resolve()
    require(not any(run.iterdir()),'P80 mapping requires a fresh empty run')
    link=run/'fresh_link';link.mkdir()
    linked=p80_link.source_contract(cfg,link,platform,firmware,call)
    origin_identity=verify_budget_origin(origin,link);save(run/'budget_origin.json',origin_identity)
    # Mapping libraries always come from this fresh P80 link. The separate
    # characterization process loads S0's own library paths, avoiding duplicate
    # logical-library containers when that older DDC is read.
    (run/'libraries.tcl').write_text(templates.libraries_script(link,cfg))
    (run/'budget_libraries.tcl').write_text(templates.libraries_script(origin,cfg))
    (run/'task_mode.sdc').write_text(reports.constraints());(run/'libs').mkdir()
    for path in (link/'libs').glob('*.db'):shutil.copyfile(str(path),str(run/'libs'/path.name))
    for name in ('technology_verification.json','memory_library_verification.json','arch02_sram_config.vh'):
        shutil.copyfile(str(link/name),str(run/name))
    (run/'tool_version.tcl').write_text('puts "P80_TOOL_VERSION_READY"\nquit\n')
    version=call([cfg['tools']['dc_shell'],'-f',run/'tool_version.tcl'],run,'tool_version.txt')
    soc_synth.require_tool_marker(version,'P80_TOOL_VERSION_READY')
    tool=dict(version=templates.tool_version_from_banner(version),executable_sha256=digest(Path(cfg['tools']['dc_shell']).resolve()))
    require(tool['version']==templates.tool_version_from_banner((origin/'final_link.log').read_text()),
        'Measured boundary source used a different DC version')
    character=run/'characterization';character.mkdir()
    (character/'characterize.tcl').write_text(characterization_script(origin,run))
    log=call([cfg['tools']['dc_shell'],'-f',character/'characterize.tcl'],character,'characterize.log')
    soc_synth.require_tool_marker(log,'S0_CHARACTERIZATION_READY not_mapping_or_acceptance=true')
    old=templates.characterize_inventory(character/'characterized_blocks.tsv')
    new={}
    for line in (link/'linked_boundaries.tsv').read_text().splitlines():
        fields=line.split('\t');require(len(fields)==3 and fields[0] in BLOCKS and fields[0] not in new,'Invalid P80 boundary')
        require(fields[1].endswith('/'+BLOCKS[fields[0]]),'Wrong P80 block instance')
        new[fields[0]]=dict(instance=fields[1],reference=fields[2])
    require(set(new)==set(BLOCKS),'Missing new boundary inventory')
    precision={};removed={}
    for block in BLOCKS:
        source_ports=ports(character/(block+'.budget_ports.tsv'))
        new_ports=ports(link/(block+'.linked_ports.tsv'))
        require(source_ports==new_ports,'P80 boundary port bits/directions differ; do not borrow old budgets')
        exported=character/(block+'.characterized.tcl');raw=exported.read_text()
        original=character/(block+'.characterized.raw.tcl');original.write_text(raw)
        native=character/(block+'.native_clocks.tsv')
        translated,removed[block]=translated_budget(raw,native.read_text(),old[block]['reference'],new[block]['reference'])
        exported.write_text(translated)
        precision[block]=dict(raw_sha256=digest(original),effective_sha256=digest(exported),
            native_clock_sha256=digest(native),ports=source_ports,source_reference=old[block]['reference'],
            new_reference=new[block]['reference'],port_delay_load_constraints_changed=False,
            removed_mapped_only_cells=removed[block],source_is_S0_budget_not_P80_timing_PASS=True)
    save(run/'boundary_contract.json',precision)
    before=json.loads((link/'source_inputs.json').read_text())
    before.update({str(p.resolve()):digest(p) for p in (link/'linked.ddc',link/'link_receipt.json',
        Path(__file__),Path(templates.__file__),run/'boundary_contract.json',run/'libraries.tcl',run/'task_mode.sdc')})
    save(run/'source_inputs.json',before)
    library_hashes={str(p):digest(p) for p in (link/'libs').glob('*.db')}
    timing={};fingerprints={}
    for block in ('shared_sram','accelerator','cpu_soc'):
        dest=run/'blocks'/block;dest.mkdir(parents=True)
        budget=character/(block+'.characterized.tcl') if block!='cpu_soc' else run/'task_mode.sdc'
        deps=dict(fresh_P80_link=digest(link/'linked.ddc'),boundary_contract=digest(run/'boundary_contract.json'),
            budget_environment=digest(origin/'mapped.ddc'))
        if block=='cpu_soc':deps.update({b:digest(run/'blocks'/b/'mapped.ddc') for b in BLOCKS})
        text=templates.cpu_script(link,run) if block=='cpu_soc' else templates.block_script(
            link,run,block,new[block]['reference'],removed[block])
        (dest/'compile.tcl').write_text(text);deps['mapping_script']=digest(dest/'compile.tcl')
        fingerprints[block]=fingerprint(block,before,dict(period_ns=PERIOD,corner=CORNER,row_lanes=5,
            macro_read_latency=1,transaction_metadata_depth=linked['transaction_metadata_depth'],stage='P80'),
            library_hashes,{str(budget):digest(budget),'task_mode':digest(run/'task_mode.sdc')},tool,deps)
        started=time.monotonic();log=call([cfg['tools']['dc_shell'],'-f',dest/'compile.tcl'],dest,'compile.log')
        timing[block]=time.monotonic()-started
        soc_synth.require_tool_marker(log,'S0_CPU_MAPPED children_fixed=true' if block=='cpu_soc' else 'S0_BLOCK_MAPPED '+block)
        for name in ('mapped.ddc','mapped.v','mapped.sdc'):
            require((dest/name).is_file() and (dest/name).stat().st_size,'Missing P80 mapped block '+name)
        shutil.copyfile(str(budget),str(dest/'constraints.tcl'));shutil.copyfile(str(run/'tool_version.txt'),str(dest/'tool_version.txt'))
        save(dest/'cache.json',dict(schema='arch03-p80-partition-cache-v1',status='mapped',fingerprint=fingerprints[block],
            elapsed_seconds=timing[block],artifacts={p.name:digest(p) for p in dest.iterdir() if p.is_file()}))
    child={b:dict(cpu=templates.same_blocks(run/'blocks'/b/'mapped.v',run/'blocks/cpu_soc'/(b+'_after_cpu.v'))) for b in BLOCKS}
    (run/'final_link.tcl').write_text(templates.top_script(link,run,cfg))
    started=time.monotonic();log=call([cfg['tools']['dc_shell'],'-f',run/'final_link.tcl'],run,'final_link.log')
    link_seconds=time.monotonic()-started
    for block in BLOCKS:child[block]['top']=templates.same_blocks(run/'blocks'/block/'mapped.v',run/(block+'_after_link.v'))
    save(run/'child_identity.json',child)
    tracked=dict(before)
    tracked.update({str(p):digest(p) for p in run.rglob('*') if p.is_file()})
    save(run/'synthesis_inputs.json',tracked)
    result=reports.collect_reports(run,linked,tracked,log)
    area=json.loads((run/'area_inventory.json').read_text());area.pop('conservative_budget_within_1_2mm2',None)
    area.update(project_budget_mm2=1.0,conservative_budget_within_1_0mm2=area['conservative_budget_library_area']<=1e6)
    save(run/'area_inventory.json',area)
    attribution=area_attribution(area);save(run/'partition_area.json',attribution)
    verify_budget_origin(origin,link)
    result.update(scope='p80_partitioned_whole_soc_task_mode',project_limit_mm2=1.0,
        transaction_metadata_depth=linked['transaction_metadata_depth'],old_linked_ddc_reused=False,
        boundary_origin=origin_identity,block_cache_reused=False,block_fingerprints=fingerprints,
        block_mapping_seconds=timing,final_link_seconds=link_seconds,child_definitions_checked=True,
        area_summary={k:v for k,v in area.items() if k!='rows'},partition_area={k:v for k,v in attribution.items() if k!='rows'},
        stage_accepted=False)
    result['artifacts']={p.name:digest(p) for p in run.iterdir() if p.is_file()}
    return result
