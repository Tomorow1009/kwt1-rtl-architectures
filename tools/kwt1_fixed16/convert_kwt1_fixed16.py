"""Bit-exact, transaction-level model of arch02 FFN1 (Python 3.6+, NumPy).

Fixed RTL widths: X/W/result signed16, accumulator/bias signed40, total signed41.
The frozen float encoding is F_x=12, F_w=16, F_y=12. No TensorFlow is needed here.
This is a numerical model, not a clock/bus/SRAM timing simulator.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

import numpy as np

ROWS, INNER, COLUMNS, LAYERS = 99, 64, 256, 12
LOAD_WORDS, OUTPUTS = 23488, 25344
RTL_COMMIT = "8aa230695668458673b370bf85f8a397fc507a34"
DEFAULT_FORMAT = {"fx": 12, "fw": 16, "fy": 12}


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def save_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False,
                                     allow_nan=False) + "\n", encoding="utf-8")


def _integer(value, name, low, high):
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer)):
        raise ValueError(name + " must be an integer")
    value = int(value)
    if not low <= value <= high:
        raise ValueError("{} must be in {}..{}".format(name, low, high))
    return value


def validate_format(fmt=None):
    fmt = dict(DEFAULT_FORMAT if fmt is None else fmt)
    if set(fmt) != {"fx", "fw", "fy"}:
        raise ValueError("Format must contain exactly fx, fw, fy; RTL widths are fixed")
    fmt = {k: _integer(v, k, 0, 31) for k, v in fmt.items()}
    _integer(fmt["fx"] + fmt["fw"] - fmt["fy"], "shift", 0, 31)
    return fmt


def load_formats(path=None):
    if path is None:
        return [dict(DEFAULT_FORMAT) for _ in range(LAYERS)]
    obj = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if obj.get("schema") != "arch02-fixed-width-format-v1":
        raise ValueError("Unsupported format schema")
    widths = {"x": 16, "w": 16, "bias": 40, "accumulator": 40, "total": 41, "result": 16}
    if obj.get("widths") != widths:
        raise ValueError("This model implements the current fixed-width RTL only")
    layers = obj.get("layers")
    if not isinstance(layers, list) or len(layers) != LAYERS:
        raise ValueError("Expected exactly 12 ordered layer formats")
    result = []
    for i, layer in enumerate(layers, 1):
        if set(layer) != {"layer", "fx", "fw", "fy"} or type(layer["layer"]) is not int or layer["layer"] != i:
            raise ValueError("Invalid/missing/duplicate layer format")
        result.append(validate_format({k: layer[k] for k in ("fx", "fw", "fy")}))
    return result


def _signed_array(values, bits, name, shape=None):
    a = np.asarray(values)
    if a.dtype.kind not in "iu" or (shape is not None and a.shape != shape):
        raise ValueError("{} must be an integer array of shape {}".format(name, shape))
    lo, hi = -(1 << (bits - 1)), (1 << (bits - 1)) - 1
    # Check uint64 before int64 conversion, so large unsigned values cannot wrap.
    if a.size and (int(a.min()) < lo or int(a.max()) > hi):
        raise ValueError("{} is outside signed{}".format(name, bits))
    return a.astype(np.int64, copy=False)


def _float_array(values, name, shape=None):
    a = np.asarray(values)
    if a.dtype.kind not in "fiu" or (shape is not None and a.shape != shape):
        raise ValueError("{} must be a real array of shape {}".format(name, shape))
    a = a.astype(np.float64)
    if not np.isfinite(a).all():
        raise ValueError(name + " contains NaN or infinity")
    return a


def quantize(values, fractional, bits):
    """Encode finite host floats: round nearest/ties away, then signed saturation.

    Power-of-two scaling is exact for binary floating point in the relevant
    range. Splitting integer/fraction avoids floor(abs(x)+0.5)'s tie-neighbor bug.
    Count clipping after rounding, matching the existing conversion protocol.
    """
    fractional = _integer(fractional, "fractional", 0, 62)
    bits = _integer(bits, "bits", 2, 40)
    a = _float_array(values, "quantize input")
    lo, hi = -(1 << (bits - 1)), (1 << (bits - 1)) - 1
    with np.errstate(over="ignore"):
        scaled = np.ldexp(a, fractional)
    # Values beyond these caps inevitably saturate; cap before modf/int casting.
    capped = np.clip(scaled, lo - 1, hi + 1)
    fraction, integral = np.modf(np.abs(capped))
    rounded = np.copysign(integral + (fraction >= 0.5), capped)
    encoded = np.clip(rounded, lo, hi).astype(np.int64)
    return encoded, int(np.count_nonzero(rounded != encoded))


def requantize(total, shift=12):
    """Exact combinational requantize.sv, including signed41 minimum and shift=0."""
    shift = _integer(shift, "shift", 0, 31)
    total = _signed_array(total, 41, "total")
    magnitude = np.abs(total)  # int64 safely contains abs(-2**40)
    if shift:
        magnitude = (magnitude + (1 << (shift - 1))) >> shift
    rounded = np.where(total < 0, -magnitude, magnitude)
    result = np.clip(rounded, -32768, 32767)
    return result, (result != rounded).astype(np.int64)


def dot64_int(x, w, bias=0, shift=12):
    """One accepted 64-element dot64 transaction; returns plain integer fields."""
    x = _signed_array(x, 16, "x", (64,))
    w = _signed_array(w, 16, "w", (64,))
    bias = _integer(bias, "bias", -(1 << 39), (1 << 39) - 1)
    shift = _integer(shift, "shift", 0, 31)
    # Any prefix of 64 signed16 products fits signed38, so accumulator40
    # wrapping is impossible for all legal inputs, not just observed speech.
    accumulator = int(np.dot(x, w))
    total = accumulator + bias
    result, saturated = requantize(np.array(total, dtype=np.int64), shift)
    return dict(accumulator=accumulator, total=total,
                result=int(result), saturated=int(saturated))


def ffn1_int(x, w, bias, shift=12):
    """One full FFN1 task; all result arrays are indexed [row, column]."""
    x = _signed_array(x, 16, "X", (ROWS, INNER))
    w = _signed_array(w, 16, "W", (INNER, COLUMNS))
    bias = _signed_array(bias, 40, "bias", (COLUMNS,))
    shift = _integer(shift, "shift", 0, 31)
    # int64 multiplication/accumulation is exact here: 64*2**30 plus bias40.
    accumulator = x @ w
    total = accumulator + bias[np.newaxis, :]
    result, saturated = requantize(total, shift)
    return dict(accumulator=accumulator, total=total, result=result, saturated=saturated)


def ffn1_float(x, w, bias, fmt=None):
    """Float FFN1 tensors -> same quantization/arithmetic as the current RTL.

    y_float is decoded fixed-point result, not the official float32 Dense output.
    """
    fmt = validate_format(fmt)
    x = _float_array(x, "X", (ROWS, INNER))
    w = _float_array(w, "W", (INNER, COLUMNS))
    bias = _float_array(bias, "bias", (COLUMNS,))
    xq, xc = quantize(x, fmt["fx"], 16)
    wq, wc = quantize(w, fmt["fw"], 16)
    bq, bc = quantize(bias, fmt["fx"] + fmt["fw"], 40)
    shift = fmt["fx"] + fmt["fw"] - fmt["fy"]
    result = ffn1_int(xq, wq, bq, shift)
    result.update(x_int=xq, w_int=wq, bias_int=bq,
                  y_float=np.ldexp(result["result"].astype(np.float64), -fmt["fy"]),
                  clipping=dict(x=xc, w=wc, bias=bc), format=fmt, shift=shift)
    return result


def run12_float(x, w, bias, formats=None):
    """12 independently captured FFN1 tasks; this does not chain encoder blocks."""
    x = _float_array(x, "X", (LAYERS, ROWS, INNER))
    w = _float_array(w, "W", (LAYERS, INNER, COLUMNS))
    bias = _float_array(bias, "bias", (LAYERS, COLUMNS))
    formats = load_formats() if formats is None else formats
    if len(formats) != LAYERS:
        raise ValueError("Expected 12 formats")
    parts = [ffn1_float(x[i], w[i], bias[i], formats[i]) for i in range(LAYERS)]
    keys = ("accumulator", "total", "result", "saturated", "y_float")
    out = {k: np.stack([p[k] for p in parts]) for k in keys}
    out["layers"] = [dict(layer=i+1, format=p["format"], shift=p["shift"],
                          clipping=p["clipping"], output_saturated=int(p["saturated"].sum()))
                     for i, p in enumerate(parts)]
    return out


def pack_load(x, w, bias):
    x = _signed_array(x, 16, "X", (ROWS, INNER))
    w = _signed_array(w, 16, "W", (INNER, COLUMNS))
    bias = _signed_array(bias, 40, "bias", (COLUMNS,))
    words = [int(v) & 65535 for v in x.flat]
    for group in range(32):
        words.extend(int(w[k, group*8+lane]) & 65535 for k in range(64) for lane in range(8))
        for lane in range(8):
            value = int(bias[group*8+lane]) & ((1 << 40) - 1)
            words.extend((value >> shift) & 65535 for shift in (0, 16, 32))
    return np.array(words, dtype=np.int64)


def unpack_load(words):
    words = np.asarray(words)
    if words.shape != (LOAD_WORDS,) or words.dtype.kind not in "iu":
        raise ValueError("Expected 23488 integer load words")
    if int(words.min()) < 0 or int(words.max()) > 65535:
        raise ValueError("Each load word must fit unsigned16")
    words = words.astype(np.int64)
    x = words[:6336].reshape(ROWS, INNER).copy()
    x[x >= 32768] -= 65536
    w, bias = np.empty((INNER, COLUMNS), dtype=np.int64), np.empty(COLUMNS, dtype=np.int64)
    for group in range(32):
        start = 6336 + group * 536
        bank = words[start:start+512].reshape(64, 8).copy()
        bank[bank >= 32768] -= 65536
        w[:, group*8:group*8+8] = bank
        for lane in range(8):
            at = start + 512 + lane*3
            low, middle, high = (int(v) for v in words[at:at+3])
            if high > 255:
                raise ValueError("Illegal bias high-byte padding at group {}, lane {}".format(group, lane))
            value = low | (middle << 16) | (high << 32)
            bias[group*8+lane] = value - (1 << 40) if value & (1 << 39) else value
    return x, w, bias


def read_hex(path, bits, count, signed=False):
    lines = Path(path).read_text(encoding="ascii").splitlines()
    if len(lines) != count:
        raise ValueError("{}: expected {} lines, got {}".format(path, count, len(lines)))
    pattern = re.compile(r"[0-9a-fA-F]{%d}\Z" % ((bits+3)//4))
    out = np.empty(count, dtype=np.int64)
    for i, line in enumerate(lines):
        if not pattern.fullmatch(line):
            raise ValueError("{}:{}: malformed HEX".format(path, i+1))
        value = int(line, 16)
        if value >= 1 << bits:
            raise ValueError("{}:{}: nonzero reserved high bits".format(path, i+1))
        out[i] = value - (1 << bits) if signed and value & (1 << (bits-1)) else value
    return out


def write_hex(path, values, bits):
    mask, width = (1 << bits) - 1, (bits+3)//4
    with Path(path).open("x", encoding="ascii", newline="\n") as handle:
        for value in np.asarray(values).flat:
            handle.write(format(int(value) & mask, "0%dx" % width) + "\n")


def stream_coordinates():
    return np.array([row*COLUMNS + group*8 + lane
                     for group in range(32) for row in range(ROWS) for lane in range(8)], dtype=np.int64)


def check_capture(path, expected):
    actual = np.loadtxt(str(path), delimiter=",", dtype=np.int64, ndmin=2)
    if actual.shape != (OUTPUTS, 4):
        raise ValueError("Capture must contain 25344 rows of coordinate,total,result,saturated")
    if not np.array_equal(np.sort(actual[:, 0]), np.arange(OUTPUTS)):
        raise ValueError("Missing, duplicate, or invalid output coordinate")
    if not np.array_equal(actual[:, 0], stream_coordinates()):
        raise ValueError("Unexpected RTL output sequence")
    actual = actual[np.argsort(actual[:, 0])]
    for i, key in enumerate(("total", "result", "saturated"), 1):
        if not np.array_equal(actual[:, i], expected[key].ravel()):
            raise ValueError("RTL capture mismatch in " + key)
    return dict(outputs=OUTPUTS, mismatches=0, capture_sha256=sha256(path))


def check_hex_task(folder, shift=None):
    folder = Path(folder)
    layout_path = folder / "layout.json"
    if layout_path.exists():
        layout = json.loads(layout_path.read_text(encoding="utf-8-sig"))
        if layout.get("load_words") != LOAD_WORDS or layout.get("outputs") != OUTPUTS:
            raise ValueError("Bad layout counts")
        recorded_shift = _integer(layout.get("shift"), "layout shift", 0, 31)
        if shift is not None and shift != recorded_shift:
            raise ValueError("Requested shift disagrees with layout.json")
        shift = recorded_shift
        digests = layout.get("sha256")
        required = {"load.hex", "total.hex", "result.hex", "saturated.hex"}
        if not isinstance(digests, dict) or not required.issubset(digests):
            raise ValueError("Missing HEX hashes in layout.json")
        for name, digest in digests.items():
            if Path(name).name != name or name in (".", "..") or not re.fullmatch(r"[0-9a-f]{64}", str(digest)):
                raise ValueError("Invalid layout file or hash")
            if sha256(folder / name) != digest:
                raise ValueError("Hash mismatch: " + name)
    elif shift is None:
        raise ValueError("Supply --shift when layout.json is absent")
    x, w, bias = unpack_load(read_hex(folder / "load.hex", 16, LOAD_WORDS))
    result = ffn1_int(x, w, bias, shift)
    for key, bits, signed in (("total", 41, True), ("result", 16, True), ("saturated", 1, False)):
        actual = read_hex(folder / (key + ".hex"), bits, OUTPUTS, signed).reshape(ROWS, COLUMNS)
        if not np.array_equal(actual, result[key]):
            raise ValueError("Reference HEX mismatch in " + key)
    return dict(status="passed", outputs=OUTPUTS, mismatches=0, shift=shift,
                output_saturated=int(result["saturated"].sum()), load_sha256=sha256(folder / "load.hex"))


def error_metrics(decoded, reference):
    decoded, reference = _float_array(decoded, "decoded"), _float_array(reference, "reference")
    if decoded.shape != reference.shape or not decoded.size:
        raise ValueError("Error metrics require equal nonempty shapes")
    delta = decoded - reference
    sse = float(np.sum(delta*delta))
    ssr = float(np.sum(reference*reference))
    n = decoded.size
    nrmse = float(np.sqrt(sse/n) / max(np.sqrt(ssr/n), 1e-8))
    return dict(outputs=n, error_squared_sum=sse, reference_squared_sum=ssr,
                nrmse_percent=100*nrmse, max_abs_error=float(np.max(np.abs(delta))))


# Self-contained numerical implementation; no companion Python file needed.
numeric = sys.modules[__name__]

def export_layer(folder,x,w,bias,fmt,layer,reference=None):
    folder = Path(folder)
    folder.mkdir(parents=True,exist_ok=False)
    result = numeric.ffn1_float(x,w,bias,fmt)
    numeric.write_hex(folder / "load.hex",numeric.pack_load(result["x_int"],result["w_int"],result["bias_int"]),16)
    for key,bits in (("total",41),("result",16),("saturated",1)):
        numeric.write_hex(folder / (key+".hex"),result[key],bits)
    np.savez_compressed(str(folder / "expected.npz"),**{k:result[k] for k in ("total","result","saturated")})
    hashes = {p.name:numeric.sha256(p) for p in folder.iterdir()}
    layout = dict(schema="arch02-hex-v1",layer_number=layer,kind="real",shift=result["shift"],
                  load_words=23488,outputs=25344,format=fmt,bias_fraction=fmt["fx"]+fmt["fw"],
                  result_fraction=fmt["fy"],sha256=hashes)
    numeric.save_json(folder / "layout.json",layout)
    audit = numeric.check_hex_task(folder,result["shift"])
    audit.update(clipping=result["clipping"],format=fmt,layer_number=layer)
    if reference is not None:
        audit["error"] = numeric.error_metrics(result["y_float"],reference)
    numeric.save_json(folder / "hex_check.json",audit)
    return result,audit



def convert_sample(sample, weights, out):
    sample, weights, out = Path(sample), Path(weights), Path(out)
    if out.exists():
        raise ValueError("Output exists; choose a NEW directory")
    with np.load(str(sample), allow_pickle=False) as data:
        x = _float_array(data["X"], "X", (12,99,64))
        y = _float_array(data["Y"], "Y", (12,99,256)) if "Y" in data else None
    with np.load(str(weights), allow_pickle=False) as data:
        w = _float_array(data["W"], "W", (12,64,256))
        b = _float_array(data["b"], "b", (12,256))
    out.mkdir(parents=True)
    reports = []
    for i in range(12):
        _, report = export_layer(out / ("layer_%02d" % (i+1)), x[i], w[i], b[i],
                                 dict(DEFAULT_FORMAT), i+1, None if y is None else y[i])
        reports.append(report)
    manifest = dict(status="passed", schema="kwt1-fixed16-conversion-v2", layers=reports,
        outputs=304128, shift=16, format=DEFAULT_FORMAT, bias_fraction=28,
        sample_sha256=sha256(sample), weights_sha256=sha256(weights),
        converter_sha256=sha256(__file__), rtl_commit=RTL_COMMIT,
        software_hex_check_only=True)
    save_json(out / "manifest.json", manifest)
    return manifest


def converter_main():
    p = argparse.ArgumentParser(description="Frozen KWT-1 FFN1 converter: X16/F12 W16/F16 b40/F28 Y16/F12 SHIFT=16")
    p.add_argument("--sample", type=Path, required=True, help="Complete float NPZ: X[12,99,64], optional Y[12,99,256]")
    p.add_argument("--weights", type=Path, required=True, help="Shared float NPZ: W[12,64,256], b[12,256]")
    p.add_argument("--out", type=Path, required=True, help="New output directory; overwriting refused")
    a = p.parse_args()
    try:
        convert_sample(a.sample, a.weights, a.out)
    except (OSError, ValueError, KeyError) as exc:
        print("FAIL: " + str(exc), file=sys.stderr)
        return 1
    print("PASS: 12 layers, 304128 outputs; use +SHIFT=16", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(converter_main())
