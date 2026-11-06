"""Deterministic, arbitrary-precision integer oracle. No third-party packages."""
from pathlib import Path
import json
import random

ROOT = Path(__file__).resolve().parents[1]

def reference(xs, ws, bias, shift):
    total = sum(x*w for x, w in zip(xs, ws)) + bias
    q, r = divmod(abs(total), 2**shift)
    if shift and r >= 2**(shift-1):
        q += 1
    rounded = -q if total < 0 else q
    return total, max(-32768, min(32767, rounded)), int(not -32768 <= rounded <= 32767)

def main():
    cases = []
    def add(name, xs=None, ws=None, bias=0, shift=12):
        xs = [0]*64 if xs is None else xs
        ws = [0]*64 if ws is None else ws
        assert len(xs) == len(ws) == 64
        assert all(-32768 <= v <= 32767 for v in xs + ws)
        assert -(1<<39) <= bias < (1<<39) and 0 <= shift <= 31
        total, result, sat = reference(xs, ws, bias, shift)
        cases.append(dict(name=name, x=xs, w=ws, bias=bias, shift=shift,
                          total=total, result=result, saturated=sat))
    add('zero')
    add('zero_weights', [32767]*64)
    add('zero_inputs', ws=[-32768]*64)
    for a,b in ((4096,64),(-4096,64),(4096,-64),(-4096,-64)):
        add(f'signs_{a}_{b}', [a]*64, [b]*64)
    add('min_times_min', [-32768]*64, [-32768]*64, shift=31)
    add('max_times_max', [32767]*64, [32767]*64, shift=31)
    add('min_times_max', [-32768]*64, [32767]*64, shift=31)
    add('cancel', [32767]*64, [32767]*32+[-32767]*32, bias=-4096)
    add('positive_saturation', [-32768]*64, [-32768]*64, shift=0)
    add('negative_saturation', [-32768]*64, [32767]*64, shift=0)
    add('bias_max_plus_dot', [-32768]*64, [-32768]*64, bias=(1<<39)-1)
    add('bias_min_plus_dot', [-32768]*64, [32767]*64, bias=-(1<<39))
    for s in range(32):
        for q in (-32769,-32768,-1,0,1,32767,32768):
            b = q * 2**s
            if -(1<<39) <= b < (1<<39):
                add(f'exact_s{s}_q{q}', bias=b, shift=s)
        if s:
            for q in (0,1,32767,32768):
                for delta in (-1,0,1):
                    for sign in (-1,1):
                        b = sign*(q*2**s+2**(s-1)+delta)
                        if -(1<<39) <= b < (1<<39):
                            add(f'round_s{s}_q{q}_d{delta}_sign{sign}', bias=b, shift=s)
    rng = random.Random(20261106)
    for i in range(240):
        limit = 255 if i % 2 else 32767
        add(f'random_{i}', [rng.randint(-limit-1,limit) for _ in range(64)],
            [rng.randint(-limit-1,limit) for _ in range(64)],
            bias=rng.randint(-(1<<35),(1<<35)-1), shift=rng.randrange(32))
    out = ROOT/'vectors'
    out.mkdir(exist_ok=True)
    for key,bits in [('x',16),('w',16),('bias',40),('shift',5),('total',41),('result',16),('saturated',1)]:
        values = [v for c in cases for v in (c[key] if isinstance(c[key],list) else [c[key]])]
        (out/f'{key}.hex').write_text(''.join(f'{v & ((1<<bits)-1):0{(bits+3)//4}X}\n' for v in values))
    (out/'cases.vh').write_text(f'localparam CASES = {len(cases)};\n')
    (out/'manifest.json').write_text(json.dumps(cases,indent=2))
    (out/'case_names.txt').write_text(''.join(f'{i}: {c["name"]}\n' for i,c in enumerate(cases)))
    print(f'Generated {len(cases)} cases, including 240 random cases')

if __name__ == '__main__':
    main()
