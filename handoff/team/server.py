"""Server stage driver; Python 3.6 standard library, immutable bundle inputs."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
from datetime import datetime

ROOT=Path(__file__).resolve().parent
STAGES=['preflight','software','unit','vcs','synth','hold','audit']

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):
    temp=p.with_suffix('.tmp')
    temp.write_text(json.dumps(x,indent=2),encoding='utf-8')
    os.replace(str(temp),str(p))

def alive(pid):
    try:os.kill(int(pid),0);return True
    except ProcessLookupError:return False
    except PermissionError:return True
    except (ValueError,TypeError):return False

def inputs():
    m=json.loads((ROOT/'manifest.json').read_text())
    for rel,digest in m['files'].items():
        p=(ROOT/rel).resolve();p.relative_to(ROOT)
        if sha(p)!=digest:raise ValueError('Bundle hash mismatch '+rel)
    return m

def preflight(cfg):
    layers=sorted(p.name for p in (ROOT/'validated_data').glob('layer_*') if p.is_dir())
    if layers!=['layer_%02d'%n for n in range(1,13)]:raise ValueError('Expected exactly 12 data layers')
    for name,p in cfg['tools'].items():
        if not Path(p).is_file() or not os.access(p,os.X_OK):raise ValueError('Missing executable '+name+': '+p)
    if not Path(cfg['process_archive']).is_file():raise ValueError('Missing process archive')
    for size,m in cfg['models'].items():
        if sha(Path(m['path']))!=m['sha256']:raise ValueError('Vendor model changed '+size)
        if 'ARM_UD_MODEL' not in Path(m['path']).read_text(errors='replace'):raise ValueError('Missing functional branch '+size)
        lib=Path(cfg['sram_root'])/('RAMSP%sX16/lib/RAMSP%sX16_ss_0p99v_0p99v_125c.lib'%(size,size))
        if not lib.is_file():raise ValueError('Missing macro corner '+str(lib))
    return {'status':'passed','note':'Paths/hashes only; licenses exercised by subsequent tools','python':sys.version}

def run_stage(stage,session,state,cfg):
    if stage in state['stages']:raise ValueError('Stage already recorded; inspect it, use a new session for retry')
    index=STAGES.index(stage)
    if index and state['stages'].get(STAGES[index-1],{}).get('status')!='passed':
        raise ValueError('Required preceding stage not passed: '+STAGES[index-1])
    inputs()
    record={'status':'running','started':datetime.now().isoformat(),'pid':os.getpid()}
    state['stages'][stage]=record;save(session/'state.json',state)
    env=os.environ.copy()
    env['PATH']=os.pathsep.join(str(Path(p).parent) for p in cfg['tools'].values())+os.pathsep+env.get('PATH','')
    for field,key in [('vcs','HANDOFF_VCS_RUN'),('synth','HANDOFF_SYNTH_RUN'),('hold','HANDOFF_HOLD_RUN')]:
        if field in state['stages'] and 'run' in state['stages'][field]:env[key]=state['stages'][field]['run']
    try:
        if stage=='preflight':record.update(preflight(cfg))
        else:
            if stage in ('software','unit','vcs'):
                mode={'software':'check-data','unit':'unit','vcs':'all'}[stage]
                cmd=[sys.executable,str(ROOT/'vcs_run.py'),'--root',str(ROOT),'--mode',mode,'--config',str(ROOT/'vendor_config.json'),'--filelist',str(ROOT/'vendor.f'),'--vendor-mode','functional']
                marker='RUN '
            else:
                cmd=[sys.executable,str(ROOT/(stage+'_stage.py'))]
                marker={'synth':'SYNTH_RUN ','hold':'HOLD_RUN ','audit':'FINAL_AUDIT_PASS '}[stage]
            log=session/(stage+'.log')
            record['command']=cmd;record['log']=str(log)
            with log.open('w') as f:
                p=subprocess.Popen(cmd,cwd=str(ROOT),env=env,stdout=f,stderr=subprocess.STDOUT)
                record['child_pid']=p.pid;save(session/'state.json',state)
                rc=p.wait()
            record['exit_code']=rc
            text=log.read_text(errors='replace')
            if rc:raise ValueError('Stage failed; inspect '+str(log))
            found=[line[len(marker):].strip() for line in text.splitlines() if line.startswith(marker)]
            if len(found)!=1:raise ValueError('Missing/ambiguous run marker '+stage)
            output=Path(found[0]).resolve();output.relative_to(ROOT)
            record['run']=str(output)
            if stage in ('software','unit','vcs','audit'):
                result=json.loads((output/'summary.json').read_text())
                if result['status']!='passed':raise ValueError('Summary not passed')
                if stage=='software' and result.get('software_real_outputs')!=304128:raise ValueError('Software count')
                if stage=='vcs':
                    if result.get('real_outputs')!=304128 or result.get('vendor_model_mode')!='functional':raise ValueError('VCS coverage')
                    if not result['jobs'] or not all(j['passed'] for j in result['jobs']):raise ValueError('Failed VCS job')
                if stage=='audit' and result.get('integer_and_capture_rechecked')!=304128:raise ValueError('Audit coverage')
                record['summary_sha256']=sha(output/'summary.json')
            elif stage=='synth':
                if 'SYNTHESIS_REPORTS_READY' not in text:raise ValueError('No synthesis completion')
            else:
                if 'HOLD_REPORTS_READY' not in text:raise ValueError('No hold completion')
                summary=(output/'summary.txt').read_text()
                slacks={k:float(re.search(k+r' slack=([^ ]+)',summary).group(1)) for k in ('max','min')}
                if min(slacks.values())<0:raise ValueError('Negative slack '+str(slacks))
                record['slack_ns']=slacks
            record['status']='passed'
        inputs()
    except BaseException as exc:
        record.update(status='failed',error=str(exc));raise
    finally:
        record['finished']=datetime.now().isoformat();save(session/'state.json',state)
    print('STAGE_PASS',stage,record.get('run',''),flush=True)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('stage',choices=['status','all']+STAGES)
    p.add_argument('--session',required=True)
    a=p.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,80}',a.session):raise ValueError('Invalid session name')
    cfg=json.loads((ROOT/'server_config.json').read_text())
    session=ROOT/'team_sessions'/a.session
    lock=Path(cfg['server_root'])/'.arch02_team_lock'
    if a.stage=='status':
        print((session/'state.json').read_text() if (session/'state.json').exists() else 'SESSION_NOT_CREATED')
        if lock.exists():
            owner=json.loads((lock/'owner.json').read_text()) if (lock/'owner.json').exists() else {'incomplete_lock':True}
            owner['pid_alive_on_this_host']=alive(owner.get('pid')) if owner.get('host')==socket.gethostname() else 'unknown_host'
            print('LOCK',json.dumps(owner))
        if (session/'state.json').exists():
            state=json.loads((session/'state.json').read_text())
            for name,item in state['stages'].items():
                if item.get('status') in ('running','failed') and item.get('child_pid'):
                    print('CHILD_PROCESS',name,item['child_pid'],'alive='+str(alive(item['child_pid'])))
        else:print('LOCK_FREE')
        return
    inputs()
    try:lock.mkdir()
    except FileExistsError:raise ValueError('Team lock exists. Use status; do not remove/restart without checking actual process.')
    try:
        save(lock/'owner.json',dict(pid=os.getpid(),host=socket.gethostname(),bundle=str(ROOT),session=a.session,started=datetime.now().isoformat()))
        session.mkdir(parents=True,exist_ok=True)
        for folder in ('dc_runs','audits'): (ROOT/folder).mkdir(exist_ok=True)
        state=json.loads((session/'state.json').read_text()) if (session/'state.json').exists() else dict(bundle=str(ROOT),manifest_sha256=sha(ROOT/'manifest.json'),stages={})
        if state['manifest_sha256']!=sha(ROOT/'manifest.json'):raise ValueError('Session manifest changed')
        for stage in STAGES if a.stage=='all' else [a.stage]:run_stage(stage,session,state,cfg)
        if a.stage=='all':print('TEAM_FLOW_PASS outputs=304128 physical_signoff=false',flush=True)
    finally:
        # Only remove the lock created by this process. Crash leftovers require human inspection.
        if (lock/'owner.json').exists():
            owner=json.loads((lock/'owner.json').read_text())
            active_child=any(item.get('status') in ('running','failed') and item.get('child_pid') and alive(item['child_pid']) for item in locals().get('state',{}).get('stages',{}).values())
            if not active_child and owner.get('pid')==os.getpid() and owner.get('host')==socket.gethostname():
                (lock/'owner.json').unlink();lock.rmdir()

if __name__=='__main__':
    try:main()
    except Exception as exc:print('FAIL:',exc,file=sys.stderr);sys.exit(1)
