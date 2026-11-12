"""N1 X14/W12/b32 identity over the unchanged B0 v3 lossless payload.

The only wire-format changes are global-header words 2 and 7.  SRAM words,
segment order, bias storage, mode selection and alignment remain unchanged.
Python 3.6 standard library; this module never mutates the B0 codec globals.
"""
import hashlib
from pathlib import Path
import struct

import systolic_b_codec as base

MAGIC, VERSION, LAYOUT = 0x3343574b, 0x00030000, 0x00100004
NUMERIC_FORMAT = 0x000e0c20
RAW_BYTES, HALVES, HEADER_BYTES, MAX_BYTES = 46976, 23488, 32, 47008


def validate_raw(raw):
    """Validate canonical tile16 data without silently truncating containers."""
    if len(raw) != RAW_BYTES:
        raise ValueError('N1 raw length must be 46976 bytes')
    values = struct.unpack('<23488h', raw)
    if any(v < -8192 or v > 8191 for v in values[:6336]):
        raise ValueError('N1 X14 sign extension')
    unsigned = struct.unpack('<23488H', raw)
    for tile in range(16):
        start = 6336 + tile * 1072
        if any(v < -2048 or v > 2047 for v in values[start:start + 1024]):
            raise ValueError('N1 W12 sign extension tile=%d' % tile)
        for lane in range(16):
            at = start + 1024 + lane * 3
            expected = 255 if unsigned[at + 1] & 0x8000 else 0
            if unsigned[at + 2] != expected:
                raise ValueError('N1 b32 sign extension/padding tile=%d lane=%d' % (tile, lane))
    return raw


def _header_identity(data, layout, numeric):
    out = bytearray(data)
    struct.pack_into('<I', out, 8, layout)
    struct.pack_into('<I', out, 28, numeric)
    return bytes(out)


def read_header(data):
    if len(data) < HEADER_BYTES or len(data) % 4:
        raise ValueError('Invalid N1 stream length/alignment')
    magic, version, layout, flags, total, halves, raw_bytes, numeric = struct.unpack_from('<8I', data)
    if (magic, version, layout, halves, raw_bytes, numeric) != (
            MAGIC, VERSION, LAYOUT, HALVES, RAW_BYTES, NUMERIC_FORMAT):
        raise ValueError('Unsupported N1 header/numeric format')
    if flags not in (0, 1) or total != len(data) or total > MAX_BYTES:
        raise ValueError('Invalid N1 flags/encoded length')
    if flags and total != MAX_BYTES:
        raise ValueError('Wrong N1 raw length')
    return dict(version=version, layout=layout, numeric_format_id=numeric,
                raw=bool(flags), encoded_bytes=total, decoded_halfwords=halves)


def _base_stream(data):
    read_header(data)
    return _header_identity(data, base.LAYOUT, 0)


def encode(raw, force_raw=False):
    validate_raw(raw)
    return _header_identity(base.encode(raw, force_raw=force_raw), LAYOUT, NUMERIC_FORMAT)


def decode_wire(data):
    wire = base.decode_wire(_base_stream(data))
    validate_raw(wire[2144:14816] + wire[:2144] + wire[14816:])
    return wire


def decode(data):
    wire = decode_wire(data)
    return wire[2144:14816] + wire[:2144] + wire[14816:]


def verify_coordinates(raw, wire):
    validate_raw(raw)
    return base.verify_coordinates(raw, wire)


def dependency_hashes():
    return {Path(module.__file__).name: hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest()
            for module in (base, base.v2)}


def describe(data):
    info = base.describe(_base_stream(data))
    decode_wire(data)
    info.update(read_header(data))
    info.update(sha256=hashlib.sha256(data).hexdigest(), shift=10,
                encoding_algorithm='unchanged_B0_v3', base_codec_sha256=dependency_hashes(),
                rtl_verified=False, cpu_executed=False)
    return info
