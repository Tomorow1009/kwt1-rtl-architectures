"""Prepare independent C80 software inputs from original group8 references.

No DUT/firmware execution or hardware acceptance. Source files remain intact.
The internal canonical geometry and integer oracle are unchanged from N1;
only the external lossless stream has the new C80 identity.
"""
import argparse
import json
from pathlib import Path
import struct

import c80_codec as codec
import n1_data as source_data

require, read, save, sha = source_data.require, source_data.read, source_data.save, source_data.sha
geometry = source_data.geometry
FORMAT, FILES = source_data.FORMAT, source_data.FILES
LAYOUT_SCHEMA = 'kwt1-arch03-c80-tile16-x14-w12-b32-v1'
CASE_SCHEMA = 'arch03-c80-case-v1'


def dependencies():
    return {Path(m.__file__).name: sha(m.__file__) for m in
            (source_data, geometry, codec, codec.candidate, codec.n1_codec)}


def prepare_case(source, destination, force_raw=False, layout_id=codec.LAYOUT):
    source, destination = Path(source), Path(destination)
    require(layout_id == codec.LAYOUT, 'C80 requires layout 0x00100006')
    require(not destination.exists(), 'Preserve earlier prepared C80 inputs')
    before = {name: sha(source/name) for name in list(FILES) + ['layout.json']}
    deps = dependencies()
    audit = source_data.inspect_case(source)
    meta, words, _, _ = source_data.source_case(source)
    packed = geometry.reorder_words(words)
    geometry.verify_reorder(words, packed)
    raw = struct.pack('<23488H', *packed)
    encoded = codec.encode(raw, force_raw=force_raw)
    require(codec.decode(encoded) == raw, 'C80 reconstruction mismatch')
    require(codec.n1_codec.verify_coordinates(raw, codec.decode_wire(encoded)) == 23488,
            'C80 internal coordinate mismatch')
    require(dependencies() == deps and all(sha(source/n) == h for n, h in before.items()),
            'Source or software changed during C80 preparation')
    destination.mkdir(parents=True)
    (destination/'load.bin').write_bytes(raw)
    source_data.write_hex(destination/'load.hex', packed, 16)
    source_data.write_hex(destination/'load32.hex', struct.unpack('<11744I', raw), 32)
    for name in FILES:
        if name != 'load.hex':
            (destination/name).write_bytes((source/name).read_bytes())
    source_data._write_npz(destination/'expected.npz', [
        (name, (99, 256), source_data.hex_values(source/(name+'.hex'), 25344,
         FILES[name+'.hex'][0], name != 'saturated')) for name in ('total', 'result', 'saturated')])
    layout = dict(schema=LAYOUT_SCHEMA, shift=10, numeric_format=FORMAT,
        numeric_format_id=codec.NUMERIC_FORMAT, layout=codec.LAYOUT,
        input_bytes=codec.CANONICAL_BYTES, output_bytes=50688,
        source_layout_sha256=before['layout.json'],
        source_sha256={name: meta['files'][name]['sha256'] for name in FILES},
        canonical_files=['load.bin', 'load.hex', 'load32.hex'],
        verification_only=['total.hex', 'result.hex', 'saturated.hex', 'expected.npz'],
        original_coordinates_checked=22976, original_bias_parts_checked=768,
        layout_script_sha256=sha(__file__), dependencies_sha256=deps, reference_audit=audit,
        sha256={p.name: sha(p) for p in destination.iterdir() if p.is_file()},
        rtl_executed=False, stage_accepted=False)
    save(destination/'layout_manifest.json', layout)
    (destination/'codec.bin').write_bytes(encoded)
    source_data.write_hex(destination/'codec32.hex', struct.unpack('<%dI' % (len(encoded)//4), encoded), 32)
    record = codec.describe(encoded)
    record.update(schema=CASE_SCHEMA, numeric_format=FORMAT,
        source_layout_sha256=layout['source_layout_sha256'],
        tile_layout_sha256=sha(destination/'layout_manifest.json'),
        source_sha256=sha(destination/'load.bin'), force_raw=force_raw,
        runtime_inputs=['codec32.hex'],
        files={name: sha(destination/name) for name in ('codec.bin', 'codec32.hex')},
        codec_script_sha256=sha(codec.__file__), preparation_script_sha256=sha(__file__),
        dependencies_sha256=deps, pr_converter_commit=source_data.PR_COMMIT,
        pr_converter_sha256=source_data.CONVERTER_SHA, stage_accepted=False)
    save(destination/'codec.json', record)
    require(all(sha(source/n) == h for n, h in before.items()), 'Source changed while copying')
    return record


def verify_prepared(source, destination):
    source, destination = Path(source), Path(destination)
    meta, words, _, _ = source_data.source_case(source)
    layout, record = read(destination/'layout_manifest.json'), read(destination/'codec.json')
    require(layout.get('schema') == LAYOUT_SCHEMA and layout['shift'] == 10 and
        layout['layout'] == codec.LAYOUT and layout['numeric_format_id'] == codec.NUMERIC_FORMAT and
        layout['numeric_format'] == FORMAT and layout['input_bytes'] == codec.CANONICAL_BYTES and
        layout['output_bytes'] == 50688, 'Wrong C80 prepared layout or numeric identity')
    require(layout['source_layout_sha256'] == sha(source/'layout.json') and
        layout['source_sha256'] == {name: meta['files'][name]['sha256'] for name in FILES} and
        layout['layout_script_sha256'] == sha(__file__) and layout['dependencies_sha256'] == dependencies(),
        'C80 source/preparation changed')
    geometry.check_hashes(destination, layout['sha256'])
    raw = (destination/'load.bin').read_bytes()
    packed = list(struct.unpack('<23488H', raw))
    geometry.verify_reorder(words, packed)
    require(packed == source_data.hex_values(destination/'load.hex', 23488, 16), 'C80 halfword order')
    require(list(struct.unpack('<11744I', raw)) == source_data.hex_values(destination/'load32.hex', 11744, 32),
            'C80 canonical word byte order')
    for name in FILES:
        if name != 'load.hex':
            require(sha(destination/name) == meta['files'][name]['sha256'], 'C80 reference copy changed')
    require(record.get('schema') == CASE_SCHEMA and record['numeric_format'] == FORMAT and
        record['shift'] == 10 and record['tile_layout_sha256'] == sha(destination/'layout_manifest.json') and
        record['source_layout_sha256'] == layout['source_layout_sha256'] and
        record['source_sha256'] == sha(destination/'load.bin') and
        record['codec_script_sha256'] == sha(codec.__file__) and
        record['preparation_script_sha256'] == sha(__file__) and record['dependencies_sha256'] == dependencies(),
        'Wrong C80 codec/source identity')
    geometry.check_hashes(destination, record['files'])
    encoded = (destination/'codec.bin').read_bytes()
    require(codec.decode(encoded) == raw, 'C80 reconstruction changed')
    codec.n1_codec.verify_coordinates(raw, codec.decode_wire(encoded))
    require(list(struct.unpack('<%dI' % (len(encoded)//4), encoded)) ==
        source_data.hex_values(destination/'codec32.hex', len(encoded)//4, 32), 'C80 encoded byte order')
    for key, value in codec.describe(encoded).items():
        require(record[key] == value, 'C80 codec descriptor changed: ' + key)
    return record


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('command', choices=['prepare', 'verify'])
    p.add_argument('source', type=Path); p.add_argument('destination', type=Path)
    p.add_argument('--force-raw', action='store_true')
    a = p.parse_args()
    result = (prepare_case(a.source, a.destination, a.force_raw) if a.command == 'prepare'
              else verify_prepared(a.source, a.destination))
    print(json.dumps(result, sort_keys=True))
