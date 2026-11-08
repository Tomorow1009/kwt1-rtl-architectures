"""Recheck frozen full-matrix evidence and select inputs for real RTL runs.

Does not fabricate captures or count software outputs as RTL acceptance.
"""
import argparse
import json
from pathlib import Path
import sys
import numpy as np
from numeric import (aggregate_tasks, decode, encode_arrays, error_metrics, export_task,
                     integer_model, numeric_format, sha)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('evaluation', type=Path)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    root = a.evaluation.parent
    report = json.loads(a.evaluation.read_text())
    if a.output.exists():
        p.error('Use a new output directory')
    for name, key in [('samples.json', 'source_manifest_sha256'), ('parameters.npz', 'parameters_sha256'), ('environment.json', 'environment_sha256')]:
        if sha(root/name) != report[key]:
            raise ValueError('Changed evaluation input: '+name)
    validate = json.loads((root/'samples.json').read_text())
    if len({s['sample_id'] for s in validate['samples']}) != 600 or not report['full_600_coverage']:
        raise ValueError('Expected full development corpus')
    with np.load(str(root/'parameters.npz'), allow_pickle=False) as z:
        weights, biases = z['W'], z['b']
    recomputed = []
    # Independent legacy implementation cross-check, retained unchanged from
    # the previously verified arch02 path, in addition to the new integer model.
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]/'arch02/arch02/scripts'))
    from data import reference, export
    for sample in report['sample_artifacts']:
        path = root/sample['path']
        if sha(path) != sample['sha256']:
            raise ValueError('Changed full-matrix sample')
        with np.load(str(path), allow_pickle=False) as z:
            x, y = z['X'], z['Y_float']
        for i in range(12):
            q, integer, _ = encode_arrays(x[i], weights[i], biases[i])
            legacy = reference(q['X'], q['W'], q['b'], 12)
            for key in ('total', 'result', 'saturated'):
                np.testing.assert_array_equal(integer[key], legacy[key])
            recomputed.append(dict(sample_id=sample['sample_id'], layer=i+1,
                                   **error_metrics(decode(integer['result'], numeric_format()), y[i])))
    summary = aggregate_tasks(recomputed)
    for key in ('samples', 'task_count', 'max_layer_nrmse', 'max_task_nrmse', 'threshold_passed'):
        if summary[key] != report[key]:
            raise ValueError('Recomputed precision mismatch: '+key)
    a.output.mkdir(parents=True)
    records = []
    selected = [('layer_%02d' % i, report['sample_artifacts'][0]['sample_id'], i) for i in range(1, 13)]
    selected += [(name, report[key]['sample_id'], report[key]['layer']) for name, key in
                 [('worst_error', 'worst_task'), ('largest_input', 'largest_input_task'), ('largest_output', 'largest_output_task')]]
    artifacts = {s['sample_id']: s for s in report['sample_artifacts']}
    source_dir = a.output/'float_sources'; source_dir.mkdir()
    for name, sample, layer in selected:
        with np.load(str(root/artifacts[sample]['path']), allow_pickle=False) as z:
            x, y = z['X'][layer-1], z['Y_float'][layer-1]
        source = source_dir/(name+'.npz')
        np.savez_compressed(str(source), X=x, W=weights[layer-1], b=biases[layer-1], Y_float=y)
        config = export_task(source, a.output/name, layer, sample_id=sample)
        records.append(dict(case=name, sample_id=sample, layer=layer, reference_npz=source.relative_to(a.output).as_posix(),
                            reference_npz_sha256=sha(source), codec_sha256=sha(a.output/name/'codec.json')))
    x, w, b = np.zeros((99, 64), np.int64), np.zeros((64, 256), np.int64), np.zeros(256, np.int64)
    export(a.output/'zero', x, w, b, integer_model(x, w, b), 12)
    x[:] = -32768; w[:] = -32768
    b[::2] = -(1 << 39); b[1::2] = (1 << 39)-1
    for shift in (0, 31):
        export(a.output/('shift%02d' % shift), x, w, b, integer_model(x, w, b, shift), shift)
    w[::2] = -32767; w[1::2] = 32767; b[:] = 0
    export(a.output/'cancellation', x, w, b, integer_model(x, w, b), 12)
    result = dict(source_evaluation_sha256=sha(a.evaluation), recomputed=summary,
        independent_integer_implementations_bit_exact=True, rtl_verified=False, cases=records,
        directed_cases=['zero', 'shift00', 'shift31', 'cancellation'])
    (a.output/'selection.json').write_text(json.dumps(result, indent=2), encoding='utf8')
    print('PRECISION_RECHECK_PASS samples=600 tasks=7200 selected_real_cases=15 directed_cases=4', flush=True)


if __name__ == '__main__':
    main()
