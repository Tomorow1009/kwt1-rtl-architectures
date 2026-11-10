"""Reproduce v2 byte/prefix budgets from frozen full-matrix captures.

Checks source hashes and losslessly round-trips every encoded task. Does not
run RTL or use Y_float as a runtime input. No TensorFlow dependency.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import time

import numpy as np
import numeric
import dma16_layout
import icb32_codec as codec


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def bound_file(root, name, expected):
    if Path(name).name != name:
        raise ValueError('Capture path must be a simple filename')
    path = root / name
    if sha(path) != expected:
        raise ValueError('Capture hash mismatch: ' + name)
    return path


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--captures', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    root, out = args.captures.resolve(), args.output.resolve()
    epath = root / 'evaluation.json'
    evaluation = json.loads(epath.read_text(encoding='utf-8-sig'))
    if sha(Path(numeric.__file__)) != evaluation['code_sha256']['numeric.py']:
        raise ValueError('Quantization implementation changed')
    bound_file(root, 'samples.json', evaluation['source_manifest_sha256'])
    ppath = bound_file(root, 'parameters.npz', evaluation['parameters_sha256'])
    with np.load(str(ppath), allow_pickle=False) as z:
        weights, wc = numeric.quantize(z['W'], 12, 16)
        biases, bc = numeric.quantize(z['b'], 24, 40)
    if weights.shape != (12, 64, 256) or biases.shape != (12, 256):
        raise ValueError('Parameter geometry')
    out.mkdir(parents=True, exist_ok=False)
    tasks, clipping, started = [], int(wc.sum() + bc.sum()), time.monotonic()
    captures = evaluation['sample_artifacts']
    if len(captures) != evaluation['samples'] or len({s['sample_id'] for s in captures}) != len(captures):
        raise ValueError('Capture coverage/identity')
    for index, sample in enumerate(captures):
        path = bound_file(root, sample['path'], sample['sha256'])
        with np.load(str(path), allow_pickle=False) as z:
            x, xc = numeric.quantize(z['X'], 12, 16)
        if x.shape != (12, 99, 64):
            raise ValueError('Input geometry')
        clipping += int(xc.sum())
        for layer in range(12):
            raw = dma16_layout.pack_tile16(x[layer], weights[layer], biases[layer])
            encoded = codec.encode(raw)
            decoded = codec.decode(encoded)
            if decoded != raw:
                raise ValueError('Lossless failure')
            # Independent original-coordinate map, not encoder traversal.
            dma16_layout.verify_coordinates(decoded, x[layer], weights[layer], biases[layer])
            info = codec.describe(encoded)
            prefix = info['prefix_bytes']
            n = info['transfer_transactions']
            tasks.append(dict(sample_id=sample['sample_id'], layer=layer + 1,
                              encoded_bytes=len(encoded), prefix_bytes=prefix,
                              transactions=n, raw=info['raw'],
                              ideal_pure_mac_lower_bound=max(n, prefix // 2 + 25600 + 24),
                              current_control_model_lower_bound=max(n, prefix // 2 + 27200 + 24),
                              encoded_sha256=info['sha256']))
        if (index + 1) % 25 == 0 or index == 0:
            print('COMPRESSION_CHECK samples=%d tasks=%d seconds=%.2f' %
                  (index + 1, len(tasks), time.monotonic() - started), flush=True)
    if len(tasks) != evaluation['task_count']:
        raise ValueError('Task coverage')
    metrics = {}
    for field in ('encoded_bytes', 'prefix_bytes', 'transactions',
                  'ideal_pure_mac_lower_bound', 'current_control_model_lower_bound'):
        values = [t[field] for t in tasks]
        metrics[field] = dict(min=min(values), mean=sum(values) / len(values), max=max(values))
    result = dict(schema='arch03-icb32-compression-review-v1', samples=len(captures),
                  tasks=len(tasks), scope='internal_development_captures',
                  software_lossless_verified=True,
                  coordinate_checks=len(tasks) * (6336 + 16384 + 256),
                  roundtrip_halfwords=len(tasks) * 23488,
                  rtl_verified=False, cpu_executed=False, official_precision_verified=False,
                  hardware_100_sample_set_verified=False, clipping=clipping,
                  metrics=metrics, raw_fallback_tasks=sum(t['raw'] for t in tasks),
                  ideal_transfer_under_30000=sum(t['transactions'] <= 30000 for t in tasks),
                  elapsed_seconds=time.monotonic() - started,
                  evaluation_sha256=sha(epath), parameters_sha256=sha(ppath),
                  sample_hash_chain=hashlib.sha256(''.join(s['sha256'] for s in captures).encode()).hexdigest(),
                  code_sha256={p.name: sha(p) for p in [Path(__file__), Path(codec.__file__),
                                                       Path(numeric.__file__), Path(dma16_layout.__file__)]})
    csvpath = out / 'tasks.csv'
    with csvpath.open('w', newline='', encoding='utf8') as f:
        writer = csv.DictWriter(f, fieldnames=list(tasks[0]))
        writer.writeheader()
        writer.writerows(tasks)
    result['tasks_csv_sha256'] = sha(csvpath)
    (out / 'summary.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n', encoding='utf8')
    print(json.dumps(result, sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
