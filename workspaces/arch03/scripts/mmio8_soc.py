"""Real ASIC/E203 execution of the original MMIO8 driver with timed ICB loading.

No eight-lane DMA, task-input ITCM preload, or expected-answer injection.
The caller owns the common server lock. Python 3.6 standard library only.
"""
import re
import time
from decimal import Decimal, InvalidOperation
from pathlib import Path
from server_run import ROOT, A2, A3, sha, save, vendor
from install_platform import platform_sources
from install_mmio8_source import install
from asic_boot import prepare, loader_include, image_bytes
from build_dma16_firmware import elf_image, metadata_image
from stdcell_verify import extract_model
from timing_contract import TB_PERIOD_NS
import dma16_batch as common
import mmio8_source_layout as layout

MARKERS = [
    'ARCH03_ASIC_BOOT_READY bytes=262144 macros=32 scope=initial_ITCM_only',
    'ARCH03_ASIC_MODE_MATCH test_mode=0 pllbypass=1 divider_bypass=1',
    'ARCH03_BOOT_MODE_MATCH bootrom_selected=1 scope=complete_task',
    'ARCH03_DMA16_SOURCE_READY words=11744 scope=PC_file_only no_ITCM_task_data=true']
FIRMWARE_SOURCES = {'workspaces/arch03/sw/'+name for name in
                    ('kwt.h', 'kwt.c', 'main_mmio8_source.c', 'start.S', 'link.ld')}
FIRMWARE_SOURCES.update({'workspaces/arch03/scripts/build_mmio8_source.py',
                         'workspaces/arch03/scripts/build_dma16_firmware.py'})


def source_list():
    return [A2/'rtl/requantize.sv', A2/'rtl/dot64.sv',
            A2/'arch02/rtl/sram_port.sv', A2/'arch02/rtl/sram_macro_adapter.sv',
            A2/'arch02/rtl/arch02_linear.sv'] + [A3/'rtl'/name for name in
                ('arch03_icb_accel.sv', 'arch03_icb_arb2.sv',
                 'arch03_icb_memory_router.sv', 'arch03_shared_sram.sv', 'arch03_tcm_ram.sv')]


def verify_firmware(firmware, source_root=ROOT):
    firmware, source_root = Path(firmware), Path(source_root).resolve()
    manifest = common.read(firmware/'manifest.json')
    common.require(manifest.get('run_mode') == 'single_cpu_mmio8_source_v1' and
                   manifest.get('physical_boot_policy') == 'firmware_only_no_task_inputs', 'Wrong MMIO8 source firmware mode')
    expected = dict(task_source_address='0xb0000000', shared_input_address='0xa0000000',
                    shared_output_address='0xa000c000', peripheral_id='0x4b575403', layout_tag='0x00080001')
    common.require(all(manifest.get(key) == value for key, value in expected.items()), 'MMIO8 firmware address/layout mismatch')
    config = manifest['configuration']
    common.require(config.get('irq_enabled') is False and config.get('original_mmio_driver_unchanged') is True,
                   'Expected original polling MMIO8 driver')
    common.require(set(manifest['source_sha256']) == FIRMWARE_SOURCES, 'Incomplete MMIO8 firmware source identity')
    for rel, digest in manifest['source_sha256'].items():
        path = (source_root/rel).resolve();path.relative_to(source_root)
        common.require(sha(path) == digest, 'MMIO8 firmware source changed: '+rel)
    elf = firmware/'driver.elf'
    common.require(sha(elf) == manifest['elf_sha256'], 'MMIO8 firmware ELF changed')
    base, segments = elf_image(elf.read_bytes())
    common.require(segments == manifest['segments'], 'MMIO8 firmware segment metadata changed')
    shifts = {}
    for name, meta in manifest['images'].items():
        shift = meta['shift']
        common.require(type(shift) is int and 0 <= shift <= 31 and name == 'shift_%02d' % shift and
                       shift not in shifts, 'MMIO8 firmware shift name/duplicate')
        path, binary = firmware/(name+'.verilog'), firmware/(name+'.bin')
        wanted = metadata_image(base, shift)
        common.require(meta['image_bytes'] == 262144 and meta['metadata_offset'] == 0xfff0 and
                       meta['task_input_region_start'] == 0x10000 and meta['firmware_only'] is True and
                       meta['task_input_region_nonzero_bytes'] == 0, 'MMIO8 boot policy metadata changed')
        common.require(sha(path) == meta['sha256'] and image_bytes(path) == wanted and
                       sha(binary) == meta['binary_sha256'] and binary.read_bytes() == wanted and
                       not any(wanted[0x10000:]), 'MMIO8 boot image changed or contains task inputs')
        shifts[shift] = path
    common.require(shifts, 'Missing MMIO8 firmware images')
    return manifest, shifts


def fields_line(text, prefix, expected):
    lines = [line for line in text.splitlines() if line.startswith(prefix+' ')]
    common.require(len(lines) == 1, 'Expected one '+prefix)
    tokens = lines[0][len(prefix)+1:].split()
    common.require(all(re.fullmatch(r'[a-z_]+=[^\s=]+', token) for token in tokens), 'Malformed '+prefix)
    pairs = [token.split('=', 1) for token in tokens]
    fields = dict(pairs)
    common.require(len(fields) == len(pairs) and set(fields) == set(expected), 'Missing/duplicate/unexpected '+prefix+' fields')
    return fields


def natural(fields, key):
    common.require(re.fullmatch(r'\d+', fields[key]), 'Invalid nonnegative integer '+key)
    return int(fields[key])


def read_window(text, saturated):
    common.require(type(saturated) is int and 0 <= saturated <= 25344, 'Invalid expected saturation count')
    common.require(not re.search(r'(?im)^\s*(?:Error-|Fatal:|Error:|FATAL\b|FAIL\b|\S*_FAIL\b)', text), 'MMIO8 simulator error marker')
    for marker in MARKERS:
        common.require(text.splitlines().count(marker) == 1, 'Missing/duplicate ASIC mode marker: '+marker)
    done = fields_line(text, 'ARCH03_MMIO8_SOURCE_PASS', ('outputs', 'cpu_executed', 'cycles', 'cpu_cycles', 'saturated'))
    common.require(done['cpu_executed'] == 'true' and natural(done, 'outputs') == 25344 and
                   natural(done, 'saturated') == saturated, 'MMIO8 completion/capture mismatch')
    fields = fields_line(text, 'MMIO8_SOURCE_WINDOW', ('start_cycle', 'end_cycle', 'cycles', 'start_ns', 'end_ns',
        'start_edge_ns', 'start_phase_ns',
        'source_read_acks', 'input_write_acks', 'input_read_acks', 'output_write_acks', 'command_wait', 'response_wait'))
    start, end, cycles = [natural(fields, key) for key in ('start_cycle', 'end_cycle', 'cycles')]
    cpu_cycles = natural(done, 'cpu_cycles')
    common.require(0 < cycles == end-start == natural(done, 'cycles') and cpu_cycles >= cycles,
                   'MMIO8 measured/CPU cycle mismatch')
    try:
        t0, t1 = Decimal(fields['start_ns']), Decimal(fields['end_ns'])
        edge, phase = Decimal(fields['start_edge_ns']), Decimal(fields['start_phase_ns'])
    except InvalidOperation:
        raise ValueError('Invalid MMIO8 task timestamps')
    period = Decimal(TB_PERIOD_NS); tolerance = Decimal('0.000002')
    common.require(all(t.is_finite() for t in (t0, t1, edge, phase)) and 0 <= edge <= t0 < t1 and
                   0 <= phase < period and abs(t0-edge-phase) <= tolerance and
                   abs(t1-edge-Decimal(cycles)*period) <= tolerance,
                   'MMIO8 time/cycle mismatch')
    counts = {key: natural(fields, key) for key in
              ('source_read_acks', 'input_write_acks', 'input_read_acks', 'output_write_acks')}
    common.require(counts == dict(source_read_acks=11744, input_write_acks=11744,
                                  input_read_acks=23488, output_write_acks=25344), 'MMIO8 actual transaction count mismatch')
    # These are observed successful O4 data-region transactions. In particular,
    # each LHU and SH consumes its own 32-bit bus transaction in this reference.
    useful = dict(source_read=counts['source_read_acks']*4, initial_shared_write=counts['input_write_acks']*4,
                  shared_input_read=counts['input_read_acks']*2, output_write=counts['output_write_acks']*2)
    return dict(start_cycle=start, end_cycle=end, cycles=cycles, start_ns=str(t0), end_ns=str(t1),
        start_edge_ns=str(edge), start_phase_ns=str(phase), elapsed_ns=str(t1-t0),
        counted_duration_ns=str(Decimal(cycles)*period),
        cycle_quantization='end_minus_start_clock_index; ceiling of exact event duration, less than one cycle conservative rounding',
        period_ns=TB_PERIOD_NS, cpu_cycles=cpu_cycles, saturated=saturated, outputs=25344,
        boundary='first_source_valid_to_last_output_write_response_with_drain_proof',
        completion_proof='window published only after CPU data-port and arbiter/router drain; PASS after CPU mailbox',
        successful_data_region_icb_transactions=counts, data_region_transaction_count=sum(counts.values()),
        data_region_bus_word_bits=32, data_region_bus_slot_bytes=sum(counts.values())*4,
        useful_bytes_by_phase=useful, total_useful_data_region_bytes=sum(useful.values()),
        transaction_scope='four task-data phases only; excludes MMIO registers/polls, mailbox and instruction traffic',
        total_system_transactions=None, command_wait_cycles=natural(fields, 'command_wait'),
        response_wait_cycles=natural(fields, 'response_wait'), task_per_second=150000000.0/cycles,
        mmac_per_second=1622016.0*150.0/cycles)


def check_frozen(frozen):
    for path, digest in frozen.items():
        common.require(sha(Path(path)) == digest, 'Frozen MMIO8 input changed: '+path)


def compile_design(cfg, run, platform_source, call, firmware=None):
    run = Path(run).resolve()
    firmware = Path(firmware or ROOT/'firmware_mmio8').resolve();firmware.relative_to(ROOT.resolve())
    fw, images = verify_firmware(firmware)
    platform = run/'platform';platform_manifest = install(platform_source, platform)
    loader = run/'arch03_asic_boot.svh';loader.write_text(loader_include())
    model = extract_model(cfg, run)
    team = source_list()
    monitors = [A3/'tb'/name for name in ('arch03_dma16_source.sv', 'arch03_clock_mode_guard.sv')]
    libs = [model]+vendor(cfg, run)
    files = platform_sources(platform)+team+monitors+[platform/'tb/tb_top.v']+libs
    includes = list(dict.fromkeys([run, A3/'tb', platform/'rtl/e203/core']+[path.parent for path in files]))
    command = [cfg['tools']['vcs'], '-full64', '-sverilog', '-timescale=1ns/1fs', '+define+ARM_UD_MODEL',
               '+define+functional', '-top', 'tb_top', '-o', str(run/'simv')]
    command += ['+incdir+'+str(path) for path in includes]+files
    save(run/'compile_command.json', [str(value) for value in command])
    tracked = files+[loader, A3/'tb/arch03_mmio8_source_monitor.svh', run/'arch02_sram_config.vh', firmware/'manifest.json']
    tracked += [path for path in platform.rglob('*') if path.is_file()]
    tracked += [path for path in firmware.iterdir() if path.is_file() and path.suffix in ('.elf', '.bin', '.verilog')]
    tracked += [ROOT/rel for rel in fw['source_sha256']]
    tracked += [path for base in (A2, A3) for path in base.rglob('*') if path.is_file() and path.suffix in ('.vh', '.svh')]
    tracked += [A3/'scripts'/name for name in ('server_run.py', 'install_platform.py', 'install_dma16.py',
        'install_mmio8_source.py', 'asic_boot.py', 'build_mmio8_source.py', 'build_dma16_firmware.py',
        'mmio8_soc.py', 'mmio8_source_layout.py', 'dma16_batch.py', 'timing_contract.py', 'stdcell_verify.py',
        'activity.py', 'activity_fast.py', 'activity_scan.cpp')]
    before = {str(path.resolve()): sha(path) for path in tracked}
    save(run/'source_inputs.json', before)
    started = time.monotonic();log = call(command, run, 'compile.log')
    common.require(not re.search(r'Warning-\[(?:IPDW|PCWM-W|INAV|SIOB)\]', log), 'MMIO8 VCS declaration/width warning requires review')
    common.require((run/'simv').is_file(), 'Missing MMIO8 simulator')
    check_frozen(before)
    boot_by_shift, boot_files = {}, []
    for shift, image in sorted(images.items()):
        boot = run/('boot_shift_%02d' % shift)
        boot_receipt = prepare(image, boot)
        boot_receipt.update(scope='initial_ITCM_firmware_only', runtime_task_loading='CPU_original_SysMem_ICB')
        save(boot/'manifest.json', boot_receipt)
        boot_by_shift[shift] = boot
        boot_files += [path for path in boot.iterdir() if path.is_file()]
    receipt = dict(status='compiled_only', scope='asic_rtl_functional', cpu_executed=False,
        reference='original_repaired_MMIO8_same_SysMem_source', DMA_present=False,
        elapsed_seconds=time.monotonic()-started, global_FPGA_defined=False,
        platform_baseline_sha256=platform_manifest['baseline_sha256'], firmware_sha256=sha(firmware/'manifest.json'),
        source_inputs_sha256=sha(run/'source_inputs.json'), command_sha256=sha(run/'compile_command.json'),
        executable_sha256=sha(run/'simv'), input_task_bytes_in_boot=0,
        gate_simulation_verified=False, timing_verified=False, system_power_verified=False)
    save(run/'compile_receipt.json', receipt)
    frozen = dict(before)
    for path in boot_files+[run/name for name in ('simv', 'compile_command.json', 'compile.log', 'source_inputs.json', 'compile_receipt.json')]:
        frozen[str(path.resolve())] = sha(path)
    check_frozen(frozen)
    return frozen, receipt, boot_by_shift


def verify(cfg, run, platform_source, cases, call, activity_cases=(), firmware=None):
    run = Path(run).resolve()
    common.require(cases and len(cases) == len(set(cases)) and set(cases) <= set(common.CASES14), 'Invalid/duplicate MMIO8 reference cases')
    common.require(set(activity_cases) <= set(cases), 'Unselected MMIO8 activity case')
    original_inputs, shifts = {}, set()
    for name in cases:
        source = ROOT/'validated_data'/name
        meta, _, _, _ = common.source_case(source);shifts.add(meta['shift'])
        for path in [source/'layout.json']+[source/rel for rel in meta['sha256']]:
            original_inputs[str(path.resolve())] = sha(path)
    # Reject missing boot shifts before invoking the compiler.
    _, images = verify_firmware(Path(firmware or ROOT/'firmware_mmio8').resolve())
    common.require(shifts <= set(images), 'MMIO8 firmware is missing required task shifts')
    frozen, receipt, boot_by_shift = compile_design(cfg, run, platform_source, call, firmware)
    frozen.update(original_inputs);check_frozen(frozen)
    save(run/'frozen_inputs.json', frozen)
    frozen_manifest_sha = sha(run/'frozen_inputs.json')
    results = []
    for name in cases:
        try:
            check_frozen(frozen)
            common.require(sha(run/'frozen_inputs.json') == frozen_manifest_sha, 'MMIO8 frozen manifest changed')
            source, task = ROOT/'validated_data'/name, run/(name+'_data')
            info = layout.prepare_case(source, task);layout.verify_prepared(source, task)
            capture = run/(name+'.csv')
            command = [str(run/'simv'), '+BOOT_DIR='+str(boot_by_shift[info['shift']]),
                       '+LOAD32='+str(task/'load32.hex'), '+DATA_DIR='+str(task),
                       '+CAPTURE='+str(capture), '+SHIFT='+str(info['shift'])]
            if name in activity_cases:command += ['+ACTIVITY='+str(run/(name+'.vcd'))]
            save(run/(name+'_command.json'), command)
            started = time.monotonic();text = call(command, run, name+'.log');elapsed = time.monotonic()-started
            captured = common.check_capture(capture, task)
            window = read_window(text, captured['saturated'])
            item = dict(case=name, status='passed', scope='asic_rtl_functional', cpu_executed=True,
                outputs=25344, task_window=window, capture=captured, host_elapsed_seconds=elapsed,
                firmware_shift=info['shift'], layout_sha256=sha(task/'layout_manifest.json'),
                boot_manifest_sha256=sha(boot_by_shift[info['shift']]/'manifest.json'),
                frozen_inputs_sha256=frozen_manifest_sha,
                artifacts={suffix: sha(run/(name+suffix)) for suffix in ('_command.json', '.log', '.csv')},
                gate_simulation_verified=False, timing_verified=False, system_power_verified=False, official_precision_verified=False)
            if name in activity_cases:
                from activity_fast import audit_activity
                item['activity'] = audit_activity(run/(name+'.vcd'), window, run, call)
            check_frozen(frozen);layout.verify_prepared(source, task)
            common.require(sha(run/'frozen_inputs.json') == frozen_manifest_sha, 'MMIO8 frozen manifest changed')
            save(run/(name+'_result.json'), item)
            results.append(item);save(run/'case_progress.json', results)
            print('MMIO8_SOURCE_ASIC_CASE_PASS', name, 'cycles', window['cycles'], 'host_seconds', elapsed, flush=True)
        except BaseException as exc:
            save(run/(name+'_failure.json'), dict(case=name, status='failed', error=str(exc), type=type(exc).__name__,
                scope='MMIO8_reference_attempt', asic_execution_verified=False, frozen_inputs_sha256=frozen_manifest_sha))
            raise
    total_cycles = sum(item['task_window']['cycles'] for item in results)
    return dict(status='passed', scope='asic_rtl_functional', cpu_executed=True, asic_cpu_verified=True,
        reference='original_repaired_MMIO8_same_SysMem_source', DMA_present=False, global_FPGA_defined=False,
        cases=results, aggregate=dict(tasks=len(results), outputs=len(results)*25344, cycles=total_cycles,
            average_cycles=total_cycles/float(len(results)), task_per_second=len(results)*150000000.0/total_cycles,
            mmac_per_second=len(results)*1622016.0*150.0/total_cycles),
        compile_receipt=receipt, frozen_inputs_sha256=frozen_manifest_sha,
        gate_simulation_verified=False, timing_verified=False, system_power_verified=False, official_precision_verified=False)
