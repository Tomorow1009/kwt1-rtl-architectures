"""Standalone RTL decoder tests; not DMA/ASIC CPU/PPA acceptance."""
import argparse
import hashlib
import json
from pathlib import Path
import random
import struct
import subprocess

import icb32_codec as codec

ROOT = Path(__file__).resolve().parents[3]


def run(command, root, log):
    with (root / log).open('w', encoding='utf8') as f:
        result = subprocess.run([str(c) for c in command], cwd=str(root), stdout=f, stderr=subprocess.STDOUT)
    text = (root / log).read_text(encoding='utf8', errors='replace')
    if result.returncode:
        raise RuntimeError('Command failed: %s\n%s' % (log, text[-4000:]))
    return text


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--vivado-bin', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    out = args.output.resolve();out.mkdir(parents=True, exist_ok=False)
    sources = [ROOT / 'workspaces/arch03/rtl/arch03_icb32_decoder.sv',
               ROOT / 'workspaces/arch03/tb/tb_arch03_icb32_decoder.sv']
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    tracked = sources + [Path(__file__), Path(codec.__file__)]
    hashes = {str(p.resolve()): sha(p) for p in tracked}
    tool = lambda name: args.vivado_bin / (name + '.bat')
    run([tool('xvlog'), '--sv'] + sources, out, 'compile.log')
    run([tool('xelab'), 'tb_arch03_icb32_decoder', '-debug', 'typical', '-s', 'decoder'], out, 'elaborate.log')
    (out / 'run.tcl').write_text('run all\nquit\n', encoding='ascii')
    rng = random.Random(20261110)
    cases = []
    for width in range(1, 17):
        values = [rng.randrange(-(1 << (width - 1)), 1 << (width - 1)) for _ in range(23488)]
        for tile in range(16):
            for lane in range(16):
                i = 6336 + tile * 1072 + 1024 + lane * 3
                values[i:i + 3] = [-32768, -1, 255]
        raw = b''.join(struct.pack('<H', v & 65535) for v in values)
        encoded = codec.encode(raw)
        cases.append(('width%02d' % width, raw, encoded, 0))
    raw, encoded = cases[7][1:3]
    cases.append(('forced_raw', raw, codec.encode(raw, force_raw=True), 0))
    for name, offset, value, error in [('bad_magic', 0, 0, 2), ('bad_layout', 8, 1, 2),
                                       ('bad_width', 32, 0, 3), ('bad_count', 32, 8, 3)]:
        changed = bytearray(encoded);struct.pack_into('<I', changed, offset, value)
        cases.append((name, raw, bytes(changed), error))
    results = []
    for name, raw, encoded, error in cases:
        case = out / name;case.mkdir()
        (case / 'load32.hex').write_text(''.join('%08x\n' % v[0] for v in struct.iter_unpack('<I', encoded)), encoding='ascii')
        (case / 'raw16.hex').write_text(''.join('%04x\n' % v[0] for v in struct.iter_unpack('<H', raw)), encoding='ascii')
        opts = out / (name + '.options')
        opts.write_text('decoder\n-tclbatch run.tcl\n-testplusarg DATA=%s\n-testplusarg WORDS=%d\n-testplusarg BAD=%d\n' %
                        (case.as_posix(), len(encoded) // 4, error), encoding='ascii')
        text = run([tool('xsim'), '-f', opts], out, name + '.log')
        expected = 'DECODER_ERROR_PASS code=%d' % error if error else 'DECODER_SUITE_PASS'
        if expected not in text or 'Fatal:' in text:
            raise ValueError('Missing RTL decoder pass: %s\n%s' % (name, text[-2000:]))
        results.append(dict(case=name, words=len(encoded) // 4, expected_error=error,
                            encoded_sha256=hashlib.sha256(encoded).hexdigest(), log_sha256=sha(out / (name + '.log'))))
        print('PASS DECODER ' + name, flush=True)
    if any(sha(Path(p)) != h for p, h in hashes.items()):
        raise ValueError('Source changed during run')
    summary = dict(status='passed', cpu_executed=False, dma_executed=False, scope='standalone_decoder',
                   cases=results, source_sha256=hashes)
    (out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf8')
    print('LOCAL_DECODER_PASS ' + str(out), flush=True)


if __name__ == '__main__':
    main()
