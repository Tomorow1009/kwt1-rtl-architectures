"""Lossless B layout v3. Python >=3.6, integer-only, no model changes.

Canonical input is the already-quantized v1 tile16 byte stream. Wire-decoded
order is W0/bias0, X rows 0..98, W1/bias1 .. W15/bias15. All payloads are
little endian and 32-bit aligned. Hardware must publish only after shared ACK.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path
import icb32_codec as v2

MAGIC, VERSION, LAYOUT = 0x3343574b, 0x00030000, 0x00100003
RAW_BYTES, HALVES, HEADER_BYTES, MAX_BYTES = 46976, 23488, 32, 47008
RAW_FLAG = 1
W_RAW, W_BLOCK, W_COLUMN = 0, 1, 2
X_SIGNED, X_DELTA, X_RAW = 0, 1, 2


def _pack(values, widths):
    bits, pos = 0, 0
    for value, width in zip(values, widths):
        bits |= (value & ((1 << width) - 1)) << pos
        pos += width
    return bits.to_bytes(((pos + 31) // 32) * 4, 'little')


def _unpack(data, offset, widths, signed=True):
    size = ((sum(widths) + 31) // 32) * 4
    if offset % 4 or offset < 0 or offset + size > len(data):
        raise ValueError('Truncated or misaligned payload')
    bits = int.from_bytes(data[offset:offset + size], 'little')
    if bits >> sum(widths):
        raise ValueError('Nonzero payload padding')
    values = []
    for width in widths:
        value = bits & ((1 << width) - 1)
        if signed and width and value & (1 << (width - 1)):
            value -= 1 << width
        values.append(value)
        bits >>= width
    return values, offset + size


def _word(data, offset):
    if offset < 0 or offset % 4 or offset + 4 > len(data):
        raise ValueError('Truncated or misaligned header')
    return struct.unpack_from('<I', data, offset)[0]


def encode_row(values):
    if len(values) != 64:
        raise ValueError('X row must contain 64 values')
    width = v2.signed_width(values)  # Also checks type and signed16 bounds.
    base = min(values)
    delta_width = (max(values) - base).bit_length()
    candidates = [
        (struct.pack('<I', X_RAW | (16 << 2)) + struct.pack('<64h', *values), 'raw'),
        (struct.pack('<I', X_SIGNED | (width << 2)) + _pack(values, [width] * 64), 'signed'),
        (struct.pack('<I', X_DELTA | (delta_width << 2) | ((base & 65535) << 16)) +
         _pack([v - base for v in values], [delta_width] * 64), 'delta')]
    # Stable ties prefer raw, then signed, then delta: simpler decoding.
    chosen = min(candidates, key=lambda x: len(x[0]))
    return chosen[0], dict(mode=chosen[1], bytes=len(chosen[0]),
                           candidates={name: len(data) for data, name in candidates})


def decode_row(data, offset):
    header = _word(data, offset)
    mode, width = header & 3, (header >> 2) & 31
    base = (header >> 16) - (65536 if header & 0x80000000 else 0)
    if header & 0xff80 or mode == 3 or width > 16:
        raise ValueError('Illegal X row header')
    if mode != X_DELTA and (base != 0 or width == 0):
        raise ValueError('Illegal signed/raw row base or width')
    if mode == X_RAW and width != 16:
        raise ValueError('Illegal raw row width')
    values, end = _unpack(data, offset + 4, [width] * 64, signed=mode != X_DELTA)
    if mode == X_DELTA:
        values = [v + base for v in values]
        if any(v < -32768 or v > 32767 for v in values):
            raise ValueError('Delta reconstruction exceeds signed16')
    return values, end


def encode_weight(values):
    if len(values) != 1024:
        raise ValueError('Weight tile must contain 1024 values')
    widths = [v2.signed_width(values[lane::16]) for lane in range(16)]
    table = sum((width - 1) << (4 * lane) for lane, width in enumerate(widths))
    candidates = [
        (struct.pack('<I1024h', W_RAW, *values), 'raw'),
        (struct.pack('<I', W_BLOCK) + b''.join(v2.encode_block(values[k:k + 64])
                                            for k in range(0, 1024, 64)), 'block'),
        (struct.pack('<IQ', W_COLUMN, table) + _pack(values, widths * 64), 'column')]
    chosen = min(candidates, key=lambda x: len(x[0]))
    return chosen[0], dict(mode=chosen[1], bytes=len(chosen[0]),
                           candidates={name: len(data) for data, name in candidates})


def decode_weight(data, offset):
    mode = _word(data, offset)
    offset += 4
    if mode == W_RAW:
        return _unpack(data, offset, [16] * 1024)
    if mode == W_BLOCK:
        values = []
        for _ in range(16):
            block, offset = v2.decode_block(data, offset, expected_count=64)
            values += block
        return values, offset
    if mode == W_COLUMN:
        if offset + 8 > len(data):
            raise ValueError('Truncated column width table')
        table = int.from_bytes(data[offset:offset + 8], 'little')
        widths = [((table >> (4 * lane)) & 15) + 1 for lane in range(16)]
        return _unpack(data, offset + 8, widths * 64)
    raise ValueError('Illegal weight mode/header')


def wire_raw(raw):
    v2._raw_check(raw)
    return raw[12672:14816] + raw[:12672] + raw[14816:]


def encode(raw, force_raw=False):
    v2._raw_check(raw)
    x_parts = [encode_row(list(struct.unpack_from('<64h', raw, row * 128)))[0]
               for row in range(99)]
    w_parts = []
    for tile in range(16):
        offset = 12672 + tile * 2144
        w_parts.append(encode_weight(list(struct.unpack_from('<1024h', raw, offset)))[0]
                       + raw[offset + 2048:offset + 2144])
    body = w_parts[0] + b''.join(x_parts) + b''.join(w_parts[1:])
    flags = RAW_FLAG if force_raw or len(body) >= RAW_BYTES else 0
    if flags:
        body = wire_raw(raw)
    return struct.pack('<8I', MAGIC, VERSION, LAYOUT, flags, len(body) + 32,
                       HALVES, RAW_BYTES, 0) + body


def read_header(data):
    if not isinstance(data, bytes) or len(data) < 32 or len(data) % 4:
        raise ValueError('Invalid stream length/alignment')
    magic, ver, layout, flags, total, halves, raw_bytes, reserved = struct.unpack_from('<8I', data)
    if (magic, ver, layout, halves, raw_bytes, reserved) != (MAGIC, VERSION, LAYOUT, HALVES, RAW_BYTES, 0):
        raise ValueError('Unsupported v3 header')
    if flags not in (0, 1) or total != len(data) or total > MAX_BYTES:
        raise ValueError('Invalid flags or encoded length')
    if flags and total != MAX_BYTES:
        raise ValueError('Wrong raw length')
    return dict(version=ver, layout=layout, raw=bool(flags), encoded_bytes=total,
                decoded_halfwords=halves)


def _read_bias(data, offset):
    if offset + 96 > len(data):
        raise ValueError('Truncated bias')
    bias = data[offset:offset + 96]
    if any(bias[lane * 6 + 5] for lane in range(16)):
        raise ValueError('Nonzero bias padding')
    return bias, offset + 96


def decode_wire(data):
    info = read_header(data)
    if info['raw']:
        wire = data[32:]
        for tile in range(16):
            offset = 0 if tile == 0 else 12672 + tile * 2144
            _read_bias(wire, offset + 2048)
        return wire
    offset, parts = 32, []
    for tile in range(16):
        weights, offset = decode_weight(data, offset)
        bias, offset = _read_bias(data, offset)
        parts.append(struct.pack('<1024h', *weights) + bias)
        if tile == 0:
            for _ in range(99):
                row, offset = decode_row(data, offset)
                parts.append(struct.pack('<64h', *row))
    if offset != len(data):
        raise ValueError('Trailing stream bytes')
    return b''.join(parts)


def decode(data):
    """Return canonical v1 tile16 ordering for compatibility/reference checks."""
    wire = decode_wire(data)
    return wire[2144:14816] + wire[:2144] + wire[14816:]


def verify_coordinates(raw, wire):
    """Independent coordinate audit, not encode/decode inverse permutation reuse."""
    v2._raw_check(raw)
    if len(wire) != RAW_BYTES:
        raise ValueError('Wrong decoded wire length')
    checks = 0
    for row in range(99):
        for k in range(64):
            a, b = (row * 64 + k) * 2, 2144 + (row * 64 + k) * 2
            if raw[a:a + 2] != wire[b:b + 2]:
                raise ValueError('X mismatch row=%d k=%d' % (row, k))
            checks += 1
    for column in range(256):
        tile, lane = divmod(column, 16)
        wire_tile = 0 if tile == 0 else 14816 + (tile - 1) * 2144
        for k in range(64):
            a = 12672 + tile * 2144 + (k * 16 + lane) * 2
            b = wire_tile + (k * 16 + lane) * 2
            if raw[a:a + 2] != wire[b:b + 2]:
                raise ValueError('W mismatch k=%d column=%d' % (k, column))
            checks += 1
        for part in range(3):
            a = 12672 + tile * 2144 + 2048 + lane * 6 + part * 2
            b = wire_tile + 2048 + lane * 6 + part * 2
            if raw[a:a + 2] != wire[b:b + 2]:
                raise ValueError('Bias mismatch column=%d part=%d' % (column, part))
            checks += 1
    return checks


def describe(data):
    info = read_header(data)
    decode_wire(data)
    modes = dict(X={}, W={})
    if info['raw']:
        prefix, all_x = 32 + 2144 + 640, 32 + 2144 + 12672
    else:
        pos, prefix, all_x = 32, None, None
        for tile in range(16):
            mode = _word(data, pos)
            name = ['raw', 'block', 'column'][mode]
            modes['W'][name] = modes['W'].get(name, 0) + 1
            _, pos = decode_weight(data, pos)
            _, pos = _read_bias(data, pos)
            if tile == 0:
                for row in range(99):
                    name = ['signed', 'delta', 'raw'][_word(data, pos) & 3]
                    modes['X'][name] = modes['X'].get(name, 0) + 1
                    _, pos = decode_row(data, pos)
                    if row == 4:
                        prefix = pos
                all_x = pos
    info.update(prefix_bytes=prefix, all_x_bytes=all_x, modes=modes,
                source_words=len(data) // 4, transfer_transactions=len(data) // 2 + 12672,
                original_bytes=RAW_BYTES, sha256=hashlib.sha256(data).hexdigest(),
                rtl_verified=False, cpu_executed=False)
    return info


def export(raw_path, output, force_raw=False):
    raw_path, output = Path(raw_path), Path(output)
    raw = raw_path.read_bytes()
    data = encode(raw, force_raw)
    checked = verify_coordinates(raw, decode_wire(data))
    if decode(data) != raw:
        raise ValueError('Canonical reconstruction mismatch')
    info = describe(data)
    info.update(schema='arch03-systolic-b-lossless-v3', coordinate_halfwords_checked=checked,
                source_sha256=hashlib.sha256(raw).hexdigest())
    output.mkdir(parents=True, exist_ok=False)
    (output / 'load.bin').write_bytes(data)
    (output / 'load32.hex').write_text(''.join('%08x\n' % v[0] for v in struct.iter_unpack('<I', data)), encoding='ascii')
    (output / 'decoded_wire.hex').write_text(''.join('%04x\n' % v[0] for v in struct.iter_unpack('<H', decode_wire(data))), encoding='ascii')
    (output / 'codec.json').write_text(json.dumps(info, indent=2, sort_keys=True) + '\n', encoding='utf8')
    return info


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--raw-tile16', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--force-raw', action='store_true')
    args = ap.parse_args()
    print(json.dumps(export(args.raw_tile16, args.output, args.force_raw), sort_keys=True))
