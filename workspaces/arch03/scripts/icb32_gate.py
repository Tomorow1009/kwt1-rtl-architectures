"""Strict ICB32 mapped E203 functional checks; no SDF/timing acceptance.

A read-only DC probe binds actual module ports. Missing/optimized hierarchy is
an error, never permission to guess internal aliases or preload task data.
"""
import json
import re
import time
from pathlib import Path
from server_run import ROOT, A2, A3, sha, save, vendor
from gate_soc import mapped_loader, input_values as baseline_inputs
from asic_boot import prepare
from stdcell_verify import extract_model
from icb32_soc import verify_firmware, MARKERS, run_case
from icb32_synth import SYSMEM, area_inventory, verify_top_sysmem, require_loop_free_timing
from icb32_gate_monitor import generate
from icb32_activity import audit_activity
from soc_power import power_databases, tcl_path
from soc_synth import require_tool_marker
from timing_contract import TB_HALF_PERIOD_NS, validate_period
import icb32_data as data

# run_case only handles physical boot, dynamic source and result checking. It
# does not confer the ASIC-RTL build scope on this separately compiled netlist.

SCOPE = 'icb32_whole_soc_mapped_functional_without_SDF'
PROBE_MARKER = 'ICB32_MAPPED_PORT_PROBE_READY netlist_modified=false'
REFERENCES = dict(accel='arch03_icb32_accel', core='arch03_linear16x4', decoder='arch03_icb32_decoder', shared='arch03_shared_sram_turnover',
                  arb='arch03_icb_arb2_turnover', router='arch03_icb_memory_router_turnover')
INSTANCE_SUFFIXES = dict(accel='u_arch03_accel', core='u_arch03_accel/core', decoder='u_arch03_accel/decoder', shared='u_arch03_shared',
                         arb='u_arch03_arb', router='u_arch03_router')
SIMPLE_PATH = r'[A-Za-z_$][A-Za-z0-9_$]*(?:/[A-Za-z_$][A-Za-z0-9_$]*)*'


def interfaces():
    master = dict(SYSMEM)
    slave = {n: ('in' if d == 'out' else 'out', w) for n, (d, w) in master.items()}
    base = dict(clk=('in', 1), rst_n=('in', 1))
    result = {}
    result['accel'] = dict(base, **slave)
    result['accel'].update({'dma_'+n: spec for n, spec in master.items()}); result['accel']['irq'] = ('out', 1)
    result['shared'] = dict(base, **slave)
    result['arb'] = dict(base, **master)
    for prefix in ('cpu_', 'dma_'):
        result['arb'].update({prefix+n: spec for n, spec in slave.items()})
    result['router'] = dict(base, **slave)
    for prefix in ('mem_', 'src_'):
        result['router'].update({prefix+n: spec for n, spec in master.items()})
    for role in ('arb', 'router'):
        result[role]['transaction_pending'] = ('out', 1)
    result['core'] = dict(base, start_valid=('in', 1), start_ready=('out', 1), cancel=('in', 1),
                          prefetch_enable=('in', 1), shift=('in', 5), load_valid=('in', 1),
                          load_ready=('out', 1), load_data=('in', 64), load_count=('in', 3), out_valid=('out', 1),
                          out_ready=('in', 1), out_row=('out', 7), out_column=('out', 8),
                          result=('out', 16), saturated=('out', 1), busy=('out', 1), done=('out', 1), error=('out', 1))
    result['decoder']=dict(base,start=('in',1),cancel=('in',1),encoded_bytes=('in',32),
        in_valid=('in',1),in_ready=('out',1),in_data=('in',32),out_valid=('out',1),
        out_ready=('in',1),out_data=('out',64),out_count=('out',3),busy=('out',1),
        done=('out',1),error=('out',1),error_code=('out',4),accepted_bytes=('out',32),decoded_halfwords=('out',32))
    return result


def port_bits(spec):
    return {name if width == 1 else '%s[%d]' % (name, bit): direction
            for name, (direction, width) in spec.items() for bit in range(width)}


def probe_script(synthesis):
    libraries = power_databases(synthesis)
    text = r'''
proc icb32_probe {} {
    set_app_var sh_continue_on_error false
    set_app_var link_library [list * @LIBS@]
    read_ddc @DDC@
    current_design e203_soc_top
    if {![link]} {error "Mapped ICB32 probe link failed"}
    set out [open mapped_port_probe.tsv w]
    foreach {role reference instance} {@REFERENCES@} {
        # DC also creates hierarchical arithmetic references named e.g.
        # arch03_icb32_accel_DW01_add_*. Match the actual module instance
        # suffix as well; never pick the first prefix match or bind a child.
        set cells [get_cells -quiet -hierarchical -filter "is_hierarchical == true && ref_name =~ $reference* && full_name =~ */$instance"]
        if {[sizeof_collection $cells] != 1} {
            error "Missing/ambiguous actual mapped module ${role}: [get_object_name $cells]"
        }
        set path [get_object_name $cells]
        puts $out "cell\t$role\t$path\t[get_attribute $cells ref_name]"
        foreach_in_collection pin [get_pins -of_objects $cells] {
            puts $out "pin\t$role\t[get_object_name $pin]\t[get_attribute $pin direction]"
        }
    }
    foreach {label pattern} {
        test_mode */u_e203_subsys_hclkgen/test_mode
        pllbypass */u_e203_subsys_hclkgen/pllbypass
        plloutdivby1 */u_e203_subsys_hclkgen/plloutdivby1
        bootrom_selected */u_sirv_aon_wrapper/bootrom_deglitch/io_q
    } {
        set pin [get_pins -quiet -hierarchical -filter "full_name =~ $pattern"]
        if {[sizeof_collection $pin] != 1} {error "Missing/ambiguous mapped clock/boot guard $label"}
        puts $out "guard\t$label\t[get_object_name $pin]\t[get_attribute $pin direction]"
    }
    close $out
    puts "@MARKER@"
}
if {[catch {icb32_probe} message]} {
    puts stderr "Error: ICB32_GATE_PROBE_ABORT $message"
    exit 1
}
quit
'''
    return text.replace('@LIBS@', ' '.join(tcl_path(p) for p in libraries)).replace('@DDC@', tcl_path(synthesis/'mapped.ddc')).replace(
        '@REFERENCES@', ' '.join('%s %s %s' % (role, reference, INSTANCE_SUFFIXES[role])
                                for role, reference in sorted(REFERENCES.items()))).replace('@MARKER@', PROBE_MARKER)


def parse_probe(text, frozen_probe):
    cells = {}; pins = {r: {} for r in REFERENCES}; guards = {}
    for line in text.splitlines():
        fields = line.split('\t')
        if len(fields) != 4:
            raise ValueError('Malformed mapped probe record')
        kind, role, path, value = fields
        if kind == 'cell':
            if role not in REFERENCES or role in cells or not re.fullmatch(SIMPLE_PATH, path) or not re.fullmatch(
                    re.escape(REFERENCES[role])+r'(?:_\w+)?', value):
                raise ValueError('Unknown/duplicate/unsupported mapped module path/reference')
            cells[role] = path
        elif kind == 'pin':
            if role not in pins or path in pins[role]:
                raise ValueError('Unknown/duplicate mapped module pin')
            pins[role][path] = {'input': 'in', 'output': 'out'}.get(value, value)
        elif kind == 'guard':
            if role in guards or not re.fullmatch(SIMPLE_PATH, path) or value not in ('in', 'out', 'input', 'output'):
                raise ValueError('Duplicate/invalid mapped clock/boot probe')
            guards[role] = path
        else:
            raise ValueError('Unknown probe record kind')
    if set(cells) != set(REFERENCES) or len(set(cells.values())) != 6:
        raise ValueError('Incomplete/aliased six-module mapped hierarchy')
    if cells['core'] != cells['accel']+'/core' or cells['decoder'] != cells['accel']+'/decoder':
        raise ValueError('Actual core instance is not under the observed accelerator')
    if any(cells[r].rsplit('/', 1)[0] != cells['accel'].rsplit('/', 1)[0] for r in ('shared', 'arb', 'router')):
        raise ValueError('Mapped fabric modules do not share the observed subsystem')
    for role, specification in interfaces().items():
        expected = {cells[role]+'/'+name: direction for name, direction in port_bits(specification).items()}
        if pins[role] != expected:
            raise ValueError('Mapped interface direction/width/port mismatch: '+role)
    if set(guards) != {'test_mode', 'pllbypass', 'plloutdivby1', 'bootrom_selected'}:
        raise ValueError('Incomplete actual clock/boot mode probe')
    clock_roots = {guards[k].rsplit('/', 1)[0] for k in ('test_mode', 'pllbypass', 'plloutdivby1')}
    if len(clock_roots) != 1 or not next(iter(clock_roots)).endswith('/u_e203_subsys_hclkgen'):
        raise ValueError('Ambiguous actual mapped clock guard')
    if not guards['bootrom_selected'].endswith('/u_sirv_aon_wrapper/bootrom_deglitch/io_q'):
        raise ValueError('Wrong actual mapped boot guard')
    prior = {}
    for line in frozen_probe.splitlines():
        fields = line.split('\t', 2)
        if len(fields) != 3 or fields[0] in prior or not fields[1].isdigit():
            raise ValueError('Malformed frozen synthesis probe')
        names = fields[2].split()
        if len(names) != int(fields[1]) or len(set(names)) != len(names):
            raise ValueError('Frozen synthesis probe count mismatch')
        prior[fields[0]] = set(names)
    needed_dma = {n for n in pins['accel'] if n.startswith(cells['accel']+'/dma_')}
    frozen_counts = {}
    for group, role, expected, pattern in (
            ('dma_interface', 'accel', needed_dma, 'dma_'),
            ('core_interface', 'core', set(pins['core']), ''),
            ('decoder_interface', 'decoder', set(pins['decoder']), '')):
        names = prior.get(group, set()); prefix = cells[role]+'/'
        # DC full_name wildcards also match pins below descendant cells.
        # Verify the exact direct module boundary, retaining all raw evidence.
        if any(not n.startswith(prefix+pattern) for n in names):
            raise ValueError('Frozen synthesis probe contains a foreign hierarchy: '+group)
        direct = {n for n in names if '/' not in n[len(prefix):]}
        if direct != expected:
            raise ValueError('Mapped DC probe disagrees with frozen synthesis DMA/core interface')
        frozen_counts[group] = dict(total=len(names), direct=len(direct), descendants=len(names-direct))
    convert = lambda path: 'u_e203_soc_top.'+path.replace('/', '.')
    return dict(bindings={r: convert(path) for r, path in cells.items()},
                guards={r: convert(path) for r, path in guards.items()},
                cells=cells, port_interfaces=interfaces(), pin_counts={r: len(p) for r, p in pins.items()},
                frozen_synthesis_interfaces_crosschecked=True, frozen_probe_counts=frozen_counts,
                alias_binding_used=False)


def verify_synthesis(synthesis, expected_sha, cfg):
    synthesis = Path(synthesis).resolve(); synthesis.relative_to(Path(cfg['server_root']).resolve())
    summary_path = synthesis/'summary.json'
    if not re.fullmatch('[a-f0-9]{64}', expected_sha) or sha(summary_path) != expected_sha:
        raise ValueError('ICB32 synthesis summary digest mismatch')
    summary = json.loads(summary_path.read_text())
    state = json.loads((synthesis.parent/'state.json').read_text()).get('stages', {}).get('icb32_synth', {})
    if (state.get('status') != 'passed' or state.get('summary_sha256') != expected_sha or
            summary.get('synthesis_completed') is not True or summary.get('scope') != 'icb32_whole_soc_task_mode_preliminary_synthesis'):
        raise ValueError('ICB32 synthesis report collection not complete')
    required = ('mapped.v', 'mapped.ddc', 'mapped.sdc', 'leaf_area.tsv', 'area_inventory.json',
                'source_inputs.json', 'synthesis_inputs.json', 'mapped_probe_inventory.tsv',
                'mapped_sysmem_ports.tsv', 'area_basis.json', 'check_timing.rpt')
    for name in required:
        if sha(synthesis/name) != summary['artifacts'][name]:
            raise ValueError('Changed ICB32 synthesis artifact '+name)
    require_loop_free_timing((synthesis/'check_timing.rpt').read_text())
    traced = {}
    for receipt in ('source_inputs.json', 'synthesis_inputs.json'):
        for name, digest in json.loads((synthesis/receipt).read_text()).items():
            if sha(Path(name)) != digest:
                raise ValueError('Changed ICB32 synthesis input '+name)
            if name in traced and traced[name] != digest:
                raise ValueError('Conflicting ICB32 synthesis input receipts')
            traced[name] = digest
    source_bundle = synthesis.parents[2]
    old_manifest = json.loads((source_bundle/'manifest.json').read_text())['files']
    current = json.loads((ROOT/'manifest.json').read_text())['files']
    # Compare only actual traced hardware, not every file in either package.
    # Later bundles may add unrelated test firmware/RTL without changing the
    # mapped design. The selected gate firmware has its own verify_firmware
    # source/ELF/boot manifest check and is frozen in gate/source_inputs.json.
    prefixes = ('workspaces/arch02/rtl/', 'workspaces/arch02/arch02/rtl/', 'workspaces/arch03/rtl/')
    hardware = {}
    for name, digest in traced.items():
        path = Path(name).resolve()
        try:
            relative = path.relative_to(source_bundle).as_posix()
        except ValueError:
            continue
        if relative.startswith(prefixes) and path.suffix in ('.v', '.sv', '.vh', '.svh'):
            hardware[relative] = digest
    if not hardware:
        raise ValueError('Synthesis receipts have no traced production hardware')
    preparation = ['workspaces/arch03/scripts/'+n for n in ('install_platform.py', 'install_dma16.py', 'install_icb32.py',
                   'technology_binding.py', 'memory_technology.py', 'timing_contract.py', 'icb32_synth.py')]
    preparation += ['workspaces/arch03/'+n for n in ('technology_bindings.json', 'memory_technology.json')]
    for relative in preparation+list(hardware):
        digest = old_manifest.get(relative)
        if (not digest or (relative in hardware and hardware[relative] != digest) or
                current.get(relative) != digest or sha(source_bundle/relative) != digest or sha(ROOT/relative) != digest):
            raise ValueError('Changed ICB32 hardware preparation '+relative)
    validate_period(summary['metrics']['period_ns'])
    if int(summary['metrics']['RAMSP128X16']) != 96 or int(summary['metrics']['RAMSP4096X16']) != 128:
        raise ValueError('Wrong ICB32 mapped macro inventory')
    area = area_inventory((synthesis/'leaf_area.tsv').read_text(), summary['metrics']['area'])
    verify_top_sysmem((synthesis/'mapped.v').read_text())
    power_databases(synthesis)
    return summary, area


def probe_mapped(cfg, run, synthesis, call):
    tracked = [synthesis/n for n in ('mapped.ddc', 'mapped.v', 'mapped_probe_inventory.tsv')]+power_databases(synthesis)
    before = {str(path): sha(path) for path in tracked}
    tcl = run/'mapped_probe.tcl'; tcl.write_text(probe_script(synthesis)); before[str(tcl)] = sha(tcl)
    command = [cfg['tools']['dc_shell'], '-f', tcl]
    save(run/'probe_command.json', [str(p) for p in command])
    log = call(command, run, 'mapped_probe.log'); require_tool_marker(log, PROBE_MARKER)
    result = parse_probe((run/'mapped_port_probe.tsv').read_text(), (synthesis/'mapped_probe_inventory.tsv').read_text())
    for name, digest in before.items():
        if sha(Path(name)) != digest:
            raise ValueError('Mapped probe input changed')
    result.update(status='actual_mapped_module_ports_verified', source_inputs=before,
                  command_sha256=sha(run/'probe_command.json'), log_sha256=sha(run/'mapped_probe.log'),
                  port_probe_sha256=sha(run/'mapped_port_probe.tsv'), netlist_modified=False)
    save(run/'mapped_binding_receipt.json', result)
    return result


def verify_gate_memory_config(synthesis, run):
    # This production include is generated per run, so it has no package-relative
    # counterpart. Match the actual gate vendor configuration to its traced
    # synthesis input instead of accidentally exempting it with test headers.
    inputs = json.loads((synthesis/'source_inputs.json').read_text())
    matches = [(Path(name), digest) for name, digest in inputs.items()
               if Path(name).name == 'arch02_sram_config.vh']
    if len(matches) != 1:
        raise ValueError('Missing/ambiguous traced synthesis SRAM configuration')
    original, digest = matches[0]
    if sha(original) != digest or sha(run/'arch02_sram_config.vh') != digest:
        raise ValueError('Gate SRAM model configuration differs from synthesized hardware')


def testbench(netlist, probe):
    verify_top_sysmem(netlist)
    values = baseline_inputs()
    top = re.findall(r'\bmodule\s+e203_soc_top\s*\(.*?\bendmodule\b', netlist, re.S)
    if len(top) != 1:
        raise ValueError('Missing/duplicate mapped SoC top')
    inputs = []
    for declaration in re.findall(r'\binput\s+([^;]+);', top[0]):
        names = re.sub(r'\[[^]]+\]|\b(?:wire|reg|logic|signed)\b', '', declaration)
        inputs.extend(n.strip() for n in names.split(','))
    expected_inputs = set(values)|{'sysmem_icb_'+n for n, (direction, _) in SYSMEM.items() if direction == 'in'}
    if len(inputs) != len(set(inputs)) or set(inputs) != expected_inputs:
        raise ValueError('Unreviewed mapped top input ports')
    declarations = []
    for name, (_, width) in SYSMEM.items():
        values['sysmem_icb_'+name] = 'a3_source_'+name
        declarations.append('wire %sa3_source_%s;' % ('' if width == 1 else '[%d:0] ' % (width-1), name))
    return '''`timescale 1ns/1fs
module tb_top;
reg clk=0,lfextclk=0,rst_n=0;
always #@HALF@ clk <= ~clk;
always #33 lfextclk <= ~lfextclk;
initial begin #120 rst_n <= 1; end
@WIRES@
e203_soc_top u_e203_soc_top(
@PORTS@);
`include "arch03_asic_boot.svh"
`include "arch03_icb32_gate_monitor.svh"
arch03_clock_mode_guard a3_gate_mode(.clk(a3_mon_clk),.rst_n(a3_mon_rst_n),
    .active(a3_window_active),.finished(a3_window_finished),
@GUARDS@);
endmodule
'''.replace('@HALF@', TB_HALF_PERIOD_NS).replace('@WIRES@', '\n'.join(declarations)).replace(
        '@PORTS@', ',\n'.join('    .%s(%s)' % item for item in sorted(values.items()))).replace(
        '@GUARDS@', ',\n'.join('    .%s(%s)' % item for item in sorted(probe['guards'].items())))


def verify(cfg,run,synthesis,expected_sha,cases,call,activity_cases=(),firmware=None):
    run,synthesis=Path(run),Path(synthesis).resolve()
    data.require(cases and len(cases)==len(set(cases)) and set(cases)<=set(data.CASES14) and
                 set(activity_cases)<=set(cases),'Invalid gate case selection')
    data.require(not any((run/n).exists() for n in ('simv','source_inputs.json','mapped_probe.tcl','summary.json')),
                 'ICB32 gate requires a fresh directory')
    summary,area=verify_synthesis(synthesis,expected_sha,cfg)
    firmware=Path(firmware or ROOT/'firmware').resolve();firmware.relative_to(ROOT.resolve())
    fw,base=verify_firmware(firmware)
    data.require(summary['link_report']['row_lanes']==fw['configuration']['row_lanes'],
                 'Gate firmware row lanes differ from synthesized hardware')
    probe=probe_mapped(cfg,run,synthesis,call)
    loader=run/'arch03_asic_boot.svh';loader.write_text(mapped_loader(area))
    monitor=run/'arch03_icb32_gate_monitor.svh'
    monitor.write_text(generate((A3/'tb/arch03_icb32_monitor.svh').read_text(),probe['bindings']))
    tb=run/'tb_top.sv';tb.write_text(testbench((synthesis/'mapped.v').read_text(),probe))
    model=extract_model(cfg,run)
    modules=[A3/'tb'/n for n in ('arch03_task_window_icb32.sv','arch03_icb32_source.sv',
             'arch03_clock_mode_guard.sv','arch03_icb32_gate_proof.sv')]
    files=[synthesis/'mapped.v']+modules+[tb,model]+vendor(cfg,run)
    verify_gate_memory_config(synthesis,run)
    tracked=files+[loader,monitor,firmware/'manifest.json',synthesis/'summary.json',
        run/'arch02_sram_config.vh',run/'mapped_binding_receipt.json',run/'mapped_port_probe.tsv',
        run/'mapped_probe.tcl',run/'mapped_probe.log',run/'probe_command.json',A3/'tb/arch03_icb32_monitor.svh']
    tracked+=[p for p in firmware.iterdir() if p.is_file() and p.suffix in ('.elf','.bin','.verilog')]
    tracked+=[ROOT/rel for rel in fw['source_sha256']]
    if fw['configuration']['irq_enabled']:tracked.append(A3/'irq_mapping.json')
    tracked+=[A3/'scripts'/n for n in ('icb32_gate.py','icb32_gate_monitor.py','icb32_activity.py',
        'icb32_soc.py','icb32_data.py','icb32_codec.py','build_icb32_firmware.py','dma16_batch.py',
        'activity_fast.py','activity_scan.cpp','gate_soc.py','asic_boot.py','stdcell_verify.py','timing_contract.py')]
    before={str(p.resolve()):sha(p) for p in tracked};save(run/'source_inputs.json',before)
    cmd=[cfg['tools']['vcs'],'-full64','-sverilog','-timescale=1ns/1fs','+define+ARM_UD_MODEL',
         '+define+functional','-top','tb_top','-o',str(run/'simv'),'+incdir+'+str(run)]+files
    save(run/'compile_command.json',[str(p) for p in cmd]);log=call(cmd,run,'compile.log')
    data.require(not re.search(r'Warning-\[(?:IPDW|PCWM-W|INAV|SIOB)\]|(?m:^\s*Error-)',log),
                 'ICB32 gate declaration/width/tool error')
    data.require((run/'simv').is_file(),'Missing compiled gate simulator')
    before.update({str(p.resolve()):sha(p) for p in (run/'simv',run/'compile_command.json',run/'compile.log')})
    save(run/'source_inputs.json',before)
    runtime=dict(executable=str((run/'simv').resolve()),row_lanes=fw['configuration']['row_lanes'])
    results=[]
    for name in cases:
        row=run_case(runtime,fw,base,ROOT/'validated_data'/name,run,name,call,name in activity_cases)
        if name in activity_cases:
            row['activity']=audit_activity(run/(name+'.vcd'),row['task_window'],run,call)
            row['activity_audited']=True
        for path,digest in before.items():data.require(sha(Path(path))==digest,'Gate input changed: '+path)
        for directory in (run/(name+'_data'),run/(name+'_boot')):
            for path in directory.iterdir():
                if path.is_file():before[str(path.resolve())]=sha(path)
        for path in (run/(name+'_firmware.verilog'),run/(name+'_command.json'),run/(name+'.log'),run/(name+'.csv')):
            before[str(path.resolve())]=sha(path)
        save(run/'source_inputs.json',before)
        results.append(row);save(run/'case_progress.json',results)
        print('ICB32_GATE_CPU_CASE_PASS',name,'cycles',row['task_window']['cycles'],flush=True)
    verify_synthesis(synthesis,expected_sha,cfg);verify_firmware(firmware)
    return dict(status='passed',scope=SCOPE,cases=results,cpu_executed=True,gate_simulation_verified=True,
        firmware_sha256=sha(firmware/'manifest.json'),source_inputs_sha256=sha(run/'source_inputs.json'),
        synthesis_run=str(synthesis),synthesis_summary_sha256=expected_sha,
        mapped_binding_receipt_sha256=sha(run/'mapped_binding_receipt.json'),
        source_setup_hold_nonnegative=summary['setup_hold_nonnegative'],
        global_FPGA_defined=False,input_task_bytes_in_boot=0,sdf_annotated=False,
        timing_verified=False,system_power_verified=False,physical_signoff=False,
        artifacts={p.name:sha(p) for p in run.iterdir() if p.is_file() and p.suffix!='.vcd'})
