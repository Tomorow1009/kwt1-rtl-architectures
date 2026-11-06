"""Exercise real export corruption in disposable build-directory copies only."""
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from verify_real_hex import DEFAULT_DATA


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('output',type=Path,help='New empty fixture directory inside the run directory')
    args = p.parse_args()
    args.output.mkdir(parents=True,exist_ok=False)
    data = DEFAULT_DATA
    manifest = json.loads((data/'manifest.json').read_text(encoding='utf-8-sig'))
    first = manifest['layers'][0]['hex_dir']
    tests = [('missing_file','x.hex'),('wrong_count','w.hex'),('wrong_answer','result.hex'),
             ('padding_bits','shift.hex'),('bad_format','manifest.numeric_format.x_fraction')]
    results = []
    for name,expected in tests:
        root = args.output/name
        root.mkdir()
        shutil.copy2(data/'manifest.json',root/'manifest.json')
        # Only layer one is needed: each fixture must fail at that exact layer.
        shutil.copytree((data/first).parent,(root/first).parent)
        folder = root/first
        if name=='missing_file':
            (folder/'x.hex').unlink()
        elif name=='wrong_count':
            q=folder/'w.hex'; q.write_text('\n'.join(q.read_text().splitlines()[:-1])+'\n')
        elif name=='wrong_answer':
            (folder/'result.hex').write_text('0000\n')
        elif name=='padding_bits':
            (folder/'shift.hex').write_text('EC\n')
        else:
            changed=dict(manifest)
            changed['numeric_format']=dict(manifest['numeric_format'],x_fraction=11)
            (root/'manifest.json').write_text(json.dumps(changed))
        proc=subprocess.run([sys.executable,str(Path(__file__).with_name('verify_real_hex.py')),str(root)],
                            stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
        (root/'check.log').write_text(proc.stdout,encoding='utf-8')
        passed=proc.returncode!=0 and 'FAIL:' in proc.stdout and expected in proc.stdout
        if name!='bad_format':
            passed=passed and 'layer 01' in proc.stdout
        results.append(dict(test=name,passed=passed,exit_code=proc.returncode,message=proc.stdout.strip()))
        print(('PASS' if passed else 'FAIL')+': negative test '+name)
    (args.output/'summary.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
    return 0 if all(r['passed'] for r in results) else 1


if __name__=='__main__':
    sys.exit(main())
