#!/usr/bin/env python3
"""One entry point: official KWT-1 + WAV -> full FFN1 float tensors -> arch02 HEX.

Also supports --from-float for existing complete exports. No training or RTL
mutation. Run python kwt_to_hex.py --help for options.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import uuid
import wave

HERE = Path(__file__).resolve().parent
SUPPORT = HERE / "_support"
WORDS = "yes,no,up,down,left,right,on,off,stop,go".split(",")
SEED = "kwt1-full100-20261108"


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def save_json(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8")


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024*1024), b""):
            digest.update(block)
    return digest.hexdigest()


def checked_path(root, name):
    path = (root / name).resolve()
    path.relative_to(root.resolve())
    return path


def find_model(root):
    root = root.resolve()
    candidates = [root] + sorted(root.glob("keyword-transformer*")) + sorted(root.glob("keyword-transformer*/keyword-transformer*"))
    found = [p for p in candidates if (p / "kws_streaming/models/kws_transformer.py").is_file()
             and (p / "models_data_v2_12_labels/kwt1/flags.json").is_file()]
    if len(found) != 1:
        raise ValueError("Cannot identify one official model directory; supply --model with the inner repository root.")
    model = found[0]
    for name in ("best_weights.index", "best_weights.data-00000-of-00001", "flags.json", "labels.txt"):
        if not (model / "models_data_v2_12_labels/kwt1" / name).is_file():
            raise FileNotFoundError("Missing official model file: " + name)
    return model


def find_audio(root):
    root = root.resolve()
    candidates = [root, root / "speech_commands_v0.02"]
    found = [p for p in candidates if (p / "validation_list.txt").is_file() and (p / "testing_list.txt").is_file()]
    if len(found) != 1:
        raise ValueError("Cannot identify audio directory; supply --audio containing official split lists and word/WAV folders.")
    return found[0]


def check_protocol(local_rtl=None):
    protocol = read_json(SUPPORT / "rtl_protocol.json")
    for entry in protocol["files"]:
        path = SUPPORT / entry["local_path"]
        raw = path.read_bytes()
        blob = hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()
        if blob != entry["git_blob"]:
            raise ValueError("Bundled protocol source hash mismatch: " + str(path))
        if local_rtl:
            local = local_rtl / entry["repository_path"]
            if not local.is_file() or local.read_bytes().replace(b"\r\n", b"\n") != raw.replace(b"\r\n", b"\n"):
                raise ValueError("Local RTL differs from supported protocol; review before conversion: " + str(local))
    return protocol


def check_environment(raw_mode):
    if raw_mode and sys.version_info[:2] != (3, 8):
        raise RuntimeError("WAV extraction needs the pinned Python 3.8 environment. Use run_kwt_to_hex.ps1 or --from-float with NumPy.")
    required = {"numpy": "1.19.5", "tensorflow": "2.4.0", "tensorflow-addons": "0.12.1", "protobuf": "3.20.3"} if raw_mode else {"numpy": None}
    versions = {"python": sys.version.split()[0]}
    for name, expected in required.items():
        try:
            actual = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            raise RuntimeError("Missing dependency %s; install requirements-lock.txt in Python 3.8." % name)
        if expected and actual != expected:
            raise RuntimeError("Expected %s==%s; found %s" % (name, expected, actual))
        versions[name] = actual
    return versions


def select_samples(audio, split, count, sample_list):
    valid = set((audio / "validation_list.txt").read_text(encoding="utf-8").splitlines())
    testing = set((audio / "testing_list.txt").read_text(encoding="utf-8").splitlines())
    if split == "validation":
        available = valid
    elif split == "testing":
        available = testing
    else:
        available = {p.relative_to(audio).as_posix() for p in audio.glob("*/*.wav")
                     if p.parent.name != "_background_noise_"} - valid - testing
    if sample_list:
        selected = sample_list.read_text(encoding="utf-8-sig").splitlines()
        if not selected or len(selected) != len(set(selected)) or any(n not in available for n in selected):
            raise ValueError("Sample list contains duplicates or paths outside the selected split")
        if count is not None:
            if count > len(selected):
                raise ValueError("Requested count exceeds sample list length")
            selected = selected[:count]
        method = "Explicit ordered sample list"
    else:
        count = 100 if count is None else count
        rank = lambda n: hashlib.sha256((SEED + ":" + n).encode("utf-8")).hexdigest()
        selected, used, speakers = [], set(), set()
        buckets = {}
        for name in sorted(available, key=rank):
            buckets.setdefault(name.split("/")[0], []).append(name)

        def take(word):
            candidates = [n for n in buckets.get(word, []) if n not in used]
            if not candidates:
                raise ValueError("Not enough %s samples for balanced selection; provide --sample-list." % word)
            fresh = [n for n in candidates if Path(n).name.split("_nohash_")[0] not in speakers]
            name = (fresh or candidates)[0]
            selected.append(name)
            used.add(name)
            speakers.add(Path(name).name.split("_nohash_")[0])

        unknown_count = count // 10
        base, extra = divmod(count - unknown_count, 10)
        for i, word in enumerate(WORDS):
            for _ in range(base + int(i < extra)):
                take(word)
        unknown_words = sorted(set(buckets) - set(WORDS), key=rank)
        if unknown_count and not unknown_words:
            raise ValueError("No unknown word samples")
        for i in range(unknown_count):
            take(unknown_words[i % len(unknown_words)])
        method = "Fixed hash ranking; approximately 90% ten target words, 10% unknown; prefer distinct speakers"
    records = []
    for number, name in enumerate(selected, 1):
        path = checked_path(audio, name)
        with wave.open(str(path), "rb") as wav:
            if (wav.getnchannels(), wav.getsampwidth(), wav.getframerate()) != (1, 2, 16000):
                raise ValueError("Expected mono 16-bit PCM 16kHz WAV: " + name)
            frames = wav.getnframes()
        word = name.split("/")[0]
        records.append(dict(sample=number, wav=name, wav_sha256=sha(path), original_frames=frames,
                            label=word if word in WORDS else "_unknown_"))
    return dict(split=split, count=len(records), selection_method=method, seed=SEED,
                label_counts=dict(Counter(r["label"] for r in records)), silence_samples=0,
                distinct_speakers=len({Path(r["wav"]).name.split("_nohash_")[0] for r in records}),
                samples=records, scope="Development inputs, not official 600-sample evaluation selection")


def check_float_archive(root):
    manifest = read_json(root / "manifest.json")
    if manifest.get("schema") != "kwt1-full-ffn1-float-v1" or manifest.get("status") != "passed":
        raise ValueError("Expected complete FFN1 float archive. The old single-dot ORIGINAL_FLOAT ZIP cannot be converted into full matrices.")
    if manifest.get("shapes") != dict(X=[12,99,64], W=[12,64,256], b=[12,256], Y=[12,99,256]):
        raise ValueError("Incomplete float matrix dimensions")
    if not manifest.get("samples") or manifest.get("total_outputs_checked") != len(manifest["samples"])*304128:
        raise ValueError("Float archive sample/output count mismatch")
    if sha(root / "shared_weights.npz") != manifest["shared_weights_sha256"]:
        raise ValueError("Shared weights hash mismatch")
    for sample in manifest["samples"]:
        if sha(checked_path(root, sample["file"])) != sample["sha256"]:
            raise ValueError("Float sample hash mismatch")
    return manifest


def run_stage(script, arguments, log_path):
    cmd = [sys.executable, "-B", str(SUPPORT / script)] + [str(a) for a in arguments]
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    with log_path.open("w", encoding="utf-8") as log:
        log.write("ARGV=" + json.dumps(cmd, ensure_ascii=False) + "\n")
        log.flush()
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   text=True, encoding="utf-8", errors="replace", env=env)
        try:
            for line in process.stdout:
                log.write(line)
                log.flush()
                if line.startswith(("PASS", "Verified", "Complete:")):
                    print(line.rstrip(), flush=True)
            code = process.wait()
        except BaseException:
            process.terminate()
            process.wait()
            raise
    if code:
        detail = "\n".join(log_path.read_text(encoding="utf-8").splitlines()[-12:])
        raise RuntimeError("%s failed (%d). Log: %s\n%s" % (script, code, log_path, detail))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, default=Path("D:/FPGA芯片赛道"), help="Parent containing downloaded model and speech_commands_v0.02")
    parser.add_argument("--model", type=Path, help="Official model repository root; auto-detected otherwise")
    parser.add_argument("--audio", type=Path, help="Speech Commands directory; auto-detected otherwise")
    parser.add_argument("--count", type=int, help="WAV count (default 100, or all entries of sample-list)")
    parser.add_argument("--split", choices=("training", "validation", "testing"), default="validation")
    parser.add_argument("--sample-list", type=Path, help="Ordered word/file.wav list")
    parser.add_argument("--from-float", type=Path, help="Existing complete float export; skips TensorFlow and WAV extraction")
    parser.add_argument("--rtl-repo", type=Path, help="Optional local private Git checkout: reject mismatched RTL/protocol files")
    parser.add_argument("--output", type=Path, help="New output directory; never overwritten")
    parser.add_argument("--threads", type=int, default=4)
    args = parser.parse_args(argv)
    if (args.count is not None and args.count < 1) or args.threads < 1:
        parser.error("count and threads must be positive")
    if args.from_float and (args.count is not None or args.sample_list or args.model or args.audio):
        parser.error("--from-float converts the entire supplied archive; do not combine with raw-input selection options")
    out = (args.output or HERE / "runs" / (datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:8])).resolve()
    if out.exists():
        parser.error("Output already exists; choose a new --output to preserve previous results")
    status = None
    try:
        protocol = check_protocol(args.rtl_repo.resolve() if args.rtl_repo else None)
        versions = check_environment(not args.from_float)
        if args.from_float:
            float_root = args.from_float.resolve()
            floats = check_float_archive(float_root)
            selection = dict(count=len(floats["samples"]), split=floats["split"], selection_method="Existing complete float archive")
        else:
            model = find_model(args.model or args.data_root)
            audio = find_audio(args.audio or args.data_root)
            selection = select_samples(audio, args.split, args.count, args.sample_list)
            float_root = out / "float"
        support_hashes = {p.relative_to(HERE).as_posix(): sha(p) for p in SUPPORT.rglob("*") if p.is_file() and "__pycache__" not in p.parts}
        out.mkdir(parents=True, exist_ok=False)
        (out / "logs").mkdir()
        status = dict(status="running", stage="selection", created_at_utc=datetime.now(timezone.utc).isoformat(),
                      entry_script_sha256=sha(__file__), support_sha256=support_hashes, environment=versions,
                      rtl_commit=protocol["commit"], rtl_repository=protocol["repository"],
                      selection=selection, float_directory=str(float_root))
        save_json(out / "status.json", status)
        save_json(out / "rtl_protocol.json", protocol)
        if not args.from_float:
            (out / "selection").mkdir()
            save_json(out / "selection/selection.json", selection)
            samples_path = out / "selection/samples.txt"
            samples_path.write_text("\n".join(r["wav"] for r in selection["samples"]) + "\n", encoding="utf-8")
            status.update(stage="extract_float", model=str(model), audio=str(audio))
            save_json(out / "status.json", status)
            print("Extracting %d WAV samples; batch=1, all 12 full FFN1 matrices." % selection["count"], flush=True)
            run_stage("export_full.py", ["--repo", model, "--audio", audio, "--out", float_root,
                      "--split", args.split, "--sample-list", samples_path, "--limit", selection["count"], "--threads", args.threads], out / "logs/extract.log")
            floats = check_float_archive(float_root)
        status.update(stage="convert_and_check_hex")
        save_json(out / "status.json", status)
        run_stage("convert_hex.py", ["--input", float_root, "--out", out / "hex"], out / "logs/convert.log")
        report = read_json(out / "hex/manifest.json")
        if report["status"] != "passed" or report["total_outputs_checked"] != selection["count"] * 304128:
            raise ValueError("Final HEX verification count mismatch")
        for path, digest in support_hashes.items():
            if sha(HERE / path) != digest:
                raise ValueError("Tool source changed while running: " + path)
        status.update(status="passed", stage="complete", samples=selection["count"], matrix_tasks=selection["count"]*12,
                      outputs_checked=report["total_outputs_checked"], max_layer_nrmse_percent=report["aggregate_max_nrmse_percent"],
                      individual_tasks_above_3_percent=report["individual_tasks_above_3_percent"],
                      precision_threshold_met=report["aggregate_max_nrmse_percent"] <= 3 and report["individual_tasks_above_3_percent"] == 0,
                      hex_manifest_sha256=sha(out / "hex/manifest.json"), float_manifest_sha256=sha(float_root / "manifest.json"),
                      completed_at_utc=datetime.now(timezone.utc).isoformat(),
                      scope="Full float/HEX software validation only; no RTL simulation, SRAM/SoC, official600 or PPA validation")
        save_json(out / "status.json", status)
        print("DONE: %d samples, %d complete matrices, %d outputs; max layer NRMSE %.6f%%" % (status["samples"], status["matrix_tasks"], status["outputs_checked"], status["max_layer_nrmse_percent"]), flush=True)
        print("OUTPUT: " + str(out), flush=True)
        return 0
    except (Exception, KeyboardInterrupt) as exc:
        if status is not None:
            status.update(status="failed", error=str(exc) or "Interrupted")
            save_json(out / "status.json", status)
        print("ERROR: " + (str(exc) or "Interrupted"), file=sys.stderr, flush=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
