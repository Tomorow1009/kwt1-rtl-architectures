`timescale 1ns/1fs
// Actual DMA16 + actual linear16 + actual shared-SRAM RTL. The source is a
// handshake-respecting test device holding offline packet bytes, not answers.
// Uses the actual new arbiter/router; the CPU input is idle, not an E203 model.
module tb_arch03_icb32_contention #(parameter ROW_LANES=4);
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
    reg cpu_cmd_valid=0,cpu_cmd_read=0,cpu_rsp_ready=0,cpu_done=0;
    reg [31:0] cpu_cmd_addr=0,cpu_cmd_wdata=0;
    reg [3:0] cpu_cmd_wmask=0;
    wire cpu_cmd_ready,cpu_rsp_valid,cpu_rsp_err;
    wire [31:0] cpu_rsp_rdata;
    integer cpu_n,cpu_served=0,dma_grants_waiting=0;
    arch03_icb32_accel #(.ROW_LANES(ROW_LANES)) dut(.*);
    arch03_icb_arb2_turnover arb(
        .clk(clk),.rst_n(rst_n),.cpu_cmd_valid(cpu_cmd_valid),.cpu_cmd_ready(cpu_cmd_ready),.cpu_cmd_addr(cpu_cmd_addr),
        .cpu_cmd_read(cpu_cmd_read),.cpu_cmd_wdata(cpu_cmd_wdata),.cpu_cmd_wmask(cpu_cmd_wmask),
        .cpu_rsp_valid(cpu_rsp_valid),.cpu_rsp_ready(cpu_rsp_ready),.cpu_rsp_rdata(cpu_rsp_rdata),.cpu_rsp_err(cpu_rsp_err),
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
        .mem_rsp_rdata(shared_rsp_data),.mem_rsp_err(shared_rsp_err),
        .src_cmd_valid(src_cmd_valid),.src_cmd_ready(src_cmd_ready),.src_cmd_addr(src_cmd_addr),
        .src_cmd_read(src_cmd_read),.src_cmd_wdata(src_cmd_wdata),.src_cmd_wmask(src_cmd_wmask),
        .src_rsp_valid(source_rsp_valid && response_gate),.src_rsp_ready(src_rsp_ready),
        .src_rsp_rdata(source_data),.src_rsp_err(1'b0),.transaction_pending(router_pending));
    arch03_shared_sram_turnover shared(
        .clk(clk),.rst_n(rst_n),.cmd_valid(mem_cmd_valid && command_gate),
        .cmd_ready(shared_ready),.cmd_addr(mem_cmd_addr),.cmd_read(mem_cmd_read),
        .cmd_wdata(mem_cmd_wdata),.cmd_wmask(mem_cmd_wmask),.rsp_valid(shared_rsp_valid),
        .rsp_ready(mem_rsp_ready && response_gate),.rsp_rdata(shared_rsp_data),.rsp_err(shared_rsp_err));
    reg [15:0] packet[0:23487],expected[0:25343];
    reg [31:0] encoded[0:11751];
    integer encoded_bytes=0,encoded_words=0,v;
    string encoded_file;
    reg expected_sat[0:25343],seen[0:25343];
    reg pending=0,saved_read;
    reg [3:0] saved_kind;
    reg [31:0] saved_addr,saved_data;
    reg started=0,ended=0,held=0;
    realtime start_ns=0,end_ns=0;
    reg [68:0] held_payload;
    integer start_cycle=0,end_cycle=0,initial_writes=0,reads=0,writes=0,output_words=0;
    integer i,idx,fd,source_words=0,sat_count=0,overlap=0,max_fifo=0,cycles;
    string data_dir,capture_path;
    reg [8191:0] filename;
    always #3.333333 clk=~clk;
    // Master valid is registered. Observe its issuing edge after NBA updates,
    // including a request held for ready; clock-sampling on the next edge would
    // omit the first offered cycle. The timestamp independently checks cycles.
    always @(posedge dma_cmd_valid) if(rst_n && !started && dma_cmd_read &&
        dma_cmd_addr>=32'hb0000000 && dma_cmd_addr<32'hb000c000) begin
        if(dut.core.x_valid!==1'b0 || dut.core.bank_valid!==2'b00)
            $fatal(1,"Previous task cache validity survived the first source request");
        started=1;start_cycle=tick;start_ns=$realtime;
    end
    always @(posedge clk or negedge rst_n) begin
        if(!rst_n) begin
            tick<=0;source_pending<=0;source_rsp_valid<=0;source_delay<=0;last_delay<=0;
        end else begin
            tick<=tick+1;
            if(last_delay!=0)last_delay<=last_delay-1;
            if(src_cmd_valid && src_cmd_ready) begin
                if(!src_cmd_read || source_pending)$fatal(1,"Bad source transaction");
                source_pending<=1;source_delay<=jitter ? 2+(tick%3) : 0;
                source_data<=encoded[(src_cmd_addr-32'hb0000000)/4];
                // Nominal model: registered response after accepted request,
                // consumable on the next edge, matching the SoC source model.
                if(!jitter)source_rsp_valid<=1;
            end
            if(source_pending && !source_rsp_valid) begin
                if(source_delay!=0)source_delay<=source_delay-1;
                else source_rsp_valid<=1;
            end
            if(source_rsp_valid && src_rsp_ready && response_gate) begin
                source_pending<=0;source_rsp_valid<=0;
            end
            if(jitter && dma_cmd_valid && dma_cmd_ready && dut.transport.cmd_kind==4 && output_words==12671)last_delay<=31;
        end
    end
    always @(posedge clk) if(rst_n) begin
        if(held && (!dma_cmd_valid || {dma_cmd_read,dma_cmd_addr,dma_cmd_wdata,dma_cmd_wmask}!==held_payload))
            $fatal(1,"DMA command unstable");
        held=dma_cmd_valid && !dma_cmd_ready;
        held_payload={dma_cmd_read,dma_cmd_addr,dma_cmd_wdata,dma_cmd_wmask};
        if(dut.error_q!=0)$fatal(1,"DMA16 engine error code=%0d phase=%0d addr=%h",dut.error_q,dut.error_phase_q,dut.error_addr_q);
        if(dut.tr_output_count>max_fifo)max_fifo=dut.tr_output_count;
        if(dut.core.issue_read && dut.core.load_fire)overlap=overlap+1;
        if(dut.committed_valid && dut.committed_ready) begin
            if(dut.decoded_words>=initial_writes || dut.committed_data!==encoded[dut.decoded_words])
                $fatal(1,"Decoder consumed uncommitted or wrong encoded word");
        end
        if(dut.load_fire) begin
            for(v=0;v<dut.core_load_count;v=v+1)
                if(dut.core_load_data[v*16+:16]!==packet[dut.load_count_q+v])
                    $fatal(1,"Decompressed core stream mismatch halfword=%0d",dut.load_count_q+v);
        end
        if(dut.output_fire) begin
            idx=dut.core_row*256+dut.core_col;
            if(dut.core_result!==expected[idx] || dut.core_sat!==expected_sat[idx])$fatal(1,"Actual core result/saturation mismatch");
            sat_count=sat_count+dut.core_sat;
        end
        // Responses before simultaneous commands: one owner and exactly one ACK.
        if(dma_rsp_valid && dma_rsp_ready) begin
            if(!pending || dma_rsp_err)$fatal(1,"Orphan/error DMA response");
            if(saved_kind==1)source_words=source_words+1;
            if(saved_kind==2) begin
                idx=(saved_addr-32'ha0000000)/4;
                if(saved_data!==encoded[idx])$fatal(1,"Initial loading mismatch");
                initial_writes=initial_writes+1;
            end
            if(saved_kind==3) begin
                $fatal(1,"Forward candidate performed forbidden shared readback");
                if(initial_writes!=11744)$fatal(1,"Core feed before initial loading complete");
                idx=(saved_addr-32'ha0000000)/2;
                if(dma_rsp_rdata!=={packet[idx+1],packet[idx]})$fatal(1,"Shared read data mismatch");
            end
            if(saved_kind==4) begin
                idx=(saved_addr-32'ha000c000)/2;
                if(saved_addr<32'ha000c000 || saved_addr>=32'ha0018600 || saved_addr[1:0]!=0 ||
                    seen[idx] || seen[idx+1] || saved_data!=={expected[idx+1],expected[idx]})
                    $fatal(1,"Output write mismatch addr=%h data=%h",saved_addr,saved_data);
                seen[idx]=1;seen[idx+1]=1;output_words=output_words+1;
                $fdisplay(fd,"%0d,%0d",idx,$signed(saved_data[15:0]));
                $fdisplay(fd,"%0d,%0d",idx+1,$signed(saved_data[31:16]));
                if(output_words==12672)begin ended=1;end_cycle=tick+1;end_ns=$realtime;end
            end
            pending=0;
        end
        if(dma_cmd_valid && dma_cmd_ready) begin
            if(pending)$fatal(1,"Multiple DMA requests outstanding");
            pending=1;saved_read=dma_cmd_read;saved_addr=dma_cmd_addr;saved_data=dma_cmd_wdata;saved_kind=dut.transport.cmd_kind;
            if(dma_cmd_read)reads=reads+1;else writes=writes+1;
        end
        if(dut.done_q && (!ended || output_words!=12672 || pending || dma_cmd_valid || arb_pending || router_pending))
            $fatal(1,"DMA DONE before final response/fabric drain");
        if(tick>2000000)$fatal(1,"DMA16 datapath timeout");
    end
    always @(posedge clk) if(rst_n) begin
        if(!cpu_cmd_valid || cpu_cmd_ready)dma_grants_waiting=0;
        else if(dma_cmd_valid && dma_cmd_ready)begin
            dma_grants_waiting=dma_grants_waiting+1;
            if(dma_grants_waiting>8)$fatal(1,"CPU starved by DMA");
        end
    end
    task cpu_access(input bit reading,input [31:0] address,input [31:0] data,input [3:0] mask,input [31:0] expected_data);
        begin
            @(negedge clk);cpu_cmd_valid=1;cpu_cmd_read=reading;cpu_cmd_addr=address;cpu_cmd_wdata=data;cpu_cmd_wmask=mask;
            @(posedge clk);while(!cpu_cmd_ready)@(posedge clk);
            @(negedge clk);cpu_cmd_valid=0;while(!cpu_rsp_valid)@(negedge clk);
            if(cpu_rsp_err || (reading && cpu_rsp_rdata!==expected_data))$fatal(1,"CPU SRAM read/write mismatch");
            repeat(3)@(negedge clk);cpu_rsp_ready=1;
            @(posedge clk);while(!cpu_rsp_valid)@(posedge clk);
            @(negedge clk);cpu_rsp_ready=0;cpu_served=cpu_served+1;
        end
    endtask
    initial begin
        wait(rst_n && dut.active);
        for(cpu_n=0;cpu_n<32;cpu_n=cpu_n+1)begin
            cpu_access(0,32'ha0073ffc+cpu_n*4,32'hdeadbeef,15,0);
            cpu_access(0,32'ha0073ffc+cpu_n*4,32'h12345678,5,0);
            cpu_access(1,32'ha0073ffc+cpu_n*4,0,0,32'hde34be78);
        end
        cpu_done=1;$display("ICB32_CPU_CONTENTION_PASS accesses=%0d byte_masks=true bank_boundary=true",cpu_served);
    end
    task write_reg(input [11:0] offset,input [31:0] data);
        begin
            @(negedge clk);cmd_valid=1;cmd_read=0;cmd_addr=32'h40000000+offset;cmd_wdata=data;cmd_wmask=15;
            @(posedge clk);while(!cmd_ready)@(posedge clk);
            @(negedge clk);cmd_valid=0;while(!rsp_valid)@(negedge clk);
            if(rsp_err)$fatal(1,"MMIO configuration failed offset=%h",offset);
            rsp_ready=1;@(negedge clk);rsp_ready=0;
        end
    endtask
    initial begin
        if(!$value$plusargs("ENCODED_FILE=%s",encoded_file))$fatal(1,"ENCODED_FILE required");
        if(!$value$plusargs("ENCODED_BYTES=%d",encoded_bytes))$fatal(1,"ENCODED_BYTES required");
        encoded_words=encoded_bytes/4;
        $readmemh(encoded_file,encoded,0,encoded_words-1);
        if(!$value$plusargs("DATA_DIR=%s",data_dir))$fatal(1,"DATA_DIR required");
        if(!$value$plusargs("CAPTURE=%s",capture_path))capture_path="dma_capture.csv";
        if(!$value$plusargs("SHIFT=%d",shift_arg))shift_arg=12;
        if(!$value$plusargs("PREFETCH=%d",prefetch))prefetch=1;
        if(!$value$plusargs("JITTER=%d",jitter))jitter=1;
        for(i=0;i<23488;i=i+1)packet[i]=16'hxxxx;
        for(i=0;i<25344;i=i+1)begin expected[i]=16'hxxxx;expected_sat[i]=1'bx;seen[i]=0;end
        $sformat(filename,"%s/load.hex",data_dir);$readmemh(filename,packet);
        $sformat(filename,"%s/result.hex",data_dir);$readmemh(filename,expected);
        $sformat(filename,"%s/saturated.hex",data_dir);$readmemh(filename,expected_sat);
        for(i=0;i<23488;i=i+1)if((^packet[i])===1'bx)$fatal(1,"Missing packet input");
        for(i=0;i<25344;i=i+1)if((^expected[i])===1'bx || expected_sat[i]===1'bx)$fatal(1,"Missing reference output");
        fd=$fopen(capture_path,"w");if(!fd)$fatal(1,"Capture open failed");
        repeat(4)@(negedge clk);rst_n=1;
        write_reg(12'h034,encoded_bytes);write_reg(12'h03c,32'h00100002);write_reg(12'h00c,shift_arg);write_reg(12'h024,prefetch ? 3 : 1);write_reg(12'h040,7);write_reg(12'h004,1);
        wait(dut.done_q);repeat(4)@(negedge clk);
        for(i=0;i<25344;i=i+1)if(!seen[i])$fatal(1,"Missing actual output");
        if(reads!=encoded_words || writes!=encoded_words+12672 || initial_writes!=encoded_words || source_words!=encoded_words ||
            output_words!=12672 || dut.load_count_q!=23488 || dut.output_count_q!=25344 ||
            dut.saturated_count_q!=sat_count || (dut.output_acks_q<<2)!=50688 || !irq)
            $fatal(1,"DMA16 transaction/output/final status accounting");
        if(prefetch && overlap==0)$fatal(1,"No actual compute/prefetch overlap");
        if(!started || (end_ns-start_ns)-(end_cycle-start_cycle)*6.666666>0.00001 ||
            (end_ns-start_ns)-(end_cycle-start_cycle)*6.666666< -0.00001)
            $fatal(1,"Issue-edge timing and independent timestamps disagree");
        $fclose(fd);
        $display("ARCH03_ICB32_DATAPATH_PASS outputs=25344 cycles=%0d prefetch=%0d jitter=%0d overlap=%0d fifo_max=%0d saturated=%0d cpu_executed=false",end_cycle-start_cycle,prefetch,jitter,overlap,max_fifo,sat_count);
        $display("ICB32_TASK_METRICS bytes=%0d turns=%0d rows=%0d",encoded_bytes,dut.turnovers,ROW_LANES);
        // No reset: the completed core still has X valid. A second START must
        // invalidate it before issuing any new hardware loading request. Hold
        // that request, then cancel and drain it through the actual fabric.
        if(dut.core.x_valid!==1'b1)$fatal(1,"Restart probe has no old X cache to invalidate");
        @(negedge clk);hold_source_probe=1;started=0;
        write_reg(12'h004,1);wait(dma_cmd_valid);@(negedge clk);
        if(!started || dut.core.x_valid || dut.core.bank_valid!=0)
            $fatal(1,"Restart invalidation probe failed started=%0d x_valid=%0d banks=%0d",started,dut.core.x_valid,dut.core.bank_valid);
        write_reg(12'h004,2);
        if(!dma_cmd_valid || dut.state_q!=5)$fatal(1,"Restart cancellation withdrew an offered request");
        @(negedge clk);hold_source_probe=0;
        wait(!dut.active && !arb_pending && !router_pending && !dut.core_cancel_q && dut.core_start_ready);
        if(dut.done_q || !dut.aborted_q || (dut.stage_acks_q<<2)!=0 || (dut.output_acks_q<<2)!=0 || source_words!=encoded_words+1)
            $fatal(1,"Restart probe cancelled incorrectly or wrote unrequested shared data");
        $display("ARCH03_ICB32_RESTART_INVALIDATION_PASS no_reset=true held_request_drained=true");
        $display("ICB32_TRANSPORT_METRICS bytes=%0d turns=%0d rows=%0d",encoded_bytes,dut.turnovers,ROW_LANES);
        if(!cpu_done || cpu_served!=96)$fatal(1,"CPU contention unfinished");
        $finish;
    end
endmodule
