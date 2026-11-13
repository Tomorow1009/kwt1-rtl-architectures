`timescale 1ns/1ps
// Isolated protocol stress. Distinct source/read data deliberately detects any
// accidental write-ACK forwarding; full-matrix tests use the actual SRAM RTL.
module tb_arch03_t80_transport;
    reg clk=0,rst_n=0,start=0,cancel=0;
    always #3 clk=~clk;
    wire cmd_valid,cmd_ready,cmd_read,rsp_ready,busy,done,aborted,error;
    wire [31:0] cmd_addr,cmd_wdata,committed_data,error_addr;
    wire [3:0] cmd_wmask,error_kind;
    wire committed_valid,committed_ready,output_ready;
    wire [31:0] source_acks,stage_acks,read_acks,output_acks,decoded_words;
    wire draining,transaction_pending;
    wire [2:0] pending_kind_status;
    wire [5:0] output_fifo_count;
    wire [31:0] offered_cycles,response_wait_cycles,turnovers;
    integer tick=0,out_count=0,consume_count=0,latency=1,fault_kind=0,cases=0;
    reg slave_pending=0,fault_seen=0,hold_read=0;
    integer delay_left=0,slave_kind=0;
    reg [31:0] slave_addr=0,slave_data=0,read_data=0;
    reg [31:0] memory[0:15];
    reg written[0:15];
    wire rsp_valid=slave_pending && delay_left==0;
    wire rsp_err=rsp_valid && fault_kind==slave_kind && !fault_seen;
    wire [31:0] rsp_rdata=read_data;
    wire is_readback=cmd_read && cmd_addr[31:16]==16'ha000;
    assign cmd_ready=(!slave_pending || (rsp_valid && rsp_ready)) &&
        tick%5!=0 && !(hold_read && is_readback);
    assign committed_ready=tick%7!=0;
    wire output_valid=busy && out_count<12672 && tick%4!=0;
    wire [31:0] output_addr=32'ha000c000+out_count*4;
    wire [31:0] output_data=32'h12340000+out_count;
    arch03_t80_transport dut(.clk(clk),.rst_n(rst_n),.start(start),.cancel(cancel),
        .source_addr(32'hb0000000),.input_addr(32'ha0000000),.encoded_bytes(32'd64),
        .output_valid(output_valid),.output_ready(output_ready),.output_addr(output_addr),.output_data(output_data),
        .committed_valid(committed_valid),.committed_ready(committed_ready),.committed_data(committed_data),
        .cmd_valid(cmd_valid),.cmd_ready(cmd_ready),.cmd_addr(cmd_addr),.cmd_read(cmd_read),
        .cmd_wdata(cmd_wdata),.cmd_wmask(cmd_wmask),.rsp_valid(rsp_valid),.rsp_ready(rsp_ready),
        .rsp_rdata(rsp_rdata),.rsp_err(rsp_err),.busy(busy),.done(done),.aborted(aborted),.error(error),
        .error_addr(error_addr),.error_kind(error_kind),.source_acks(source_acks),.stage_acks(stage_acks),
        .read_acks(read_acks),.output_acks(output_acks),.decoded_words(decoded_words),
        .draining(draining),.transaction_pending(transaction_pending),.pending_kind_status(pending_kind_status),
        .output_fifo_count(output_fifo_count),.offered_cycles(offered_cycles),
        .response_wait_cycles(response_wait_cycles),.turnovers(turnovers));
    function [31:0] source_word(input integer index);
        source_word=32'hbeef0100+index;
    endfunction
    function [31:0] shared_word(input integer index);
        shared_word=source_word(index)^32'h55aa55aa;
    endfunction
    reg held=0;
    reg [68:0] held_payload;
    integer k,index;
    always @(posedge clk) begin
        tick<=tick+1;
        if(rst_n)begin
            if(held && (!cmd_valid || {cmd_addr,cmd_read,cmd_wdata,cmd_wmask}!==held_payload))
                $fatal(1,"T80 request changed under backpressure/cancel");
            held<=cmd_valid && !cmd_ready;held_payload<={cmd_addr,cmd_read,cmd_wdata,cmd_wmask};
            if(start)begin
                out_count<=0;consume_count<=0;fault_seen<=0;
                for(k=0;k<16;k=k+1)written[k]<=0;
            end else begin
                if(output_valid && output_ready)out_count<=out_count+1;
                if(committed_valid && committed_ready)begin
                    if(consume_count>=16 || committed_data!==shared_word(consume_count) ||
                        read_acks<=consume_count)$fatal(1,"Decoder did not consume real read response");
                    consume_count<=consume_count+1;
                end
            end
            if(slave_pending && delay_left>0)delay_left<=delay_left-1;
            if(rsp_valid && rsp_ready)begin
                slave_pending<=0;
                if(rsp_err)fault_seen<=1;
                else if(slave_kind==2)begin
                    index=(slave_addr-32'ha0000000)/4;
                    if(slave_data!==source_word(index))$fatal(1,"Wrong staged source data");
                    // Model a legal independently changed shared value; this
                    // distinguishes read-response data from retained write data.
                    memory[index]<=shared_word(index);written[index]<=1;
                end
            end
            if(cmd_valid && cmd_ready)begin
                if(slave_pending && !(rsp_valid && rsp_ready))$fatal(1,"More than one outstanding");
                slave_pending<=1;slave_addr<=cmd_addr;slave_data<=cmd_wdata;
                delay_left<=latency+tick%3;
                if(cmd_addr>=32'hb0000000)begin
                    slave_kind<=1;read_data<=source_word((cmd_addr-32'hb0000000)/4);
                    if(!cmd_read)$fatal(1,"Write to source");
                end else if(cmd_addr<32'ha000c000)begin
                    index=(cmd_addr-32'ha0000000)/4;
                    if(index>=16)$fatal(1,"Input address out of range");
                    slave_kind<=cmd_read ? 3 : 2;
                    if(cmd_read)begin
                        if(!written[index])$fatal(1,"Read accepted before write ACK");
                        read_data<=memory[index];
                    end
                end else begin
                    slave_kind<=4;
                    if(cmd_read || cmd_wmask!=15)$fatal(1,"Wrong output transaction");
                end
            end
            if(done && (slave_pending || cmd_valid || transaction_pending ||
                output_acks!=12672 || source_acks!=16 || stage_acks!=16 || read_acks!=16 ||
                decoded_words!=16 || consume_count!=16))$fatal(1,"Premature DONE");
        end
        if(tick>3000000)$fatal(1,"Protocol stress timeout");
    end
    task run_case(input integer fail_phase,input bit cancel_read,input integer read_latency);
        begin
            @(negedge clk);fault_kind=fail_phase;latency=read_latency;hold_read=cancel_read;start=1;
            @(negedge clk);start=0;
            if(cancel_read)begin
                wait(cmd_valid && is_readback && !cmd_ready);
                @(negedge clk);cancel=1;
                repeat(7)@(negedge clk);
                if(!cmd_valid || !busy)$fatal(1,"Cancel withdrew held read");
                hold_read=0;
                wait(aborted);@(negedge clk);cancel=0;
            end else if(fail_phase!=0)begin
                wait(aborted);@(negedge clk);
                if(!error || error_kind!=fail_phase || !fault_seen)$fatal(1,"Wrong error phase/drain");
            end else begin
                wait(done);@(negedge clk);
                if(error || aborted)$fatal(1,"Unexpected full-run failure");
            end
            repeat(4)@(negedge clk);
            if(busy || cmd_valid || slave_pending || transaction_pending)$fatal(1,"Undrained case");
            cases=cases+1;
            $display("T80_TRANSPORT_CASE_PASS case=%0d fault=%0d cancel_held_read=%0d latency=%0d",cases,fail_phase,cancel_read,read_latency);
        end
    endtask
    initial begin
        repeat(3)@(negedge clk);rst_n=1;
        run_case(0,0,1);
        run_case(1,0,2);run_case(2,0,2);run_case(3,0,2);run_case(4,0,2);
        run_case(0,1,2);
        run_case(0,0,2);
        $display("T80_TRANSPORT_PROTOCOL_PASS cases=%0d independent_read_payload=true no_reset_restart=true",cases);
        $finish;
    end
endmodule
