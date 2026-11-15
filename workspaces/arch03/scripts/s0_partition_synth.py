"""Three-DDC T80 mapping, with measured top-context boundary constraints.

S0 only: unchanged T80 RTL and baseline link may be reused after full input
identity checks. Every output lives in a new run; none is a timing PASS.
"""
import json
import math
from pathlib import Path
import re
import shutil
import time

import t80_synth as baseline
import soc_synth
from partition_synth_contract import (require, digest, tcl_path, fingerprint,
    CORNER, PERIOD, area_attribution, characterize_script)

ROOT = Path(__file__).resolve().parents[3]
BASELINE_SUMMARY = 'c485b3f77cd7c4f9d7911c5e2052babbc2d8c83811b94ec72c608ffed027f341'
BASELINE_NETLIST = '6a9ab02be889d4aecb55576a71c51ce68f324fc8a0897430e0dbe40a1373eff2'
BLOCKS = {'accelerator': 'u_arch03_accel', 'shared_sram': 'u_arch03_shared'}


def save(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True)+'\n')


def checked_file(path, want):
    path = Path(path)
    require(path.is_file() and digest(path) == want, 'Changed input: '+str(path))


def verify_origin(origin, bundle):
    """Pins measured T80, not the abandoned T64 DDC or desktop delivery copy."""
    origin = Path(origin).resolve(); bundle = Path(bundle).resolve()
    require('T80_Delivery_20261113' not in origin.parts, 'Use original run, not protected delivery')
    checked_file(origin/'summary.json', BASELINE_SUMMARY)
    result = json.loads((origin/'summary.json').read_text())
    state = json.loads((origin.parent/'state.json').read_text())['stages']['t80_synth']
    require(state['status'] == 'passed' and state['summary_sha256'] == BASELINE_SUMMARY,
            'Original T80 mapping did not complete')
    require(result['synthesis_completed'] and result['scope'] == 't80_whole_soc_task_mode_preliminary_synthesis',
            'Wrong baseline synthesis scope')
    checked_file(origin/'mapped.v', BASELINE_NETLIST)
    for name, want in result['artifacts'].items():
        checked_file(origin/name, want)
    require((origin/'task_mode.sdc').read_text() == baseline.constraints(), 'Original clock or interface assumptions changed')
    traced = {}
    for name in ('source_inputs.json', 'synthesis_inputs.json'):
        for path, want in json.loads((origin/name).read_text()).items():
            checked_file(path, want)
            require(path not in traced or traced[path] == want, 'Conflicting origin identity')
            traced[path] = want
    old = origin.parents[2]
    old_manifest = json.loads((old/'manifest.json').read_text())['files']
    current = json.loads((bundle/'manifest.json').read_text())['files']
    selected = json.loads((bundle/'handoff/team/evidence/S0_T80_SOURCE_IDENTITY_20261115.json').read_text())['files']
    selected = {r['path'] for r in selected}
    selected.update('workspaces/arch03/'+n for n in ('technology_bindings.json', 'memory_technology.json'))
    # Include every actual traced HDL/header, not just the named accelerator.
    for path, want in traced.items():
        try: relative = Path(path).resolve().relative_to(old).as_posix()
        except ValueError: continue
        if relative.startswith('workspaces/') and Path(relative).suffix in ('.sv', '.v', '.vh', '.svh'):
            selected.add(relative)
    for name in sorted(selected):
        require(name in current and current[name] == old_manifest.get(name), 'S0 source changed: '+name)
        checked_file(old/name, current[name]); checked_file(bundle/name, current[name])
    # The reused linked database is an UNMAPPED link of these exact sources.
    require(str(origin/'linked.ddc') in traced, 'Untraced original linked database')
    baseline.area_basis(origin)
    return dict(origin=str(origin), baseline_summary_sha256=BASELINE_SUMMARY,
        baseline_netlist_sha256=BASELINE_NETLIST, traced=traced,
        selected_source_hashes={n: current[n] for n in sorted(selected)},
        origin_artifacts=dict(result['artifacts']), original_summary=result)


def libraries_script(origin, cfg):
    standard = origin/'libs'/Path(cfg['standard_library_member']).name
    memories = sorted(p for p in (origin/'libs').glob('*.db') if p != standard)
    require(standard.is_file() and len(memories) == 2, 'Expected standard and two SRAM DBs')
    return ('set_app_var target_library [list '+tcl_path(standard)+']\n'
        'set_app_var link_library [concat [list *] $target_library [list '+
        ' '.join(tcl_path(p) for p in memories)+']]\n')


def proc_script(body, marker):
    return ('proc s0_execute {} {\n'
        'global target_library\nset_app_var sh_continue_on_error false\n'+body+
        '\nputs "'+marker+'"\n}\n'
        'if {[catch {s0_execute} message]} {puts stderr "Error: S0_ABORT $message"; exit 1}\nquit\n')


FIND_BLOCK = r'''
proc s0_block {suffix} {
    current_design e203_soc_top
    set cell [get_cells -hierarchical -filter "full_name =~ */$suffix"]
    if {[sizeof_collection $cell] != 1} {error "Missing or ambiguous S0 block $suffix"}
    return [list [get_object_name $cell] [get_attribute $cell ref_name]]
}
proc s0_export {suffix destination} {
    set pair [s0_block $suffix]
    current_design [lindex $pair 1]
    write -format verilog -hierarchy -output $destination
    current_design e203_soc_top
}
'''


def block_script(origin, run, block, reference, removed_map_only=(), seed=None):
    require(block in BLOCKS and re.fullmatch(r'[A-Za-z_][A-Za-z0-9_$]*', reference), 'Invalid block identity')
    small, large = (92, 0) if block == 'accelerator' else (0, 64)
    for name in removed_map_only:
        require(re.fullmatch(r'U[0-9]+',name), 'Unexpected removed mapped-cell name')
    absent=''.join('if {[sizeof_collection [get_cells -quiet '+name+']] != 0} {error "Removed map-only cell exists in original RTL: '+name+'"}\n'
                   for name in removed_map_only)
    seeded=('read_ddc '+tcl_path(seed)+'\ncurrent_design '+reference+'\nif {![link]} {error "Recovery seed unresolved"}\n') if seed else ''
    optimization=('set_fix_hold [all_clocks]\ncompile -incremental_mapping -map_effort high\n' if seed else
                  'compile -map_effort high\nset_fix_hold [all_clocks]\ncompile -incremental_mapping -map_effort high\n')
    body = ('source '+tcl_path(run/'libraries.tcl')+'\nread_ddc '+tcl_path(origin/'linked.ddc')+'\n'+FIND_BLOCK+
        'set pair [s0_block '+BLOCKS[block]+']\n'
        'if {[lindex $pair 1] ne "'+reference+'"} {error "Characterized reference differs from linked RTL"}\n'
        'current_design '+reference+'\n'
        'if {![link]} {error "S0 block unresolved references"}\n'+absent+seeded+
        'source '+tcl_path(run/'characterization'/(block+'.characterized.tcl'))+'\n'
        'if {[get_object_name [current_design]] ne "'+reference+'"} {error "Boundary script changed current design"}\n'
        'if {[sizeof_collection [get_clocks hf_clk]] != 1 || abs([get_attribute [get_clocks hf_clk] period]-6.666666)>0.0000001} {error "Bad characterized clock"}\n'
        'set memories [get_cells -hierarchical -filter "ref_name == RAMSP128X16 || ref_name == RAMSP4096X16"]\n'
        'set_dont_touch $memories true\n'
        'set_fix_multiple_port_nets -all -buffer_constants\n'+
        optimization+
        'if {[sizeof_collection [get_cells -hierarchical -filter "ref_name == RAMSP128X16"]] != '+str(small)+
        ' || [sizeof_collection [get_cells -hierarchical -filter "ref_name == RAMSP4096X16"]] != '+str(large)+
        '} {error "Block macro count changed"}\n'
        'redirect area.rpt {report_area -hierarchy}\nredirect check_timing.rpt {check_timing}\n'
        'redirect timing_max.rpt {report_timing -delay_type max -max_paths 100 -significant_digits 8}\n'
        'redirect timing_min.rpt {report_timing -delay_type min -max_paths 100 -significant_digits 8}\n'
        'redirect constraints.rpt {report_constraint -all_violators}\n'
        'write -format ddc -hierarchy -output mapped.ddc\nwrite -format verilog -hierarchy -output mapped.v\n'
        'write_sdc mapped.sdc\n')
    return proc_script(body, 'S0_BLOCK_MAPPED '+block)


def load_children(run):
    return '\n'.join('read_ddc '+tcl_path(run/'blocks'/block/'mapped.ddc') for block in sorted(BLOCKS))+'\n'


def cpu_script(origin, run):
    body = ('source '+tcl_path(run/'libraries.tcl')+'\nread_ddc '+tcl_path(origin/'linked.ddc')+'\n'+
        load_children(run)+FIND_BLOCK+
        'current_design e203_soc_top\nif {![link]} {error "S0 CPU link unresolved"}\n'+baseline.macro_guard()+
        '\nsource '+tcl_path(run/'task_mode.sdc')+'\n'
        'foreach suffix {u_arch03_accel u_arch03_shared} {\n'
        '    set pair [s0_block $suffix]\n    set_dont_touch [get_cells [lindex $pair 0]] true\n}\n'
        'set_dont_touch [get_cells -hierarchical -filter "ref_name == RAMSP128X16 || ref_name == RAMSP4096X16"] true\n'
        'set_fix_multiple_port_nets -all -buffer_constants\ncompile -map_effort high\n'+
        soc_synth.mapped_exceptions()+
        '\nset_fix_hold [all_clocks]\ncompile -incremental_mapping -map_effort high\n'+baseline.macro_guard()+
        '\nwrite -format ddc -hierarchy -output mapped.ddc\nwrite -format verilog -hierarchy -output mapped.v\n'
        'write_sdc mapped.sdc\n'
        's0_export u_arch03_accel accelerator_after_cpu.v\n'
        's0_export u_arch03_shared shared_sram_after_cpu.v\n')
    return proc_script(body, 'S0_CPU_MAPPED children_fixed=true')


def top_script(origin, run, cfg):
    # Exact existing final report implementation; no compile during final link.
    text = baseline.script(run, cfg)
    text = baseline.replace_once(text, 'read_ddc linked.ddc',
        'read_ddc '+tcl_path(run/'blocks/cpu_soc/mapped.ddc')+'\n'+load_children(run))
    text = baseline.replace_once(text, 'compile -map_effort high', '# S0 final link only; mapping occurred per block')
    text = baseline.replace_once(text, 'compile -incremental_mapping -map_effort high', '# No silent top remapping')
    text = baseline.replace_once(text, 'set_fix_multiple_port_nets -all -buffer_constants', '# No topology changes at final link')
    text = baseline.replace_once(text, 'set_fix_hold [all_clocks]', '# Final hold is measured without changes')
    text = baseline.replace_once(text, 'write -format verilog -hierarchy -output mapped.v', FIND_BLOCK+
        '\ns0_export u_arch03_accel accelerator_after_link.v\n'
        's0_export u_arch03_shared shared_sram_after_link.v\n'
        'foreach suffix {u_arch03_accel u_arch03_shared} {\n'
        '    set pair [s0_block $suffix]\n'
        '    set pins [get_pins -of_objects [get_cells [lindex $pair 0]]]\n'
        '    if {[sizeof_collection $pins] == 0} {error "Missing cross-block timing boundary"}\n'
        '    redirect ${suffix}_cross_max.rpt {report_timing -through $pins -delay_type max -max_paths 200 -significant_digits 8}\n'
        '    redirect ${suffix}_cross_min.rpt {report_timing -through $pins -delay_type min -max_paths 200 -significant_digits 8}\n'
        '}\n'
        'redirect hierarchy.rpt {report_hierarchy}\nwrite -format verilog -hierarchy -output mapped.v')
    return text


def module_tokens(text):
    """Canonical mapped Verilog tokens, ignoring only comments and whitespace."""
    text = re.sub(r'/\*.*?\*/|//[^\n]*', '', text, flags=re.S)
    rows = {}
    for match in re.finditer(r'\bmodule\s+([^\s(]+)\s*\(.*?\bendmodule\b', text, re.S):
        name = match.group(1)
        require(name not in rows, 'Duplicate mapped module '+name)
        # Escaped Verilog identifiers end in whitespace. Preserve them as tokens.
        tokens = re.findall(r'\\[^\s]+|[A-Za-z_$][A-Za-z0-9_$]*|[0-9]+\x27[sS]?[bBoOdDhH][0-9a-fA-FxXzZ?_]+|\S', match.group(0))
        rows[name] = tokens
    require(rows and len(rows) == len(re.findall(r'\bmodule\b', text)), 'Incomplete mapped module parsing')
    return rows


def same_blocks(expected, observed):
    a = module_tokens(Path(expected).read_text()); b = module_tokens(Path(observed).read_text())
    require(a == b, 'Mapped child changed during CPU mapping or top linking')
    return dict(module_count=len(a), expected_sha256=digest(expected), observed_sha256=digest(observed),
                equal_tokens=True, comparison='all modules including child definitions; comments/whitespace excluded')


def characterize_inventory(path):
    rows = {}
    for line in Path(path).read_text().splitlines():
        fields = line.split('\t')
        require(len(fields) == 5 and fields[0] in BLOCKS and fields[0] not in rows, 'Invalid characterized inventory')
        block, instance, reference, inputs, outputs = fields
        require(instance.endswith('/'+BLOCKS[block]) and int(inputs)>0 and int(outputs)>0,
                'Missing characterized ports')
        rows[block] = dict(instance=instance, reference=reference, inputs=int(inputs), outputs=int(outputs))
    require(set(rows) == set(BLOCKS), 'Incomplete characterization')
    return rows


def tool_version_from_banner(text):
    """Use a successfully exited DC session, preserving the full patch suffix.

    This installation prints valid version information for -version but exits 1.
    Do not weaken the process ledger's nonzero-exit failure rule to accept it.
    """
    versions = re.findall(r'Version\s+([A-Z]-20\d\d\.\d\d(?:-SP\d+)?(?:-\d+)?)\b', text)
    require(len(set(versions)) == 1, 'Cannot identify exact DC version from startup banner')
    return versions[0]


def restore_clock_precision(exported, native):
    """Undo decimal serialization rounding, retaining every boundary delay.

    Native attributes come from the characterized design under the exact top
    constraints. No clock is added and no non-clock command is changed.
    Unknown script forms fail rather than silently restoring a default budget.
    """
    clocks = {}
    for line in native.splitlines():
        fields = line.split('\t')
        require(len(fields) == 4 and fields[0] not in clocks, 'Invalid native clock inventory')
        name = fields[0]
        require(name in ('hf_clk', 'lf_clk'), 'Unreviewed characterized clock')
        numbers = [float(x) for x in fields[1:]]
        require(all(math.isfinite(x) for x in numbers), 'Nonfinite native clock')
        period, first, second = numbers
        expected = 6.666666 if name == 'hf_clk' else 66.0
        require(abs(period-expected) <= 1e-7 and 0 <= first < second < period,
                'Native characterized clock differs from top clock')
        clocks[name] = fields[1:]
    require('hf_clk' in clocks, 'Missing native HF clock')
    seen = set(); lines = []
    number = r'[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?'
    for line in exported.splitlines(keepends=True):
        if not re.match(r'^\s*create_clock\b', line):
            require(not re.match(r'^\s*create_generated_clock\b', line), 'Generated boundary clock needs explicit review')
            lines.append(line); continue
        names = re.findall(r'-name\s+(?:"([^"]+)"|\{([^}]+)\}|([^\s]+))', line)
        require(len(names) == 1, 'Missing/ambiguous exported clock name')
        name = next(x for x in names[0] if x)
        require(name in clocks and name not in seen, 'Unexpected or repeated exported clock')
        period, first, second = clocks[name]
        p = re.findall(r'-period\s+('+number+r')(?=\s|$)', line)
        w = re.findall(r'-waveform\s+\{\s*('+number+r')\s+('+number+r')\s*\}', line)
        require(len(p) == len(w) == 1, 'Unsupported exported clock syntax')
        # DC's six-significant-digit writer may round; large discrepancies are
        # configuration changes and must not be repaired by this serializer.
        for serialized, actual in zip([p[0]]+list(w[0]), clocks[name]):
            require(abs(float(serialized)-float(actual)) <= max(1e-5,abs(float(actual))*1e-5),
                    'Clock discrepancy is more than serialization rounding')
        line, count = re.subn(r'-period\s+'+number+r'(?=\s|$)', '-period '+period, line)
        require(count == 1, 'Ambiguous clock period replacement')
        line, count = re.subn(r'-waveform\s+\{\s*'+number+r'\s+'+number+r'\s*\}',
                             '-waveform {'+first+' '+second+'}', line)
        require(count == 1, 'Ambiguous clock waveform replacement')
        lines.append(line); seen.add(name)
    require(seen == set(clocks), 'Incomplete exported clock inventory')
    return ''.join(lines)


def remove_mapped_only_directives(text):
    """Drop only old mapped-cell map-only directives; prove absence in RTL later.

    Clock/port/load/timing commands are retained byte-for-byte. Unknown forms
    are rejected, not silently dropped. The raw exported script is preserved.
    """
    lines=[];removed=[]
    for line in text.splitlines(keepends=True):
        if re.match(r'\s*set_map_only\b',line):
            match=re.fullmatch(r'[ \t]*set_map_only\s+\[get_cells\s+(U[0-9]+)\][ \t]*(?:\r?\n)?',line)
            require(match and match.group(1) not in removed,'Unsupported or duplicate exported map-only directive')
            removed.append(match.group(1))
        else:lines.append(line)
    return ''.join(lines),removed


def execute(cfg, run, origin, call, recovery=None):
    run=Path(run); origin=Path(origin).resolve()
    require(not any(run.iterdir()), 'S0 requires a new empty run')
    before = verify_origin(origin, ROOT)
    save(run/'origin_identity.json', before)
    (run/'libraries.tcl').write_text(libraries_script(origin, cfg))
    (run/'task_mode.sdc').write_text(baseline.constraints())
    (run/'libs').mkdir()
    for p in (origin/'libs').glob('*.db'): shutil.copy2(str(p), str(run/'libs'/p.name))
    for name in ('technology_verification.json', 'memory_library_verification.json', 'arch02_sram_config.vh'):
        shutil.copy2(str(origin/name), str(run/name))
    linked_inputs=dict(before['traced'])
    linked_inputs[str((run/'arch02_sram_config.vh').resolve())]=digest(run/'arch02_sram_config.vh')
    for name in ('s0_partition_synth.py','partition_synth_contract.py','s0_server.py'):
        path=Path(__file__).with_name(name).resolve();linked_inputs[str(path)]=digest(path)
    if recovery is not None:
        from s0_recovery import verify_seed
        recovered=verify_seed(recovery['run'],recovery['state_sha256'])
        linked_inputs.update(recovered['inputs'])
        path=Path(__file__).with_name('s0_recovery.py').resolve();linked_inputs[str(path)]=digest(path)
        save(run/'recovery_seed.json',recovered)
    save(run/'source_inputs.json',linked_inputs)
    (run/'tool_version.tcl').write_text('puts "S0_TOOL_VERSION_READY"\nquit\n')
    version = call([cfg['tools']['dc_shell'], '-f', run/'tool_version.tcl'], run, 'tool_version.txt')
    soc_synth.require_tool_marker(version, 'S0_TOOL_VERSION_READY')
    actual_version = tool_version_from_banner(version)
    original_version = tool_version_from_banner((origin/'icb32_synth.log').read_text())
    require(original_version == actual_version, 'Original mapping used another DC version')
    tool = dict(version=actual_version, executable_sha256=digest(Path(cfg['tools']['dc_shell']).resolve()))
    character = run/'characterization'; character.mkdir()
    script = characterize_script(origin/'mapped.ddc', run/'task_mode.sdc', run/'libraries.tcl')
    (character/'characterize.tcl').write_text(script)
    log = call([cfg['tools']['dc_shell'], '-f', character/'characterize.tcl'], character, 'characterize.log')
    soc_synth.require_tool_marker(log, 'S0_CHARACTERIZATION_READY not_mapping_or_acceptance=true')
    identities = characterize_inventory(character/'characterized_blocks.tsv')
    save(run/'boundaries.json', identities)
    precision_receipt = {};removed_map_only={}
    for block in BLOCKS:
        exported = character/(block+'.characterized.tcl')
        original = character/(block+'.characterized.raw.tcl')
        native = character/(block+'.native_clocks.tsv')
        raw = exported.read_text()
        exact = restore_clock_precision(raw, native.read_text())
        clean,removed=remove_mapped_only_directives(exact)
        removed_map_only[block]=removed
        original.write_text(raw); exported.write_text(clean)
        precision_receipt[block] = dict(raw_sha256=digest(original), exact_sha256=digest(exported),
            native_clock_sha256=digest(native), boundary_delays_modified=False,
            removed_mapped_only_cells=removed,
            removed_cells_must_be_absent_in_original_linked_RTL=True,
            operation='restore native clock text precision; remove only absent old mapped-cell set_map_only directives')
    save(run/'clock_serialization.json', precision_receipt)
    library_hashes = {str(p): digest(p) for p in (origin/'libs').glob('*.db')}
    timing = {}; fingerprints = {}
    for block in ('shared_sram', 'accelerator', 'cpu_soc'):
        dest = run/'blocks'/block; dest.mkdir(parents=True)
        budget = character/(block+'.characterized.tcl') if block != 'cpu_soc' else run/'task_mode.sdc'
        dependencies = {'original_link':digest(origin/'linked.ddc'), 'boundary_environment':digest(origin/'mapped.ddc')}
        if block == 'cpu_soc':
            dependencies.update({name:digest(run/'blocks'/name/'mapped.ddc') for name in BLOCKS})
        seed=Path(recovered['seed_ddc']) if recovery is not None and block=='accelerator' else None
        if seed:
            require(removed_map_only[block]==recovered['no_op_cells'],'Recovery differs from original no-op error inventory')
            dependencies['unaccepted_recovery_seed_ddc']=digest(seed)
            dependencies['recovery_receipt']=digest(run/'recovery_seed.json')
        script = cpu_script(origin,run) if block == 'cpu_soc' else block_script(
            origin,run,block,identities[block]['reference'],removed_map_only[block],seed)
        (dest/'compile.tcl').write_text(script)
        # The effective generated compiler script is also a cache dependency.
        dependencies['mapping_script']=digest(dest/'compile.tcl')
        fingerprints[block] = fingerprint(block,before['selected_source_hashes'],
            dict(period_ns=PERIOD,corner=CORNER,row_lanes=5,macro_read_latency=1),library_hashes,
            {str(budget):digest(budget),'task_mode':digest(run/'task_mode.sdc')},tool,dependencies)
        started=time.monotonic()
        log=call([cfg['tools']['dc_shell'],'-f',dest/'compile.tcl'],dest,'compile.log')
        timing[block]=time.monotonic()-started
        soc_synth.require_tool_marker(log, 'S0_CPU_MAPPED children_fixed=true' if block=='cpu_soc' else 'S0_BLOCK_MAPPED '+block)
        for name in ('mapped.ddc','mapped.v','mapped.sdc'):
            require((dest/name).is_file() and (dest/name).stat().st_size>0, 'Missing mapped block '+name)
        shutil.copy2(str(budget),str(dest/'constraints.tcl'))
        shutil.copy2(str(run/'tool_version.txt'),str(dest/'tool_version.txt'))
        save(dest/'cache.json',dict(schema='arch03-s0-partition-cache-v1',status='mapped',fingerprint=fingerprints[block],
            elapsed_seconds=timing[block],artifacts={p.name:digest(p) for p in dest.iterdir() if p.is_file()}))
    child_proof = {}
    for block in BLOCKS:
        child_proof[block] = dict(cpu=same_blocks(run/'blocks'/block/'mapped.v',run/'blocks/cpu_soc'/(block+'_after_cpu.v')))
    (run/'final_link.tcl').write_text(top_script(origin,run,cfg))
    log=call([cfg['tools']['dc_shell'],'-f',run/'final_link.tcl'],run,'final_link.log')
    for block in BLOCKS:
        child_proof[block]['top']=same_blocks(run/'blocks'/block/'mapped.v',run/(block+'_after_link.v'))
    save(run/'child_identity.json',child_proof)
    tracked={str(p):digest(p) for p in run.rglob('*') if p.is_file()}
    save(run/'synthesis_inputs.json',tracked)
    report=baseline.collect_reports(run,dict(status='linked',scope='s0_three_ddc_link',origin=before['origin'],row_lanes=5,
        origin_identity_sha256=digest(run/'origin_identity.json'),block_fingerprints=fingerprints),tracked,log)
    area=json.loads((run/'area_inventory.json').read_text())
    area.pop('conservative_budget_within_1_2mm2',None)
    area.update(project_budget_mm2=1.0,conservative_budget_within_1_0mm2=area['conservative_budget_library_area']<=1e6)
    save(run/'area_inventory.json',area)
    attribution=area_attribution(area); save(run/'partition_area.json',attribution)
    report.update(scope='s0_t80_partitioned_whole_soc_task_mode',project_limit_mm2=1.0,
        area_summary={k:v for k,v in area.items() if k!='rows'},
        partition_area={k:v for k,v in attribution.items() if k!='rows'},block_mapping_seconds=timing,
        block_cache_reused=False,original_unmapped_link_reused=True,child_definitions_checked=True,
        stage_accepted=False)
    if recovery is not None:
        report['incremental_recovery']=dict(seed_sha256=digest(Path(recovered['seed_ddc'])),
            failed_run=recovered['failed_run'],failed_state_sha256=recovered['failed_state_sha256'],
            fresh_compile_and_reports=True,old_failed_state_unchanged=True)
    verify_origin(origin,ROOT)
    report['artifacts']={p.name:digest(p) for p in run.iterdir() if p.is_file()}
    return report
