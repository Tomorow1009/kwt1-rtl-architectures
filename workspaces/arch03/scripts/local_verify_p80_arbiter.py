"""P80 ordered arbiter tests at metadata depths 2/4/8; no SoC/PPA claim."""
import argparse
from datetime import datetime
import json
from pathlib import Path
import re
from local_verify import ROOT,A3,run,sha

def main():
    p=argparse.ArgumentParser();p.add_argument('--vivado-bin',type=Path,required=True);a=p.parse_args()
    folder=ROOT/'local_runs'/('p80_arbiter_'+datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    folder.mkdir(parents=True)
    files=[A3/'rtl/arch03_icb_arb2_queued.sv',A3/'rtl/arch03_p80_transport.sv',
           A3/'tb/tb_arch03_p80_arbiter.sv',Path(__file__).resolve()]
    before={str(f):sha(f) for f in files};tool=lambda n:a.vivado_bin/(n+'.bat')
    run([tool('xvlog'),'--sv']+files[:-1],folder,'compile.log')
    (folder/'run.tcl').write_text('run all\nquit\n')
    rows=[]
    for depth in (2,4,8):
        name='p80_arb%d'%depth
        run([tool('xelab'),'tb_'+name,'-s',name],folder,name+'_elaborate.log')
        log=run([tool('xsim'),name,'-tclbatch','run.tcl'],folder,name+'_simulation.log')
        matches=re.findall(r'^P80_ARBITER_PASS depth=%d ([^\r\n]+)'%depth,log,re.M)
        if len(matches)!=1:raise ValueError('Missing P80 arbiter depth %d receipt'%depth)
        row={k:int(v) for k,v in re.findall(r'(\w+)=(\d+)',matches[0])};row['depth']=depth
        if row['accepted']!=row['returned']:raise ValueError('Unreturned command')
        rows.append(row)
    if any(sha(Path(f))!=h for f,h in before.items()):raise ValueError('P80 input changed during test')
    result=dict(status='passed',scope='isolated_ordered_arbiter_only',cpu_executed=False,
        real_platform_tested=False,transport_simulated=False,transport_syntax_compiled=True,
        seed='0x80c32a91',rows=rows,source_sha256=before,
        scenarios=['CPU/DMA accepted-request fairness','held command stability','ordered response ownership',
            'held response stability','error forwarding','full simultaneous pop/push','reset with pending',
            'both masters and queues completely drained'])
    (folder/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print('P80_ARBITER_LOCAL_PASS',str(folder),flush=True)

if __name__=='__main__':main()
