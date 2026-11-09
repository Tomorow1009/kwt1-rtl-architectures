"""Repack frozen arch03 Q12 cases into the tile16 DMA transport layout.

No training, TensorFlow, new quantization or RTL acceptance is performed here.
Only load.bin/load.hex/load32.hex are runtime inputs. All results are test-only.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import struct

import numpy as np
import numeric

ROWS, DEPTH, COLS, LANES = 99, 64, 256, 16
X_HALVES, TILE_HALVES, TILES = 6336, 1072, 16
INPUT_BYTES, OUTPUT_BYTES = 46976, 50688
SCHEMA = 'kwt1-arch03-dma-tile16-q12-v1'
DEFAULT_CASES = ['layer_%02d' % n for n in range(1, 13)] + ['extremes', 'rounding']


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def save_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True,
                                    ensure_ascii=False, allow_nan=False)+'\n', encoding='utf8')


def pack_tile16(x, w, bias):
    """Emit tile -> reduction coordinate -> lane, followed by each bias."""
    x = numeric.signed_array(x, (ROWS, DEPTH), 16, 'X')
    w = numeric.signed_array(w, (DEPTH, COLS), 16, 'W')
    bias = numeric.signed_array(bias, (COLS,), 40, 'b')
    halves = [int(v) & 0xffff for v in x.flat]
    for tile in range(TILES):
        for k in range(DEPTH):
            for lane in range(LANES):
                halves.append(int(w[k, tile*LANES+lane]) & 0xffff)
        for lane in range(LANES):
            value = int(bias[tile*LANES+lane]) & ((1 << 40)-1)
            halves.extend((value >> shift) & 0xffff for shift in (0, 16, 32))
    return struct.pack('<23488H', *halves)


def verify_coordinates(payload, x, w, bias):
    """Check every original matrix coordinate against a direct byte address.

    Deliberately does not call a tile16 inverse or follow the encoder's loop
    order. W is visited k -> original column, and biases by original column.
    The returned matrices come from the actual transported bytes.
    """
    if not isinstance(payload, bytes) or len(payload) != INPUT_BYTES:
        raise ValueError('Expected exactly 46976 input bytes')
    x = numeric.signed_array(x, (ROWS, DEPTH), 16, 'X')
    w = numeric.signed_array(w, (DEPTH, COLS), 16, 'W')
    bias = numeric.signed_array(bias, (COLS,), 40, 'b')
    decoded = dict(X=np.empty_like(x), W=np.empty_like(w), b=np.empty_like(bias))
    for row in range(ROWS):
        for k in range(DEPTH):
            address = 2*(row*64+k)
            value = struct.unpack_from('<h', payload, address)[0]
            if value != x[row, k]:
                raise ValueError('X coordinate mismatch row=%d k=%d byte=%d' % (row, k, address))
            decoded['X'][row, k] = value
    for k in range(DEPTH):
        for column in range(COLS):
            address = 12672+(column//16)*2144+k*32+(column % 16)*2
            value = struct.unpack_from('<h', payload, address)[0]
            if value != w[k, column]:
                raise ValueError('W coordinate mismatch k=%d column=%d byte=%d' % (k, column, address))
            decoded['W'][k, column] = value
    for column in range(COLS):
        address = 12672+(column//16)*2144+2048+(column % 16)*6
        encoded = payload[address:address+6]
        if encoded[5] != 0:
            raise ValueError('Bias high padding must be zero column=%d' % column)
        value = int.from_bytes(encoded[:5], 'little', signed=True)
        if value != bias[column]:
            raise ValueError('Bias coordinate mismatch column=%d byte=%d' % (column, address))
        decoded['b'][column] = value
    return decoded


def _check_file_hashes(root, entries):
    for name, expected in entries.items():
        if Path(name).name != name or not re.fullmatch(r'[0-9a-f]{64}', expected):
            raise ValueError('Invalid source file/hash entry')
        if sha(root/name) != expected:
            raise ValueError('Source hash mismatch: '+name)


def read_prepared_case(source):
    """Read an existing 8-lane fixture, without changing or requantizing it."""
    source = Path(source)
    layout = read_json(source/'layout.json')
    if layout['load_words'] != 23488 or layout['outputs'] != 25344:
        raise ValueError('Unexpected legacy fixture shape')
    shift = layout['shift']
    numeric.numeric_format(shift)
    required = {'load.hex', 'expected.npz', 'total.hex', 'result.hex', 'saturated.hex'}
    if not required <= set(layout['sha256']):
        raise ValueError('Missing legacy fixture hashes')
    _check_file_hashes(source, layout['sha256'])
    texts = (source/'load.hex').read_text(encoding='ascii').split()
    if len(texts) != 23488 or any(not re.fullmatch(r'[0-9a-fA-F]{4}', t) for t in texts):
        raise ValueError('Invalid 16-bit legacy input HEX')
    quantized = numeric.unpack_words(np.asarray([int(t, 16) for t in texts], dtype=np.int64))
    metadata = dict(kind='directed_fixture', quantization=numeric.numeric_format(shift))
    source_hashes = dict(layout['sha256'], **{'layout.json': sha(source/'layout.json')})
    if (source/'codec.json').exists():
        codec = read_json(source/'codec.json')
        numeric.validate_format(codec['numeric_format'])
        if codec['numeric_format']['shift'] != shift:
            raise ValueError('Conflicting source shift')
        _check_file_hashes(source, codec['sha256'])
        source_hashes.update(codec['sha256'])
        source_hashes['codec.json'] = sha(source/'codec.json')
        metadata = dict(kind='model_fixture', sample_id=codec['sample_id'], layer=codec['layer'],
                        quantization=codec['numeric_format'], source_float_npz_sha256=codec['source_sha256'],
                        clipped=codec['clipped'])
        if (source/'input_integer.npz').exists():
            with np.load(str(source/'input_integer.npz'), allow_pickle=False) as z:
                for key in ('X', 'W', 'b'):
                    if not np.array_equal(quantized[key], z[key]):
                        raise ValueError('Legacy stream differs from original integer coordinates: '+key)
    expected = {}
    recomputed = numeric.integer_model(quantized['X'], quantized['W'], quantized['b'], shift)
    with np.load(str(source/'expected.npz'), allow_pickle=False) as z:
        for key in ('total', 'result', 'saturated'):
            expected[key] = np.array(z[key])
            if not np.array_equal(expected[key], recomputed[key]):
                raise ValueError('Original expected matrix mismatch: '+key)
    return quantized, expected, shift, metadata, source_hashes


def model_provenance(receipt, model_root):
    receipt, model_root = Path(receipt), Path(model_root).resolve()
    data = read_json(receipt)
    if data.get('commit') != '237e4097afd4f6851e0b82f0a8d65c2dfe8eae30' or data.get('all_match') is not True:
        raise ValueError('Unverified upstream model receipt')
    files = {}
    for entry in data['files']:
        path = (model_root/entry['path']).resolve()
        path.relative_to(model_root)
        actual = sha(path)
        if actual != entry['upstream_sha256']:
            raise ValueError('Model source changed: '+entry['path'])
        files[entry['path']] = actual
    return dict(upstream_commit=data['commit'], receipt_sha256=sha(receipt),
                verified_model_files=files, verified_file_count=len(files))


def export_case(source, output, provenance=None):
    source, output = Path(source), Path(output)
    if output.exists():
        raise ValueError('Output already exists; use a new directory')
    q, expected, shift, metadata, sources = read_prepared_case(source)
    payload = pack_tile16(q['X'], q['W'], q['b'])
    transported = verify_coordinates(payload, q['X'], q['W'], q['b'])
    actual = numeric.integer_model(transported['X'], transported['W'], transported['b'], shift)
    for key in ('total', 'result', 'saturated'):
        if not np.array_equal(actual[key], expected[key]):
            raise ValueError('Transported expected matrix mismatch: '+key)
    output.mkdir(parents=True)
    (output/'load.bin').write_bytes(payload)
    (output/'load.hex').write_text(''.join('%04x\n' % v for v in struct.unpack('<23488H', payload)), encoding='ascii')
    (output/'load32.hex').write_text(''.join('%08x\n' % v for v in struct.unpack('<11744I', payload)), encoding='ascii')
    (output/'result.bin').write_bytes(expected['result'].astype('<i2').tobytes(order='C'))
    for name in ('expected.npz', 'total.hex', 'result.hex', 'saturated.hex'):
        shutil.copyfile(str(source/name), str(output/name))
    manifest = dict(schema=SCHEMA, source_case=source.resolve().as_posix(), source_sha256=sources,
        source_metadata=metadata, model=provenance or dict(status='not_supplied'),
        numeric_format=numeric.numeric_format(shift),
        shape=dict(X=[99, 64], W=[64, 256], b=[256], output=[99, 256]),
        layout=dict(input_bytes=INPUT_BYTES, input_halfwords=23488, input_words32=11744,
            output_bytes=OUTPUT_BYTES, output_words32=12672, address_alignment_bytes=4,
            byte_order='little', packing='word32 = first_half | (second_half << 16)',
            X_order='row,k', X_halfwords=X_HALVES, tiles=TILES, lanes=LANES,
            tile_halfwords=TILE_HALVES, tile_bytes=2144, tile_order='tile ascending; W[k,lane]; bias[lane,low16,mid16,high8_zero_pad8]',
            W_byte_address='12672 + (column//16)*2144 + k*32 + (column%16)*2',
            bias_byte_address='12672 + (column//16)*2144 + 2048 + (column%16)*6',
            output_order='row,column', output_byte_address='2*(row*256+column)',
            tiles_detail=[dict(tile=t, first_column=t*16, W_byte_offset=12672+t*2144,
                               bias_byte_offset=14720+t*2144) for t in range(16)]),
        runtime_inputs=['load.bin', 'load.hex', 'load32.hex'],
        verification_only=['expected.npz', 'total.hex', 'result.hex', 'result.bin', 'saturated.hex'],
        verification=dict(all_original_coordinates_checked=22976, transported_outputs_checked=25344,
                          total_result_saturation_bit_exact=True, rtl_verified=False,
                          official_precision_verified=False, hardware_loading_time_excluded=False),
        generator_sha256=sha(__file__), numeric_sha256=sha(Path(numeric.__file__)),
        sha256={p.name: sha(p) for p in output.iterdir() if p.is_file()})
    # 6336 X + 16384 W + 256 bias = 22976 independent original coordinates.
    save_json(output/'layout_manifest.json', manifest)
    verify_export(source, output)
    return manifest


def verify_export(source, output):
    output = Path(output)
    manifest = read_json(output/'layout_manifest.json')
    if manifest['schema'] != SCHEMA:
        raise ValueError('Unexpected tile16 layout schema')
    _check_file_hashes(output, manifest['sha256'])
    q, expected, shift, _, sources = read_prepared_case(source)
    if sources != manifest['source_sha256'] or manifest['numeric_format'] != numeric.numeric_format(shift):
        raise ValueError('Source provenance changed')
    payload = (output/'load.bin').read_bytes()
    decoded = verify_coordinates(payload, q['X'], q['W'], q['b'])
    for filename, code, count in [('load.hex', 'H', 23488), ('load32.hex', 'I', 11744)]:
        words = [int(t, 16) for t in (output/filename).read_text(encoding='ascii').split()]
        if len(words) != count or struct.pack('<%d%s' % (count, code), *words) != payload:
            raise ValueError('HEX/binary packing mismatch: '+filename)
    actual = numeric.integer_model(decoded['X'], decoded['W'], decoded['b'], shift)
    for key in expected:
        if not np.array_equal(actual[key], expected[key]):
            raise ValueError('Output differs from original reference: '+key)
    raw_result = (output/'result.bin').read_bytes()
    if len(raw_result) != OUTPUT_BYTES:
        raise ValueError('Output byte count mismatch')
    # Direct row-major addresses, independent of tile input packing.
    for row in range(ROWS):
        for column in range(COLS):
            if struct.unpack_from('<h', raw_result, 2*(row*256+column))[0] != expected['result'][row, column]:
                raise ValueError('Output row-major coordinate mismatch')
    return dict(status='passed', coordinates=22976, outputs=25344, rtl_verified=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True, help='Existing prepared-case root')
    parser.add_argument('--output', type=Path, required=True, help='New tile16 case root')
    parser.add_argument('--cases', nargs='+', default=DEFAULT_CASES)
    parser.add_argument('--upstream-receipt', type=Path)
    parser.add_argument('--model-root', type=Path)
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    if len(args.cases) != len(set(args.cases)) or any(not re.fullmatch(r'[A-Za-z0-9_-]+', n) for n in args.cases):
        parser.error('Cases must be unique simple directory names')
    if bool(args.upstream_receipt) != bool(args.model_root):
        parser.error('Supply both upstream receipt and model root')
    provenance = model_provenance(args.upstream_receipt, args.model_root) if args.model_root else None
    if not args.verify_only and args.output.exists():
        parser.error('Output root already exists; use a new directory')
    records = []
    for name in args.cases:
        if args.verify_only:
            verify_export(args.source/name, args.output/name)
        else:
            export_case(args.source/name, args.output/name, provenance)
        records.append(dict(case=name, layout_manifest_sha256=sha(args.output/name/'layout_manifest.json')))
        print('DMA16_LAYOUT_PASS case=%s coordinates=22976 outputs=25344' % name, flush=True)
    if not args.verify_only:
        save_json(args.output/'manifest.json', dict(schema=SCHEMA, cases=records,
            source_root=args.source.resolve().as_posix(), model=provenance,
            status='software_layout_verified', rtl_verified=False, official_precision_verified=False))
    print('DMA16_LAYOUT_ALL_PASS cases=%d outputs=%d rtl_verified=false' % (len(records), len(records)*25344))


if __name__ == '__main__':
    main()
