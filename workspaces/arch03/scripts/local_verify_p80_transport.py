"""P80 DMA metadata depth 2/4/8 protocol tests; no CPU or physical SRAM claim."""
import argparse
from datetime import datetime
import json
from pathlib import Path
import re
from local_verify import ROOT,A3,run,sha

def main():
    p=argparse.ArgumentParser();p.add_argument('--vivado-bin',type=Path,required=True);a=p.parse_args()
    folder=ROOT/'local_runs'/('p80_transport_'+datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    folder.mkdir(parents=True)
    files=[A3/'rtl/arch03_p80_transport.sv',A3/'tb/tb_arch03_p80_transport.sv',Path(__file__).resolve()]
    before={str(f):sha(f) for f in files};tool=lambda n:a.vivado_bin/(n+'.bat')
    run([tool('xvlog'),'--sv']+files[:-1],folder,'compile.log')
    (folder/'run.tcl').write_text('run all\nquit\n')
    rows=[]
    for depth in (2,4,8):
        name='p80_transport%d'%depth
        run([tool('xelab'),'tb_'+name,'-s',name],folder,name+'_elaborate.log')
        log=run([tool('xsim'),name,'-tclbatch','run.tcl'],folder,name+'_simulation.log')
        matches=re.findall(r'^P80_TRANSPORT_PROTOCOL_PASS depth=%d ([^\r\n]+)'%depth,log,re.M)
        if len(matches)!=1:raise ValueError('Missing P80 DMA depth %d receipt'%depth)
        row={k:int(v) for k,v in re.findall(r'(\w+)=(\d+)',matches[0])};row['depth']=depth
        if row['cases']!=9 or row['peak']!=depth:raise ValueError('P80 coverage incomplete')
        rows.append(row)
    if any(sha(Path(f))!=h for f,h in before.items()):raise ValueError('P80 input changed during test')
    result=dict(status='passed',scope='isolated_ordered_DMA_protocol_only',cpu_executed=False,
        real_platform_tested=False,physical_sram_tested=False,rows=rows,source_sha256=before,
        scenarios=['response-only decoder payload','successful shared write before read',
            'latency 1/2 plus variable waits','data FIFO reservation','four ordered error addresses/types',
            'cancel held read','cancel multiple accepted transactions','reset with pending',
            'no-reset recovery','final write ACK delay','complete drain'])
    (folder/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print('P80_TRANSPORT_LOCAL_PASS',str(folder),flush=True)

if __name__=='__main__':main()
