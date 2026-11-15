"""Exercise the queued passive window independently of DUT-generated counters."""
import argparse
from datetime import datetime
import json
from pathlib import Path
import re
from local_verify import ROOT,A3,run,sha

def main():
    p=argparse.ArgumentParser();p.add_argument('--vivado-bin',type=Path,required=True);a=p.parse_args()
    folder=ROOT/'local_runs'/('p80_window_'+datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    folder.mkdir(parents=True)
    files=[A3/'tb/arch03_task_window_p80.sv',A3/'tb/tb_arch03_p80_window.sv',Path(__file__).resolve()]
    before={str(f):sha(f) for f in files};tool=lambda n:a.vivado_bin/(n+'.bat')
    run([tool('xvlog'),'--sv']+files[:-1],folder,'compile.log')
    (folder/'run.tcl').write_text('run all\nquit\n')
    rows=[]
    for depth in (2,4,8):
        name='p80_window%d'%depth
        run([tool('xelab'),'tb_'+name,'-s',name],folder,name+'_elaborate.log')
        log=run([tool('xsim'),name,'-tclbatch','run.tcl'],folder,name+'_simulation.log')
        matches=re.findall(r'^P80_WINDOW_PASS depth=%d ([^\r\n]+)'%depth,log,re.M)
        if len(matches)!=1:raise ValueError('Missing queued window receipt')
        row={k:int(v) for k,v in re.findall(r'(\w+)=(\d+)',matches[0])};row['depth']=depth
        if row['successful']!=5 or row['rejected']!=9:raise ValueError('Window scenario count')
        rows.append(row)
    if any(sha(Path(f))!=h for f,h in before.items()):raise ValueError('P80 window input changed')
    result=dict(status='passed',scope='passive_window_directed_stimulus_only',cpu_executed=False,
        rows=rows,source_sha256=before,boundary='first_source_VALID_to_final_ACK_confirmed_after_drain')
    (folder/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print('P80_WINDOW_LOCAL_PASS',str(folder),flush=True)

if __name__=='__main__':main()
