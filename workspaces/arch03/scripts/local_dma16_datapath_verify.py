"""Real DMA/linear16/shared-SRAM local regression; not E203 or ASIC timing."""
import argparse
import json
import re
from datetime import datetime
from pathlib import Path
import numpy as np
from local_verify import A2, A3, ROOT, run, sha


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--vivado-bin', required=True, type=Path)
    parser.add_argument('--data', required=True, type=Path)
    parser.add_argument('--cases', nargs='+', default=['layer_%02d' % x for x in range(1, 13)] + ['extremes', 'rounding'])
    parser.add_argument('--prefetch', type=int, nargs='+', choices=[0, 1], default=[0, 1])
    parser.add_argument('--jitter', type=int, choices=[0, 1], default=1)
    args = parser.parse_args()
    folder = ROOT / 'local_runs' / ('dma16_datapath_' + datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    folder.mkdir(parents=True)
    data = args.data.resolve()
    files = [A2 / 'rtl/requantize.sv', A2 / 'rtl/dot64.sv', A2 / 'arch02/rtl/sram_port.sv',
             A2 / 'arch02/rtl/sram_macro_adapter.sv', A2 / 'arch02/tb/pin_mock.sv',
             A3 / 'rtl/arch03_linear16.sv', A3 / 'rtl/arch03_dma16_accel.sv',
             A3 / 'rtl/arch03_icb_arb2.sv', A3 / 'rtl/arch03_icb_memory_router.sv',
             A3 / 'rtl/arch03_shared_sram.sv', A3 / 'tb/tb_arch03_dma16_datapath.sv']
    cfg_path = A2 / 'arch02/tb/pin_mock_config.json'
    cfg = json.loads(cfg_path.read_text())
    lines = []
    for size in ('128', '4096'):
        for key, width in [('cen_low', 1), ('gwen_low', 1), ('wen_low', 1), ('ema', 3), ('emaw', 2), ('ret1n', 1)]:
            lines.append("`define A02_%s_%s %d'd%d" % (size, key.upper(), width, cfg['macros'][size][key]))
    config = folder / 'arch02_sram_config.vh'
    config.write_text('\n'.join(lines) + '\n')
    before = {p: sha(p) for p in files + [cfg_path, config, Path(__file__).resolve()]}
    data_hashes = {}
    for name in args.cases:
        task = data / name
        layout = json.loads((task / 'layout_manifest.json').read_text())
        if layout['schema'] != 'kwt1-arch03-dma-tile16-q12-v1':
            raise ValueError('Unexpected DMA16 layout schema')
        for filename, digest in layout['sha256'].items():
            if sha(task / filename) != digest:
                raise ValueError('Vector hash mismatch: ' + str(task / filename))
        data_hashes[name] = sha(task / 'layout_manifest.json')
    tool = lambda name: args.vivado_bin / (name + '.bat')
    run([tool('xvlog'), '--sv', '-d', 'ARCH02_PIN_MOCK', '-i', folder] + files, folder, 'compile.log')
    run([tool('xelab'), 'tb_arch03_dma16_datapath', '-debug', 'typical', '-s', 'dma16_datapath'], folder, 'elaborate.log')
    (folder / 'run.tcl').write_text('run all\nquit\n')
    rows = []
    for name in args.cases:
        task = data / name
        layout = json.loads((task / 'layout_manifest.json').read_text())
        for pf in args.prefetch:
            tag = name + '_pf%d' % pf
            capture = folder / (tag + '.csv')
            options = folder / (tag + '.options')
            options.write_text('dma16_datapath\n-tclbatch run.tcl\n-testplusarg DATA_DIR=%s\n-testplusarg CAPTURE=%s\n-testplusarg SHIFT=%d\n-testplusarg PREFETCH=%d\n-testplusarg JITTER=%d\n' %
                               (task.as_posix(), capture.as_posix(), layout['numeric_format']['shift'], pf, args.jitter))
            text = run([tool('xsim'), '-f', options], folder, tag + '.log')
            matches = re.findall(r'ARCH03_DMA16_DATAPATH_PASS outputs=25344 cycles=(\d+) prefetch=(\d+) jitter=(\d+) overlap=(\d+) fifo_max=(\d+) saturated=(\d+) cpu_executed=false', text)
            if len(matches) != 1:
                raise ValueError('Missing unique DMA16 completion: ' + tag)
            if 'ARCH03_DMA16_RESTART_INVALIDATION_PASS no_reset=true held_request_drained=true' not in text:
                raise ValueError('Missing next-task invalidation/cancel probe: ' + tag)
            actual = np.loadtxt(str(capture), delimiter=',', dtype=np.int64, ndmin=2)
            if actual.shape != (25344, 2) or not np.array_equal(np.sort(actual[:, 0]), np.arange(25344)):
                raise ValueError('Incomplete output coordinates: ' + tag)
            ordered = actual[np.argsort(actual[:, 0])]
            with np.load(str(task / 'expected.npz'), allow_pickle=False) as expected:
                if not np.array_equal(ordered[:, 1], expected['result'].ravel()):
                    raise ValueError('Actual DMA writes differ from reference: ' + tag)
            cycles, pf_read, jitter, overlap, fifo_max, saturated = map(int, matches[0])
            rows.append(dict(case=name, cycles=cycles, prefetch=pf_read, jitter=jitter, overlap=overlap,
                             fifo_max=fifo_max, saturated=saturated, outputs=25344,
                             capture_sha256=sha(capture), layout_sha256=data_hashes[name]))
            print('PASS DMA16 datapath ' + tag + ' cycles=' + str(cycles), flush=True)
    for path, digest in before.items():
        if sha(path) != digest:
            raise ValueError('Source changed during run: ' + str(path))
    for name, digest in data_hashes.items():
        if sha(data / name / 'layout_manifest.json') != digest:
            raise ValueError('Vector layout changed during run')
    report = dict(status='passed', cpu_executed=False, backend='pin_mock', dma_executed=True,
                  scope='local_dma16_linear16_arbiter_router_shared_sram_no_e203', tasks=len(rows),
                  next_task_cache_invalidation_and_cancel=True,
                  outputs=len(rows)*25344, cases=rows,
                  source_sha256={p.relative_to(ROOT).as_posix(): h for p, h in before.items()})
    (folder / 'summary.json').write_text(json.dumps(report, indent=2) + '\n')
    print('LOCAL_DMA16_DATAPATH_PASS ' + str(folder), flush=True)


if __name__ == '__main__':
    main()
