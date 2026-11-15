"""Positive and deliberately faulty stimuli for the original-bus observer."""
import argparse
from datetime import datetime
import json
from pathlib import Path
import re
import subprocess
from local_verify import ROOT,A3,run,sha

def main():
    p=argparse.ArgumentParser();p.add_argument('--vivado-bin',type=Path,required=True);a=p.parse_args()
    folder=ROOT/'local_runs'/('p80_route_'+datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    folder.mkdir(parents=True)
    files=[A3/'tb/arch03_p80_route_observer.sv',A3/'tb/tb_arch03_p80_route.sv',Path(__file__).resolve()]
    before={str(f):sha(f) for f in files};tool=lambda n:a.vivado_bin/(n+'.bat')
    run([tool('xvlog'),'--sv']+files[:-1],folder,'compile.log')
    (folder/'run.tcl').write_text('run all\nquit\n')
    rows=[];negative=[]
    for depth in (2,4,8):
        name='p80_route%d'%depth
        run([tool('xelab'),'tb_'+name,'-s',name],folder,name+'_elaborate.log')
        log=run([tool('xsim'),name,'-tclbatch','run.tcl'],folder,name+'_simulation.log')
        matches=re.findall(r'^P80_ROUTE_PASS depth=%d ([^\r\n]+)'%depth,log,re.M)
        if len(matches)!=1:raise ValueError('Missing queued route receipt')
        row={k:int(v) for k,v in re.findall(r'(\w+)=(\d+)',matches[0])};row['depth']=depth
        rows.append(row)
    messages={1:'root payload mismatch/bypass',2:'O4 reordered/payload mismatch',
        3:'slave payload mismatch',4:'master response data',5:'orphan root response',6:'response wrong master'}
    for fault,message in sorted(messages.items()):
        path=folder/('negative_%d.log'%fault)
        options=folder/('negative_%d.options'%fault)
        options.write_text('p80_route4\n-tclbatch run.tcl\n-testplusarg FAULT=%d\n'%fault)
        with path.open('w') as output:
            proc=subprocess.run([str(tool('xsim')),'-f',str(options)],cwd=str(folder),stdout=output,stderr=subprocess.STDOUT,timeout=120)
        log=path.read_text()
        if not re.search(r'(?m)^Fatal: P80_ROUTE_REJECT '+re.escape(message)+r'\s*$',log) or 'P80_ROUTE_PASS' in log:
            raise ValueError('Missing intended route rejection '+str(path))
        negative.append(dict(fault=fault,reason=message,log_sha256=sha(path),exit_code=proc.returncode))
    if any(sha(Path(f))!=h for f,h in before.items()):raise ValueError('P80 route input changed')
    result=dict(status='passed',scope='passive_route_directed_stimulus_only',cpu_executed=False,
        original_platform_executed=False,rows=rows,negative=negative,source_sha256=before)
    (folder/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print('P80_ROUTE_LOCAL_PASS',str(folder),flush=True)

if __name__=='__main__':main()
