`timescale 1ns/1fs
// Real DMA/core/arbiter/router/shared SRAM with a procedural MMIO/mailbox
// initiator. The production observer is included unchanged, but NO E203 is
// instantiated. Its hardcoded cpu_executed=true line is NOT CPU evidence here.
`define FIX_SOURCE_PORTS \
    output wire sysmem_icb_cmd_valid,input wire sysmem_icb_cmd_ready, \
    output wire [31:0] sysmem_icb_cmd_addr,output wire sysmem_icb_cmd_read, \
    output wire [31:0] sysmem_icb_cmd_wdata,output wire [3:0] sysmem_icb_cmd_wmask, \
    input wire sysmem_icb_rsp_valid,output wire sysmem_icb_rsp_ready, \
    input wire [31:0] sysmem_icb_rsp_rdata,input wire sysmem_icb_rsp_err
`define FIX_SOURCE_CONNECT \
    .sysmem_icb_cmd_valid(sysmem_icb_cmd_valid),.sysmem_icb_cmd_ready(sysmem_icb_cmd_ready), \
    .sysmem_icb_cmd_addr(sysmem_icb_cmd_addr),.sysmem_icb_cmd_read(sysmem_icb_cmd_read), \
    .sysmem_icb_cmd_wdata(sysmem_icb_cmd_wdata),.sysmem_icb_cmd_wmask(sysmem_icb_cmd_wmask), \
    .sysmem_icb_rsp_valid(sysmem_icb_rsp_valid),.sysmem_icb_rsp_ready(sysmem_icb_rsp_ready), \
    .sysmem_icb_rsp_rdata(sysmem_icb_rsp_rdata),.sysmem_icb_rsp_err(sysmem_icb_rsp_err)
`define FIX_WIRES(P) \
    wire P``cmd_valid,P``cmd_ready,P``cmd_read,P``rsp_valid,P``rsp_ready,P``rsp_err; \
    wire [31:0] P``cmd_addr,P``cmd_wdata,P``rsp_rdata;wire [3:0] P``cmd_wmask;
`define FIX_CONNECT(P) \
    .cmd_valid(P``cmd_valid),.cmd_ready(P``cmd_ready),.cmd_addr(P``cmd_addr), \
    .cmd_read(P``cmd_read),.cmd_wdata(P``cmd_wdata),.cmd_wmask(P``cmd_wmask), \
    .rsp_valid(P``rsp_valid),.rsp_ready(P``rsp_ready),.rsp_rdata(P``rsp_rdata),.rsp_err(P``rsp_err)

module dma16_fixture_mems(input wire clk,rst_n,`FIX_SOURCE_PORTS);
    reg expl_axi_icb_cmd_valid=0,expl_axi_icb_cmd_read=0,expl_axi_icb_rsp_ready=0;
    reg [31:0] expl_axi_icb_cmd_addr=0,expl_axi_icb_cmd_wdata=0;
    reg [3:0] expl_axi_icb_cmd_wmask=15;
    wire expl_axi_icb_cmd_ready,expl_axi_icb_rsp_valid,expl_axi_icb_rsp_err;
    wire [31:0] expl_axi_icb_rsp_rdata;
    reg a3_cpu_cmd_valid=0,a3_cpu_cmd_read=0,a3_cpu_rsp_ready=0;
    reg [31:0] a3_cpu_cmd_addr=0,a3_cpu_cmd_wdata=0;
    reg [3:0] a3_cpu_cmd_wmask=15;
    wire a3_cpu_cmd_ready,a3_cpu_rsp_valid,a3_cpu_rsp_err;
    wire [31:0] a3_cpu_rsp_rdata;
    `FIX_WIRES(a3_dma_)
    `FIX_WIRES(a3_bus_)
    `FIX_WIRES(a3_mem_)
    wire a3_arb_pending,a3_router_pending,arch03_dma_irq;
    arch03_dma16_accel u_arch03_accel(.clk(clk),.rst_n(rst_n),`FIX_CONNECT(expl_axi_icb_),
        .dma_cmd_valid(a3_dma_cmd_valid),.dma_cmd_ready(a3_dma_cmd_ready),.dma_cmd_addr(a3_dma_cmd_addr),
        .dma_cmd_read(a3_dma_cmd_read),.dma_cmd_wdata(a3_dma_cmd_wdata),.dma_cmd_wmask(a3_dma_cmd_wmask),
        .dma_rsp_valid(a3_dma_rsp_valid),.dma_rsp_ready(a3_dma_rsp_ready),.dma_rsp_rdata(a3_dma_rsp_rdata),
        .dma_rsp_err(a3_dma_rsp_err),.irq(arch03_dma_irq));
    arch03_icb_arb2 u_arch03_arb(.clk(clk),.rst_n(rst_n),`FIX_CONNECT(a3_bus_),
        .cpu_cmd_valid(a3_cpu_cmd_valid),.cpu_cmd_ready(a3_cpu_cmd_ready),.cpu_cmd_addr(a3_cpu_cmd_addr),
        .cpu_cmd_read(a3_cpu_cmd_read),.cpu_cmd_wdata(a3_cpu_cmd_wdata),.cpu_cmd_wmask(a3_cpu_cmd_wmask),
        .cpu_rsp_valid(a3_cpu_rsp_valid),.cpu_rsp_ready(a3_cpu_rsp_ready),.cpu_rsp_rdata(a3_cpu_rsp_rdata),.cpu_rsp_err(a3_cpu_rsp_err),
        .dma_cmd_valid(a3_dma_cmd_valid),.dma_cmd_ready(a3_dma_cmd_ready),.dma_cmd_addr(a3_dma_cmd_addr),
        .dma_cmd_read(a3_dma_cmd_read),.dma_cmd_wdata(a3_dma_cmd_wdata),.dma_cmd_wmask(a3_dma_cmd_wmask),
        .dma_rsp_valid(a3_dma_rsp_valid),.dma_rsp_ready(a3_dma_rsp_ready),.dma_rsp_rdata(a3_dma_rsp_rdata),
        .dma_rsp_err(a3_dma_rsp_err),.transaction_pending(a3_arb_pending));
    arch03_icb_memory_router u_arch03_router(.clk(clk),.rst_n(rst_n),`FIX_CONNECT(a3_bus_),
        .mem_cmd_valid(a3_mem_cmd_valid),.mem_cmd_ready(a3_mem_cmd_ready),.mem_cmd_addr(a3_mem_cmd_addr),
        .mem_cmd_read(a3_mem_cmd_read),.mem_cmd_wdata(a3_mem_cmd_wdata),.mem_cmd_wmask(a3_mem_cmd_wmask),
        .mem_rsp_valid(a3_mem_rsp_valid),.mem_rsp_ready(a3_mem_rsp_ready),.mem_rsp_rdata(a3_mem_rsp_rdata),.mem_rsp_err(a3_mem_rsp_err),
        .src_cmd_valid(sysmem_icb_cmd_valid),.src_cmd_ready(sysmem_icb_cmd_ready),.src_cmd_addr(sysmem_icb_cmd_addr),
        .src_cmd_read(sysmem_icb_cmd_read),.src_cmd_wdata(sysmem_icb_cmd_wdata),.src_cmd_wmask(sysmem_icb_cmd_wmask),
        .src_rsp_valid(sysmem_icb_rsp_valid),.src_rsp_ready(sysmem_icb_rsp_ready),.src_rsp_rdata(sysmem_icb_rsp_rdata),
        .src_rsp_err(sysmem_icb_rsp_err),.transaction_pending(a3_router_pending));
    arch03_shared_sram u_arch03_shared(.clk(clk),.rst_n(rst_n),`FIX_CONNECT(a3_mem_));
    integer shift_arg=12,prefetch_arg=1;
    task mmio_write(input [11:0] offset,input [31:0] value);
        begin
            @(negedge clk);expl_axi_icb_cmd_valid=1;expl_axi_icb_cmd_addr=32'h40000000+offset;
            expl_axi_icb_cmd_read=0;expl_axi_icb_cmd_wdata=value;expl_axi_icb_cmd_wmask=15;
            @(posedge clk);while(!expl_axi_icb_cmd_ready)@(posedge clk);
            @(negedge clk);expl_axi_icb_cmd_valid=0;
            while(!expl_axi_icb_rsp_valid)@(negedge clk);
            if(expl_axi_icb_rsp_err)$fatal(1,"Fixture MMIO write rejected");
            expl_axi_icb_rsp_ready=1;@(negedge clk);expl_axi_icb_rsp_ready=0;
        end
    endtask
    task mailbox_write(input integer index,input [31:0] value);
        begin
            @(negedge clk);a3_cpu_cmd_valid=1;a3_cpu_cmd_addr=32'ha001f000+index*4;
            a3_cpu_cmd_read=0;a3_cpu_cmd_wdata=value;a3_cpu_cmd_wmask=15;
            @(posedge clk);while(!a3_cpu_cmd_ready)@(posedge clk);
            @(negedge clk);a3_cpu_cmd_valid=0;
            while(!a3_cpu_rsp_valid)@(negedge clk);
            if(a3_cpu_rsp_err)$fatal(1,"Fixture mailbox write rejected");
            a3_cpu_rsp_ready=1;@(negedge clk);a3_cpu_rsp_ready=0;
        end
    endtask
    initial begin
        if(!$value$plusargs("SHIFT=%d",shift_arg))shift_arg=12;
        if(!$value$plusargs("PREFETCH=%d",prefetch_arg))prefetch_arg=1;
        wait(rst_n);repeat(2)@(negedge clk);
        mailbox_write(0,0);
        mmio_write(12'h00c,shift_arg);mmio_write(12'h024,prefetch_arg ? 3 : 1);
        mmio_write(12'h040,7);mmio_write(12'h004,1);
        wait(u_arch03_accel.done_q);repeat(3)@(negedge clk);
        if(u_arch03_accel.error_q || !arch03_dma_irq)$fatal(1,"Fixture DMA completion error");
        mailbox_write(1,0);mailbox_write(2,u_arch03_accel.load_count_q);
        mailbox_write(3,u_arch03_accel.output_count_q);
        // These are explicitly fixture placeholders, not executed CPU cycles.
        mailbox_write(4,0);mailbox_write(5,0);mailbox_write(6,u_arch03_accel.saturated_count_q);
        $display("DMA16_MONITOR_FIXTURE_READY_TO_CHECK cpu_executed=false dma_executed=true");
        mailbox_write(0,32'h4b575450);
        repeat(20)@(negedge clk);$fatal(1,"Production monitor did not accept complete fixture outputs");
    end
endmodule
module dma16_fixture_main(input wire clk,rst_n,`FIX_SOURCE_PORTS);
    dma16_fixture_mems u_e203_subsys_mems(.clk(clk),.rst_n(rst_n),`FIX_SOURCE_CONNECT);
endmodule
module dma16_fixture_subsys(input wire clk,rst_n,`FIX_SOURCE_PORTS);
    dma16_fixture_main u_e203_subsys_main(.clk(clk),.rst_n(rst_n),`FIX_SOURCE_CONNECT);
endmodule
module dma16_fixture_soc(input wire clk,rst_n,`FIX_SOURCE_PORTS);
    dma16_fixture_subsys u_e203_subsys_top(.clk(clk),.rst_n(rst_n),`FIX_SOURCE_CONNECT);
endmodule
module tb_arch03_dma16_monitor_fixture;
    reg clk=0,rst_n=0;always #3.333333 clk=~clk;
    `FIX_WIRES(a3_source_)
    dma16_fixture_soc u_e203_soc_top(.clk(clk),.rst_n(rst_n),
        .sysmem_icb_cmd_valid(a3_source_cmd_valid),.sysmem_icb_cmd_ready(a3_source_cmd_ready),
        .sysmem_icb_cmd_addr(a3_source_cmd_addr),.sysmem_icb_cmd_read(a3_source_cmd_read),
        .sysmem_icb_cmd_wdata(a3_source_cmd_wdata),.sysmem_icb_cmd_wmask(a3_source_cmd_wmask),
        .sysmem_icb_rsp_valid(a3_source_rsp_valid),.sysmem_icb_rsp_ready(a3_source_rsp_ready),
        .sysmem_icb_rsp_rdata(a3_source_rsp_rdata),.sysmem_icb_rsp_err(a3_source_rsp_err));
    initial begin
        $display("DMA16_MONITOR_FIXTURE_NO_CPU production_monitor_cpu_flag_must_be_ignored=true");
        repeat(5)@(negedge clk);rst_n=1;
    end
    `include "arch03_dma16_monitor.svh"
endmodule
`undef FIX_SOURCE_PORTS
`undef FIX_SOURCE_CONNECT
`undef FIX_WIRES
`undef FIX_CONNECT
