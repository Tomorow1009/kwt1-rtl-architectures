"""Real XSim protocol test for the CPU/DMA arbiter and existing-SysMem router."""
import argparse
import hashlib
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
A3=ROOT/'workspaces/arch03'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--vivado-bin',required=True)
    args=parser.parse_args()
    folder=ROOT/'local_runs'/('arch03_turnover_fabric_'+datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    folder.mkdir(parents=True)
    files=[A3/'rtl/arch03_icb_arb2_turnover.sv',A3/'rtl/arch03_icb_memory_router_turnover.sv',A3/'tb/tb_arch03_icb_turnover_fabric.sv']
    hashes={str(p):sha(p) for p in files+[Path(__file__).resolve()]}
    tool=lambda name:Path(args.vivado_bin)/(name+'.bat')
    def run(argv,log):
        with (folder/log).open('w',encoding='utf8') as output:
            process=subprocess.run([str(a) for a in argv],cwd=str(folder),stdout=output,stderr=subprocess.STDOUT,timeout=1800)
        text=(folder/log).read_text(errors='replace')
        if process.returncode or re.search(r'(?im)^\s*(fatal|error)(:|\s)',text):
            raise RuntimeError('Fabric test failed: '+str(folder/log))
        return text
    run([tool('xvlog'),'--sv']+files,'compile.log')
    run([tool('xelab'),'tb_arch03_icb_turnover_fabric','-debug','typical','-s','fabric'],'elaborate.log')
    (folder/'run.tcl').write_text('run all\nquit\n',encoding='ascii')
    text=run([tool('xsim'),'fabric','-tclbatch','run.tcl'],'simulation.log')
    matches=re.findall(r'^FABRIC_PROTOCOL_PASS (.+)$',text,re.M)
    if len(matches)!=1 or 'FABRIC_STALLED_GRANT_PASS' not in text:
        raise ValueError('Missing fabric acceptance markers')
    if 'FABRIC_TURNOVER_PASS' not in text: raise ValueError('No same-edge turnover proof')
    metrics={key:int(value) for key,value in re.findall(r'(\w+)=(\d+)',matches[0])}
    for path,digest in hashes.items():
        if sha(path)!=digest:
            raise ValueError('Source changed during fabric test: '+path)
    result=dict(status='passed',cpu_executed=False,dma_executed=False,protocol_targets='independent_stubs',
                metrics=metrics,source_sha256={Path(p).relative_to(ROOT).as_posix():h for p,h in hashes.items()},
                log_sha256=sha(folder/'simulation.log'))
    (folder/'summary.json').write_text(json.dumps(result,indent=2),encoding='utf8')
    print('LOCAL_FABRIC_PASS '+str(folder),flush=True)


if __name__=='__main__':
    main()
