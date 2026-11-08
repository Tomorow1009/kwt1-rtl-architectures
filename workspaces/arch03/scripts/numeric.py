"""Arch02/03 fixed-point codec and integer oracle; no TensorFlow dependency.

The runtime input contains X/W/b only. Expected outputs are verification artifacts.
See ../NUMERIC_FORMAT.md for the wire protocol and quantization contract.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np

SHAPES = {'X': (99, 64), 'W': (64, 256), 'b': (256,)}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def numeric_format(shift=12):
    if type(shift) is not int or not 0 <= shift <= 31:
        raise ValueError('shift must be an integer in 0..31')
    return dict(x_bits=16, w_bits=16, bias_bits=40, accumulator_bits=40,
                sum_bits=41, output_bits=16, x_fraction_bits=12,
                w_fraction_bits=12, bias_fraction_bits=24, shift=shift,
                output_fraction_bits=24-shift, rounding='nearest_ties_away_from_zero',
                overflow='saturate', byte_order='little')


def validate_format(config):
    if config != numeric_format(config.get('shift')):
        raise ValueError('Inconsistent numeric format/scale')
    return config


def quantize(values, fraction, bits):
    values = np.asarray(values)
    if values.dtype.kind not in 'fiu' or not np.isfinite(values).all():
        raise ValueError('Expected finite real inputs')
    # Clip before scaling so even finite float64 extremes cannot overflow.
    lo, hi = -(1 << (bits-1)), (1 << (bits-1))-1
    scale = float(2**fraction)
    bounded = np.clip(values.astype(np.float64), (lo-1)/scale, (hi+1)/scale)
    scaled = bounded * scale
    frac, whole = np.modf(np.abs(scaled))
    rounded = np.copysign(whole + (frac >= .5), scaled)
    clipped = (rounded < lo) | (rounded > hi)
    return np.clip(rounded, lo, hi).astype(np.int64), clipped


def signed_array(value, shape, bits, name):
    a = np.asarray(value)
    if a.shape != shape or a.dtype.kind not in 'iu':
        raise ValueError('Invalid shape/integer type: '+name)
    if np.any(a < -(1 << (bits-1))) or np.any(a > (1 << (bits-1))-1):
        raise ValueError('Integer out of range: '+name)
    return a.astype(np.int64)


def integer_model(x, w, b, shift=12):
    numeric_format(shift)
    x = signed_array(x, SHAPES['X'], 16, 'X')
    w = signed_array(w, SHAPES['W'], 16, 'W')
    b = signed_array(b, SHAPES['b'], 40, 'b')
    # 64 signed 16x16 products fit in signed 38 bits, so the RTL's
    # signed 40-bit accumulator never wraps for any legal input.
    total = x @ w + b
    magnitude = np.abs(total)
    rounded = (magnitude + (1 << (shift-1))) >> shift if shift else magnitude
    rounded = np.where(total < 0, -rounded, rounded)
    result = np.clip(rounded, -32768, 32767)
    return dict(total=total, result=result, saturated=(result != rounded).astype(np.int64))


def encode_arrays(x, w, b, shift=12):
    numeric_format(shift)
    quantized, clipped = {}, {}
    for key, a, bits, frac in [('X', x, 16, 12), ('W', w, 16, 12), ('b', b, 40, 24)]:
        if np.asarray(a).shape != SHAPES[key]:
            raise ValueError('Invalid full matrix shape: '+key)
        quantized[key], flags = quantize(a, frac, bits)
        clipped[key] = int(flags.sum())
    return quantized, integer_model(quantized['X'], quantized['W'], quantized['b'], shift), clipped


def pack_words(x, w, b):
    x = signed_array(x, SHAPES['X'], 16, 'X')
    w = signed_array(w, SHAPES['W'], 16, 'W')
    b = signed_array(b, SHAPES['b'], 40, 'b')
    words = [int(v) & 65535 for v in x.flat]
    for group in range(32):
        words.extend(int(w[k, group*8+lane]) & 65535 for k in range(64) for lane in range(8))
        for lane in range(8):
            bias = int(b[group*8+lane]) & ((1 << 40)-1)
            words.extend((bias >> bit) & 65535 for bit in (0, 16, 32))
    return np.asarray(words, dtype='<u2')


def unpack_words(words):
    a = np.asarray(words)
    if a.shape != (23488,) or a.dtype.kind not in 'iu' or np.any(a < 0) or np.any(a > 65535):
        raise ValueError('Expected 23488 unsigned 16-bit load words')
    a = a.astype(np.int64)
    signed = lambda v: np.where(v >= 32768, v-65536, v)
    x = signed(a[:6336]).reshape(99, 64)
    w, b = np.empty((64, 256), dtype=np.int64), np.empty(256, dtype=np.int64)
    for group in range(32):
        block = a[6336+536*group:6336+536*(group+1)]
        w[:, group*8:group*8+8] = signed(block[:512]).reshape(64, 8)
        pieces = block[512:].reshape(8, 3)
        if np.any(pieces[:, 2] > 255):
            raise ValueError('Bias high padding must be zero')
        bias = pieces[:, 0] | (pieces[:, 1] << 16) | (pieces[:, 2] << 32)
        b[group*8:group*8+8] = np.where(bias >= (1 << 39), bias-(1 << 40), bias)
    return dict(X=x, W=w, b=b)


def decode(values, config):
    validate_format(config)
    a = np.asarray(values)
    if a.dtype.kind not in 'iu' or np.any(a < -32768) or np.any(a > 32767):
        raise ValueError('Invalid signed int16 output')
    result = np.ldexp(a.astype(np.float64), config['shift']-24)
    if not np.isfinite(result).all():
        raise ValueError('Non-finite decoded output')
    return result


def read_capture(path):
    # Parse integer strings strictly: numpy's float-to-int fallback can truncate
    # malformed CSV values such as 1.5 on some supported numpy versions.
    rows = []
    for line in Path(path).read_text(encoding='ascii').splitlines():
        parts = line.split(',')
        if len(parts) not in (2, 3) or any(not p.strip().lstrip('+-').isdigit() for p in parts):
            raise ValueError('Invalid integer capture row')
        rows.append([int(p) for p in parts])
    if not rows or len({len(r) for r in rows}) != 1:
        raise ValueError('Invalid capture columns')
    a = np.asarray(rows, dtype=np.int64)
    if a.shape[0] != 25344 or not np.array_equal(np.sort(a[:, 0]), np.arange(25344)):
        raise ValueError('Missing/duplicate/non-matrix capture')
    a = a[np.argsort(a[:, 0])]
    values = signed_array(a[:, 1], (25344,), 16, 'capture')
    if a.shape[1] == 3 and np.any((a[:, 2] != 0) & (a[:, 2] != 1)):
        raise ValueError('Invalid capture saturation flag')
    return values.reshape(99, 256), a[:, 2].reshape(99, 256) if a.shape[1] == 3 else None


def error_metrics(values, reference):
    values, reference = np.asarray(values, dtype=np.float64), np.asarray(reference, dtype=np.float64)
    if values.shape != (99, 256) or reference.shape != values.shape or not np.isfinite(reference).all() or not np.isfinite(values).all():
        raise ValueError('Invalid finite full matrix reference/output')
    with np.errstate(over='ignore', invalid='ignore'):
        delta = values-reference
        sse, energy = float(np.sum(delta*delta)), float(np.sum(reference*reference))
    if not np.isfinite([sse, energy]).all():
        raise ValueError('Non-finite metric energy')
    count = reference.size
    nrmse = (sse/count)**.5 / max((energy/count)**.5, 1e-8)
    return dict(sse=sse, reference_energy=energy, outputs=count, nrmse=nrmse,
                max_absolute_error=float(np.max(np.abs(delta))), threshold_passed=nrmse <= .03)


def aggregate_tasks(tasks):
    if not tasks:
        raise ValueError('No tasks')
    seen, sums = set(), {i: [0., 0., 0] for i in range(1, 13)}
    for t in tasks:
        key = (t['sample_id'], t['layer'])
        if not isinstance(key[0], str) or not key[0] or type(key[1]) is not int or key[1] not in sums or key in seen:
            raise ValueError('Duplicate/invalid sample-layer')
        seen.add(key)
        for i, k in enumerate(('sse', 'reference_energy', 'outputs')):
            sums[t['layer']][i] += t[k]
    samples = {s for s, _ in seen}
    if seen != {(s, l) for s in samples for l in range(1, 13)}:
        raise ValueError('Each sample must cover all 12 layers')
    layers = []
    for layer, (sse, energy, count) in sums.items():
        ratio = (sse/count)**.5 / max((energy/count)**.5, 1e-8)
        if not np.isfinite(ratio):
            raise ValueError('Non-finite aggregate')
        layers.append(dict(layer=layer, outputs=count, sse=sse, reference_energy=energy, nrmse=ratio))
    maximum = max(t['nrmse'] for t in layers)
    worst = max(tasks, key=lambda t: t['nrmse'])
    failing = [dict(sample_id=t['sample_id'], layer=t['layer'], nrmse=t['nrmse']) for t in tasks if not t['threshold_passed']]
    return dict(samples=len(samples), task_count=len(tasks), layers=layers,
                max_layer_nrmse=maximum, max_task_nrmse=worst['nrmse'],
                worst_task=dict(sample_id=worst['sample_id'], layer=worst['layer']),
                layer_threshold_passed=maximum <= .03, task_threshold_passed=not failing,
                threshold_passed=maximum <= .03 and not failing, failing_tasks=failing)


def export_task(source, output, layer, shift=12, sample_id='external'):
    if type(layer) is not int or not 1 <= layer <= 12:
        raise ValueError('layer must be 1..12')
    output = Path(output)
    if output.exists():
        raise ValueError('Output directory already exists')
    with np.load(str(source), allow_pickle=False) as z:
        q, expected, clipped = encode_arrays(z['X'], z['W'], z['b'], shift)
    words = pack_words(q['X'], q['W'], q['b'])
    decoded = unpack_words(words)
    for key in q:
        if not np.array_equal(decoded[key], q[key]):
            raise ValueError('Codec roundtrip mismatch')
    # Reuse the existing fixture format for local ICB and CPU preparation.
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]/'arch02/arch02/scripts'))
    from data import export
    export(output, q['X'], q['W'], q['b'], expected, shift)
    (output/'load.bin').write_bytes(words.tobytes())
    np.savez_compressed(str(output/'input_integer.npz'), **q)
    config = dict(schema_version=1, sample_id=sample_id, layer=layer, numeric_format=numeric_format(shift),
                  clipped=clipped, source_sha256=sha(source), input_load_words=23488,
                  runtime_inputs=['load.bin', 'load.hex'],
                  verification_only=['total.hex', 'result.hex', 'saturated.hex', 'expected.npz'],
                  sha256={p.name: sha(p) for p in output.iterdir() if p.is_file()})
    (output/'codec.json').write_text(json.dumps(config, indent=2), encoding='utf8')
    return config


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    e = sub.add_parser('encode'); e.add_argument('npz', type=Path); e.add_argument('--output', type=Path, required=True)
    e.add_argument('--layer', type=int, required=True); e.add_argument('--shift', type=int, default=12)
    e.add_argument('--sample-id', default='external')
    d = sub.add_parser('decode'); d.add_argument('capture', type=Path); d.add_argument('--codec', type=Path, required=True)
    d.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    if a.command == 'encode':
        export_task(a.npz, a.output, a.layer, a.shift, a.sample_id)
    else:
        if a.output.exists():
            raise ValueError('Output already exists')
        config = json.loads(a.codec.read_text(encoding='utf8'))
        values, sat = read_capture(a.capture)
        decoded = decode(values, config['numeric_format'])
        np.savez_compressed(str(a.output), Y_decoded=decoded, result_int=values,
                            **({'saturated': sat} if sat is not None else {}))
        a.output.with_suffix('.json').write_text(json.dumps(dict(capture_sha256=sha(a.capture),
            codec_sha256=sha(a.codec), decoded_sha256=sha(a.output), layer=config['layer'],
            sample_id=config['sample_id'], numeric_format=config['numeric_format'], all_finite=True), indent=2), encoding='utf8')


if __name__ == '__main__':
    main()
