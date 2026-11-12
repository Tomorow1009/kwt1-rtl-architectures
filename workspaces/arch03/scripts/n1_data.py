"""Strict N1 source/reference checks and immutable task preparation.

Group8 sources remain intact.  A separate tile16/v3 payload uses layout 4 and
numeric identity 0x000e0c20.  Preparation and capture checks need Python 3.6
standard library only; local float conversion additionally needs NumPy and the
byte-identical PR #9 converter.  No legacy Q12 batch identity is accepted.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import struct
import zipfile

import dma16_batch as geometry
import n1_codec as codec
import systolic_b_data as base_data

require, read, save, sha = geometry.require, geometry.read, geometry.save, geometry.sha
CASES14 = geometry.CASES14
ROOT = Path(__file__).resolve().parents[3]
PR_COMMIT = '50c1261f3f7fafe1531e05e023aadd926cefa24a'
CONVERTER_SHA = 'c99301b68185f599b95e4b4b3cbe5e62db27128dcf3cf04e4725bdb9a5620c35'
CONVERTER = ROOT/'tools/kwt-x14-w12-b32/convert_kwt1_x14_w12_b32.py'
FORMAT = dict(x_bits=14, x_fraction=10, w_bits=12, w_fraction=12,
              product_bits=26, accumulator_bits=32, bias_bits=32, bias_fraction=22,
              total_bits=33, total_fraction=22, result_bits=16, result_fraction=12, shift=10)
FILES = {'load.hex': (16, 23488), 'total.hex': (33, 25344),
         'result.hex': (16, 25344), 'saturated.hex': (1, 25344)}
SOURCE_SCHEMA = 'kwt1-x14-w12-b32-group8-v1'
LAYOUT_SCHEMA = 'kwt1-arch03-n1-tile16-x14-w12-b32-v1'
CASE_SCHEMA = 'arch03-n1-case-v1'
DATA100_INVENTORY_SHA = 'ae052bc1e543930abece8202a5b1439dcbd50dd4f5d7d09fb8f049eb30eeb997'

# Only generic runtime evidence/timing parsing is shared. Source identities,
# integer references and captures below are N1-specific and never use Q12 data.
read_window = base_data.read_window


def parse_result(text, saturated, required_markers=()):
    require('ARCH03_N1_TOTAL_PROOF ' in text, 'Missing N1 signed33 total proof')
    return base_data.parse_result(text, saturated, required_markers)


def hex_values(path, count, bits, signed=False):
    """One exact-width word per line, including the nine-digit signed33 ABI."""
    lines = Path(path).read_text(encoding='ascii').splitlines()
    pattern = re.compile(r'[0-9a-fA-F]{%d}' % ((bits + 3) // 4))
    require(len(lines) == count and all(pattern.fullmatch(s) for s in lines),
            'Invalid HEX line count/width: ' + str(path))
    values = [int(s, 16) for s in lines]
    require(all(v < (1 << bits) for v in values), 'Nonzero HEX reserved high bits: ' + str(path))
    return [v - (1 << bits) if signed and v & (1 << (bits - 1)) else v for v in values]


def write_hex(path, values, bits):
    mask = (1 << bits) - 1
    template = '%0' + str((bits + 3) // 4) + 'x\n'
    Path(path).write_bytes(''.join(template % (int(v) & mask) for v in values).encode('ascii'))


def decode_group8(words):
    """Use original matrix coordinates, independent of the tile copy routine."""
    require(len(words) == 23488 and all(type(v) is int and 0 <= v <= 65535 for v in words),
            'Invalid group8 words')
    signed = [v - 65536 if v & 32768 else v for v in words]
    x = [signed[row * 64:(row + 1) * 64] for row in range(99)]
    require(all(-8192 <= v <= 8191 for row in x for v in row), 'X14 sign extension')
    w = [[signed[6336 + (col // 8) * 536 + k * 8 + col % 8]
          for col in range(256)] for k in range(64)]
    require(all(-2048 <= v <= 2047 for row in w for v in row), 'W12 sign extension')
    bias = []
    for col in range(256):
        at = 6336 + (col // 8) * 536 + 512 + (col % 8) * 3
        u = words[at] | (words[at + 1] << 16)
        require(words[at + 2] == (255 if u & (1 << 31) else 0),
                'b32 sign extension/padding column=%d' % col)
        bias.append(u - (1 << 32) if u & (1 << 31) else u)
    return x, w, bias


def integer_reference(x, w, bias):
    """Python unbounded integers, all 64 prefix sums and output coordinates."""
    totals, results, saturated = [], [], []
    acc_min, acc_max = 0, 0
    for row in range(99):
        sums = [0] * 256
        for k in range(64):
            factor, weights = x[row][k], w[k]
            for col in range(256):
                sums[col] += factor * weights[col]
                require(-(1 << 31) <= sums[col] < (1 << 31),
                        'Accumulator overflow row=%d column=%d k=%d' % (row, col, k))
        acc_min, acc_max = min(acc_min, min(sums)), max(acc_max, max(sums))
        for col in range(256):
            total = sums[col] + bias[col]
            require(-(1 << 32) <= total < (1 << 32), 'Total33 overflow')
            quotient, remainder = divmod(abs(total), 1024)
            magnitude = quotient + int(remainder >= 512)
            rounded = -magnitude if total < 0 else magnitude
            result = min(32767, max(-32768, rounded))
            totals.append(total); results.append(result); saturated.append(int(result != rounded))
    return dict(total=totals, result=results, saturated=saturated,
                accumulator_min=acc_min, accumulator_max=acc_max)


def source_case(source):
    source = Path(source)
    meta = read(source/'layout.json')
    require(meta.get('schema') == SOURCE_SCHEMA and meta.get('format') == FORMAT,
            'Wrong N1 source schema/numeric format')
    require(meta.get('load_words') == 23488 and meta.get('outputs') == 25344 and
            meta.get('bias_storage_bits') == 40, 'Wrong N1 source dimensions/bias container')
    require(set(meta['files']) == set(FILES), 'Unexpected source HEX file set')
    for name in FILES:
        require(meta['files'][name] == dict(bytes=(source/name).stat().st_size, sha256=sha(source/name)),
                'Source identity mismatch: ' + name)
    words = hex_values(source/'load.hex', 23488, 16)
    decode_group8(words)
    # Read total even when the caller only needs results, rejecting stale 41-bit files.
    hex_values(source/'total.hex', 25344, 33, True)
    results = hex_values(source/'result.hex', 25344, 16)
    saturated = hex_values(source/'saturated.hex', 25344, 1)
    return meta, words, results, saturated


def inspect_case(source):
    source = Path(source)
    meta, words, _, _ = source_case(source)
    x, w, bias = decode_group8(words)
    reference = integer_reference(x, w, bias)
    for field in ('total', 'result', 'saturated'):
        bits, count = FILES[field + '.hex']
        expected = hex_values(source/(field + '.hex'), count, bits, field != 'saturated')
        if reference[field] != expected:
            at = next(i for i, pair in enumerate(zip(reference[field], expected)) if pair[0] != pair[1])
            raise ValueError('%s mismatch row=%d column=%d' % (field, at // 256, at % 256))
    return dict(status='passed', outputs=25344, macs_checked=1622016,
                total_mismatches=0, result_mismatches=0, saturated_mismatches=0,
                total_min=min(reference['total']), total_max=max(reference['total']),
                accumulator_min=reference['accumulator_min'], accumulator_max=reference['accumulator_max'],
                saturated=sum(reference['saturated']), source_layout_sha256=sha(source/'layout.json'),
                format=FORMAT, rtl_executed=False, official_accuracy_verified=False)


def index_dataset(root, expected_sha=DATA100_INVENTORY_SHA, expected_samples=100):
    """Index PR100 using its frozen HEX inventory, not the old Q12 manifest ABI.

    expected_sha identifies SHA256_FILES.json (the PR documents do NOT publish
    a manifest.json hash).  Each task binds both actual root JSON identities.
    Full integer reference recomputation occurs during prepare_case.
    """
    root = Path(root)
    require(sha(root/'SHA256_FILES.json') == expected_sha, 'N1 dataset inventory changed')
    inventory = read(root/'SHA256_FILES.json')
    manifest = read(root/'manifest.json')
    require(manifest.get('format') == FORMAT, 'Wrong N1 dataset format')
    expected = {'sample_%03d/layer_%02d/%s' % (sample, layer, name)
                for sample in range(1, expected_samples+1) for layer in range(1, 13) for name in FILES}
    require(set(inventory) == expected, 'N1 dataset must contain the exact frozen sample/layer/HEX set')
    actual = {path.relative_to(root).as_posix() for path in root.rglob('*.hex')}
    require(actual == expected, 'Extra or missing N1 dataset HEX file')
    for rel in sorted(expected):
        path = root/rel
        require(not path.is_symlink() and inventory[rel] == dict(bytes=path.stat().st_size, sha256=sha(path)),
                'N1 dataset HEX changed: ' + rel)
    tasks = []
    manifest_sha = sha(root/'manifest.json')
    for sample in range(1, expected_samples+1):
        for layer in range(1, 13):
            rel = 'sample_%03d/layer_%02d' % (sample, layer)
            folder = root/rel
            meta = read(folder/'layout.json')
            require(meta.get('schema') == SOURCE_SCHEMA and meta.get('format') == FORMAT and
                    meta.get('layer') == layer and meta.get('load_words') == 23488 and
                    meta.get('outputs') == 25344 and meta.get('bias_storage_bits') == 40,
                    'N1 layer metadata changed: ' + rel)
            require(meta['files'] == {name: inventory[rel+'/'+name] for name in FILES},
                    'N1 layer/inventory disagreement: ' + rel)
            tasks.append(dict(key=rel.replace('/', '_'), source=str(folder.resolve()), sample=sample,
                              layer=layer, shift=10, source_layout_sha256=sha(folder/'layout.json'),
                              dataset_inventory_sha256=expected_sha, dataset_manifest_sha256=manifest_sha))
    return tasks


def _write_npz(path, arrays):
    """Portable deterministic int64 NPZ; verification-only, never hardware input."""
    with zipfile.ZipFile(str(path), 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for name, shape, values in arrays:
            header = repr(dict(descr='<i8', fortran_order=False, shape=shape))
            header += ' ' * ((16 - ((10 + len(header) + 1) % 16)) % 16) + '\n'
            payload = b'\x93NUMPY\x01\x00' + struct.pack('<H', len(header)) + header.encode('latin1')
            payload += struct.pack('<%dq' % len(values), *values)
            info = zipfile.ZipInfo(name + '.npy', date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, payload)


def prepare_case(source, destination, force_raw=False, layout_id=codec.LAYOUT):
    source, destination = Path(source), Path(destination)
    require(layout_id == codec.LAYOUT, 'N1 only accepts layout 0x00100004')
    require(not destination.exists(), 'Prepared case already exists')
    audit = inspect_case(source)
    meta, words, _, _ = source_case(source)
    packed = geometry.reorder_words(words)
    raw = struct.pack('<23488H', *packed)
    encoded = codec.encode(raw, force_raw=force_raw)
    require(codec.decode(encoded) == raw, 'Lossless reconstruction mismatch')
    require(codec.verify_coordinates(raw, codec.decode_wire(encoded)) == 23488, 'N1 coordinate audit')
    destination.mkdir(parents=True)
    (destination/'load.bin').write_bytes(raw)
    write_hex(destination/'load.hex', packed, 16)
    write_hex(destination/'load32.hex', struct.unpack('<11744I', raw), 32)
    for name in FILES:
        if name != 'load.hex':
            (destination/name).write_bytes((source/name).read_bytes())
    _write_npz(destination/'expected.npz', [
        (name, (99, 256), hex_values(source/(name+'.hex'), 25344, FILES[name+'.hex'][0], name != 'saturated'))
        for name in ('total', 'result', 'saturated')])
    layout = dict(schema=LAYOUT_SCHEMA, shift=10, numeric_format=FORMAT,
                  numeric_format_id=codec.NUMERIC_FORMAT, layout=codec.LAYOUT,
                  input_bytes=46976, output_bytes=50688,
                  source_layout_sha256=sha(source/'layout.json'),
                  source_sha256={name: meta['files'][name]['sha256'] for name in FILES},
                  runtime_inputs=['load.bin', 'load.hex', 'load32.hex'],
                  verification_only=['total.hex', 'result.hex', 'saturated.hex', 'expected.npz'],
                  original_coordinates_checked=22976, original_bias_parts_checked=768,
                  layout_script_sha256=sha(__file__), geometry_script_sha256=sha(geometry.__file__),
                  reference_audit=audit,
                  sha256={p.name: sha(p) for p in destination.iterdir() if p.is_file()})
    save(destination/'layout_manifest.json', layout)
    (destination/'codec.bin').write_bytes(encoded)
    write_hex(destination/'codec32.hex', struct.unpack('<%dI' % (len(encoded)//4), encoded), 32)
    record = codec.describe(encoded)
    record.update(schema=CASE_SCHEMA, numeric_format=FORMAT,
                  source_layout_sha256=layout['source_layout_sha256'],
                  tile_layout_sha256=sha(destination/'layout_manifest.json'),
                  source_sha256=sha(destination/'load.bin'), force_raw=force_raw,
                  runtime_inputs=['codec32.hex'],
                  files={name: sha(destination/name) for name in ('codec.bin', 'codec32.hex')},
                  codec_script_sha256=sha(codec.__file__), preparation_script_sha256=sha(__file__),
                  pr_converter_commit=PR_COMMIT, pr_converter_sha256=CONVERTER_SHA)
    save(destination/'codec.json', record)
    return record


def verify_prepared(source, destination):
    source, destination = Path(source), Path(destination)
    meta, words, _, _ = source_case(source)
    layout, record = read(destination/'layout_manifest.json'), read(destination/'codec.json')
    require(layout['schema'] == LAYOUT_SCHEMA and layout['shift'] == 10 and layout['numeric_format'] == FORMAT,
            'Prepared numeric format changed')
    require(layout['source_layout_sha256'] == sha(source/'layout.json') and
            layout['source_sha256'] == {name: meta['files'][name]['sha256'] for name in FILES} and
            layout['layout_script_sha256'] == sha(__file__) and
            layout['geometry_script_sha256'] == sha(geometry.__file__), 'Prepared source/layout changed')
    geometry.check_hashes(destination, layout['sha256'])
    raw = (destination/'load.bin').read_bytes()
    geometry.verify_reorder(words, list(struct.unpack('<23488H', raw)))
    require(list(struct.unpack('<23488H', raw)) == hex_values(destination/'load.hex', 23488, 16), 'Halfword order')
    require(list(struct.unpack('<11744I', raw)) == hex_values(destination/'load32.hex', 11744, 32), 'Word byte order')
    for name in FILES:
        if name != 'load.hex':
            require(sha(destination/name) == meta['files'][name]['sha256'], 'Reference copy changed')
    require(record['schema'] == CASE_SCHEMA and record['numeric_format'] == FORMAT and record['shift'] == 10 and
            record['tile_layout_sha256'] == sha(destination/'layout_manifest.json') and
            record['source_layout_sha256'] == layout['source_layout_sha256'] and
            record['source_sha256'] == sha(destination/'load.bin') and
            record['codec_script_sha256'] == sha(codec.__file__) and
            record['preparation_script_sha256'] == sha(__file__), 'Codec identity changed')
    geometry.check_hashes(destination, record['files'])
    encoded = (destination/'codec.bin').read_bytes()
    require(codec.decode(encoded) == raw, 'Codec reconstruction changed')
    codec.verify_coordinates(raw, codec.decode_wire(encoded))
    require(list(struct.unpack('<%dI' % (len(encoded)//4), encoded)) ==
            hex_values(destination/'codec32.hex', len(encoded)//4, 32), 'Encoded byte order')
    for key, value in codec.describe(encoded).items():
        require(record[key] == value, 'Codec descriptor changed: ' + key)
    return record


def check_capture(capture, task):
    """CSV row,col,result,sat,total (decimal), with no legacy four-column fallback."""
    task = Path(task)
    expected = {name: hex_values(task/(name+'.hex'), 25344, FILES[name+'.hex'][0], name != 'saturated')
                for name in ('total', 'result', 'saturated')}
    seen = set()
    with Path(capture).open('r', encoding='ascii') as stream:
        for line in stream:
            parts = line.strip().split(',')
            require(len(parts) == 5, 'Capture must carry row,col,result,sat,total')
            row, col = int(parts[0]), int(parts[1])
            require(0 <= row < 99 and 0 <= col < 256, 'Capture coordinate out of range')
            index = row * 256 + col
            require(index not in seen, 'Duplicate capture coordinate')
            seen.add(index)
            for key, actual in zip(('result', 'saturated', 'total'), parts[2:]):
                require(int(actual) == expected[key][index], 'Capture %s mismatch row=%d col=%d' % (key, row, col))
    require(len(seen) == 25344, 'Missing capture coordinate')
    return dict(outputs=len(seen), mismatches=0, total_checked=True,
                saturated=sum(expected['saturated']), capture_sha256=sha(capture))


def converter_module():
    require(sha(CONVERTER) == CONVERTER_SHA, 'Frozen PR converter changed')
    spec = importlib.util.spec_from_file_location('frozen_x14_converter', str(CONVERTER))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    require(module.FORMAT == FORMAT, 'Converter format disagrees')
    return module


def _export_integer_case(folder, x, w, bias, description):
    converter = converter_module()
    import numpy as np
    x, w, bias = np.asarray(x, dtype=np.int64), np.asarray(w, dtype=np.int64), np.asarray(bias, dtype=np.int64)
    ref = converter.reference(x, w, bias)
    folder.mkdir(parents=True, exist_ok=False)
    payloads = {'load.hex': converter.encode(converter.pack(x, w, bias), 16)}
    payloads.update({key+'.hex': converter.encode(value, FILES[key+'.hex'][0]) for key, value in ref.items()})
    for name, payload in payloads.items():
        (folder/name).write_bytes(payload)
    save(folder/'layout.json', dict(schema=SOURCE_SCHEMA, format=FORMAT, load_words=23488,
        outputs=25344, bias_storage_bits=40, directed=description,
        files={name: dict(bytes=len(payload), sha256=hashlib.sha256(payload).hexdigest())
               for name, payload in payloads.items()}))
    return inspect_case(folder)


def local14(float_root, output):
    """Use the exact B0 fixed float matrices, quantized afresh with PR #9."""
    import numpy as np
    converter = converter_module()
    float_root, output = Path(float_root), Path(output)
    require(not output.exists(), 'local14 destination exists')
    output.mkdir(parents=True)
    cases = []
    for layer in range(1, 13):
        name = 'layer_%02d' % layer
        original = float_root/name/'float_tensors.npz'
        with np.load(str(original), allow_pickle=False) as arrays:
            y = arrays['Y_float'].astype(np.float64)
            audit = converter.export_layer(output/'source'/name, arrays['X'], arrays['W'], arrays['b'], layer, y)
        result = np.asarray(hex_values(output/'source'/name/'result.hex', 25344, 16, True)).reshape(99, 256)/4096.0
        error = result-y
        sse, energy = float(np.sum(error*error)), float(np.sum(y*y))
        audit.update(source_float_sha256=sha(original), source_float_path=str(original.resolve()),
                     sse=sse, reference_energy=energy, fresh_float_reference=True)
        save(output/'source'/name/'conversion_audit.json', audit)
        cases.append(dict(name=name, conversion=audit))
    x = [[(-8192, 8191, 0, 1, -1)[row % 5] for _ in range(64)] for row in range(99)]
    w = [[(-2048, 2047, 0, 1, -1)[col % 5] for col in range(256)] for _ in range(64)]
    bias = [(-(1 << 31), (1 << 31)-1, 0, -512, 512)[col % 5] for col in range(256)]
    cases.append(dict(name='extremes', conversion=_export_integer_case(output/'source/extremes', x, w, bias,
        'Every PE sees 64 same-sign extreme products, cancellation/zero and signed32 extreme biases.')))
    # Zero products isolate every positive/negative rounding boundary, including
    # the asymmetric signed16 upper/lower saturation transitions.
    rounding = [0, 511, 512, 513, -511, -512, -513, 32767*1024+511,
                32767*1024+512, -32768*1024-511, -32768*1024-512,
                32767*1024, -32768*1024, (1 << 31)-1, -(1 << 31)]
    cases.append(dict(name='rounding', conversion=_export_integer_case(output/'source/rounding',
        [[0]*64 for _ in range(99)], [[0]*256 for _ in range(64)],
        [rounding[c % len(rounding)] for c in range(256)], 'Half-away rounding and exact/overflow signed16 boundaries.')))
    for item in cases:
        name = item['name']
        item['prepared'] = prepare_case(output/'source'/name, output/'prepared'/name)
        verify_prepared(output/'source'/name, output/'prepared'/name)
    result = dict(schema='arch03-n1-local14-v1', status='software_passed', cases=cases,
                  format=FORMAT, tasks=14, outputs=14*25344, converter_commit=PR_COMMIT,
                  converter_sha256=CONVERTER_SHA, source_float_root=str(float_root.resolve()),
                  rtl_executed=False, official_accuracy_verified=False)
    save(output/'manifest.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command')
    p = sub.add_parser('prepare'); p.add_argument('source', type=Path); p.add_argument('destination', type=Path)
    p.add_argument('--force-raw', action='store_true')
    p = sub.add_parser('verify'); p.add_argument('source', type=Path); p.add_argument('destination', type=Path)
    p = sub.add_parser('check'); p.add_argument('source', type=Path)
    p = sub.add_parser('local14'); p.add_argument('float_root', type=Path); p.add_argument('output', type=Path)
    args = parser.parse_args()
    if args.command == 'prepare': result = prepare_case(args.source, args.destination, args.force_raw)
    elif args.command == 'verify': result = verify_prepared(args.source, args.destination)
    elif args.command == 'check': result = inspect_case(args.source)
    elif args.command == 'local14':
        result = local14(args.float_root, args.output)
        result = {key: value for key, value in result.items() if key != 'cases'}
    else: parser.error('Choose prepare, verify, check or local14')
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
