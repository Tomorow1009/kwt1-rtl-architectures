"""Gate observer/proof tests against RTL ports; explicitly not mapped E203."""
import argparse
from datetime import datetime
import json
from pathlib import Path
from local_verify import A2,A3,ROOT,run,sha
from c32_soc import source_list
from c32_gate_monitor import generate
from p80_mapped_aliases import DEFAULT_BINDINGS


def main():
    p=argparse.ArgumentParser();p.add_argument('--vivado-bin',type=Path,required=True);a=p.parse_args()
    folder=ROOT/'local_runs'/('c32_gate_observer_'+datetime.now().strftime('%Y%m%d_%H%M%S_%f'));folder.mkdir(parents=True)
    files=[A3/'tb'/n for n in ('arch03_p80_gate_proof.sv','tb_arch03_p80_gate_proof.sv')]
    tool=lambda n:a.vivado_bin/(n+'.bat')
    run([tool('xvlog'),'--sv']+files,folder,'proof_compile.log')
    (folder/'run.tcl').write_text('run all\nquit\n')
    for depth in (2,):
        snapshot='proof%d'%depth
        opts=folder/(snapshot+'.prj');opts.write_text('tb_arch03_p80_gate_proof\n-generic_top DEPTH=%d\n-s %s\n'%(depth,snapshot))
        run([tool('xelab'),'-f',opts],folder,snapshot+'_elaborate.log')
        log=run([tool('xsim'),snapshot,'-tclbatch',(folder/'run.tcl').as_posix()],folder,snapshot+'.log')
        if log.count('P80_GATE_PROOF_PASS depth=%d'%depth)!=1:raise ValueError('Missing multi-outstanding completion proof')
    fixture=A3/'tb/tb_arch03_c32_sequence_fixture.sv';text=fixture.read_text()
    prefix=text[:text.index('    integer phase=0')];suffix=text[text.index('module sequence_fixture_main'):]
    generated=folder/'fixture.sv'
    generated.write_text(prefix+'endmodule\n'+suffix.replace('arch03_c32_sequence_monitor.svh','generated_monitor.svh'))
    cfg_path=A2/'arch02/tb/pin_mock_config.json';cfg=json.loads(cfg_path.read_text());lines=[]
    for size in ('128','4096'):
        for key,width in [('cen_low',1),('gwen_low',1),('wen_low',1),('ema',3),('emaw',2),('ret1n',1)]:
            lines.append("`define A02_%s_%s %d'd%d"%(size,key.upper(),width,cfg['macros'][size][key]))
    (folder/'arch02_sram_config.vh').write_text('\n'.join(lines)+'\n')
    source=(A3/'tb/arch03_c32_monitor.svh').read_text()
    (folder/'generated_monitor.svh').write_text(generate(source,DEFAULT_BINDINGS,2))
    files+=source_list()+[A2/'arch02/tb/pin_mock.sv']+[A3/'tb'/n for n in
        ('arch03_task_window_p80.sv','arch03_p80_route_observer.sv','arch03_icb32_source.sv','arch03_icb32_sequence_source.sv')]
    tracked=files+[fixture,generated,cfg_path,Path(__file__).resolve(),A3/'scripts/c32_gate_monitor.py',A3/'scripts/p80_mapped_aliases.py',
        A3/'tb/arch03_c32_monitor.svh',A3/'tb/arch03_p80_route_audit.svh',folder/'generated_monitor.svh']
    before={str(f):sha(f) for f in tracked}
    run([tool('xvlog'),'--sv','-d','ARCH02_PIN_MOCK','-i',folder]+list(dict.fromkeys(files))+[generated],folder,'monitor_compile.log')
    run([tool('xelab'),'tb_arch03_c32_sequence_fixture','-s','c32_gate_monitor'],folder,'monitor_elaborate.log')
    if any(sha(Path(f))!=h for f,h in before.items()):raise ValueError('Observer input changed')
    result=dict(status='local_proof_and_elaboration_passed',proof_depths=[2],cpu_executed=False,
        mapped_netlist_tested=False,full_observer_elaborated_only=True,source_sha256=before)
    (folder/'summary.json').write_text(json.dumps(result,indent=2)+'\n');print('C32_GATE_LOCAL_PASS',str(folder),flush=True)


if __name__=='__main__':main()
