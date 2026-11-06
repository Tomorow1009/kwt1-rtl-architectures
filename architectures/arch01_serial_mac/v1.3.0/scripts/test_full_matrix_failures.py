"""Fault injection on new temporary copies; original NPZ/HEX remain untouched."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import numpy as np
from full_matrix_data import DEFAULT_DATA, load_layer, compare_capture


def main():
    p=argparse.ArgumentParser();p.add_argument('run',type=Path);p.add_argument('--data-root',type=Path,default=DEFAULT_DATA)
    args=p.parse_args();run=args.run.resolve();source=args.data_root.resolve()
    dest=run/'negative_tests';dest.mkdir(exist_ok=False)
    manifest=json.loads((source/'manifest.json').read_text(encoding='utf-8-sig'))
    layer=next(x for x in manifest['layers'] if x['layer_number']==1)
    results=[]
    for case,word in [('valid',''),('shape','shape'),('range','out of range'),('reference','result_int'),('quantization','quantization')]:
        root=dest/('npz_'+case);folder=root/Path(layer['hex_dir']).parent;folder.mkdir(parents=True)
        for name in ('integer_tensors.npz','float_tensors.npz'):
            shutil.copy2(source/Path(layer['hex_dir']).parent/name,folder/name)
        path=folder/'integer_tensors.npz'
        with np.load(path,allow_pickle=False) as archive: data={k:archive[k].copy() for k in archive.files}
        if case=='shape': data['X_int']=data['X_int'][:-1]
        elif case=='range': data['W_int'][0,0]=32768
        elif case=='reference': data['result_int'][0,0]+=1
        elif case=='quantization': data['X_int'][0,0]+=1
        np.savez_compressed(path,**data)
        error=''
        try: load_layer(root,layer)
        except (ValueError,KeyError,OSError) as exc: error=str(exc)
        ok=(not error) if case=='valid' else word in error
        results.append(dict(suite='npz',case=case,passed=ok,error=error))
    # Small seven-file fixtures exercise the actual compiled TB without full preflight.
    for case,word in [('valid','PASS: batch HEX tasks=1'),('missing','Cannot open'),('truncated','Missing'),('reference','Mismatch')]:
        folder=dest/('hex_'+case);folder.mkdir()
        for name in ('x','w','bias','shift','total','result','saturated'):
            with (run/'data/layer_01'/(name+'.hex')).open() as f:
                values=[next(f) for _ in range(64 if name in ('x','w') else 1)]
            (folder/(name+'.hex')).write_text(''.join(values),encoding='ascii')
        if case=='missing': (folder/'w.hex').unlink()
        if case=='truncated': (folder/'x.hex').write_text('0000\n',encoding='ascii')
        if case=='reference':
            path=folder/'result.hex';path.write_text(f'{int(path.read_text(),16)^1:04x}\n',encoding='ascii')
        result=subprocess.run([shutil.which('vvp'),str(run/'iverilog/batch.vvp'),'+DATA_DIR='+folder.as_posix(),'+TASKS=1'],cwd=folder,capture_output=True,text=True,timeout=30)
        text=result.stdout+result.stderr;(folder/'check.log').write_text(text,encoding='utf-8')
        ok=word in text and ((result.returncode==0) if case=='valid' else result.returncode!=0)
        results.append(dict(suite='hex',case=case,passed=ok,exit_code=result.returncode))
    # Confirm reconstruction detects a plausible numerical error and duplicate task index.
    original=np.loadtxt(run/'iverilog/layer_01_full.csv',delimiter=',',dtype=np.int64)
    for case in ('duplicate','value'):
        data=original.copy()
        data[256,0 if case=='duplicate' else 2]-=1
        path=dest/(case+'.csv');np.savetxt(path,data,fmt='%d',delimiter=',')
        error=''
        try: compare_capture(path,run/'data/layer_01/expected.npz')
        except ValueError as exc: error=str(exc)
        results.append(dict(suite='capture',case=case,passed=bool(error),error=error))
    (dest/'summary.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
    for item in results: print(('PASS' if item['passed'] else 'FAIL')+': '+item['suite']+' '+item['case'])
    return 0 if all(x['passed'] for x in results) else 1


if __name__=='__main__': sys.exit(main())
