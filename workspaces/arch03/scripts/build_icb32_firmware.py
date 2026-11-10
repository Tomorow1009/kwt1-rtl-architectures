"""Build firmware-only RV32 ICB32 boot images with Zig, no task data input.

The default build polls. IRQ/WFI requires a separately reviewed PLIC/CLINT JSON
mapping; compiler success is never CPU, interrupt, timing or power acceptance.
Python 3.6 standard library only. Historical firmware/scripts remain untouched.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess

ROOT = Path(__file__).resolve().parents[3]
SW = ROOT/'workspaces/arch03/sw'
IRQ_MACROS = {
    'irq_id': 'KWT_DMA_IRQ_ID', 'plic_priority_addr': 'KWT_PLIC_PRIORITY_ADDR',
    'plic_enable_addr': 'KWT_PLIC_ENABLE_ADDR', 'plic_enable_mask': 'KWT_PLIC_ENABLE_MASK',
    'plic_threshold_addr': 'KWT_PLIC_THRESHOLD_ADDR', 'plic_claim_addr': 'KWT_PLIC_CLAIM_ADDR',
    'mtime_addr': 'KWT_MTIME_ADDR', 'mtimecmp_addr': 'KWT_MTIMECMP_ADDR',
    'timer_wake_ticks': 'KWT_TIMER_WAKE_TICKS', 'timer_probe_cycles': 'KWT_TIMER_PROBE_CYCLES'}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def save(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False)+'\n', encoding='utf8')


def irq_config(path):
    data = json.loads(Path(path).read_text(encoding='utf-8-sig'))
    require(data.get('mapping_verified') is True and isinstance(data.get('mapping_evidence'), str)
            and data['mapping_evidence'].strip(), 'IRQ mapping needs explicit verified source evidence')
    values = {}
    for field in IRQ_MACROS:
        value = data[field]
        if isinstance(value, str):
            value = int(value, 0)
        require(type(value) is int and 0 < value <= 0xffffffff, 'Invalid IRQ field: '+field)
        values[field] = value
    require(0 < values['irq_id'] < 32 and values['plic_enable_mask'] == 1 << values['irq_id'], 'IRQ ID/enable mask mismatch')
    for field in IRQ_MACROS:
        if field.endswith('_addr'):
            require(values[field] % 4 == 0, 'Unaligned IRQ register: '+field)
    addresses = [values[k] for k in IRQ_MACROS if k.endswith('_addr')]
    addresses += [values['mtime_addr']+4, values['mtimecmp_addr']+4]
    require(len(addresses) == len(set(addresses)) and max(addresses) <= 0xffffffff, 'Overlapping IRQ register addresses')
    require(values['timer_wake_ticks'] > 0 and values['timer_probe_cycles'] > 0, 'A real periodic timer is required')
    return dict(values=values, mapping_evidence=data['mapping_evidence'], input_sha256=sha(path))


def elf_image(raw):
    require(raw[:7] == b'\x7fELF\x01\x01\x01' and len(raw) >= 52, 'Expected ELF32 little endian')
    h = struct.unpack_from('<HHIIIIIHHHHHH', raw, 16)
    require(h[0] == 2 and h[1] == 243 and h[3] == 0x80000000, 'Wrong ELF type/architecture/entry')
    require(h[8] == 32 and h[4]+h[8]*h[9] <= len(raw), 'Invalid program headers')
    image = bytearray(262144)
    segments = []
    occupied = set()
    for i in range(h[9]):
        typ, off, va, pa, filesz, memsz, flags, align = struct.unpack_from('<IIIIIIII', raw, h[4]+i*h[8])
        if typ != 1 or not filesz:
            continue
        require(va == pa and 0x80000000 <= pa < pa+filesz <= 0x8000fff0
                and filesz <= memsz and off+filesz <= len(raw), 'Firmware load segment escapes ITCM code region')
        span = set(range(pa-0x80000000, pa-0x80000000+filesz))
        require(not span.intersection(occupied), 'Overlapping firmware load segments')
        occupied.update(span)
        image[pa-0x80000000:pa-0x80000000+filesz] = raw[off:off+filesz]
        segments.append(dict(address=pa, file_bytes=filesz, memory_bytes=memsz, flags=flags))
    require(segments and not any(image[0xfff0:]), 'Firmware occupies metadata or task input region')
    return image, segments


def metadata_image(base, shift, encoded_bytes=47008, row_lanes=4):
    require(type(encoded_bytes) is int and 32 <= encoded_bytes <= 47008 and encoded_bytes%4==0, "Invalid encoded length")
    require(row_lanes in (1,4), "Invalid row lanes")
    require(type(shift) is int and 0 <= shift <= 31 and len(base) == 262144, 'Invalid boot shift/image')
    require(not any(base[0xfff0:]), 'Base image contains forbidden metadata/input bytes')
    result = bytearray(base)
    struct.pack_into('<4I', result, 0xfff0, shift, encoded_bytes, 0x00100002, row_lanes)
    require(not any(result[0x10000:]), 'Task inputs must never enter the ITCM boot image')
    return result


def self_test():
    # Synthetic ELF tests check the build boundary, not CPU behavior.
    raw = bytearray(0x104)
    raw[:7] = b'\x7fELF\x01\x01\x01'
    struct.pack_into('<HHIIIIIHHHHHH', raw, 16, 2, 243, 1, 0x80000000, 52, 0, 0, 52, 32, 1, 0, 0, 0)
    struct.pack_into('<IIIIIIII', raw, 52, 1, 0x100, 0x80000000, 0x80000000, 4, 4, 5, 4)
    raw[0x100:] = b'\x13\0\0\0'
    image, _ = elf_image(bytes(raw))
    for shift in (0, 11, 12, 31):
        boot = metadata_image(image, shift)
        require(struct.unpack_from('<I', boot, 0xfff0)[0] == shift and not any(boot[0x10000:]), 'Self-test image mismatch')
    for address in (0x8000fff0, 0x80010000, 0x90000000):
        bad = bytearray(raw)
        struct.pack_into('<I', bad, 52+8, address);struct.pack_into('<I', bad, 52+12, address)
        try:
            elf_image(bytes(bad))
        except ValueError:
            pass
        else:
            raise AssertionError('Illegal load segment accepted')
    bad = bytearray(image);bad[0x10000] = 1
    try:
        metadata_image(bad, 12)
    except ValueError:
        pass
    else:
        raise AssertionError('Task input boot preload accepted')
    return dict(status='passed', checks=8, scope='ELF_and_boot_boundary_only', cpu_executed=False)


def build(zig, output, shifts, mode=1, prefetch=1, timeout=100000000, cancel_timeout=1000000, interrupt=None, row_lanes=4, encoded_bytes=47008):
    zig, output = Path(zig).resolve(), Path(output).resolve()
    require(not output.exists(), 'Firmware output exists; use a new directory')
    require(shifts and len(set(shifts)) == len(shifts) and all(type(s) is int and 0 <= s <= 31 for s in shifts), 'Invalid unique shifts')
    require(mode == 1 and prefetch in (0, 1) and 0 < timeout < (1 << 63) and 0 < cancel_timeout < (1 << 63), 'Invalid firmware configuration')
    require(not interrupt or mode == 1, 'WFI mode is only for task DMA; debug MMIO needs CPU service')
    sources = [SW/n for n in ('kwt_icb32.h', 'kwt_icb32.c', 'main_icb32.c', 'start_icb32.S', 'link.ld')]
    sources += [Path(__file__).resolve(), ROOT/'workspaces/arch03/ICB32_ABI.md']
    before = {p.relative_to(ROOT).as_posix(): sha(p) for p in sources}
    output.mkdir(parents=True)
    elf = output/'driver.elf'
    definitions = dict(KWT_ICB32_ROWS=row_lanes, KWT_ICB32_USE_IRQ=int(interrupt is not None), KWT_ICB32_DEFAULT_MODE=mode,
                       KWT_ICB32_DEFAULT_PREFETCH=prefetch, KWT_ICB32_TIMEOUT_CYCLES=timeout,
                       KWT_ICB32_CANCEL_TIMEOUT_CYCLES=cancel_timeout)
    if interrupt:
        definitions.update({IRQ_MACROS[k]: v for k, v in interrupt['values'].items()})
        definitions['KWT_DMA_IRQ_MAPPING_VERIFIED'] = 1
    command = [str(zig), 'cc', '-target', 'riscv32-freestanding-none', '-mcpu=generic_rv32+m+a+c',
               '-mabi=ilp32', '-ffreestanding', '-fno-stack-protector', '-fno-builtin', '-Os',
               '-Wall', '-Wextra', '-Werror', '-nostdlib', '-mno-relax', '-Wl,-T,'+str(SW/'link.ld')]
    command += ['-D%s=%sull' % (name, value) for name, value in sorted(definitions.items())]
    command += [str(SW/name) for name in ('start_icb32.S', 'kwt_icb32.c', 'main_icb32.c')]+['-o', str(elf)]
    environment = os.environ.copy()
    environment['ZIG_LOCAL_CACHE_DIR'] = str(output/'zig-local-cache')
    environment['ZIG_GLOBAL_CACHE_DIR'] = str(ROOT/'local_runs/zig-icb32-cache')
    save(output/'build_command.json', command)
    compiled = subprocess.run(command, env=environment, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (output/'build.log').write_bytes(compiled.stdout)
    require(compiled.returncode == 0, 'Zig failed; inspect preserved build.log')
    base, segments = elf_image(elf.read_bytes())
    images = {}
    for shift in shifts:
        image = metadata_image(base, shift, encoded_bytes, row_lanes)
        name = 'shift_%02d' % shift
        binary, text = output/(name+'.bin'), output/(name+'.verilog')
        binary.write_bytes(image)
        text.write_bytes(''.join('%02x\n' % byte for byte in image).encode('ascii'))
        images[name] = dict(shift=shift, encoded_bytes=encoded_bytes, row_lanes=row_lanes, image_bytes=len(image), sha256=sha(text), binary_sha256=sha(binary),
            firmware_only=True, metadata_offset=0xfff0, task_input_region_start=0x10000,
            task_input_region_nonzero_bytes=sum(v != 0 for v in image[0x10000:]))
    require(before == {p.relative_to(ROOT).as_posix(): sha(p) for p in sources}, 'Firmware source changed during build')
    report = dict(run_mode='single_cpu_icb32_v2', status='compiled_only', compiler_sha256=sha(zig),
        compiler_version=subprocess.check_output([str(zig), 'version'], env=environment).decode().strip(),
        command=command, elf_sha256=sha(elf), source_sha256=before, segments=segments, images=images,
        configuration=dict(row_lanes=row_lanes, default_encoded_bytes=encoded_bytes, mode=mode, prefetch=prefetch, irq_enabled=interrupt is not None,
                           timeout_cycles=timeout, cancel_timeout_cycles=cancel_timeout, irq_mapping=interrupt),
        physical_boot_policy='firmware_only_no_task_inputs', task_source_address='0xb0000000',
        numeric_layout_id='0x00100002', peripheral_id='0x4b574604' if row_lanes==4 else '0x4b574601', cpu_executed=False,
        interrupts_executed=False, timer_wakeup_verified=False, rtl_verified=False,
        timing_verified=False, system_power_verified=False)
    save(output/'manifest.json', report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--zig', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--shifts', nargs='+', type=int, default=[11, 12])
    parser.add_argument('--mode', type=int, choices=(1,), default=1)
    parser.add_argument('--rows', type=int, choices=(1,4), default=4)
    parser.add_argument('--encoded-bytes', type=int, default=47008)
    parser.add_argument('--prefetch', type=int, choices=(0, 1), default=1)
    parser.add_argument('--timeout-cycles', type=int, default=100000000)
    parser.add_argument('--cancel-timeout-cycles', type=int, default=1000000)
    parser.add_argument('--irq-config', type=Path)
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps(self_test(), sort_keys=True));return
    require(args.zig is not None and args.output is not None, 'Build needs --zig and --output')
    interrupt = irq_config(args.irq_config) if args.irq_config else None
    result = build(args.zig, args.output, args.shifts, args.mode, args.prefetch,
                   args.timeout_cycles, args.cancel_timeout_cycles, interrupt, args.rows, args.encoded_bytes)
    print('ICB32_FIRMWARE_BUILT images=%d irq=%s cpu_executed=false input_preloaded=false' %
          (len(result['images']), result['configuration']['irq_enabled']))


if __name__ == '__main__':
    main()
