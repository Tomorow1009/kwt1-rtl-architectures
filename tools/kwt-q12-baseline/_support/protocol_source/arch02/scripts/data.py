"""Export independently checked NPZ to the architecture-2 loading protocol."""
import hashlib
import json
from pathlib import Path
import sys
import numpy as np

ARCH=Path(__file__).resolve().parents[1]
PROJECT=ARCH.parent
sys.path.insert(0,str(PROJECT/'scripts'))
from full_matrix_data import DEFAULT_DATA, load_layer, FORMAT, write_hex


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x): Path(p).write_text(json.dumps(x,indent=2),encoding='utf-8')


def reference(x,w,b,shift):
    total=x.astype(np.int64)@w.astype(np.int64)+b.astype(np.int64)
    q,r=np.divmod(np.abs(total),1<<shift)
    rounded=np.where(total<0,-1,1)*(q+(2*r>=(1<<shift)))
    result=np.clip(rounded,-32768,32767)
    return dict(total=total,result=result,saturated=(rounded!=result).astype(np.int64))


def export(folder,x,w,b,expected,shift):
    folder.mkdir(parents=True)
    words=[int(v)&65535 for v in x.flat]
    for group in range(32):
        words.extend(int(w[k,group*8+lane])&65535 for k in range(64) for lane in range(8))
        for lane in range(8):
            value=int(b[group*8+lane])&((1<<40)-1)
            words.extend((value>>bit)&65535 for bit in (0,16,32))
    assert len(words)==23488
    # Decode the stream using bank addresses, independent of HEX formatting.
    decoded_x=np.array(words[:6336],dtype=np.int64).reshape(99,64)
    decoded_x=np.where(decoded_x>=32768,decoded_x-65536,decoded_x)
    assert np.array_equal(decoded_x,x)
    for group in range(32):
        start=6336+group*536
        for lane in range(8):
            bank=np.array([words[start+k*8+lane] for k in range(64)])
            bank=np.where(bank>=32768,bank-65536,bank)
            assert np.array_equal(bank,w[:,group*8+lane])
            low=start+512+lane*3
            bias=words[low]+(words[low+1]<<16)+(words[low+2]<<32)
            if bias&(1<<39):bias-=1<<40
            assert bias==int(b[group*8+lane]) and words[low+2]<256
    write_hex(folder/'load.hex',words,16)
    for key,bits in [('total',41),('result',16),('saturated',1)]:write_hex(folder/(key+'.hex'),expected[key],bits)
    np.savez_compressed(folder/'expected.npz',**expected)
    info=dict(shift=shift,load_words=23488,outputs=25344,sha256={p.name:sha(p) for p in folder.iterdir()})
    save(folder/'layout.json',info)
    return info


def prepare(root,out):
    root=Path(root).resolve();manifest=json.loads((root/'manifest.json').read_text(encoding='utf-8-sig'))
    for key,value in dict(FORMAT,shift=12).items():
        if manifest['numeric_format'].get(key)!=value:raise ValueError('numeric_format.'+key)
    if sorted(l['layer_number'] for l in manifest['layers'])!=list(range(1,13)):raise ValueError('Expected 12 layers')
    reports=[]
    for layer in sorted(manifest['layers'],key=lambda x:x['layer_number']):
        number=layer['layer_number']
        try:
            arrays,report=load_layer(root,layer)
            expected=reference(arrays['X_int'],arrays['W_int'],arrays['b_int'],12)
            for key,source in [('total','total_int'),('result','result_int'),('saturated','saturated')]:
                if not np.array_equal(expected[key],arrays[source]):raise ValueError(key+' matrix mismatch')
            report['layout']=export(out/f'layer_{number:02d}',arrays['X_int'],arrays['W_int'],arrays['b_int'],expected,12)
            reports.append(report);print(f'PASS software layer={number:02d} outputs=25344',flush=True)
        except Exception as exc:raise ValueError(f'layer={number:02d}: {exc}') from exc
    x=np.array([[-32768,32767,-1,0,1,4096,-4096,123][(row+k)%8] for row in range(99) for k in range(64)],dtype=np.int64).reshape(99,64)
    w=np.array([[0,1,-1,32767,-32768,17,-19,4096][(col+k//8)%8] for k in range(64) for col in range(256)],dtype=np.int64).reshape(64,256)
    b=np.array([((1<<39)-1) if col%8==0 else -(1<<39) if col%8==1 else (col-128)*4096 for col in range(256)],dtype=np.int64)
    export(out/'extremes',x,w,b,reference(x,w,b,12),12)
    x=np.zeros((99,64),dtype=np.int64)
    values=[0,1023,1024,1025,-1023,-1024,-1025,32767*2048,32768*2048,-32768*2048,-32769*2048]
    b=np.array([values[col%len(values)] for col in range(256)],dtype=np.int64)
    export(out/'rounding',x,w,b,reference(x,w,b,11),11)
    return dict(status='passed',tasks=304128,layers=reports,data_root=str(root),manifest_sha256=sha(root/'manifest.json'))


def compare(path,data,output):
    actual=np.loadtxt(path,delimiter=',',dtype=np.int64,ndmin=2)
    if actual.shape!=(25344,4):raise ValueError(f'{path}: capture shape {actual.shape}')
    ids=actual[:,0]
    if not np.array_equal(np.sort(ids),np.arange(25344)):raise ValueError('Missing/duplicate matrix coordinates')
    # Hardware emits group -> row -> lane; require that exact sequence as well.
    sequence=np.array([row*256+group*8+lane for group in range(32) for row in range(99) for lane in range(8)])
    if not np.array_equal(ids,sequence):raise ValueError('Output scheduling order mismatch')
    actual=actual[np.argsort(ids)]
    with np.load(data/'expected.npz',allow_pickle=False) as expected:
        for col,key in enumerate(('total','result','saturated'),1):
            bad=np.flatnonzero(actual[:,col]!=expected[key].ravel())
            if bad.size:
                idx=int(bad[0]);raise ValueError(f'{path}: row={idx//256} column={idx%256} {key}')
    np.savez_compressed(output,**{key:actual[:,i].reshape(99,256) for i,key in enumerate(('total','result','saturated'),1)})
    return dict(outputs=25344,capture_sha256=sha(path),matrix_sha256=sha(output))
