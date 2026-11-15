"""Compile/elaborate production P80 observers against real team modules only.

This fixture supplies hierarchy and port declarations, never E203 execution or
original-fabric functionality. Functional route stimuli have a separate test.
"""
import argparse
from datetime import datetime
import json
from pathlib import Path
from local_verify import A2,A3,ROOT,run,sha
from p80_soc import source_list
from p80_bus_metrics import instrument
from p80_contention import monitor as contention

def main():
    p=argparse.ArgumentParser();p.add_argument('--vivado-bin',type=Path,required=True);a=p.parse_args()
    folder=ROOT/'local_runs'/('p80_monitor_elaborate_'+datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    folder.mkdir(parents=True)
    fixture=A3/'tb/tb_arch03_p80_sequence_fixture.sv'
    text=fixture.read_text()
    prefix=text[:text.index('    integer phase=0')]
    prefix=prefix.replace('    `FIX_WIRES(a3_dma_)','    `FIX_WIRES(mem_icb_)\n    `FIX_WIRES(a3_dma_)')
    suffix=text[text.index('module sequence_fixture_main'):]
    generated=folder/'fixture.sv'
    cfg_path=A2/'arch02/tb/pin_mock_config.json';cfg=json.loads(cfg_path.read_text());lines=[]
    for size in ('128','4096'):
        for key,width in [('cen_low',1),('gwen_low',1),('wen_low',1),('ema',3),('emaw',2),('ret1n',1)]:
            lines.append("`define A02_%s_%s %d'd%d"%(size,key.upper(),width,cfg['macros'][size][key]))
    (folder/'arch02_sram_config.vh').write_text('\n'.join(lines)+'\n')
    files=source_list()+[A2/'arch02/tb/pin_mock.sv']+[A3/'tb'/name for name in
        ('arch03_task_window_p80.sv','arch03_p80_route_observer.sv','arch03_icb32_source.sv','arch03_icb32_sequence_source.sv')]
    tracked=files+[fixture,cfg_path,Path(__file__).resolve(),A3/'scripts/p80_bus_metrics.py',A3/'scripts/p80_contention.py']
    tracked+=list((A3/'tb').glob('arch03_p80_*.svh'))
    before={str(f):sha(f) for f in tracked};tool=lambda n:a.vivado_bin/(n+'.bat')
    for mode in ('positive','contention','sequence'):
        code=(A3/'tb/arch03_p80_sequence_monitor.svh').read_text() if mode=='sequence' else instrument((A3/'tb/arch03_p80_monitor.svh').read_text(),5)
        if mode=='contention':code=contention(code)
        (folder/'generated_monitor.svh').write_text(code)
        generated.write_text(prefix+'endmodule\n'+suffix.replace('arch03_p80_sequence_monitor.svh','generated_monitor.svh'))
        run([tool('xvlog'),'--sv','-d','ARCH02_PIN_MOCK','-i',folder,'-i',A3/'tb']+files+[generated],folder,mode+'_compile.log')
        run([tool('xelab'),'tb_arch03_p80_sequence_fixture','-s','p80_'+mode],folder,mode+'_elaborate.log')
    if any(sha(Path(f))!=h for f,h in before.items()):raise ValueError('Monitor input changed')
    result=dict(status='elaborated_only',modes=['positive','contention','sequence'],
        cpu_executed=False,original_platform_executed=False,simulation_executed=False,source_sha256=before)
    (folder/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print('P80_MONITORS_ELABORATED',str(folder),flush=True)

if __name__=='__main__':main()
