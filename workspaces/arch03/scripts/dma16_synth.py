"""Independent DMA16 whole-SoC synthesis; reports are not timing acceptance.

Python 3.6 standard library only. Reuses pinned library verification and the
reviewed task-mode timing assumptions, never an earlier architecture's DDC.
"""
import json
import math
import re
from pathlib import Path

from asic_link import libraries, sha
from install_dma16 import install
from install_platform import platform_sources
from technology_binding import load_bindings
from memory_technology import METADATA
from dc_blocks import measured_metrics
from timing_contract import validate_period
import soc_synth

A3 = Path(__file__).resolve().parents[1]
ROOT = A3.parents[1]
AREA_EVIDENCE = ROOT/'handoff/team/evidence/UNDERGRAD_D3_SERVER_20261109.json'
LINK_MARKER = 'ARCH03_DMA16_LINK_READY whole_soc=true timing_verified=false'
SYNTH_MARKER = 'ARCH03_DMA16_SYNTH_REPORTS_READY timing_verified=false scoring_area_verified=false'
# Independent external contract, intentionally not generated from the installer.
SYSMEM = {'cmd_valid': ('out', 1), 'cmd_ready': ('in', 1),
          'cmd_addr': ('out', 32), 'cmd_read': ('out', 1),
          'cmd_wdata': ('out', 32), 'cmd_wmask': ('out', 4),
          'rsp_valid': ('in', 1), 'rsp_ready': ('out', 1),
          'rsp_rdata': ('in', 32), 'rsp_err': ('in', 1)}
MACROS = {('itcm', 'RAMSP4096X16'): 32, ('dtcm', 'RAMSP4096X16'): 32,
          ('shared', 'RAMSP4096X16'): 64, ('accelerator', 'RAMSP4096X16'): 2,
          ('accelerator', 'RAMSP128X16'): 32}


def sysmem_bits():
    result = {}
    for name, (direction, width) in SYSMEM.items():
        base = 'sysmem_icb_'+name
        for bit in range(width):
            result[base if width == 1 else '%s[%d]' % (base, bit)] = direction
    return result


def port_guard(report='sysmem_ports.tsv'):
    """Audit every declared bit and its inclusion in the actual I/O collections."""
    expected = ' '.join('{%s} %s' % item for item in sorted(sysmem_bits().items()))
    return r'''
unset -nocomplain expected_sysmem seen_sysmem
array set expected_sysmem {@EXPECTED@}
array set seen_sysmem {}
set port_file [open {@REPORT@} w]
foreach_in_collection port [get_ports -quiet sysmem_icb_*] {
    set name [get_object_name $port]
    if {![info exists expected_sysmem($name)] || [info exists seen_sysmem($name)]} {
        error "Unexpected/duplicate SysMem port bit $name"
    }
    set direction [get_attribute $port direction]
    if {$direction eq "input"} {set direction in}
    if {$direction eq "output"} {set direction out}
    if {$direction ne $expected_sysmem($name)} {error "SysMem direction mismatch $name"}
    if {$direction eq "in"} {set group [all_inputs]} else {set group [all_outputs]}
    if {[sizeof_collection [remove_from_collection $port $group]] != 0} {
        error "SysMem port omitted from timed I/O collection $name"
    }
    set seen_sysmem($name) 1
    puts $port_file "$name\t$direction"
}
close $port_file
if {[array size seen_sysmem] != 106} {error "Expected all 106 SysMem port bits"}
# All four input groups receive HF max/min delay and transition below;
# all six output groups receive HF max/min delay and load, including constants.
puts "ARCH03_DMA16_SYSMEM_PORTS groups=10 bits=106 domain=hf_clk"
'''.replace('@EXPECTED@', expected).replace('@REPORT@', report)


def constraints():
    return port_guard()+soc_synth.constraints()


def verify_ports(text):
    actual = {}
    for line in text.splitlines():
        fields = line.split('\t')
        if len(fields) != 2 or fields[0] in actual:
            raise ValueError('Malformed/duplicate SysMem port inventory')
        actual[fields[0]] = fields[1]
    if actual != sysmem_bits():
        raise ValueError('SysMem width/direction inventory mismatch')
    return dict(groups=10, bits=106, input_bits=35, output_bits=71,
                clock='hf_clk', max_delay_ns=1.0, min_delay_ns=0.0,
                input_transition_ns=0.1, output_load_library_units=0.01,
                external_receiver_specification_verified=False)


def verify_top_sysmem(text):
    """Independent ANSI/non-ANSI declaration audit before and after mapping."""
    text = re.sub(r'/\*.*?\*/|//[^\n]*', '', text, flags=re.S)
    tops = re.findall(r'\bmodule\s+e203_soc_top\s*\(.*?\bendmodule\b', text, re.S)
    if len(tops) != 1:
        raise ValueError('Missing/ambiguous DMA16 SoC top')
    actual = {}
    header, body = tops[0].split(');', 1)
    declarations_list = re.findall(r'\b(input|output|inout)\s+(.*?)(?=\b(?:input|output|inout)\b|$)', header, re.S)
    declarations_list += re.findall(r'\b(input|output|inout)\s+([^;]+);', body)
    for direction, declarations in declarations_list:
        match = re.search(r'\[\s*(\d+)\s*:\s*(\d+)\s*\]', declarations)
        width = abs(int(match.group(1))-int(match.group(2)))+1 if match else 1
        names = re.sub(r'\[[^]]+\]|\b(?:wire|reg|logic|signed)\b', '', declarations)
        for name in names.split(','):
            name = name.strip()
            if not name.startswith('sysmem_icb_'):
                continue
            key = name[len('sysmem_icb_'):]
            if key in actual:
                raise ValueError('Duplicate top SysMem declaration')
            if direction == 'inout' or (match and (int(match.group(1)) != width-1 or int(match.group(2)) != 0)):
                raise ValueError('Unexpected SysMem direction or bit indices')
            actual[key] = ('in' if direction == 'input' else 'out', width)
    if actual != SYSMEM:
        raise ValueError('Top SysMem declarations differ from fixed DMA16 contract')


def macro_guard():
    return r'''
set m128 [get_cells -hierarchical -filter "ref_name == RAMSP128X16"]
set m4096 [get_cells -hierarchical -filter "ref_name == RAMSP4096X16"]
if {[sizeof_collection $m128] != 32 || [sizeof_collection $m4096] != 130} {
    error "Expected DMA16 32 small and 130 large SRAM macros"
}
foreach {pattern reference expected} {
    */u_e203_itcm_gnrl_ram/* RAMSP4096X16 32
    */u_e203_dtcm_gnrl_ram/* RAMSP4096X16 32
    */u_arch03_shared/* RAMSP4096X16 64
    */u_arch03_accel/* RAMSP4096X16 2
    */u_arch03_accel/* RAMSP128X16 32
} {
    set count 0
    foreach_in_collection cell [get_cells -hierarchical -filter "ref_name == $reference"] {
        if {[string match $pattern [get_object_name $cell]]} {incr count}
    }
    if {$count != $expected} {error "DMA16 SRAM owner mismatch $pattern $reference"}
}
foreach forbidden {sirv_sim_ram sram_wrap_32KX64 sram_wrap_64KX32 ROM1KX32} {
    if {[sizeof_collection [get_cells -hierarchical -filter "ref_name =~ $forbidden*"]] != 0} {
        error "Functional memory leaked into DMA16 ASIC branch $forbidden"
    }
}
'''


def link_script(standard, databases, sources, includes):
    text = r'''
proc dma16_link {} {
global search_path target_library
set_app_var sh_continue_on_error false
set_app_var search_path [concat [list @INCLUDES@] $search_path]
set_app_var target_library [list @STANDARD@]
set_app_var link_library [concat [list *] $target_library [list @DATABASES@]]
define_design_lib WORK -path ./work
# ASIC only; never FPGA/FPGA_SOURCE or functional RAM implementations.
analyze -format sverilog -define SYNTHESIS [list @SOURCES@]
elaborate e203_soc_top
current_design e203_soc_top
if {![link]} {error "DMA16 whole-SoC unresolved references"}
foreach reference {@TARGET_CELLS@} {
    if {[sizeof_collection [get_lib_cells */$reference]] != 1} {error "Missing/ambiguous cell $reference"}
}
uniquify
@MACROS@
@PORTS@
redirect check_design.rpt {check_design}
redirect references.rpt {report_reference -hierarchy}
redirect hierarchy.rpt {report_hierarchy}
write -format ddc -hierarchy -output linked.ddc
puts "@MARKER@"
}
if {[catch {dma16_link} message]} {
    puts stderr "Error: DMA16_LINK_ABORT $message"
    exit 1
}
quit
'''
    values = {'STANDARD': '{%s}' % standard,
              'DATABASES': ' '.join('{%s}' % p for p in databases),
              'SOURCES': ' '.join('{%s}' % p for p in sources),
              'INCLUDES': ' '.join('{%s}' % p for p in includes),
              'TARGET_CELLS': ' '.join(sorted(v['target'] for v in load_bindings()['cells'].values())),
              'MACROS': macro_guard(), 'PORTS': port_guard('linked_sysmem_ports.tsv'), 'MARKER': LINK_MARKER}
    for key, value in values.items():
        text = text.replace('@'+key+'@', value)
    return text


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise ValueError('Reviewed synthesis template changed: '+old)
    return text.replace(old, new)


def observability_script():
    return r'''
# Diagnostic only: do not retain implementation aliases with dont_touch.
# A gate monitor must use observed names/module boundary pins after mapping.
set probe_file [open mapped_probe_inventory.tsv w]
foreach {label pattern kind} {
    dma_interface */u_arch03_accel/dma_* pin
    core_interface */u_arch03_accel/core/* pin
    core_done_alias */u_arch03_accel/core_done_q* net
    fifo_count_alias */u_arch03_accel/fifo_count_q* net
    half_alias */u_arch03_accel/half_q* net
    load_word_alias */u_arch03_accel/load_word_q* net
    error_alias */u_arch03_accel/error_q* net
} {
    if {$kind eq "pin"} {
        set probes [get_pins -quiet -hierarchical -filter "full_name =~ $pattern"]
    } else {
        set probes [get_nets -quiet -hierarchical -filter "full_name =~ $pattern"]
    }
    puts $probe_file "$label\t[sizeof_collection $probes]\t[get_object_name $probes]"
}
close $probe_file
'''


def script(run, cfg):
    # Share the reviewed report/CDC implementation, with fail-closed exact
    # substitutions. This reads the NEW linked.ddc produced above.
    text = soc_synth.script(run, cfg)
    text = replace_once(text, '!= 138', '!= 162')
    text = replace_once(text, 'source task_mode.sdc', macro_guard()+'\nsource task_mode.sdc')
    text = replace_once(text, 'write -format verilog', macro_guard()+
                        port_guard('mapped_sysmem_ports.tsv')+observability_script()+'\nwrite -format verilog')
    old = 'ARCH03_SOC_SYNTH_REPORTS_READY timing_verified=false scoring_area_verified=false'
    text = replace_once(text, old, SYNTH_MARKER)
    return text


def owner(name):
    for token, category in (('u_e203_itcm_gnrl_ram', 'itcm'), ('u_e203_dtcm_gnrl_ram', 'dtcm'),
                            ('u_arch03_shared', 'shared'), ('u_arch03_accel', 'accelerator'),
                            ('u_arch03_arb', 'dma_arbiter'), ('u_arch03_router', 'dma_router')):
        if token in name.split('/')[:-1]:
            return category
    return 'platform_other'


def area_inventory(text, reported_total):
    rows = []; seen = set(); groups = {}; actual = {}
    memories = json.loads(METADATA.read_text())['cells']
    for line in text.splitlines():
        fields = line.split('\t')
        if len(fields) != 4:
            raise ValueError('Malformed leaf area row')
        name, reference, value, library = fields
        if not name or name in seen or not library:
            raise ValueError('Duplicate/missing leaf instance or library')
        seen.add(name); area = float(value)
        if reference in ('**logic_0**', '**logic_1**'):
            if area != 0 or library != 'builtin_logic_constant':
                raise ValueError('Invalid virtual constant area/source')
            kind = 'virtual_constant'
        else:
            if not math.isfinite(area) or area <= 0 or library == 'builtin_logic_constant':
                raise ValueError('Invalid physical leaf library area')
            kind = 'sram' if reference in memories else 'standard_cell'
            if kind == 'sram' and abs(area-memories[reference]['area']) > 0.01:
                raise ValueError('Mapped SRAM area differs from pinned Liberty')
        category = owner(name)
        group = groups.setdefault(category, {k+'_'+v: 0 for k in
                                  ('standard_cell', 'sram', 'virtual_constant') for v in ('area', 'count')})
        group[kind+'_area'] += area; group[kind+'_count'] += 1
        if kind == 'sram':
            key = category, reference; actual[key] = actual.get(key, 0)+1
        rows.append(dict(instance=name, reference=reference, library=library, area=area, owner=category, kind=kind))
    if actual != MACROS:
        raise ValueError('DMA16 mapped SRAM ownership/count mismatch')
    for category in ('accelerator', 'dma_arbiter', 'dma_router', 'shared'):
        if groups.get(category, {}).get('standard_cell_count', 0) == 0:
            raise ValueError('Missing added logic hierarchy '+category)
    total = sum(r['area'] for r in rows)
    if not math.isfinite(float(reported_total)) or abs(total-float(reported_total)) > max(1., total*1e-5):
        raise ValueError('Leaf area sum disagrees with whole-SoC report')
    known = sum(groups[c]['standard_cell_area']+groups[c]['sram_area'] for c in
                ('accelerator', 'dma_arbiter', 'dma_router'))+groups['shared']['standard_cell_area']
    # Inline IRQ OR/glue can map outside the named new modules. Charge ALL
    # remaining stdcells conservatively, including reusable E203/TCM logic;
    # never hide new cells within a fixed-platform exemption.
    residual = sum(g['standard_cell_area'] for c, g in groups.items() if c not in
                   ('accelerator', 'dma_arbiter', 'dma_router', 'shared'))
    return dict(whole_system_library_area=total, reported_total=float(reported_total), groups=groups,
                leaf_count=len(rows), macro_count=162, physical_sram_bytes=1048*1024,
                known_added_library_area=known, conservative_budget_library_area=known+residual,
                conservative_budget_rule='All SoC standard cells plus all accelerator SRAM; excludes only 64 shared and 64 TCM reused macros',
                reused_sram_library_area={c: groups[c]['sram_area'] for c in ('itcm', 'dtcm', 'shared')},
                units='library units; see separately verified area_basis',
                official_scoring_area_mm2=None, scoring_area_verified=False,
                virtual_constant_note='Only DC logical constants have zero area; no physical tie-cell insertion claimed', rows=rows)


def area_basis(run):
    """Reuse prior exhaustive LEF geometry proof only for identical libraries."""
    basis = json.loads(AREA_EVIDENCE.read_text(encoding='utf8'))['area_basis']
    technology = json.loads((run/'technology_verification.json').read_text())
    memory = json.loads((run/'memory_library_verification.json').read_text())
    pinned = load_bindings(); metadata = json.loads(METADATA.read_text())
    standard_sha = '5d236b1571f5bc791895328fa3f6f94e3873e985ee7963b9ac5e3e849b48949f'
    if technology['library_sha256'] != standard_sha or pinned['library_sha256'] != standard_sha:
        raise ValueError('Area geometry proof is for a different standard library')
    if (basis['units'] != 'um^2' or basis['standard_cells_checked'] != 1276 or
            basis['standard_missing'] != 0 or basis['standard_max_relative_error'] > 1e-10 or
            basis['standard_lef_sha256'] != '561b217e16475a32fb946b2c3ff599e9c9a3e5d6fd100ca73b7a03e8c0d4712b'):
        raise ValueError('Incomplete prior standard-cell area unit cross-check')
    actual = {m['cell']: m for m in memory}
    if len(memory) != 2 or set(actual) != set(metadata['cells']):
        raise ValueError('Incomplete current SRAM library verification')
    geometry = {}
    for cell, spec in metadata['cells'].items():
        old = basis['sram'][cell]; current = actual[cell]
        if (current['sha256'] != spec['sha256'] or abs(current['library_area']-spec['area']) > 1e-6 or
                abs(float(old['width_um'])*float(old['height_um'])-spec['area']) > 1e-6 or
                abs(float(old['area_um2'])-spec['area']) > 1e-6):
            raise ValueError('SRAM geometry or current library fingerprint mismatch')
        geometry[cell] = {k: old[k] for k in ('width_um', 'height_um', 'area_um2', 'lef_sha256')}
    return dict(status='identical_library_geometry_proof_reused', units='um^2',
                source_evidence=str(AREA_EVIDENCE.relative_to(ROOT)), source_sha256=sha(AREA_EVIDENCE),
                standard_liberty_sha256=standard_sha, standard_lef_sha256=basis['standard_lef_sha256'],
                standard_cells_checked=1276, sram=geometry, prior_macro_counts_reused=False,
                physical_signoff=False, official_scoring_verified=False)


def require_loop_free_timing(report):
    # Positive slack after DC breaks a feedback arc is not strict STA proof.
    # Require the actual final mapped check, not a synthetic PASS marker.
    if 'Checking loops' not in report:
        raise ValueError('Missing final mapped timing loop check')
    if re.search(r'TIM-209|timing\s+loops\s+detected|loop\s+breakpoint', report, re.I):
        raise ValueError('Mapped timing contains combinational loops; preserve reports and repair RTL')
    return dict(final_mapped_loop_check_present=True, combinational_loops_detected=False,
                strict_timing_verified=False)


def collect_reports(run, linked, before, text):
    soc_synth.require_tool_marker(text, SYNTH_MARKER)
    loop_check = require_loop_free_timing((run/'check_timing.rpt').read_text())
    metrics = measured_metrics((run/'metrics.txt').read_text(), (run/'area.rpt').read_text())
    validate_period(metrics['period_ns'])
    if float(metrics['lf_period_ns']) != 66 or int(metrics['RAMSP128X16']) != 32 or int(metrics['RAMSP4096X16']) != 130:
        raise ValueError('DMA16 mapped clocks/SRAM count changed')
    ports = verify_ports((run/'mapped_sysmem_ports.tsv').read_text())
    verify_ports((run/'sysmem_ports.tsv').read_text())
    verify_top_sysmem((run/'mapped.v').read_text())
    area = area_inventory((run/'leaf_area.tsv').read_text(), metrics['area'])
    basis = area_basis(run)
    area.update(units='um^2', known_added_mm2=area['known_added_library_area']/1e6,
                conservative_budget_mm2=area['conservative_budget_library_area']/1e6,
                project_budget_mm2=2.0,
                conservative_budget_within_2mm2=area['conservative_budget_library_area'] <= 2e6)
    (run/'area_inventory.json').write_text(json.dumps(area, indent=2)+'\n')
    (run/'area_basis.json').write_text(json.dumps(basis, indent=2)+'\n')
    for name in ('mapped.v', 'mapped.ddc', 'mapped.sdc', 'check_timing.rpt', 'constraints.rpt',
                 'timing_max.rpt', 'timing_min.rpt', 'check_design_mapped.rpt', 'references_mapped.rpt',
                 'qor.rpt', 'hierarchy.rpt', 'mapped_probe_inventory.tsv'):
        if not (run/name).is_file() or not (run/name).stat().st_size:
            raise ValueError('Missing DMA16 synthesis artifact '+name)
    for path, digest in before.items():
        if sha(Path(path)) != digest:
            raise ValueError('DMA16 synthesis input changed: '+path)
    return dict(status='reports_ready_review_required', scope='dma16_whole_soc_task_mode_preliminary_synthesis',
                synthesis_completed=True, timing_verified=False, scoring_area_verified=False,
                setup_hold_nonnegative=min(float(metrics['max']), float(metrics['min'])) >= 0,
                metrics=metrics, loop_check=loop_check,
                area_summary={k: v for k, v in area.items() if k != 'rows'},
                area_basis=basis, sysmem_constraints=ports,
                required_reviews=['All check_timing, unconstrained paths and structural warnings',
                    'Clock propagation, gated clocks, reset release, fixed boot/PLL task mode',
                    'Only four existing LF timer stage-0 CDC exceptions; no SysMem false paths',
                    'HF SysMem 1 ns/0 ns interface assumptions and source timing',
                    'Exact added-area attribution including inline IRQ/glue; conservative total provided',
                    'Mapped gate monitor observability: internal aliases may be optimized; adapt to module ports',
                    'Post-synthesis full 14 cases, all 12 complete-window power runs and activity coverage'],
                gate_monitor_observability_verified=False, gate_simulation_verified=False,
                system_power_verified=False, physical_signoff=False, link_report=linked,
                artifacts={p.name: sha(p) for p in run.iterdir() if p.is_file()})


def synth(cfg, run, platform_source, call):
    from dma16_soc import source_list
    run = Path(run); platform = run/'platform'
    if any((run/name).exists() for name in ('platform', 'libs', 'linked.ddc', 'mapped.v', 'summary.json')):
        raise ValueError('DMA16 synthesis requires a fresh run, never an older mapped DDC')
    manifest = install(platform_source, platform)
    top = platform/'rtl/e203/soc/e203_soc_top.v'
    if not top.is_file():
        candidates = list(platform.rglob('e203_soc_top.v'))
        if len(candidates) != 1:
            raise ValueError('Missing/ambiguous installed SoC top')
        top = candidates[0]
    verify_top_sysmem(top.read_text())
    sources = platform_sources(platform)+source_list()+[A3/'rtl/arch03_tcm_ram.sv']
    if len(sources) != len(set(sources)):
        raise ValueError('Duplicate DMA16 synthesis source')
    includes = list(dict.fromkeys([run, platform/'rtl/e203/core']+[p.parent for p in sources]))
    def library_call(cmd, cwd, name):
        text = call(cmd, cwd, name)
        if re.search(r'(?im)^\s*(Error-|Fatal:|Error:)', text):
            raise ValueError('Library tool errors prevent DMA16 link')
        return text
    standard, databases, lib_inputs = libraries(cfg, run, library_call)
    if any(not path.stat().st_size for path in [standard]+databases):
        raise ValueError('Empty compiled technology database')
    basis = area_basis(run)  # Stop before DC if the reused unit proof is invalid.
    tracked = sources+lib_inputs+[run/'arch02_sram_config.vh', AREA_EVIDENCE]
    tracked += [p for p in platform.rglob('*') if p.is_file()]
    tracked += [p for base in (A3, A3.parent/'arch02') for p in base.rglob('*')
                if p.is_file() and p.suffix in ('.vh', '.svh')]
    tracked += [A3/'scripts'/n for n in ('dma16_synth.py', 'dma16_soc.py', 'install_dma16.py',
                'install_platform.py', 'asic_link.py', 'soc_synth.py', 'dc_blocks.py',
                'technology_binding.py', 'memory_technology.py', 'timing_contract.py')]
    tcl = run/'dma16_link.tcl'; tcl.write_text(link_script(standard, databases, sources, includes))
    tracked += [tcl]
    before = {str(p.resolve()): sha(p) for p in tracked}
    (run/'source_inputs.json').write_text(json.dumps(before, indent=2)+'\n')
    log = call([cfg['tools']['dc_shell'], '-f', tcl], run, 'dma16_link.log')
    soc_synth.require_tool_marker(log, LINK_MARKER)
    if not (run/'linked.ddc').is_file() or not (run/'linked.ddc').stat().st_size:
        raise ValueError('Missing new DMA16 linked DDC')
    verify_ports((run/'linked_sysmem_ports.tsv').read_text())
    for path, digest in before.items():
        if sha(Path(path)) != digest:
            raise ValueError('DMA16 link input changed: '+path)
    linked = dict(status='linked', scope='dma16_whole_soc_link_only', tcm_mode='asic_macro',
                  platform_baseline_sha256=manifest['baseline_sha256'], expected_macros={'RAMSP128X16': 32, 'RAMSP4096X16': 130},
                  library_inputs={str(p): sha(p) for p in lib_inputs}, area_basis=basis,
                  synthesis_verified=False, timing_verified=False, physical_signoff=False)
    sdc = run/'task_mode.sdc'; sdc.write_text(constraints())
    tcl = run/'dma16_synth.tcl'; tcl.write_text(script(run, cfg))
    before.update({str(p.resolve()): sha(p) for p in (run/'linked.ddc', sdc, tcl)})
    (run/'synthesis_inputs.json').write_text(json.dumps(before, indent=2)+'\n')
    log = call([cfg['tools']['dc_shell'], '-f', tcl], run, 'dma16_synth.log')
    return collect_reports(run, linked, before, log)
