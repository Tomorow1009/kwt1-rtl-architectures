"""Local ICB regression. This is explicitly NOT an E203 execution acceptance."""
import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
A2=ROOT/'workspaces/arch02'
A3=ROOT/'workspaces/arch03'
sys.path.insert(0,str(A2/'arch02/scripts'))
from data import prepare

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def run(argv,cwd,log):
    with (cwd/log).open('w',encoding='utf8') as out:
        p=subprocess.run([str(x) for x in argv],cwd=str(cwd),stdout=out,stderr=subprocess.STDOUT,timeout=3600)
    text=(cwd/log).read_text(errors='replace')
    if p.returncode or re.search(r'(?im)^\s*(fatal|error)(:|\s)',text):
        raise RuntimeError('Command failed: '+str(cwd/log))
    return text

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--vivado-bin',required=True)
    ap.add_argument('--backend',choices=['behavioral','pin_mock'],default='behavioral')
    ap.add_argument('--cases',nargs='+',default=['layer_01','extremes','rounding'])
    ap.add_argument('--prepared',type=Path)
    ap.add_argument('--next-case',help='Run each selected case, this different case, then abort/poison/recover the first case in one simulation')
    args=ap.parse_args()
    folder=ROOT/'local_runs'/('arch03_'+datetime.now().strftime('%Y%m%d_%H%M%S_%f')+'_'+args.backend)
    folder.mkdir(parents=True)
    data=args.prepared.resolve() if args.prepared else folder/'data'
    if not args.prepared:
        report=prepare(ROOT/'architectures/arch01_serial_mac/v1.3.0/KWT1/model_data/outputs/real_sample_001',data)
        (folder/'software.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    files=[A2/'rtl/requantize.sv',A2/'rtl/dot64.sv',A2/'arch02/rtl/sram_port.sv',
           A2/'arch02/rtl/arch02_linear.sv',A3/'rtl/arch03_icb_accel.sv',
           A3/'rtl/arch03_shared_sram.sv',A3/'tb/tb_arch03_icb.sv']
    define='ARCH02_BEHAVIORAL'
    if args.backend=='behavioral':files.append(A2/'arch02/tb/sram_model.sv')
    else:
        define='ARCH02_PIN_MOCK'
        files += [A2/'arch02/rtl/sram_macro_adapter.sv',A2/'arch02/tb/pin_mock.sv']
        cfg=json.loads((A2/'arch02/tb/pin_mock_config.json').read_text())
        lines=[]
        for size in ('128','4096'):
            for key,width in [('cen_low',1),('gwen_low',1),('wen_low',1),('ema',3),('emaw',2),('ret1n',1)]:
                lines.append("`define A02_%s_%s %d'd%d"%(size,key.upper(),width,cfg['macros'][size][key]))
        (folder/'arch02_sram_config.vh').write_text('\n'.join(lines)+'\n',encoding='ascii')
    tool=lambda n:Path(args.vivado_bin)/(n+'.bat')
    tracked=files+[Path(__file__).resolve()]
    if args.backend=='pin_mock':tracked += [A2/'arch02/tb/pin_mock_config.json',folder/'arch02_sram_config.vh']
    source_hashes={str(p):sha(p) for p in tracked}
    run([tool('xvlog'),'--sv','-d',define,'-i',folder]+files,folder,'compile.log')
    run([tool('xelab'),'tb_arch03_icb','-debug','typical','-s','arch03_icb'],folder,'elaborate.log')
    (folder/'run.tcl').write_text('run all\nquit\n',encoding='ascii')
    results=[]
    for name in args.cases:
        task=data/name
        layout=json.loads((task/'layout.json').read_text())
        # Validate prepared vectors before using them, including reused local preparation.
        for filename,digest in layout['sha256'].items():
            if sha(task/filename)!=digest:raise ValueError('Vector hash mismatch: '+filename)
        capture=folder/(name+'.csv')
        opt=folder/(name+'.options')
        options='arch03_icb\n-tclbatch run.tcl\n-testplusarg DATA_DIR=%s\n-testplusarg CAPTURE=%s\n-testplusarg SHIFT=%d\n'%(
            task.as_posix(),capture.as_posix(),layout['shift'])
        captures=[(name,task,capture)]
        if args.next_case:
            second=data/args.next_case
            second_layout=json.loads((second/'layout.json').read_text())
            for filename,digest in second_layout['sha256'].items():
                if sha(second/filename)!=digest:raise ValueError('Second vector hash mismatch: '+filename)
            second_capture=folder/(name+'__next.csv');recovery=folder/(name+'__recovery.csv')
            options+='-testplusarg SECOND_DIR=%s\n-testplusarg SECOND_SHIFT=%d\n-testplusarg SECOND_CAPTURE=%s\n-testplusarg RECOVERY_CAPTURE=%s\n'%(
                second.as_posix(),second_layout['shift'],second_capture.as_posix(),recovery.as_posix())
            captures += [(args.next_case,second,second_capture),(name,task,recovery)]
        opt.write_text(options,encoding='ascii')
        text=run([tool('xsim'),'-f',opt],folder,name+'.log')
        if 'ARCH03_ICB_PASS outputs=25344' not in text:raise RuntimeError('Missing PASS '+name)
        if args.next_case and 'ARCH03_ICB_SEQUENCE_PASS tasks=3 outputs=76032' not in text:
            raise RuntimeError('Missing consecutive-task acceptance '+name)
        import numpy as np
        for case_name,vector,capture_file in captures:
            actual=np.loadtxt(str(capture_file),delimiter=',',dtype=np.int64,ndmin=2)
            if actual.shape!=(25344,3) or not np.array_equal(np.sort(actual[:,0]),np.arange(25344)):
                raise ValueError('capture coverage')
            actual=actual[np.argsort(actual[:,0])]
            with np.load(str(vector/'expected.npz'),allow_pickle=False) as expected:
                for index,key in [(1,'result'),(2,'saturated')]:
                    if not np.array_equal(actual[:,index],expected[key].ravel()):raise ValueError('capture '+key)
            results.append(dict(case=case_name,outputs=25344,capture=capture_file.name,capture_sha256=sha(capture_file)))
        print('PASS arch03 ICB',args.backend,name,flush=True)
    for path,digest in source_hashes.items():
        if sha(path)!=digest:raise ValueError('Source changed during local RTL run: '+path)
    summary=dict(status='passed',cpu_executed=False,backend=args.backend,cases=results,
                 consecutive_tasks=bool(args.next_case),abort_recovery=bool(args.next_case),
                 source_sha256={Path(p).relative_to(ROOT).as_posix():h for p,h in source_hashes.items()},data_root=str(data))
    (folder/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf8')
    print('LOCAL_ICB_PASS '+str(folder),flush=True)
if __name__=='__main__':main()
