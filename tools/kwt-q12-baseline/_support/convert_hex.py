"""Convert full float archive to Q12 arch02 tasks; independently decode every HEX.

This Q12 format is an engineering baseline, not a competition-mandated precision.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import numpy as np
from check_hex import validate_layer, sha256, read_words, decode_load


def quantize(a, fractional, bits):
    scaled = a.astype(np.float64) * (1 << fractional)
    fraction, integral = np.modf(np.abs(scaled))
    rounded = np.copysign(integral + (fraction >= .5), scaled)
    clipped = np.clip(rounded, -(1 << (bits - 1)), (1 << (bits - 1)) - 1)
    return clipped.astype(np.int64), int(np.count_nonzero(rounded != clipped))


def write_hex(path, values, bits):
    mask, width = (1 << bits) - 1, (bits + 3) // 4
    with path.open("w", encoding="ascii", newline="\n") as f:
        f.writelines(format(int(v) & mask, "0%dx" % width) + "\n" for v in np.asarray(values).flat)


def save(path, value):
    path.write_text(json.dumps(value, indent=2), encoding="utf-8")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    tool_dir = Path(__file__).resolve().parent
    protocol = json.loads((tool_dir / "rtl_protocol.json").read_text())
    for entry in protocol["files"]:
        raw = (tool_dir / entry["local_path"]).read_bytes()
        blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        if blob != entry["git_blob"]:
            raise ValueError("Pinned Git source changed: " + entry["local_path"])
    upstream_path = tool_dir / "protocol_source/arch02/scripts/data.py"
    spec = importlib.util.spec_from_file_location("pinned_arch02_data", str(upstream_path))
    upstream = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(upstream)
    from verify_real_hex import quantize as exact_quantize

    def check_quantization(floats, integers, fractional, bits):
        exact = np.fromiter((exact_quantize(v, fractional, bits) for v in floats.flat),
                            dtype=np.int64, count=floats.size).reshape(floats.shape)
        if not np.array_equal(exact, integers):
            raise ValueError("Quantization differs from pinned repository rational reference")
    if a.out.exists():
        p.error("Output already exists; choose a new directory")
    m = json.loads((a.input / "manifest.json").read_text(encoding="utf-8"))
    if m["schema"] != "kwt1-full-ffn1-float-v1" or m["status"] != "passed":
        raise ValueError("Expected validated full float archive")
    if sha256(a.input / "shared_weights.npz") != m["shared_weights_sha256"]:
        raise ValueError("Weight hash mismatch")
    with np.load(str(a.input / "shared_weights.npz"), allow_pickle=False) as weights:
        w_all, b_all = weights["W"], weights["b"]
    assert w_all.shape == (12, 64, 256) and b_all.shape == (12, 256)
    wq, _ = quantize(w_all, 12, 16)
    bq, _ = quantize(b_all, 24, 40)
    check_quantization(w_all, wq, 12, 16)
    check_quantization(b_all, bq, 24, 40)
    a.out.mkdir(parents=True)
    reports = []
    error_sums = np.zeros(12, dtype=np.float64)
    reference_sums = np.zeros(12, dtype=np.float64)
    task_threshold_failures = 0
    for sample in m["samples"]:
        source = (a.input / sample["file"]).resolve()
        source.relative_to(a.input.resolve())
        if sha256(source) != sample["sha256"]:
            raise ValueError("Sample hash mismatch")
        with np.load(str(source), allow_pickle=False) as data:
            x_all, y_all = data["X"], data["Y"]
        assert x_all.shape == (12, 99, 64) and y_all.shape == (12, 99, 256)
        sample_reports = []
        for layer in range(12):
            x, xc = quantize(x_all[layer], 12, 16)
            w, wc = quantize(w_all[layer], 12, 16)
            b, bc = quantize(b_all[layer], 24, 40)
            check_quantization(x_all[layer], x, 12, 16)
            total = x @ w + b
            assert np.all(total >= -(1 << 40)) and np.all(total < (1 << 40))
            q, r = np.divmod(np.abs(total), 4096)
            rounded = np.where(total < 0, -1, 1) * (q + (r >= 2048))
            result = np.clip(rounded, -32768, 32767)
            saturated = (rounded != result).astype(np.int64)
            expected = dict(total=total, result=result, saturated=saturated)
            upstream_expected = upstream.reference(x, w, b, 12)
            for key in expected:
                if not np.array_equal(expected[key], upstream_expected[key]):
                    raise ValueError("Pinned repository numerical reference mismatch: " + key)
            folder = a.out / ("sample_%06d" % sample["sample"]) / ("layer_%02d" % (layer + 1))
            folder.mkdir(parents=True)
            words = [int(v) & 65535 for v in x.flat]
            for group in range(32):
                words.extend(int(w[k, group*8+lane]) & 65535 for k in range(64) for lane in range(8))
                for lane in range(8):
                    value = int(b[group*8+lane]) & ((1 << 40) - 1)
                    words.extend((value >> shift) & 65535 for shift in (0, 16, 32))
            assert len(words) == 23488
            write_hex(folder / "load.hex", words, 16)
            for name, bits in (("total", 41), ("result", 16), ("saturated", 1)):
                write_hex(folder / (name + ".hex"), expected[name], bits)
            np.savez_compressed(str(folder / "expected.npz"), **expected)
            hashes = {f.name: sha256(f) for f in folder.iterdir()}
            save(folder / "layout.json", dict(schema="arch02-hex-v1", shift=12,
                 load_words=23488, outputs=25344, kind="real", layer_number=layer+1, sha256=hashes))
            decoded = decode_load(read_words(folder / "load.hex", 16, 23488))
            for actual, wanted in zip(decoded, (x, w, b)):
                if not np.array_equal(actual, wanted):
                    raise ValueError("HEX differs from quantized source")
            audit = validate_layer(folder, expected_layer=layer+1)
            error = result / 4096. - y_all[layer].astype(np.float64)
            error_sum = float(np.sum(error**2))
            reference_sum = float(np.sum(y_all[layer].astype(np.float64)**2))
            nrmse = float(np.sqrt(error_sum / 25344) / max(np.sqrt(reference_sum / 25344), 1e-8))
            error_sums[layer] += error_sum
            reference_sums[layer] += reference_sum
            task_threshold_failures += int(nrmse > .03)
            audit.update(input_clipped=xc, weight_clipped=wc, bias_clipped=bc,
                         output_saturated=int(saturated.sum()),
                         nrmse=nrmse, nrmse_percent=nrmse*100,
                         error_squared_sum=error_sum, float_reference_squared_sum=reference_sum,
                         pinned_repository_quantization_and_reference="matched",
                         quantized_vs_float_max_abs_error=float(np.abs(error).max()),
                         quantized_vs_float_rmse=float(np.sqrt(np.mean(error**2))))
            save(folder / "hex_check.json", audit)
            sample_reports.append(audit)
        reports.append(dict(sample=sample["sample"], wav=sample["wav"], layers=sample_reports))
        print("PASS sample %d: 304128 integer outputs; all HEX independently decoded" % sample["sample"], flush=True)
    elements_per_layer = len(reports) * 25344
    layer_nrmse = np.sqrt(error_sums / elements_per_layer) / np.maximum(np.sqrt(reference_sums / elements_per_layer), 1e-8)
    save(a.out / "manifest.json", dict(schema="kwt1-full-arch02-q12-v1", status="passed",
         rtl_repository=protocol["repository"], rtl_commit=protocol["commit"], rtl_path=protocol["development_path"],
         protocol_sha256=sha256(tool_dir / "rtl_protocol.json"),
         float_manifest_sha256=sha256(a.input / "manifest.json"),
         converter_sha256=sha256(__file__), checker_sha256=sha256(Path(__file__).with_name("check_hex.py")),
         numeric_format=dict(input="signed16 Q12", weight="signed16 Q12", bias="signed40 Q24",
                             total="signed41 Q24", result="signed16 Q12", rounding="nearest, ties away from zero", saturation=True),
         total_outputs_checked=len(reports)*304128, samples=reports,
         aggregate_layer_nrmse=layer_nrmse.tolist(), aggregate_max_nrmse_percent=float(layer_nrmse.max()*100),
         individual_tasks_above_3_percent=task_threshold_failures,
         limitation="Software checks only. No RTL simulation, official accuracy evaluation, or SRAM/bus execution in this run."))


if __name__ == "__main__":
    main()
