"""Standalone R1/R4 core regression; not E203, DMA, timing or server acceptance.

The input adapter independently permutes the checked legacy stream into tile16.
Reference totals/results remain the existing independently checked matrix values.
"""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
A2 = ROOT / 'workspaces/arch02'
A3 = ROOT / 'workspaces/arch03'
sys.path.insert(0, str(A2 / 'arch02/scripts'))
from data import prepare


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(argv, cwd, log):
    with (cwd / log).open('w', encoding='utf8') as out:
        proc = subprocess.run([str(a) for a in argv], cwd=str(cwd), stdout=out,
                              stderr=subprocess.STDOUT, timeout=3600)
    text = (cwd / log).read_text(errors='replace')
    if proc.returncode or re.search(r'(?im)^\s*(fatal|error)(:|\s)', text):
        raise RuntimeError('Failed: ' + str(cwd / log))
    return text


def tile16(source, target):
    layout = json.loads((source / 'layout.json').read_text())
    for name, digest in layout['sha256'].items():
        if sha(source / name) != digest:
            raise ValueError('Source vector hash changed: ' + name)
    old = [int(x, 16) for x in (source / 'load.hex').read_text().split()]
    if len(old) != 23488 or any(not 0 <= x < 65536 for x in old):
        raise ValueError('Legacy stream geometry')
    order = list(range(6336))
    for tile in range(16):
        for k in range(64):
            for lane in range(16):
                order.append(6336 + (tile * 2 + lane // 8) * 536 + k * 8 + lane % 8)
        for lane in range(16):
            for part in range(3):
                order.append(6336 + (tile * 2 + lane // 8) * 536 + 512 + lane % 8 * 3 + part)
    if sorted(order) != list(range(23488)):
        raise ValueError('Tile16 conversion is not a complete permutation')
    words = [old[i] for i in order]
    # Check every original (k,column) and every bias part through the inverse
    # address map, independently of the forward loop's lane/group split.
    for column in range(256):
        for k in range(64):
            old_idx = 6336 + (column >> 3) * 536 + (k << 3) + (column & 7)
            new_idx = 6336 + (column >> 4) * 1072 + (k << 4) + (column & 15)
            if old[old_idx] != words[new_idx]:
                raise ValueError('Tile16 weight coordinate mismatch')
        for part in range(3):
            old_idx = 6336 + (column >> 3) * 536 + 512 + (column & 7) * 3 + part
            new_idx = 6336 + (column >> 4) * 1072 + 1024 + (column & 15) * 3 + part
            if old[old_idx] != words[new_idx] or (part == 2 and words[new_idx] > 255):
                raise ValueError('Tile16 bias coordinate/padding mismatch')
    target.mkdir(parents=True)
    (target / 'load.hex').write_text(''.join('%04x\n' % x for x in words), encoding='ascii')
    for name in ('expected.npz', 'total.hex', 'result.hex', 'saturated.hex'):
        shutil.copyfile(source / name, target / name)
    result = dict(schema='arch03-core-tile16-v1', shift=layout['shift'],
                  load_words=23488, outputs=25344, source_layout_sha256=sha(source / 'layout.json'),
                  sha256={p.name: sha(p) for p in target.iterdir()})
    (target / 'layout.json').write_text(json.dumps(result, indent=2), encoding='utf8')
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--vivado-bin', required=True)
    ap.add_argument('--rows', type=int, choices=[1,4], default=4)
    ap.add_argument('--backend', choices=['behavioral', 'pin_mock'], default='pin_mock')
    ap.add_argument('--cases', nargs='+', default=['layer_%02d' % i for i in range(1, 13)] + ['extremes', 'rounding'])
    ap.add_argument('--prefetch', type=int, nargs='+', choices=[0, 1], default=[0, 1])
    ap.add_argument('--jitter', type=int, choices=[0, 1], default=1)
    ap.add_argument('--repeats', type=int, default=2)
    ap.add_argument('--prepared', type=Path, help='Existing checked tile8 vectors')
    args = ap.parse_args()
    if args.repeats < 1:
        raise ValueError('repeats must be positive')
    folder = ROOT / 'local_runs' / ('arch03_linear16x4_' + datetime.now().strftime('%Y%m%d_%H%M%S_%f') + '_' + args.backend)
    folder.mkdir(parents=True)
    source = args.prepared.resolve() if args.prepared else folder / 'tile8'
    if not args.prepared:
        report = prepare(ROOT / 'architectures/arch01_serial_mac/v1.3.0/KWT1/model_data/outputs/real_sample_001', source)
        (folder / 'software.json').write_text(json.dumps(report, indent=2), encoding='utf8')
    for name in sorted(set(args.cases + ['layer_01', 'layer_12'])):
        tile16(source / name, folder / 'tile16' / name)
    files = [A2 / 'rtl/requantize.sv', A2 / 'rtl/dot64.sv', A2 / 'arch02/rtl/sram_port.sv',
             A3 / 'rtl/arch03_linear16x4.sv', A3 / 'tb/tb_arch03_linear16x4.sv']
    define = 'ARCH02_BEHAVIORAL'
    if args.backend == 'behavioral':
        files.append(A2 / 'arch02/tb/sram_model.sv')
    else:
        define = 'ARCH02_PIN_MOCK'
        files.extend([A2 / 'arch02/rtl/sram_macro_adapter.sv', A2 / 'arch02/tb/pin_mock.sv'])
        cfg = json.loads((A2 / 'arch02/tb/pin_mock_config.json').read_text())
        lines = []
        for size in ('128', '4096'):
            for key, width in [('cen_low', 1), ('gwen_low', 1), ('wen_low', 1), ('ema', 3), ('emaw', 2), ('ret1n', 1)]:
                lines.append("`define A02_%s_%s %d'd%d" % (size, key.upper(), width, cfg['macros'][size][key]))
        (folder / 'arch02_sram_config.vh').write_text('\n'.join(lines) + '\n', encoding='ascii')
    tracked = files + [Path(__file__).resolve()]
    if args.backend == 'pin_mock':
        tracked.extend([A2 / 'arch02/tb/pin_mock_config.json', folder / 'arch02_sram_config.vh'])
    hashes = {str(p): sha(p) for p in tracked}
    tool = lambda name: Path(args.vivado_bin) / (name + '.bat')
    run([tool('xvlog'), '--sv', '-d', define, '-i', folder] + files, folder, 'compile.log')
    (folder / 'elaborate.options').write_text('tb_arch03_linear16x4\n-generic_top ROW_LANES=%d\n-debug typical\n-s linear16\n' % args.rows)
    run([tool('xelab'), '-f', folder / 'elaborate.options'], folder, 'elaborate.log')
    (folder / 'run.tcl').write_text('run all\nquit\n', encoding='ascii')
    results = []
    sequence = np.array([row * 256 + tile * 16 + lane for tile in range(16)
                         for row in range(99) for lane in range(16)])
    for name in args.cases:
        task = folder / 'tile16' / name
        layout = json.loads((task / 'layout.json').read_text())
        second_name = 'layer_12' if name != 'layer_12' else 'layer_01'
        second = folder / 'tile16' / second_name
        second_layout = json.loads((second / 'layout.json').read_text())
        for prefetch in args.prefetch:
            tag = name + '_pf%d' % prefetch
            capture = folder / tag
            opts = folder / (tag + '.options')
            opts.write_text('linear16\n-tclbatch run.tcl\n-testplusarg DATA_DIR=%s\n-testplusarg OUTPUT_FILE=%s\n-testplusarg SHIFT=%d\n-testplusarg PREFETCH=%d\n-testplusarg JITTER=%d\n-testplusarg REPEATS=%d\n-testplusarg SECOND_DATA_DIR=%s\n-testplusarg SECOND_SHIFT=%d\n' % (
                task.as_posix(), capture.as_posix(), layout['shift'], prefetch, args.jitter, args.repeats,
                second.as_posix(), second_layout['shift']), encoding='ascii')
            text = run([tool('xsim'), '-f', opts], folder, tag + '.log')
            matches = re.findall(r'ICB32_RCORE_CORE_PASS task=(\d+) outputs=25344 cycles=(\d+) prefetch=(\d+) overlap=(\d+) stalls=(\d+)', text)
            if len(matches) != args.repeats or 'ICB32_RCORE_CORE_SUITE_PASS tasks=%d' % args.repeats not in text:
                raise ValueError('Missing DMA16 pass marker: ' + tag)
            if text.count('ICB32_RCORE_CANCEL_PASS phase=') != 5 or 'ICB32_RCORE_BAD_BIAS_PASS' not in text:
                raise ValueError('Missing cancel/error checks: ' + tag)
            if 'ICB32_RCORE_RESET_PASS' not in text or (prefetch and 'ICB32_RCORE_PREFETCH_CANCEL_PASS' not in text):
                raise ValueError('Missing reset/prefetch cancel checks: ' + tag)
            for task_run, cycles, pf, overlap, stalls in matches:
                actual_path = folder / (tag + '.' + task_run + '.csv')
                actual = np.loadtxt(str(actual_path), delimiter=',', dtype=np.int64, ndmin=2)
                if actual.shape != (25344, 4) or not np.array_equal(actual[:, 0], sequence):
                    raise ValueError('DMA16 output coordinate/order mismatch: ' + tag)
                ordered = actual[np.argsort(actual[:, 0])]
                reference_task = second if int(task_run) % 2 else task
                reference_name = second_name if int(task_run) % 2 else name
                with np.load(str(reference_task / 'expected.npz'), allow_pickle=False) as expected:
                    for col, key in enumerate(('total', 'result', 'saturated'), 1):
                        if not np.array_equal(ordered[:, col], expected[key].ravel()):
                            raise ValueError('DMA16 capture mismatch: ' + key)
                results.append(dict(case=reference_name, task=int(task_run), prefetch=int(pf), cycles=int(cycles),
                                    overlap=int(overlap), output_stalls=int(stalls), outputs=25344,
                                    capture=actual_path.name, capture_sha256=sha(actual_path),
                                    layout_sha256=sha(reference_task / 'layout.json')))
            print('PASS DMA16 core %s %s' % (args.backend, tag), flush=True)
    for path, digest in hashes.items():
        if sha(path) != digest:
            raise ValueError('Source changed during run: ' + path)
    summary = dict(status='passed', row_lanes=args.rows, cpu_executed=False, dma_executed=False, backend=args.backend,
                   jitter=args.jitter, tasks=len(results), outputs=25344 * len(results), cases=results,
                   cancel_phases=5, malformed_bias_recovery=True, consecutive_tasks=args.repeats,
                   source_sha256={Path(p).relative_to(ROOT).as_posix(): h for p, h in hashes.items()})
    (folder / 'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf8')
    print('LOCAL_LINEAR16X4_PASS ' + str(folder), flush=True)


if __name__ == '__main__':
    main()
