"""Standalone Linux VCS vendor regression; Python 3.6, standard library only.

Expected bundle layout: rtl/, arch02/{rtl,tb}/, vectors/, validated_data/.
No implicit SRAM configuration and no substitute model fallback.
"""
import argparse
import csv
import hashlib
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def save(p, value):
    p.write_text(json.dumps(value, indent=2), encoding='utf-8')


def read_hex(path, bits, count, signed=False):
    lines = path.read_text().splitlines()
    if len(lines) != count:
        raise ValueError('{} count {} expected {}'.format(path, len(lines), count))
    result = []
    for i, line in enumerate(lines):
        if not re.fullmatch('[0-9a-fA-F]{%d}' % ((bits + 3) // 4), line):
            raise ValueError('{} line {} invalid HEX'.format(path, i + 1))
        value = int(line, 16)
        if value >= (1 << bits):
            raise ValueError('{} line {} unused high bits'.format(path, i + 1))
        if signed and value & (1 << (bits - 1)):
            value -= 1 << bits
        result.append(value)
    return result


def reference(folder):
    words = read_hex(folder / 'load.hex', 16, 23488)
    totals = read_hex(folder / 'total.hex', 41, 25344, True)
    results = read_hex(folder / 'result.hex', 16, 25344, True)
    sats = read_hex(folder / 'saturated.hex', 1, 25344)
    shift = json.loads((folder / 'layout.json').read_text())['shift']
    if not isinstance(shift, int) or not 0 <= shift <= 31:
        raise ValueError('Invalid shift')
    signed16 = lambda x: x - 65536 if x >= 32768 else x
    x = [signed16(v) for v in words[:6336]]
    for group in range(32):
        start = 6336 + group * 536
        w = [signed16(v) for v in words[start:start + 512]]
        for lane in range(8):
            pos = start + 512 + lane * 3
            if words[pos + 2] >= 256:
                raise ValueError('Malformed bias padding')
            bias = words[pos] + (words[pos + 1] << 16) + (words[pos + 2] << 32)
            if bias & (1 << 39): bias -= 1 << 40
            for row in range(99):
                idx = row * 256 + group * 8 + lane
                total = bias + sum(x[row * 64 + k] * w[k * 8 + lane] for k in range(64))
                q, rem = divmod(abs(total), 1 << shift)
                rounded = (q + (2 * rem >= (1 << shift))) * (-1 if total < 0 else 1)
                result = max(-32768, min(32767, rounded))
                expected = (total, result, int(rounded != result))
                if expected != (totals[idx], results[idx], sats[idx]):
                    raise ValueError('{} row={} col={} reference mismatch'.format(folder, row, idx % 256))
    return totals, results, sats


def compare(capture, data, output):
    expected = [read_hex(data / name, bits, 25344, signed) for name, bits, signed in
                [('total.hex', 41, True), ('result.hex', 16, True), ('saturated.hex', 1, False)]]
    matrix = [None] * 25344
    with capture.open() as f:
        rows = list(csv.reader(f))
    if len(rows) != 25344: raise ValueError('Output count ' + str(capture))
    for stream, line in enumerate(rows):
        values = list(map(int, line))
        if len(values) != 4: raise ValueError('Capture columns')
        idx = values[0]
        group, rem = divmod(stream, 99 * 8)
        row, lane = divmod(rem, 8)
        if idx != row * 256 + group * 8 + lane:
            raise ValueError('Output scheduling/coordinate mismatch ' + str(stream))
        if matrix[idx] is not None: raise ValueError('Duplicate output')
        if values[1:] != [a[idx] for a in expected]:
            raise ValueError('RTL row={} col={} mismatch'.format(idx // 256, idx % 256))
        matrix[idx] = values[1:]
    if any(v is None for v in matrix): raise ValueError('Missing output')
    for col, name in enumerate(('total', 'result', 'saturated')):
        with (output.parent / (output.name + '_' + name + '.csv')).open('w', newline='') as f:
            writer = csv.writer(f)
            for row in range(99):writer.writerow([matrix[row * 256 + c][col] for c in range(256)])
    return {'outputs': 25344, 'capture_sha256': sha(capture)}


def command(argv, cwd, log, negative=None):
    with log.open('w') as f:
        p = subprocess.run([str(x) for x in argv], cwd=str(cwd), stdout=f,
                           stderr=subprocess.STDOUT, timeout=3600)
    text = log.read_text(errors='replace')
    failed = p.returncode != 0 or bool(re.search(r'(?im)^\s*(?:fatal|error)(?:\s|:|-|\[)', text))
    if negative:
        if negative not in text or not failed or 'PASS: arch02' in text:
            raise ValueError('Negative test did not fail correctly: ' + str(log))
    elif failed: raise ValueError('Command failed: ' + str(log))
    return text


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, default=Path(__file__).resolve().parent)
    p.add_argument('--mode', choices=['check-data', 'unit', 'smoke', 'all'], default='unit')
    p.add_argument('--config', type=Path)
    p.add_argument('--filelist', type=Path)
    p.add_argument('--include', action='append', default=[])
    p.add_argument('--vendor-mode', choices=['timing', 'functional'], default='timing',
                   help='Explicit ARM vendor branch; functional defines ARM_UD_MODEL, never a mock fallback')
    args = p.parse_args()
    root = args.root.resolve()
    run = root / 'server_runs' / datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    run.mkdir(parents=True)
    summary = {'status': 'running', 'mode': args.mode, 'backend': 'vendor',
               'vendor_model_mode': args.vendor_mode,
               'timing_signoff': False, 'jobs': [], 'run': str(run)}
    print('RUN ' + str(run), flush=True)
    try:
        package = json.loads((root / 'manifest.json').read_text())
        for rel, digest in package['files'].items():
            source = (root / rel).resolve()
            source.relative_to(root)
            if sha(source) != digest: raise ValueError('Bundle hash mismatch ' + rel)
        summary['bundle_manifest_sha256'] = sha(root / 'manifest.json')
        if args.mode == 'check-data':
            for folder in sorted((root / 'validated_data').iterdir()):
                if folder.is_dir():
                    reference(folder)
                    print('PASS integer reference ' + folder.name, flush=True)
            summary.update(status='passed', software_real_outputs=304128, vendor_simulated=False)
            return 0
        if not args.config or not args.filelist:
            raise ValueError('Explicit vendor --config and --filelist required')
        cfg = json.loads(args.config.read_text())
        if cfg.get('kind') != 'vendor_confirmed' or not cfg.get('evidence'):
            raise ValueError('Need confirmed vendor configuration and evidence')
        header = []
        for size in ('128', '4096'):
            c = cfg['macros'][size]
            if c['read_latency'] != 1 or c['clock_edge'] != 'posedge':
                raise ValueError('Native SRAM timing requires adapter revision')
            for key, width in [('cen_low', 1), ('gwen_low', 1), ('wen_low', 1), ('ema', 3), ('emaw', 2), ('ret1n', 1)]:
                if type(c[key]) is not int or not 0 <= c[key] < (1 << width):raise ValueError('Invalid config ' + key)
                header.append("`define A02_{}_{} {}'d{}".format(size, key.upper(), width, c[key]))
        (run / 'arch02_sram_config.vh').write_text('\n'.join(header) + '\n')
        models = []
        for line in args.filelist.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith('#'):continue
            model = (args.filelist.resolve().parent / line).resolve()
            if re.search(r'\bmodule\s+arch02_pin_mock\b', model.read_text(errors='replace')):
                raise ValueError('Mock forbidden in vendor build')
            models.append(model)
        if not models:raise ValueError('Empty vendor filelist')
        sources = [root / x for x in ['rtl/dot64.sv', 'rtl/requantize.sv',
            'arch02/rtl/arch02_linear.sv', 'arch02/rtl/sram_port.sv', 'arch02/rtl/sram_macro_adapter.sv',
            'arch02/tb/tb_arch02.sv', 'arch02/tb/tb_lanes.sv', 'arch02/tb/tb_sram_adapter.sv',
            'arch02/tb/tb_sram_guard.sv']] + models
        summary['sources'] = {str(s): sha(s) for s in sources}
        summary['config'] = cfg
        vcs = shutil.which('vcs')
        if not vcs:raise ValueError('vcs missing from initialized PATH')
        tops = ['tb_sram_adapter'] if args.mode == 'unit' else ['tb_sram_adapter', 'tb_arch02', 'tb_arch02_l2', 'tb_lanes', 'tb_sram_guard']
        includes = [run, root / 'vectors'] + sorted(set(m.parent for m in models)) + [Path(x).resolve() for x in args.include]
        vendor_flags = ['+define+ARM_UD_MODEL'] if args.vendor_mode == 'functional' else []
        if args.vendor_mode == 'functional':
            for model in models:
                if 'ARM_UD_MODEL' not in model.read_text(errors='replace'):
                    raise ValueError('Selected model has no confirmed ARM_UD_MODEL branch: ' + str(model))
        for top in tops:
            build = run / top;build.mkdir()
            command([vcs, '-full64', '-sverilog', '-timescale=1ns/1ps', '-debug_access+all',
                     '-top', top, '-o', build / 'simv'] + vendor_flags + ['+incdir+' + str(x) for x in includes] + sources,
                    build, build / 'compile.log')
        def simulate(top, tag, plus, marker=None, negative=None):
            text = command([run / top / 'simv'] + ['+' + s for s in plus], run, run / (tag + '.log'), negative)
            if marker and marker not in text:raise ValueError('Missing PASS ' + tag)
            item = {'tag': tag, 'passed': True, 'expected_failure': negative}
            summary['jobs'].append(item);save(run / 'summary.json', summary)
            print('PASS ' + tag, flush=True)
            return text, item
        simulate('tb_sram_adapter', 'sram_adapter', [], 'PASS: SRAM adapter cases=4')
        if args.mode != 'unit':
            layers = range(1, 13) if args.mode == 'all' else [1]
            jobs = [('layer_{:02d}'.format(n), 1, 0, 0) for n in layers] + [('extremes', 1, 1, 0), ('rounding', 2, 1, 1)]
            for name, lat, jitter, resets in jobs:
                data = root / 'validated_data' / name
                reference(data)
                capture = run / (name + '.csv')
                plus = ['DATA_DIR=' + str(data), 'OUTPUT_FILE=' + str(capture), 'SHIFT=' + ('11' if name == 'rounding' else '12'), 'JITTER=' + str(jitter), 'RESET_PROBES=' + str(resets)]
                if name == 'rounding':plus += ['SECOND_DATA_DIR=' + str(root / 'validated_data/extremes'), 'SECOND_SHIFT=12', 'VCD']
                text, item = simulate('tb_arch02_l2' if lat == 2 else 'tb_arch02', name, plus)
                count = 2 if name == 'rounding' else 1
                if len(re.findall(r'^PASS: arch02 outputs=25344 latency=' + str(lat), text, re.M)) != count:raise ValueError('Matrix PASS count ' + name)
                if resets and len(re.findall(r'^PASS reset probe=', text, re.M)) != 9:raise ValueError('Reset coverage')
                item.update(compare(capture, data, run / name))
                item['metrics'] = re.findall(r'^METRICS .*$', text, re.M)
                if len(item['metrics']) != count:raise ValueError('Missing metrics')
                if count == 2:item['second'] = compare(Path(str(capture) + '.second.csv'), root / 'validated_data/extremes', run / 'rounding_second')
                save(run / 'summary.json', summary)
            simulate('tb_lanes', 'numerical', ['DATA_DIR=' + str(root / 'vectors')], 'PASS: numerical cases=1103 lanes=8 checks=8824')
            for case, message in [('padding', 'Malformed bias padding'), ('missing', 'Missing load.hex'), ('short_file', 'Missing/invalid load word'), ('timeout', 'No progress timeout'), ('reference', 'Mismatch row=0 column=0')]:
                data = run / ('negative_' + case);shutil.copytree(str(root / 'validated_data/layer_01'), str(data))
                if case == 'missing':(data / 'load.hex').unlink()
                elif case == 'short_file':(data / 'load.hex').write_text('0000\n')
                elif case in ('padding', 'reference'):
                    path = data / ('load.hex' if case == 'padding' else 'result.hex')
                    lines = path.read_text().splitlines();idx = 6850 if case == 'padding' else 0
                    lines[idx] = '{:04x}'.format(int(lines[idx], 16) | 256 if case == 'padding' else int(lines[idx], 16) ^ 1)
                    path.write_text('\n'.join(lines) + '\n')
                plus = ['DATA_DIR=' + str(data), 'OUTPUT_FILE=' + str(data / 'actual.csv')]
                if case == 'timeout':plus += ['TRUNCATE_WORDS=100']
                simulate('tb_arch02', 'negative_' + case, plus, negative=message)
            simulate('tb_sram_guard', 'negative_uninitialized', [], negative='Uninitialized SRAM read')
            summary['real_outputs'] = len(layers) * 25344
        for source, digest in summary['sources'].items():
            if sha(Path(source)) != digest:raise ValueError('Source changed during run')
        summary['status'] = 'passed'
        print('VCS_VENDOR_PASS mode={} model={} real_outputs={}'.format(args.mode, args.vendor_mode, summary.get('real_outputs', 0)), flush=True)
        return 0
    except Exception as exc:
        summary.update(status='failed', error=str(exc))
        print('FAIL ' + str(exc), flush=True)
        return 1
    finally:
        save(run / 'summary.json', summary)


if __name__ == '__main__':
    sys.exit(main())
