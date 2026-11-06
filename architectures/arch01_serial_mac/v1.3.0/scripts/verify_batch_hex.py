"""Read-only full-shard integer verification. Python + NumPy, no TensorFlow."""
import argparse
import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = ROOT/'KWT1/model_data/outputs/all_speech_dot00'
FORMAT = 'x/w signed16 frac12; bias signed40 frac24; total signed41; result signed16; nearest ties away; saturate'
FILES = dict(x=(16,64,True), w=(16,64,True), bias=(40,1,True),
             shift=(5,1,False), total=(41,1,True), result=(16,1,True), saturated=(1,1,False))


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()


def require(condition,message):
    if not condition: raise ValueError(message)


def quantized(a,frac,bits):
    require(np.isfinite(a).all(),'nonfinite float tensor')
    scaled=a.astype(np.float64)*2**frac
    whole=np.floor(np.abs(scaled))
    q=np.sign(scaled)*(whole+((np.abs(scaled)-whole)>=0.5))
    return np.clip(q,-2**(bits-1),2**(bits-1)-1).astype(np.int64)


def read_hex(path,bits,count,signed,context,per_task):
    # Fixed ASCII records: vectorized decoder, strict width and LF/CRLF checks.
    raw=path.read_bytes(); width=(bits+3)//4
    if len(raw)==count*(width+1):
        lines=np.frombuffer(raw,dtype=np.uint8).reshape(count,width+1)
        require(np.all(lines[:,-1]==10),f'{path.name}: invalid line ending/width')
    elif len(raw)==count*(width+2):
        lines=np.frombuffer(raw,dtype=np.uint8).reshape(count,width+2)
        require(np.all(lines[:,-2:]==[13,10]),f'{path.name}: invalid CRLF records')
    else:
        raise ValueError(f'{path.name}: wrong byte/element count; got {len(raw)}, expected {count} records of {width} hex digits')
    digits=lines[:,:width]
    valid=((digits>=48)&(digits<=57))|((digits>=65)&(digits<=70))|((digits>=97)&(digits<=102))
    if not valid.all():
        line=int(np.argwhere(~valid)[0,0]); raise ValueError(context(line//per_task)+f' {path.name} line={line+1}: invalid/X/Z hex character')
    values=np.zeros(count,dtype=np.int64)
    for col in range(width):
        c=digits[:,col].astype(np.int64)
        nibble=np.where(c<=57,c-48,np.where(c<=70,c-55,c-87))
        values=(values<<4)|nibble
    bad=values >= 1<<bits
    if bad.any():
        line=int(np.flatnonzero(bad)[0]); raise ValueError(context(line//per_task)+f' {path.name} line={line+1}: nonzero padding bits')
    if signed: values=np.where(values & (1<<(bits-1)),values-(1<<bits),values)
    return values


def check_equal(actual,expected,label,context):
    expected=np.broadcast_to(expected,actual.shape)
    bad=actual!=expected
    if bad.any():
        idx=tuple(int(x) for x in np.argwhere(bad)[0])
        task=idx[0]*12+idx[1]
        raise ValueError(f'{context(task)} {label} index={idx}: got {actual[idx]}, expected {expected[idx]}')


def verify(root):
    root=root.resolve(); manifest_path=root/'manifest.json'
    m=json.loads(manifest_path.read_text(encoding='utf-8-sig'))
    require(m['status']=='complete','manifest status is not complete')
    require(m['layers']==12 and m['coordinate']==[0,0] and m['shift']==12,'unsupported layers/coordinate/shift')
    require(m['numeric_format']==FORMAT,'unsupported manifest numeric_format')
    require(sha(root/'samples.csv')==m['inventory_sha256'],'samples.csv SHA256 mismatch')
    with (root/'samples.csv').open(encoding='utf-8-sig',newline='') as f: index=list(csv.DictReader(f))
    require(len(index)==m['total_samples']==len({r['path'] for r in index}),'sample inventory count/uniqueness mismatch')
    require(m['total_tasks']==12*len(index),'manifest task count mismatch')
    require([int(r['sample_id']) for r in index]==list(range(len(index))),'sample IDs not contiguous')
    paths=[s['path'] for s in m['shards']]
    require(len(paths)==len(set(paths)),'duplicate shard path')
    with np.load(root/'shared_parameters.npz',allow_pickle=False) as p:
        wf,w,bf,b=(p[k] for k in ('W_float','W_int','b_float','b_int'))
        require(w.shape==(12,64) and b.shape==(12,),'shared parameter shapes mismatch')
        require(w.dtype.kind in 'iu' and b.dtype.kind in 'iu','shared integer dtype mismatch')
        require(np.array_equal(w,quantized(wf,12,16)),'shared W quantization mismatch')
        require(np.array_equal(b,quantized(bf,24,40)),'shared bias quantization mismatch')
    completed=0; cursor=0; stats={}; reports=[]
    for shard in m['shards']:
        tag=shard['path']
        try:
            folder=(root/tag).resolve(); folder.relative_to(root)
            n=int(shard['samples']); tasks=int(shard['tasks']); split=shard['split']
            require(n>0 and tasks==n*12,'invalid shard task/sample count')
            require(shard['first_sample_id']==cursor and shard['last_sample_id']==cursor+n-1,'shard sample coverage gap/overlap')
            rows=index[cursor:cursor+n]
            require(len(rows)==n,'shard beyond sample inventory')
            for i,row in enumerate(rows):
                require(row['shard']==tag and row['split']==split and int(row['sample_in_shard'])==i and
                        int(row['first_task_in_shard'])==i*12,'sample/shard mapping mismatch at sample '+row['sample_id'])
            def context(task):
                row=rows[min(task//12,n-1)]
                return f'shard={tag} task={task} sample_id={row["sample_id"]} sample={row["path"]} layer={task%12+1:02d}'
            required={name+'.hex' for name in FILES}|{'selected_float.npz'}
            require(required.issubset(shard['sha256']),'missing file hashes in shard manifest')
            hashes={}
            for name in sorted(required):
                digest=sha(folder/name); hashes[name]=digest
                require(digest==shard['sha256'][name],f'{name}: SHA256 mismatch (task/sample/layer unavailable before decode)')
            arrays={}
            for name,(bits,per,signed) in FILES.items():
                a=read_hex(folder/(name+'.hex'),bits,tasks*per,signed,context,per)
                arrays[name]=a.reshape((n,12,64) if per==64 else (n,12))
            x=arrays['x']; context0=context
            check_equal(arrays['w'],w,'w.hex/shared W',context)
            check_equal(arrays['bias'],b,'bias.hex/shared bias',context)
            check_equal(arrays['shift'],12,'shift.hex',context)
            # int16 products, 64 terms and int40 bias fit int64 exactly.
            total=np.sum(x*arrays['w'],axis=2,dtype=np.int64)+arrays['bias']
            whole,rem=np.divmod(np.abs(total),4096)
            rounded=np.where(total<0,-1,1)*(whole+(rem>=2048))
            result=np.clip(rounded,-32768,32767); saturated=result!=rounded
            for name,expected in [('total',total),('result',result),('saturated',saturated)]:
                check_equal(arrays[name],expected,name+'.hex/integer oracle',context)
            with np.load(folder/'selected_float.npz',allow_pickle=False) as f:
                xf,yf=f['X_float'],f['Y_float']
                require(xf.shape==(n,12,64) and yf.shape==(n,12),'selected_float.npz shape mismatch')
                require(xf.dtype==np.float32 and yf.dtype==np.float32,'selected_float.npz must be float32')
                require(np.isfinite(yf).all(),'nonfinite Y_float')
                check_equal(x,quantized(xf,12,16),'x.hex/float quantization',context)
                error=result/4096.0-yf.astype(np.float64)
                st=stats.setdefault(split,dict(samples=0,tasks=0,sse=np.zeros(12),ref=np.zeros(12),
                    max_abs=np.zeros(12),saturated=np.zeros(12,dtype=np.int64),x_clipped=np.zeros(12,dtype=np.int64)))
                st['samples']+=n; st['tasks']+=tasks
                st['sse']+=np.sum(error*error,axis=0); st['ref']+=np.sum(yf.astype(np.float64)**2,axis=0)
                st['max_abs']=np.maximum(st['max_abs'],np.max(np.abs(error),axis=0))
                st['saturated']+=np.sum(saturated,axis=0)
                scaled=xf.astype(np.float64)*4096; aq=np.floor(np.abs(scaled)); rq=np.sign(scaled)*(aq+((np.abs(scaled)-aq)>=.5))
                st['x_clipped']+=np.sum((rq < -32768)|(rq > 32767),axis=(0,2))
            completed+=tasks; cursor+=n
            reports.append(dict(path=tag,samples=n,tasks=tasks,passed=True,sha256=hashes))
            print(f'PASS shard={tag} tasks={tasks} cumulative={completed}/{m["total_tasks"]}',flush=True)
        except (OSError,ValueError,KeyError,IndexError) as exc:
            raise ValueError(f'shard={tag}: {exc}') from exc
    require(cursor==len(index) and completed==m['total_tasks'],'incomplete shard coverage')
    require(set(stats)==set(m['splits']),'split coverage mismatch')
    metrics={}
    for split,st in stats.items():
        require(st['samples']==m['splits'][split]['samples'] and st['tasks']==m['splits'][split]['tasks'],split+' count mismatch')
        metrics[split]=dict(samples=st['samples'],tasks=st['tasks'],
            nrmse_per_layer=(np.sqrt(st['sse']/st['samples'])/np.maximum(np.sqrt(st['ref']/st['samples']),1e-8)).tolist(),
            max_absolute_error_per_layer=st['max_abs'].tolist(),saturated_per_layer=st['saturated'].tolist(),
            x_clipped_per_layer=st['x_clipped'].tolist())
    return dict(status='passed',checked_at_utc=datetime.now(timezone.utc).isoformat(),data_root=str(root),
        scope='All exported Y[0,0] tasks only; not full matrices or classification accuracy',
        samples=cursor,tasks=completed,shards=len(reports),python=sys.version,numpy=np.__version__,splits=metrics,
        manifest_sha256=sha(manifest_path),inventory_sha256=sha(root/'samples.csv'),
        shared_parameters_sha256=sha(root/'shared_parameters.npz'),results=reports)


def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('root',type=Path,nargs='?',default=DEFAULT_DATA)
    p.add_argument('--report',type=Path); args=p.parse_args()
    try:
        report=verify(args.root)
        if args.report:
            args.report.parent.mkdir(parents=True,exist_ok=True)
            args.report.write_text(json.dumps(report,indent=2),encoding='utf-8')
        print(f'PASS: software samples={report["samples"]} shards={report["shards"]} tasks={report["tasks"]}')
        return 0
    except (OSError,ValueError,KeyError,TypeError) as exc:
        print('FAIL: '+str(exc),file=sys.stderr); return 1


if __name__=='__main__': sys.exit(main())
