"""Build an isolated polling CPU/shared-SRAM stress image, not performance FW."""
import argparse
import os
from pathlib import Path
import subprocess
from build_p80_firmware import ROOT, SW, elf_image, metadata_image, require, save, sha
from p80_soc import verify_firmware

BENCHMARK = 'p80_cpu_shared_sram_contention_v1'
SCRATCH = dict(address=0xa0040000, bytes=128, minimum_checked_rounds=1,
               pattern='0x5a69c300 XOR (round*33+word)', operations='volatile write/fence/read/compare')


def build(zig, output, shifts=(10,), rows=5, layout=0x00100004, transaction_depth=4):
    require(transaction_depth in (2,4,8),'Invalid P80 depth')
    require(rows == 5 and layout == 0x00100004, 'Invalid N1 rows/layout')
    zig, output = Path(zig).resolve(), Path(output).resolve()
    require(not output.exists(), 'Use a new contention firmware directory')
    require(shifts and len(set(shifts)) == len(shifts) and all(type(s) is int and s == 10 for s in shifts),
            'Invalid contention image shifts')
    sources = [SW/n for n in ('kwt_p80.h', 'kwt_p80.c', 'main_p80_contention.c', 'start_icb32.S', 'link.ld')]
    sources += [Path(__file__).resolve(), Path(__file__).resolve().with_name('build_p80_firmware.py'),
                ROOT/'workspaces/arch03/P80_ABI.md']
    before = {p.relative_to(ROOT).as_posix(): sha(p) for p in sources}
    output.mkdir(parents=True)
    elf = output/'driver.elf'
    command = [str(zig), 'cc', '-target', 'riscv32-freestanding-none', '-mcpu=generic_rv32+m+a+c',
               '-mabi=ilp32', '-ffreestanding', '-fno-stack-protector', '-fno-builtin', '-Os',
               '-Wall', '-Wextra', '-Werror', '-nostdlib', '-mno-relax', '-Wl,-T,'+str(SW/'link.ld'),
               '-DKWT_P80_TRANSACTION_DEPTH=%du'%transaction_depth,'-DKWT_ICB32_USE_IRQ=0','-DKWT_ICB32_ROWS=%du'%rows]
    command += [str(SW/n) for n in ('start_icb32.S', 'kwt_p80.c', 'main_p80_contention.c')]+['-o', str(elf)]
    environment = os.environ.copy()
    environment['ZIG_LOCAL_CACHE_DIR'] = str(output/'zig-local-cache')
    environment['ZIG_GLOBAL_CACHE_DIR'] = str(ROOT/'local_runs/zig-p80-contention-cache')
    save(output/'build_command.json', command)
    result = subprocess.run(command, env=environment, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (output/'build.log').write_bytes(result.stdout)
    require(result.returncode == 0, 'Contention compilation failed; preserved build.log')
    base, segments = elf_image(elf.read_bytes()); images = {}
    for shift in shifts:
        image = metadata_image(base, shift, 47008, rows, layout); name = 'shift_%02d' % shift
        binary, text = output/(name+'.bin'), output/(name+'.verilog')
        binary.write_bytes(image); text.write_bytes(''.join('%02x\n' % v for v in image).encode('ascii'))
        images[name] = dict(layout=layout,shift=shift, encoded_bytes=47008, row_lanes=rows, image_bytes=len(image), sha256=sha(text), binary_sha256=sha(binary),
                            firmware_only=True, task_input_region_nonzero_bytes=0)
    require(before == {p.relative_to(ROOT).as_posix(): sha(p) for p in sources}, 'Firmware inputs changed')
    manifest = dict(run_mode='single_cpu_p80_x14_w12_b32_v4', benchmark=BENCHMARK, scratch=SCRATCH,
        performance_firmware=False, status='compiled_only', command=command, compiler_sha256=sha(zig),
        compiler_version=subprocess.check_output([str(zig), 'version'], env=environment).decode().strip(),
        elf_sha256=sha(elf), source_sha256=before, segments=segments, images=images,
        numeric_layout_id='0x%08x'%layout,supported_layout_ids=['0x00100004'],numeric_format='0x000e0c20',peripheral_id='0x4b57530b',
        configuration=dict(transaction_metadata_depth=transaction_depth,default_layout=layout,row_lanes=rows,default_encoded_bytes=47008,mode=1, prefetch=1, irq_enabled=False, irq_mapping=None, benchmark=BENCHMARK,
                           timeout_cycles=100000000, cancel_timeout_cycles=1000000),
        physical_boot_policy='firmware_only_no_task_inputs', cpu_executed=False,
        timing_verified=False, system_power_verified=False)
    save(output/'manifest.json', manifest); verify_firmware(output)
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--zig', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--transaction-depth',type=int,choices=(2,4,8),default=4)
    parser.add_argument('--rows', type=int, choices=(5,), default=5)
    parser.add_argument('--layout', type=int, choices=(4,), default=4)
    args = parser.parse_args(); build(args.zig, args.output, rows=args.rows, layout=0x00100000+args.layout,transaction_depth=args.transaction_depth)
    print('P80_CONTENTION_FIRMWARE_BUILT cpu_executed=false performance_firmware=false')
