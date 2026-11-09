"""Offline port-only monitor/proof tests using real RTL, never mapped gates."""
import argparse
import json
import re
from datetime import datetime
from pathlib import Path
import numpy as np
from local_verify import A2,A3,ROOT,run,sha
from dma16_gate_monitor import generate,DEFAULT_BINDINGS

READ_TASK='''
    reg [31:0] fix_status,fix_count,fix_outputs,fix_sat;
    task mmio_read(input [11:0] offset,output [31:0] value);
        begin
            @(negedge clk);expl_axi_icb_cmd_valid=1;expl_axi_icb_cmd_addr=32'h40000000+offset;
            expl_axi_icb_cmd_read=1;expl_axi_icb_cmd_wmask=15;
            @(posedge clk);while(!expl_axi_icb_cmd_ready)@(posedge clk);
            @(negedge clk);expl_axi_icb_cmd_valid=0;
            while(!expl_axi_icb_rsp_valid)@(negedge clk);
            if(expl_axi_icb_rsp_err)$fatal(1,"Fixture MMIO read rejected");
            value=expl_axi_icb_rsp_rdata;
            expl_axi_icb_rsp_ready=1;@(negedge clk);expl_axi_icb_rsp_ready=0;
        end
    endtask
'''


def fixture(text):
    if text.count('task mailbox_write(')!=1:raise ValueError('Fixture task changed')
    text=text.replace('    task mailbox_write(',READ_TASK+'    task mailbox_write(')
    text=text.replace('`include "arch03_dma16_monitor.svh"','`include "arch03_dma16_gate_monitor.svh"')
    text=text.replace('mailbox_write(0,0);','mailbox_write(0,0);mmio_read(12\'h058,fix_status);mmio_read(12\'h008,fix_status);')
    start=text.index('        wait(u_arch03_accel.done_q);')
    end=text.index('        $display("DMA16_MONITOR_FIXTURE_READY_TO_CHECK',start)
    text=text[:start]+'''        wait(arch03_dma_irq);repeat(3)@(negedge clk);
        mmio_read(12'h008,fix_status);if((fix_status&24)!=8)$fatal(1,"Fixture DMA done/error");
        mmio_read(12'h05c,fix_status);mmio_read(12'h058,fix_status);mmio_read(12'h020,fix_status);
        mmio_read(12'h018,fix_count);mmio_read(12'h01c,fix_outputs);mmio_read(12'h070,fix_sat);
        mailbox_write(1,0);mailbox_write(2,fix_count);mailbox_write(3,fix_outputs);
        mailbox_write(4,0);mailbox_write(5,0);mailbox_write(6,fix_sat);
'''+text[end:]
    if re.search(r'u_arch03_accel\.\w+_q',text):raise ValueError('Fixture still uses DUT register names')
    return text


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--vivado-bin',required=True,type=Path)
    parser.add_argument('--data',required=True,type=Path);args=parser.parse_args()
    folder=ROOT/'local_runs'/('dma16_gate_monitor_offline_'+datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    folder.mkdir(parents=True);task=args.data.resolve()
    production=A3/'tb/arch03_dma16_monitor.svh';original_fixture=A3/'tb/tb_arch03_dma16_monitor_fixture.sv'
    generated=folder/'arch03_dma16_gate_monitor.svh';generated.write_text(generate(production.read_text(),DEFAULT_BINDINGS))
    generated_fixture=folder/'tb_arch03_dma16_gate_monitor_fixture.sv';generated_fixture.write_text(fixture(original_fixture.read_text()))
    if re.search(r'\.\w+_q\b|`A3MEM|`A3DMA',generated.read_text()):raise ValueError('Generated monitor has register/alias dependency')
    for bad in ({},dict(DEFAULT_BINDINGS,core='1\'b0')):
        try:generate(production.read_text(),bad)
        except ValueError:pass
        else:raise ValueError('Bad hierarchy binding was accepted')
    files=[A2/'rtl/requantize.sv',A2/'rtl/dot64.sv',A2/'arch02/rtl/sram_port.sv',
           A2/'arch02/rtl/sram_macro_adapter.sv',A2/'arch02/tb/pin_mock.sv',
           A3/'rtl/arch03_linear16.sv',A3/'rtl/arch03_dma16_accel.sv',
           A3/'rtl/arch03_icb_arb2.sv',A3/'rtl/arch03_icb_memory_router.sv',A3/'rtl/arch03_shared_sram.sv',
           A3/'tb/arch03_task_window16.sv',A3/'tb/arch03_dma16_source.sv',
           A3/'tb/arch03_dma16_gate_proof.sv',A3/'tb/tb_arch03_dma16_gate_proof.sv',generated_fixture]
    cfg_path=A2/'arch02/tb/pin_mock_config.json';cfg=json.loads(cfg_path.read_text());lines=[]
    for size in ('128','4096'):
        for key,width in [('cen_low',1),('gwen_low',1),('wen_low',1),('ema',3),('emaw',2),('ret1n',1)]:
            lines.append("`define A02_%s_%s %d'd%d"%(size,key.upper(),width,cfg['macros'][size][key]))
    config=folder/'arch02_sram_config.vh';config.write_text('\n'.join(lines)+'\n')
    hashes={p:sha(p) for p in files+[cfg_path,config,generated,production,original_fixture,
        A3/'scripts/dma16_gate_monitor.py',Path(__file__).resolve()]}
    layout=json.loads((task/'layout_manifest.json').read_text())
    for name,digest in layout['sha256'].items():
        if sha(task/name)!=digest:raise ValueError('Data changed before test')
    tool=lambda name:args.vivado_bin/(name+'.bat')
    run([tool('xvlog'),'--sv','-d','ARCH02_PIN_MOCK','-i',folder,'-i',A3/'tb']+files,folder,'compile.log')
    run([tool('xelab'),'tb_arch03_dma16_gate_proof','-debug','typical','-s','proof'],folder,'proof_elaborate.log')
    (folder/'run.tcl').write_text('run all\nquit\n')
    log=run([tool('xsim'),'proof','-tclbatch','run.tcl'],folder,'proof.log')
    proof=re.findall(r'^DMA16_GATE_PROOF_SUITE_PASS cases=(\d+)',log,re.M)
    if len(proof)!=1 or int(proof[0])!=14:raise ValueError('Missing 14-case gate-proof acceptance')
    print('PASS gate proof directed cases=14',flush=True)
    run([tool('xelab'),'tb_arch03_dma16_monitor_fixture','-debug','typical','-s','fixture'],folder,'fixture_elaborate.log')
    capture=folder/'layer_01_pf1.csv';options=folder/'fixture.options'
    options.write_text('fixture\n-tclbatch run.tcl\n-testplusarg DATA_DIR=%s\n-testplusarg LOAD32=%s\n-testplusarg CAPTURE=%s\n-testplusarg SHIFT=%d\n-testplusarg PREFETCH=1\n'%(
        task.as_posix(),(task/'load32.hex').as_posix(),capture.as_posix(),layout['numeric_format']['shift']))
    log=run([tool('xsim'),'-f',options],folder,'fixture.log')
    if 'DMA16_MONITOR_FIXTURE_READY_TO_CHECK cpu_executed=false' not in log:raise ValueError('Missing no-CPU scope')
    observed=re.findall(r'^ARCH03_DMA16_BATCH_RESULT (\{.+\})$',log,re.M)
    windows=re.findall(r'^DMA16_TASK_WINDOW (.+)$',log,re.M)
    if len(observed)!=1 or len(windows)!=1:raise ValueError('Missing generated monitor acceptance')
    observed=json.loads(observed[0]);window=dict(x.split('=') for x in windows[0].split())
    if observed['cycles']!=225770 or int(window['finished_cycle'])<=int(window['end_cycle']):
        raise ValueError('Late MMIO proof changed endpoint or did not delay finish')
    actual=np.loadtxt(str(capture),delimiter=',',dtype=np.int64,ndmin=2)
    indexes=actual[:,0]*256+actual[:,1]
    if actual.shape!=(25344,4) or not np.array_equal(np.sort(indexes),np.arange(25344)):raise ValueError('Coordinates incomplete')
    ordered=actual[np.argsort(indexes)]
    with np.load(str(task/'expected.npz'),allow_pickle=False) as expected:
        if not np.array_equal(ordered[:,2],expected['result'].ravel()) or not np.array_equal(ordered[:,3],expected['saturated'].ravel()):
            raise ValueError('Output mismatch')
    for path,digest in hashes.items():
        if sha(path)!=digest:raise ValueError('Source changed during offline gate monitor test: '+str(path))
    for name,digest in layout['sha256'].items():
        if sha(task/name)!=digest:raise ValueError('Data changed during test')
    report=dict(status='passed',scope='offline_port_only_monitor_and_MMIO_proof_on_real_RTL_pin_mock',
                cpu_executed=False,dma_executed=True,gate_simulation_verified=False,
                actual_mapped_hierarchy_probed=False,proof_cases=int(proof[0]),tasks=1,outputs=25344,
                cycles=observed['cycles'],window=window,bindings=DEFAULT_BINDINGS,
                source_sha256={p.relative_to(ROOT).as_posix():h for p,h in hashes.items()})
    (folder/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
    print('LOCAL_DMA16_GATE_MONITOR_OFFLINE_PASS '+str(folder),flush=True)


if __name__=='__main__':main()
