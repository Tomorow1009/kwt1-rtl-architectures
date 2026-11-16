"""Strict N1 mapped E203 functional result/saturation checks; no SDF/timing acceptance.

A read-only DC probe binds actual module ports. Missing/optimized hierarchy is
an error, never permission to guess internal aliases or preload task data.
"""
import json
import re
import time
from pathlib import Path
from server_run import ROOT, A2, A3, sha, save, vendor
from gate_soc import mapped_loader, input_values as baseline_inputs
from asic_boot import prepare as physical_boot
from stdcell_verify import extract_model
from p80_window import read_window
from c32_soc import verify_firmware, MARKERS
from build_c32_firmware import metadata_image
import systolic_b_data as runtime_parser
from t80_synth import SYSMEM, area_inventory, verify_top_sysmem, require_loop_free_timing, constraints
from c32_gate_monitor import generate, PROOF
from icb32_activity import audit_activity
from soc_power import power_databases, tcl_path
from soc_synth import require_tool_marker
from timing_contract import TB_HALF_PERIOD_NS, validate_period
import n1_data as data
import c80_data as wire_data
from c32_paths import allowed_run

# run_case only handles physical boot, dynamic source and result checking. It
# does not confer the ASIC-RTL build scope on this separately compiled netlist.

SCOPE = 'c32_whole_soc_mapped_functional_without_SDF'
PROBE_MARKER = 'C32_MAPPED_PORT_PROBE_READY netlist_modified=false'
REFERENCES = dict(accel='arch03_c32_accel', core='arch03_c32_linear16x2', decoder='arch03_c80_decoder', shared='arch03_shared_sram_turnover',
                  arb='arch03_icb_arb2_queued', router='arch03_icb_memory_router_turnover')
INSTANCE_SUFFIXES = dict(accel='u_arch03_accel', core='u_arch03_accel/core', decoder='u_arch03_accel/decoder', shared='u_arch03_shared',
                         arb='u_arch03_arb', router='u_arch03_router')
SIMPLE_PATH = r'[A-Za-z_$][A-Za-z0-9_$]*(?:/[A-Za-z_$][A-Za-z0-9_$]*)*'


def check_capture(capture, task):
    """Four actual mapped fields; never weaken n1_data's five-field RTL check."""
    task = Path(task)
    expected = data.hex_values(task/'result.hex', 25344, 16, True)
    saturated = data.hex_values(task/'saturated.hex', 25344, 1)
    seen = set()
    with Path(capture).open('r', encoding='ascii') as stream:
        for line in stream:
            fields = line.strip().split(',')
            data.require(len(fields)==4, 'N1 mapped capture requires row,col,result,saturated')
            row, col, value, sat = map(int, fields)
            data.require(0<=row<99 and 0<=col<256, 'Mapped capture coordinate out of range')
            index = row*256+col
            data.require(index not in seen, 'Duplicate mapped capture coordinate')
            data.require(value==expected[index] and sat==saturated[index],
                         'Mapped result/saturation mismatch row=%d col=%d' % (row,col))
            seen.add(index)
    data.require(len(seen)==25344, 'Incomplete mapped output coordinates')
    return dict(outputs=25344, mismatches=0, saturated=sum(saturated),
                total_checked=False, internal_total_observable=False,
                capture_fields=['row','col','result','saturated'], capture_sha256=sha(capture))


def parse_result(text, saturated, required_markers=()):
    data.require(text.count('P80_BUS_ROUTE_PASS ')==1, 'Missing mapped original bus route proof')
    data.require(text.count(PROOF)==1, 'Missing/duplicate N1 mapped result/saturation proof')
    data.require('ARCH03_N1_TOTAL_PROOF' not in text, 'Mapped result-only run claims internal total proof')
    return runtime_parser.parse_result(text, saturated, list(required_markers)+[PROOF])


def run_case(contract, fw, base, source, run, name, call, activity=False, force_raw=False):
    """Run N1 firmware on the mapped design with its explicit capture scope."""
    data.require(contract['layout_id']==0x00100006 and contract['row_lanes']==2,
                 'Mapped N1 runtime numeric/layout configuration changed')
    task=run/(name+'_data'); info=wire_data.prepare_case(source,task,force_raw,contract['layout_id'])
    wire_data.verify_prepared(source,task)
    image=metadata_image(base,info['shift'],info['encoded_bytes'],contract['row_lanes'],info['layout'])
    boot_image=run/(name+'_firmware.verilog')
    boot_image.write_bytes(''.join('%02x\n'%value for value in image).encode('ascii'))
    boot=run/(name+'_boot'); boot_receipt=physical_boot(boot_image,boot)
    boot_receipt.update(scope='initial_ITCM_firmware_only',encoded_bytes=info['encoded_bytes'],
                        shift=info['shift'],row_lanes=2,input_bytes_preloaded=0)
    save(boot/'manifest.json',boot_receipt)
    capture=run/(name+'.csv')
    command=[contract['executable'],'+BOOT_DIR='+str(boot.resolve()),
        '+LOAD32='+str((task/'codec32.hex').resolve()),'+CODEC_BYTES='+str(info['encoded_bytes']),
        '+LAYOUT='+str(info['layout']),'+DATA_DIR='+str(task.resolve()),
        '+CAPTURE='+str(capture.resolve()),'+SHIFT='+str(info['shift'])]
    data.require(not activity, 'N1 mapped activity requires the qualified SAIF replay entry')
    save(run/(name+'_command.json'),command)
    started=time.monotonic(); text=call(command,run,name+'.log'); elapsed=time.monotonic()-started
    captured=check_capture(capture,task)
    markers=MARKERS+['ARCH03_ICB32_SOURCE_READY words=%d scope=PC_file_only no_ITCM_task_data=true' %
                     (info['encoded_bytes']//4)]
    result=parse_result(text,captured['saturated'],markers)
    window=read_window(text,result,info['encoded_bytes'])
    cpu=re.findall(r'^ARCH03_ICB32_CPU_CYCLES (\d+)$',text,re.M)
    irq=re.findall(r'^ARCH03_ICB32_IRQ_PROOF enabled=(\d+) external=(\d+) timer=(\d+) wfi=(\d+) events=(\d+) unhandled=(\d+)$',text,re.M)
    data.require(len(cpu)==len(irq)==1,'Missing mapped CPU/IRQ completion proof')
    enabled,external,timer,wfi,events,unhandled=map(int,irq[0])
    data.require(enabled==int(fw['configuration']['irq_enabled']),'Mapped IRQ mode mismatch')
    if enabled:
        data.require(external>0 and timer>0 and wfi>0 and events&1 and unhandled==0,
                     'Incomplete mapped IRQ/WFI proof')
    wire_data.verify_prepared(source,task)
    for filename,digest in boot_receipt['files'].items():
        data.require(sha(boot/filename)==digest,'Physical boot changed')
    return dict(case=name,outputs=25344,total_outputs=None,total_checked=False,
        internal_total_observable=False,numeric_format='0x000e0c20',
        result=result,task_window=window,capture=captured,passive_metrics=None,
        cpu_cycles=int(cpu[0]),host_elapsed_seconds=elapsed,codec_sha256=sha(task/'codec.json'),
        layout_sha256=sha(task/'layout_manifest.json'),boot_manifest_sha256=sha(boot/'manifest.json'),
        log_sha256=sha(run/(name+'.log')),
        irq_proof=dict(enabled=bool(enabled),external=external,timer=timer,wfi=wfi,
                       events=events,unhandled=unhandled),activity_requested=False,activity_audited=False)


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
    result['arb']['accepted_queue_count']=('out',4)
    result['router'] = dict(base, **slave)
    for prefix in ('mem_', 'src_'):
        result['router'].update({prefix+n: spec for n, spec in master.items()})
    for role in ('arb', 'router'):
        result[role]['transaction_pending'] = ('out', 1)
    result['core'] = dict(base, start_valid=('in', 1), start_ready=('out', 1), cancel=('in', 1),
                          prefetch_enable=('in', 1), layout_v3=('in', 1), shift=('in', 5), load_valid=('in', 1),
                          load_ready=('out', 1), load_data=('in', 64), load_count=('in', 3), out_valid=('out', 1),
                          out_ready=('in', 1), out_row=('out', 7), out_column=('out', 8),
                          result=('out', 32), saturated=('out', 2), busy=('out', 1), done=('out', 1), error=('out', 1))
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
            ('core_interface', 'core', set(pins['core']), '')):
        names = prior.get(group, set()); prefix = cells[role]+'/'
        # DC full_name wildcards also match pins below descendant cells.
        # Verify the exact direct module boundary, retaining all raw evidence.
        if any(not n.startswith(prefix+pattern) for n in names):
            raise ValueError('Frozen synthesis probe contains a foreign hierarchy: '+group)
        direct = {n for n in names if '/' not in n[len(prefix):]}
        if direct != expected:
            raise ValueError('Mapped DC probe disagrees with frozen synthesis DMA/core interface')
        frozen_counts[group] = dict(total=len(names), direct=len(direct), descendants=len(names-direct))
    # The frozen status inventory contains every descendant pin under accel.
    # Independently match the selected N1 decoder's whole direct boundary.
    all_status=prior.get('status_interface',set())
    prefix=cells['decoder']+'/'
    direct={n for n in all_status if n.startswith(prefix) and '/' not in n[len(prefix):]}
    if direct!=set(pins['decoder']):
        raise ValueError('Frozen synthesis status inventory does not prove every N1 decoder pin')
    frozen_counts['decoder_from_status_interface']=dict(direct=len(direct),inventory_total=len(all_status))
    convert = lambda path: 'u_e203_soc_top.'+path.replace('/', '.')
    return dict(bindings={r: convert(path) for r, path in cells.items()},
                guards={r: convert(path) for r, path in guards.items()},
                cells=cells, port_interfaces=interfaces(), pin_counts={r: len(p) for r, p in pins.items()},
                frozen_synthesis_interfaces_crosschecked=True, frozen_probe_counts=frozen_counts,
                alias_binding_used=False)


def verify_synthesis(synthesis,expected_sha,cfg):
    from c32_validation import verify_synthesis as verify_partitioned
    return verify_partitioned(synthesis,expected_sha,cfg)


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
    receipt_names=['source_inputs.json']
    summary_path=synthesis/'summary.json'
    summary=json.loads(summary_path.read_text()) if summary_path.exists() else {}
    if summary.get('scope')=='c32_partitioned_whole_soc_task_mode':
        # The fresh C32 link and final mapping both trace SRAM configuration. The
        # copied current header is frozen in the final synthesis input receipt.
        # Read both pinned receipts, retaining all ancestors and rejecting any
        # conflicting digest; never patch the completed synthesis evidence.
        receipt_names.append('synthesis_inputs.json')
        for name in receipt_names:
            if summary['artifacts'].get(name)!=sha(synthesis/name):
                raise ValueError('Changed frozen C32 SRAM provenance receipt '+name)
        linked=json.loads((synthesis/'synthesis_inputs.json').read_text())
        for name,value in linked.items():
            if name in inputs and inputs[name]!=value:
                raise ValueError('Conflicting C32 SRAM provenance receipts')
            inputs[name]=value
        if summary['artifacts'].get('arch02_sram_config.vh')!=sha(synthesis/'arch02_sram_config.vh'):
            raise ValueError('Changed frozen C32 SRAM configuration')
    matches = [(Path(name), digest) for name, digest in inputs.items()
               if Path(name).name == 'arch02_sram_config.vh']
    if not matches or len({digest for _,digest in matches})!=1:
        raise ValueError('Missing/ambiguous traced synthesis SRAM configuration')
    # A mapped repair retains its ancestors' exact inputs as well as its own
    # newly generated vendor include. Every traced copy must agree; do not
    # arbitrarily select one or ignore a differing historical configuration.
    current=(synthesis/'arch02_sram_config.vh').resolve()
    if current not in {path.resolve() for path,_ in matches}:
        raise ValueError('Current synthesis SRAM configuration is not traced')
    digest=matches[0][1]
    if any(sha(path)!=value for path,value in matches) or sha(run/'arch02_sram_config.vh')!=digest:
        raise ValueError('Gate SRAM model configuration differs from synthesized hardware')
    save(run/'memory_configuration_receipt.json',dict(sha256=digest,
        synthesis_receipts={name:sha(synthesis/name) for name in receipt_names},
        identical_traced_inputs=[str(path.resolve()) for path,_ in matches],
        gate_configuration=str((run/'arch02_sram_config.vh').resolve())))


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
`include "arch03_c32_gate_monitor.svh"
arch03_clock_mode_guard a3_gate_mode(.clk(a3_mon_clk),.rst_n(a3_mon_rst_n),
    .active(a3_window_active),.finished(a3_window_finished),
@GUARDS@);
endmodule
'''.replace('@HALF@', TB_HALF_PERIOD_NS).replace('@WIRES@', '\n'.join(declarations)).replace(
        '@PORTS@', ',\n'.join('    .%s(%s)' % item for item in sorted(values.items()))).replace(
        '@GUARDS@', ',\n'.join('    .%s(%s)' % item for item in sorted(probe['guards'].items())))


def verify(cfg,run,synthesis,expected_sha,cases,call,activity_cases=(),firmware=None):
    run,synthesis=allowed_run(run,cfg,'N1 gate output'),allowed_run(synthesis,cfg,'N1 synthesis')
    data.require(not activity_cases,'N1 gate activity requires the separately validated SAIF path')
    data.require(cases and len(cases)==len(set(cases)) and set(cases)<=set(data.CASES14) and
                 set(activity_cases)<=set(cases),'Invalid gate case selection')
    data.require(not any((run/n).exists() for n in ('simv','source_inputs.json','mapped_probe.tcl','summary.json')),
                 'ICB32 gate requires a fresh directory')
    summary,area=verify_synthesis(synthesis,expected_sha,cfg)
    firmware=Path(firmware or ROOT/'firmware').resolve();firmware.relative_to(ROOT.resolve())
    fw,base=verify_firmware(firmware)
    data.require(fw['configuration']['default_layout']==0x00100006,'N1 gate binds numeric layout6 only')
    data.require(summary['link_report']['row_lanes']==fw['configuration']['row_lanes'],
                 'Gate firmware row lanes differ from synthesized hardware')
    data.require(summary['transaction_metadata_depth']==fw['configuration']['transaction_metadata_depth'],'Gate firmware queue depth differs from mapped hardware')
    probe=probe_mapped(cfg,run,synthesis,call)
    loader=run/'arch03_asic_boot.svh';loader.write_text(mapped_loader(area))
    monitor=run/'arch03_c32_gate_monitor.svh'
    monitor.write_text(generate((A3/'tb/arch03_c32_monitor.svh').read_text(),probe['bindings'],fw['configuration']['transaction_metadata_depth']))
    tb=run/'tb_top.sv';tb.write_text(testbench((synthesis/'mapped.v').read_text(),probe))
    model=extract_model(cfg,run)
    modules=[A3/'tb'/n for n in ('arch03_task_window_p80.sv','arch03_icb32_source.sv',
             'arch03_clock_mode_guard.sv','arch03_p80_gate_proof.sv','arch03_p80_route_observer.sv')]
    files=[synthesis/'mapped.v']+modules+[tb,model]+vendor(cfg,run)
    verify_gate_memory_config(synthesis,run)
    tracked=files+[loader,monitor,firmware/'manifest.json',synthesis/'summary.json',
        run/'arch02_sram_config.vh',run/'memory_configuration_receipt.json',Path(__file__),run/'mapped_binding_receipt.json',run/'mapped_port_probe.tsv',
        run/'mapped_probe.tcl',run/'mapped_probe.log',run/'probe_command.json',A3/'tb/arch03_c32_monitor.svh', A3/'tb/arch03_p80_route_audit.svh', A3/'scripts/p80_window.py']
    tracked+=[p for p in firmware.iterdir() if p.is_file() and p.suffix in ('.elf','.bin','.verilog')]
    tracked+=[ROOT/rel for rel in fw['source_sha256']]
    if fw['configuration']['irq_enabled']:tracked.append(A3/'irq_mapping.json')
    tracked+=[A3/'scripts'/n for n in ('c32_gate.py','c32_paths.py','c32_gate_monitor.py','p80_mapped_aliases.py','icb32_gate_monitor.py','icb32_activity.py',
        'c32_validation.py','c32_partition_synth.py','c32_link.py','t80_synth.py','s0_partition_synth.py','partition_synth_contract.py','c32_soc.py','c80_data.py','c80_codec.py','c80_codec_candidate.py','n1_data.py','n1_codec.py','systolic_b_data.py','systolic_b_codec.py','icb32_codec.py','build_c32_firmware.py','dma16_batch.py',
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
    runtime=dict(executable=str((run/'simv').resolve()),row_lanes=2,layout_id=0x00100006,passive_metrics=False,transaction_metadata_depth=fw['configuration']['transaction_metadata_depth'])
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
        numeric_format='0x000e0c20',layout_id=0x00100006,shift=10,transaction_metadata_depth=fw['configuration']['transaction_metadata_depth'],
        internal_total_observable=False,total_checked=False,capture_fields=['row','col','result','saturated'],
        firmware_sha256=sha(firmware/'manifest.json'),source_inputs_sha256=sha(run/'source_inputs.json'),
        synthesis_run=str(synthesis),synthesis_summary_sha256=expected_sha,
        mapped_binding_receipt_sha256=sha(run/'mapped_binding_receipt.json'),
        source_setup_hold_nonnegative=summary['setup_hold_nonnegative'],
        global_FPGA_defined=False,input_task_bytes_in_boot=0,sdf_annotated=False,
        timing_verified=False,system_power_verified=False,physical_signoff=False,
        artifacts={p.name:sha(p) for p in run.iterdir() if p.is_file() and p.suffix!='.vcd'})
