`timescale 1ns/1fs
// Passive, simulation-only task observer. Never drives a DUT signal.
// START is the first source read VALID assertion, including the interval from
// the sending edge to its first possible acceptance edge. The event observer
// sees NBA-generated VALID at its actual assertion time; sampling only VALID
// at the next posedge would discard that first cycle. start_cycle is the most
// recent sending-edge index; start_ns retains the actual (including gate delay)
// event time. END is the last related response ACK. FINISHED may be later,
// while pending/FIFO state proves that ACK was the final transaction; that
// observation delay must not be added to the measured response endpoint.
module arch03_task_window_p80 #(
    parameter [31:0] SOURCE_BASE=32'hb0000000,
    parameter [31:0] INPUT_BASE=32'ha0000000,
    parameter [31:0] OUTPUT_BASE=32'ha000c000,
    parameter integer MAX_INPUT_WORDS=11752, OUTPUT_BYTES=50688, MAX_OUTSTANDING=8
)(
    input wire clk,rst_n,task_arm,task_cancel,
    input wire [31:0] encoded_bytes,
    input wire cmd_valid,cmd_ready,cmd_read,
    input wire [31:0] cmd_addr,input wire [3:0] cmd_wmask,
    input wire rsp_valid,rsp_ready,rsp_err,
    input wire global_pending,fifo_empty,core_done,
    output reg active=0,finished=0,failed=0,
    output reg [31:0] failure_code=0,
    output reg [63:0] start_cycle=0,end_cycle=0,
    output wire [63:0] window_cycles,
    output reg [31:0] source_read_acks=0,input_write_acks=0,input_read_acks=0,output_write_acks=0,
    output reg [63:0] command_wait_cycles=0,response_wait_cycles=0
);
    localparam integer OUTPUT_WORDS=OUTPUT_BYTES/4;
    reg [31:0] bytes_q=0;
    wire [31:0] input_words=bytes_q/4;
    localparam K_SOURCE=1,K_INPUT_WRITE=2,K_INPUT_READ=3,K_OUTPUT=4,K_INVALID=5;
    // Codes: 1 arm while busy, 2 transfer before source/start, 3 outstanding
    // metadata overflow, 4 orphan response, 5 bus error, 6 address/mask, 7 duplicate,
    // 8 input not committed, 9 incomplete counts, 10 premature core done,
    // 11 cancellation, 12 command after complete output coverage.
    reg armed=0,start_seen=0,core_done_seen=0;
    reg source_seen[0:MAX_INPUT_WORDS-1];
    reg input_written[0:MAX_INPUT_WORDS-1];
    reg input_read[0:MAX_INPUT_WORDS-1];
    reg output_seen[0:OUTPUT_WORDS-1];
    reg [63:0] cycle_index=0;
    reg [63:0] last_response_cycle=0;
    integer outstanding=0,pending_kind=0,pending_index=0,i,kind,index;
    integer pending_wr=0,pending_rd=0;
    integer accepted_kind[0:MAX_OUTSTANDING-1],accepted_index[0:MAX_OUTSTANDING-1];
    realtime start_ns=0,end_ns=0,last_response_ns=0,finished_ns=0;
    wire source_address=cmd_addr>=SOURCE_BASE &&
        {1'b0,cmd_addr}<{1'b0,SOURCE_BASE}+bytes_q;
    wire input_address=cmd_addr>=INPUT_BASE &&
        {1'b0,cmd_addr}<{1'b0,INPUT_BASE}+bytes_q;
    wire output_address=cmd_addr>=OUTPUT_BASE &&
        {1'b0,cmd_addr}<{1'b0,OUTPUT_BASE}+OUTPUT_BYTES;
    assign window_cycles=start_seen ? (finished ? end_cycle-start_cycle : cycle_index-start_cycle) : 64'b0;
    task reject(input [31:0] code);
        begin if(!failed) begin failed=1;failure_code=code;end end
    endtask
    // This is an event monitor, deliberately not always_ff/synthesizable RTL.
    always @(cmd_valid or cmd_addr or cmd_read) begin
        if(rst_n && finished && !armed && cmd_valid) reject(12);
        if(rst_n && armed && !start_seen && cmd_valid && cmd_read &&
            cmd_addr>=SOURCE_BASE && {1'b0,cmd_addr}<{1'b0,SOURCE_BASE}+bytes_q) begin
            start_seen=1;active=1;start_cycle=cycle_index;start_ns=$realtime;
        end
    end
    // Interface state may drain in the NBA region of the final ACK edge, or
    // later through real gate propagation. Do not postpone END one extra edge.
    always @(armed or failed or outstanding or global_pending or fifo_empty or
             core_done_seen or output_write_acks or source_read_acks or
             input_write_acks or input_read_acks or cmd_valid) begin
        if(rst_n && armed && !finished && outstanding==0 && !cmd_valid && !global_pending && fifo_empty) begin
            if(failed || (start_seen && core_done_seen && output_write_acks==OUTPUT_WORDS &&
                source_read_acks==input_words && input_write_acks==input_words && input_read_acks==input_words)) begin
                end_cycle=start_seen ? (last_response_cycle>=start_cycle ? last_response_cycle : cycle_index) : 0;
                end_ns=start_seen && last_response_cycle>=start_cycle ? last_response_ns : $realtime;
                finished_ns=$realtime;
                active=0;finished=1;armed=0;
                $display("ICB32_TASK_WINDOW finished=1 failed=%0d failure_code=%0d start_cycle=%0d end_cycle=%0d cycles=%0d start_ns=%.6f end_ns=%.6f finished_cycle=%0d finished_ns=%.6f source_bytes=%0d input_write_bytes=%0d input_read_bytes=%0d output_bytes=%0d",failed,failure_code,start_cycle,end_cycle,end_cycle-start_cycle,start_ns,end_ns,cycle_index,finished_ns,source_read_acks*4,input_write_acks*4,input_read_acks*4,output_write_acks*4);
            end
        end
    end
    always @(posedge clk or negedge rst_n) begin
        if(!rst_n) begin
            cycle_index=0;armed=0;start_seen=0;active=0;finished=0;failed=0;failure_code=0;
            start_cycle=0;end_cycle=0;start_ns=0;end_ns=0;last_response_cycle=0;last_response_ns=0;finished_ns=0;outstanding=0;pending_kind=0;pending_index=0;pending_wr=0;pending_rd=0;
            source_read_acks=0;input_write_acks=0;input_read_acks=0;output_write_acks=0;
            command_wait_cycles=0;response_wait_cycles=0;core_done_seen=0;
            for(i=0;i<MAX_INPUT_WORDS;i=i+1) begin source_seen[i]=0;input_written[i]=0;input_read[i]=0;end
            for(i=0;i<OUTPUT_WORDS;i=i+1) output_seen[i]=0;
        end else begin
            cycle_index=cycle_index+1;
            if(!task_arm && finished && !armed && rsp_valid && rsp_ready) reject(4);
            if(task_arm) begin
                if(armed || active || outstanding!=0 || global_pending || !fifo_empty || cmd_valid) reject(1);
                else begin
                    bytes_q=encoded_bytes;
                    armed=1;start_seen=0;active=0;finished=0;failed=0;failure_code=0;
                    start_cycle=0;end_cycle=0;start_ns=0;end_ns=0;last_response_cycle=0;last_response_ns=0;finished_ns=0;outstanding=0;pending_kind=0;pending_index=0;pending_wr=0;pending_rd=0;
                    source_read_acks=0;input_write_acks=0;input_read_acks=0;output_write_acks=0;
                    command_wait_cycles=0;response_wait_cycles=0;core_done_seen=0;
                    for(i=0;i<MAX_INPUT_WORDS;i=i+1) begin source_seen[i]=0;input_written[i]=0;input_read[i]=0;end
                    for(i=0;i<OUTPUT_WORDS;i=i+1) output_seen[i]=0;
                    if(encoded_bytes<32 || encoded_bytes>MAX_INPUT_WORDS*4 || encoded_bytes%4) reject(6);
                end
            end
            if(armed && !task_arm) begin
                if(task_cancel) reject(11);
                if(active && cmd_valid && !cmd_ready) command_wait_cycles=command_wait_cycles+1;
                if(active && rsp_valid && !rsp_ready) response_wait_cycles=response_wait_cycles+1;
                // Responses retire before a possible simultaneous next command.
                if(rsp_valid && rsp_ready) begin
                    last_response_cycle=cycle_index;last_response_ns=$realtime;
                    if(outstanding==0) reject(4);
                    else begin
                        pending_kind=accepted_kind[pending_rd];pending_index=accepted_index[pending_rd];
                        pending_rd=(pending_rd+1)%MAX_OUTSTANDING;
                        outstanding=outstanding-1;
                        if(rsp_err) reject(5);
                        else if(!failed) begin
                            case(pending_kind)
                                K_SOURCE: begin
                                    if(source_seen[pending_index]) reject(7);
                                    source_seen[pending_index]=1;source_read_acks=source_read_acks+1;
                                end
                                K_INPUT_WRITE: begin
                                    if(input_written[pending_index]) reject(7);
                                    if(!source_seen[pending_index]) reject(8);
                                    input_written[pending_index]=1;input_write_acks=input_write_acks+1;
                                end
                                K_INPUT_READ: begin
                                    if(input_read[pending_index]) reject(7);
                                    if(!input_written[pending_index]) reject(8);
                                    input_read[pending_index]=1;input_read_acks=input_read_acks+1;
                                end
                                K_OUTPUT: begin
                                    if(output_seen[pending_index]) reject(7);
                                    output_seen[pending_index]=1;output_write_acks=output_write_acks+1;
                                    if(output_write_acks==OUTPUT_WORDS && (source_read_acks!=input_words ||
                                        input_write_acks!=input_words || input_read_acks!=input_words)) reject(9);
                                end
                                default: reject(6);
                            endcase
                        end
                    end
                end
                if(cmd_valid && cmd_ready) begin
                    if(!start_seen) reject(2);
                    if(outstanding>=MAX_OUTSTANDING) reject(3);
                    if(output_write_acks==OUTPUT_WORDS) reject(12);
                    kind=K_INVALID;index=0;
                    if(cmd_addr[1:0]!=0 || (!cmd_read && cmd_wmask!=4'hf)) reject(6);
                    else if(source_address && cmd_read) begin kind=K_SOURCE;index=(cmd_addr-SOURCE_BASE)/4;end
                    else if(input_address) begin
                        kind=cmd_read ? K_INPUT_READ : K_INPUT_WRITE;index=(cmd_addr-INPUT_BASE)/4;
                        if(cmd_read && !input_written[index]) reject(8);
                    end else if(output_address && !cmd_read) begin kind=K_OUTPUT;index=(cmd_addr-OUTPUT_BASE)/4;end
                    else reject(6);
                    if(outstanding<MAX_OUTSTANDING) begin
                        accepted_kind[pending_wr]=kind;accepted_index[pending_wr]=index;
                        pending_wr=(pending_wr+1)%MAX_OUTSTANDING;
                    end
                    // An illegal over-capacity acceptance still has a real
                    // response to drain. Coverage is already rejected, but do
                    // not publish a failed completion before that response.
                    outstanding=outstanding+1;
                end
                if(core_done) begin
                    core_done_seen=1;
                    if(input_read_acks!=input_words) reject(10);
                end
            end
        end
    end
    initial begin
        if(MAX_INPUT_WORDS<=0 || OUTPUT_BYTES<=0 || OUTPUT_BYTES%4 ||
            (MAX_OUTSTANDING!=2 && MAX_OUTSTANDING!=4 && MAX_OUTSTANDING!=8))
            $fatal(1,"Invalid DMA16 window geometry");
    end
endmodule
