"""Independent complete-matrix NPZ validation and seven-file HEX export."""
import hashlib
import json
from pathlib import Path
import numpy as np
from verify_real_hex import FORMAT, quantize

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = ROOT/'KWT1/model_data/outputs/real_sample_001'
TASKS = 99*256


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check_equal(actual, expected, label):
    if actual.shape != expected.shape:
        raise ValueError(f'{label}: shape {actual.shape}, expected {expected.shape}')
    bad = np.argwhere(actual != expected)
    if bad.size:
        idx = tuple(bad[0])
        raise ValueError(f'{label}{idx}: got {actual[idx]}, expected {expected[idx]}')


def load_layer(root, layer):
    folder = (root/layer['hex_dir']).resolve().parent
    folder.relative_to(root.resolve())
    arrays = {}
    specifications = {
        'float_tensors.npz': [('X',(99,64),None),('W',(64,256),None),
                              ('b',(256,),None),('Y_float',(99,256),None)],
        'integer_tensors.npz': [('X_int',(99,64),16),('W_int',(64,256),16),
                                ('b_int',(256,),40),('total_int',(99,256),41),
                                ('result_int',(99,256),16),('saturated',(99,256),1)]}
    for name, specs in specifications.items():
        with np.load(folder/name, allow_pickle=False) as archive:
            for key, shape, bits in specs:
                a = archive[key]
                label = f'{name}/{key}'
                if a.shape != shape:
                    raise ValueError(f'{label}: shape {a.shape}, expected {shape}')
                if bits is None:
                    if a.dtype != np.dtype('float32') or not np.isfinite(a).all():
                        raise ValueError(f'{label}: expected finite float32')
                else:
                    if a.dtype.kind not in 'iub':
                        raise ValueError(f'{label}: expected integer dtype')
                    lo,hi = (0,1) if bits == 1 else (-(1<<(bits-1)),(1<<(bits-1))-1)
                    bad = np.argwhere((a<lo)|(a>hi))
                    if bad.size:
                        idx=tuple(bad[0]); raise ValueError(f'{label}{idx}: out of range {a[idx]}')
                    a = a.astype(np.int64)
                arrays[key] = a
    clipped = {}
    for key,frac,bits in [('X',12,16),('W',12,16),('b',24,40)]:
        a=arrays[key]
        q=np.array([quantize(v,frac,bits) for v in a.flat],dtype=np.int64).reshape(a.shape)
        check_equal(arrays[key+'_int'],q,key+' quantization')
        scaled=a.astype(np.float64)*(2**frac)
        rounded=np.sign(scaled)*np.floor(np.abs(scaled)+0.5)
        clipped[key]=int(np.count_nonzero((rounded<-(2**(bits-1)))|(rounded>2**(bits-1)-1)))
    total=arrays['X_int']@arrays['W_int']+arrays['b_int']
    magnitude=np.abs(total)
    q,r=np.divmod(magnitude,4096)
    rounded=np.where(total<0,-1,1)*(q+(2*r>=4096))
    result=np.clip(rounded,-32768,32767)
    saturated=(result!=rounded).astype(np.int64)
    for key,a in [('total_int',total),('result_int',result),('saturated',saturated)]:
        check_equal(arrays[key],a,key)
    decoded=result.astype(np.float64)/4096
    reference=arrays['Y_float'].astype(np.float64)
    error=decoded-reference
    metrics=dict(layer=layer['layer_number'],tasks=TASKS,passed=True,
                 max_absolute_error=float(np.max(np.abs(error))),
                 rmse=float(np.sqrt(np.mean(error**2))),
                 nrmse=float(np.sqrt(np.mean(error**2))/max(np.sqrt(np.mean(reference**2)),1e-8)),
                 saturated=int(saturated.sum()),clipped=clipped,
                 source_sha256={str((folder/n).relative_to(root)):sha(folder/n) for n in specifications})
    return arrays,metrics


def write_hex(path, values, bits):
    mask=(1<<bits)-1; width=(bits+3)//4
    with Path(path).open('w',encoding='ascii',newline='\n') as f:
        f.writelines(f'{int(v)&mask:0{width}x}\n' for v in np.asarray(values).flat)


def export_layer(folder, a):
    folder.mkdir(parents=True)
    # Stream a row at a time; columns inner, then k within each dot.
    for name,key in [('x','X_int'),('w','W_int')]:
        with (folder/(name+'.hex')).open('w',encoding='ascii',newline='\n') as f:
            for row in range(99):
                values=np.tile(a[key][row],(256,1)) if name=='x' else a[key].T
                f.writelines(f'{int(v)&65535:04x}\n' for v in values.flat)
    for name,values,bits in [('bias',np.tile(a['b_int'],99),40),
                             ('shift',np.full(TASKS,12),5),
                             ('total',a['total_int'],41),('result',a['result_int'],16),
                             ('saturated',a['saturated'],1)]:
        write_hex(folder/(name+'.hex'),values,bits)
    np.savez_compressed(folder/'expected.npz',total=a['total_int'],result=a['result_int'],saturated=a['saturated'])
    # A one-dot waveform fixture avoids reparsing 25343 preceding dots.
    last=folder/'last';last.mkdir()
    for name,values,bits in [('x',a['X_int'][-1,:],16),('w',a['W_int'][:,-1],16),
                             ('bias',[a['b_int'][-1]],40),('shift',[12],5),
                             ('total',[a['total_int'][-1,-1]],41),('result',[a['result_int'][-1,-1]],16),
                             ('saturated',[a['saturated'][-1,-1]],1)]:
        write_hex(last/(name+'.hex'),values,bits)
    np.savez_compressed(last/'expected.npz',total=a['total_int'][-1:,-1:],
                        result=a['result_int'][-1:,-1:],saturated=a['saturated'][-1:,-1:])
    return {p.relative_to(folder).as_posix():dict(sha256=sha(p),bytes=p.stat().st_size) for p in folder.rglob('*') if p.is_file()}


def prepare(root, layers, output=None):
    root=Path(root).resolve()
    manifest=json.loads((root/'manifest.json').read_text(encoding='utf-8-sig'))
    for key,value in dict(FORMAT,shift=12).items():
        if manifest['numeric_format'].get(key)!=value:
            raise ValueError('manifest numeric_format.'+key)
    entries=manifest['layers']
    if sorted(x['layer_number'] for x in entries)!=list(range(1,13)):
        raise ValueError('manifest must contain layers 1..12 exactly once')
    reports=[]
    for layer in sorted(entries,key=lambda x:x['layer_number']):
        number=layer['layer_number']
        if number not in layers: continue
        try:
            arrays,report=load_layer(root,layer)
            if output is not None:
                report['exports']=export_layer(Path(output)/f'layer_{number:02d}',arrays)
            reports.append(report)
            print(f'PASS software layer={number:02d} outputs={TASKS} saturated={report["saturated"]}',flush=True)
        except (OSError,ValueError,KeyError,TypeError) as exc:
            raise ValueError(f'layer={number:02d}: {exc}') from exc
    return dict(status='passed',data_root=str(root),manifest_sha256=sha(root/'manifest.json'),
                tasks=len(reports)*TASKS,layers=reports,
                scope='Independent captured input per layer; complete matrices, not chained inference')


def compare_capture(csv_path, expected_path, output=None, skip=0, count=TASKS, task_base=0):
    actual=np.loadtxt(csv_path,delimiter=',',dtype=np.int64,ndmin=2)
    if actual.shape!=(count,4): raise ValueError(f'{csv_path}: capture shape {actual.shape}, expected {(count,4)}')
    check_equal(actual[:,0],np.arange(skip,skip+count)+task_base,'task sequence')
    with np.load(expected_path,allow_pickle=False) as expected:
        for col,key in enumerate(('total','result','saturated'),1):
            wanted=expected[key].ravel()[skip:skip+count]
            bad=np.flatnonzero(actual[:,col]!=wanted)
            if bad.size:
                i=int(bad[0]);task=task_base+skip+i
                raise ValueError(f'{csv_path}: row={task//256} column={task%256} {key}: got={actual[i,col]} expected={wanted[i]}')
    if output is not None:
        np.savez_compressed(output,**{key:actual[:,col].reshape(99,256) for col,key in enumerate(('total','result','saturated'),1)})
    return dict(passed=True,tasks=count,skip=skip,capture_sha256=sha(csv_path))
