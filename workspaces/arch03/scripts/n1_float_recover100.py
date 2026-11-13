"""Recover one fixed original FLOAT candidate per verified WAV, never from HEX.

Requires the exact sample001 probe. This only generates candidates; a separate
server-side comparison against all original NPZ hashes is mandatory afterwards.
No alternate inference profiles, overwrite, training or quantization.
"""
import argparse
import datetime
import importlib.util
import json
from pathlib import Path, PurePosixPath
import re
import sys

import n1_float_single_probe as probe

PROBE_SCRIPT_SHA = 'a90cd0b806797eaef91518c14d45d6412e70a7c7625aee0dfa9b205a1ab36665'
PROBE_RESULT_SHA = '007797d05edaa035bbcb655ff2d52a86d51105f8a3f05b36e21f93b0a4cf2d8a'
FIRST_SHA = '275444a4f5d895cd0fdf8a10a23705fb784ba7151a6d4980aa4ff50793f8533e'
SCHEMA = 'n1-recovered-float100-candidates-v1'


def validate_samples(rows):
    probe.require(len(rows) == 100, 'Require exactly100 original samples')
    seen = set()
    for number, row in enumerate(rows, 1):
        probe.require(row['sample'] == row['original_rank'] == number, 'Original rank/order changed')
        relative = PurePosixPath(row['wav'])
        probe.require(not relative.is_absolute() and len(relative.parts) == 2
                      and '..' not in relative.parts and '\\' not in row['wav']
                      and relative.suffix == '.wav', 'Unsafe WAV relative path')
        probe.require(row['wav'] not in seen, 'Duplicate original WAV')
        probe.require(row['split'] in ('training', 'testing', 'validation'), 'Unknown split')
        probe.require(re.fullmatch('[a-f0-9]{64}', row['wav_sha256']) is not None, 'Invalid WAV hash')
        seen.add(row['wav'])


def execute(args):
    args.mode = 'probe'
    args.expected_npz_sha256 = FIRST_SHA
    files, helper_path, _, _ = probe.preflight(args)
    probe.require(probe.sha(probe.__file__) == PROBE_SCRIPT_SHA, 'Single probe implementation changed')
    probe.require(probe.sha(args.probe_run/'result.json') == PROBE_RESULT_SHA, 'Exact original probe required')
    initial = json.loads((args.probe_run/'result.json').read_text())
    probe.require(initial['status'] == 'exact_original_npz_match'
                  and initial['strict_original_npz_match'] is True
                  and initial['capture_repeat_bit_exact'] is True
                  and probe.sha(args.probe_run/'float_tensors.npz') == FIRST_SHA,
                  'Original sample001 probe identity failed')
    files[str((args.probe_run/'result.json').resolve())] = PROBE_RESULT_SHA
    files[str((args.probe_run/'float_tensors.npz').resolve())] = FIRST_SHA
    files[str(Path(__file__).resolve())] = probe.sha(__file__)
    listing = json.loads(args.wav_hashlist.read_text(encoding='utf-8-sig'))
    rows = listing['samples']
    validate_samples(rows)
    data_root = args.data_root.resolve(strict=True)
    wav_paths = []
    for row in rows:
        path = data_root.joinpath(*PurePosixPath(row['wav']).parts).resolve(strict=True)
        path.relative_to(data_root)
        probe.require(path.is_file() and probe.sha(path) == row['wav_sha256'], 'Original WAV differs')
        files[str(path)] = row['wav_sha256']
        wav_paths.append(path)
    args.output.mkdir(parents=True, exist_ok=False)
    identity = dict(schema=SCHEMA, started_utc=datetime.datetime.utcnow().isoformat()+'Z',
        samples=100, layers=1200, source_files_sha256=files,
        server_manifest_sha256=probe.SERVER_MANIFEST_SHA,
        wav_hashlist_sha256=probe.WAV_LIST_SHA, shared_weights_sha256=probe.WEIGHTS_SHA,
        probe_result_sha256=PROBE_RESULT_SHA, probe_script_sha256=PROBE_SCRIPT_SHA,
        extractor_sha256=probe.HELPER_SHA, batch_size=1, threads=4,
        source_proof_sha256=probe.sha(args.source_proof), training=False,
        original_archive_obtained=False, complete100_original_npz_match=False,
        n1_precision_accepted=False, quantization_executed=False)
    probe.save(args.output/'identity.json', identity)
    try:
        probe.require('tensorflow' not in sys.modules, 'Use a fresh process')
        import numpy as np
        probe.require(np.__version__ == '1.19.5', 'Audited NumPy version required')
        spec = importlib.util.spec_from_file_location('n1_original_full_matrix_extract', str(helper_path))
        helper = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(helper)
        tf, model, infer, weights, biases, checked, flags = helper.build_runtime(args.model_root, 4)
        probe.require(tf.__version__ == '2.4.0' and len(checked) == 162, 'Audited model/runtime differs')
        with np.load(str(args.shared_weights), allow_pickle=False) as shared:
            np.testing.assert_array_equal(weights, shared['W'])
            np.testing.assert_array_equal(biases, shared['b'])
        probe.save(args.output/'effective_flags.json', flags)
        candidates = []
        for row, path in zip(rows, wav_paths):
            audio = helper.read_audio(path)[None, :]
            values = [value.numpy() for value in infer(audio)]
            repeated = [value.numpy() for value in infer(audio)]
            for a, b in zip(values, repeated):
                np.testing.assert_array_equal(a, b)
            x, y, logits = values
            probe.require(x.shape == (1, 12, 99, 64) and y.shape == (1, 12, 99, 256), 'Capture shape')
            original_logits = np.asarray(model(audio, training=False))
            np.testing.assert_allclose(logits, original_logits, rtol=1e-4, atol=2e-5)
            max_errors = []
            for layer in range(12):
                expected = x[0, layer].astype(np.float64) @ weights[layer].astype(np.float64) + biases[layer].astype(np.float64)
                np.testing.assert_allclose(y[0, layer], expected, rtol=1e-4, atol=2e-5)
                max_errors.append(float(np.max(np.abs(y[0, layer]-expected))))
            folder = args.output/('sample_%03d'%row['sample'])
            folder.mkdir()
            candidate = probe.write_candidate(folder/'float_tensors.npz', dict(X=x[0], Y=y[0], logits=logits))
            if row['sample'] == 1:
                probe.require(candidate['npz_sha256'] == FIRST_SHA, 'Known first NPZ changed; stop')
            probe.require(probe.sha(path) == row['wav_sha256'], 'WAV mutated during inference')
            item = dict(sample=row['sample'], original_rank=row['original_rank'], wav=row['wav'],
                split=row['split'], wav_sha256=row['wav_sha256'], **candidate,
                capture_repeat_bit_exact=True, full_matrix_float64_max_abs_errors=max_errors,
                capture_original_logits_max_abs_error=float(np.max(np.abs(logits-original_logits))))
            probe.save(folder/'candidate.json', item)
            candidates.append(item)
            print('N1_FLOAT_CANDIDATE', row['sample'], candidate['npz_sha256'], flush=True)
        for path, digest in files.items():
            probe.require(probe.sha(path) == digest, 'Source changed during recovery: '+path)
        result = dict(identity, status='100_candidates_generated_original_identity_join_pending',
            identity_sha256=probe.sha(args.output/'identity.json'), checked_model_variables=len(checked),
            python=sys.version, numpy=np.__version__, tensorflow=tf.__version__, samples_provenance=candidates,
            finished_utc=datetime.datetime.utcnow().isoformat()+'Z')
        probe.save(args.output/'summary.json', result)
        small = dict(schema='n1-float100-candidate-hashes-v1', count=100,
            server_manifest_sha256=probe.SERVER_MANIFEST_SHA, shared_weights_sha256=probe.WEIGHTS_SHA,
            identity_sha256=result['identity_sha256'], summary_sha256=probe.sha(args.output/'summary.json'),
            samples=[{key:item[key] for key in ('sample','original_rank','wav','split','wav_sha256','npz_sha256','bytes')}
                     for item in candidates])
        probe.save(args.output/'candidate_hashes.json', small)
        print('N1_FLOAT100_CANDIDATES_SHA', probe.sha(args.output/'candidate_hashes.json'), flush=True)
        return 0
    except BaseException as exc:
        probe.save(args.output/'failure.json', dict(status='failed_preserved', error_type=type(exc).__name__,
            error=str(exc), complete100_original_npz_match=False, n1_precision_accepted=False))
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('model-root','data-root','upstream-receipt','shared-weights','wav-hashlist','source-proof','probe-run','output'):
        parser.add_argument('--'+name, type=Path, required=True)
    return execute(parser.parse_args())


if __name__ == '__main__':
    sys.exit(main())
