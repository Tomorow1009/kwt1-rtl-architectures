"""Synthetic observer tests, explicitly NOT CPU or arithmetic acceptance."""
import argparse
import json
import subprocess
from datetime import datetime
from pathlib import Path
from local_verify import A3,ROOT,run,sha
from server_run import check_capture


def main():
    p=argparse.ArgumentParser();p.add_argument('--vivado-bin',required=True,type=Path)
    p.add_argument('--data',required=True,type=Path);a=p.parse_args()
    folder=ROOT/'local_runs'/('sequence_observer_'+datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    folder.mkdir(parents=True)
    files=[A3/'tb/arch03_task_window.sv',A3/'tb/tb_arch03_monitor_compile.sv',A3/'tb/tb_arch03_sequence_observer.sv']
    tracked=files+[A3/'tb/arch03_monitor.svh',A3/'tb/arch03_sequence_monitor.svh',Path(__file__).resolve()]
    before={path:sha(path) for path in tracked}
    tool=lambda name:a.vivado_bin/(name+'.bat')
    run([tool('xvlog'),'--sv','-d','ARCH03_MONITOR_SELFTEST','-i',A3/'tb']+files,folder,'compile.log')
    run([tool('xelab'),'tb_arch03_sequence_observer','-debug','typical','-s','sequence_observer'],folder,'elaborate.log')
    (folder/'run.tcl').write_text('run all\nquit\n')
    tests={None:'ARCH03_SEQUENCE_OBSERVER_SELFTEST_PASS tasks=3 outputs=76032 cpu_executed=false',
           'NEGATIVE_MISSING_ABORT':'Poison/abort bus evidence incomplete',
           'NEGATIVE_SKIP_TIMEOUT':'Recovery task began before abort/timeout evidence',
           'NEGATIVE_REPEAT_OUTPUT':'Sequence CPU result mismatch',
           'NEGATIVE_MISSING_REFERENCE':'Missing/unknown'}
    for mode,marker in tests.items():
        name=mode or 'positive';prefix=folder/name
        first=folder/'missing_reference' if mode=='NEGATIVE_MISSING_REFERENCE' else a.data/'layer_01'
        options=['sequence_observer','-tclbatch run.tcl','-testplusarg DATA_DIR='+first.resolve().as_posix(),
                 '-testplusarg SECOND_DIR='+(a.data/'layer_12').resolve().as_posix(),
                 '-testplusarg CAPTURE_PREFIX='+prefix.as_posix()]
        if mode:options+=['-testplusarg '+mode]
        opt=folder/(name+'.options');opt.write_text('\n'.join(options)+'\n',encoding='ascii')
        path=folder/(name+'.log')
        with path.open('w') as out:
            result=subprocess.run([str(tool('xsim')),'-f',str(opt)],cwd=str(folder),stdout=out,stderr=subprocess.STDOUT,timeout=300)
        text=path.read_text(errors='replace')
        if marker not in text or 'cpu_executed=true' in text:raise ValueError('Wrong observer result/scope: '+name)
        if mode and 'ARCH03_SEQUENCE_OBSERVER_SELFTEST_PASS' in text:raise ValueError('Negative observer case passed')
        if not mode:
            if result.returncode or 'Fatal:' in text or 'cannot be opened' in text:raise ValueError('Positive observer test failed')
            for index,case in enumerate(['layer_01','layer_12','layer_01'],1):
                check_capture(folder/(name+'__task%d.csv'%index),a.data/case,2)
    for path,digest in before.items():
        if sha(path)!=digest:raise ValueError('Observer input changed during selftest')
    (folder/'summary.json').write_text(json.dumps(dict(status='passed',cpu_executed=False,
        arithmetic_hardware_present=False,stimulus='precomputed verification vectors drive a synthetic observer-only hierarchy',
        tasks_in_positive_test=3,outputs_checked=76032,negative_tests=4,
        source_sha256={p.relative_to(ROOT).as_posix():v for p,v in before.items()},
        logs={p.name:sha(p) for p in folder.glob('*.log')}),indent=2))
    print('LOCAL_SEQUENCE_OBSERVER_PASS '+str(folder),flush=True)


if __name__=='__main__':main()
