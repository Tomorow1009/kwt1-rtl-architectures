"""Portable local checks and immutable server bundle preparation (Python >=3.8)."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from datetime import datetime
import zipfile
from types import SimpleNamespace

REPO = Path(__file__).resolve().parents[2]
WORK = REPO / 'workspaces/arch02'
DEFAULT_DATA = 'architectures/arch01_serial_mac/v1.3.0/KWT1/model_data/outputs/real_sample_001'

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def save(p, value):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes((json.dumps(value, ensure_ascii=False, indent=2)+'\n').encode('utf-8'))

def git(*args):
    return subprocess.check_output(['git', '-C', str(REPO)]+list(args)).decode('utf-8').strip()

def config(path):
    data = json.loads((REPO/'handoff/team/config.example.json').read_text(encoding='utf-8'))
    if path:
        extra = json.loads(Path(path).read_text(encoding='utf-8-sig'))
        if set(extra)-set(data):
            raise ValueError('Unknown configuration keys: '+str(set(extra)-set(data)))
        data.update(extra)
    if not re.fullmatch(r'[a-zA-Z0-9_-]{1,32}',data['member']):
        raise ValueError('member must be 1-32 ASCII letters/digits/_/-')
    p = Path(data['data_root'])
    data['data_root'] = str((p if p.is_absolute() else REPO/p).resolve())
    return data

def executable(name, folder=''):
    suffix = '.bat' if name in ('xvlog','xelab','xsim') else '.exe'
    p = str(Path(folder)/(name+suffix)) if folder else shutil.which(name)
    if not p or not Path(p).is_file():
        raise FileNotFoundError('Missing tool '+name+'; configure its bin directory')
    return str(Path(p).resolve())

def verify_data(cfg):
    root = Path(cfg['data_root'])
    m = json.loads((root/'manifest.json').read_text(encoding='utf-8-sig'))
    if sorted(x['layer_number'] for x in m['layers']) != list(range(1,13)):
        raise ValueError('Expected layers 1..12')
    files = {str(root/'manifest.json'):sha(root/'manifest.json')}
    for layer in m['layers']:
        folder = (root/layer['hex_dir']).resolve().parent
        folder.relative_to(root)
        for name in ('float_tensors.npz','integer_tensors.npz'):
            p = folder/name
            files[str(p)] = sha(p)
    return files

def load_data_module():
    sys.path.insert(0,str(WORK/'arch02/scripts'))
    import data
    return data

def preflight(cfg, simulator):
    import numpy
    required = ['iverilog','vvp'] if simulator=='iverilog' else ['xvlog','xelab','xsim'] if simulator=='xsim' else ['iverilog','vvp','xvlog','xelab','xsim']
    tools = {name:executable(name,cfg['icarus_bin'] if name in ('iverilog','vvp') else cfg['vivado_bin']) for name in required}
    apps = {}
    for key,name in [('vnc_exe','vncviewer'),('filezilla_exe','filezilla')]:
        p = cfg[key] or shutil.which(name)
        apps[key] = {'path':p,'found':bool(p and Path(p).is_file())}
    return dict(status='local_prerequisites_passed',python=sys.version,numpy=numpy.__version__,commit=git('rev-parse','HEAD'),dirty=git('status','--porcelain'),data=verify_data(cfg),tools=tools,desktop_apps=apps,computer_control=cfg['computer_control'],desktop_ready=False,note='GUI/control/login must be observed in the current Codex session; executable presence is not authentication or control proof.')

def package(cfg, output, allow_dirty):
    dirty = git('status','--porcelain','--','workspaces/arch02','handoff/team')
    if dirty and not allow_dirty:
        raise ValueError('Commit source/tool changes before packaging; --development permits explicitly uncommitted rehearsal only')
    data_hashes=verify_data(cfg)
    commit=git('rev-parse','HEAD')
    name=cfg['member']+'-'+datetime.now().strftime('%Y%m%d_%H%M%S')+'-'+commit[:12]
    folder=output/name
    folder.mkdir(parents=True,exist_ok=False)
    for sub in ['rtl','scripts','arch02/rtl','arch02/tb','arch02/scripts']:
        for p in (WORK/sub).iterdir():
            if p.is_file() and p.suffix in ('.sv','.py','.json','.ps1'):
                q=folder/sub/p.name;q.parent.mkdir(parents=True,exist_ok=True)
                q.write_bytes(p.read_bytes().replace(b'\r\n',b'\n'))
    shutil.copyfile(str(WORK/'arch02/scripts/server_vcs.py'),str(folder/'vcs_run.py'))
    for name2 in ['server.py','server_config.json','synth_stage.py','hold_stage.py','audit_stage.py']:
        shutil.copyfile(str(REPO/'handoff/team'/name2),str(folder/name2))
    subprocess.run([sys.executable,str(folder/'scripts/gen_vectors.py')],check=True,cwd=str(folder))
    report=load_data_module().prepare(Path(cfg['data_root']),folder/'validated_data')
    save(folder/'software_preparation.json',report)
    cfg_server=json.loads((folder/'server_config.json').read_text())
    macro=dict(cen_low=1,gwen_low=1,wen_low=1,ema=2,emaw=0,ret1n=1,read_latency=1,clock_edge='posedge')
    save(folder/'vendor_config.json',dict(kind='vendor_confirmed',evidence='2026-11-08 actual model inspection; server preflight verifies pinned vendor model hashes',macros={'128':macro,'4096':macro}))
    (folder/'vendor.f').write_bytes(('\n'.join(cfg_server['models'][str(n)]['path'] for n in (128,4096))+'\n').encode())
    save(folder/'manifest.json',dict(source_commit=commit,development=bool(dirty),member=cfg['member'],data_hashes=data_hashes,files={p.relative_to(folder).as_posix():sha(p) for p in folder.rglob('*') if p.is_file()}))
    archive=output/(folder.name+'.zip')
    with zipfile.ZipFile(str(archive),'x',zipfile.ZIP_DEFLATED) as z:
        for p in folder.rglob('*'):
            if p.is_file():z.write(str(p),p.relative_to(output).as_posix())
    save(output/(folder.name+'.receipt.json'),dict(bundle=str(archive),sha256=sha(archive),source_commit=commit,development=bool(dirty),outputs=report['tasks']))
    print('BUNDLE_READY',archive,'SHA256',sha(archive),flush=True)

def macro_tests(cfg,output,simulator):
    preflight(cfg,simulator)
    subprocess.run([sys.executable,str(WORK/'scripts/gen_vectors.py')],check=True)
    sys.path.insert(0,str(WORK/'arch02/scripts'))
    import run
    folder=output/('macro_'+datetime.now().strftime('%Y%m%d_%H%M%S'))
    folder.mkdir(parents=True,exist_ok=False)
    summary=dict(status='running',results=[],source_commit=git('rev-parse','HEAD'),sources={str(p.relative_to(REPO)):sha(p) for sub in ('rtl','arch02/rtl','arch02/tb') for p in (WORK/sub).glob('*.sv')})
    try:
        for backend in ('behavioral','pin_mock'):
            args=SimpleNamespace(backend=backend,icarus_bin=cfg['icarus_bin'],vivado_bin=cfg['vivado_bin'])
            run.configure_backend(args)
            for engine in ['iverilog','xsim'] if simulator=='both' else [simulator]:
                work=folder/(backend+'_'+engine);work.mkdir()
                run.build(engine,work,args)
                text=run.simulate(engine,work,'tb_sram_adapter','adapter',[],args)
                if 'PASS: SRAM adapter cases=4' not in text:raise ValueError('Missing macro PASS')
                if backend=='pin_mock':
                    text=run.simulate(engine,work,'tb_pin_mask','pin_mask',[],args)
                    if 'PASS:' not in text:raise ValueError('Missing mask PASS')
                summary['results'].append(dict(backend=backend,simulator=engine,cases=4,passed=True))
                save(folder/'summary.json',summary)
                print('MACRO_PASS',backend,engine,flush=True)
        for rel,digest in summary['sources'].items():
            if sha(REPO/rel)!=digest:raise ValueError('Source changed during macro test')
        summary['status']='passed'
    except Exception as exc:
        summary.update(status='failed',error=str(exc));raise
    finally:save(folder/'summary.json',summary)
    print('LOCAL_MACRO_PASS',folder,flush=True)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=['preflight','software','package','macro'])
    p.add_argument('--config');p.add_argument('--simulator',choices=['both','iverilog','xsim'],default='both')
    p.add_argument('--output',type=Path,default=REPO/'local_runs')
    p.add_argument('--development',action='store_true')
    a=p.parse_args();cfg=config(a.config);a.output=a.output.resolve()
    if a.action=='preflight':
        report=preflight(cfg,a.simulator);save(a.output/'preflight.json',report);print(json.dumps(report,ensure_ascii=False,indent=2))
    elif a.action=='macro':macro_tests(cfg,a.output,a.simulator)
    elif a.action=='software':
        out=a.output/('software_'+datetime.now().strftime('%Y%m%d_%H%M%S'))
        out.mkdir(parents=True,exist_ok=False)
        report=load_data_module().prepare(Path(cfg['data_root']),out/'validated_data')
        save(out/'summary.json',report);print('SOFTWARE_PASS',report['tasks'],out)
    else:package(cfg,a.output,a.development)

if __name__=='__main__':
    try:main()
    except Exception as exc:
        print('FAIL:',exc,file=sys.stderr);sys.exit(1)
