"""Offline C80 candidate, not a frozen hardware ABI.

Keeps mathematical coordinates and the W0/b0, X, W1/b1... stream order.
Rows reset prediction every eight *logical* rows, independent of PE count.
All block descriptors are byte aligned; only the complete stream is padded
to 32 bits. Bias is signed32. No lossy transform, training or RTL execution.
"""
from functools import lru_cache
import struct

import n1_codec
import systolic_b_codec as legacy

MAGIC = 0x50303843  # C80P: experimental software, never an accepted DUT layout.
VERSION = 1
RESET_ROWS = 8
RAW_BYTES = 46464
HEADER_BYTES = 32
LIMIT = 15


def need(ok, message):
    if not ok:
        raise ValueError(message)


def width(values):
    return max((v.bit_length() + 1 if v >= 0 else (~v).bit_length() + 1
                for v in values), default=0) if any(values) else 0


def signed(value, bits):
    return value - (1 << bits) if bits and value & (1 << (bits - 1)) else value


def pack(fields):
    word = offset = 0
    for value, bits in fields:
        need(0 <= bits <= 32, 'Invalid field width')
        need(-(1 << (bits - 1)) <= value < (1 << bits) if bits else value == 0,
             'Field does not fit')
        word |= (value & ((1 << bits) - 1)) << offset
        offset += bits
    return word.to_bytes((offset + 7) // 8, 'little')


class Reader:
    def __init__(self, data, offset):
        self.data, self.begin, self.bit = data, offset, offset * 8

    def get(self, count):
        need(count >= 0 and self.bit + count <= 8 * len(self.data), 'Truncated payload')
        if not count:
            return 0
        start, shift = divmod(self.bit, 8)
        end = (self.bit + count + 7) // 8
        value = (int.from_bytes(self.data[start:end], 'little') >> shift) & ((1 << count) - 1)
        self.bit += count
        return value

    def finish(self):
        pad = (-self.bit) % 8
        need(self.get(pad) == 0, 'Nonzero block padding')
        return self.bit // 8


def zigzag(value):
    return 2 * value if value >= 0 else -2 * value - 1


def rice_cost(values, k, raw_bits):
    return sum((LIMIT + raw_bits) if (zigzag(v) >> k) >= LIMIT
               else (zigzag(v) >> k) + 1 + k for v in values)


def rice_k(values, raw_bits):
    return min(range(12), key=lambda k: (rice_cost(values, k, raw_bits), k))


def rice_fields(value, k, raw_bits):
    need(-(1 << (raw_bits - 1)) <= value < (1 << (raw_bits - 1)), 'Rice escape overflow')
    u = zigzag(value)
    quotient = u >> k
    if quotient >= LIMIT:
        return [((1 << LIMIT) - 1, LIMIT), (value, raw_bits)]
    return [((1 << quotient) - 1, quotient), (0, 1), (u & ((1 << k) - 1), k)]


def rice_read(reader, k, raw_bits):
    quotient = 0
    while quotient < LIMIT and reader.get(1):
        quotient += 1
    if quotient == LIMIT:
        return signed(reader.get(raw_bits), raw_bits)
    value = (quotient << k) | reader.get(k)
    return -(value // 2) - 1 if value & 1 else value // 2


def descriptor(mode, parameter=0):
    need(0 <= mode < 16 and 0 <= parameter < 16, 'Descriptor overflow')
    return struct.pack('<H', mode | parameter << 4)


def descriptor_read(data, offset):
    need(offset + 2 <= len(data), 'Truncated descriptor')
    word = struct.unpack_from('<H', data, offset)[0]
    need(word >> 8 == 0, 'Reserved descriptor bits')
    return word & 15, (word >> 4) & 15, offset + 2


def encode_row(values, previous=None):
    values = tuple(values)
    need(len(values) == 64 and all(type(v) is int and -8192 <= v <= 8191 for v in values), 'X14 row')
    need(previous is None or len(previous) == 64, 'Previous row size')
    sw = width(values)
    base, delta_width = min(values), (max(values) - min(values)).bit_length()
    adjacent = [values[i] - values[i - 1] for i in range(1, 64)]
    aw = width(adjacent)
    candidates = [
        ('signed', descriptor(1, sw) + pack((v, sw) for v in values)),
        ('raw14', descriptor(0, 14) + pack((v, 14) for v in values)),
        ('delta', descriptor(2, delta_width) + struct.pack('<h', base) +
         pack((v - base, delta_width) for v in values)),
        ('adjacent_fixed', descriptor(3, aw) + struct.pack('<h', values[0]) +
         pack((v, aw) for v in adjacent))]
    k = rice_k(adjacent, 15)
    candidates.append(('adjacent_rice', descriptor(5, k) + struct.pack('<h', values[0]) +
                       pack(f for v in adjacent for f in rice_fields(v, k, 15))))
    if previous is not None:
        residual = [a - b for a, b in zip(values, previous)]
        rw, k = width(residual), rice_k(residual, 15)
        candidates += [
            ('previous_fixed', descriptor(4, rw) + pack((v, rw) for v in residual)),
            ('previous_rice', descriptor(6, k) + pack(f for v in residual for f in rice_fields(v, k, 15)))]
    name, payload = min(candidates, key=lambda pair: len(pair[1]))
    return payload, dict(mode=name, bytes=len(payload), candidates={n: len(p) for n, p in candidates})


def decode_row(data, offset, previous=None):
    mode, parameter, offset = descriptor_read(data, offset)
    need(mode in range(7), 'Unsupported X mode')
    need(parameter <= (11 if mode in (5, 6) else 15), 'Unsupported X parameter')
    need(mode not in (0, 1, 2) or parameter <= 14, 'X width exceeds14')
    need(mode != 0 or parameter == 14, 'Wrong raw X width')
    need(mode not in (4, 6) or previous is not None, 'Missing previous-row initial state')
    initial = 0
    if mode in (2, 3, 5):
        need(offset + 2 <= len(data), 'Truncated predictor initial value')
        initial = struct.unpack_from('<h', data, offset)[0]
        need(-8192 <= initial <= 8191, 'Noncanonical predictor initial value')
        offset += 2
    reader = Reader(data, offset)
    count = 63 if mode in (3, 5) else 64
    if mode in (5, 6):
        values = [rice_read(reader, parameter, 15) for _ in range(count)]
    else:
        values = [reader.get(parameter) for _ in range(count)]
        if mode != 2:
            values = [signed(v, parameter) for v in values]
    if mode == 2:
        values = [initial + v for v in values]
    elif mode in (3, 5):
        rebuilt = [initial]
        for v in values:
            rebuilt.append(rebuilt[-1] + v)
        values = rebuilt
    elif mode in (4, 6):
        values = [v + p for v, p in zip(values, previous)]
    need(len(values) == 64 and all(-8192 <= v <= 8191 for v in values), 'X reconstruction exceeds14')
    return values, reader.finish()


@lru_cache(maxsize=256)
def encode_weight(values):
    need(len(values) == 1024 and all(type(v) is int and -2048 <= v <= 2047 for v in values), 'W12 tile')
    widths = [width(values[lane::16]) for lane in range(16)]
    block_widths = [width(values[i:i + 64]) for i in range(0, 1024, 64)]
    table = lambda seq: pack((v, 4) for v in seq)
    ks = [rice_k(values[lane::16], 12) for lane in range(16)]
    k = rice_k(values, 12)
    candidates = [
        ('column', descriptor(1) + table(widths) + pack((v, widths[i % 16]) for i, v in enumerate(values))),
        ('raw12', descriptor(0, 12) + pack((v, 12) for v in values)),
        ('block64', descriptor(2) + table(block_widths) + pack((v, block_widths[i // 64]) for i, v in enumerate(values))),
        ('rice', descriptor(3, k) + pack(f for v in values for f in rice_fields(v, k, 12))),
        ('column_rice', descriptor(4) + table(ks) + pack(f for i, v in enumerate(values)
                                                        for f in rice_fields(v, ks[i % 16], 12)))]
    name, payload = min(candidates, key=lambda pair: len(pair[1]))
    return payload, dict(mode=name, bytes=len(payload), candidates={n: len(p) for n, p in candidates})


def decode_weight(data, offset):
    mode, parameter, offset = descriptor_read(data, offset)
    need(mode in range(5), 'Unsupported W mode')
    need((mode == 0 and parameter == 12) or (mode == 3 and parameter <= 11) or
         (mode in (1, 2, 4) and parameter == 0), 'Invalid W parameter')
    reader = Reader(data, offset)
    table = [reader.get(4) for _ in range(16)] if mode in (1, 2, 4) else None
    need(table is None or max(table) <= (11 if mode == 4 else 12), 'Invalid W table')
    values = []
    for i in range(1024):
        if mode in (3, 4):
            value = rice_read(reader, parameter if mode == 3 else table[i % 16], 12)
        else:
            bits = parameter if mode == 0 else table[i % 16 if mode == 1 else i // 64]
            value = signed(reader.get(bits), bits)
        need(-2048 <= value <= 2047, 'W reconstruction exceeds12')
        values.append(value)
    return values, reader.finish()


def unpack_canonical(raw):
    n1_codec.validate_raw(raw)
    x = [list(struct.unpack_from('<64h', raw, row * 128)) for row in range(99)]
    weights, biases = [], []
    for tile in range(16):
        start = 12672 + tile * 2144
        weights.append(tuple(struct.unpack_from('<1024h', raw, start)))
        biases.append([struct.unpack_from('<i', raw, start + 2048 + lane * 6)[0] for lane in range(16)])
    return x, weights, biases


def encode(raw, profile='candidate', force_raw=False):
    need(profile in ('candidate', 'compact_bias_v3'), 'Unknown offline profile')
    x, weights, biases = unpack_canonical(raw)
    pieces, rows, tiles = [], [], []
    for tile in range(16):
        payload, detail = (encode_weight(weights[tile]) if profile == 'candidate'
                           else legacy.encode_weight(weights[tile]))
        pieces.append(payload + struct.pack('<16i', *biases[tile]));tiles.append(detail)
        if tile == 0:
            for row in range(99):
                previous = x[row - 1] if row % RESET_ROWS else None
                payload, detail = (encode_row(x[row], previous) if profile == 'candidate'
                                   else legacy.encode_row(x[row]))
                pieces.append(payload);rows.append(detail)
    body = b''.join(pieces)
    encoded_body = body + bytes((-len(body)) % 4)
    raw_fallback = force_raw or len(encoded_body) >= RAW_BYTES
    if raw_fallback:
        pieces = []
        for tile in range(16):
            pieces.append(struct.pack('<1024h16i', *(weights[tile] + tuple(biases[tile]))))
            if tile == 0:
                pieces.append(struct.pack('<6336h', *(v for row in x for v in row)))
        encoded_body = b''.join(pieces)
        need(len(encoded_body) == RAW_BYTES, 'Raw size')
    header = struct.pack('<8I', MAGIC, VERSION, int(profile == 'compact_bias_v3'),
                         int(raw_fallback), HEADER_BYTES + len(encoded_body), RAW_BYTES,
                         n1_codec.NUMERIC_FORMAT, RESET_ROWS)
    return header + encoded_body, dict(profile=profile, bytes=len(header) + len(encoded_body),
        raw=raw_fallback, header_bytes=32, bias_bytes=1024,
        trailing_padding=0 if raw_fallback else (-len(body)) % 4,
        x_blocks=rows, weight_tiles=tiles, software_only=True, rtl_abi_frozen=False)


def decode(data):
    need(isinstance(data, bytes) and len(data) >= HEADER_BYTES and len(data) % 4 == 0, 'Stream alignment')
    magic, ver, profile, flags, length, raw_bytes, numeric, reset = struct.unpack_from('<8I', data)
    need((magic, ver, raw_bytes, numeric, reset) == (MAGIC, VERSION, RAW_BYTES,
         n1_codec.NUMERIC_FORMAT, RESET_ROWS), 'Unsupported candidate header')
    need(profile in (0, 1) and flags in (0, 1) and length == len(data) and
         length <= HEADER_BYTES + RAW_BYTES, 'Candidate length/flags')
    need(not flags or length == HEADER_BYTES + RAW_BYTES, 'Raw length mismatch')
    x, weights, biases, offset = [], [], [], HEADER_BYTES
    for tile in range(16):
        if flags:
            need(offset + 2048 <= len(data), 'Truncated raw W')
            values = list(struct.unpack_from('<1024h', data, offset));offset += 2048
        elif profile:
            values, offset = legacy.decode_weight(data, offset)
        else:
            values, offset = decode_weight(data, offset)
        need(all(-2048 <= v <= 2047 for v in values), 'W12 sign extension')
        weights.append(values)
        need(offset + 64 <= len(data), 'Truncated bias32')
        biases.append(list(struct.unpack_from('<16i', data, offset)));offset += 64
        if tile == 0:
            for row in range(99):
                if flags:
                    need(offset + 128 <= len(data), 'Truncated raw X')
                    values = list(struct.unpack_from('<64h', data, offset));offset += 128
                elif profile:
                    values, offset = legacy.decode_row(data, offset)
                else:
                    values, offset = decode_row(data, offset, x[-1] if row % RESET_ROWS else None)
                need(all(-8192 <= v <= 8191 for v in values), 'X14 sign extension')
                x.append(values)
    need(0 <= len(data) - offset <= 3 and not any(data[offset:]), 'Trailing candidate bytes')
    # Return coordinate matrices, not the encoder's raw stream permutation.
    w = [[weights[col // 16][k * 16 + col % 16] for col in range(256)] for k in range(64)]
    b = [biases[col // 16][col % 16] for col in range(256)]
    return x, w, b
