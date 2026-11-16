"""Reconstruct an exact C32 transfer in a new private directory only.

Reads frozen C80 members whose hashes match its manifest. Never writes the
source, resumes a queue, touches Desktop/T80, or grants hardware acceptance.
"""
import base64
import hashlib
import json
from pathlib import Path, PurePosixPath
import struct
import zlib

ROOT = Path('/tmp/s4_21usr_c32_20261116_2010')
BASE = Path('/tmp/s4_21usr_c80_20261116_1245/light-light126-c80-74f3ae7')
COMPRESSED_SHA = '64d6f32d905cd59decb73a08a7120d31634d95dc4503b3717feccf1ea22525b5'
PAYLOAD_SHA = '40fed77e347aad1347f1998f19801652770b176c5f5e0e03f405d68d0a11c602'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def reconstruct(compressed, read_base, manifest):
    assert len(compressed) == 72999 and sha(compressed) == COMPRESSED_SHA
    raw = zlib.decompress(compressed)
    size = struct.unpack_from('<I', raw)[0]
    assert 0 < size < len(raw)-4
    spec = json.loads(raw[4:4+size].decode('utf8'))
    data = raw[4+size:]
    assert spec['schema'] == 'c32-exact-overlay-delta-v1'
    assert spec['payload_sha256'] == PAYLOAD_SHA
    assert spec['metadata']['source_commit'] == '61246bb2a21c56a9bfd871fd68de93028d79f5fd'
    assert len(spec['files']) == 114

    def literal(pair):
        offset, count = pair
        assert type(offset) is int and type(count) is int and 0 <= offset <= offset+count <= len(data)
        return data[offset:offset+count]

    files = {}
    for name, value in spec['files'].items():
        if 'literal' in value:
            result = literal(value['literal'])
        else:
            member = PurePosixPath(value['base'])
            assert not member.is_absolute() and '..' not in member.parts and '\\' not in value['base']
            assert manifest['files'].get(value['base']) == value['base_sha256'], value['base']
            source = read_base(value['base'])
            assert sha(source) == value['base_sha256'], value['base']
            tag = value['rename']
            assert tag in (None, 'c80', 'p80')
            if tag:
                source = source.replace(tag.encode(), b'c32').replace(tag.upper().encode(), b'C32')
            chunks = []
            for part in value['chunks']:
                if isinstance(part, list):
                    lo, hi = part
                    assert type(lo) is int and type(hi) is int and 0 <= lo <= hi <= len(source)
                    chunks.append(source[lo:hi])
                else:
                    assert set(part) == {'literal'}
                    chunks.append(literal(part['literal']))
            result = b''.join(chunks)
        assert sha(result) == value['sha256'], name
        files[name] = dict(sha256=value['sha256'], base64=base64.b64encode(result).decode('ascii'))
    result = (json.dumps(dict(spec['metadata'], files=files), sort_keys=True, separators=(',', ':'))+'\n').encode()
    assert sha(result) == PAYLOAD_SHA
    return result


def main():
    assert ROOT.resolve() == ROOT and ROOT.stat().st_mode & 0o777 == 0o700
    manifest_raw = (BASE/'manifest.json').read_bytes()
    assert sha(manifest_raw) == 'd0f18e4a6aa8a928df37d4347f1a8853c448e823f0685a83c5b710732e5e7a59'
    compressed = base64.b64decode(''.join((ROOT/'delta03.b64').read_text().split()), validate=True)
    result = reconstruct(compressed, lambda name: (BASE/name).read_bytes(), json.loads(manifest_raw))
    assert (BASE/'manifest.json').read_bytes() == manifest_raw
    output = ROOT/'payload_61246bb.json'
    with output.open('xb') as stream:
        stream.write(result)
    print('C32_EXACT_PAYLOAD_RECONSTRUCTED', len(result), sha(result), flush=True)


if __name__ == '__main__':
    main()
