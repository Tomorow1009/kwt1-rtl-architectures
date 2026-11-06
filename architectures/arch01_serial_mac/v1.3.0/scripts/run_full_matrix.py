"""Complete-matrix verification, with one compile per simulator and isolated evidence."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from datetime import datetime
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import uuid
from full_matrix_data import ROOT, DEFAULT_DATA, TASKS, prepare, compare_capture, sha


def save(path, value):
    Path(path).write_text(json.dumps(value,indent=2),encoding='utf-8')


def tool(name, directory=''):
    if directory:
        path=Path(directory)/(name+('.bat' if name in ('xvlog','xelab','xsim') else '.exe'))
        if not path.is_file(): raise FileNotFoundError(path)
        return str(path.resolve())
    found=shutil.which(name)
    if not found: raise FileNotFoundError('Tool not found: '+name)
    return found


def execute(argv, cwd, log, timeout=7200):
    with Path(log).open('w',encoding='utf-8') as f:
        result=subprocess.run([str(x) for x in argv],cwd=cwd,stdout=f,stderr=subprocess.STDOUT,timeout=timeout)
    if result.returncode: raise RuntimeError(f'exit={result.returncode}: {log}')


def simulate(engine, build, data, tag, skip, count, wave, args):
    capture=build/(tag+'.csv')
    task_base=TASKS-1 if tag.endswith('_last') else 0
    available=1 if task_base else TASKS
    if task_base: data=data/'last';skip=0
    plus=[f'DATA_DIR={data.as_posix()}',f'TASKS={available}',f'SKIP_TASKS={skip}',
          f'LIMIT_TASKS={count}',f'TASK_BASE={task_base}',f'OUTPUT_FILE={capture.as_posix()}']
    log=build/(tag+'.log')
    if engine=='iverilog':
        execute([tool('vvp',args.icarus_bin),'batch.vvp']+['+'+v for v in plus]+(['+VCD'] if wave else []),build,log)
        if wave: (build/'batch.vcd').rename(build/(tag+'.vcd'))
    else:
        commands=[]
        if wave:
            commands=['log_wave -r /tb_batch_hex/dut/*','log_wave /tb_batch_hex/task_id /tb_batch_hex/actual_count',
                      'add_wave -r /tb_batch_hex/dut/*','add_wave /tb_batch_hex/task_id /tb_batch_hex/actual_count',
                      f'save_wave_config {tag}.wcfg']
        (build/(tag+'.tcl')).write_text('\n'.join(commands+['run all','quit'])+'\n',encoding='ascii')
        (build/(tag+'.options')).write_text('\n'.join([f'-testplusarg "{v}"' for v in plus]+[f'-tclbatch {tag}.tcl',f'-wdb {tag}.wdb'])+'\n',encoding='ascii')
        execute([tool('xsim',args.vivado_bin),'batch_sim','-f',tag+'.options'],build,log)
    matches=re.findall(r'^PASS: batch HEX tasks=(\d+) skip=(\d+) available=(\d+)',log.read_text(errors='replace'),re.M)
    if matches!=[(str(count),str(skip),str(available))]:
        raise ValueError(f'{engine} {tag}: invalid/missing PASS {matches}')
    result=compare_capture(capture,data/'expected.npz',None if wave else build/(tag+'.npz'),skip,count,task_base)
    result.update(simulator=engine,tag=tag,wave=wave,log=str(log),task_base=task_base)
    print(f'PASS {engine} {tag} outputs={count}',flush=True)
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data-root',type=Path,default=DEFAULT_DATA)
    p.add_argument('--mode',choices=['software','all','layer'],default='all')
    p.add_argument('--layer',type=int)
    p.add_argument('--simulator',choices=['both','iverilog','xsim'],default='both')
    p.add_argument('--vivado-bin',default='');p.add_argument('--icarus-bin',default='')
    args=p.parse_args()
    if (args.mode=='layer') != (args.layer is not None) or (args.layer is not None and not 1<=args.layer<=12):
        p.error('--layer 1..12 is required only with --mode layer')
    layers=[args.layer] if args.layer else list(range(1,13))
    run=ROOT/'sim/full_matrix_kwt1'/(datetime.now().strftime('%Y%m%d_%H%M%S')+'_'+uuid.uuid4().hex[:8])
    run.mkdir(parents=True)
    print('Run directory: '+str(run),flush=True)
    sources=['rtl/dot64.sv','rtl/requantize.sv','tb/tb_batch_hex.sv','scripts/full_matrix_data.py',
             'scripts/run_full_matrix.py','scripts/verify_real_hex.py','scripts/run_full_matrix_kwt1.ps1']
    summary=dict(status='running',run=str(run),mode=args.mode,simulator=args.simulator,layers=layers,results=[],
                 sources={name:sha(ROOT/name) for name in sources})
    save(run/'summary.json',summary)
    try:
        software=prepare(args.data_root,layers,None if args.mode=='software' else run/'data')
        save(run/'software.json',software)
        summary['software_tasks']=software['tasks']
        engines=[] if args.mode=='software' else (['iverilog','xsim'] if args.simulator=='both' else [args.simulator])
        lock=Lock()
        def run_engine(engine):
            build=run/engine;build.mkdir()
            rtl=[ROOT/'rtl/requantize.sv',ROOT/'rtl/dot64.sv',ROOT/'tb/tb_batch_hex.sv']
            if engine=='iverilog':
                execute([tool('iverilog',args.icarus_bin),'-g2012','-Wall','-s','tb_batch_hex','-o','batch.vvp']+rtl,build,build/'compile.log')
            else:
                execute([tool('xvlog',args.vivado_bin),'--sv']+rtl,build,build/'compile.log')
                execute([tool('xelab',args.vivado_bin),'tb_batch_hex','-debug','typical','-s','batch_sim'],build,build/'elaborate.log')
            for layer in layers:
                data=run/'data'/f'layer_{layer:02d}'
                for suffix,skip,count,wave in [('full',0,TASKS,False),('first_row_boundary',0,257,True),('last',TASKS-1,1,True)]:
                    tag=f'layer_{layer:02d}_{suffix}'
                    try:
                        result=simulate(engine,build,data,tag,skip,count,wave,args)
                        with lock:
                            summary['results'].append(result)
                            save(run/'summary.json',summary)
                    except Exception as exc:
                        raise RuntimeError(f'{engine} layer={layer:02d} {suffix}: {exc}') from exc
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures=[pool.submit(run_engine,engine) for engine in engines]
            for future in futures: future.result()
        for name,digest in summary['sources'].items():
            if sha(ROOT/name)!=digest: raise ValueError('Source changed during run: '+name)
        summary['status']='passed'
        summary['rtl_unique_tasks_per_simulator']={engine:len(layers)*TASKS for engine in engines}
        print(f'PASS: full matrices software={software["tasks"]} simulators={engines}',flush=True)
        return 0
    except Exception as exc:
        summary.update(status='failed',error=str(exc));print('FAIL: '+str(exc),file=sys.stderr,flush=True);return 1
    finally: save(run/'summary.json',summary)


if __name__=='__main__': sys.exit(main())
