"""Build an isolated polling CPU/shared-SRAM stress image, not performance FW."""
import argparse
import os
from pathlib import Path
import subprocess
from build_dma16_firmware import ROOT, SW, elf_image, metadata_image, require, save, sha
from dma16_soc import verify_firmware

BENCHMARK = 'cpu_shared_sram_contention_v1'
SCRATCH = dict(address=0xa0040000, bytes=128, minimum_checked_rounds=16,
               pattern='0x5a69c300 XOR (round*33+word)', operations='volatile write/fence/read/compare')


def build(zig, output, shifts=(11, 12)):
    zig, output = Path(zig).resolve(), Path(output).resolve()
    require(not output.exists(), 'Use a new contention firmware directory')
    require(shifts and len(set(shifts)) == len(shifts) and all(type(s) is int and 0 <= s <= 31 for s in shifts),
            'Invalid contention image shifts')
    sources = [SW/n for n in ('kwt_dma16.h', 'kwt_dma16.c', 'main_dma16_contention.c', 'start_dma16.S', 'link.ld')]
    sources += [Path(__file__).resolve(), Path(__file__).resolve().with_name('build_dma16_firmware.py'),
                ROOT/'workspaces/arch03/DMA16_ABI.md']
    before = {p.relative_to(ROOT).as_posix(): sha(p) for p in sources}
    output.mkdir(parents=True)
    elf = output/'driver.elf'
    command = [str(zig), 'cc', '-target', 'riscv32-freestanding-none', '-mcpu=generic_rv32+m+a+c',
               '-mabi=ilp32', '-ffreestanding', '-fno-stack-protector', '-fno-builtin', '-Os',
               '-Wall', '-Wextra', '-Werror', '-nostdlib', '-mno-relax', '-Wl,-T,'+str(SW/'link.ld'),
               '-DKWT_DMA16_USE_IRQ=0']
    command += [str(SW/n) for n in ('start_dma16.S', 'kwt_dma16.c', 'main_dma16_contention.c')]+['-o', str(elf)]
    environment = os.environ.copy()
    environment['ZIG_LOCAL_CACHE_DIR'] = str(output/'zig-local-cache')
    environment['ZIG_GLOBAL_CACHE_DIR'] = str(ROOT/'local_runs/zig-dma16-cache')
    save(output/'build_command.json', command)
    result = subprocess.run(command, env=environment, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (output/'build.log').write_bytes(result.stdout)
    require(result.returncode == 0, 'Contention compilation failed; preserved build.log')
    base, segments = elf_image(elf.read_bytes()); images = {}
    for shift in shifts:
        image = metadata_image(base, shift); name = 'shift_%02d' % shift
        binary, text = output/(name+'.bin'), output/(name+'.verilog')
        binary.write_bytes(image); text.write_bytes(''.join('%02x\n' % v for v in image).encode('ascii'))
        images[name] = dict(shift=shift, image_bytes=len(image), sha256=sha(text), binary_sha256=sha(binary),
                            firmware_only=True, task_input_region_nonzero_bytes=0)
    require(before == {p.relative_to(ROOT).as_posix(): sha(p) for p in sources}, 'Firmware inputs changed')
    manifest = dict(run_mode='single_cpu_dma16_v1', benchmark=BENCHMARK, scratch=SCRATCH,
        performance_firmware=False, status='compiled_only', command=command, compiler_sha256=sha(zig),
        compiler_version=subprocess.check_output([str(zig), 'version'], env=environment).decode().strip(),
        elf_sha256=sha(elf), source_sha256=before, segments=segments, images=images,
        configuration=dict(mode=1, prefetch=1, irq_enabled=False, irq_mapping=None, benchmark=BENCHMARK,
                           timeout_cycles=100000000, cancel_timeout_cycles=1000000),
        physical_boot_policy='firmware_only_no_task_inputs', cpu_executed=False,
        timing_verified=False, system_power_verified=False)
    save(output/'manifest.json', manifest); verify_firmware(output)
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--zig', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args(); build(args.zig, args.output)
    print('DMA16_CONTENTION_FIRMWARE_BUILT cpu_executed=false performance_firmware=false')
