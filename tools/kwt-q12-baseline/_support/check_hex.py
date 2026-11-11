"""Independently decode and recompute an architecture-2 HEX task (Python 3.6+)."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

import numpy as np


HEX_FILES = {"load.hex": (16, 23488), "total.hex": (41, 25344),
             "result.hex": (16, 25344), "saturated.hex": (1, 25344)}


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_words(path, bits, count, signed=False):
    """Reject permissive readmemh constructs, bad padding, and extra words."""
    path = Path(path)
    try:
        lines = path.read_bytes().decode("ascii").splitlines()
    except (OSError, UnicodeError) as exc:
        raise ValueError("{}: unreadable ASCII HEX: {}".format(path.name, exc))
    if len(lines) != count:
        raise ValueError("{}: expected {} lines, got {}".format(path.name, count, len(lines)))
    width = (bits + 3) // 4
    pattern = re.compile(r"[0-9a-fA-F]{%d}\Z" % width)
    words = np.empty(count, dtype=np.int64)
    for index, line in enumerate(lines):
        if not pattern.fullmatch(line):
            raise ValueError("{}:{}: expected exactly {} HEX digits".format(path.name, index + 1, width))
        value = int(line, 16)
        if value >= (1 << bits):
            raise ValueError("{}:{}: nonzero reserved high bits".format(path.name, index + 1))
        if signed and value & (1 << (bits - 1)):
            value -= 1 << bits
        words[index] = value
    return words


def decode_load(words):
    """Use bank addresses to rebuild complete row-major X, W, and bias."""
    if len(words) != 23488:
        raise ValueError("load word count")
    x = words[:6336].reshape(99, 64).copy()
    x[x >= 32768] -= 65536
    w = np.empty((64, 256), dtype=np.int64)
    bias = np.empty(256, dtype=np.int64)
    for group in range(32):
        start = 6336 + group * 536
        bank_words = words[start:start + 512].reshape(64, 8).copy()
        bank_words[bank_words >= 32768] -= 65536
        w[:, group * 8:(group + 1) * 8] = bank_words
        for lane in range(8):
            at = start + 512 + lane * 3
            low, middle, high = [int(v) for v in words[at:at + 3]]
            if high > 255:
                raise ValueError("load.hex: malformed bias padding group={} lane={}".format(group, lane))
            value = low | (middle << 16) | (high << 32)
            bias[group * 8 + lane] = value - (1 << 40) if value & (1 << 39) else value
    return x, w, bias


def recompute(x, w, bias, shift):
    # Deliberately independent of data.reference's matrix multiply and divmod.
    total = np.zeros((99, 256), dtype=np.int64)
    for k in range(64):
        total += x[:, k:k + 1] * w[k:k + 1, :]
    total += bias[np.newaxis, :]
    if np.any(total < -(1 << 40)) or np.any(total >= (1 << 40)):
        raise ValueError("total does not fit signed41")
    magnitude = np.abs(total)
    rounded_magnitude = magnitude >> shift
    if shift:
        rounded_magnitude += (magnitude & ((1 << shift) - 1)) >= (1 << (shift - 1))
    rounded = np.where(total < 0, -rounded_magnitude, rounded_magnitude)
    result = np.minimum(np.maximum(rounded, -32768), 32767)
    return {"total": total, "result": result,
            "saturated": (result != rounded).astype(np.int64)}


def validate_layer(folder, expected_layer=None):
    folder = Path(folder)
    try:
        layout = json.loads((folder / "layout.json").read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        raise ValueError("layout.json: {}".format(exc))
    if layout.get("load_words") != 23488 or layout.get("outputs") != 25344:
        raise ValueError("layout count mismatch")
    shift = layout.get("shift")
    if type(shift) is not int or not 0 <= shift <= 31:
        raise ValueError("layout shift must be an integer in 0..31")
    if expected_layer is not None:
        if type(layout.get("layer_number")) is not int or layout["layer_number"] != expected_layer:
            raise ValueError("layout layer_number mismatch")
        if layout.get("kind") != "real":
            raise ValueError("real layer must be identified as kind=real")
    digests = layout.get("sha256")
    required = set(HEX_FILES) | {"expected.npz"}
    if not isinstance(digests, dict) or set(digests) != required:
        raise ValueError("layout SHA-256 file set mismatch")
    for name, digest in digests.items():
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError("invalid SHA-256 for " + name)
        if not (folder / name).is_file() or sha256(folder / name) != digest:
            raise ValueError("SHA-256 mismatch: " + name)
    words = read_words(folder / "load.hex", 16, 23488)
    x, w, bias = decode_load(words)
    recomputed = recompute(x, w, bias, shift)
    with np.load(str(folder / "expected.npz"), allow_pickle=False) as expected:
        if set(expected.files) != {"total", "result", "saturated"}:
            raise ValueError("expected.npz array names")
        for key, bits, signed in (("total", 41, True), ("result", 16, True), ("saturated", 1, False)):
            decoded = read_words(folder / (key + ".hex"), bits, 25344, signed).reshape(99, 256)
            if expected[key].shape != (99, 256) or expected[key].dtype.kind not in "iu":
                raise ValueError("expected.npz {} shape or integer type".format(key))
            for label, actual in (("HEX", decoded), ("NPZ", expected[key])):
                bad = np.flatnonzero(actual.ravel() != recomputed[key].ravel())
                if bad.size:
                    index = int(bad[0])
                    raise ValueError("{} {} mismatch row={} column={}".format(label, key, index // 256, index % 256))
    return {"status": "passed", "outputs": 25344, "layer_number": layout.get("layer_number"),
            "shift": shift, "sha256": digests, "layout_sha256": sha256(folder / "layout.json"),
            "verification": "strict HEX decode, bank reconstruction, independent integer recomputation"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    parser.add_argument("--layer", type=int, choices=range(1, 13))
    args = parser.parse_args()
    try:
        print(json.dumps(validate_layer(args.folder, args.layer), indent=2))
    except (ValueError, OSError, KeyError) as exc:
        print("FAIL: {}".format(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
