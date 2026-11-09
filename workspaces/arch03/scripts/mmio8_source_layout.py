"""Wrap unchanged legacy tile8 halfwords as a little-endian 32-bit ICB source.

No quantization, tile reorder or reference computation. Python 3.6 stdlib only.
Original expected files stay verification-only and never enter ITCM or hardware.
"""
import argparse
from pathlib import Path
import struct
from dma16_batch import CASES14, FILES, check_hashes, hex_values, read, require, save, sha, source_case

SCHEMA = 'kwt1-arch03-mmio8-source-q12-v1'


def verify_words(original, words32, payload):
    require(len(original) == 23488 and len(words32) == 11744 and len(payload) == 46976, 'Wrong input size')
    # Decode every original coordinate directly, independently of struct.pack.
    for index, expected in enumerate(original):
        actual = (words32[index//2] >> (16*(index % 2))) & 65535
        require(actual == expected, 'Original halfword differs at '+str(index))
        require(payload[2*index] == (expected & 255) and payload[2*index+1] == expected >> 8,
                'Source byte order differs at '+str(index))
    for col in range(256):
        high = 6336+(col//8)*536+512+(col % 8)*3+2
        require(original[high] < 256, 'Bias40 high padding is not zero')


def prepare_case(source, destination):
    source, destination = Path(source), Path(destination)
    require(not destination.exists(), 'Prepared directory exists')
    meta, words, _, _ = source_case(source)
    payload = struct.pack('<23488H', *words)
    packed = list(struct.unpack('<11744I', payload))
    verify_words(words, packed, payload)
    destination.mkdir(parents=True)
    for name in sorted(FILES):
        (destination/name).write_bytes((source/name).read_bytes())
    (destination/'load.bin').write_bytes(payload)
    (destination/'load32.hex').write_bytes(''.join('%08x\n' % w for w in packed).encode('ascii'))
    record = dict(schema=SCHEMA, shift=meta['shift'], input_bytes=46976, output_bytes=50688,
        source_layout_sha256=sha(source/'layout.json'), source_sha256=meta['sha256'],
        layout='X6336 row-major; 32 tiles of W64x8 k-lane then bias8x3; unchanged original stream',
        packing='two uint16 per little-endian uint32; earlier halfword in bits15:0',
        alignment_bytes=4, source_base='0xb0000000', layout_tag='0x00080001',
        numeric_format=dict(input='signed16 Q12', weight='signed16 Q12', bias='signed40 Q24', result='signed16 Q12'),
        quantization='unchanged upstream quantization and references; no conversion beyond packing',
        runtime_inputs=['load.bin', 'load.hex', 'load32.hex'], verification_only=sorted(FILES-{'load.hex'}),
        input_halfwords_checked=23488, bias_high_parts_checked=256, layout_script_sha256=sha(__file__),
        source_validation_script_sha256=sha(Path(__file__).with_name('dma16_batch.py')),
        hardware_executed=False, sha256={p.name: sha(p) for p in destination.iterdir() if p.is_file()})
    save(destination/'layout_manifest.json', record)
    return record


def verify_prepared(source, destination):
    source, destination = Path(source), Path(destination)
    record = read(destination/'layout_manifest.json')
    meta, original, _, _ = source_case(source)
    require(record['schema'] == SCHEMA and record['shift'] == meta['shift'] and
            record['source_layout_sha256'] == sha(source/'layout.json') and
            record['source_sha256'] == meta['sha256'] and record['layout_script_sha256'] == sha(__file__) and
            record['source_validation_script_sha256'] == sha(Path(__file__).with_name('dma16_batch.py')),
            'Prepared source or script changed')
    check_hashes(destination, record['sha256'])
    for name in FILES:
        require(sha(destination/name) == meta['sha256'][name], 'Original file changed: '+name)
    verify_words(original, hex_values(destination/'load32.hex', 11744, 32), (destination/'load.bin').read_bytes())
    return record


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    require(not a.output.exists(), 'Output exists')
    records = []
    for name in CASES14:
        prepare_case(a.data/name, a.output/name)
        verify_prepared(a.data/name, a.output/name)
        records.append(dict(case=name, layout_manifest_sha256=sha(a.output/name/'layout_manifest.json')))
    save(a.output/'manifest.json', dict(schema=SCHEMA, status='packing_verified', cases=records,
        input_halfwords_checked=14*23488, original_layout_preserved=True, hardware_executed=False))
    print('MMIO8_SOURCE_LAYOUT_PASS cases=14 halfwords=328832 hardware_executed=false')


if __name__ == '__main__':
    main()
