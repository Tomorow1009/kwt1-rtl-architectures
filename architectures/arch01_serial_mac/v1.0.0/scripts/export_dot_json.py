"""Export one already-extracted floating-point dot product. Standard library only.

Input JSON: {"x": [64 floats], "w": [64 floats], "bias": float, "shift": 12}
This is NOT a KWT checkpoint/intermediate-tensor extraction tool.
"""
import argparse
import json
import math
from pathlib import Path
from gen_vectors import reference


def quantize(value, frac, bits):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError('Numeric finite values required')
    if not math.isfinite(value):
        raise ValueError('NaN/Inf are not supported')
    # Integer arithmetic on the exact supplied binary float avoids half-boundary
    # errors caused by adding 0.5 to a nearly-half floating-point value.
    n, d = value.as_integer_ratio()
    q, rem = divmod(abs(n) * (1 << frac), d)
    if 2 * rem >= d:
        q += 1
    rounded = -q if n < 0 else q
    clipped = max(-(1 << (bits-1)), min((1 << (bits-1))-1, rounded))
    return clipped, clipped != rounded


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    data = json.loads(args.input.read_text(encoding='utf-8-sig'))
    for key in ('x', 'w'):
        if not isinstance(data[key], list) or len(data[key]) != 64:
            raise ValueError(f'{key} must contain exactly 64 numbers')
    shift = data.get('shift', 12)
    if type(shift) is not int or not 0 <= shift <= 31:
        raise ValueError('shift must be an integer in [0,31]')
    xq = [quantize(v,12,16) for v in data['x']]
    wq = [quantize(v,12,16) for v in data['w']]
    bias, bias_clipped = quantize(data['bias'],24,40)
    xs, ws = [v[0] for v in xq], [v[0] for v in wq]
    total, result, saturated = reference(xs,ws,bias,shift)
    args.output.mkdir(parents=True,exist_ok=True)
    for name, values, bits in [('x',xs,16),('w',ws,16),('bias',[bias],40),
            ('shift',[shift],5),('total',[total],41),('result',[result],16),
            ('saturated',[saturated],1)]:
        (args.output/f'{name}.hex').write_text(''.join(
            f'{v & ((1 << bits)-1):0{(bits+3)//4}X}\n' for v in values),encoding='ascii')
    floating_dot = math.fsum(float(x)*float(w) for x,w in zip(data['x'],data['w'])) + float(data['bias'])
    report = dict(input=str(args.input.resolve()), count=64, x_fraction_bits=12,
        w_fraction_bits=12, bias_fraction_bits=24, shift=shift,
        x_clipped=sum(v[1] for v in xq), w_clipped=sum(v[1] for v in wq),
        bias_clipped=bias_clipped, total_integer=total, result_integer=result,
        saturated=saturated, decoded_result=result*2.0**(shift-24),
        floating_dot_python=floating_dot,
        note='floating_dot_python is not the captured TensorFlow float32 output')
    (args.output/'metadata.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    main()
