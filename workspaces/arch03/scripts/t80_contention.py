"""Real E203 scratch traffic on the original shared arbiter, outside PPA."""
from pathlib import Path
import re
from build_t80_contention import BENCHMARK, SCRATCH
from server_run import ROOT
import t80_soc as soc
from n1_data import require


def monitor(text):
    anchor='reg [4095:0] a3_activity_path'
    require(text.count(anchor)==1 and text.count('                        $finish;')==1, 'Monitor template changed')
    declarations='''integer a3_competing=0,a3_cpu_grants=0,a3_dma_grants=0;
integer a3_scratch_writes=0,a3_scratch_reads=0,a3_fair_wait=0,a3_fair_max=0;
always @(posedge a3_mon_clk) begin
    if(a3_mon_rst_n && a3_window_active)begin
        if(`A3MEM.mem_icb_cmd_valid && `A3MEM.a3_dma_cmd_valid)a3_competing=a3_competing+1;
        if(`A3MEM.mem_icb_cmd_valid && `A3MEM.mem_icb_cmd_ready)begin
            a3_cpu_grants=a3_cpu_grants+1;a3_fair_wait=0;
            if(`A3MEM.mem_icb_cmd_addr>=32'ha0040000 && `A3MEM.mem_icb_cmd_addr<32'ha0040080)begin
                if(`A3MEM.mem_icb_cmd_read)a3_scratch_reads=a3_scratch_reads+1;
                else a3_scratch_writes=a3_scratch_writes+1;
            end
        end else if(!`A3MEM.mem_icb_cmd_valid)a3_fair_wait=0;
        if(`A3MEM.a3_dma_cmd_valid && `A3MEM.a3_dma_cmd_ready)begin
            a3_dma_grants=a3_dma_grants+1;
            if(`A3MEM.mem_icb_cmd_valid)a3_fair_wait=a3_fair_wait+1;
        end
        if(a3_fair_wait>a3_fair_max)a3_fair_max=a3_fair_wait;
        if(a3_fair_wait>8)$fatal(1,"CPU denied more than eight accepted DMA opportunities");
    end
end
'''
    finish='''                        if(a3_competing<=0 || a3_cpu_grants<=0 || a3_dma_grants<=0 ||
                           a3_scratch_writes<=0 || a3_scratch_reads<=0 || a3_mail[28]<1 || a3_mail[30]!=0)
                            $fatal(1,"No real concurrent CPU scratch traffic");
                        $display("T80_CPU_CONTENTION competing=%0d cpu_grants=%0d dma_grants=%0d scratch_writes=%0d scratch_reads=%0d fair_max=%0d rounds=%0d",a3_competing,a3_cpu_grants,a3_dma_grants,a3_scratch_writes,a3_scratch_reads,a3_fair_max,a3_mail[28]);
                        $finish;'''
    return text.replace(anchor,declarations+anchor).replace('                        $finish;',finish)


def verify_firmware(firmware):
    fw,base=soc.verify_firmware(firmware)
    require(fw.get('benchmark')==BENCHMARK and fw.get('scratch')==SCRATCH and
            fw.get('performance_firmware') is False and fw['configuration']['irq_enabled'] is False,
            'Contention needs the dedicated polling image')
    require('workspaces/arch03/sw/main_t80_contention.c' in fw['source_sha256'] and
            'workspaces/arch03/sw/main_t80.c' not in fw['source_sha256'],'Wrong CPU main')
    return fw,base


def verify(cfg,run,platform,cases,call,firmware=None):
    firmware=Path(firmware or ROOT/'firmware_contention').resolve()
    verify_firmware(firmware)
    report=soc.verify(cfg,run,platform,cases,call,(),firmware,False,'contention')
    for row in report['cases']:
        text=(Path(run)/(row['case']+'.log')).read_text()
        matches=re.findall(r'^T80_CPU_CONTENTION competing=(\d+) cpu_grants=(\d+) dma_grants=(\d+) scratch_writes=(\d+) scratch_reads=(\d+) fair_max=(\d+) rounds=(\d+)$',text,re.M)
        require(len(matches)==1,'Missing real CPU contention proof')
        values=list(map(int,matches[0]));require(all(v>0 for v in values[:5]+values[6:]) and values[5]<=8,
            'No competition/service or fairness limit exceeded')
        row['contention']=dict(zip(('competing_cycles','cpu_grants','dma_grants','scratch_writes',
            'scratch_reads','maximum_dma_grants_while_cpu_waits','checked_scratch_rounds'),values))
    report.update(scope='t80_asic_cpu_shared_contention_validation',benchmark=BENCHMARK,
        scratch=SCRATCH,contention_verified=True,performance_measurement=False,
        evidence_limit='Actual E203 scratch traffic with observed concurrent requests; not an IRQ energy measurement')
    return report
