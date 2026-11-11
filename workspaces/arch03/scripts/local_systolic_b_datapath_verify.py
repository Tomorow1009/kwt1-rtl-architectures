"""Systolic B/v2 compressed DMA/shared-SRAM local regression; not E203 or ASIC timing."""
import argparse
import json
import re
import struct
from icb32_codec import encode, decode, describe
from datetime import datetime
from pathlib import Path
import numpy as np
from local_verify import A2, A3, ROOT, run, sha


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--vivado-bin', required=True, type=Path)
    parser.set_defaults(rows=5)
    parser.add_argument('--raw', action='store_true')
    parser.add_argument('--data', required=True, type=Path)
    parser.add_argument('--cases', nargs='+', default=['layer_%02d' % x for x in range(1, 13)] + ['extremes', 'rounding'])
    parser.add_argument('--prefetch', type=int, nargs='+', choices=[0, 1], default=[0, 1])
    parser.add_argument('--jitter', type=int, choices=[0, 1], default=1)
    args = parser.parse_args()
    folder = ROOT / 'local_runs' / ('systolic_b_datapath_' + datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    folder.mkdir(parents=True)
    data = args.data.resolve()
    files = [A2 / 'rtl/requantize.sv', A2 / 'arch02/rtl/sram_port.sv',
             A2 / 'arch02/rtl/sram_macro_adapter.sv', A2 / 'arch02/tb/pin_mock.sv',
             A3 / 'rtl/arch03_systolic5x16.sv', A3 / 'rtl/arch03_linear16x5_systolic.sv', A3 / 'rtl/arch03_systolic_b_accel.sv',
             A3 / 'rtl/arch03_icb32_decoder.sv', A3 / 'rtl/arch03_icb32_transport.sv',
             A3 / 'rtl/arch03_icb_arb2_turnover.sv', A3 / 'rtl/arch03_icb_memory_router_turnover.sv',
             A3 / 'rtl/arch03_shared_sram_turnover.sv', A3 / 'tb/tb_arch03_systolic_b_datapath.sv']
    cfg_path = A2 / 'arch02/tb/pin_mock_config.json'
    cfg = json.loads(cfg_path.read_text())
    lines = []
    for size in ('128', '4096'):
        for key, width in [('cen_low', 1), ('gwen_low', 1), ('wen_low', 1), ('ema', 3), ('emaw', 2), ('ret1n', 1)]:
            lines.append("`define A02_%s_%s %d'd%d" % (size, key.upper(), width, cfg['macros'][size][key]))
    config = folder / 'arch02_sram_config.vh'
    config.write_text('\n'.join(lines) + '\n')
    before = {p: sha(p) for p in files + [cfg_path, config, Path(__file__).resolve(), A3 / 'scripts/icb32_codec.py']}
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
    (folder / 'elaborate.options').write_text('tb_arch03_systolic_b_datapath\n-debug typical\n-s icb32_datapath\n')
    run([tool('xelab'), '-f', folder / 'elaborate.options'], folder, 'elaborate.log')
    (folder / 'run.tcl').write_text('run all\nquit\n')
    rows = []
    for name in args.cases:
        task = data / name
        layout = json.loads((task / 'layout_manifest.json').read_text())
        raw = struct.pack('<23488H', *[int(x,16) for x in (task / 'load.hex').read_text().split()])
        encoded = encode(raw, force_raw=args.raw)
        if decode(encoded) != raw: raise ValueError('Codec mismatch')
        encoded_path = folder / (name + '_encoded.hex')
        encoded_path.write_text(''.join('%08x\n' % v[0] for v in struct.iter_unpack('<I', encoded)))
        for pf in args.prefetch:
            tag = name + '_pf%d' % pf
            capture = folder / (tag + '.csv')
            options = folder / (tag + '.options')
            options.write_text('icb32_datapath\n-tclbatch run.tcl\n-testplusarg DATA_DIR=%s\n-testplusarg CAPTURE=%s\n-testplusarg SHIFT=%d\n-testplusarg PREFETCH=%d\n-testplusarg JITTER=%d\n-testplusarg ENCODED_FILE=%s\n-testplusarg ENCODED_BYTES=%d\n' %
                               (task.as_posix(), capture.as_posix(), layout['numeric_format']['shift'], pf, args.jitter, encoded_path.as_posix(), len(encoded)))
            text = run([tool('xsim'), '-f', options], folder, tag + '.log')
            matches = re.findall(r'ARCH03_SYSTOLIC_B_DATAPATH_PASS outputs=25344 cycles=(\d+) prefetch=(\d+) jitter=(\d+) overlap=(\d+) fifo_max=(\d+) saturated=(\d+) cpu_executed=false', text)
            if len(matches) != 1:
                raise ValueError('Missing unique DMA16 completion: ' + tag)
            if 'ARCH03_SYSTOLIC_B_RESTART_INVALIDATION_PASS no_reset=true held_request_drained=true' not in text:
                raise ValueError('Missing next-task invalidation/cancel probe: ' + tag)
            actual = np.loadtxt(str(capture), delimiter=',', dtype=np.int64, ndmin=2)
            if actual.shape != (25344, 2) or not np.array_equal(np.sort(actual[:, 0]), np.arange(25344)):
                raise ValueError('Incomplete output coordinates: ' + tag)
            ordered = actual[np.argsort(actual[:, 0])]
            with np.load(str(task / 'expected.npz'), allow_pickle=False) as expected:
                if not np.array_equal(ordered[:, 1], expected['result'].ravel()):
                    raise ValueError('Actual DMA writes differ from reference: ' + tag)
            cycles, pf_read, jitter, overlap, fifo_max, saturated = map(int, matches[0])
            metrics = re.findall(r'ICB32_TASK_METRICS bytes=(\d+) turns=(\d+) rows=(\d+)', text)
            if len(metrics)!=1 or int(metrics[0][0])!=len(encoded) or int(metrics[0][2])!=args.rows: raise ValueError('Missing transport metrics')
            rows.append(dict(transactions=len(encoded)//2+12672, turnovers=int(metrics[0][1]), row_lanes=args.rows, encoded_bytes=len(encoded), raw_fallback=describe(encoded)['raw'], encoded_sha256=sha(encoded_path), case=name, cycles=cycles, prefetch=pf_read, jitter=jitter, overlap=overlap,
                             fifo_max=fifo_max, saturated=saturated, outputs=25344,
                             capture_sha256=sha(capture), layout_sha256=data_hashes[name]))
            print('PASS ICB32 datapath ' + tag + ' cycles=' + str(cycles), flush=True)
    for path, digest in before.items():
        if sha(path) != digest:
            raise ValueError('Source changed during run: ' + str(path))
    for name, digest in data_hashes.items():
        if sha(data / name / 'layout_manifest.json') != digest:
            raise ValueError('Vector layout changed during run')
    report = dict(status='passed', cpu_executed=False, backend='pin_mock', dma_executed=True,
                  scope='local_systolic_b_v2_transport_decoder_turnover_shared_sram_no_e203', tasks=len(rows),
                  next_task_cache_invalidation_and_cancel=True,
                  outputs=len(rows)*25344, cases=rows,
                  source_sha256={p.relative_to(ROOT).as_posix(): h for p, h in before.items()})
    (folder / 'summary.json').write_text(json.dumps(report, indent=2) + '\n')
    print('LOCAL_SYSTOLIC_B_DATAPATH_PASS ' + str(folder), flush=True)


if __name__ == '__main__':
    main()
