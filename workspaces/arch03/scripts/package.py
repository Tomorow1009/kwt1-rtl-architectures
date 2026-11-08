"""Package committed source, independently hashed data and compiled firmware.

The official E203 platform and licensed technology libraries stay on the server;
the installer verifies the pinned complete platform source fingerprint first.
"""
import argparse,datetime,hashlib,json,shutil,subprocess,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*args):
    return subprocess.check_output(['git','-c','safe.directory='+ROOT.as_posix()]+list(args),cwd=str(ROOT)).decode().strip()
def main():
    p=argparse.ArgumentParser();p.add_argument('--data',required=True,type=Path)
    p.add_argument('--firmware',required=True,type=Path);p.add_argument('--member',required=True)
    a=p.parse_args()
    import re
    if not re.fullmatch('[A-Za-z0-9_-]{1,60}',a.member):raise ValueError('Member identifier')
    if git('status','--porcelain'):raise ValueError('Commit source first; working tree is not clean')
    commit=git('rev-parse','HEAD')
    name=a.member+'-arch03-'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')+'-'+commit[:12]
    folder=ROOT/'local_runs'/name;folder.mkdir()
    prefixes=('workspaces/arch02/','workspaces/arch03/','architectures/arch01_serial_mac/v1.3.0/KWT1/model_data/outputs/real_sample_001/')
    include=['handoff/team/server_config.json','handoff/team/unpack.py']
    for rel in git('ls-files').splitlines():
        if rel.startswith(prefixes) or rel in include:
            target=folder/rel;target.parent.mkdir(parents=True,exist_ok=True)
            # Use committed bytes, independent of checkout line-ending conversion.
            raw=subprocess.check_output(['git','-c','safe.directory='+ROOT.as_posix(),'show',commit+':'+rel],cwd=str(ROOT))
            target.write_bytes(raw)
    fw=json.loads((a.firmware/'manifest.json').read_text())
    if fw.get('run_mode','single_cpu_v2') not in ('single_cpu_v2','sequence_cpu_v1'):
        raise ValueError('Unsupported firmware run mode')
    for rel,digest in fw['source_sha256'].items():
        if sha(folder/'workspaces/arch03/sw'/rel)!=digest:raise ValueError('Firmware/committed source mismatch')
    if sha(a.firmware/'driver.elf')!=fw['elf_sha256']:raise ValueError('ELF changed')
    for case,meta in fw['images'].items():
        if sha(a.firmware/(case+'.verilog'))!=meta['sha256']:raise ValueError('Firmware image changed')
        if sha(a.data/case/'load.hex')!=meta['input_sha256']:raise ValueError('Firmware/input mismatch')
        layout=json.loads((a.data/case/'layout.json').read_text())
        if layout['shift']!=meta['shift']:raise ValueError('Firmware shift mismatch')
        if fw.get('run_mode')=='sequence_cpu_v1':
            next_case=meta['next_case']
            if Path(next_case).name!=next_case or next_case in ('.','..'):raise ValueError('Invalid next case')
            if meta['tasks']!=[case,next_case,case]:raise ValueError('Sequence task order mismatch')
            secondary=json.loads((a.data/next_case/'layout.json').read_text())
            if sha(a.data/next_case/'load.hex')!=meta['next_input_sha256'] or secondary['shift']!=meta['next_shift']:
                raise ValueError('Sequence secondary input/shift changed')
            for rel,digest in secondary['sha256'].items():
                if sha(a.data/next_case/rel)!=digest:raise ValueError('Secondary data changed '+next_case+'/'+rel)
        for rel,digest in layout['sha256'].items():
            if sha(a.data/case/rel)!=digest:raise ValueError('Data changed '+case+'/'+rel)
    shutil.copytree(str(a.data),str(folder/'validated_data'))
    shutil.copytree(str(a.firmware),str(folder/'firmware'))
    fw.pop('command',None) # Local absolute paths are not part of the portable manifest.
    (folder/'firmware/manifest.json').write_text(json.dumps(fw,indent=2),encoding='utf8')
    files={q.relative_to(folder).as_posix():sha(q) for q in sorted(folder.rglob('*')) if q.is_file()}
    manifest=dict(source_commit=commit,member=a.member,files=files,architecture='arch03',
                  platform_dependency='pinned external official source; installer checks complete RTL digest',
                  cpu_execution_verified=False,official_precision_verified=False)
    (folder/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
    archive=folder.with_suffix('.zip')
    with zipfile.ZipFile(str(archive),'w',zipfile.ZIP_DEFLATED) as z:
        for q in sorted(folder.rglob('*')):
            if q.is_file():z.write(str(q),name+'/'+q.relative_to(folder).as_posix())
    receipt=dict(source_commit=commit,archive=archive.name,bytes=archive.stat().st_size,sha256=sha(archive),files=len(files))
    (folder.parent/(name+'.receipt.json')).write_text(json.dumps(receipt,indent=2),encoding='utf8')
    print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
