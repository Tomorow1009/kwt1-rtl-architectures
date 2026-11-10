"""Lossless transport v2 for the frozen tile16 Q12 stream (Python >=3.6).

No quantization, training, hardware acceptance or output data compression.
The corresponding RTL must consume bytes only after successful shared writes.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path

MAGIC = 0x3243574b  # little endian ASCII KWC2
VERSION = 0x00020000
LAYOUT = 0x00100002
RAW_BYTES = 46976
HALVES = 23488
HEADER_BYTES = 32
MAX_BYTES = RAW_BYTES + HEADER_BYTES
RAW_FLAG = 1


def _raw_check(raw):
    if not isinstance(raw, bytes) or len(raw) != RAW_BYTES:
        raise ValueError('Expected 46976 tile16 bytes')
    for tile in range(16):
        for lane in range(16):
            if raw[12672 + tile * 2144 + 2048 + lane * 6 + 5]:
                raise ValueError('Nonzero bias padding')


def signed_width(values):
    if not 1 <= len(values) <= 64:
        raise ValueError('Block count must be 1..64')
    if any(type(v) is not int or not -32768 <= v <= 32767 for v in values):
        raise ValueError('Block values must be signed16 integers')
    # -1 and 0 require one bit. A negative v fits when ~v fits b-1 bits.
    return max(1, max((v if v >= 0 else ~v).bit_length() + 1 for v in values))


def encode_block(values):
    width = signed_width(values)
    packed = 0
    mask = (1 << width) - 1
    for index, value in enumerate(values):
        packed |= (value & mask) << (index * width)
    size = ((len(values) * width + 31) // 32) * 4
    header = width | ((len(values) - 1) << 5)
    return struct.pack('<I', header) + packed.to_bytes(size, 'little')


def decode_block(data, offset=0, expected_count=None):
    if offset < 0 or offset % 4 or offset + 4 > len(data):
        raise ValueError('Truncated or misaligned block header')
    word = struct.unpack_from('<I', data, offset)[0]
    width, count = word & 31, ((word >> 5) & 63) + 1
    if word >> 11 or not 1 <= width <= 16:
        raise ValueError('Illegal block header')
    if expected_count is not None and count != expected_count:
        raise ValueError('Wrong block element count')
    size = ((count * width + 31) // 32) * 4
    end = offset + 4 + size
    if end > len(data):
        raise ValueError('Truncated block payload')
    bits = int.from_bytes(data[offset + 4:end], 'little')
    if bits >> (count * width):
        raise ValueError('Nonzero block padding')
    values = []
    for index in range(count):
        v = (bits >> (index * width)) & ((1 << width) - 1)
        values.append(v - (1 << width) if v & (1 << (width - 1)) else v)
    return values, end


def _segments():
    yield 0, 6336, False
    for tile in range(16):
        start = 6336 + tile * 1072
        yield start, 1024, False
        yield start + 1024, 48, True


def encode(raw, force_raw=False):
    _raw_check(raw)
    parts = []
    if not force_raw:
        for start, count, bias in _segments():
            if bias:
                parts.append(raw[start * 2:(start + count) * 2])
            else:
                for i in range(start, start + count, 64):
                    parts.append(encode_block(list(struct.unpack_from('<64h', raw, i * 2))))
    body = b''.join(parts)
    flags = RAW_FLAG if force_raw or len(body) >= RAW_BYTES else 0
    if flags:
        body = raw
    total = HEADER_BYTES + len(body)
    return struct.pack('<8I', MAGIC, VERSION, LAYOUT, flags, total, HALVES,
                       RAW_BYTES, 0) + body


def read_header(data):
    if not isinstance(data, bytes) or len(data) < HEADER_BYTES or len(data) % 4:
        raise ValueError('Invalid stream length/alignment')
    magic, version, layout, flags, total, halves, raw_bytes, reserved = struct.unpack_from('<8I', data)
    if (magic, version, layout, halves, raw_bytes, reserved) != (MAGIC, VERSION, LAYOUT, HALVES, RAW_BYTES, 0):
        raise ValueError('Unsupported stream header')
    if flags not in (0, RAW_FLAG) or total != len(data) or total > MAX_BYTES:
        raise ValueError('Invalid flags or encoded length')
    if flags == RAW_FLAG and total != MAX_BYTES:
        raise ValueError('Wrong raw length')
    return dict(version=version, layout=layout, raw=bool(flags), encoded_bytes=total,
                decoded_halfwords=halves)


def decode(data):
    info = read_header(data)
    if info['raw']:
        raw = data[HEADER_BYTES:]
    else:
        offset, parts = HEADER_BYTES, []
        for start, count, bias in _segments():
            if bias:
                end = offset + count * 2
                if end > len(data):
                    raise ValueError('Truncated bias')
                parts.append(data[offset:end])
                offset = end
            else:
                for _ in range(count // 64):
                    values, offset = decode_block(data, offset, expected_count=64)
                    parts.append(struct.pack('<64h', *values))
        if offset != len(data):
            raise ValueError('Trailing stream bytes')
        raw = b''.join(parts)
    _raw_check(raw)
    return raw


def describe(data):
    info = read_header(data)
    decode(data)  # Do not report an unchecked malformed stream.
    if info['raw']:
        prefix = HEADER_BYTES + 7408 * 2
    else:
        prefix = HEADER_BYTES
        for _ in range(99 + 16):
            _, prefix = decode_block(data, prefix, expected_count=64)
        prefix += 96
    info.update(prefix_bytes=prefix, source_words=len(data) // 4,
                transfer_transactions=len(data) // 2 + 12672,
                original_bytes=RAW_BYTES,
                sha256=hashlib.sha256(data).hexdigest(),
                rtl_verified=False, cpu_executed=False)
    return info


def export(raw_path, output, force_raw=False):
    raw_path, output = Path(raw_path), Path(output)
    raw = raw_path.read_bytes()
    data = encode(raw, force_raw=force_raw)
    if decode(data) != raw:
        raise AssertionError('Lossless reconstruction failed')
    info = describe(data)
    info.update(schema='arch03-icb32-lossless-v2',
                source_sha256=hashlib.sha256(raw).hexdigest(),
                runtime_inputs=['load.bin', 'load32.hex'])
    output.mkdir(parents=True, exist_ok=False)
    (output / 'load.bin').write_bytes(data)
    (output / 'load32.hex').write_text(''.join('%08x\n' % v[0] for v in struct.iter_unpack('<I', data)), encoding='ascii')
    (output / 'codec.json').write_text(json.dumps(info, indent=2, sort_keys=True) + '\n', encoding='utf8')
    return info


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--raw-tile16', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--force-raw', action='store_true')
    args = ap.parse_args()
    print(json.dumps(export(args.raw_tile16, args.output, args.force_raw), sort_keys=True))
