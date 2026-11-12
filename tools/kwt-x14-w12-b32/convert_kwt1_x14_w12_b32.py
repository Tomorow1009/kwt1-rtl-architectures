"""Frozen FFN1 X14/F10 W12/F12 b32/F22 -> result16/F12, SHIFT=10.

Python 3.6+ and NumPy. Group8, sign-extended 16-bit load words; three bias
words retained. total.hex uses native signed33 (9 HEX digits), not signed41.
No TensorFlow, RTL execution, or model training. Output directories are new.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import sys
import zipfile

import numpy as np

FORMAT = dict(x_bits=14, x_fraction=10, w_bits=12, w_fraction=12,
              product_bits=26, accumulator_bits=32, bias_bits=32,
              bias_fraction=22, total_bits=33, total_fraction=22,
              result_bits=16, result_fraction=12, shift=10)
FILES = {'load.hex': (16, 23488), 'total.hex': (33, 25344),
         'result.hex': (16, 25344), 'saturated.hex': (1, 25344)}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def file_hash(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def save(path, obj):
    Path(path).write_text(json.dumps(obj, indent=2, ensure_ascii=False,
                                    allow_nan=False) + '\n', encoding='utf-8')


def floats(a, shape, name):
    a = np.asarray(a)
    if a.shape != shape or a.dtype.kind not in 'fiu':
        raise ValueError('Invalid ' + name + ' shape/type: ' + str(a.shape))
    a = a.astype(np.float64)
    if not np.isfinite(a).all():
        raise ValueError('Non-finite ' + name)
    return a


def integers(a, shape, bits, name):
    a = np.asarray(a)
    if a.shape != shape or a.dtype.kind not in 'iu':
        raise ValueError('Invalid integer ' + name)
    if int(a.min()) < -(1 << (bits-1)) or int(a.max()) >= (1 << (bits-1)):
        raise ValueError('Out of range ' + name)
    return a.astype(np.int64)


def quantize(a, fraction, bits):
    lo, hi = -(1 << (bits-1)), (1 << (bits-1))-1
    with np.errstate(over='ignore'):
        scaled = np.ldexp(a, fraction)
    capped = np.clip(scaled, lo-1, hi+1)
    frac, whole = np.modf(np.abs(capped))
    rounded = np.copysign(whole + (frac >= 0.5), capped)
    encoded = np.clip(rounded, lo, hi).astype(np.int64)
    return encoded, int(np.count_nonzero(encoded != rounded))


def reference(x, w, b):
    x = integers(x, (99,64), 14, 'X')
    w = integers(w, (64,256), 12, 'W')
    b = integers(b, (256,), 32, 'b')
    accumulator = x @ w
    if np.any(accumulator < -(1 << 31)) or np.any(accumulator >= (1 << 31)):
        raise ValueError('Accumulator overflow')
    total = accumulator + b
    if np.any(total < -(1 << 32)) or np.any(total >= (1 << 32)):
        raise ValueError('Total overflow')
    mag = (np.abs(total) + 512) >> 10
    rounded = np.where(total < 0, -mag, mag)
    result = np.clip(rounded, -32768, 32767)
    return dict(total=total, result=result, saturated=(result != rounded).astype(np.int64))


def pack(x, w, b):
    words = [int(v) & 65535 for v in x.flat]
    for g in range(32):
        words.extend(int(w[k,g*8+lane]) & 65535 for k in range(64) for lane in range(8))
        for lane in range(8):
            # Sign extend signed32 to signed40, then preserve old three-word ABI.
            v = int(b[g*8+lane]) & ((1 << 40)-1)
            words.extend((v >> n) & 65535 for n in (0,16,32))
    return words


def encode(values, bits):
    fmt = '%0' + str((bits+3)//4) + 'x\n'
    mask = (1 << bits)-1
    return ''.join(fmt % (int(v) & mask) for v in np.asarray(values).flat).encode('ascii')


def decode(data, bits, count, signed=False):
    lines = data.decode('ascii').splitlines()
    pattern = re.compile('[0-9a-fA-F]{%d}' % ((bits+3)//4))
    if len(lines) != count or any(pattern.fullmatch(v) is None for v in lines):
        raise ValueError('Invalid HEX line count/encoding')
    values = [int(v,16) for v in lines]
    if any(v >= (1 << bits) for v in values):
        raise ValueError('Nonzero reserved high bits')
    if signed:
        values = [v-(1 << bits) if v & (1 << (bits-1)) else v for v in values]
    return np.array(values,dtype=np.int64)


def check_layer(folder):
    """Independent load decoder and k-wise integer reference (no pack/matmul)."""
    folder = Path(folder)
    raw = {name:(folder/name).read_bytes() for name in FILES}
    words = decode(raw['load.hex'],16,23488)
    signed = np.where(words >= 32768,words-65536,words)
    x = signed[:6336].reshape(99,64)
    if np.any(x < -8192) or np.any(x > 8191):
        raise ValueError('X14 sign extension')
    w = np.empty((64,256),dtype=np.int64)
    b = np.empty(256,dtype=np.int64)
    for c in range(256):
        base = 6336 + (c//8)*536
        lane = c%8
        w[:,c] = signed[base+lane:base+512:8]
        at = base+512+lane*3
        u = int(words[at]) | (int(words[at+1]) << 16)
        if int(words[at+2]) != (255 if u & (1 << 31) else 0):
            raise ValueError('b32 sign extension or padding')
        b[c] = u-(1 << 32) if u & (1 << 31) else u
    if np.any(w < -2048) or np.any(w > 2047):
        raise ValueError('W12 sign extension')
    acc = np.zeros((99,256),dtype=np.int64)
    for k in range(64):
        acc += x[:,k:k+1] * w[k:k+1,:]
        if np.any(acc < -(1 << 31)) or np.any(acc >= (1 << 31)):
            raise ValueError('Prefix accumulator overflow')
    total = acc+b
    if np.any(total < -(1 << 32)) or np.any(total >= (1 << 32)):
        raise ValueError('Total overflow')
    # Divide/remainder implementation, independent of reference's add-and-shift.
    q, rem = np.divmod(np.abs(total),1024)
    q += rem >= 512
    q = np.where(total < 0,-q,q)
    result = np.minimum(np.maximum(q,-32768),32767)
    expected = dict(total=total,result=result,saturated=(result != q).astype(np.int64))
    for key in expected:
        bits,count = FILES[key+'.hex']
        actual = decode(raw[key+'.hex'],bits,count,key != 'saturated').reshape(99,256)
        if not np.array_equal(actual,expected[key]):
            raise ValueError('Mismatch ' + key)
    meta_path = folder/'layout.json'
    if meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding='utf-8'))
        if meta['format'] != FORMAT:
            raise ValueError('Wrong format')
        for name,data in raw.items():
            if meta['files'][name] != dict(bytes=len(data),sha256=digest(data)):
                raise ValueError('Hash mismatch ' + name)
    return dict(status='passed',outputs=25344,mismatches=0,
                accumulator_min=int(acc.min()),accumulator_max=int(acc.max()),
                total_min=int(total.min()),total_max=int(total.max()),
                saturated=int((result != q).sum()))


def export_layer(folder, x, w, b, layer, y=None):
    if type(layer) is not int or not 1 <= layer <= 12:
        raise ValueError('Layer must be 1..12')
    x = floats(x,(99,64),'X'); w = floats(w,(64,256),'W'); b = floats(b,(256,),'b')
    if y is not None:
        y = floats(y,(99,256),'Y')
    xq,xc = quantize(x,10,14); wq,wc = quantize(w,12,12); bq,bc = quantize(b,22,32)
    results = reference(xq,wq,bq)
    data = {'load.hex':encode(pack(xq,wq,bq),16)}
    data.update({k+'.hex':encode(v,FILES[k+'.hex'][0]) for k,v in results.items()})
    folder = Path(folder); folder.mkdir(parents=True,exist_ok=False)
    for name,raw in data.items():
        (folder/name).write_bytes(raw)
    save(folder/'layout.json',dict(schema='kwt1-x14-w12-b32-group8-v1',layer=layer,
         format=FORMAT,load_words=23488,outputs=25344,bias_storage_bits=40,
         files={k:dict(bytes=len(v),sha256=digest(v)) for k,v in data.items()}))
    audit = check_layer(folder)
    audit.update(layer=layer,clipping=dict(x=xc,w=wc,b=bc))
    if y is not None:
        delta = results['result'].astype(np.float64)/4096-y
        audit['error'] = dict(nrmse_percent=float(100*np.sqrt(np.mean(delta*delta))/max(np.sqrt(np.mean(y*y)),1e-8)),
                              max_abs_error=float(np.max(np.abs(delta))))
    save(folder/'hex_check.json',audit)
    return audit


def arrays(data, weights=False):
    with np.load(io.BytesIO(data),allow_pickle=False) as z:
        if weights:
            return floats(z['W'],(12,64,256),'W'),floats(z['b'],(12,256),'b')
        return floats(z['X'],(12,99,64),'X'),floats(z['Y'],(12,99,256),'Y') if 'Y' in z else None


def convert_sample(sample_bytes, weight_arrays, out):
    x,y = arrays(sample_bytes); w,b = weight_arrays
    return [export_layer(Path(out)/('layer_%02d'%(i+1)),x[i],w[i],b[i],i+1,
                         None if y is None else y[i]) for i in range(12)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument('--archive',type=Path,help='Original worst100 FLOAT zip; select original samples 001..030')
    modes.add_argument('--sample',type=Path,help='One complete 12-layer float NPZ')
    modes.add_argument('--check',type=Path,help='Recheck one layer directory, without writing')
    parser.add_argument('--weights',type=Path,help='Shared weights NPZ, required with --sample')
    parser.add_argument('--out',type=Path,help='New or empty output directory')
    a = parser.parse_args()
    if a.check:
        if a.out or a.weights:
            parser.error('--check takes no --out/--weights')
        print(json.dumps(check_layer(a.check))); return 0
    if not a.out or (a.sample and not a.weights) or (a.archive and a.weights):
        parser.error('Use --archive ZIP --out DIR or --sample NPZ --weights NPZ --out DIR')
    if a.out.exists() and (not a.out.is_dir() or any(a.out.iterdir())):
        raise ValueError('Output must be new or empty; existing contents are protected')
    if a.out.is_symlink():
        raise ValueError('Symlink output refused')
    a.out.mkdir(parents=True,exist_ok=True)
    manifest = dict(schema='kwt1-x14-w12-b32-group8-v1',status='running',format=FORMAT,
                    converter_sha256=file_hash(__file__),samples=[],rtl_executed=False)
    save(a.out/'manifest.json',manifest)
    if a.archive:
        manifest.update(source_archive=str(a.archive),archive_sha256=file_hash(a.archive),
                        selection='Original frozen SHIFT16 ranking, first 30; NOT reranked for X14/W12/b32')
        with zipfile.ZipFile(str(a.archive)) as z:
            roots = [n[:-len('shared_weights.npz')] for n in z.namelist() if n.endswith('/shared_weights.npz')]
            if len(roots) != 1 or len(z.namelist()) != len(set(z.namelist())):
                raise ValueError('Ambiguous ZIP members')
            root = roots[0]; wb = z.read(root+'shared_weights.npz'); weights = arrays(wb,True)
            manifest['weights_sha256'] = digest(wb)
            for n in range(1,31):
                name = 'sample_%03d'%n
                sb = z.read(root+name+'/float_tensors.npz')
                source = json.loads(z.read(root+name+'/source.json').decode('utf-8-sig'))
                layers = convert_sample(sb,weights,a.out/name)
                manifest['samples'].append(dict(sample=n,original_rank=n,wav=source['wav'],
                    split=source['split'],wav_sha256=source['wav_sha256'],sample_sha256=digest(sb),layers=layers))
                save(a.out/'manifest.json',manifest)
                print('PASS %s: 12 layers, 304128 outputs'%name,flush=True)
    else:
        sb = a.sample.read_bytes(); wb = a.weights.read_bytes()
        layers = convert_sample(sb,arrays(wb,True),a.out/'sample_001')
        manifest.update(weights_sha256=digest(wb),selection='Explicit single float sample')
        manifest['samples'] = [dict(sample=1,sample_sha256=digest(sb),layers=layers)]
    layers = [layer for sample in manifest['samples'] for layer in sample['layers']]
    manifest.update(status='passed',sample_count=len(manifest['samples']),layer_count=len(layers),
                    outputs=len(layers)*25344,hex_files=len(layers)*4,mismatches=0,
                    clipping={k:sum(v['clipping'][k] for v in layers) for k in ('x','w','b')},
                    saturated=sum(v['saturated'] for v in layers),
                    max_layer_nrmse_percent=max((v['error']['nrmse_percent'] for v in layers if 'error' in v),default=None),
                    scope='Software integer/HEX verification only; no RTL, SoC, official600 or model classification acceptance')
    inventory = {p.relative_to(a.out).as_posix():dict(bytes=p.stat().st_size,sha256=file_hash(p))
                 for p in sorted(a.out.rglob('*.hex'))}
    if len(inventory) != manifest['hex_files']:
        raise ValueError('Final HEX inventory count mismatch')
    save(a.out/'SHA256_FILES.json',inventory)
    manifest['inventory_sha256'] = file_hash(a.out/'SHA256_FILES.json')
    save(a.out/'manifest.json',manifest)
    print('COMPLETE samples=%d outputs=%d mismatches=0'%(manifest['sample_count'],manifest['outputs']))
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError,ValueError,KeyError,zipfile.BadZipFile) as exc:
        print('FAIL: '+str(exc),file=sys.stderr)
        sys.exit(1)
