"""Read-only by default: verify 12 KWT dot tasks without TensorFlow."""
import argparse
import hashlib
import json
import math
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = ROOT/'KWT1/model_data/outputs/real_sample_001'
FORMAT = dict(x_bits=16, w_bits=16, bias_bits=40, total_bits=41,
              result_bits=16, x_fraction=12, w_fraction=12, bias_fraction=24,
              rounding='nearest, ties away from zero', overflow='saturation')


def equal(actual, expected, label):
    if actual != expected:
        raise ValueError(f'{label}: got {actual!r}, expected {expected!r}')


def read_hex(path, bits, count, signed=True):
    lines = path.read_text(encoding='ascii').splitlines()
    equal(len(lines), count, f'{path.name} element count')
    values = []
    for i, line in enumerate(lines):
        if not re.fullmatch(r'[0-9a-fA-F]{%d}' % ((bits+3)//4), line):
            raise ValueError(f'{path.name}[{i}]: invalid hex width/characters: {line!r}')
        value = int(line,16)
        if value >= 1 << bits:
            raise ValueError(f'{path.name}[{i}]: nonzero padding bits')
        if signed and value & (1 << (bits-1)):
            value -= 1 << bits
        values.append(value)
    return values


def rounded_ratio(n, d):
    q, r = divmod(abs(n),d)
    q += int(2*r >= d)
    return -q if n < 0 else q


def quantize(value, frac, bits):
    value = float(value)
    if not math.isfinite(value):
        raise ValueError('nonfinite floating input')
    n, d = value.as_integer_ratio()
    q = rounded_ratio(n * 2**frac,d)
    return min(2**(bits-1)-1,max(-2**(bits-1),q))


def vector_equal(actual, expected, label):
    equal(len(actual),len(expected),label+' length')
    for i,(a,b) in enumerate(zip(actual,expected)):
        equal(int(a),int(b),f'{label}[{i}]')


def validate(root):
    root = root.resolve()
    manifest = json.loads((root/'manifest.json').read_text(encoding='utf-8-sig'))
    fmt = manifest['numeric_format']
    for key,value in FORMAT.items():
        equal(fmt[key],value,'manifest.numeric_format.'+key)
    shift = fmt['shift']
    if type(shift) is not int or not 0 <= shift <= 31:
        raise ValueError('manifest shift must be an integer in [0,31]')
    layers = manifest['layers']
    equal(sorted(layer['layer_number'] for layer in layers),list(range(1,13)),
          'manifest layer numbers')
    rows, hashes = [], {}
    for layer in sorted(layers,key=lambda item:item['layer_number']):
        number = layer['layer_number']
        try:
            folder = (root/layer['hex_dir']).resolve()
            folder.relative_to(root)  # do not read paths outside the data root
            selected = layer['selected_dot']
            i,j = selected['row'], selected['column']
            if type(i) is not int or type(j) is not int or not (0<=i<99 and 0<=j<256):
                raise ValueError('invalid selected row/column')
            x = read_hex(folder/'x.hex',16,64)
            w = read_hex(folder/'w.hex',16,64)
            bias = read_hex(folder/'bias.hex',40,1)[0]
            equal(read_hex(folder/'shift.hex',5,1,False)[0],shift,'shift.hex')
            total = sum(a*b for a,b in zip(x,w)) + bias
            rounded = rounded_ratio(total,2**shift)
            result = min(32767,max(-32768,rounded))
            saturated = int(result != rounded)
            equal(read_hex(folder/'total.hex',41,1)[0],total,'total.hex[0]')
            equal(read_hex(folder/'result.hex',16,1)[0],result,'result.hex[0]')
            equal(read_hex(folder/'saturated.hex',1,1,False)[0],saturated,'saturated.hex[0]')
            with np.load(folder.parent/'integer_tensors.npz',allow_pickle=False) as ints, \
                    np.load(folder.parent/'float_tensors.npz',allow_pickle=False) as floats:
                for key,shape in [('X',(99,64)),('W',(64,256)),('b',(256,)),('Y_float',(99,256))]:
                    equal(floats[key].shape,shape,'float_tensors.npz/'+key+' shape')
                    equal(floats[key].dtype,np.dtype('float32'),'float_tensors.npz/'+key+' dtype')
                for key,shape in [('X_int',(99,64)),('W_int',(64,256)),('b_int',(256,)),
                                  ('total_int',(99,256)),('result_int',(99,256)),('saturated',(99,256))]:
                    equal(ints[key].shape,shape,'integer_tensors.npz/'+key+' shape')
                    if ints[key].dtype.kind not in ('i','u','b'):
                        raise ValueError('integer_tensors.npz/'+key+': non-integer dtype')
                vector_equal(x,ints['X_int'][i,:],'x.hex vs NPZ')
                vector_equal(w,ints['W_int'][:,j],'w.hex vs NPZ')
                equal(bias,int(ints['b_int'][j]),'bias.hex vs NPZ')
                for key,value in [('total_int',total),('result_int',result),('saturated',saturated)]:
                    equal(int(ints[key][i,j]),value,'integer_tensors.npz/'+key)
                vector_equal(x,[quantize(v,12,16) for v in floats['X'][i,:]],'x.hex vs float quantization')
                vector_equal(w,[quantize(v,12,16) for v in floats['W'][:,j]],'w.hex vs float quantization')
                equal(bias,quantize(floats['b'][j],24,40),'bias.hex vs float quantization')
                y_float = float(floats['Y_float'][i,j])
                if not math.isfinite(y_float):
                    raise ValueError('nonfinite Y_float')
                equal(y_float,selected['tensorflow_float32'],'Y_float vs manifest')
            for key,value in [('total_integer',total),('result_integer',result),('saturated',bool(saturated))]:
                equal(selected[key],value,'manifest.selected_dot.'+key)
            decoded = result * 2.0**(shift-24)
            rows.append(dict(layer=number,row=i,column=j,hex_dir=str(folder),shift=shift,
                total=total,result=result,saturated=saturated,float_reference=y_float,
                decoded_result=decoded,absolute_error=abs(decoded-y_float),passed=True))
            for path in list(sorted(folder.glob('*.hex'))) + [folder.parent/'integer_tensors.npz',folder.parent/'float_tensors.npz']:
                hashes[str(path.relative_to(root))] = hashlib.sha256(path.read_bytes()).hexdigest()
            print(f'PASS layer={number:02d} total={total} result={result} sat={saturated} '
                  f'float={y_float:.9g} decoded={decoded:.9g} abs_error={abs(decoded-y_float):.9g}')
        except (OSError,ValueError,KeyError,IndexError,TypeError) as exc:
            raise ValueError(f'layer {number:02d} ({layer["hex_dir"]}): {exc}') from exc
    return dict(passed=12,total=12,scope='12 selected independent dots; not complete layer or SoC',
                checked_at_utc=datetime.now(timezone.utc).isoformat(),data_root=str(root),
                python=sys.version,numpy=np.__version__,numeric_format=fmt,layers=rows,sha256=hashes)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('data_root',nargs='?',type=Path,default=DEFAULT_DATA)
    parser.add_argument('--report',type=Path,help='Optional output JSON; omitted means no writes')
    args = parser.parse_args()
    try:
        report = validate(args.data_root)
        if args.report:
            args.report.parent.mkdir(parents=True,exist_ok=True)
            args.report.write_text(json.dumps(report,indent=2),encoding='utf-8')
        print('PASS: software 12/12 real KWT dots (HEX, integer NPZ, float quantization)')
        return 0
    except (OSError,ValueError,KeyError,TypeError) as exc:
        print('FAIL: '+str(exc),file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
