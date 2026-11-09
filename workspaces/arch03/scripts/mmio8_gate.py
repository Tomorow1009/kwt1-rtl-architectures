"""Mapped original MMIO8 reference with the complete SysMem loading window.

Independent fresh MMIO8 synthesis is mandatory. This is not an eight-lane DMA
design. Bind observed module pins, never implementation aliases retained by
dont_touch. Python 3.6; zero-delay functional evidence is not STA acceptance.
"""
import json
import re
import time
from pathlib import Path
import dma16_gate as shared
import dma16_activity as fabric_activity
import mmio8_soc as soc
import mmio8_synth as synth
import mmio8_source_layout as layout
from server_run import ROOT, A3, sha, save, vendor
from asic_boot import prepare
from stdcell_verify import extract_model
from soc_power import power_databases
from soc_synth import require_tool_marker

SCOPE = 'mmio8_source_whole_soc_mapped_functional_without_SDF'
PROBE_MARKER = 'MMIO8_SOURCE_MAPPED_PORT_PROBE_READY netlist_modified=false DMA_present=false'
REFERENCES = dict(accel='arch03_icb_accel', shared='arch03_shared_sram',
                  arb='arch03_icb_arb2', router='arch03_icb_memory_router')
SUFFIXES = {name: shared.INSTANCE_SUFFIXES[name] for name in REFERENCES}


def interfaces():
    result = {name: shared.interfaces()[name] for name in ('shared', 'arb', 'router')}
    result['accel'] = dict(result['shared'])
    return result


def probe_script(synthesis):
    text = shared.probe_script(synthesis)
    old = ' '.join('%s %s %s' % (role, reference, shared.INSTANCE_SUFFIXES[role])
                   for role, reference in sorted(shared.REFERENCES.items()))
    new = ' '.join('%s %s %s' % (role, reference, SUFFIXES[role])
                   for role, reference in sorted(REFERENCES.items()))
    text = synth.shared.replace_once(text, old, new)
    return synth.shared.replace_once(text, shared.PROBE_MARKER, PROBE_MARKER)


def parse_probe(text):
    cells, refs, guards = {}, {}, {}
    pins = {role: {} for role in REFERENCES}
    for line in text.splitlines():
        fields = line.split('\t')
        if len(fields) != 4:
            raise ValueError('Malformed MMIO8 mapped probe')
        kind, role, path, value = fields
        if kind == 'cell':
            if (role not in REFERENCES or role in cells or
                    not re.fullmatch(shared.SIMPLE_PATH, path) or
                    not path.endswith('/'+SUFFIXES[role]) or
                    not re.fullmatch(re.escape(REFERENCES[role])+r'(?:_\w+)?', value)):
                raise ValueError('Wrong/duplicate MMIO8 actual module')
            cells[role], refs[role] = path, value
        elif kind == 'pin':
            if role not in pins or path in pins[role]:
                raise ValueError('Unknown/duplicate MMIO8 mapped pin')
            pins[role][path] = {'input': 'in', 'output': 'out'}.get(value, value)
        elif kind == 'guard':
            if role in guards or not re.fullmatch(shared.SIMPLE_PATH, path) or value not in ('in', 'out', 'input', 'output'):
                raise ValueError('Invalid MMIO8 clock/boot guard')
            guards[role] = path
        else:
            raise ValueError('Unknown MMIO8 mapped probe record')
    if set(cells) != set(REFERENCES) or len(set(cells.values())) != 4:
        raise ValueError('Incomplete/aliased MMIO8 fabric')
    if len({path.rsplit('/', 1)[0] for path in cells.values()}) != 1:
        raise ValueError('MMIO8 modules belong to different subsystems')
    for role, spec in interfaces().items():
        expected = {cells[role]+'/'+name: direction for name, direction in shared.port_bits(spec).items()}
        if pins[role] != expected:
            raise ValueError('MMIO8 module port direction/width mismatch: '+role)
    if set(guards) != {'test_mode', 'pllbypass', 'plloutdivby1', 'bootrom_selected'}:
        raise ValueError('Incomplete MMIO8 clock/boot guards')
    roots = {guards[k].rsplit('/', 1)[0] for k in ('test_mode', 'pllbypass', 'plloutdivby1')}
    if len(roots) != 1 or not next(iter(roots)).endswith('/u_e203_subsys_hclkgen'):
        raise ValueError('Wrong MMIO8 clock guard hierarchy')
    if not guards['bootrom_selected'].endswith('/u_sirv_aon_wrapper/bootrom_deglitch/io_q'):
        raise ValueError('Wrong MMIO8 boot guard hierarchy')
    convert = lambda p: 'u_e203_soc_top.'+p.replace('/', '.')
    return dict(bindings={k: convert(v) for k, v in cells.items()},
                guards={k: convert(v) for k, v in guards.items()}, cells=cells,
                references=refs, pin_counts={k: len(v) for k, v in pins.items()},
                alias_binding_used=False, DMA_present=False)


def generate_monitor(text, bindings):
    if set(bindings) != set(REFERENCES) or len(set(bindings.values())) != 4 or any(
            not re.fullmatch(r'[A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)*', p) for p in bindings.values()):
        raise ValueError('Incomplete/invalid MMIO8 monitor bindings')
    text = synth.shared.replace_once(text,
        '`define M8MEM u_e203_soc_top.u_e203_subsys_top.u_e203_subsys_main.u_e203_subsys_mems\n', '')
    text = synth.shared.replace_once(text, '`define M8ACC `M8MEM.u_arch03_accel\n', '')
    for macro in ('M8ACC', 'M8MEM'):
        text = synth.shared.replace_once(text, '`undef '+macro+'\n', '')
    text = text.replace('`M8ACC.', bindings['accel']+'.')
    for name in synth.shared.SYSMEM:
        text = text.replace('`M8MEM.a3_cpu_'+name, bindings['arb']+'.cpu_'+name)
    for old, new in (('a3_arb_pending', bindings['arb']+'.transaction_pending'),
                     ('a3_router_pending', bindings['router']+'.transaction_pending'),
                     ('clk', bindings['arb']+'.clk'), ('rst_n', bindings['arb']+'.rst_n')):
        text = text.replace('`M8MEM.'+old, new)
    if '`M8' in text or re.search(r'\ba3_(?:cpu_|arb_pending|router_pending)', text):
        raise ValueError('Unbound MMIO8 implementation alias')
    return text


def verify_synthesis(synthesis, expected_sha, cfg):
    synthesis = Path(synthesis).resolve(); synthesis.relative_to(Path(cfg['server_root']).resolve())
    if not re.fullmatch('[a-f0-9]{64}', expected_sha) or sha(synthesis/'summary.json') != expected_sha:
        raise ValueError('MMIO8 synthesis summary digest mismatch')
    summary = json.loads((synthesis/'summary.json').read_text())
    state = json.loads((synthesis.parent/'state.json').read_text()).get('stages', {}).get('mmio8_synth', {})
    if (state.get('status') != 'passed' or state.get('summary_sha256') != expected_sha or
            summary.get('scope') != synth.SCOPE or summary.get('DMA_present') is not False or
            summary.get('synthesis_completed') is not True):
        raise ValueError('Fresh original-MMIO8 source synthesis is required')
    for name in ('mapped.v', 'mapped.ddc', 'mapped.sdc', 'leaf_area.tsv', 'area_inventory.json',
                 'source_inputs.json', 'synthesis_inputs.json', 'mapped_sysmem_ports.tsv',
                 'area_basis.json', 'check_timing.rpt'):
        if sha(synthesis/name) != summary['artifacts'][name]:
            raise ValueError('Changed MMIO8 synthesis artifact '+name)
    synth.shared.require_loop_free_timing((synthesis/'check_timing.rpt').read_text())
    traced = {}
    for name in ('source_inputs.json', 'synthesis_inputs.json'):
        for path, digest in json.loads((synthesis/name).read_text()).items():
            if sha(Path(path)) != digest or (path in traced and traced[path] != digest):
                raise ValueError('Changed/conflicting MMIO8 synthesis input '+path)
            traced[path] = digest
    source_bundle = synthesis.parents[2]
    original = json.loads((source_bundle/'manifest.json').read_text())['files']
    current = json.loads((ROOT/'manifest.json').read_text())['files']
    hardware = {}
    for path, digest in traced.items():
        try:
            relative = Path(path).resolve().relative_to(source_bundle).as_posix()
        except ValueError:
            continue
        if (relative.startswith(('workspaces/arch02/rtl/', 'workspaces/arch02/arch02/rtl/', 'workspaces/arch03/rtl/'))
                and Path(relative).suffix in ('.v', '.sv', '.vh', '.svh')):
            hardware[relative] = digest
    if not hardware:
        raise ValueError('Missing traced MMIO8 production RTL')
    preparation = ['workspaces/arch03/scripts/'+n for n in ('install_platform.py', 'install_dma16.py',
        'install_mmio8_source.py', 'technology_binding.py', 'memory_technology.py', 'timing_contract.py',
        'mmio8_synth.py', 'dma16_synth.py', 'soc_synth.py')]
    preparation += ['workspaces/arch03/'+n for n in ('technology_bindings.json', 'memory_technology.json')]
    for relative in preparation+list(hardware):
        digest = original.get(relative)
        if (not digest or (relative in hardware and hardware[relative] != digest) or current.get(relative) != digest or
                sha(source_bundle/relative) != digest or sha(ROOT/relative) != digest):
            raise ValueError('Changed MMIO8 hardware/preparation '+relative)
    synth.shared.validate_period(summary['metrics']['period_ns'])
    if int(summary['metrics']['RAMSP128X16']) != 8 or int(summary['metrics']['RAMSP4096X16']) != 130:
        raise ValueError('Wrong MMIO8 SRAM inventory')
    area = synth.area_inventory((synthesis/'leaf_area.tsv').read_text(), summary['metrics']['area'])
    synth.shared.verify_top_sysmem((synthesis/'mapped.v').read_text())
    synth.shared.verify_ports((synthesis/'mapped_sysmem_ports.tsv').read_text())
    power_databases(synthesis)
    return summary, area


def probe_mapped(cfg, run, synthesis, call):
    tracked = [synthesis/n for n in ('mapped.ddc', 'mapped.v')]+power_databases(synthesis)
    tcl = run/'mapped_probe.tcl'; tcl.write_text(probe_script(synthesis)); tracked.append(tcl)
    before = {str(p): sha(p) for p in tracked}
    command = [cfg['tools']['dc_shell'], '-f', tcl]
    save(run/'probe_command.json', [str(p) for p in command])
    log = call(command, run, 'mapped_probe.log'); require_tool_marker(log, PROBE_MARKER)
    result = parse_probe((run/'mapped_port_probe.tsv').read_text())
    soc.check_frozen(before)
    result.update(status='actual_mapped_module_ports_verified', source_inputs=before,
                  command_sha256=sha(run/'probe_command.json'), log_sha256=sha(run/'mapped_probe.log'),
                  port_probe_sha256=sha(run/'mapped_port_probe.tsv'), netlist_modified=False)
    save(run/'mapped_binding_receipt.json', result)
    return result


def testbench(netlist, probe):
    text = shared.testbench(netlist, probe)
    text = synth.shared.replace_once(text, 'arch03_dma16_gate_monitor.svh', 'arch03_mmio8_gate_monitor.svh')
    return synth.shared.replace_once(text, '`include "arch03_dma16_metrics.svh"\n', '')


def audit_activity(path, window, run, call):
    # Original-MMIO8 and DMA16 share these exact external SysMem/fabric ports.
    # Keep the independent native full-file scanner and bit-completeness proof.
    result = fabric_activity.audit_activity(path, window, run, call)
    header = result.pop('dma16_header')
    header['status'] = 'mmio8_source_declarations_verified'
    result['mmio8_source_header'] = header
    result['auditor']['kind'] = 'complete_native_stream_scan_and_SHA256_plus_mmio8_source_header'
    result['auditor']['mmio8_adapter_sha256'] = sha(Path(__file__))
    return result


def verify(cfg, run, synthesis, expected_sha, cases, call, activity_cases=(), firmware=None):
    run, synthesis = Path(run), Path(synthesis).resolve()
    if (not cases or len(cases) != len(set(cases)) or not set(cases) <= set(soc.common.CASES14) or
            not set(activity_cases) <= set(cases)):
        raise ValueError('Invalid MMIO8 gate case selection')
    if any((run/n).exists() for n in ('simv', 'source_inputs.json', 'mapped_probe.tcl', 'summary.json')):
        raise ValueError('MMIO8 gate requires a fresh run')
    summary, area = verify_synthesis(synthesis, expected_sha, cfg)
    firmware = Path(firmware or ROOT/'firmware_mmio8').resolve(); firmware.relative_to(ROOT.resolve())
    fw, images = soc.verify_firmware(firmware)
    probe = probe_mapped(cfg, run, synthesis, call)
    loader = run/'arch03_asic_boot.svh'; loader.write_text(shared.mapped_loader(area))
    original_monitor = A3/'tb/arch03_mmio8_source_monitor.svh'
    monitor = run/'arch03_mmio8_gate_monitor.svh'
    monitor.write_text(generate_monitor(original_monitor.read_text(), probe['bindings']))
    tb = run/'tb_top.sv'; tb.write_text(testbench((synthesis/'mapped.v').read_text(), probe))
    files = [synthesis/'mapped.v', A3/'tb/arch03_dma16_source.sv', A3/'tb/arch03_clock_mode_guard.sv',
             tb, extract_model(cfg, run)]+vendor(cfg, run)
    shared.verify_gate_memory_config(synthesis, run)
    boots, tasks = {}, {}
    for shift, image in sorted(images.items()):
        boot = run/('boot_shift_%02d' % shift); receipt = prepare(image, boot)
        receipt.update(scope='initial_ITCM_firmware_only', runtime_task_loading='CPU_original_SysMem_ICB')
        save(boot/'manifest.json', receipt); boots[shift] = boot
    for name in cases:
        source, task = ROOT/'validated_data'/name, run/(name+'_data')
        info = layout.prepare_case(source, task); layout.verify_prepared(source, task)
        if info['shift'] not in boots:
            raise ValueError('Missing original MMIO8 firmware shift')
        tasks[name] = source, task, info
    tracked = files+[loader, monitor, original_monitor, firmware/'manifest.json', synthesis/'summary.json',
        run/'arch02_sram_config.vh']+[run/n for n in ('mapped_binding_receipt.json', 'mapped_port_probe.tsv',
        'mapped_probe.tcl', 'mapped_probe.log', 'probe_command.json')]
    tracked += [p for p in firmware.iterdir() if p.is_file() and p.suffix in ('.elf', '.bin', '.verilog')]
    tracked += [ROOT/rel for rel in fw['source_sha256']]
    tracked += [p for boot in boots.values() for p in boot.iterdir() if p.is_file()]
    tracked += [p for _, task, _ in tasks.values() for p in task.iterdir() if p.is_file()]
    tracked += [A3/'scripts'/n for n in ('mmio8_gate.py', 'mmio8_soc.py', 'mmio8_source_layout.py',
        'mmio8_synth.py', 'dma16_gate.py', 'dma16_synth.py', 'dma16_activity.py', 'activity.py',
        'activity_fast.py', 'activity_scan.cpp', 'dma16_batch.py', 'gate_soc.py', 'asic_boot.py',
        'stdcell_verify.py', 'timing_contract.py')]
    before = {str(p.resolve()): sha(p) for p in tracked}; save(run/'source_inputs.json', before)
    cmd = [cfg['tools']['vcs'], '-full64', '-sverilog', '-timescale=1ns/1fs', '+define+ARM_UD_MODEL',
           '+define+functional', '-top', 'tb_top', '-o', str(run/'simv'), '+incdir+'+str(run)]+files
    save(run/'compile_command.json', [str(p) for p in cmd]); compiled = call(cmd, run, 'compile.log')
    if re.search(r'Warning-\[(?:IPDW|PCWM-W|INAV|SIOB)\]|(?m:^\s*Error-)', compiled) or not (run/'simv').is_file():
        raise ValueError('MMIO8 mapped compilation failed or interface warning requires review')
    before.update({str(p.resolve()): sha(p) for p in [run/n for n in ('simv', 'compile_command.json', 'compile.log')]})
    save(run/'source_inputs.json', before); results = []
    for name in cases:
        soc.check_frozen(before)
        source, task, info = tasks[name]; capture = run/(name+'.csv')
        cmd = [run/'simv', '+BOOT_DIR='+str(boots[info['shift']]), '+LOAD32='+str(task/'load32.hex'),
               '+DATA_DIR='+str(task), '+CAPTURE='+str(capture), '+SHIFT='+str(info['shift'])]
        if name in activity_cases:
            cmd.append('+ACTIVITY='+str(run/(name+'.vcd')))
        save(run/(name+'_command.json'), [str(p) for p in cmd])
        started = time.monotonic(); text = call(cmd, run, name+'.log'); elapsed = time.monotonic()-started
        captured = soc.common.check_capture(capture, task); window = soc.read_window(text, captured['saturated'])
        row = dict(case=name, outputs=25344, capture=captured, task_window=window,
                   host_elapsed_seconds=elapsed, layout_sha256=sha(task/'layout_manifest.json'),
                   boot_manifest_sha256=sha(boots[info['shift']]/'manifest.json'))
        if name in activity_cases:
            row['activity'] = audit_activity(run/(name+'.vcd'), window, run, call)
        layout.verify_prepared(source, task); soc.verify_firmware(firmware); soc.check_frozen(before)
        results.append(row); save(run/'case_progress.json', results)
        print('MMIO8_SOURCE_GATE_CPU_CASE_PASS', name, flush=True)
    verify_synthesis(synthesis, expected_sha, cfg)
    return dict(status='passed', scope=SCOPE, cases=results, cpu_executed=True, gate_simulation_verified=True,
        reference='original_repaired_MMIO8_same_SysMem_source', DMA_present=False,
        firmware_sha256=sha(firmware/'manifest.json'), source_inputs_sha256=sha(run/'source_inputs.json'),
        synthesis_run=str(synthesis), synthesis_summary_sha256=expected_sha,
        mapped_binding_receipt_sha256=sha(run/'mapped_binding_receipt.json'),
        source_setup_hold_nonnegative=summary['setup_hold_nonnegative'], global_FPGA_defined=False,
        input_task_bytes_in_boot=0, timing_verified=False, system_power_verified=False, physical_signoff=False,
        artifacts={p.name: sha(p) for p in run.iterdir() if p.is_file() and p.suffix != '.vcd'})
