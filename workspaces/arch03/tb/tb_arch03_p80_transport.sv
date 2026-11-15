`timescale 1ns/1ps
// Ordered multi-request slave. Shared reads deliberately return data different
// from the source/write payload, so retained write-data forwarding cannot pass.
module tb_arch03_p80_transport #(parameter DEPTH=4);
    localparam WORDS=64;
    reg clk=0,rst_n=0,start=0,cancel=0;
    always #3 clk=~clk;
    wire cmd_valid,cmd_read,rsp_ready,busy,done,aborted,error;
    reg cmd_ready=0,rsp_valid=0,rsp_err=0;
    reg [31:0] rsp_data=0;
    wire [31:0] cmd_addr,cmd_data,committed_data,error_addr;
    wire [3:0] cmd_mask,error_kind,q_occupancy,q_peak;
    wire committed_valid,output_ready,draining,pending;
    reg committed_ready=0;
    wire [31:0] source_acks,stage_acks,read_acks,output_acks,decoded_words;
    wire [31:0] offered,waiting,turnovers,credit_stalls;
    wire [2:0] pending_kind;wire [5:0] output_count;
    integer tick=0,out_count=0,consume_count=0,latency=1,fault_kind=0,cases=0;
    integer head=0,tail=0,count=0,phase_count[0:4];
    integer q_kind[0:16383],q_due[0:16383];
    reg [31:0] q_addr[0:16383],q_data[0:16383],q_read[0:16383];
    reg q_error[0:16383];
    reg [31:0] memory[0:WORDS-1];reg written[0:WORDS-1];
    reg fault_scheduled=0,fault_seen=0,hold_read=0;
    reg [31:0] expected_error_addr=0;
    integer output_requests=0,final_ack_waits=0,peak_seen=0,simultaneous=0;
    integer accepted_total=0,returned_total=0,k,index,kind;
    reg held=0;reg [68:0] held_payload;
    wire is_readback=cmd_read && cmd_addr>=32'ha0000000 && cmd_addr<32'ha000c000;
    wire output_valid=busy && out_count<12672;
    wire [31:0] output_addr=32'ha000c000+out_count*4;
    wire [31:0] output_data=32'h12340000+out_count;
    arch03_p80_transport #(.TRANSACTION_DEPTH(DEPTH)) dut(
        .clk(clk),.rst_n(rst_n),.start(start),.cancel(cancel),
        .source_addr(32'hb0000000),.input_addr(32'ha0000000),.encoded_bytes(WORDS*4),
        .output_valid(output_valid),.output_ready(output_ready),.output_addr(output_addr),.output_data(output_data),
        .committed_valid(committed_valid),.committed_ready(committed_ready),.committed_data(committed_data),
        .cmd_valid(cmd_valid),.cmd_ready(cmd_ready),.cmd_addr(cmd_addr),.cmd_read(cmd_read),
        .cmd_wdata(cmd_data),.cmd_wmask(cmd_mask),.rsp_valid(rsp_valid),.rsp_ready(rsp_ready),
        .rsp_rdata(rsp_data),.rsp_err(rsp_err),.busy(busy),.done(done),.aborted(aborted),.error(error),
        .error_addr(error_addr),.error_kind(error_kind),.source_acks(source_acks),.stage_acks(stage_acks),
        .read_acks(read_acks),.output_acks(output_acks),.decoded_words(decoded_words),
        .draining(draining),.transaction_pending(pending),.pending_kind_status(pending_kind),
        .output_fifo_count(output_count),.offered_cycles(offered),.response_wait_cycles(waiting),
        .turnovers(turnovers),.accepted_queue_count(q_occupancy),.accepted_queue_peak(q_peak),
        .accepted_credit_stalls(credit_stalls));
    function [31:0] source_word(input integer n);source_word=32'hbeef0100+n;endfunction
    function [31:0] shared_word(input integer n);shared_word=source_word(n)^32'h55aa55aa;endfunction

    always @(posedge clk) begin
        tick=tick+1;
        if(!rst_n) begin
            head=0;tail=0;count=0;held=0;out_count<=0;consume_count<=0;
        end else begin
            if(q_occupancy!==count)$fatal(1,"P80 DMA ledger mismatch");
            if(dut.source_reserved>3 || dut.source_count>dut.source_reserved ||
                dut.commit_reserved>16 || dut.commit_count>dut.commit_reserved || output_count>32)
                $fatal(1,"P80 reserved data credit violated");
            if(held && (!cmd_valid || {cmd_addr,cmd_read,cmd_data,cmd_mask}!==held_payload))
                $fatal(1,"P80 changed held request on cancel/backpressure");
            held=cmd_valid && !cmd_ready;held_payload={cmd_addr,cmd_read,cmd_data,cmd_mask};
            if(start) begin
                if(count!=0 || cmd_valid)$fatal(1,"New task started before drain");
                head=0;tail=0;out_count<=0;consume_count<=0;output_requests=0;
                fault_scheduled=0;fault_seen=0;accepted_total=0;returned_total=0;
                for(k=0;k<WORDS;k=k+1)written[k]=0;
                for(k=0;k<5;k=k+1)phase_count[k]=0;
            end else begin
                if(output_valid && output_ready)out_count<=out_count+1;
                if(committed_valid && committed_ready) begin
                    if(consume_count>=WORDS || committed_data!==shared_word(consume_count) || read_acks<=consume_count)
                        $fatal(1,"P80 decoder input was not the actual read response");
                    consume_count<=consume_count+1;
                end
            end
            if(draining && committed_valid)$fatal(1,"Published old task data during draining");
            if(rsp_valid && rsp_ready && cmd_valid && cmd_ready)simultaneous=simultaneous+1;
            if(count!=0 && q_kind[head]==4 && q_addr[head]==32'ha00185fc && !rsp_valid) begin
                final_ack_waits=final_ack_waits+1;
                if(done)$fatal(1,"DONE before final output ACK");
            end
            if(rsp_valid && rsp_ready) begin
                if(count==0)$fatal(1,"Unowned P80 response");
                if(rsp_err)fault_seen=1;
                else if(q_kind[head]==2) begin
                    index=(q_addr[head]-32'ha0000000)/4;
                    if(q_data[head]!==source_word(index))$fatal(1,"Staged source payload mismatch");
                    memory[index]=shared_word(index);written[index]=1;
                end
                head=head+1;count=count-1;returned_total=returned_total+1;
            end
            if(cmd_valid && cmd_ready) begin
                if(count>=DEPTH || tail>=16384)$fatal(1,"P80 accepted metadata overflow");
                if(cmd_addr>=32'hb0000000)begin
                    kind=1;index=(cmd_addr-32'hb0000000)/4;
                    if(!cmd_read || cmd_mask!=0 || index<0 || index>=WORDS)$fatal(1,"Bad source request");
                    q_read[tail]=source_word(index);
                end else if(cmd_addr<32'ha000c000)begin
                    index=(cmd_addr-32'ha0000000)/4;kind=cmd_read ? 3 : 2;
                    if(index<0 || index>=WORDS || cmd_mask!=(cmd_read ? 0 : 15))$fatal(1,"Bad shared request");
                    if(cmd_read) begin
                        if(!written[index])$fatal(1,"Read before successful shared write ACK");
                        q_read[tail]=memory[index];
                    end else q_read[tail]=0;
                end else begin
                    kind=4;
                    if(cmd_read || cmd_mask!=15 || cmd_addr!==32'ha000c000+output_requests*4 ||
                        cmd_data!==32'h12340000+output_requests)$fatal(1,"Output address/data sequence mismatch");
                    output_requests=output_requests+1;q_read[tail]=0;
                end
                q_kind[tail]=kind;q_addr[tail]=cmd_addr;q_data[tail]=cmd_data;
                q_due[tail]=tick+latency+(tick%3);
                if(kind==4 && output_requests==12672)q_due[tail]=q_due[tail]+37;
                q_error[tail]=(kind==fault_kind && phase_count[kind]>=1 && !fault_scheduled);
                if(q_error[tail]) begin fault_scheduled=1;expected_error_addr=cmd_addr;end
                phase_count[kind]=phase_count[kind]+1;tail=tail+1;count=count+1;accepted_total=accepted_total+1;
                if(count>peak_seen)peak_seen=count;
            end
            if(done && (count!=0 || cmd_valid || pending || output_acks!=12672 ||
                source_acks!=WORDS || stage_acks!=WORDS || read_acks!=WORDS || decoded_words!=WORDS ||
                consume_count!=WORDS || accepted_total!=returned_total))$fatal(1,"Premature P80 DONE");
        end
        if(tick>3000000)$fatal(1,"P80 transport timeout");
    end

    always @(negedge clk) begin
        if(!rst_n)begin cmd_ready=0;rsp_valid=0;rsp_data=0;rsp_err=0;committed_ready=0;end
        else begin
            cmd_ready=count<16 && tick%5!=0 && !(hold_read && is_readback);
            rsp_valid=count!=0 && tick>=q_due[head];
            if(count!=0)begin rsp_data=q_read[head];rsp_err=q_error[head];end
            committed_ready=tick%7!=0 && tick%997>130;
        end
    end

    task run_case(input integer fail_phase,input integer cancel_mode,input integer delay_cycles);
        begin
            @(negedge clk);#1;fault_kind=fail_phase;latency=delay_cycles;hold_read=cancel_mode==1;start=1;
            @(negedge clk);#1;start=0;
            if(cancel_mode==1) begin
                wait(cmd_valid && is_readback && !cmd_ready);
                @(negedge clk);#1;cancel=1;
                repeat(7)@(negedge clk);
                if(!cmd_valid || !busy)$fatal(1,"Cancel withdrew offered P80 command");
                #1;hold_read=0;wait(aborted);@(negedge clk);#1;cancel=0;
            end else if(cancel_mode==2) begin
                wait(q_occupancy==DEPTH);@(negedge clk);#1;cancel=1;
                wait(aborted);@(negedge clk);#1;cancel=0;
            end else if(fail_phase!=0) begin
                wait(aborted);@(negedge clk);#1;
                if(!error || error_kind!=fail_phase || error_addr!==expected_error_addr || !fault_seen)
                    $fatal(1,"Wrong ordered error address/type");
            end else begin
                wait(done);@(negedge clk);#1;
                if(error || aborted)$fatal(1,"Unexpected P80 completion error");
            end
            repeat(4)@(negedge clk);
            if(busy || cmd_valid || count!=0 || pending || accepted_total!=returned_total)$fatal(1,"Undrained P80 case");
            cases=cases+1;
            $display("P80_TRANSPORT_CASE_PASS depth=%0d case=%0d fault=%0d cancel=%0d latency=%0d accepted=%0d",DEPTH,cases,fail_phase,cancel_mode,delay_cycles,accepted_total);
        end
    endtask
    initial begin
        repeat(3)@(negedge clk);#1;rst_n=1;
        run_case(0,0,1);
        run_case(1,0,2);run_case(2,0,2);run_case(3,0,2);run_case(4,0,2);
        run_case(0,1,2);run_case(0,2,12);
        // Global reset resets the actual bus model with the master. Soft cancel
        // above instead waits for every previously accepted response.
        @(negedge clk);#1;latency=12;start=1;
        @(negedge clk);#1;start=0;wait(q_occupancy==DEPTH);
        @(negedge clk);#1;rst_n=0;repeat(3)@(negedge clk);#1;rst_n=1;cases=cases+1;
        run_case(0,0,2);
        if(cases!=9 || peak_seen!=DEPTH || simultaneous==0 || final_ack_waits==0)
            $fatal(1,"P80 transport directed coverage incomplete");
        $display("P80_TRANSPORT_PROTOCOL_PASS depth=%0d cases=%0d peak=%0d simultaneous=%0d final_ack_waits=%0d independent_read_payload=true no_reset_restart=true",DEPTH,cases,peak_seen,simultaneous,final_ack_waits);
        $finish;
    end
endmodule
module tb_p80_transport2;tb_arch03_p80_transport #(.DEPTH(2)) test();endmodule
module tb_p80_transport4;tb_arch03_p80_transport #(.DEPTH(4)) test();endmodule
module tb_p80_transport8;tb_arch03_p80_transport #(.DEPTH(8)) test();endmodule
