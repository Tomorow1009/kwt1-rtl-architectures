#!/usr/bin/env python3
"""Read-only identity join; no audio, tensors, inference, network or writes."""
import argparse
import collections
import gzip
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys

MANIFEST_SHA = '9900a9bd1addbdeb256020ba9a04f4615791fbd5a624abd411364098c382c97e'
INDEX_SHA = '4f73b8ac8c02c6a1ba91a83e4dbd84992972bf110328eb84e8b670189f5bc201'
DECODED_SHA = '3ab4f4743dd40dd1f5b090688cb572e569c536755976134baefe1acf483111b7'
CSV_SHA = '1aea9aa75107cde96e2adad290f2d8f8fafb78be89f009f8e6ae9f514fcba09d'
WEIGHTS_SHA = '99a3f2d990203b2bd9f3bdf5dc98974d6a7102027f7d67b9abf19e72ee03a6ad'
ARCHIVE_SHA = 'edb98e1dcb02a9e142a62161b2769b54cffae1cf2ba143d0210c776b46ec36d9'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def checked_read(path, expected, limit):
    path = Path(path)
    require(path.is_file() and not path.is_symlink(), 'Missing/nonregular/symlink input')
    require(path.stat().st_size <= limit, 'Input exceeds fixed size budget')
    raw = path.read_bytes()
    require(digest(raw) == expected, 'Input SHA-256 differs: '+str(path))
    return raw


def evaluate(index, manifest):
    require(index.get('schema') == 'n1-audio-path-index-v2', 'Index schema')
    require(index.get('source_csv_sha256') == CSV_SHA, 'CSV source identity')
    require(index.get('count') == 105829 and index.get('index_base') == 0, 'Index count/base')
    paths = index['paths']; splits = index['splits']
    require(len(paths) == len(splits) == 105829 and len(set(paths)) == 105829, 'Index duplicate/count')
    require(all(isinstance(p, str) and not PurePosixPath(p).is_absolute()
                and len(PurePosixPath(p).parts) == 2 and '..' not in PurePosixPath(p).parts
                and '\\' not in p and p.endswith('.wav') for p in paths), 'Unsafe indexed path')
    require(dict(collections.Counter(splits)) == dict(training=84843, testing=11005, validation=9981), 'Index splits')
    samples = manifest['samples']
    require(len(samples) == 100, 'Manifest sample count')
    require(manifest.get('weights_sha256') == WEIGHTS_SHA, 'Shared weights identity')
    if 'archive_sha256' in manifest:
        require(manifest['archive_sha256'] == ARCHIVE_SHA, 'Original archive identity')
    lookup = {p: n for n, p in enumerate(paths)}
    ids = [row['sample'] for row in samples]
    require(all(type(n) is int for n in ids), 'Noninteger sample number')
    ordered = sorted(samples, key=lambda row: row['sample'])
    indices = [lookup.get(row.get('wav'), -1) for row in ordered]
    missing = sum(n < 0 for n in indices)
    split_mismatch = sum(n >= 0 and splits[n] != row.get('split') for n, row in zip(indices, ordered))
    bad_hash = sum(not re.fullmatch('[0-9a-f]{64}', str(row.get(key, '')))
                   for row in ordered for key in ('wav_sha256', 'sample_sha256'))
    result = dict(samples=100, matched=100-missing, missing=missing,
        duplicate_sample_ids=100-len(set(ids)),
        duplicate_wavs=100-len(set(row.get('wav') for row in ordered)),
        sample_order_matches=ids == list(range(1, 101)),
        ranks_match=all(row.get('original_rank') == row['sample'] for row in ordered),
        split_mismatches=split_mismatch, malformed_source_hashes=bad_hash,
        selected_splits=dict(collections.Counter(row.get('split') for row in ordered)))
    result['passed'] = (not missing and not split_mismatch and not bad_hash
        and result['duplicate_sample_ids'] == result['duplicate_wavs'] == 0
        and result['sample_order_matches'] and result['ranks_match']
        and result['selected_splits'] == dict(training=83, testing=13, validation=4))
    result['wav_bytes_verified'] = False
    result['float_source_recovered'] = False
    result['indices'] = indices
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', required=True, type=Path)
    parser.add_argument('--index', type=Path, default=Path(__file__).with_name('audio_index.json.gz'))
    args = parser.parse_args()
    raw_manifest = checked_read(args.manifest, MANIFEST_SHA, 2000000)
    compressed = checked_read(args.index, INDEX_SHA, 1000000)
    raw_index = gzip.decompress(compressed)
    require(len(raw_index) == 4230951 and digest(raw_index) == DECODED_SHA, 'Decoded index identity')
    result = evaluate(json.loads(raw_index.decode('ascii')), json.loads(raw_manifest.decode('utf-8-sig')))
    indices = result.pop('indices')
    print('N1_AUDIO_PATH_JOIN '+json.dumps(result, sort_keys=True, separators=(',', ':')))
    print('INDICES_001_050 '+','.join(str(n) for n in indices[:50]))
    print('INDICES_051_100 '+','.join(str(n) for n in indices[50:]))
    print('SOURCE_HASHES '+json.dumps(dict(server_manifest_sha256=MANIFEST_SHA,
        compressed_index_sha256=INDEX_SHA, decoded_index_sha256=DECODED_SHA,
        local_source_csv_sha256=CSV_SHA, weights_sha256=WEIGHTS_SHA,
        original_archive_sha256=json.loads(raw_manifest.decode('utf-8-sig')).get('archive_sha256'),
        index_base=0), sort_keys=True, separators=(',', ':')))
    require(checked_read(args.manifest, MANIFEST_SHA, 2000000) == raw_manifest
            and checked_read(args.index, INDEX_SHA, 1000000) == compressed, 'Inputs changed during audit')
    return 0 if result['passed'] else 2


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as exc:
        print('N1_AUDIO_PATH_JOIN_FAIL '+str(exc), file=sys.stderr)
        sys.exit(1)
