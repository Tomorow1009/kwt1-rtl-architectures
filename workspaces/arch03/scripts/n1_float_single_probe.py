"""Prepare/probe only sample_001; exact original NPZ SHA is the success gate.

Importing this module does not import NumPy, TensorFlow or the model. The probe
mode is explicit and requires a separately recorded successful WAV source join.
No batching expansion, quantization, training or original-file replacement.
"""
import argparse
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import re
import sys
import zipfile
import zlib

SCRIPT_DIR = Path(__file__).resolve().parent
HELPER_SHA = '6296cdaddddc5d086ab111d5fd8ead446df97d782e9bc10ff604a763c71f5606'
NUMERIC_SHA = '8e763ae71e154d057f216c4f84d4dd675a1226d7ca9e38eaf03a95728ff1b2f5'
UPSTREAM_SHA = 'c32351a0eea6220c1f5ce017bb25fe0406af46c057f99a843c100b72052201b4'
WAV_LIST_SHA = '5da67b0f6acc1cf89ca6d14166845606731c1442e00d6c083a2fc540c9541b3c'
SERVER_MANIFEST_SHA = '9900a9bd1addbdeb256020ba9a04f4615791fbd5a624abd411364098c382c97e'
WEIGHTS_SHA = '99a3f2d990203b2bd9f3bdf5dc98974d6a7102027f7d67b9abf19e72ee03a6ad'
INDEX_SHA = 'af4385be16ff8ea6613c61a5f494aaa9c904f81dcc311f71870cfeb96824c07d'
WAV_RELATIVE = 'down/90645155_nohash_0.wav'
WAV_SHA = '0c150dd68724cc63c1d42e7fff54bf53244f33bf4739a5f8dce428ac260d4070'
SHAPES = (('X', (12,99,64)), ('Y', (12,99,256)), ('logits', (1,12)))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    with Path(path).open('x', encoding='utf-8') as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write('\n')


def proof_identity(proof, expected_npz_sha):
    require(re.fullmatch('[0-9a-f]{64}', expected_npz_sha or '') is not None, 'Original sample NPZ SHA required')
    require(proof.get('schema') == 'n1-wav-source-join-receipt-v1', 'WAV join receipt schema')
    require(proof.get('passed') is True and proof.get('checked') == 100
            and proof.get('mismatches') == 0 and proof.get('inputs_stable') is True, 'WAV source join not passed')
    require(proof.get('wav_hashlist_sha256') == WAV_LIST_SHA
            and proof.get('server_manifest_sha256') == SERVER_MANIFEST_SHA, 'WAV join input identity')
    require(proof.get('sample_001_float_npz_sha256') == expected_npz_sha, 'Original sample NPZ identity disagreement')
    require(isinstance(proof.get('observed_server_time'), str) and proof['observed_server_time'], 'Missing observation time')
    require(re.fullmatch('[0-9a-f]{64}', proof.get('evidence_sha256', '')) is not None, 'Missing observation evidence hash')


def write_candidate(path, arrays):
    import numpy as np
    require(list(arrays) == [name for name, _ in SHAPES], 'Candidate keys/order must be X,Y,logits')
    for name, shape in SHAPES:
        value = arrays[name]
        require(value.shape == shape and value.dtype == np.dtype('float32'), 'Wrong float32 shape: '+name)
        require(np.isfinite(value).all(), 'Nonfinite candidate: '+name)
    path = Path(path)
    require(not path.exists(), 'Candidate already exists; preserve prior results')
    # A declared candidate serialization, not evidence of the unavailable
    # original exporter key order, compression mode or NPY-header settings.
    with path.open('xb') as handle:
        np.savez_compressed(handle, X=arrays['X'], Y=arrays['Y'], logits=arrays['logits'])
    with np.load(str(path), allow_pickle=False) as loaded:
        require(loaded.files == [name for name, _ in SHAPES], 'Candidate NPZ key order')
        for name, _ in SHAPES:
            np.testing.assert_array_equal(loaded[name], arrays[name])
    with zipfile.ZipFile(str(path)) as zipped:
        require(zipped.testzip() is None, 'Candidate CRC')
        members = [dict(name=v.filename, compression=v.compress_type, crc32=v.CRC,
            compressed_bytes=v.compress_size, bytes=v.file_size, timestamp=list(v.date_time))
            for v in zipped.infolist()]
    return dict(npz_sha256=sha(path), bytes=path.stat().st_size, members=members,
        arrays={name:dict(shape=list(value.shape), dtype=value.dtype.str,
            c_order_bytes_sha256=hashlib.sha256(value.tobytes(order='C')).hexdigest())
            for name, value in arrays.items()},
        serialization='numpy.savez_compressed X,Y,logits; original serialization unconfirmed')


def preflight(args):
    require(not args.output.exists() and not args.output.is_symlink(), 'Use a new output directory')
    files = {}
    def check(path, expected):
        path = Path(path).resolve(strict=True)
        require(path.is_file() and sha(path) == expected, 'Source identity differs: '+str(path))
        files[str(path)] = expected
        return path
    check(__file__, sha(__file__))
    helper = check(SCRIPT_DIR/'full_matrix_eval.py', HELPER_SHA)
    check(SCRIPT_DIR/'numeric.py', NUMERIC_SHA)
    check(args.upstream_receipt, UPSTREAM_SHA)
    check(args.shared_weights, WEIGHTS_SHA)
    check(args.wav_hashlist, WAV_LIST_SHA)
    info = json.loads(args.upstream_receipt.read_text(encoding='utf-8-sig'))
    require(info['commit'] == '237e4097afd4f6851e0b82f0a8d65c2dfe8eae30'
            and info['all_match'] and len(info['files']) == 36, 'Wrong official model receipt')
    model_root = args.model_root.resolve(strict=True)
    for item in info['files']:
        relative = PurePosixPath(item['path'])
        require(not relative.is_absolute() and '..' not in relative.parts, 'Unsafe model source path')
        model_path = model_root.joinpath(*relative.parts).resolve(strict=True)
        model_path.relative_to(model_root)
        check(model_path, item['upstream_sha256'])
    data_root = args.data_root.resolve(strict=True)
    wav = data_root.joinpath(*PurePosixPath(WAV_RELATIVE).parts).resolve(strict=True)
    wav.relative_to(data_root)
    check(wav, WAV_SHA)
    listing = json.loads(args.wav_hashlist.read_text(encoding='utf-8-sig'))
    require(listing['count'] == 100 and listing['selected_indices_comma_ascii_sha256'] == INDEX_SHA, 'Selected100 identity')
    first = listing['samples'][0]
    require(first['sample'] == first['original_rank'] == 1 and first['wav'] == WAV_RELATIVE
            and first['wav_sha256'] == WAV_SHA and first['split'] == 'training', 'Wrong first sample')
    if args.mode == 'probe':
        require(args.source_proof is not None, 'Separate actual server WAV join receipt required')
        proof = json.loads(args.source_proof.read_text(encoding='utf-8-sig'))
        proof_identity(proof, args.expected_npz_sha256)
        check(args.source_proof, sha(args.source_proof))
    elif args.expected_npz_sha256 is not None:
        require(re.fullmatch('[0-9a-f]{64}', args.expected_npz_sha256) is not None, 'Invalid expected NPZ SHA')
    return files, helper, wav, first


def execute(args):
    files, helper_path, wav_path, first = preflight(args)
    args.output.mkdir(parents=True, exist_ok=False)
    identity = dict(schema='n1-single-float-recovery-probe-v1', mode=args.mode,
        sample=1, wav=WAV_RELATIVE, samples=1, layers=12, source_files_sha256=files,
        expected_original_sample_npz_sha256=args.expected_npz_sha256,
        started_utc=datetime.datetime.utcnow().isoformat()+'Z',
        original_npz_serialization_confirmed=False, original_inference_batch_confirmed=False,
        candidate_profile=dict(batch_size=1, threads=4, seed=20261109,
            extractor_sha256=HELPER_SHA, key_order=['X','Y','logits'], dtype='float32',
            writer='numpy.savez_compressed', training=False),
        float_source_recovered=False, complete100_recovered=False, n1_precision_accepted=False)
    save(args.output/'identity.json', identity)
    if args.mode == 'prepare':
        save(args.output/'result.json', dict(status='prepared_not_executed', **identity))
        print('N1_SINGLE_FLOAT_PROBE prepared_not_executed')
        return 0
    try:
        require('tensorflow' not in sys.modules, 'Run probe in a fresh process')
        import numpy as np
        require(np.__version__ == '1.19.5', 'Use the audited NumPy environment')
        spec = importlib.util.spec_from_file_location('n1_existing_full_matrix_extract', str(helper_path))
        helper = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(helper)
        tf, model, infer, weights, biases, checked, flags = helper.build_runtime(args.model_root, 4)
        require(tf.__version__ == '2.4.0', 'Use the audited TensorFlow environment')
        with np.load(str(args.shared_weights), allow_pickle=False) as shared:
            np.testing.assert_array_equal(weights, shared['W'])
            np.testing.assert_array_equal(biases, shared['b'])
        audio = helper.read_audio(wav_path)[None, :]
        first_values = [value.numpy() for value in infer(audio)]
        repeated = [value.numpy() for value in infer(audio)]
        for initial, again in zip(first_values, repeated):
            np.testing.assert_array_equal(initial, again)
        x, y, logits = first_values
        require(x.shape == (1,12,99,64) and y.shape == (1,12,99,256), 'Incomplete full matrix capture')
        original_logits = np.asarray(model(audio, training=False))
        np.testing.assert_allclose(logits, original_logits, rtol=1e-4, atol=2e-5)
        max_errors = []
        for layer in range(12):
            recomputed = x[0,layer].astype(np.float64) @ weights[layer].astype(np.float64) + biases[layer].astype(np.float64)
            np.testing.assert_allclose(y[0,layer], recomputed, rtol=1e-4, atol=2e-5)
            max_errors.append(float(np.max(np.abs(y[0,layer]-recomputed))))
        candidate = write_candidate(args.output/'float_tensors.npz', dict(X=x[0], Y=y[0], logits=logits))
        for path, expected in files.items():
            require(sha(path) == expected, 'Source changed during probe: '+path)
        exact = candidate['npz_sha256'] == args.expected_npz_sha256
        save(args.output/'source_candidate.json', dict(first, scope='Candidate provenance, not copied original source.json'))
        save(args.output/'effective_flags.json', flags)
        result = dict(status='exact_original_npz_match' if exact else 'candidate_npz_mismatch_stop',
            identity_sha256=sha(args.output/'identity.json'), python=sys.version,
            numpy=np.__version__, tensorflow=tf.__version__, checked_model_variables=len(checked),
            serialization_runtime=dict(numpy_npyio_sha256=sha(np.lib.npyio.__file__),
                numpy_format_sha256=sha(np.lib.format.__file__), zipfile_sha256=sha(zipfile.__file__),
                zlib_build_version=zlib.ZLIB_VERSION, zlib_runtime_version=zlib.ZLIB_RUNTIME_VERSION),
            capture_repeat_bit_exact=True, full_matrix_float64_max_abs_errors=max_errors,
            capture_original_logits_max_abs_error=float(np.max(np.abs(logits-original_logits))),
            candidate=candidate, expected_original_sample_npz_sha256=args.expected_npz_sha256,
            strict_original_npz_match=exact, sample_001_float_source_recovered=exact,
            complete100_recovered=False, n1_precision_accepted=False,
            auto_expand_to_100=False, quantization_executed=False)
        save(args.output/'result.json', result)
        print('N1_SINGLE_FLOAT_PROBE '+result['status']+' '+candidate['npz_sha256'])
        return 0 if exact else 2
    except BaseException as exc:
        save(args.output/'failure.json', dict(status='failed_preserved', error_type=type(exc).__name__,
            error=str(exc), complete100_recovered=False, n1_precision_accepted=False))
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=('prepare','probe'), default='prepare')
    parser.add_argument('--model-root', type=Path, required=True)
    parser.add_argument('--data-root', type=Path, required=True)
    parser.add_argument('--upstream-receipt', type=Path, required=True)
    parser.add_argument('--shared-weights', type=Path, required=True)
    parser.add_argument('--wav-hashlist', type=Path, required=True)
    parser.add_argument('--source-proof', type=Path)
    parser.add_argument('--expected-npz-sha256')
    parser.add_argument('--output', type=Path, required=True)
    return execute(parser.parse_args())


if __name__ == '__main__':
    sys.exit(main())
