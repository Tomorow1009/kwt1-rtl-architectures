"""C80 host format preparation; no C80 hardware acceptance is implied.

One selected codec family, with raw fallback. The payload is byte-identical
to the screened full C80 candidate; the 32-byte header now has a distinct
layout/version. P80 and the experimental C80P header are explicitly rejected.
Logical prediction resets every eight rows, independent of MAC row count.
"""
import hashlib
from pathlib import Path
import struct

import c80_codec_candidate as candidate
import n1_codec

MAGIC, VERSION, LAYOUT = 0x3543574b, 0x00050000, 0x00100006
NUMERIC_FORMAT = 0x000e0c20
HEADER_BYTES = 32
RAW_HALFWORDS, RAW_BYTES = 23232, 46464
INTERNAL_HALFWORDS, CANONICAL_BYTES = 23488, 46976
MAX_BYTES = HEADER_BYTES+RAW_BYTES
RESET_LOGICAL_ROWS = 8


def read_header(data):
    candidate.need(isinstance(data, bytes) and len(data) >= HEADER_BYTES and len(data)%4 == 0,
                   'Invalid C80 length/alignment')
    magic, version, layout, flags, total, halves, raw, numeric = struct.unpack_from('<8I',data)
    candidate.need((magic,version,layout,halves,raw,numeric) ==
        (MAGIC,VERSION,LAYOUT,RAW_HALFWORDS,RAW_BYTES,NUMERIC_FORMAT), 'Wrong C80 identity')
    candidate.need(flags in (0,1) and total == len(data) and total <= MAX_BYTES and
                   (not flags or total == MAX_BYTES), 'Invalid C80 flags/size')
    return dict(version=version,layout=layout,numeric_format_id=numeric,raw=bool(flags),
        encoded_bytes=total,external_raw_halfwords=halves,internal_halfwords=INTERNAL_HALFWORDS,
        reset_logical_rows=RESET_LOGICAL_ROWS)


def from_candidate(data):
    candidate.decode(data)
    header=struct.unpack_from('<8I',data)
    candidate.need(header[2] == 0, 'Compact-bias-only software comparison is not the C80 format')
    return struct.pack('<8I',MAGIC,VERSION,LAYOUT,header[3],len(data),RAW_HALFWORDS,
                       RAW_BYTES,NUMERIC_FORMAT)+data[HEADER_BYTES:]


def _candidate_stream(data):
    info=read_header(data)
    return struct.pack('<8I',candidate.MAGIC,candidate.VERSION,0,int(info['raw']),len(data),
                       RAW_BYTES,NUMERIC_FORMAT,RESET_LOGICAL_ROWS)+data[HEADER_BYTES:]


def encode(raw,force_raw=False):
    return from_candidate(candidate.encode(raw,'candidate',force_raw)[0])


def decode_coordinates(data):
    return candidate.decode(_candidate_stream(data))


def decode(data):
    x,w,b=decode_coordinates(data)
    halves=[v & 65535 for row in x for v in row]
    for tile in range(16):
        halves.extend(w[k][tile*16+lane] & 65535 for k in range(64) for lane in range(16))
        for lane in range(16):
            value=b[tile*16+lane] & ((1<<40)-1)
            halves.extend((value>>shift)&65535 for shift in (0,16,32))
    raw=struct.pack('<23488H',*halves)
    return n1_codec.validate_raw(raw)


def decode_wire(data):
    raw=decode(data)
    return raw[12672:14816]+raw[:12672]+raw[14816:]


def describe(data):
    info=read_header(data);decode_coordinates(data)
    info.update(sha256=hashlib.sha256(data).hexdigest(),shift=10,
        header_bytes=HEADER_BYTES,canonical_bytes=CANONICAL_BYTES,external_raw_bytes=RAW_BYTES,
        encoding_algorithm='C80_exact_predictor_bounded_Rice_compact_bias_byte_blocks',
        codec_sha256={Path(m.__file__).name:hashlib.sha256(Path(m.__file__).read_bytes()).hexdigest()
                      for m in (candidate,n1_codec)},
        source_order='W0/b0,X0..98,W1/b1..W15/b15',
        software_only=True,rtl_verified=False,cpu_executed=False,format_frozen=False)
    return info
