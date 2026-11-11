"""Check the retained scalar MMIO adapter on actual B RTL; no CPU execution."""
import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from local_verify import A2,A3,ROOT,run,sha


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--vivado-bin',required=True,type=Path)
    p.add_argument('--data',required=True,type=Path)
    p.add_argument('--cases',nargs='+',default=['extremes','rounding'])
    a=p.parse_args()
    folder=ROOT/'local_runs'/('systolic_b_debug_'+datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    folder.mkdir()
    files=[A2/'rtl/requantize.sv',A2/'arch02/rtl/sram_port.sv',
        A2/'arch02/rtl/sram_macro_adapter.sv',A2/'arch02/tb/pin_mock.sv']
    files += [A3/'rtl'/n for n in ['arch03_systolic5x16.sv','arch03_linear16x5_systolic.sv',
        'arch03_systolic_b_accel.sv','arch03_icb32_decoder.sv','arch03_systolic_b_decoder.sv','arch03_systolic_b_transport.sv']]
    files += [A3/'tb/tb_arch03_systolic_b_debug.sv']
    cfg_path=A2/'arch02/tb/pin_mock_config.json';cfg=json.loads(cfg_path.read_text())
    lines=[]
    for size in ('128','4096'):
        for key,width in [('cen_low',1),('gwen_low',1),('wen_low',1),('ema',3),('emaw',2),('ret1n',1)]:
            lines.append("`define A02_%s_%s %d'd%d"%(size,key.upper(),width,cfg['macros'][size][key]))
    config=folder/'arch02_sram_config.vh';config.write_text('\n'.join(lines)+'\n')
    hashes={f:sha(f) for f in files+[Path(__file__).resolve(),cfg_path,config]}
    tool=lambda name:a.vivado_bin/(name+'.bat')
    run([tool('xvlog'),'--sv','-d','ARCH02_PIN_MOCK','-i',folder]+files,folder,'compile.log')
    run([tool('xelab'),'tb_arch03_systolic_b_debug','-debug','typical','-s','debug_b'],folder,'elaborate.log')
    (folder/'run.tcl').write_text('run all\nquit\n')
    results=[]
    for name in a.cases:
        task=a.data.resolve()/name;layout=json.loads((task/'layout_manifest.json').read_text())
        for filename,digest in layout['sha256'].items():
            if sha(task/filename)!=digest:raise ValueError('Debug data changed '+filename)
        opts=folder/(name+'.options')
        opts.write_text('debug_b\n-tclbatch run.tcl\n-testplusarg DATA_DIR=%s\n-testplusarg SHIFT=%d\n'%
                       (task.as_posix(),layout['numeric_format']['shift']))
        text=run([tool('xsim'),'-f',opts],folder,name+'.log')
        m=re.findall(r'SYSTOLIC_B_DEBUG_PASS outputs=25344 held_cycles=(\d+) no_dma=true unknown_layout_rejected=true cpu_executed=false',text)
        if len(m)!=1 or int(m[0])<1:raise ValueError('Missing scalar/hold/debug proof')
        results.append(dict(case=name,outputs=25344,held_cycles=int(m[0]),log_sha256=sha(folder/(name+'.log')),
                            layout_sha256=sha(task/'layout_manifest.json')))
        print('PASS B scalar debug '+name,flush=True)
    for f,digest in hashes.items():
        if sha(f)!=digest:raise ValueError('Source changed '+str(f))
    report=dict(status='passed',cpu_executed=False,dma_executed=False,scope='B_scalar_MMIO_pair_adapter',
        cases=results,outputs=len(results)*25344,unknown_layout_rejected=True,
        source_sha256={f.relative_to(ROOT).as_posix():v for f,v in hashes.items()})
    (folder/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
    print('LOCAL_SYSTOLIC_B_DEBUG_PASS '+str(folder),flush=True)


if __name__=='__main__':main()
