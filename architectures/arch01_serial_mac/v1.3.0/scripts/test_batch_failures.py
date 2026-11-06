"""Negative tests use fresh copies under the selected run directory only."""
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
from verify_batch_hex import DEFAULT_DATA, FILES


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run',type=Path)
    parser.add_argument('--data-root',type=Path,default=DEFAULT_DATA)
    args=parser.parse_args(); run=args.run.resolve(); source=args.data_root.resolve()
    dest=run/'negative_tests'; dest.mkdir(exist_ok=False)
    original=json.loads((source/'manifest.json').read_text())
    first=original['shards'][0]['path']; results=[]
    for case,expected in [('missing','bias.hex'),('truncated','x.hex'),('answer','integer oracle'),
                          ('invalid','invalid/X/Z'),('padding','padding'),('range','task/sample'),('hash','SHA256 mismatch')]:
        root=dest/('software_'+case); root.mkdir()
        for name in ('samples.csv','shared_parameters.npz'): shutil.copy2(source/name,root/name)
        shutil.copytree(source/first,root/first)
        m=json.loads(json.dumps(original)); folder=root/first
        changed=None
        if case=='missing': (folder/'bias.hex').unlink()
        elif case=='truncated':
            changed='x.hex'; data=(folder/changed).read_bytes(); (folder/changed).write_bytes(data[:-5])
        elif case in ('answer','hash'):
            changed='result.hex'; data=(folder/changed).read_text().splitlines(); data[0]=f'{int(data[0],16)^1:04X}'; (folder/changed).write_bytes(('\n'.join(data)+'\n').encode())
        elif case=='invalid':
            changed='x.hex'; data=(folder/changed).read_bytes(); (folder/changed).write_bytes(b'XXXX\n'+data[5:])
        elif case=='padding':
            changed='shift.hex'; data=(folder/changed).read_bytes(); (folder/changed).write_bytes(b'EC\n'+data[3:])
        else: m['shards'][0]['tasks']-=1
        if changed and case!='hash': m['shards'][0]['sha256'][changed]=hashlib.sha256((folder/changed).read_bytes()).hexdigest()
        (root/'manifest.json').write_text(json.dumps(m))
        proc=subprocess.run([sys.executable,str(Path(__file__).with_name('verify_batch_hex.py')),str(root)],capture_output=True,text=True)
        output=proc.stdout+proc.stderr; (root/'check.log').write_text(output,encoding='utf-8')
        ok=proc.returncode!=0 and 'FAIL:' in output and expected in output and 'shard=training/shard_0000' in output
        results.append(dict(suite='software',case=case,passed=ok,exit_code=proc.returncode,expected=expected,log=str(root/'check.log')))
        print(('PASS' if ok else 'FAIL')+': software '+case,flush=True)
    # Direct TB tests bypass software preflight to exercise loader/scoreboard.
    vvp=shutil.which('vvp'); snapshot=run/'iverilog/batch.vvp'
    if not vvp or not snapshot.exists(): raise RuntimeError('Run staged Icarus validation first')
    for case,expected in [('valid','PASS: batch HEX tasks=1'),('missing','Cannot open'),('truncated','Missing'),
                          ('answer','Mismatch'),('invalid','Invalid/X/Z'),('padding','Padding'),
                          ('width','Invalid width'),('range','Invalid task range'),('trailing','Unexpected trailing')]:
        folder=dest/('rtl_'+case); folder.mkdir()
        for name,(_,per,_) in FILES.items():
            with (source/first/(name+'.hex')).open() as f: values=[next(f).strip() for _ in range(per)]
            (folder/(name+'.hex')).write_text('\n'.join(values)+'\n',encoding='ascii')
        if case=='missing': (folder/'w.hex').unlink()
        elif case=='truncated': (folder/'x.hex').write_text('0000\n')
        elif case=='answer':
            p=folder/'result.hex'; p.write_text(f'{int(p.read_text(),16)^1:04X}\n')
        elif case=='invalid':
            p=folder/'x.hex'; p.write_text('XXXX\n'+'\n'.join(p.read_text().splitlines()[1:])+'\n')
        elif case=='padding': (folder/'shift.hex').write_text('EC\n')
        elif case=='width': (folder/'shift.hex').write_text('00C\n')
        elif case=='trailing':
            with (folder/'result.hex').open('a') as f: f.write('garbage\n')
        proc=subprocess.run([vvp,str(snapshot),'+DATA_DIR='+folder.as_posix(),'+TASKS=1',
                             '+SKIP_TASKS='+('1' if case=='range' else '0')],cwd=folder,capture_output=True,text=True,timeout=30)
        output=proc.stdout+proc.stderr; (folder/'check.log').write_text(output,encoding='utf-8')
        ok=expected in output and ((proc.returncode==0) if case=='valid' else (proc.returncode!=0 and 'PASS: batch HEX' not in output))
        results.append(dict(suite='iverilog',case=case,passed=ok,exit_code=proc.returncode,expected=expected,log=str(folder/'check.log')))
        print(('PASS' if ok else 'FAIL')+': Icarus '+case,flush=True)
    (dest/'summary.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
    return 0 if all(x['passed'] for x in results) else 1


if __name__=='__main__': sys.exit(main())
