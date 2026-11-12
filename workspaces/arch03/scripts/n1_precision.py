"""Fresh float/HEX precision reaudit for the exact N1 worst100 source archive.

Read-only inputs; no extraction, regeneration over old HEX, or use of Q12 error
statistics.  The immutable PR converter is loaded by API, never its 30-case CLI.
This report is SOFTWARE precision only; real N1 batch identity is a separate
required join before claiming hardware accuracy or entering the next stage.
"""
import argparse
import datetime
import hashlib
import io
import json
import math
from pathlib import Path
import re
import sys
import zipfile

import n1_data as data

ARCHIVE_SHA = 'edb98e1dcb02a9e142a62161b2769b54cffae1cf2ba143d0210c776b46ec36d9'
ARCHIVE_ROOT = 'KWT1_WORST100_ORIGINAL_FLOAT/'
THRESHOLD_PERCENT = 3.0
SCHEMA = 'arch03-n1-float-precision-v1'


def digest_bytes(raw):
    return hashlib.sha256(raw).hexdigest()


def stamp(path):
    stat = Path(path).stat()
    return (stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns)


def independent_reference(x, w, bias):
    """k-wise int64 operations with every signed32 prefix checked, no matmul."""
    import numpy as np
    accumulator = np.zeros((99, 256), dtype=np.int64)
    minimum, maximum = 0, 0
    for k in range(64):
        accumulator += x[:, k:k+1]*w[k:k+1, :]
        minimum = min(minimum, int(accumulator.min()))
        maximum = max(maximum, int(accumulator.max()))
        data.require(minimum >= -(1 << 31) and maximum < (1 << 31), 'N1 prefix accumulator overflow')
    total = accumulator+bias
    data.require(int(total.min()) >= -(1 << 32) and int(total.max()) < (1 << 32), 'N1 total33 overflow')
    quotient, remainder = np.divmod(np.abs(total), 1024)
    magnitude = quotient+(remainder >= 512)
    rounded = np.where(total < 0, -magnitude, magnitude)
    result = np.maximum(-32768, np.minimum(32767, rounded))
    return dict(total=total, result=result, saturated=(result != rounded).astype(np.int64)), minimum, maximum


def audit_layer(folder, x_float, w_float, bias_float, y_float, converter):
    import numpy as np
    folder = Path(folder)
    meta, words, _, _ = data.source_case(folder)
    xq, xc = converter.quantize(x_float, 10, 14)
    wq, wc = converter.quantize(w_float, 12, 12)
    bq, bc = converter.quantize(bias_float, 22, 32)
    x, w, bias = data.decode_group8(words)
    # Independent original-coordinate decoding proves values and layout,
    # including weights that could be hidden by an all-zero input matrix.
    for name, actual, expected in (('X', x, xq), ('W', w, wq), ('b', bias, bq)):
        data.require(np.array_equal(np.asarray(actual, dtype=np.int64), expected),
                     'Fresh float quantization differs at original '+name+' coordinates')
    api_reference = converter.reference(xq, wq, bq)
    reference, acc_min, acc_max = independent_reference(xq, wq, bq)
    rebuilt = {'load.hex': converter.encode(converter.pack(xq, wq, bq), 16)}
    for name in ('total', 'result', 'saturated'):
        data.require(np.array_equal(reference[name], api_reference[name]),
                     'Independent N1 integer reference differs: '+name)
        bits, count = data.FILES[name+'.hex']
        actual = np.asarray(data.hex_values(folder/(name+'.hex'), count, bits, name != 'saturated'), dtype=np.int64)
        data.require(np.array_equal(actual, reference[name].reshape(-1)), 'Original HEX reference differs: '+name)
        rebuilt[name+'.hex'] = converter.encode(reference[name], bits)
    for filename, raw in rebuilt.items():
        data.require(raw == (folder/filename).read_bytes(), 'Fresh reference HEX bytes differ: '+filename)
        data.require(digest_bytes(raw) == meta['files'][filename]['sha256'], 'Fresh HEX hash differs: '+filename)
    floating_result = reference['result'].astype(np.float64)/4096.
    delta = floating_result-y_float
    sse = float(np.sum(delta*delta, dtype=np.float64))
    energy = float(np.sum(y_float*y_float, dtype=np.float64))
    count = 25344
    nrmse = 100*math.sqrt(sse/count)/max(math.sqrt(energy/count), 1e-8)
    data.require(all(math.isfinite(v) and v >= 0 for v in (sse, energy, nrmse)), 'Invalid float error statistics')
    return dict(outputs=count, sse=sse, reference_energy=energy, nrmse_percent=nrmse,
                max_abs_error=float(np.max(np.abs(delta))), clipping=dict(x=xc, w=wc, b=bc),
                saturated=int(reference['saturated'].sum()), accumulator_min=acc_min, accumulator_max=acc_max,
                total_min=int(reference['total'].min()), total_max=int(reference['total'].max()),
                integer_mismatches=0, hex_byte_mismatches=0,
                source_layout_sha256=data.sha(folder/'layout.json'),
                source_hex_sha256={name: meta['files'][name]['sha256'] for name in data.FILES})


def aggregate(rows):
    """Combine squared errors and reference energies before taking each root."""
    layers = []
    for layer in range(1, 13):
        selected = [row for row in rows if row['layer'] == layer]
        data.require(selected, 'Missing precision layer')
        count = sum(row['outputs'] for row in selected)
        sse = math.fsum(row['sse'] for row in selected)
        energy = math.fsum(row['reference_energy'] for row in selected)
        nrmse = 100*math.sqrt(sse/count)/max(math.sqrt(energy/count), 1e-8)
        layers.append(dict(layer=layer, tasks=len(selected), outputs=count, sse=sse,
                           reference_energy=energy, nrmse_percent=nrmse,
                           precision_limit_percent=THRESHOLD_PERCENT, within_limit=nrmse <= THRESHOLD_PERCENT,
                           clipping={k: sum(row['clipping'][k] for row in selected) for k in ('x', 'w', 'b')},
                           saturated=sum(row['saturated'] for row in selected)))
    return layers


def _audit(archive, dataset, output, manifest_sha, sample_count=100):
    """sample_count exists only for tiny fixtures; production CLI fixes 100.

    Any non-100 report is fixture_passed/failed and cannot set precision_verified.
    Tests may pin synthetic archive/inventory constants via unittest mocks.
    """
    import numpy as np
    archive, dataset, output = Path(archive).resolve(), Path(dataset).resolve(), Path(output).resolve()
    data.require(type(sample_count) is int and 1 <= sample_count <= 100, 'Invalid sample count')
    data.require(re.fullmatch('[a-f0-9]{64}', manifest_sha), 'Provide exact dataset manifest SHA-256')
    data.require(archive.is_file() and not archive.is_symlink(), 'Missing complete original FLOAT archive')
    data.require(data.sha(archive) == ARCHIVE_SHA, 'Complete FLOAT archive SHA differs from fixed source')
    data.require(data.sha(dataset/'manifest.json') == manifest_sha, 'Dataset root manifest changed')
    manifest = data.read(dataset/'manifest.json')
    data.require(not output.exists(), 'Precision output exists; preserve previous evidence')
    data.require(output != dataset and dataset not in output.parents and output != archive.parent,
                 'Precision output must not be written within the dataset/archive directory')
    tasks = data.index_dataset(dataset, expected_sha=data.DATA100_INVENTORY_SHA, expected_samples=sample_count)
    before = {str(archive): stamp(archive), str(dataset/'manifest.json'): stamp(dataset/'manifest.json'),
              str(dataset/'SHA256_FILES.json'): stamp(dataset/'SHA256_FILES.json')}
    converter = data.converter_module()
    converter_stamp = stamp(data.CONVERTER)
    output.mkdir(parents=True)
    identity = dict(schema=SCHEMA, status='running', numeric_format=data.FORMAT,
        numeric_format_id=0x000e0c20, layout_id=0x00100004, samples=sample_count,
        tasks=sample_count*12, outputs=sample_count*12*25344, dataset=str(dataset), float_archive=str(archive),
        dataset_manifest_sha256=manifest_sha, dataset_inventory_sha256=data.DATA100_INVENTORY_SHA,
        float_archive_sha256=ARCHIVE_SHA, converter_commit=data.PR_COMMIT,
        converter_sha256=data.CONVERTER_SHA, audit_script_sha256=data.sha(__file__),
        data_script_sha256=data.sha(data.__file__), python_version=sys.version, numpy_version=np.__version__,
        started_utc=datetime.datetime.utcnow().isoformat()+'Z', cpu_executed=False,
        rtl_integer_match_required=True, official_precision_verified=False, fixture=sample_count != 100)
    data.save(output/'identity.json', identity)
    rows = []
    try:
        with zipfile.ZipFile(str(archive)) as zipped:
            names = zipped.namelist()
            data.require(len(names) == len(set(names)), 'Duplicate FLOAT archive member')
            data.require(all(not name.startswith('/') and '\\' not in name and '..' not in name.split('/') for name in names),
                         'Unsafe/ambiguous FLOAT archive member name')
            weight_members = [name for name in names if name.endswith('/shared_weights.npz')]
            data.require(weight_members == [ARCHIVE_ROOT+'shared_weights.npz'], 'Unexpected FLOAT archive root')
            expected_members = {ARCHIVE_ROOT+'sample_%03d/float_tensors.npz'%n for n in range(1, sample_count+1)}
            actual_members = {name for name in names if re.fullmatch(re.escape(ARCHIVE_ROOT)+r'sample_\d+/float_tensors\.npz', name)}
            data.require(actual_members == expected_members, 'Incomplete/extra FLOAT sample matrices')
            weights_raw = zipped.read(weight_members[0])
            weights, biases = converter.arrays(weights_raw, weights=True)
            weights_sha = digest_bytes(weights_raw)
            if 'weights_sha256' in manifest:
                data.require(manifest['weights_sha256'] == weights_sha, 'Dataset weights provenance disagrees')
            if 'archive_sha256' in manifest:
                data.require(manifest['archive_sha256'] == ARCHIVE_SHA, 'Dataset archive provenance disagrees')
            sample_meta = {}
            if 'samples' in manifest:
                entries = manifest['samples']
                data.require(len(entries) == sample_count and sorted(entry['sample'] for entry in entries) == list(range(1, sample_count+1)),
                             'Dataset original sample numbering differs')
                sample_meta = {entry['sample']: entry for entry in entries}
            provenance = []
            for sample in range(1, sample_count+1):
                name = 'sample_%03d' % sample
                raw = zipped.read(ARCHIVE_ROOT+name+'/float_tensors.npz')
                x, y = converter.arrays(raw)
                data.require(y is not None, 'Complete same-batch FLOAT Y is required; no inferred substitute')
                sample_sha = digest_bytes(raw)
                meta = sample_meta.get(sample, {})
                if 'sample_sha256' in meta:
                    data.require(meta['sample_sha256'] == sample_sha, 'Sample float identity differs at '+name)
                if 'original_rank' in meta:
                    data.require(meta['original_rank'] == sample, 'Original ordering changed at '+name)
                source_member = ARCHIVE_ROOT+name+'/source.json'
                data.require(source_member in names, 'Missing original speech identity '+name)
                source_raw = zipped.read(source_member)
                source = json.loads(source_raw.decode('utf-8-sig'))
                for key in ('wav', 'split', 'wav_sha256'):
                    data.require(key in source, 'Incomplete original speech provenance '+name)
                    if key in meta:data.require(meta[key] == source[key], 'Speech identity disagrees: '+name+'/'+key)
                provenance.append(dict(sample=sample, sample_float_sha256=sample_sha,
                    source_json_sha256=digest_bytes(source_raw), **{k: source[k] for k in ('wav', 'split', 'wav_sha256')}))
                for layer in range(1, 13):
                    folder = dataset/name/('layer_%02d'%layer)
                    row = audit_layer(folder, x[layer-1], weights[layer-1], biases[layer-1], y[layer-1], converter)
                    row.update(sample=sample, layer=layer, sample_float_sha256=sample_sha, weights_sha256=weights_sha)
                    rows.append(row)
                data.save(output/'progress.json', dict(status='running', samples_completed=sample,
                    tasks_completed=len(rows), outputs_checked=len(rows)*25344, software_only=True))
                print('N1_FLOAT_REAUDIT_SAMPLE_PASS', name, 'tasks', len(rows), flush=True)
        data.require(data.index_dataset(dataset, expected_sha=data.DATA100_INVENTORY_SHA,
                     expected_samples=sample_count) == tasks, 'Dataset changed during precision audit')
        data.require(data.sha(dataset/'manifest.json') == manifest_sha and data.sha(archive) == ARCHIVE_SHA and
                     data.sha(data.CONVERTER) == data.CONVERTER_SHA, 'Float/manifest/converter identity changed')
        data.require(data.sha(__file__) == identity['audit_script_sha256'] and
                     data.sha(data.__file__) == identity['data_script_sha256'], 'Precision audit code changed')
        for path, value in before.items():data.require(stamp(path) == value, 'Input mutated during precision audit')
        data.require(stamp(data.CONVERTER) == converter_stamp, 'Converter mutated during audit')
        layers = aggregate(rows)
        within = all(layer['within_limit'] for layer in layers)
        report = dict(identity)
        report.update(status=('passed' if within else 'failed_precision') if sample_count == 100 else
                      ('fixture_passed' if within else 'fixture_failed_precision'),
            identity_sha256=data.sha(output/'identity.json'), weights_sha256=weights_sha,
            integer_reference_hex_verified=True, internal_precision_verified=within and sample_count == 100,
            max_layer_nrmse_percent=max(layer['nrmse_percent'] for layer in layers),
            max_task_nrmse_percent=max(row['nrmse_percent'] for row in rows),
            precision_limit_percent=THRESHOLD_PERCENT, layer_aggregate=layers, cases=rows, samples_provenance=provenance,
            clipping={key:sum(row['clipping'][key] for row in rows) for key in ('x', 'w', 'b')},
            saturated=sum(row['saturated'] for row in rows), integer_mismatches=0, hex_byte_mismatches=0,
            finished_utc=datetime.datetime.utcnow().isoformat()+'Z',
            scope='Fresh FLOAT-to-original-HEX software precision; join same dataset identity with own N1 RTL batch before hardware acceptance')
        data.save(output/'summary.json', report)
        data.save(output/'progress.json', dict(status=report['status'], samples_completed=sample_count,
            tasks_completed=len(rows), outputs_checked=len(rows)*25344, software_only=True))
        return report
    except BaseException as exc:
        data.save(output/'failure.json', dict(status='failed', error=str(exc), completed_tasks=len(rows),
            internal_precision_verified=False, cpu_executed=False, original_inputs_unchanged_by_tool=True))
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', required=True, type=Path)
    parser.add_argument('--dataset', required=True, type=Path)
    parser.add_argument('--dataset-manifest-sha256', required=True)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    result = _audit(args.archive, args.dataset, args.output, args.dataset_manifest_sha256, sample_count=100)
    data.require(result['status'] == 'passed' and result['internal_precision_verified'], 'N1 internal float precision gate failed')
    print('N1_FLOAT_PRECISION_PASS tasks=1200 outputs=30412800 cpu_executed=false official_precision_verified=false')


if __name__ == '__main__':
    main()
