"""XSim checks for first-issued-request through final drained-write timing."""
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
    folder=ROOT/'local_runs'/('arch03_window16_'+datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    folder.mkdir(parents=True)
    files=[A3/'tb/arch03_task_window16.sv',A3/'tb/tb_arch03_task_window16.sv']
    hashes={str(p):sha(p) for p in files+[Path(__file__).resolve()]}
    tool=lambda name:Path(args.vivado_bin)/(name+'.bat')
    def run(argv,log):
        with (folder/log).open('w',encoding='utf8') as output:
            process=subprocess.run([str(a) for a in argv],cwd=str(folder),stdout=output,stderr=subprocess.STDOUT,timeout=1800)
        text=(folder/log).read_text(errors='replace')
        if process.returncode or re.search(r'(?im)^\s*(fatal|error)(:|\s)',text):
            raise RuntimeError('Window16 test failed: '+str(folder/log))
        return text
    run([tool('xvlog'),'--sv']+files,'compile.log')
    run([tool('xelab'),'tb_arch03_task_window16','-debug','typical','-s','window16'],'elaborate.log')
    (folder/'run.tcl').write_text('run all\nquit\n',encoding='ascii')
    text=run([tool('xsim'),'window16','-tclbatch','run.tcl'],'simulation.log')
    matches=re.findall(r'^WINDOW16_SUITE_PASS (.+)$',text,re.M)
    if len(matches)!=1 or 'WINDOW16_POST_DONE_REJECT_PASS' not in text:
        raise ValueError('Missing window16 acceptance marker')
    metrics={key:int(value) for key,value in re.findall(r'(\w+)=(\d+)',matches[0])}
    windows=[]
    for line in re.findall(r'^DMA16_TASK_WINDOW (.+)$',text,re.M):
        fields={key:value for key,value in re.findall(r'(\w+)=([\d.]+)',line)}
        if int(fields['cycles'])!=int(fields['end_cycle'])-int(fields['start_cycle']):
            raise ValueError('Window16 cycle contract')
        if fields['failed']=='0' and sum(int(fields[k]) for k in
                ('source_bytes','input_write_bytes','input_read_bytes','output_bytes'))!=191616:
            raise ValueError('Window16 four-leg byte count')
        windows.append(fields)
    if len(windows)!=metrics['successful_tasks']+metrics['rejected_tasks']:
        raise ValueError('Window16 completion count')
    for path,digest in hashes.items():
        if sha(path)!=digest:
            raise ValueError('Source changed during window16 test: '+path)
    result=dict(status='passed',cpu_executed=False,dma_executed=False,metrics=metrics,windows=windows,
                boundary='first_source_read_valid_event_to_last_related_ack_confirmed_by_later_drain',
                source_sha256={Path(p).relative_to(ROOT).as_posix():h for p,h in hashes.items()},
                log_sha256=sha(folder/'simulation.log'))
    (folder/'summary.json').write_text(json.dumps(result,indent=2),encoding='utf8')
    print('LOCAL_WINDOW16_PASS '+str(folder),flush=True)


if __name__=='__main__':
    main()
