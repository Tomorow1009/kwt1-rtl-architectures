"""Fresh first20 T64 software precision from byte-identical original NPZ members in a new ZIP.

This is a separate source mode, not a relaxation of n1_precision's original ZIP
check. Every matrix and shared-weight byte is pinned by the original DATA100
manifest; the recovered container has its own SHA. No inference from HEX.
"""
import argparse
import datetime
import json
from pathlib import Path
import re
import sys
import zipfile

import n1_data as data
import n1_precision as precision

SCHEMA = 'arch03-t64-first20-recovered-member-precision-v1'
SOURCE_MODE = 'exact_original_npz_members'
ROOT = 'n1-recovered-float100-20261113/'
MANIFEST_SHA = '9900a9bd1addbdeb256020ba9a04f4615791fbd5a624abd411364098c382c97e'
WEIGHTS_SHA = '99a3f2d990203b2bd9f3bdf5dc98974d6a7102027f7d67b9abf19e72ee03a6ad'
ORIGINAL_ARCHIVE_SHA = precision.ARCHIVE_SHA


def source_entry_sha(entry):
    return precision.digest_bytes(json.dumps(entry, sort_keys=True, separators=(',', ':'),
                                            ensure_ascii=False).encode('utf-8'))


def verified_manifest(dataset, count=100):
    path = Path(dataset)/'manifest.json'
    data.require(data.sha(path) == MANIFEST_SHA, 'Original DATA100 manifest identity differs')
    manifest = data.read(path)
    data.require(manifest['archive_sha256'] == ORIGINAL_ARCHIVE_SHA
                 and manifest['weights_sha256'] == WEIGHTS_SHA, 'Original archive/weights provenance differs')
    entries = manifest['samples']
    data.require(len(entries) == count and all(v['sample'] == v['original_rank'] == i
                 for i, v in enumerate(entries, 1)), 'Original sample set/order differs')
    for entry in entries:
        data.require(re.fullmatch('[a-f0-9]{64}', entry['sample_sha256']) is not None,
                     'Missing original NPZ identity')
        data.require(all(k in entry for k in ('wav', 'split', 'wav_sha256')), 'Incomplete speech provenance')
    return manifest


def verify_members(archive, archive_sha, manifest):
    """Read every member and compare to the immutable original manifest."""
    archive = Path(archive)
    data.require(archive.is_file() and not archive.is_symlink()
                 and re.fullmatch('[a-f0-9]{64}', archive_sha or '')
                 and data.sha(archive) == archive_sha, 'Recovered container identity differs')
    before = precision.stamp(archive)
    entries = manifest['samples']
    expected = {ROOT+'shared_weights.npz'} | {
        ROOT+'sample_%03d/float_tensors.npz'%v['sample'] for v in entries}
    provenance = []
    with zipfile.ZipFile(str(archive)) as zipped:
        names = zipped.namelist()
        data.require(len(names) == len(set(names)) and set(names) == expected,
                     'Recovered container member set differs')
        data.require(all(0 < v.file_size <= 16*1024**2 for v in zipped.infolist()), 'Recovered member size bound')
        weights_raw = zipped.read(ROOT+'shared_weights.npz')
        data.require(precision.digest_bytes(weights_raw) == WEIGHTS_SHA == manifest['weights_sha256'],
                     'Original shared weights differ')
        for entry in entries:
            raw = zipped.read(ROOT+'sample_%03d/float_tensors.npz'%entry['sample'])
            data.require(precision.digest_bytes(raw) == entry['sample_sha256'],
                         'Original float NPZ differs at sample_%03d'%entry['sample'])
            provenance.append(dict(sample=entry['sample'], sample_float_sha256=entry['sample_sha256'],
                source_manifest_entry_sha256=source_entry_sha(entry),
                **{k:entry[k] for k in ('wav','split','wav_sha256')}))
    data.require(precision.stamp(archive) == before and data.sha(archive) == archive_sha,
                 'Recovered container changed during verification')
    return provenance


def _audit(archive, archive_sha, dataset, output, sample_count=20):
    import numpy as np
    archive, dataset, output = Path(archive).resolve(), Path(dataset).resolve(), Path(output).resolve()
    data.require(sample_count == 20, 'T64 precision fixes the first20 samples only')
    data.require(not output.exists() and output != dataset and dataset not in output.parents
                 and output != archive.parent, 'Use separate new precision output directory')
    manifest = verified_manifest(dataset, 100)
    provenance = verify_members(archive, archive_sha, manifest)[:20]
    tasks = data.index_dataset(dataset, expected_sha=data.DATA100_INVENTORY_SHA, expected_samples=100)
    converter = data.converter_module()
    files = [archive, dataset/'manifest.json', dataset/'SHA256_FILES.json', data.CONVERTER,
             Path(__file__), Path(precision.__file__), Path(data.__file__)]
    before = {str(p):precision.stamp(p) for p in files}
    output.mkdir(parents=True)
    identity = dict(schema=SCHEMA, status='running', source_mode=SOURCE_MODE,
        original_float_archive_verified=False, original_float_archive_expected_sha256=ORIGINAL_ARCHIVE_SHA,
        recovered_original_members_verified=True, numeric_format=data.FORMAT,
        numeric_format_id=0x000e0c20, layout_id=0x00100004, samples=sample_count,
        tasks=sample_count*12, outputs=sample_count*12*25344, dataset=str(dataset), float_archive=str(archive),
        dataset_manifest_sha256=MANIFEST_SHA, dataset_inventory_sha256=data.DATA100_INVENTORY_SHA,
        float_archive_sha256=archive_sha, converter_commit=data.PR_COMMIT,
        converter_sha256=data.CONVERTER_SHA, audit_script_sha256=data.sha(__file__),
        numeric_audit_script_sha256=data.sha(precision.__file__), data_script_sha256=data.sha(data.__file__),
        python_version=sys.version, numpy_version=np.__version__, started_utc=datetime.datetime.utcnow().isoformat()+'Z',
        cpu_executed=False, rtl_integer_match_required=True, official_precision_verified=False,
        fixture=False, selection="original_ranks_001_through_020")
    data.save(output/'identity.json', identity)
    rows = []
    try:
        with zipfile.ZipFile(str(archive)) as zipped:
            weights, biases = converter.arrays(zipped.read(ROOT+'shared_weights.npz'), weights=True)
            for sample in provenance:
                number = sample['sample']
                raw = zipped.read(ROOT+'sample_%03d/float_tensors.npz'%number)
                data.require(precision.digest_bytes(raw) == sample['sample_float_sha256'], 'Recovered NPZ changed')
                x, y = converter.arrays(raw)
                data.require(y is not None, 'Complete original FLOAT Y required')
                for layer in range(1, 13):
                    folder = dataset/('sample_%03d'%number)/('layer_%02d'%layer)
                    row = precision.audit_layer(folder,x[layer-1],weights[layer-1],biases[layer-1],y[layer-1],converter)
                    row.update(sample=number, layer=layer, sample_float_sha256=sample['sample_float_sha256'],
                               weights_sha256=WEIGHTS_SHA)
                    rows.append(row)
                data.save(output/'progress.json',dict(status='running',samples_completed=number,
                    tasks_completed=len(rows),outputs_checked=len(rows)*25344,software_only=True))
                print('T64_FIRST20_FLOAT_SAMPLE_PASS', number, 'tasks', len(rows), flush=True)
        data.require(data.index_dataset(dataset,expected_sha=data.DATA100_INVENTORY_SHA,
                     expected_samples=100) == tasks, 'Dataset changed during precision audit')
        data.require(verified_manifest(dataset,100) == manifest and
                     data.sha(archive) == archive_sha and data.sha(data.CONVERTER) == data.CONVERTER_SHA,
                     'Recovered source/converter identity changed')
        for path, value in before.items():
            data.require(precision.stamp(path) == value, 'Input mutated during precision audit')
        layers = precision.aggregate(rows)
        within = all(layer['within_limit'] for layer in layers)
        report = dict(identity)
        report.update(status='passed' if within else 'failed_precision',
            identity_sha256=data.sha(output/'identity.json'), weights_sha256=WEIGHTS_SHA,
            integer_reference_hex_verified=True, internal_precision_verified=within,
            max_layer_nrmse_percent=max(r['nrmse_percent'] for r in layers),
            max_task_nrmse_percent=max(r['nrmse_percent'] for r in rows),
            precision_limit_percent=precision.THRESHOLD_PERCENT, layer_aggregate=layers,
            cases=rows, samples_provenance=provenance,
            clipping={k:sum(r['clipping'][k] for r in rows) for k in ('x','w','b')},
            saturated=sum(r['saturated'] for r in rows),integer_mismatches=0,hex_byte_mismatches=0,
            finished_utc=datetime.datetime.utcnow().isoformat()+'Z',
            scope='Fresh original-member FLOAT-to-HEX software precision; own T64 240-task RTL batch join still required')
        data.save(output/'summary.json',report)
        return report
    except BaseException as exc:
        data.save(output/'failure.json',dict(status='failed',error=str(exc),completed_tasks=len(rows),
            internal_precision_verified=False,cpu_executed=False))
        raise


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive',required=True,type=Path)
    parser.add_argument('--archive-sha256',required=True)
    parser.add_argument('--dataset',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    result=_audit(args.archive,args.archive_sha256,args.dataset,args.output)
    data.require(result['status']=='passed' and result['internal_precision_verified'],'N1 recovered precision failed')
    print('T64_FIRST20_FLOAT_PRECISION_PASS tasks=240 outputs=6082560 cpu_executed=false')


if __name__=='__main__':
    main()
