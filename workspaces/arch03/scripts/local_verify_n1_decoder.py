"""Standalone N1 decoder identity, narrow containers, cancellation and stalls."""
import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import struct

import n1_codec as codec
from local_verify import ROOT, A3, run, sha


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--vivado-bin', required=True, type=Path)
    ap.add_argument('--data', required=True, type=Path)
    args = ap.parse_args()
    out = ROOT/'local_runs'/('n1_decoder_'+datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    out.mkdir(parents=True)
    sources = [A3/'rtl/arch03_n1_decoder.sv', A3/'tb/tb_arch03_n1_decoder.sv']
    tracked = sources+[Path(__file__).resolve(), Path(codec.__file__)]
    hashes = {p: sha(p) for p in tracked}
    tool = lambda name: args.vivado_bin/(name+'.bat')
    run([tool('xvlog'), '--sv']+sources, out, 'compile.log')
    run([tool('xelab'), 'tb_arch03_n1_decoder', '-debug', 'typical', '-s', 'decoder'], out, 'elaborate.log')
    (out/'run.tcl').write_text('run all\nquit\n')
    cases = []
    for name in ('layer_01', 'extremes', 'rounding'):
        raw = (args.data/name/'load.bin').read_bytes()
        cases.append((name, raw, codec.encode(raw), 0))
    raw = (args.data/'extremes/load.bin').read_bytes()
    forced = codec.encode(raw, force_raw=True)
    cases.append(('forced_raw_extremes', raw, forced, 0))
    for name, offset, word in [('magic', 0, 0), ('legacy_layout', 8, 0x00100003),
                               ('numeric_identity', 28, 0), ('decoded_count', 20, 23487)]:
        bad = bytearray(forced)
        struct.pack_into('<I', bad, offset, word)
        cases.append(('bad_'+name, raw, bytes(bad), 2))
    # Raw wire order is W0/b0 -> X -> W1/b1... . All mutations preserve
    # length and 16-bit containers so rejection must come from numeric ABI.
    for name, offset, halfword, code in [
            ('w12_extension', 32, 0x0800, 8),
            ('x14_extension', 32+2144, 0x2000, 8),
            ('bias_negative_same_beat', 32+2048+4, 0x0000, 4),
            ('bias_positive_cross_beat', 32+2048+10, 0x00ff, 4),
            ('bias_reserved_padding', 32+2048+4, 0x01ff, 4)]:
        bad = bytearray(forced)
        struct.pack_into('<H', bad, offset, halfword)
        cases.append(('bad_'+name, raw, bytes(bad), code))
    compressed = codec.encode(raw)
    _, bias_offset = codec.base.decode_weight(compressed, 32)
    for name, offset, word in [('weight_mode', 32, 3),
            ('x_mode', bias_offset+96, 3), ('x_reserved', bias_offset+96, (1<<7)|(8<<2))]:
        bad = bytearray(compressed)
        struct.pack_into('<I', bad, offset, word)
        cases.append(('bad_'+name, raw, bytes(bad), 3))
    bad = bytearray(compressed[:-4])
    struct.pack_into('<I', bad, 16, len(bad))
    cases.append(('truncated_payload', raw, bytes(bad), 6))
    results = []
    for name, raw, encoded, error in cases:
        case = out/name
        case.mkdir()
        wire = codec.base.wire_raw(raw)
        if not error:
            assert codec.verify_coordinates(raw, codec.decode_wire(encoded))==23488
        (case/'load32.hex').write_text(''.join('%08x\n' % v[0] for v in struct.iter_unpack('<I', encoded)))
        (case/'raw16.hex').write_text(''.join('%04x\n' % v[0] for v in struct.iter_unpack('<H', wire)))
        opts = out/(name+'.options')
        opts.write_text('decoder\n-tclbatch run.tcl\n-testplusarg DATA=%s\n-testplusarg WORDS=%d\n-testplusarg BAD=%d\n' %
                        (case.as_posix(), len(encoded)//4, error))
        text = run([tool('xsim'), '-f', opts], out, name+'.log')
        expected = 'DECODER_ERROR_PASS code=%d' % error if error else 'DECODER_SUITE_PASS'
        if expected not in text:
            raise ValueError('Missing N1 decoder result: '+name)
        results.append(dict(case=name, expected_error=error, words=len(encoded)//4,
            encoded_sha256=hashlib.sha256(encoded).hexdigest(), log_sha256=sha(out/(name+'.log'))))
        print('PASS N1 decoder '+name, flush=True)
    if any(sha(path)!=digest for path,digest in hashes.items()):
        raise ValueError('Source changed during run')
    report = dict(status='passed', cpu_executed=False, dma_executed=False,
        scope='standalone_n1_decoder_no_e203_no_sram', numeric_format='0x000e0c20',
        cases=results, two_no_reset_tasks_per_good_case=True,
        long_output_backpressure_cycles=187, cancellation_and_restart=True,
        source_sha256={str(p): digest for p,digest in hashes.items()})
    (out/'summary.json').write_text(json.dumps(report, indent=2)+'\n')
    print('LOCAL_N1_DECODER_PASS '+str(out), flush=True)


if __name__ == '__main__':
    main()
