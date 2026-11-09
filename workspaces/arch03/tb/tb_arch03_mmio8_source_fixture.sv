`timescale 1ns/1fs
// Original MMIO8/core/arbiter/router/shared SRAM with procedural CPU bus actions.
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

module mmio8_fixture_mems(input wire clk,rst_n,`FIX_SOURCE_PORTS);
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
    arch03_icb_accel u_arch03_accel(.clk(clk),.rst_n(rst_n),`FIX_CONNECT(expl_axi_icb_));
    assign a3_dma_cmd_valid=0;assign a3_dma_cmd_read=1;assign a3_dma_cmd_addr=0;
    assign a3_dma_cmd_wdata=0;assign a3_dma_cmd_wmask=0;assign a3_dma_rsp_ready=0;
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
    integer shift_arg=12,copied=0,sent=0,received=0,sats=0,polls=0,negative_arg=0;
    reg negative_reset_request=0;
    reg [31:0] value,status,word,row,column,group_index,within_group;
    task mmio(input reading,input [11:0] offset,input [31:0] write_value,output [31:0] read_value);
        begin
            @(posedge clk);expl_axi_icb_cmd_valid<=1;expl_axi_icb_cmd_addr<=32'h40000000+offset;
            expl_axi_icb_cmd_read<=reading;expl_axi_icb_cmd_wdata<=write_value;expl_axi_icb_cmd_wmask<=15;
            @(posedge clk);while(!expl_axi_icb_cmd_ready)@(posedge clk);
            @(negedge clk);expl_axi_icb_cmd_valid=0;
            while(!expl_axi_icb_rsp_valid)@(negedge clk);
            if(expl_axi_icb_rsp_err)$fatal(1,"MMIO8 fixture register response error offset=%h",offset);
            read_value=expl_axi_icb_rsp_rdata;
            expl_axi_icb_rsp_ready=1;@(negedge clk);expl_axi_icb_rsp_ready=0;
        end
    endtask
    task memory(input reading,input [31:0] address,input [31:0] write_value,input [3:0] write_mask,output [31:0] read_value);
        begin
            // Model a synchronous CPU-side VALID issue. It becomes visible
            // after edge N; acceptance can first occur at edge N+1.
            @(posedge clk);a3_cpu_cmd_valid<=1;a3_cpu_cmd_addr<=address;a3_cpu_cmd_read<=reading;
            a3_cpu_cmd_wdata<=write_value;a3_cpu_cmd_wmask<=write_mask;
            @(posedge clk);while(!a3_cpu_cmd_ready)@(posedge clk);
            @(negedge clk);a3_cpu_cmd_valid=0;
            while(!a3_cpu_rsp_valid)@(negedge clk);
            if(a3_cpu_rsp_err)$fatal(1,"MMIO8 fixture memory response error address=%h",address);
            read_value=a3_cpu_rsp_rdata;
            a3_cpu_rsp_ready=1;@(negedge clk);a3_cpu_rsp_ready=0;
        end
    endtask
    task mailbox_write(input integer index,input [31:0] write_value);
        reg [31:0] ignored;
        begin memory(0,32'ha001f000+4*index,write_value,15,ignored);end
    endtask
    task observe_idle;
        begin
            mmio(1,12'h008,0,status);
            if((status&31)!==32'b0)$fatal(1,"Negative test did not actually observe idle STATUS");
            $display("MMIO8_CLEAR_NEGATIVE_IDLE_STATUS value=%h",status);
        end
    endtask
    initial begin
        if(!$value$plusargs("SHIFT=%d",shift_arg))shift_arg=12;
        if(!$value$plusargs("NEGATIVE=%d",negative_arg))negative_arg=0;
        wait(rst_n);repeat(2)@(negedge clk);
        mailbox_write(0,0);mailbox_write(8,0);
        if(negative_arg!=0)begin
            $display("MMIO8_CLEAR_NEGATIVE_START case=%0d",negative_arg);
            if(negative_arg==1)begin
                // Idle STATUS without any successful CTRL2 is insufficient.
                observe_idle;mailbox_write(8,32'h4b575442);
            end else if(negative_arg==2)begin
                // A successful clear still requires a fresh idle STATUS.
                mmio(0,12'h004,2,value);mailbox_write(8,32'h4b575442);
            end else if(negative_arg==3)begin
                mmio(0,12'h004,2,value);observe_idle;
                // Invalidate an older certificate as soon as a replacement
                // CTRL2 is accepted; deliberately hold its response unacked.
                @(posedge clk);expl_axi_icb_cmd_valid<=1;expl_axi_icb_cmd_addr<=32'h40000004;
                expl_axi_icb_cmd_read<=0;expl_axi_icb_cmd_wdata<=2;expl_axi_icb_cmd_wmask<=15;
                @(posedge clk);while(!expl_axi_icb_cmd_ready)@(posedge clk);
                @(negedge clk);expl_axi_icb_cmd_valid=0;
                if(!expl_axi_icb_rsp_valid || expl_axi_icb_rsp_ready)$fatal(1,"Negative clear response was not held");
                mailbox_write(8,32'h4b575442);
            end else if(negative_arg==4 || negative_arg==5)begin
                mmio(0,12'h004,2,value);observe_idle;
                if(negative_arg==5)mailbox_write(8,32'h4b575442);
                negative_reset_request=1;wait(!rst_n);wait(rst_n);
                observe_idle;mailbox_write(8,32'h4b575442);
            end else if(negative_arg==6)begin
                mmio(0,12'h004,2,value);observe_idle;
                mmio(0,12'h004,1,value);mailbox_write(8,32'h4b575442);
            end else $fatal(1,"Unknown negative case");
            repeat(5)@(negedge clk);$fatal(1,"MMIO8_NEGATIVE_NOT_REJECTED case=%0d",negative_arg);
        end
        mmio(0,12'h004,2,value);mmio(1,12'h000,0,value);
        if(value!==32'h4b575403)$fatal(1,"Original MMIO8 ID mismatch");
        status=32'hffffffff;
        while((status&31)!=0)mmio(1,12'h008,0,status);
        mailbox_write(8,32'h4b575442);
        for(copied=0;copied<11744;copied=copied+1)begin
            memory(1,32'hb0000000+4*copied,0,15,word);
            memory(0,32'ha0000000+4*copied,word,15,value);
        end
        // Original kwt.c abort/ID/shift/start sequence is retained. This
        // initiator models bus actions only, not E203 instruction execution.
        mmio(0,12'h004,2,value);mmio(1,12'h000,0,value);
        if(value!==32'h4b575403)$fatal(1,"Original driver ID mismatch");
        mmio(0,12'h00c,shift_arg,value);mmio(0,12'h004,1,value);
        status=0;
        while(!((status&8)!=0 && received==25344))begin
            mmio(1,12'h008,0,status);polls=polls+1;
            if(status&16)$fatal(1,"Original MMIO8 core error");
            if((status&2) && sent<23488)begin
                memory(1,32'ha0000000+2*sent,0,15,word);
                word=sent[0] ? {16'b0,word[31:16]} : {16'b0,word[15:0]};
                mmio(0,12'h010,word,value);sent=sent+1;
            end
            if(status&4)begin
                mmio(1,12'h014,0,word);row=(word>>16)&127;column=(word>>23)&255;
                group_index=received/792;within_group=received%792;
                if(received>=25344 || row!=within_group/8 || column!=group_index*8+within_group%8)
                    $fatal(1,"Original MMIO8 coordinate sequence mismatch");
                memory(0,32'ha000c000+2*(row*256+column),
                    column[0] ? {word[15:0],16'b0} : {16'b0,word[15:0]},column[0] ? 4'hc : 4'h3,value);
                sats=sats+word[31];received=received+1;
            end
            if(polls>1000000)$fatal(1,"MMIO8 fixture polling timeout");
        end
        mmio(1,12'h018,0,value);if(value!=sent || sent!=23488)$fatal(1,"MMIO8 input count");
        mmio(1,12'h01c,0,value);if(value!=received || received!=25344)$fatal(1,"MMIO8 output count");
        mailbox_write(1,0);mailbox_write(2,sent);mailbox_write(3,received);
        // No CPU cycles can be reported by this procedural initiator.
        mailbox_write(4,0);mailbox_write(5,0);mailbox_write(6,sats);mailbox_write(7,32'h4b575403);
        mailbox_write(9,copied);mailbox_write(10,32'h00080001);mailbox_write(11,32'hb0000000);
        mailbox_write(12,46976);mailbox_write(13,50688);mailbox_write(14,0);mailbox_write(15,0);
        mailbox_write(16,0);mailbox_write(17,0);mailbox_write(18,0);mailbox_write(19,shift_arg);
        mailbox_write(20,32'h4d385331);
        $display("MMIO8_SOURCE_FIXTURE_READY cpu_executed=false dma_executed=false input_halves=%0d outputs=%0d polls=%0d",sent,received,polls);
        mailbox_write(0,32'h4b575450);
        repeat(20)@(negedge clk);$fatal(1,"MMIO8 production monitor did not finish");
    end

endmodule
module mmio8_fixture_main(input wire clk,rst_n,`FIX_SOURCE_PORTS);
    mmio8_fixture_mems u_e203_subsys_mems(.clk(clk),.rst_n(rst_n),`FIX_SOURCE_CONNECT);
endmodule
module mmio8_fixture_subsys(input wire clk,rst_n,`FIX_SOURCE_PORTS);
    mmio8_fixture_main u_e203_subsys_main(.clk(clk),.rst_n(rst_n),`FIX_SOURCE_CONNECT);
endmodule
module mmio8_fixture_soc(input wire clk,rst_n,`FIX_SOURCE_PORTS);
    mmio8_fixture_subsys u_e203_subsys_top(.clk(clk),.rst_n(rst_n),`FIX_SOURCE_CONNECT);
endmodule
module tb_arch03_mmio8_source_fixture;
    reg clk=0,rst_n=0;always #3.333333 clk=~clk;
    `FIX_WIRES(a3_source_)
    mmio8_fixture_soc u_e203_soc_top(.clk(clk),.rst_n(rst_n),
        .sysmem_icb_cmd_valid(a3_source_cmd_valid),.sysmem_icb_cmd_ready(a3_source_cmd_ready),
        .sysmem_icb_cmd_addr(a3_source_cmd_addr),.sysmem_icb_cmd_read(a3_source_cmd_read),
        .sysmem_icb_cmd_wdata(a3_source_cmd_wdata),.sysmem_icb_cmd_wmask(a3_source_cmd_wmask),
        .sysmem_icb_rsp_valid(a3_source_rsp_valid),.sysmem_icb_rsp_ready(a3_source_rsp_ready),
        .sysmem_icb_rsp_rdata(a3_source_rsp_rdata),.sysmem_icb_rsp_err(a3_source_rsp_err));
    initial begin
        $display("MMIO8_SOURCE_FIXTURE_NO_CPU production_monitor_cpu_flag_must_be_ignored=true");
        repeat(5)@(negedge clk);rst_n=1;
    end
    initial begin
        wait(u_e203_soc_top.u_e203_subsys_top.u_e203_subsys_main.u_e203_subsys_mems.negative_reset_request);
        @(negedge clk);rst_n=0;repeat(2)@(negedge clk);rst_n=1;
    end
    `include "arch03_mmio8_source_monitor.svh"
endmodule
`undef FIX_SOURCE_PORTS
`undef FIX_SOURCE_CONNECT
`undef FIX_WIRES
`undef FIX_CONNECT
