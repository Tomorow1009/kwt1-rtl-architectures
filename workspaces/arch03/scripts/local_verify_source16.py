"""XSim source interface validation with independent binary/halfword packing checks."""
import argparse
import hashlib
import json
import re
import struct
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
    parser.add_argument('--data',required=True,type=Path)
    args=parser.parse_args()
    data=args.data.resolve()
    packet=(data/'load.bin').read_bytes()
    halves=[int(x,16) for x in (data/'load.hex').read_text().split()]
    words=[int(x,16) for x in (data/'load32.hex').read_text().split()]
    if len(packet)!=46976 or packet!=struct.pack('<23488H',*halves) or packet!=struct.pack('<11744I',*words):
        raise ValueError('Source packet halfword/32-bit/little-endian mismatch')
    folder=ROOT/'local_runs'/('arch03_source16_'+datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    folder.mkdir(parents=True)
    files=[A3/'tb/arch03_dma16_source.sv',A3/'tb/tb_arch03_dma16_source.sv']
    hashes={str(p):sha(p) for p in files+[Path(__file__).resolve(),data/'load.bin',data/'load.hex',data/'load32.hex']}
    tool=lambda name:Path(args.vivado_bin)/(name+'.bat')
    def run(argv,log):
        with (folder/log).open('w',encoding='utf8') as output:
            process=subprocess.run([str(a) for a in argv],cwd=str(folder),stdout=output,stderr=subprocess.STDOUT,timeout=1800)
        text=(folder/log).read_text(errors='replace')
        if process.returncode or re.search(r'(?im)^\s*(fatal|error)(:|\s)',text):
            raise RuntimeError('Source16 test failed: '+str(folder/log))
        return text
    run([tool('xvlog'),'--sv']+files,'compile.log')
    run([tool('xelab'),'tb_arch03_dma16_source','-debug','typical','-s','source16'],'elaborate.log')
    (folder/'run.tcl').write_text('run all\nquit\n',encoding='ascii')
    (folder/'test.options').write_text('source16\n-tclbatch run.tcl\n-testplusarg LOAD32=%s\n'%(data/'load32.hex').as_posix(),encoding='ascii')
    text=run([tool('xsim'),'-f','test.options'],'simulation.log')
    matches=re.findall(r'^DMA16_SOURCE_UNIT_PASS (.+)$',text,re.M)
    if len(matches)!=1:
        raise ValueError('Missing source16 acceptance marker')
    for path,digest in hashes.items():
        if sha(path)!=digest:
            raise ValueError('Source changed during source16 test: '+path)
    metrics={k:int(v) for k,v in re.findall(r'(\w+)=(\d+)',matches[0])}
    result=dict(status='passed',cpu_executed=False,dma_executed=False,metrics=metrics,
                source_timing='request accepted at N registers response; earliest ACK at N+1',
                source_sha256={str(Path(p).relative_to(ROOT)):h for p,h in hashes.items()},
                log_sha256=sha(folder/'simulation.log'))
    (folder/'summary.json').write_text(json.dumps(result,indent=2),encoding='utf8')
    print('LOCAL_SOURCE16_PASS '+str(folder),flush=True)


if __name__=='__main__':
    main()
