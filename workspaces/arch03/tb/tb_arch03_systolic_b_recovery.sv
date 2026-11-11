`timescale 1ns/1fs
// Actual DMA16 + actual linear16 + actual shared-SRAM RTL. The source is a
// handshake-respecting test device holding offline packet bytes, not answers.
// Uses the actual new arbiter/router; the CPU input is idle, not an E203 model.
module tb_arch03_systolic_b_recovery;
    reg clk=0,rst_n=0,cmd_valid=0,cmd_read=0,rsp_ready=0;
    reg [31:0] cmd_addr=0,cmd_wdata=0;
    reg [3:0] cmd_wmask=0;
    wire cmd_ready,rsp_valid,rsp_err;
    wire [31:0] rsp_rdata;
    wire dma_cmd_valid,dma_cmd_ready,dma_cmd_read,dma_rsp_valid,dma_rsp_ready,dma_rsp_err,irq;
    wire [31:0] dma_cmd_addr,dma_cmd_wdata,dma_rsp_rdata;
    wire [3:0] dma_cmd_wmask;
    wire shared_ready,shared_rsp_valid,shared_rsp_err;
    wire [31:0] shared_rsp_data;
    wire bus_cmd_valid,bus_cmd_ready,bus_cmd_read,bus_rsp_valid,bus_rsp_ready,bus_rsp_err;
    wire [31:0] bus_cmd_addr,bus_cmd_wdata,bus_rsp_rdata;
    wire [3:0] bus_cmd_wmask;
    wire mem_cmd_valid,mem_cmd_ready,mem_cmd_read,mem_rsp_ready;
    wire [31:0] mem_cmd_addr,mem_cmd_wdata;
    wire [3:0] mem_cmd_wmask;
    wire src_cmd_valid,src_cmd_ready,src_cmd_read,src_rsp_ready;
    wire [31:0] src_cmd_addr,src_cmd_wdata;
    wire [3:0] src_cmd_wmask;
    wire arb_pending,router_pending;
    reg source_pending=0,source_rsp_valid=0;
    reg [31:0] source_data=0;
    integer source_delay=0,tick=0,jitter=1,prefetch=1,shift_arg=12,last_delay=0;
    reg hold_source_probe=0;
    wire command_gate=!hold_source_probe && (!jitter || tick%5!=0);
    wire response_gate=(!jitter || tick%7!=0) && last_delay==0;
    assign src_cmd_ready=command_gate && !source_pending;
    assign mem_cmd_ready=command_gate && shared_ready;
    integer inject_kind=0;
    reg injected=0;
    arch03_systolic_b_accel dut(.*);
    arch03_icb_arb2_turnover arb(
        .clk(clk),.rst_n(rst_n),.cpu_cmd_valid(1'b0),.cpu_cmd_ready(),.cpu_cmd_addr(32'b0),
        .cpu_cmd_read(1'b1),.cpu_cmd_wdata(32'b0),.cpu_cmd_wmask(4'b0),
        .cpu_rsp_valid(),.cpu_rsp_ready(1'b1),.cpu_rsp_rdata(),.cpu_rsp_err(),
        .dma_cmd_valid(dma_cmd_valid),.dma_cmd_ready(dma_cmd_ready),.dma_cmd_addr(dma_cmd_addr),
        .dma_cmd_read(dma_cmd_read),.dma_cmd_wdata(dma_cmd_wdata),.dma_cmd_wmask(dma_cmd_wmask),
        .dma_rsp_valid(dma_rsp_valid),.dma_rsp_ready(dma_rsp_ready),.dma_rsp_rdata(dma_rsp_rdata),.dma_rsp_err(dma_rsp_err),
        .cmd_valid(bus_cmd_valid),.cmd_ready(bus_cmd_ready),.cmd_addr(bus_cmd_addr),.cmd_read(bus_cmd_read),
        .cmd_wdata(bus_cmd_wdata),.cmd_wmask(bus_cmd_wmask),.rsp_valid(bus_rsp_valid),.rsp_ready(bus_rsp_ready),
        .rsp_rdata(bus_rsp_rdata),.rsp_err(bus_rsp_err),.transaction_pending(arb_pending));
    arch03_icb_memory_router_turnover router(
        .clk(clk),.rst_n(rst_n),.cmd_valid(bus_cmd_valid),.cmd_ready(bus_cmd_ready),.cmd_addr(bus_cmd_addr),
        .cmd_read(bus_cmd_read),.cmd_wdata(bus_cmd_wdata),.cmd_wmask(bus_cmd_wmask),
        .rsp_valid(bus_rsp_valid),.rsp_ready(bus_rsp_ready),.rsp_rdata(bus_rsp_rdata),.rsp_err(bus_rsp_err),
        .mem_cmd_valid(mem_cmd_valid),.mem_cmd_ready(mem_cmd_ready),.mem_cmd_addr(mem_cmd_addr),
        .mem_cmd_read(mem_cmd_read),.mem_cmd_wdata(mem_cmd_wdata),.mem_cmd_wmask(mem_cmd_wmask),
        .mem_rsp_valid(shared_rsp_valid && response_gate),.mem_rsp_ready(mem_rsp_ready),
        .mem_rsp_rdata(shared_rsp_data),.mem_rsp_err(shared_rsp_err || (inject_kind==dut.transport.pending_kind && inject_kind!=0 && !injected)),
        .src_cmd_valid(src_cmd_valid),.src_cmd_ready(src_cmd_ready),.src_cmd_addr(src_cmd_addr),
        .src_cmd_read(src_cmd_read),.src_cmd_wdata(src_cmd_wdata),.src_cmd_wmask(src_cmd_wmask),
        .src_rsp_valid(source_rsp_valid && response_gate),.src_rsp_ready(src_rsp_ready),
        .src_rsp_rdata(source_data),.src_rsp_err(inject_kind==1 && !injected),.transaction_pending(router_pending));
    arch03_shared_sram_turnover shared(
        .clk(clk),.rst_n(rst_n),.cmd_valid(mem_cmd_valid && command_gate),
        .cmd_ready(shared_ready),.cmd_addr(mem_cmd_addr),.cmd_read(mem_cmd_read),
        .cmd_wdata(mem_cmd_wdata),.cmd_wmask(mem_cmd_wmask),.rsp_valid(shared_rsp_valid),
        .rsp_ready(mem_rsp_ready && response_gate),.rsp_rdata(shared_rsp_data),.rsp_err(shared_rsp_err));

    reg [31:0] encoded[0:11751];
    reg [15:0] packet[0:23487],expected[0:25343];
    reg expected_sat[0:25343];
    reg expect_mmio_error=0,checking=0,held=0;
    reg [68:0] held_payload;
    integer encoded_bytes,encoded_words,i,probe,acks=0,consumed=0,outputs=0,idx=0,watchdog=0;
    reg [31:0] magic;
    string data_dir,encoded_file;
    reg [8191:0] filename;
    always #3.333333 clk=~clk;
    always @(posedge clk or negedge rst_n)begin
        if(!rst_n)begin tick<=0;source_pending<=0;source_rsp_valid<=0;source_delay<=0;last_delay<=0;end
        else begin
            tick<=tick+1;
            if(src_cmd_valid && src_cmd_ready)begin
                source_pending<=1;source_delay<=tick%4;
                source_data<=encoded[(src_cmd_addr-32'hb0000000)/4];
            end
            if(source_pending && !source_rsp_valid)begin
                if(source_delay!=0)source_delay<=source_delay-1;
                else source_rsp_valid<=1;
            end
            if(source_rsp_valid && src_rsp_ready && response_gate)begin source_pending<=0;source_rsp_valid<=0;end
        end
    end
    always @(posedge clk)if(rst_n)begin
        if(held && (!dma_cmd_valid || {dma_cmd_read,dma_cmd_addr,dma_cmd_wdata,dma_cmd_wmask}!==held_payload))
            $fatal(1,"Recovery changed a held command");
        held=dma_cmd_valid && !dma_cmd_ready;
        held_payload={dma_cmd_read,dma_cmd_addr,dma_cmd_wdata,dma_cmd_wmask};
        if(dma_rsp_valid && dma_rsp_ready && dma_rsp_err)injected<=1;
        if(dut.committed_valid && dut.committed_ready)begin
            if(dut.decoded_words>=dut.stage_acks_q || dut.committed_data!==encoded[dut.decoded_words])
                $fatal(1,"Error recovery leaked uncommitted data");
        end
        if(checking && dut.output_fire)begin
            idx=dut.core_row*256+dut.core_col;
            if(dut.core_row>98 || dut.core_result!=={expected[idx+1],expected[idx]} || dut.core_sat!=={expected_sat[idx+1],expected_sat[idx]})
                $fatal(1,"Recovery run result mismatch");
            outputs=outputs+2;
        end
        if(dut.done_q && (dut.tr_pending || dma_cmd_valid || arb_pending || router_pending))
            $fatal(1,"Recovery premature DONE");
        if(tick>5000000)$fatal(1,"Recovery global timeout");
    end
    task write_reg(input [11:0] offset,input [31:0] data);
        begin
            @(negedge clk);cmd_valid=1;cmd_read=0;cmd_addr=32'h40000000+offset;cmd_wdata=data;cmd_wmask=15;
            @(posedge clk);while(!cmd_ready)@(posedge clk);
            @(negedge clk);cmd_valid=0;while(!rsp_valid)@(negedge clk);
            if(rsp_err!==expect_mmio_error)$fatal(1,"MMIO error expectation offset=%h",offset);
            rsp_ready=1;@(negedge clk);rsp_ready=0;
        end
    endtask

    task await_idle;
        begin
            watchdog=0;
            while(dut.active || dut.tr_busy || dma_cmd_valid || arb_pending || router_pending || dut.core_cancel_q || !dut.core_start_ready)begin
                @(negedge clk);watchdog=watchdog+1;
                if(watchdog>300000)$fatal(1,"Recovery failed to drain");
            end
        end
    endtask
    task clear_fault;
        begin
            inject_kind=0;injected=0;
            write_reg(12'h004,4);repeat(4)@(negedge clk);
            if(dut.error_q || dut.core_error || dut.decoder_error)$fatal(1,"Recovery clear failed");
        end
    endtask
    initial begin
        if(!$value$plusargs("DATA_DIR=%s",data_dir))$fatal(1,"DATA_DIR");
        if(!$value$plusargs("ENCODED_FILE=%s",encoded_file))$fatal(1,"ENCODED_FILE");
        if(!$value$plusargs("ENCODED_BYTES=%d",encoded_bytes))$fatal(1,"ENCODED_BYTES");
        if(!$value$plusargs("SHIFT=%d",shift_arg))shift_arg=12;
        encoded_words=encoded_bytes/4;$readmemh(encoded_file,encoded,0,encoded_words-1);magic=encoded[0];
        $sformat(filename,"%s/load.hex",data_dir);$readmemh(filename,packet);
        $sformat(filename,"%s/result.hex",data_dir);$readmemh(filename,expected);
        $sformat(filename,"%s/saturated.hex",data_dir);$readmemh(filename,expected_sat);
        repeat(4)@(negedge clk);rst_n=1;
        write_reg(12'h034,encoded_bytes);write_reg(12'h00c,shift_arg);write_reg(12'h040,7);
        // Invalid size, alignment, overlap and legacy layout must reject START.
        for(probe=0;probe<5;probe=probe+1)begin
            case(probe)
                0:write_reg(12'h034,encoded_bytes-1);
                1:write_reg(12'h028,32'hb0000002);
                2:write_reg(12'h030,32'ha0000000);
                3:write_reg(12'h03c,32'h00100001);
                4:write_reg(12'h034,49156);
            endcase
            expect_mmio_error=1;write_reg(12'h004,1);expect_mmio_error=0;
            if(dut.error_q!=3 || dut.active || dma_cmd_valid)$fatal(1,"Invalid config issued DMA");
            clear_fault();write_reg(12'h034,encoded_bytes);write_reg(12'h028,32'hb0000000);
            write_reg(12'h030,32'ha000c000);write_reg(12'h03c,32'h00100002);
        end
        $display("ICB32_CONFIG_REJECT_PASS count=5");
        // Inject source/staging/output response errors; every accepted command
        // must drain and erroneous staged words must never reach the decoder.
        for(probe=1;probe<=4;probe=probe+1)begin
            if(probe!=3)begin
                inject_kind=probe;injected=0;write_reg(12'h004,1);
                wait(dut.error_q!=0);await_idle();
                if(!injected || dut.done_q || !dut.aborted_q || dut.error_phase_q!=(probe==1 ? 3 : probe==2 ? 4 : 7))
                    $fatal(1,"Response error attribution/drain");
                if(probe==2 && (dut.stage_acks_q!=0 || dut.decoded_words!=0))$fatal(1,"Failed write published data");
                clear_fault();$display("ICB32_RESPONSE_ERROR_PASS kind=%0d",probe);
            end
        end
        // Malformed and truncated compressed streams must terminate with a
        // decoder error and drain, without waiting for absent source bytes.
        encoded[0]=0;write_reg(12'h004,1);wait(dut.error_q!=0);await_idle();
        if(dut.error_phase_q!=5)$fatal(1,"Bad header phase");encoded[0]=magic;clear_fault();
        encoded[4]=encoded_bytes-4;write_reg(12'h034,encoded_bytes-4);write_reg(12'h004,1);wait(dut.error_q!=0);await_idle();
        if(dut.error_phase_q!=5 || dut.error_q!=22)$fatal(1,"Truncated payload phase/code");encoded[4]=encoded_bytes;clear_fault();write_reg(12'h034,encoded_bytes);
        $display("ICB32_FORMAT_RECOVERY_PASS");
        for(probe=0;probe<4;probe=probe+1)begin
            if(probe==0)hold_source_probe=1;
            write_reg(12'h004,1);
            case(probe)
                0:wait(dma_cmd_valid);
                1:wait(dut.transport.pending && dut.transport.pending_kind==2);
                2:wait(dut.core.issue_read);
                3:wait(dut.output_acks_q>8);
            endcase
            write_reg(12'h004,2);
            if(probe==0 && !dma_cmd_valid)$fatal(1,"Cancelled held request disappeared");
            hold_source_probe=0;await_idle();
            if(dut.done_q || !dut.aborted_q)$fatal(1,"Cancel status");
            clear_fault();$display("ICB32_CANCEL_RECOVERY_PASS phase=%0d",probe);
        end
        // Complete the same genuine data after all failures, without reset.
        checking=1;outputs=0;write_reg(12'h004,1);wait(dut.done_q);await_idle();
        if(outputs!=25344 || dut.output_acks_q!=12672 || dut.stage_acks_q!=encoded_words || !irq)
            $fatal(1,"Recovery final real task incomplete");
        checking=0;$display("ICB32_RECOVERY_SUITE_PASS outputs=25344 no_reset=true");$finish;
    end
endmodule
