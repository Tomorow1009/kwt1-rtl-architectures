"""Offline-only first20 screening from the pinned recovered FLOAT members.

No server jobs, no existing source writes and no hardware/precision approval.
The generated group8 load hashes must later be joined to server DATA100 before
freezing an ABI. Software time is not a hardware decoder-cycle measurement.
"""
import argparse
from collections import Counter
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time
import zipfile

import c80_codec_candidate as candidate
import dma16_layout
import n1_codec
import n1_data
import t80_precision

ARCHIVE_SHA = '5df11251821d2d36e85e07c8a171195d9d2ed2d4084a979519d23f6df7d683e2'
need = candidate.need


def sha_bytes(value):
    return hashlib.sha256(value).hexdigest()


def save(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False,
                                    allow_nan=False) + '\n', encoding='utf8')


def screen(archive, identity_path, output, converter_file=None):
    archive, identity_path, output = map(Path, (archive, identity_path, output))
    need(not output.exists(), 'Use a new offline screening directory')
    need(n1_data.sha(archive) == ARCHIVE_SHA, 'Different recovered source archive')
    identity = json.loads(identity_path.read_text(encoding='utf8'))
    need(identity['sha256'] == ARCHIVE_SHA and identity['all_original_npz_members_match'] is True
         and identity['members'] == 101, 'Original-member provenance mismatch')
    converter_file = Path(converter_file or n1_data.CONVERTER)
    need(n1_data.sha(converter_file) == n1_data.CONVERTER_SHA, 'Frozen PR converter changed')
    spec = importlib.util.spec_from_file_location('c80_frozen_converter', str(converter_file))
    converter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(converter)
    need(converter.FORMAT == n1_data.FORMAT, 'Converter numeric format changed')
    import numpy as np
    output.mkdir(parents=True)
    (output/'streams').mkdir()
    started, rows, clipping = time.monotonic(), [], dict(x=0, w=0, b=0)
    code = {Path(m.__file__).name: n1_data.sha(m.__file__)
            for m in (candidate, n1_codec, n1_codec.base, n1_codec.base.v2, dma16_layout)}
    code[Path(__file__).name] = n1_data.sha(__file__)
    inventory = identity['member_sha256']
    try:
        with zipfile.ZipFile(str(archive)) as zipped:
            need(len(zipped.namelist()) == len(set(zipped.namelist())) == 101 and
                 set(zipped.namelist()) == {t80_precision.ROOT + n for n in inventory}, 'Member set differs')
            wb = zipped.read(t80_precision.ROOT + 'shared_weights.npz')
            need(sha_bytes(wb) == t80_precision.WEIGHTS_SHA == inventory['shared_weights.npz'], 'Weights changed')
            wf, bf = converter.arrays(wb, True)
            w, clipping['w'] = converter.quantize(wf, 12, 12)
            b, clipping['b'] = converter.quantize(bf, 22, 32)
            for sample in range(1, 21):
                name = 'sample_%03d/float_tensors.npz' % sample
                sb = zipped.read(t80_precision.ROOT + name)
                need(sha_bytes(sb) == inventory[name], 'Original sample changed')
                xf, _ = converter.arrays(sb)
                x, xc = converter.quantize(xf, 10, 14)
                clipping['x'] += xc
                for layer in range(12):
                    stem = 'sample_%03d_layer_%02d' % (sample, layer + 1)
                    raw = dma16_layout.pack_tile16(x[layer], w[layer], b[layer])
                    dma16_layout.verify_coordinates(raw, x[layer], w[layer], b[layer])
                    load_sha = sha_bytes(converter.encode(converter.pack(x[layer], w[layer], b[layer]), 16))
                    baseline = n1_codec.encode(raw)
                    need(n1_codec.decode(baseline) == raw, 'P80 baseline roundtrip changed')
                    record = dict(sample=sample, layer=layer + 1, source_float_sha256=inventory[name],
                        group8_load_hex_sha256=load_sha, canonical_raw_sha256=sha_bytes(raw),
                        baseline_bytes=len(baseline), baseline_sha256=sha_bytes(baseline), profiles={})
                    for profile in ('compact_bias_v3', 'candidate'):
                        encoded, detail = candidate.encode(raw, profile)
                        decoded = candidate.decode(encoded)
                        for actual, expected in zip(decoded, (x[layer], w[layer], b[layer])):
                            need(np.array_equal(actual, expected), 'Coordinate integer mismatch: ' + stem)
                        filename = stem + '_' + profile + '.bin'
                        (output/'streams'/filename).write_bytes(encoded)
                        # All counts include header, tables, bias, padding, fallback.
                        record['profiles'][profile] = dict(bytes=len(encoded), sha256=sha_bytes(encoded),
                            raw=detail['raw'], bias_bytes=detail['bias_bytes'],
                            x_modes=dict(Counter(r['mode'] for r in detail['x_blocks'])),
                            w_modes=dict(Counter(r['mode'] for r in detail['weight_tiles'])),
                            block_lengths=[r['bytes'] for r in detail['x_blocks']],
                            weight_lengths=[r['bytes'] for r in detail['weight_tiles']],
                            first2_row_prefix_bytes=(32 + 2048 + 64 + 256 if detail['raw'] else
                                32 + detail['weight_tiles'][0]['bytes'] + 64 +
                                sum(r['bytes'] for r in detail['x_blocks'][:2])),
                            first5_row_prefix_bytes=(32 + 2048 + 64 + 640 if detail['raw'] else
                                32 + detail['weight_tiles'][0]['bytes'] + 64 +
                                sum(r['bytes'] for r in detail['x_blocks'][:5])),
                            input32_words=len(encoded)//4, all_four_segment_transactions=3*(len(encoded)//4)+12672)
                    rows.append(record)
                save(output/'progress.json', dict(status='running',samples=sample,tasks=len(rows),
                                                  hardware_executed=False))
                print('C80_OFFLINE_SAMPLE', sample, 'tasks', len(rows), 'seconds', round(time.monotonic()-started,2),flush=True)
        need(len(rows) == 240 and n1_data.sha(archive) == ARCHIVE_SHA, 'Incomplete or changed source')
        need(n1_data.sha(converter_file) == n1_data.CONVERTER_SHA, 'Converter changed')
        for module in (candidate, n1_codec, n1_codec.base, n1_codec.base.v2, dma16_layout):
            need(n1_data.sha(module.__file__) == code[Path(module.__file__).name], 'Screening source changed')
        metrics = {}
        for profile in ('baseline', 'compact_bias_v3', 'candidate'):
            sizes = [r['baseline_bytes'] if profile == 'baseline' else r['profiles'][profile]['bytes'] for r in rows]
            metrics[profile] = dict(min_bytes=min(sizes), mean_bytes=sum(sizes)/240., max_bytes=max(sizes),
                sum_bytes=sum(sizes), mean_four_segment_transactions=sum(3*(v//4)+12672 for v in sizes)/240.,
                conditional_mean_bus_cycles=sum(1.75*v+25344 for v in sizes)/240.,
                ideal_c32_lower_bound_cycles_mean=sum(max(51200,1.75*v+25344) for v in sizes)/240.,
                hardware_cycles_measured=False)
        summary=dict(schema='arch03-c80-offline-codec-screen-v1', status='software_roundtrip_passed',
            stage_accepted=False, candidate_frozen=False, hardware_executed=False, software_only=True,
            samples=20, tasks=240, coordinate_integers_per_task=6336+16384+256,
            coordinate_integers_checked=240*(6336+16384+256)*2,
            quantization_clipping=clipping, numerical_format=n1_data.FORMAT,
            source_archive_sha256=ARCHIVE_SHA, source_identity_sha256=n1_data.sha(identity_path),
            converter_sha256=n1_data.CONVERTER_SHA, weights_sha256=t80_precision.WEIGHTS_SHA,
            sample_order='original_ranks_001_through_020', source_npz_members_rechecked=21,
            server_hex_rechecked_this_run=False, full20_server_hash_join_required=True,
            original_zip_container_obtained=False, codec_sha256=code, metrics=metrics,
            complete_headers_bias_tables_padding_fallback_counted=True,
            raw_bias_halfwords=2, raw_halfwords=23232, raw_bytes=46464,
            reset_logical_rows=8, tied_to_mac_row_count=False, source_order='W0/b0,X0..98,W1/b1..W15/b15',
            python_version=sys.version, numpy_version=np.__version__,elapsed_seconds=time.monotonic()-started,
            limits=['Experimental software ABI; no C80 RTL or decoder-cycle/PPA evidence',
                    'Conditional bus formula is the measured P80 scenario, not a proof for arbitrary encoded streams',
                    'Same immutable source FLOAT and converter, but generated group8 hashes still require own DATA100 join',
                    'P80 completion and freeze required before C80 hardware changes'])
        save(output/'tasks.json',rows)
        with (output/'tasks.csv').open('w',newline='',encoding='utf8') as f:
            fields=['sample','layer','baseline_bytes','compact_bias_v3_bytes','candidate_bytes','group8_load_hex_sha256']
            writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader()
            for row in rows:
                writer.writerow(dict(sample=row['sample'],layer=row['layer'],baseline_bytes=row['baseline_bytes'],
                    compact_bias_v3_bytes=row['profiles']['compact_bias_v3']['bytes'],
                    candidate_bytes=row['profiles']['candidate']['bytes'],group8_load_hex_sha256=row['group8_load_hex_sha256']))
        summary['tasks_json_sha256']=n1_data.sha(output/'tasks.json')
        summary['tasks_csv_sha256']=n1_data.sha(output/'tasks.csv')
        save(output/'summary.json',summary)
        print('C80_OFFLINE_SCREEN_COMPLETE',json.dumps(metrics,sort_keys=True),flush=True)
        return summary
    except BaseException as error:
        save(output/'failure.json',dict(status='failed_preserved',error=str(error),completed_tasks=len(rows),
                                       stage_accepted=False,hardware_executed=False))
        raise


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--archive',required=True,type=Path)
    p.add_argument('--identity',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    p.add_argument('--converter-file',type=Path,help='Exact frozen PR bytes; no newline/hash relaxation')
    a=p.parse_args();screen(a.archive,a.identity,a.output,a.converter_file)
