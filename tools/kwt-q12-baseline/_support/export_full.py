"""Capture complete KWT-1 FFN1 matrices from unmodified official inference.

Python 3.8 / TensorFlow 2.4.0. Output directories must be new.
No training, quantization, synthetic silence, or accuracy claim is performed here.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import sys
from types import SimpleNamespace

os.environ.setdefault("CUDA_VISIBLE_DEVICES", "-1")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
sys.dont_write_bytecode = True


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def save_json(path, obj):
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", type=Path, required=True)
    p.add_argument("--audio", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--split", choices=["training", "validation", "testing"], default="validation")
    p.add_argument("--limit", type=int, default=1)
    p.add_argument("--sample", help="Optional word/file.wav within the chosen split")
    p.add_argument("--sample-list", type=Path, help="Ordered UTF-8 list of relative WAV paths")
    p.add_argument("--threads", type=int, default=4)
    args = p.parse_args()
    if args.limit < 1 or args.threads < 1:
        p.error("limit and threads must be positive")
    repo, audio, out = args.repo.resolve(), args.audio.resolve(), args.out.resolve()
    if out.exists():
        p.error("Output already exists; choose a new directory (no overwrite).")
    model_dir = repo / "models_data_v2_12_labels/kwt1"
    flags = json.loads((model_dir / "flags.json").read_text())
    if (flags["num_layers"], flags["d_model"], flags["mlp_dim"]) != (12, 64, 256):
        raise ValueError("Not the required KWT-1 model")
    valid = set((audio / "validation_list.txt").read_text().splitlines())
    testing = set((audio / "testing_list.txt").read_text().splitlines())
    if args.split == "validation":
        samples = sorted(valid)
    elif args.split == "testing":
        samples = sorted(testing)
    else:
        samples = sorted(p.relative_to(audio).as_posix() for p in audio.glob("*/*.wav")
                         if p.parent.name != "_background_noise_"
                         and p.relative_to(audio).as_posix() not in valid | testing)
    if args.sample and args.sample_list:
        p.error("Use only one of sample or sample-list")
    if args.sample_list:
        chosen = args.sample_list.read_text(encoding="utf-8-sig").splitlines()
        if len(chosen) != len(set(chosen)) or not chosen or any(n not in samples for n in chosen):
            raise ValueError("Sample list contains duplicates or entries outside the chosen split")
        samples = chosen
    if args.sample:
        if args.sample not in samples:
            raise ValueError("Requested sample not in selected split")
        samples = [args.sample]
    samples = samples[:args.limit]
    if not samples:
        raise ValueError("No input samples")
    for name in samples:
        (audio / name).resolve().relative_to(audio)
        if not (audio / name).is_file():
            raise FileNotFoundError(name)

    sys.path.insert(0, str(repo))
    import numpy as np
    import tensorflow as tf
    import tensorflow_addons as tfa
    from kws_streaming.models import models
    from kws_streaming.models.transformer_utils import KWSTransformer
    # Upstream input_data disables eager execution during import.
    tf.compat.v1.enable_eager_execution()
    tf.config.threading.set_intra_op_parallelism_threads(args.threads)
    tf.config.threading.set_inter_op_parallelism_threads(1)
    tf.keras.backend.clear_session()
    tf.keras.backend.set_learning_phase(0)
    tf.random.set_seed(20261108)
    overrides = dict(batch_size=1, training=False, train=0, distill_teacher_json="",
                     prenorm=False, approximate_gelu=False, use_spec_augment=0,
                     use_spec_cutout=0, time_shift_ms=0., sp_time_shift_ms=0.,
                     resample=0., sp_resample=0., volume_resample=0.,
                     background_volume=0., background_frequency=0.)
    flags.update(overrides)
    model = models.MODELS["kws_transformer"](SimpleNamespace(**flags))
    status = model.load_weights(str(model_dir / "best_weights"))
    status.assert_existing_objects_matched()
    status.expect_partial()  # training checkpoint can retain optimizer state
    transformers = [layer for layer in model.layers if isinstance(layer, KWSTransformer)]
    if len(transformers) != 1 or len(transformers[0].enc_layers) != 12:
        raise ValueError("Expected exactly one 12-layer transformer")
    blocks = transformers[0].enc_layers
    # Old Sequential checkpoint aliases emit warnings in TF 2.4. Verify all
    # actual variables byte-for-byte, rather than relying on expect_partial.
    reader = tf.train.load_checkpoint(str(model_dir / "best_weights"))
    checked_weights = []

    def check(variable, key):
        key += "/.ATTRIBUTES/VARIABLE_VALUE"
        np.testing.assert_array_equal(variable.numpy(), reader.get_tensor(key))
        checked_weights.append(dict(variable=variable.name, checkpoint_key=key, shape=list(variable.shape)))

    transformer = transformers[0]
    prefix = "layer_with_weights-0/"
    for name in ("pos_emb", "class_emb"):
        check(getattr(transformer, name), prefix + name)
    for name in ("kernel", "bias"):
        check(getattr(transformer.patch_proj, name), prefix + "patch_proj/" + name)
    for index, block in enumerate(blocks):
        base = prefix + "enc_layers/%d/" % index
        for name in ("query_dense", "key_dense", "value_dense", "combine_heads"):
            dense = getattr(block.att, name)
            check(dense.kernel, base + "att/" + name + "/kernel")
            if dense.use_bias:
                check(dense.bias, base + "att/" + name + "/bias")
        for wi, li in enumerate((0, 2)):
            for name in ("kernel", "bias"):
                check(getattr(block.ffn.layers[li], name), base + "ffn/layer_with_weights-%d/" % wi + name)
        for ln in ("layernorm1", "layernorm2"):
            for name in ("gamma", "beta"):
                check(getattr(getattr(block, ln), name), base + ln + "/" + name)
    for name in ("kernel", "bias"):
        check(getattr(model.layers[-1].layers[0], name), "layer_with_weights-1/layer_with_weights-0/" + name)
    if len(checked_weights) != len(model.weights) or model.count_params() != 607308:
        raise ValueError("Not every official model weight was verified")
    print("Verified %d variables against official checkpoint" % len(checked_weights), flush=True)
    w = np.stack([b.ffn.layers[0].kernel.numpy() for b in blocks])
    bias = np.stack([b.ffn.layers[0].bias.numpy() for b in blocks])
    assert w.shape == (12, 64, 256) and bias.shape == (12, 256)
    assert np.isfinite(w).all() and np.isfinite(bias).all()
    captures, original_calls = {}, []
    for index, block in enumerate(blocks):
        dense = block.ffn.layers[0]
        original = dense.call
        original_calls.append((dense, original))

        def capture(inputs, original=original, index=index):
            output = original(inputs)
            captures[index] = (inputs, output)
            return output

        dense.call = capture

    @tf.function(input_signature=[tf.TensorSpec([1, 16000], tf.float32)], autograph=False)
    def infer(wav):
        logits = model(wav, training=False)
        return (tf.stack([captures[i][0] for i in range(12)]),
                tf.stack([captures[i][1] for i in range(12)]), logits)

    concrete = infer.get_concrete_function()
    for dense, original in original_calls:
        dense.call = original
    out.mkdir(parents=True)
    np.savez_compressed(str(out / "shared_weights.npz"), W=w, b=bias)
    with np.load(str(out / "shared_weights.npz"), allow_pickle=False) as saved:
        assert np.array_equal(w, saved["W"]) and np.array_equal(bias, saved["b"])
    records = []
    labels = (model_dir / "labels.txt").read_text().splitlines()
    wanted = flags["wanted_words"].split(",")
    for index, name in enumerate(samples, 1):
        wav_path = audio / name
        wav, rate = tf.audio.decode_wav(tf.io.read_file(str(wav_path)),
                                        desired_channels=1, desired_samples=16000)
        if int(rate.numpy()) != 16000:
            raise ValueError("Audio sample rate must be 16000 Hz")
        x_tf, y_tf, logits = concrete(tf.reshape(wav, [1, 16000]))
        x, y = x_tf.numpy()[:, 0], y_tf.numpy()[:, 0]
        logits = np.asarray(logits[0] if isinstance(logits, (list, tuple)) else logits)
        baseline = model(tf.reshape(wav, [1, 16000]), training=False)
        baseline = np.asarray(baseline[0] if isinstance(baseline, (list, tuple)) else baseline)
        if not np.allclose(logits, baseline, atol=5e-5, rtol=5e-6):
            raise ValueError("Capture changed model outputs versus uninstrumented inference")
        assert x.shape == (12, 99, 64) and y.shape == (12, 99, 256)
        assert np.isfinite(x).all() and np.isfinite(y).all() and np.isfinite(logits).all()
        ref = x.astype(np.float64) @ w.astype(np.float64) + bias.astype(np.float64)[:, None, :]
        err = np.abs(y.astype(np.float64) - ref)
        tolerance = 5e-5 + 5e-6 * np.abs(ref)
        bad = np.count_nonzero(err > tolerance, axis=(1, 2))
        if bad.any():
            raise ValueError("Full float matrix consistency failed: " + str(bad))
        folder = out / ("sample_%06d" % index)
        folder.mkdir()
        np.savez_compressed(str(folder / "float_tensors.npz"), X=x, Y=y, logits=logits)
        with np.load(str(folder / "float_tensors.npz"), allow_pickle=False) as saved:
            assert np.array_equal(saved["X"], x) and np.array_equal(saved["Y"], y)
        record = dict(sample=index, wav=name, wav_sha256=sha(wav_path),
                      source_word=name.split("/")[0],
                      mapped_label=name.split("/")[0] if name.split("/")[0] in wanted else "_unknown_",
                      file="sample_%06d/float_tensors.npz" % index,
                      sha256=sha(folder / "float_tensors.npz"), outputs_checked=304128,
                      per_layer_outputs=[25344] * 12,
                      capture_vs_baseline_logits_max_abs_error=float(np.abs(logits - baseline).max()),
                      float_max_abs_error=err.max(axis=(1, 2)).tolist(),
                      float_out_of_tolerance=bad.tolist())
        records.append(record)
        save_json(folder / "record.json", record)
        print("PASS %d/%d %s: all 304128 float outputs checked" % (index, len(samples), name), flush=True)
    source_paths = sorted((repo / "kws_streaming").rglob("*.py"))
    source_paths += sorted(model_dir.glob("best_weights*"))
    source_paths += [model_dir / "flags.json", model_dir / "labels.txt"]
    manifest = dict(schema="kwt1-full-ffn1-float-v1", status="passed", split=args.split,
                    batch_size=1, layer_numbers=list(range(1, 13)),
                    shapes=dict(X=[12, 99, 64], W=[12, 64, 256], b=[12, 256], Y=[12, 99, 256]),
                    dtype="float32", capture="FFN first Dense input after layernorm1; output before GELU",
                    independent_float_reference="float64 X@W+b; abs_error <= 5e-5 + 5e-6*abs(reference)",
                    python=platform.python_version(), tensorflow=tf.__version__, numpy=np.__version__,
                    tensorflow_addons=tfa.__version__, inference_overrides=overrides,
                    selection_list_sha256=sha(args.sample_list) if args.sample_list else None,
                    labels=labels,
                    checkpoint_variables_checked=checked_weights,
                    version_note="Upstream asks TF 2.4.0rc1; this run uses TF 2.4.0 stable because rc1 was unavailable.",
                    repo=str(repo), audio=str(audio), exporter_sha256=sha(__file__),
                    source_sha256={str(p.relative_to(repo)).replace('\\', '/'): sha(p) for p in source_paths},
                    shared_weights_sha256=sha(out / "shared_weights.npz"), samples=records,
                    total_outputs_checked=len(samples) * 304128,
                    limitation="Raw utterance selection, not official balanced 12-class evaluation; no synthetic silence; no RTL or classification accuracy validation.")
    save_json(out / "manifest.json", manifest)
    print("Complete: " + str(out), flush=True)


if __name__ == "__main__":
    main()
