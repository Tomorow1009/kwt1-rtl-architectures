"""Standalone B/v3 RTL decoder, real vectors and malformed streams. No CPU/PPA."""
import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path
import random
import struct
import systolic_b_codec as codec
from local_verify_icb32_decoder import ROOT, run


def directed_raw():
    rng = random.Random(20261111)
    values = []
    for row in range(99):
        w = row % 17
        if row < 34:
            base = -32768 if row < 17 else 32767 - ((1 << w) - 1)
            values += [base + rng.randrange(1 << w) for _ in range(64)]
        else:
            w = max(1, w)
            values += [rng.randrange(-(1 << (w - 1)), 1 << (w - 1)) for _ in range(64)]
    for tile in range(16):
        for k in range(64):
            for lane in range(16):
                width = (lane + 1) if tile % 3 == 0 else (k // 4 + 1) if tile % 3 == 1 else 16
                values.append(-(1 << (width - 1)) if (k + lane) % 2 else (1 << (width - 1)) - 1)
        for lane in range(16):
            values += [-32768 + lane, -1, 255]
    return b''.join(struct.pack('<H', v & 65535) for v in values)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--vivado-bin', type=Path, required=True)
    ap.add_argument('--data', type=Path, required=True)
    args = ap.parse_args()
    out = ROOT / 'local_runs' / ('systolic_b_decoder_' + datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    out.mkdir(parents=True)
    sources = [ROOT / 'workspaces/arch03/rtl/arch03_systolic_b_decoder.sv',
               ROOT / 'workspaces/arch03/tb/tb_arch03_systolic_b_decoder.sv']
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    tracked = sources + [Path(__file__).resolve(), Path(codec.__file__), Path(codec.v2.__file__)]
    hashes = {str(p.resolve()): sha(p) for p in tracked}
    tool = lambda name: args.vivado_bin / (name + '.bat')
    run([tool('xvlog'), '--sv'] + sources, out, 'compile.log')
    run([tool('xelab'), 'tb_arch03_systolic_b_decoder', '-debug', 'typical', '-s', 'decoder'], out, 'elaborate.log')
    (out / 'run.tcl').write_text('run all\nquit\n', encoding='ascii')
    cases = []
    for name in ['layer_%02d' % i for i in range(1, 13)] + ['extremes', 'rounding']:
        raw = struct.pack('<23488H', *[int(x, 16) for x in (args.data / name / 'load.hex').read_text().split()])
        cases.append((name, raw, codec.encode(raw), 0))
    raw = directed_raw()
    encoded = codec.encode(raw)
    cases += [('all_modes', raw, encoded, 0), ('forced_raw', raw, codec.encode(raw, True), 0)]
    for name, off, word, code in [('magic', 0, 0, 2), ('layout', 8, 0x100002, 2),
                                 ('w_mode', 32, 3, 3)]:
        bad = bytearray(encoded);struct.pack_into('<I', bad, off, word)
        cases.append(('bad_' + name, raw, bytes(bad), code))
    _, bias = codec.decode_weight(encoded, 32)
    bad = bytearray(encoded);bad[bias + 5] = 255
    cases.append(('bad_bias', raw, bytes(bad), 4))
    x_offset = bias + 96
    for name, word in [('x_width', 17 << 2), ('x_reserved', (1 << 7) | (8 << 2)), ('x_mode', 3)]:
        bad = bytearray(encoded);struct.pack_into('<I', bad, x_offset, word)
        cases.append(('bad_' + name, raw, bytes(bad), 3))
    # Inject overflow in first row, whose constant encoding normally has no payload.
    bad = bytearray(encoded[:x_offset] + struct.pack('<I', 1 | 4 | (32767 << 16)) + b'\xff' * 8 + encoded[x_offset + 4:])
    struct.pack_into('<I', bad, 16, len(bad))
    cases.append(('bad_delta_overflow', raw, bytes(bad), 7))
    # Whole-word truncation with a self-consistent length reaches RTL payload EOF.
    bad = bytearray(encoded[:-4]);struct.pack_into('<I', bad, 16, len(bad))
    cases.append(('truncated', raw, bytes(bad), 6))
    results = []
    for name, raw, encoded, error in cases:
        case = out / name;case.mkdir()
        wire = codec.wire_raw(raw)
        if not error:
            assert codec.verify_coordinates(raw, codec.decode_wire(encoded)) == 23488
        (case / 'load32.hex').write_text(''.join('%08x\n' % v[0] for v in struct.iter_unpack('<I', encoded)), encoding='ascii')
        (case / 'raw16.hex').write_text(''.join('%04x\n' % v[0] for v in struct.iter_unpack('<H', wire)), encoding='ascii')
        opts = out / (name + '.options')
        opts.write_text('decoder\n-tclbatch run.tcl\n-testplusarg DATA=%s\n-testplusarg WORDS=%d\n-testplusarg BAD=%d\n' %
                        (case.as_posix(), len(encoded) // 4, error), encoding='ascii')
        text = run([tool('xsim'), '-f', opts], out, name + '.log')
        expected = 'DECODER_ERROR_PASS code=%d' % error if error else 'DECODER_SUITE_PASS'
        if expected not in text or 'Fatal:' in text:
            raise ValueError('Missing B/v3 decoder pass: %s\n%s' % (name, text[-3000:]))
        results.append(dict(case=name, words=len(encoded) // 4, expected_error=error,
                            encoded_sha256=hashlib.sha256(encoded).hexdigest(), log_sha256=sha(out / (name + '.log'))))
        print('PASS B_V3_DECODER ' + name, flush=True)
    if any(sha(Path(p)) != h for p, h in hashes.items()):
        raise ValueError('Source changed during run')
    summary = dict(status='passed', cpu_executed=False, dma_executed=False, scope='standalone_b_v3_decoder',
                   two_no_reset_tasks_per_good_case=True, long_output_backpressure_cycles=187,
                   cancellation_and_restart=True, cases=results, source_sha256=hashes)
    (out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf8')
    print('LOCAL_B_V3_DECODER_PASS ' + str(out), flush=True)


if __name__ == '__main__':
    main()
