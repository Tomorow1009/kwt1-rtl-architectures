"""Exercise timing observer with delayed command/response handshakes and errors."""
import argparse
import json
import subprocess
from datetime import datetime
from pathlib import Path
from local_verify import A3, ROOT, run, sha


def main():
    p=argparse.ArgumentParser();p.add_argument('--vivado-bin',required=True,type=Path)
    a=p.parse_args()
    folder=ROOT/'local_runs'/('window_'+datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    folder.mkdir(parents=True)
    files=[A3/'tb/arch03_task_window.sv',A3/'tb/tb_arch03_window.sv',A3/'tb/tb_arch03_window_repeat.sv']
    bindings=[A3/'tb/tb_arch03_monitor_compile.sv',A3/'tb/arch03_monitor.svh',A3/'tb/arch03_sequence_monitor.svh']
    before={path:sha(path) for path in files+bindings+[Path(__file__).resolve()]}
    tool=lambda name:a.vivado_bin/(name+'.bat')
    run([tool('xvlog'),'--sv']+files,folder,'compile.log')
    run([tool('xelab'),'tb_arch03_window','-debug','typical','-s','window'],folder,'elaborate.log')
    (folder/'run.tcl').write_text('run all\nquit\n')
    log=run([tool('xsim'),'window','-tclbatch','run.tcl'],folder,'positive.log')
    if 'ARCH03_WINDOW_PASS final_response_checked=true waits_checked=true' not in log:
        raise ValueError('Window positive test failed')
    negative={
        'NEGATIVE_BEFORE_BEGIN':'Data command preceded BEGIN response',
        'NEGATIVE_RESPONSE_ERROR':'Shared-memory response error during monitored run'
    }
    for option,message in negative.items():
        path=folder/(option+'.log')
        with path.open('w') as out:
            result=subprocess.run([str(tool('xsim')),'window','-tclbatch','run.tcl','-testplusarg',option],
                                  cwd=str(folder),stdout=out,stderr=subprocess.STDOUT,timeout=180)
        text=path.read_text(errors='replace')
        if message not in text or 'ARCH03_WINDOW_PASS' in text:
            raise ValueError('Negative timing test did not fail as intended: '+option)
    run([tool('xelab'),'tb_arch03_window_repeat','-debug','typical','-s','repeat_window'],folder,'repeat_elaborate.log')
    text=run([tool('xsim'),'repeat_window','-tclbatch','run.tcl'],folder,'repeat_positive.log')
    if 'ARCH03_REPEAT_WINDOW_PASS tasks=3 reset_between_tasks=false' not in text:
        raise ValueError('Repeated timing-window test failed')
    path=folder/'repeat_negative.log'
    with path.open('w') as out:
        subprocess.run([str(tool('xsim')),'repeat_window','-tclbatch','run.tcl','-testplusarg','NEGATIVE_ACTIVE_BEGIN'],
                       cwd=str(folder),stdout=out,stderr=subprocess.STDOUT,timeout=180)
    text=path.read_text(errors='replace')
    if 'Duplicate or late BEGIN marker' not in text or 'ARCH03_REPEAT_WINDOW_PASS' in text:
        raise ValueError('Duplicate BEGIN was not rejected in repeat mode')
    # Elaboration of the actual include catches path/width/module/VCD-task errors.
    # Never simulate this hierarchy substitute or label it an E203 execution.
    run([tool('xvlog'),'--sv','-i',A3/'tb',bindings[0]],folder,'monitor_compile.log')
    run([tool('xelab'),'tb_top','-debug','typical','-s','monitor_compile_only'],folder,'monitor_elaborate.log')
    run([tool('xelab'),'tb_sequence_compile','-debug','typical','-s','sequence_compile_only'],folder,'sequence_monitor_elaborate.log')
    for path,digest in before.items():
        if sha(path)!=digest:raise ValueError('Timing observer changed during test')
    (folder/'summary.json').write_text(json.dumps(dict(status='passed',cpu_executed=False,
        tests=3+len(negative),negative_rejections=negative,repeat_tasks=3,repeat_active_begin_rejected=True,
        monitor_include_elaborated=True,sequence_monitor_elaborated=True,
        source_sha256={p.relative_to(ROOT).as_posix():h for p,h in before.items()},
        log_sha256={p.name:sha(p) for p in folder.glob('*.log')}),indent=2))
    print('LOCAL_WINDOW_PASS '+str(folder),flush=True)


if __name__=='__main__':main()
