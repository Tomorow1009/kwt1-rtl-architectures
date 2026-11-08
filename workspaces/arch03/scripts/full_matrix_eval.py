"""Extract ALL twelve FC1 matrices in one frozen KWT-1 forward per sample.

Uses the unmodified upstream model at 237e4097 and its best_weights. No fitting,
training, calibration or test-split selection. Output is development evidence.
Run with TensorFlow 2.4.0 / NumPy 1.19.5 (the existing .venv-kwt environment).
"""
import argparse
from collections import Counter
import json
import os
from pathlib import Path
import sys
import time
import wave
from types import SimpleNamespace
import numpy as np
from numeric import (aggregate_tasks, decode, encode_arrays, error_metrics,
                     numeric_format, sha)


def save(path, obj):
    path = Path(path)
    temporary = path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(obj, indent=2, ensure_ascii=False, allow_nan=False), encoding='utf8')
    temporary.replace(path)


def select_samples(data_root, model_root):
    """500 target words + 99 other speech + one canonical validation silence.

    Validation silence is zero PCM in upstream input_data.py: foreground is
    muted and background is only mixed in training. We count it once, not as
    many independent recordings of the identical all-zero waveform.
    """
    validation = (data_root/'validation_list.txt').read_text().splitlines()
    testing = set((data_root/'testing_list.txt').read_text().splitlines())
    if len(validation) != len(set(validation)) or set(validation) & testing:
        raise ValueError('Duplicate or overlapping split lists')
    words = json.loads((model_root/'models_data_v2_12_labels/kwt1/flags.json').read_text())['wanted_words'].split(',')
    rank = lambda name: __import__('hashlib').sha256(('20261109:'+name).encode()).hexdigest()
    selected = []
    for word in words:
        candidates = sorted((p for p in validation if p.split('/')[0] == word), key=rank)
        if len(candidates) < 50:
            raise ValueError('Insufficient validation samples: '+word)
        selected.extend((name, word) for name in candidates[:50])
    unknown = sorted((p for p in validation if p.split('/')[0] not in words), key=rank)
    if len(unknown) < 99:
        raise ValueError('Insufficient unknown speech')
    selected.extend((name, '_unknown_') for name in unknown[:99])
    entries = []
    for index, (name, label) in enumerate(selected):
        path = (data_root/name).resolve()
        path.relative_to(data_root.resolve())
        entries.append(dict(sample_id='dev_%06d' % index, split='validation', kind='speech',
                            path=name, label=label, sha256=sha(path)))
    entries.append(dict(sample_id='dev_000599', split='validation', kind='silence',
                        path=None, label='_silence_', generation='16000 float32 zeros; validation silence, no background mixing'))
    if len(entries) != 600:
        raise ValueError('Expected exactly 600 samples')
    return entries


def read_audio(path):
    with wave.open(str(path), 'rb') as f:
        if (f.getnchannels(), f.getsampwidth(), f.getframerate(), f.getcomptype()) != (1, 2, 16000, 'NONE'):
            raise ValueError('Expected mono PCM16 16kHz WAV')
        raw = f.readframes(16000)
    result = np.zeros(16000, dtype=np.float32)
    pcm = np.frombuffer(raw, dtype='<i2').astype(np.float32)/np.float32(32768)
    result[:len(pcm)] = pcm
    return result


def check_sources(model_root, receipt):
    info = json.loads(receipt.read_text(encoding='utf8'))
    if info['commit'] != '237e4097afd4f6851e0b82f0a8d65c2dfe8eae30' or not info['all_match']:
        raise ValueError('Wrong upstream verification receipt')
    sources = {}
    for f in info['files']:
        path = (model_root/f['path']).resolve()
        path.relative_to(model_root.resolve())
        actual = sha(path)
        if actual != f['upstream_sha256']:
            raise ValueError('Model source/checkpoint changed: '+f['path'])
        sources[f['path']] = actual
    return sources


def build_runtime(model_root, threads):
    # Adapted from the team's extract_kwt.py / batch_runtime.py. Every tensor
    # is captured here; the previous exporter only retained X[0,:]/Y[0,0].
    os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
    sys.path.insert(0, str(model_root))
    import tensorflow as tf
    from kws_streaming.models import models
    from kws_streaming.models.transformer_utils import KWSTransformer
    tf.compat.v1.enable_eager_execution()
    tf.config.threading.set_intra_op_parallelism_threads(threads)
    tf.config.threading.set_inter_op_parallelism_threads(1)
    tf.keras.backend.clear_session()
    tf.keras.backend.set_learning_phase(0)
    tf.random.set_seed(20261109)
    model_dir = model_root/'models_data_v2_12_labels/kwt1'
    flags = json.loads((model_dir/'flags.json').read_text())
    flags.update(batch_size=None, training=False, train=0, distill_teacher_json='',
                 prenorm=False, approximate_gelu=False, use_spec_augment=0,
                 use_spec_cutout=0, time_shift_ms=0., sp_time_shift_ms=0.,
                 resample=0., sp_resample=0., volume_resample=0.,
                 background_volume=0., background_frequency=0.)
    model = models.MODELS['kws_transformer'](SimpleNamespace(**flags))
    status = model.load_weights(str(model_dir/'best_weights'))
    status.assert_existing_objects_matched(); status.expect_partial()
    transformer = next(layer for layer in model.layers if isinstance(layer, KWSTransformer))
    if model.count_params() != 607308 or len(transformer.enc_layers) != 12 or any(b.prenorm for b in transformer.enc_layers):
        raise ValueError('Unexpected KWT-1 architecture')
    reader = tf.train.load_checkpoint(str(model_dir/'best_weights'))
    checked = []
    def check(variable, key):
        np.testing.assert_array_equal(variable.numpy(), reader.get_tensor(key+'/.ATTRIBUTES/VARIABLE_VALUE'))
        checked.append(dict(variable=variable.name, checkpoint_key=key, shape=list(variable.shape)))
    prefix = 'layer_with_weights-0'
    for name in ('pos_emb', 'class_emb'):
        check(getattr(transformer, name), prefix+'/'+name)
    for name in ('kernel', 'bias'):
        check(getattr(transformer.patch_proj, name), prefix+'/patch_proj/'+name)
    for i, block in enumerate(transformer.enc_layers):
        base = prefix+'/enc_layers/%d/' % i
        for name in ('query_dense', 'key_dense', 'value_dense', 'combine_heads'):
            dense = getattr(block.att, name)
            check(dense.kernel, base+'att/'+name+'/kernel')
            if dense.use_bias:
                check(dense.bias, base+'att/'+name+'/bias')
        for wi, li in enumerate((0, 2)):
            for name in ('kernel', 'bias'):
                check(getattr(block.ffn.layers[li], name), base+'ffn/layer_with_weights-%d/' % wi+name)
        for ln in ('layernorm1', 'layernorm2'):
            for name in ('gamma', 'beta'):
                check(getattr(getattr(block, ln), name), base+ln+'/'+name)
    for name in ('kernel', 'bias'):
        check(getattr(model.layers[-1].layers[0], name), 'layer_with_weights-1/layer_with_weights-0/'+name)
    if len(checked) != len(model.weights):
        raise ValueError('Not all loaded weights checked')
    captures, calls = {}, []
    for index, block in enumerate(transformer.enc_layers):
        dense, original = block.ffn.layers[0], block.ffn.layers[0].call
        calls.append((dense, original))
        @tf.autograph.experimental.do_not_convert
        def capture(inputs, _index=index, _call=original):
            result = _call(inputs)
            captures[_index] = (inputs, result)
            return result
        dense.call = capture
    @tf.function(input_signature=[tf.TensorSpec([None, 16000], tf.float32)], autograph=False)
    def inference(audio):
        captures.clear()
        logits = model(audio, training=False)
        if isinstance(logits, (list, tuple)):
            logits = logits[0]
        if set(captures) != set(range(12)):
            raise ValueError('Did not capture all Dense calls')
        return (tf.stack([captures[i][0] for i in range(12)], axis=1),
                tf.stack([captures[i][1] for i in range(12)], axis=1), logits)
    try:
        infer = inference.get_concrete_function()
    finally:
        for dense, original in calls:
            dense.call = original
    weights = np.stack([b.ffn.layers[0].kernel.numpy() for b in transformer.enc_layers])
    biases = np.stack([b.ffn.layers[0].bias.numpy() for b in transformer.enc_layers])
    return tf, model, infer, weights, biases, checked, flags


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--model-root', type=Path, required=True)
    p.add_argument('--data-root', type=Path, required=True)
    p.add_argument('--upstream-receipt', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--batch-size', type=int, default=8)
    p.add_argument('--threads', type=int, default=4)
    p.add_argument('--limit', type=int, default=600, help='Smoke checks only when <600; never full acceptance')
    a = p.parse_args()
    if not 1 <= a.limit <= 600 or a.batch_size < 1 or a.threads < 1:
        p.error('Invalid size/thread count')
    if a.output.exists():
        p.error('Use a new output directory; existing evidence is immutable')
    sources = check_sources(a.model_root, a.upstream_receipt)
    entries = select_samples(a.data_root, a.model_root)
    a.output.mkdir(parents=True)
    sample_manifest = dict(dataset_kind='development', seed=20261109, split='validation', calibration=False,
        upstream_commit='237e4097afd4f6851e0b82f0a8d65c2dfe8eae30', samples=entries,
        counts=dict(Counter(t['label'] for t in entries)),
        selection='50 per target word, 99 unknown speech, one canonical zero silence; SHA256-ranked validation paths',
        split_sha256={n: sha(a.data_root/n) for n in ('validation_list.txt', 'testing_list.txt')})
    save(a.output/'samples.json', sample_manifest)
    entries = entries[:a.limit]
    code_hashes = {name: sha(Path(__file__).with_name(name)) for name in ('full_matrix_eval.py', 'numeric.py')}
    started = time.monotonic()
    tf, model, infer, weights, biases, checked, flags = build_runtime(a.model_root, a.threads)
    np.savez_compressed(str(a.output/'parameters.npz'), W=weights, b=biases)
    save(a.output/'environment.json', dict(python=sys.version, numpy=np.__version__, tensorflow=tf.__version__,
        inference_flags=flags, checked_variables=checked, model_sources=sources, code_sha256=code_hashes,
        numeric_format=numeric_format(), training=False, calibration=False, batch_size=a.batch_size,
        threads=a.threads, upstream_receipt_sha256=sha(a.upstream_receipt)))
    tasks, artifacts = [], []
    capture_check = None
    for start in range(0, len(entries), a.batch_size):
        batch = entries[start:start+a.batch_size]
        audio = np.stack([read_audio(a.data_root/e['path']) if e['kind'] == 'speech' else np.zeros(16000, np.float32) for e in batch])
        for entry in batch:
            if entry['kind'] == 'speech' and sha(a.data_root/entry['path']) != entry['sha256']:
                raise ValueError('Audio changed since manifest freeze')
        x, y, logits = [v.numpy() for v in infer(audio)]
        if x.shape != (len(batch), 12, 99, 64) or y.shape != (len(batch), 12, 99, 256):
            raise ValueError('Invalid complete capture shape')
        if not all(np.isfinite(v).all() for v in (x, y, logits)):
            raise ValueError('Non-finite model outputs')
        if start == 0:
            # Check the graph capture does not change inference and is deterministic.
            original = np.asarray(model(audio[:1], training=False))
            one = [v.numpy() for v in infer(audio[:1])]
            repeat = [v.numpy() for v in infer(audio[:1])]
            np.testing.assert_allclose(one[2], original, rtol=1e-4, atol=2e-5)
            np.testing.assert_allclose(one[0], x[:1], rtol=1e-4, atol=2e-5)
            np.testing.assert_allclose(one[1], y[:1], rtol=1e-4, atol=2e-5)
            for first, second in zip(one, repeat):
                np.testing.assert_array_equal(first, second)
            decoded, rate = tf.audio.decode_wav(tf.io.read_file(str(a.data_root/batch[0]['path'])), desired_channels=1, desired_samples=16000)
            if int(rate.numpy()) != 16000:
                raise ValueError('Unexpected sample rate')
            np.testing.assert_array_equal(decoded.numpy()[:, 0], audio[0])
            capture_check = dict(repeat_bit_exact=True, pcm_matches_tensorflow=True,
                original_logits_max_abs_error=float(np.max(np.abs(one[2]-original))),
                batch_x_max_abs_error=float(np.max(np.abs(one[0]-x[:1]))),
                batch_y_max_abs_error=float(np.max(np.abs(one[1]-y[:1]))))
        for k, entry in enumerate(batch):
            path = a.output/(entry['sample_id']+'.npz')
            np.savez_compressed(str(path), X=x[k], Y_float=y[k], logits=logits[k], audio=audio[k])
            artifacts.append(dict(sample_id=entry['sample_id'], path=path.name, sha256=sha(path)))
            for i in range(12):
                # Independent full float64 recomputation verifies orientation/capture.
                float64 = x[k, i].astype(np.float64) @ weights[i].astype(np.float64) + biases[i].astype(np.float64)
                np.testing.assert_allclose(y[k, i], float64, rtol=1e-4, atol=2e-5)
                q, integer, clipped = encode_arrays(x[k, i], weights[i], biases[i])
                metrics = error_metrics(decode(integer['result'], numeric_format()), y[k, i])
                tasks.append(dict(sample_id=entry['sample_id'], layer=i+1, **metrics,
                    clipped=clipped, output_saturated=int(integer['saturated'].sum()),
                    input_peak=float(np.max(np.abs(x[k, i]))), output_peak=float(np.max(np.abs(y[k, i]))),
                    float64_max_abs_error=float(np.max(np.abs(float64-y[k, i])))))
        save(a.output/'progress.json', dict(status='running', completed_samples=start+len(batch),
            task_count=len(tasks), elapsed_seconds=time.monotonic()-started))
        print('FULL_MATRIX_PROGRESS samples=%d/%d tasks=%d' % (start+len(batch), len(entries), len(tasks)), flush=True)
    if sources != check_sources(a.model_root, a.upstream_receipt) or any(sha(Path(__file__).with_name(n)) != h for n, h in code_hashes.items()):
        raise ValueError('Model/evaluation source changed during run')
    summary = aggregate_tasks(tasks)
    report = dict(**summary, dataset_kind='development', scope='software_integer_vs_float_full_matrices',
        full_600_coverage=len(entries) == 600, rtl_verified=False, cpu_executed=False,
        official_precision_verified=False, numeric_format=numeric_format(),
        clipping_totals={k: sum(t['clipped'][k] for t in tasks) for k in ('X', 'W', 'b')},
        output_saturated=sum(t['output_saturated'] for t in tasks), capture_check=capture_check,
        elapsed_seconds=time.monotonic()-started, tasks=tasks, sample_artifacts=artifacts,
        source_manifest_sha256=sha(a.output/'samples.json'), parameters_sha256=sha(a.output/'parameters.npz'),
        environment_sha256=sha(a.output/'environment.json'), code_sha256=code_hashes,
        largest_input_task=max(tasks, key=lambda t:t['input_peak']), largest_output_task=max(tasks, key=lambda t:t['output_peak']))
    save(a.output/'evaluation.json', report)
    save(a.output/'progress.json', dict(status='completed', threshold_passed=summary['threshold_passed'],
        completed_samples=len(entries), task_count=len(tasks), evaluation_sha256=sha(a.output/'evaluation.json')))
    print('FULL_MATRIX_FINISHED '+json.dumps({k:v for k,v in summary.items() if k not in ('layers', 'failing_tasks')}), flush=True)
    if not summary['threshold_passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
