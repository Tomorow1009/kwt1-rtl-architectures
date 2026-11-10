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

module sequence_fixture_mems(input wire clk,rst_n,`FIX_SOURCE_PORTS);
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
    arch03_icb32_accel u_arch03_accel(.clk(clk),.rst_n(rst_n),`FIX_CONNECT(expl_axi_icb_),
        .dma_cmd_valid(a3_dma_cmd_valid),.dma_cmd_ready(a3_dma_cmd_ready),.dma_cmd_addr(a3_dma_cmd_addr),
        .dma_cmd_read(a3_dma_cmd_read),.dma_cmd_wdata(a3_dma_cmd_wdata),.dma_cmd_wmask(a3_dma_cmd_wmask),
        .dma_rsp_valid(a3_dma_rsp_valid),.dma_rsp_ready(a3_dma_rsp_ready),.dma_rsp_rdata(a3_dma_rsp_rdata),
        .dma_rsp_err(a3_dma_rsp_err),.irq(arch03_dma_irq));
    arch03_icb_arb2_turnover u_arch03_arb(.clk(clk),.rst_n(rst_n),`FIX_CONNECT(a3_bus_),
        .cpu_cmd_valid(a3_cpu_cmd_valid),.cpu_cmd_ready(a3_cpu_cmd_ready),.cpu_cmd_addr(a3_cpu_cmd_addr),
        .cpu_cmd_read(a3_cpu_cmd_read),.cpu_cmd_wdata(a3_cpu_cmd_wdata),.cpu_cmd_wmask(a3_cpu_cmd_wmask),
        .cpu_rsp_valid(a3_cpu_rsp_valid),.cpu_rsp_ready(a3_cpu_rsp_ready),.cpu_rsp_rdata(a3_cpu_rsp_rdata),.cpu_rsp_err(a3_cpu_rsp_err),
        .dma_cmd_valid(a3_dma_cmd_valid),.dma_cmd_ready(a3_dma_cmd_ready),.dma_cmd_addr(a3_dma_cmd_addr),
        .dma_cmd_read(a3_dma_cmd_read),.dma_cmd_wdata(a3_dma_cmd_wdata),.dma_cmd_wmask(a3_dma_cmd_wmask),
        .dma_rsp_valid(a3_dma_rsp_valid),.dma_rsp_ready(a3_dma_rsp_ready),.dma_rsp_rdata(a3_dma_rsp_rdata),
        .dma_rsp_err(a3_dma_rsp_err),.transaction_pending(a3_arb_pending));
    arch03_icb_memory_router_turnover u_arch03_router(.clk(clk),.rst_n(rst_n),`FIX_CONNECT(a3_bus_),
        .mem_cmd_valid(a3_mem_cmd_valid),.mem_cmd_ready(a3_mem_cmd_ready),.mem_cmd_addr(a3_mem_cmd_addr),
        .mem_cmd_read(a3_mem_cmd_read),.mem_cmd_wdata(a3_mem_cmd_wdata),.mem_cmd_wmask(a3_mem_cmd_wmask),
        .mem_rsp_valid(a3_mem_rsp_valid),.mem_rsp_ready(a3_mem_rsp_ready),.mem_rsp_rdata(a3_mem_rsp_rdata),.mem_rsp_err(a3_mem_rsp_err),
        .src_cmd_valid(sysmem_icb_cmd_valid),.src_cmd_ready(sysmem_icb_cmd_ready),.src_cmd_addr(sysmem_icb_cmd_addr),
        .src_cmd_read(sysmem_icb_cmd_read),.src_cmd_wdata(sysmem_icb_cmd_wdata),.src_cmd_wmask(sysmem_icb_cmd_wmask),
        .src_rsp_valid(sysmem_icb_rsp_valid),.src_rsp_ready(sysmem_icb_rsp_ready),.src_rsp_rdata(sysmem_icb_rsp_rdata),
        .src_rsp_err(sysmem_icb_rsp_err),.transaction_pending(a3_router_pending));
    arch03_shared_sram_turnover u_arch03_shared(.clk(clk),.rst_n(rst_n),`FIX_CONNECT(a3_mem_));
    integer phase=0,i,reported_faults=0,short_timeout=8192,negative_arg=0;
    reg [31:0] descriptor_a,descriptor_b,descriptor,fault_epc;
    reg [31:0] value,status,completion,pending,bad_offset,bad_value;
    reg [31:0] records[0:32];
    reg [63:0] ticks=0,begin_tick;
    always @(posedge clk)ticks<=ticks+1;
    task reg_access(input reading,input [11:0] offset,input [31:0] write_value,input expect_error,output [31:0] read_value);
        begin
            @(negedge clk);expl_axi_icb_cmd_valid=1;expl_axi_icb_cmd_addr=32'h40000000+offset;
            expl_axi_icb_cmd_read=reading;expl_axi_icb_cmd_wdata=write_value;expl_axi_icb_cmd_wmask=15;
            @(posedge clk);while(!expl_axi_icb_cmd_ready)@(posedge clk);
            @(negedge clk);expl_axi_icb_cmd_valid=0;
            while(!expl_axi_icb_rsp_valid)@(negedge clk);
            if(expl_axi_icb_rsp_err!==expect_error)$fatal(1,"Sequence fixture unexpected MMIO response offset=%h",offset);
            read_value=expl_axi_icb_rsp_rdata;
            expl_axi_icb_rsp_ready=1;@(negedge clk);expl_axi_icb_rsp_ready=0;
        end
    endtask
    task write_reg(input [11:0] offset,input [31:0] write_value);
        reg [31:0] ignored;
        begin reg_access(0,offset,write_value,0,ignored);end
    endtask
    task read_reg(input [11:0] offset,output [31:0] read_value);
        begin reg_access(1,offset,0,0,read_value);end
    endtask
    task memory_write(input [31:0] address,input [31:0] write_value);
        begin
            @(negedge clk);a3_cpu_cmd_valid=1;a3_cpu_cmd_addr=address;
            a3_cpu_cmd_read=0;a3_cpu_cmd_wdata=write_value;a3_cpu_cmd_wmask=15;
            @(posedge clk);while(!a3_cpu_cmd_ready)@(posedge clk);
            @(negedge clk);a3_cpu_cmd_valid=0;
            while(!a3_cpu_rsp_valid)@(negedge clk);
            if(a3_cpu_rsp_err)$fatal(1,"Sequence fixture memory response error");
            a3_cpu_rsp_ready=1;@(negedge clk);a3_cpu_rsp_ready=0;
        end
    endtask
    task mail(input integer index,input [31:0] write_value);
        begin memory_write(32'ha001f000+4*index,write_value);end
    endtask
    task snapshot;
        begin
            read_reg(12'h018,records[15]);read_reg(12'h01c,records[16]);read_reg(12'h070,records[17]);
            read_reg(12'h008,records[3]);read_reg(12'h05c,records[4]);read_reg(12'h058,records[5]);
            read_reg(12'h020,records[6]);read_reg(12'h048,records[7]);read_reg(12'h04c,records[8]);
            read_reg(12'h050,records[13]);read_reg(12'h054,records[14]);read_reg(12'h060,records[9]);
            read_reg(12'h064,records[10]);read_reg(12'h068,records[11]);read_reg(12'h06c,records[12]);
        end
    endtask
    task cancel_and_drain;
        begin
            write_reg(12'h004,2);
            status=0;completion=0;pending=32'hffffffff;
            while(!(status&32'h4000) || (status&32'h39a1) || (completion&48)!=48 || (pending&32'h3f1f))begin
                read_reg(12'h008,status);read_reg(12'h05c,completion);read_reg(12'h058,pending);
            end
            snapshot;records[20]=1;
        end
    endtask
    task prepare_idle;
        begin
            read_reg(12'h000,value);if(value!==32'h4b574604)$fatal(1,"Sequence DMA ID mismatch");
            write_reg(12'h040,0);cancel_and_drain;write_reg(12'h004,4);
            status=0;pending=32'hffffffff;
            while(!(status&32'h4000) || (status&32'h39b1) || (pending&32'h3f1f))begin
                read_reg(12'h008,status);read_reg(12'h058,pending);
            end
        end
    endtask
    task configure;
        begin
            write_reg(12'h00c,descriptor&31);write_reg(12'h024,3);
            write_reg(12'h028,32'hb0000000);write_reg(12'h02c,32'ha0000000);write_reg(12'h030,32'ha000c000);
            write_reg(12'h034,(descriptor>>17)*4);write_reg(12'h038,50688);write_reg(12'h03c,32'h00100002);
        end
    endtask
    initial begin
        if(!$value$plusargs("FIRST_DESCRIPTOR=%h",descriptor_a) || !$value$plusargs("SECOND_DESCRIPTOR=%h",descriptor_b) ||
           !$value$plusargs("EXPECTED_FAULT_EPC=%h",fault_epc))$fatal(1,"Sequence fixture metadata missing");
        if(!$value$plusargs("SHORT_TIMEOUT=%d",short_timeout))short_timeout=8192;
        if(!$value$plusargs("NEGATIVE=%d",negative_arg))negative_arg=0;
        if(negative_arg)$display("ICB32_SEQUENCE_FIXTURE_NEGATIVE_ARM mode=%0d",negative_arg);
        wait(rst_n);repeat(2)@(negedge clk);
        mail(0,0);mail(32,0);mail(34,0);
        for(phase=1;phase<=10;phase=phase+1)begin
            prepare_idle;
            for(i=0;i<33;i=i+1)records[i]=0;
            descriptor=phase==9 ? descriptor_b : descriptor_a;
            mail(33,descriptor);mail(32,phase);configure;
            bad_offset=0;bad_value=0;begin_tick=ticks;
            if(phase<=5)begin
                case(phase)
                    1:begin bad_offset=32'h28;bad_value=32'hb0000002;end
                    2:begin bad_offset=32'h2c;bad_value=32'ha007f000;end
                    3:begin bad_offset=32'h30;bad_value=32'ha0000000;end
                    4:begin bad_offset=32'h34;bad_value=28;end
                    5:begin bad_offset=32'h38;bad_value=50684;end
                endcase
                write_reg(bad_offset,bad_value);reg_access(0,12'h004,1,1,value);
                reported_faults=reported_faults+1;
                $display("ICB32_SEQUENCE_FIXTURE_REGISTER_REJECTION phase=%0d CPU_trap_not_executed=true",phase);
                cancel_and_drain;
            end else if(phase==6)begin
                write_reg(12'h004,1);records[29]=0;
                while(records[29]<32)begin
                    read_reg(12'h060,records[29]);read_reg(12'h064,records[30]);read_reg(12'h008,records[31]);
                end
                if(negative_arg==1)begin
                    mail(33,descriptor_b);
                    $fatal(1,"SEQUENCE_NEGATIVE_NOT_REJECTED early source selection");
                end
                cancel_and_drain;
            end else begin
                // Mirror the public driver's second CANCEL/CLEAR/configure
                // sequence. A local tick timeout tests hardware drain only;
                // actual C mcycle timeout is NOT executed by this fixture.
                prepare_idle;configure;write_reg(12'h004,1);status=0;
                while(!(status&8) && !(phase==7 && ticks-begin_tick>=short_timeout))begin
                    read_reg(12'h008,status);
                    if(status&16)$fatal(1,"Sequence fixture DMA error");
                end
                if(phase==7)begin cancel_and_drain;records[2]=32'hffffffff;records[32]=32'hffffffff;end
                else snapshot;
            end
            records[0]=phase;records[1]=phase<=5 ? 1 : phase==6 ? 2 : phase==7 ? 3 : 4;
            records[18]=ticks-begin_tick;records[19]=0;records[21]=reported_faults;
            records[22]=7;records[23]=fault_epc;records[24]=32'h40000004;
            records[25]=descriptor;records[26]=bad_offset;records[27]=bad_value;records[28]=short_timeout;
            if(negative_arg==2 && phase==1)records[23]=fault_epc+4;
            for(i=0;i<33;i=i+1)
                if(!(negative_arg==3 && phase==1 && i==32))memory_write(32'ha0020000+(phase-1)*256+i*4,records[i]);
            mail(34,phase);
            if(negative_arg!=0 && phase==1 && negative_arg!=1)$fatal(1,"SEQUENCE_NEGATIVE_NOT_REJECTED receipt corruption");
        end
        mail(1,0);mail(2,10);mail(3,10);mail(4,reported_faults);mail(5,32'h53363431);mail(6,0);
        mail(7,descriptor_a);mail(8,descriptor_b);mail(9,short_timeout);
        $display("ICB32_SEQUENCE_FIXTURE_READY cpu_executed=false actual_CPU_traps_verified=false actual_driver_timeout_verified=false");
        mail(0,32'h53363450);
        repeat(10)@(negedge clk);$fatal(1,"Sequence observer did not accept complete run");
    end

endmodule
module sequence_fixture_main(input wire clk,rst_n,`FIX_SOURCE_PORTS);
    sequence_fixture_mems u_e203_subsys_mems(.clk(clk),.rst_n(rst_n),`FIX_SOURCE_CONNECT);
endmodule
module sequence_fixture_subsys(input wire clk,rst_n,`FIX_SOURCE_PORTS);
    sequence_fixture_main u_e203_subsys_main(.clk(clk),.rst_n(rst_n),`FIX_SOURCE_CONNECT);
endmodule
module sequence_fixture_soc(input wire clk,rst_n,`FIX_SOURCE_PORTS);
    sequence_fixture_subsys u_e203_subsys_top(.clk(clk),.rst_n(rst_n),`FIX_SOURCE_CONNECT);
endmodule
module tb_arch03_icb32_sequence_fixture;
    reg clk=0,rst_n=0;always #3.333333 clk=~clk;
    `FIX_WIRES(a3_source_)
    sequence_fixture_soc u_e203_soc_top(.clk(clk),.rst_n(rst_n),
        .sysmem_icb_cmd_valid(a3_source_cmd_valid),.sysmem_icb_cmd_ready(a3_source_cmd_ready),
        .sysmem_icb_cmd_addr(a3_source_cmd_addr),.sysmem_icb_cmd_read(a3_source_cmd_read),
        .sysmem_icb_cmd_wdata(a3_source_cmd_wdata),.sysmem_icb_cmd_wmask(a3_source_cmd_wmask),
        .sysmem_icb_rsp_valid(a3_source_rsp_valid),.sysmem_icb_rsp_ready(a3_source_rsp_ready),
        .sysmem_icb_rsp_rdata(a3_source_rsp_rdata),.sysmem_icb_rsp_err(a3_source_rsp_err));
    initial begin
        $display("ICB32_SEQUENCE_FIXTURE_NO_CPU emulated_trap_receipts=true instruction_timing_modeled=false");
        repeat(5)@(negedge clk);rst_n=1;
    end
    `include "arch03_icb32_sequence_monitor.svh"
endmodule
`undef FIX_SOURCE_PORTS
`undef FIX_SOURCE_CONNECT
`undef FIX_WIRES
`undef FIX_CONNECT
