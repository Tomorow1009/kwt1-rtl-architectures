`timescale 1ns/1fs
// N1 DMA + real five-row cache/systolic core + actual shared-SRAM RTL. The source is a
// handshake-respecting test device holding offline packet bytes, not answers.
// Local transport-only harness: CPU input idle, no E203/original mem_fab proof.
// Full original-System-Bus topology is separately checked at SoC level.
module tb_arch03_p80_datapath #(parameter SOURCE_CREDITS=3,READ_LATENCY=1,TRANSACTION_DEPTH=4);
    localparam ROW_LANES=5;
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
    integer source_delay=0,tick=0,jitter=1,prefetch=1,shift_arg=10,last_delay=0;
    reg hold_source_probe=0;
    wire command_gate=!hold_source_probe && (!jitter || tick%5!=0);
    wire response_gate=(!jitter || tick%7!=0) && last_delay==0;
    assign src_cmd_ready=command_gate && !source_pending;
    assign mem_cmd_ready=command_gate && shared_ready;
    arch03_p80_accel #(.SOURCE_CREDITS(SOURCE_CREDITS),.READ_LATENCY(READ_LATENCY),.TRANSACTION_DEPTH(TRANSACTION_DEPTH)) dut(.*);
    arch03_icb_arb2_queued #(.TRANSACTION_DEPTH(TRANSACTION_DEPTH)) arb(
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
    integer encoded_bytes=0,encoded_words=0,v,layout_arg=4;
    string encoded_file;
    reg expected_sat[0:25343],seen[0:25343],seen_total[0:25343];
    reg signed [32:0] expected_total[0:25343],observed_total[0:25343];
    integer total_count=0,numeric_lane,numeric_slot,numeric_coordinate;
    integer pending=0,pending_rd=0,pending_wr=0;
    reg saved_read;
    reg [31:0] saved_addrs[0:7],saved_datas[0:7];
    integer saved_kinds[0:7];
    reg [3:0] saved_kind;
    reg [31:0] saved_addr,saved_data;
    reg started=0,ended=0,held=0;
    realtime start_ns=0,end_ns=0;
    reg [68:0] held_payload;
    integer start_cycle=0,end_cycle=0,initial_writes=0,readbacks=0,reads=0,writes=0,output_words=0;
    integer i,idx,fd,source_words=0,sat_count=0,overlap=0,max_fifo=0,cycles;
    integer first_issue=-1,last_block_cycle=-1,block_gaps=0,blocks_issued=0,write_conflicts=0;
    integer missing_group=0,missing_weight=0,result_blocked=0,credit_blocked=0;
    integer header_wait=0;
    genvar bg;
    generate
        for(bg=0;bg<60;bg=bg+1)begin:check_x_ports
            always @(posedge clk)if(rst_n && dut.core.x_banks[bg].writing && dut.core.x_banks[bg].reading)
                $fatal(1,"B X macro simultaneous write/read %0d",bg);
        end
        for(bg=0;bg<32;bg=bg+1)begin:check_w_ports
            always @(posedge clk)if(rst_n && dut.core.weight_banks[bg].writing && dut.core.weight_banks[bg].reading)
                $fatal(1,"B W macro simultaneous write/read %0d",bg);
        end
        for(bg=0;bg<80;bg=bg+1)begin:check_pe_count
            always @(posedge clk)if(rst_n && dut.core.pe_valid[bg] &&
                dut.core.array.rows[bg/16].columns[bg%16].pe.accepted_count!==7'd64)
                $fatal(1,"B output has wrong MAC count %0d",bg);
        end
    endgenerate
    string data_dir,capture_path,first_dir,first_encoded,first_capture;
    string second_dir,second_encoded,second_capture,third_capture;
    integer first_bytes=0,second_bytes=0,task_index=0,expected_tasks=1;
    reg allow_expected_fault=0;
    reg [8191:0] filename;
    function [15:0] stream_half(input integer n);
        integer canonical;
        begin
            canonical=n;
            if(layout_arg==4)begin
                if(n<1072)canonical=6336+n;
                else if(n<7408)canonical=n-1072;
            end
            stream_half=packet[canonical];
        end
    endfunction
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
        if(dut.error_q!=0 && !allow_expected_fault)$fatal(1,"DMA16 engine error code=%0d phase=%0d addr=%h",dut.error_q,dut.error_phase_q,dut.error_addr_q);
        if(dut.tr_output_count>max_fifo)max_fifo=dut.tr_output_count;
        if(dut.core.issue_read && dut.core.load_fire)overlap=overlap+1;
        if(started && !ended && dut.core.enabled && !dut.core.compute_finished)begin
            if(!(layout_arg==4 ? dut.core.x_group_valid[dut.core.compute_group] : dut.core.x_valid))missing_group=missing_group+1;
            if(!dut.core.bank_valid[dut.core.compute_bank])missing_weight=missing_weight+1;
            if(dut.core.issue_k==0 && dut.core.occupied[dut.core.issue_block[0]])result_blocked=result_blocked+1;
            if(dut.core.response_credit>=dut.core.RESPONSE_DEPTH)credit_blocked=credit_blocked+1;
            if(layout_arg==4 && dut.core.stash_count!=0 && dut.core.consume==0 && dut.core.load_state==1)write_conflicts=write_conflicts+1;
        end
        if(dut.core.issue_read)begin
            if(layout_arg==4 && !dut.core.x_group_valid[dut.core.compute_group])$fatal(1,"Read before X group committed");
            if(dut.core.bank_tile[dut.core.compute_bank]!=dut.core.compute_tile)$fatal(1,"Wrong weight tile tag");
            if(first_issue<0)begin
                first_issue=tick-start_cycle;
                if(layout_arg==4 && dut.core.x_valid)$fatal(1,"v3 failed first-five-row early start");
            end
        end
        if(dut.core.reserve)begin
            if(last_block_cycle>=0)block_gaps=block_gaps+(tick-last_block_cycle-64);
            last_block_cycle=tick;blocks_issued=blocks_issued+1;
        end
        if(dut.committed_valid && dut.committed_ready) begin
            if(dut.decoded_words>=initial_writes || dut.committed_data!==encoded[dut.decoded_words])
                $fatal(1,"Decoder consumed uncommitted or wrong encoded word");
        end
        if(dut.load_fire) begin
            for(v=0;v<dut.core_load_count;v=v+1)
                if(dut.core_load_data[v*16+:16]!==stream_half(dut.load_count_q+v))
                    $fatal(1,"Decompressed core stream mismatch halfword=%0d",dut.load_count_q+v);
        end
        for(numeric_lane=0;numeric_lane<80;numeric_lane=numeric_lane+1)begin
            if(dut.core.pe_valid[numeric_lane])begin
                numeric_slot=dut.core.pe_block[numeric_lane*9];
                numeric_coordinate=(dut.core.slot_row[numeric_slot]+numeric_lane/16)*256+
                    dut.core.slot_tile[numeric_slot]*16+numeric_lane%16;
                if(numeric_coordinate<0 || numeric_coordinate>=25344 || seen_total[numeric_coordinate] ||
                    dut.core.converted_total[numeric_lane]!==expected_total[numeric_coordinate] ||
                    dut.core.converted[numeric_lane]!==expected[numeric_coordinate] ||
                    dut.core.converted_sat[numeric_lane]!==expected_sat[numeric_coordinate])
                    $fatal(1,"N1 coordinate/total/result/sat mismatch coordinate=%0d total=%0d expected=%0d",
                        numeric_coordinate,$signed(dut.core.converted_total[numeric_lane]),$signed(expected_total[numeric_coordinate]));
                observed_total[numeric_coordinate]=dut.core.converted_total[numeric_lane];
                seen_total[numeric_coordinate]=1;total_count=total_count+1;
            end
        end
        if(dut.output_fire) begin
            idx=dut.core_row*256+dut.core_col;
            if(dut.core_result!=={expected[idx+1],expected[idx]} || dut.core_sat!=={expected_sat[idx+1],expected_sat[idx]})$fatal(1,"Actual core result/saturation mismatch");
            sat_count=sat_count+dut.core_sat[0]+dut.core_sat[1];
        end
        // Responses before simultaneous commands: one owner and exactly one ACK.
        if(dma_rsp_valid && dma_rsp_ready) begin
            if(!pending || dma_rsp_err)$fatal(1,"Orphan/error DMA response");
            saved_addr=saved_addrs[pending_rd];saved_data=saved_datas[pending_rd];saved_kind=saved_kinds[pending_rd];
            pending_rd=(pending_rd+1)%8;
            if(saved_kind==1)source_words=source_words+1;
            if(saved_kind==2) begin
                idx=(saved_addr-32'ha0000000)/4;
                if(saved_data!==encoded[idx])$fatal(1,"Initial loading mismatch");
                initial_writes=initial_writes+1;
            end
            if(saved_kind==3) begin
                idx=(saved_addr-32'ha0000000)/4;
                if(idx!=readbacks || idx>=initial_writes)$fatal(1,"Readback before corresponding write ACK");
                if(dma_rsp_rdata!==encoded[idx])$fatal(1,"Actual shared read data mismatch");
                readbacks=readbacks+1;
            end
            if(saved_kind==4) begin
                idx=(saved_addr-32'ha000c000)/2;
                if(saved_addr<32'ha000c000 || saved_addr>=32'ha0018600 || saved_addr[1:0]!=0 ||
                    seen[idx] || seen[idx+1] || saved_data!=={expected[idx+1],expected[idx]})
                    $fatal(1,"Output write mismatch addr=%h data=%h",saved_addr,saved_data);
                seen[idx]=1;seen[idx+1]=1;output_words=output_words+1;
                if(!seen_total[idx] || !seen_total[idx+1])$fatal(1,"Write ACK without observed total33");
                $fdisplay(fd,"%0d,%0d,%0d,%0d,%0d",idx/256,idx%256,$signed(saved_data[15:0]),expected_sat[idx],$signed(observed_total[idx]));
                $fdisplay(fd,"%0d,%0d,%0d,%0d,%0d",(idx+1)/256,(idx+1)%256,$signed(saved_data[31:16]),expected_sat[idx+1],$signed(observed_total[idx+1]));
                if(output_words==12672)begin ended=1;end_cycle=tick+1;end_ns=$realtime;end
            end
            pending=pending-1;
        end
        if(dma_cmd_valid && dma_cmd_ready) begin
            if(pending>=TRANSACTION_DEPTH)$fatal(1,"P80 metadata overflow");
            pending=pending+1;saved_addrs[pending_wr]=dma_cmd_addr;saved_datas[pending_wr]=dma_cmd_wdata;
            saved_kinds[pending_wr]=dma_cmd_read ? (dma_cmd_addr>=32'hb0000000 ? 1 : 3) : (dma_cmd_addr<32'ha000c000 ? 2 : 4);
            pending_wr=(pending_wr+1)%8;
            if(dma_cmd_read)reads=reads+1;else writes=writes+1;
        end
        if(dut.done_q && started && (!ended || output_words!=12672 || pending || dma_cmd_valid || arb_pending || router_pending))
            $fatal(1,"DMA DONE before final response/fabric drain");
        if(tick>6000000)$fatal(1,"DMA16 datapath timeout");
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
    task check_access(input bit reading,input [11:0] offset,input [31:0] data,
        input bit expect_error,input [31:0] expected_data);
        begin
            allow_expected_fault=1;
            @(negedge clk);cmd_valid=1;cmd_read=reading;cmd_addr=32'h40000000+offset;cmd_wdata=data;cmd_wmask=15;
            @(posedge clk);while(!cmd_ready)@(posedge clk);
            @(negedge clk);cmd_valid=0;while(!rsp_valid)@(negedge clk);
            if(rsp_err!==expect_error || (reading && !expect_error && rsp_rdata!==expected_data))
                $fatal(1,"N1 ABI check failed offset=%h error=%b data=%h",offset,rsp_err,rsp_rdata);
            rsp_ready=1;@(negedge clk);rsp_ready=0;
            if(expect_error)begin
                write_reg(12'h004,4);
                wait(!dut.core_cancel_q && dut.core_start_ready);
            end
            allow_expected_fault=0;
        end
    endtask
    task run_case(input string directory,input string encoded_name,input integer byte_count,input string capture_name);
        begin
            @(negedge clk);started=0;
            write_reg(12'h004,4);
            wait(!dut.core_cancel_q && dut.core_start_ready);
            @(negedge clk);
            data_dir=directory;encoded_file=encoded_name;encoded_bytes=byte_count;encoded_words=byte_count/4;
            capture_path=capture_name;ended=0;held=0;pending=0;pending_rd=0;pending_wr=0;
            initial_writes=0;readbacks=0;reads=0;writes=0;output_words=0;source_words=0;sat_count=0;overlap=0;max_fifo=0;
            total_count=0;first_issue=-1;last_block_cycle=-1;block_gaps=0;blocks_issued=0;write_conflicts=0;
            missing_group=0;missing_weight=0;result_blocked=0;credit_blocked=0;
            $readmemh(encoded_file,encoded,0,encoded_words-1);
        for(i=0;i<23488;i=i+1)packet[i]=16'hxxxx;
        for(i=0;i<25344;i=i+1)begin expected[i]=16'hxxxx;expected_sat[i]=1'bx;seen[i]=0;seen_total[i]=0;expected_total[i]='x;observed_total[i]='x;end
        $sformat(filename,"%s/load.hex",data_dir);$readmemh(filename,packet);
        $sformat(filename,"%s/result.hex",data_dir);$readmemh(filename,expected);
        $sformat(filename,"%s/total.hex",data_dir);$readmemh(filename,expected_total);
        $sformat(filename,"%s/saturated.hex",data_dir);$readmemh(filename,expected_sat);
        for(i=0;i<23488;i=i+1)if((^packet[i])===1'bx)$fatal(1,"Missing packet input");
        for(i=0;i<25344;i=i+1)if((^expected[i])===1'bx || (^expected_total[i])===1'bx || expected_sat[i]===1'bx)$fatal(1,"Missing reference output");
        fd=$fopen(capture_path,"w");if(!fd)$fatal(1,"Capture open failed");
        write_reg(12'h034,encoded_bytes);write_reg(12'h03c,32'h00100000+layout_arg);write_reg(12'h00c,shift_arg);write_reg(12'h024,prefetch ? 3 : 1);write_reg(12'h040,7);write_reg(12'h004,1);
        wait(dut.done_q);repeat(4)@(negedge clk);
        for(i=0;i<25344;i=i+1)if(!seen[i] || !seen_total[i])$fatal(1,"Missing actual output");
        if(reads!=2*encoded_words || readbacks!=encoded_words || dut.read_acks_q!=encoded_words || writes!=encoded_words+12672 || initial_writes!=encoded_words || source_words!=encoded_words ||
            total_count!=25344 || output_words!=12672 || dut.load_count_q!=23488 || dut.output_count_q!=25344 ||
            dut.saturated_count_q!=sat_count || (dut.output_acks_q<<2)!=50688 || !irq)
            $fatal(1,"DMA16 transaction/output/final status accounting");
        if(prefetch && overlap==0)$fatal(1,"No actual compute/prefetch overlap");
        if(!started || (end_ns-start_ns)-(end_cycle-start_cycle)*6.666666>0.00001 ||
            (end_ns-start_ns)-(end_cycle-start_cycle)*6.666666< -0.00001)
            $fatal(1,"Issue-edge timing and independent timestamps disagree");
        $fclose(fd);
        $display("N1_TOTAL33_PASS outputs=%0d read_latency=%0d",total_count,READ_LATENCY);
        $display("ARCH03_P80_DATAPATH_PASS outputs=25344 cycles=%0d prefetch=%0d jitter=%0d overlap=%0d fifo_max=%0d saturated=%0d cpu_executed=false",end_cycle-start_cycle,prefetch,jitter,overlap,max_fifo,sat_count);
        $display("ICB32_TASK_METRICS bytes=%0d turns=%0d rows=%0d",encoded_bytes,dut.turnovers,ROW_LANES);
        if(blocks_issued!=320)$fatal(1,"Wrong block count %0d",blocks_issued);
        $display("N1_PIPELINE layout=%0d first_issue=%0d block_gaps=%0d missing_x=%0d missing_w=%0d result_blocked=%0d credit_blocked=%0d x_write_conflicts=%0d",layout_arg,first_issue,block_gaps,missing_group,missing_weight,result_blocked,credit_blocked,write_conflicts);
            task_index=task_index+1;
        end
    endtask
    initial begin
        if(!$value$plusargs("ENCODED_FILE=%s",first_encoded))$fatal(1,"ENCODED_FILE required");
        if(!$value$plusargs("ENCODED_BYTES=%d",first_bytes))$fatal(1,"ENCODED_BYTES required");
        if(!$value$plusargs("DATA_DIR=%s",first_dir))$fatal(1,"DATA_DIR required");
        if(!$value$plusargs("CAPTURE=%s",first_capture))first_capture="n1_capture.csv";
        if(!$value$plusargs("SHIFT=%d",shift_arg))shift_arg=10;
        if(shift_arg!=10)$fatal(1,"N1 requires SHIFT10");
        if(!$value$plusargs("PREFETCH=%d",prefetch))prefetch=1;
        if(!$value$plusargs("JITTER=%d",jitter))jitter=1;
        if($value$plusargs("SECOND_DATA_DIR=%s",second_dir))begin
            if(!$value$plusargs("SECOND_ENCODED_FILE=%s",second_encoded) ||
                !$value$plusargs("SECOND_ENCODED_BYTES=%d",second_bytes) ||
                !$value$plusargs("SECOND_CAPTURE=%s",second_capture) ||
                !$value$plusargs("THIRD_CAPTURE=%s",third_capture))$fatal(1,"Incomplete A/B/A options");
            expected_tasks=3;
        end
        repeat(4)@(negedge clk);rst_n=1;
        check_access(1,12'h000,0,0,32'h4b57530b);
        check_access(1,12'h074,0,0,32'h000905bf);
        check_access(1,12'h08c,0,0,32'h000e0c20);
        check_access(0,12'h08c,0,1,0);
        check_access(0,12'h00c,12,1,0);
        check_access(1,12'h00c,0,0,10);
        write_reg(12'h03c,32'h00100003);
        check_access(0,12'h004,1,1,0);
        if(dma_cmd_valid || dut.active)$fatal(1,"Legacy layout started N1");
        $display("N1_ABI_REJECTION_PASS old_layout=true old_shift=true numeric_readonly=true");
        run_case(first_dir,first_encoded,first_bytes,first_capture);
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
        $display("ARCH03_N1_RESTART_INVALIDATION_PASS no_reset=true held_request_drained=true");
        $display("ICB32_TRANSPORT_METRICS bytes=%0d turns=%0d rows=%0d",encoded_bytes,dut.turnovers,ROW_LANES);
        if(expected_tasks==3)begin
            run_case(second_dir,second_encoded,second_bytes,second_capture);
            run_case(first_dir,first_encoded,first_bytes,third_capture);
            $display("N1_NO_RESET_ABA_PASS tasks=3 total_result_sat=true");
        end
        $display("N1_DATAPATH_SUITE_PASS tasks=%0d read_latency=%0d cpu_executed=false",task_index,READ_LATENCY);
        $finish;
    end
endmodule
