"""Aggregate complete output matrices by layer; never average per-sample NRMSEs.

Input manifest: dataset_kind (development/official), provenance, and tasks containing
sample_id, layer, fraction_bits, reference_npz/sha256, actual_csv/sha256,
integer_npz/sha256. Integer archive uses result_int, or result for exported fixtures.
Official designation is supplied only after the organizer's dataset provenance is checked.
"""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from numeric import aggregate_tasks, error_metrics, read_capture, validate_format
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def evaluate(manifest):
    manifest=Path(manifest).resolve();m=json.loads(manifest.read_text(encoding='utf8'))
    if m.get('dataset_kind') not in ('development','official') or not m.get('provenance'):
        raise ValueError('Dataset designation and provenance are required')
    sums={n:[0.,0.,0] for n in range(1,13)};seen=set();samples=set();hashes={};tasks=[]
    for task in m['tasks']:
        sample=task['sample_id'];layer=task['layer'];key=(sample,layer)
        if not isinstance(sample,str) or not sample or type(layer)!=int or layer not in sums or key in seen:
            raise ValueError('Duplicate/invalid sample-layer')
        seen.add(key);samples.add(sample)
        files={}
        for name in ('reference_npz','actual_csv','integer_npz'):
            path=(manifest.parent/task[name]).resolve()
            digest=sha(path)
            if digest!=task[name+'_sha256']:raise ValueError('Input hash mismatch '+name)
            files[name]=path;hashes[str(path)]=digest
        with np.load(str(files['reference_npz']),allow_pickle=False) as z:ref=z['Y_float'].astype(np.float64)
        with np.load(str(files['integer_npz']),allow_pickle=False) as z:
            expected=z['result_int' if 'result_int' in z.files else 'result']
            expected_sat=z['saturated'] if 'saturated' in z.files else None
        if ref.shape!=(99,256) or expected.shape!=(99,256) or not np.isfinite(ref).all():
            raise ValueError('Invalid full matrix reference')
        if expected.dtype.kind not in 'iu' or np.any(expected<-32768) or np.any(expected>32767):
            raise ValueError('Invalid integer reference')
        values,actual_sat=read_capture(files['actual_csv'])
        if not np.array_equal(values,expected):raise ValueError('RTL/integer model mismatch')
        if actual_sat is not None:
            if expected_sat is None or expected_sat.shape!=(99,256) or not np.array_equal(actual_sat,expected_sat):
                raise ValueError('RTL/integer saturation mismatch or missing reference')
        fraction=task['fraction_bits']
        if type(fraction)!=int or not -7<=fraction<=31:raise ValueError('Invalid scale')
        if 'numeric_format' in task:
            config=validate_format(task['numeric_format'])
            if fraction!=config['output_fraction_bits']:raise ValueError('Inconsistent output scale')
        metrics=error_metrics(np.ldexp(values.astype(np.float64),-fraction),ref)
        tasks.append(dict(sample_id=sample,layer=layer,**metrics))
    if not samples or seen!={(s,l) for s in samples for l in range(1,13)}:
        raise ValueError('Each sample must cover all 12 layers')
    if m['dataset_kind']=='official' and len(samples)!=600:raise ValueError('Official coverage requires 600 distinct samples')
    summary=aggregate_tasks(tasks)
    return dict(dataset_kind=m['dataset_kind'],provenance=m['provenance'],samples=len(samples),
                integer_bit_exact=True,task_metrics=tasks,
                **{k:v for k,v in summary.items() if k!='samples'},
                official_precision_verified=m['dataset_kind']=='official' and summary['threshold_passed'],
                source_manifest_sha256=sha(manifest),input_sha256=hashes)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('manifest',type=Path);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();result=evaluate(a.manifest)
    a.output.write_text(json.dumps(result,indent=2),encoding='utf8')
    print(json.dumps({k:v for k,v in result.items() if k not in ('input_sha256','layers')},indent=2))
    if not result['threshold_passed']:raise SystemExit(1)
