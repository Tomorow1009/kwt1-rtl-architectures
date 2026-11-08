"""Evaluate actual local ICB captures for the selected full-matrix cases."""
import argparse
import json
import os
from pathlib import Path
import numpy as np
from evaluate import evaluate
from numeric import decode, error_metrics, read_capture, sha


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--vectors', type=Path, required=True)
    p.add_argument('--run', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    if a.output.exists():
        p.error('Use a new output directory')
    selection = json.loads((a.vectors/'selection.json').read_text())
    run = json.loads((a.run/'summary.json').read_text())
    if run['status'] != 'passed' or run['cpu_executed'] or run['consecutive_tasks']:
        raise ValueError('Expected single-task local ICB regression')
    captures = {t['case']: t for t in run['cases']}
    if len(captures) != len(run['cases']):
        raise ValueError('Duplicate case capture')
    a.output.mkdir(parents=True)
    manifest_tasks, metrics = [], []
    for case in selection['cases']:
        name = case['case']; vector = a.vectors/name
        capture = a.run/captures[name]['capture']
        if sha(capture) != captures[name]['capture_sha256'] or sha(vector/'codec.json') != case['codec_sha256']:
            raise ValueError('Changed capture/codec')
        codec = json.loads((vector/'codec.json').read_text())
        for filename, digest in codec['sha256'].items():
            if sha(vector/filename) != digest:
                raise ValueError('Changed codec input '+filename)
        reference_path = a.vectors/case['reference_npz']
        if sha(reference_path) != case['reference_npz_sha256']:
            raise ValueError('Changed floating reference')
        with np.load(str(reference_path), allow_pickle=False) as z:
            reference = z['Y_float']
        with np.load(str(vector/'expected.npz'), allow_pickle=False) as z:
            expected, expected_sat = z['result'], z['saturated']
        values, saturated = read_capture(capture)
        if not np.array_equal(values, expected) or not np.array_equal(saturated, expected_sat):
            raise ValueError('Actual RTL/integer mismatch')
        result = decode(values, codec['numeric_format'])
        metrics.append(dict(case=name, sample_id=case['sample_id'], layer=case['layer'],
                            capture_sha256=sha(capture), **error_metrics(result, reference)))
        if name.startswith('layer_'):
            task = dict(sample_id=case['sample_id'], layer=case['layer'],
                        fraction_bits=codec['numeric_format']['output_fraction_bits'], numeric_format=codec['numeric_format'])
            for key, path in [('reference_npz', reference_path), ('actual_csv', capture), ('integer_npz', vector/'expected.npz')]:
                task[key] = Path(os.path.relpath(str(path.resolve()), str(a.output.resolve()))).as_posix()
                task[key+'_sha256'] = sha(path)
            manifest_tasks.append(task)
    manifest = a.output/'capture_manifest.json'
    manifest.write_text(json.dumps(dict(dataset_kind='development', provenance='Real XSim local ICB pin_mock output; independent FC1 inputs', tasks=manifest_tasks), indent=2), encoding='utf8')
    aggregate = evaluate(manifest)
    result = dict(dataset_kind='development', scope='local_icb_pin_mock_not_cpu', cpu_executed=False,
        integer_bit_exact=True, official_precision_verified=False, task_metrics=metrics,
        twelve_layer_aggregate=aggregate, threshold_passed=aggregate['threshold_passed'] and all(t['threshold_passed'] for t in metrics),
        selection_sha256=sha(a.vectors/'selection.json'), run_summary_sha256=sha(a.run/'summary.json'))
    (a.output/'evaluation.json').write_text(json.dumps(result, indent=2, allow_nan=False), encoding='utf8')
    print('ACTUAL_RTL_PRECISION tasks=%d outputs=%d threshold_passed=%s' % (len(metrics), len(metrics)*25344, result['threshold_passed']))
    if not result['threshold_passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
