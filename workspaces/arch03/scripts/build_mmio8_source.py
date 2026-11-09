"""Compile the unchanged legacy MMIO8 driver with a real SysMem source loader.

Python 3.6 standard library. Program-only ITCM; shift metadata is at 0xfff0.
Reuse the reviewed ELF boundary helpers without changing the DMA16 builder.
Compilation does not establish CPU execution, timing, power or bus counts.
"""
import argparse
import os
from pathlib import Path
import subprocess
from build_dma16_firmware import elf_image, metadata_image, require, save, sha, self_test

ROOT = Path(__file__).resolve().parents[3]
SW = ROOT/'workspaces/arch03/sw'


def build(zig, output, shifts=(11, 12), timeout=100000000, clear_timeout=1000000):
    zig, output = Path(zig).resolve(), Path(output).resolve()
    require(not output.exists(), 'Firmware output exists; use a new directory')
    require(shifts and len(shifts) == len(set(shifts)) and
            all(type(s) is int and 0 <= s <= 31 for s in shifts), 'Invalid unique shifts')
    require(type(timeout) is int and type(clear_timeout) is int and
            0 < timeout < (1 << 63) and 0 < clear_timeout < (1 << 63), 'Invalid timeout')
    sources = [SW/n for n in ('kwt.h', 'kwt.c', 'main_mmio8_source.c', 'start.S', 'link.ld')]
    sources += [Path(__file__).resolve(), Path(__file__).resolve().with_name('build_dma16_firmware.py')]
    before = {p.relative_to(ROOT).as_posix(): sha(p) for p in sources}
    output.mkdir(parents=True)
    elf = output/'driver.elf'
    command = [str(zig), 'cc', '-target', 'riscv32-freestanding-none', '-mcpu=generic_rv32+m+a+c',
               '-mabi=ilp32', '-ffreestanding', '-fno-stack-protector', '-fno-builtin', '-Os',
               '-Wall', '-Wextra', '-Werror', '-nostdlib', '-mno-relax', '-Wl,-T,'+str(SW/'link.ld'),
               '-DKWT_MMIO8_TIMEOUT_CYCLES=%dull' % timeout,
               '-DKWT_MMIO8_CLEAR_TIMEOUT_CYCLES=%dull' % clear_timeout]
    command += [str(SW/n) for n in ('start.S', 'kwt.c', 'main_mmio8_source.c')]+['-o', str(elf)]
    environment = os.environ.copy()
    environment['ZIG_LOCAL_CACHE_DIR'] = str(output/'zig-local-cache')
    environment['ZIG_GLOBAL_CACHE_DIR'] = str(ROOT/'local_runs/zig-mmio8-source-cache')
    save(output/'build_command.json', command)
    compiled = subprocess.run(command, env=environment, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (output/'build.log').write_bytes(compiled.stdout)
    require(compiled.returncode == 0, 'Zig failed; inspect preserved build.log')
    base, segments = elf_image(elf.read_bytes())
    images = {}
    for shift in shifts:
        image = metadata_image(base, shift)
        name = 'shift_%02d' % shift
        binary, text = output/(name+'.bin'), output/(name+'.verilog')
        binary.write_bytes(image)
        text.write_bytes(''.join('%02x\n' % value for value in image).encode('ascii'))
        images[name] = dict(shift=shift, image_bytes=len(image), sha256=sha(text), binary_sha256=sha(binary),
            firmware_only=True, metadata_offset=0xfff0, task_input_region_start=0x10000,
            task_input_region_nonzero_bytes=sum(value != 0 for value in image[0x10000:]))
    require(before == {p.relative_to(ROOT).as_posix(): sha(p) for p in sources}, 'Source changed during build')
    report = dict(run_mode='single_cpu_mmio8_source_v1', status='compiled_only',
        compiler_sha256=sha(zig), compiler_version=subprocess.check_output([str(zig), 'version'], env=environment).decode().strip(),
        command=command, elf_sha256=sha(elf), source_sha256=before, segments=segments, images=images,
        configuration=dict(timeout_cycles=timeout, clear_timeout_cycles=clear_timeout, irq_enabled=False,
                           original_mmio_driver_unchanged=True),
        physical_boot_policy='firmware_only_no_task_inputs', task_source_address='0xb0000000',
        shared_input_address='0xa0000000', shared_output_address='0xa000c000',
        peripheral_id='0x4b575403', layout_tag='0x00080001',
        numeric_layout='legacy_tile8_X6336_then_32x_W512_bias24',
        software_accesses=dict(source_uint32_reads=11744, initial_shared_uint32_writes=11744,
            driver_shared_uint16_reads=23488, driver_output_int16_writes=25344,
            measured_ICB_transaction_counts=None),
        timing=dict(start='first_source_request_valid', end='last_output_write_response_with_drain',
            begin_mailbox_is_arm_only=True, cpu_cycles_are_diagnostic=True),
        cpu_executed=False, interrupts_executed=False, rtl_verified=False,
        timing_verified=False, system_power_verified=False)
    save(output/'manifest.json', report)
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--zig', type=Path)
    p.add_argument('--output', type=Path)
    p.add_argument('--shifts', nargs='+', type=int, default=[11, 12])
    p.add_argument('--timeout-cycles', type=int, default=100000000)
    p.add_argument('--clear-timeout-cycles', type=int, default=1000000)
    p.add_argument('--self-test', action='store_true')
    a = p.parse_args()
    if a.self_test:
        print(self_test());return
    require(a.zig is not None and a.output is not None, 'Build needs --zig and --output')
    result = build(a.zig, a.output, a.shifts, a.timeout_cycles, a.clear_timeout_cycles)
    print('MMIO8_SOURCE_FIRMWARE_BUILT images=%d cpu_executed=false input_preloaded=false' % len(result['images']))


if __name__ == '__main__':
    main()
