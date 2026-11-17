`timescale 1ns/1ps
// P80 ordered accepted-transaction metadata, original fabric parameters.
// Only actual shared-SRAM read responses enter the decoder FIFO.
// In-order successful write ACKs publish a prefix of readable addresses.
module arch03_g32_transport #(parameter SOURCE_CREDITS=3,TRANSACTION_DEPTH=4,ICG_BYPASS=0)(
    input wire clk,rst_n,start,cancel,
    input wire [31:0] source_addr,input_addr,encoded_bytes,
    input wire output_valid,output wire output_ready,
    input wire [31:0] output_addr,output_data,
    output wire committed_valid,input wire committed_ready,
    output wire [31:0] committed_data,
    output reg cmd_valid,input wire cmd_ready,
    output reg [31:0] cmd_addr,output reg cmd_read,
    output reg [31:0] cmd_wdata,output wire [3:0] cmd_wmask,
    input wire rsp_valid,output wire rsp_ready,
    input wire [31:0] rsp_rdata,input wire rsp_err,
    output reg busy,done,aborted,error,
    output reg [31:0] error_addr,output reg [3:0] error_kind,
    output reg [31:0] source_acks,stage_acks,read_acks,output_acks,decoded_words,
    output wire draining, transaction_pending,
    output wire [2:0] pending_kind_status,
    output wire [5:0] output_fifo_count,
    output reg [31:0] offered_cycles,response_wait_cycles,turnovers,
    output wire [3:0] accepted_queue_count,
    output reg [3:0] accepted_queue_peak,
    output reg [31:0] accepted_credit_stalls
);
    localparam K_SOURCE=1,K_STAGE=2,K_READ=3,K_OUTPUT=4;
    reg [31:0] source_q,input_q,words_q,source_next,stage_next,read_next;
    localparam PTR_W=(TRANSACTION_DEPTH==2) ? 1 : (TRANSACTION_DEPTH==4) ? 2 : 3;
    reg stopping;
    reg [2:0] cmd_kind;
    reg [2:0] accepted_kind[0:TRANSACTION_DEPTH-1];
    reg [31:0] accepted_addr[0:TRANSACTION_DEPTH-1];
    reg [PTR_W-1:0] accepted_wr,accepted_rd;
    reg [PTR_W:0] accepted_count;
    wire pending=accepted_count!=0;
    wire [2:0] pending_kind=pending ? accepted_kind[accepted_rd] : 3'd0;
    wire [31:0] pending_addr=pending ? accepted_addr[accepted_rd] : 32'd0;
    assign accepted_queue_count=accepted_count;
    reg [31:0] source_fifo[0:15],commit_fifo[0:15];
    reg [3:0] source_wr,source_rd,commit_wr,commit_rd;
    reg [4:0] source_count,commit_count,source_reserved,commit_reserved;
    reg [31:0] output_fifo_data[0:31],output_fifo_addr[0:31];
    reg [4:0] output_wr,output_rd;
    reg [5:0] output_count;
    reg [31:0] queue_addr[0:7],queue_data[0:7];
    reg [2:0] queue_kind[0:7],queue_wr,queue_rd;
    reg [3:0] queue_count;
    wire fire=cmd_valid && cmd_ready;
    assign rsp_ready=rst_n && pending;
    wire response=rsp_valid && rsp_ready;
    wire bus_fault=response && rsp_err;
    wire stop=stopping || cancel || error || bus_fault;
    assign draining=stopping;
    assign transaction_pending=pending;
    assign pending_kind_status=pending_kind;
    assign output_fifo_count=output_count;
    assign cmd_wmask=cmd_read ? 4'b0 : 4'hf;
    assign output_ready=rst_n && busy && !stop && output_count<32;
    wire output_push=output_valid && output_ready;
    assign committed_valid=rst_n && busy && !stop && commit_count!=0;
    assign committed_data=commit_fifo[commit_rd];
    wire commit_pop=committed_valid && committed_ready;
    wire source_push=response && !rsp_err && pending_kind==K_SOURCE && !stop;
    wire commit_push=response && !rsp_err && pending_kind==K_READ && !stop;
    // The next descriptor is already stored before it can become externally
    // valid. Its payload never depends combinationally on a returning response.
    // Reserve a metadata credit before presenting a registered command.
    // An externally held command can therefore never lose VALID to queue-full.
    wire [PTR_W+1:0] accepted_after_edge={1'b0,accepted_count} +
        (fire ? 1'b1 : 1'b0) - (response ? 1'b1 : 1'b0);
    wire offer_credit=accepted_after_edge<TRANSACTION_DEPTH;
    wire present=busy && !stop && queue_count!=0 && (!cmd_valid || fire) && offer_credit;
    reg [2:0] enqueue_kind;
    always @* begin
        enqueue_kind=0;
        if(busy && !stop && queue_count<8) begin
            if(output_count>=24) enqueue_kind=K_OUTPUT;
            else if(read_next<stage_acks) enqueue_kind=K_READ;
            else if(source_count!=0 && commit_reserved<16) enqueue_kind=K_STAGE;
            else if(source_next<words_q && source_reserved<SOURCE_CREDITS) enqueue_kind=K_SOURCE;
            else if(output_count!=0) enqueue_kind=K_OUTPUT;
        end
    end
    wire enqueue=enqueue_kind!=0;
    wire stage_enqueue=enqueue_kind==K_STAGE;
    wire source_enqueue=enqueue_kind==K_SOURCE;
    wire output_enqueue=enqueue_kind==K_OUTPUT;
    wire empty=!pending && !cmd_valid && queue_count==0 && source_count==0 &&
        commit_count==0 && output_count==0 && source_reserved==0 && commit_reserved==0;
    // Only FIFO numeric storage is gated; pointer, credit, ownership and
    // response logic retain the original free-running clock and enables.
    genvar gi;
    generate
        for(gi=0;gi<16;gi=gi+1)begin:source_data_gates
            wire data_clk;
            wire write_data=rst_n && busy && source_push && source_wr==gi;
            arch03_g32_icg gate(.clk(clk),.enable(write_data),.bypass(ICG_BYPASS!=0),.gated_clk(data_clk));
            always @(posedge data_clk)if(write_data)source_fifo[gi]<=rsp_rdata;
        end
        for(gi=0;gi<16;gi=gi+1)begin:commit_data_gates
            wire data_clk;
            wire write_data=rst_n && busy && commit_push && commit_wr==gi;
            arch03_g32_icg gate(.clk(clk),.enable(write_data),.bypass(ICG_BYPASS!=0),.gated_clk(data_clk));
            always @(posedge data_clk)if(write_data)commit_fifo[gi]<=rsp_rdata;
        end
        for(gi=0;gi<32;gi=gi+1)begin:output_data_gates
            wire data_clk;
            wire write_data=rst_n && busy && output_push && output_wr==gi;
            arch03_g32_icg gate(.clk(clk),.enable(write_data),.bypass(ICG_BYPASS!=0),.gated_clk(data_clk));
            always @(posedge data_clk)if(write_data)output_fifo_data[gi]<=output_data;
        end
    endgenerate
    always @(posedge clk or negedge rst_n) begin
        if(!rst_n) begin
            busy<=0;done<=0;aborted<=0;error<=0;error_addr<=0;error_kind<=0;
            source_q<=0;input_q<=0;words_q<=0;source_next<=0;stage_next<=0;read_next<=0;
            stopping<=0;accepted_count<=0;accepted_wr<=0;accepted_rd<=0;cmd_valid<=0;cmd_addr<=0;cmd_read<=1;cmd_wdata<=0;cmd_kind<=0;
            accepted_queue_peak<=0;accepted_credit_stalls<=0;
            source_wr<=0;source_rd<=0;commit_wr<=0;commit_rd<=0;
            source_count<=0;commit_count<=0;source_reserved<=0;commit_reserved<=0;
            output_wr<=0;output_rd<=0;output_count<=0;queue_wr<=0;queue_rd<=0;queue_count<=0;
            source_acks<=0;stage_acks<=0;read_acks<=0;output_acks<=0;decoded_words<=0;
            offered_cycles<=0;response_wait_cycles<=0;turnovers<=0;
        end else begin
            done<=0;aborted<=0;
            if(start && !busy && !pending && !cmd_valid) begin
                busy<=1;stopping<=0;error<=0;error_addr<=0;error_kind<=0;
                accepted_count<=0;accepted_wr<=0;accepted_rd<=0;
                accepted_queue_peak<=0;accepted_credit_stalls<=0;
                source_q<=source_addr;input_q<=input_addr;words_q<=encoded_bytes>>2;
                source_next<=0;stage_next<=0;read_next<=0;source_wr<=0;source_rd<=0;commit_wr<=0;commit_rd<=0;
                source_count<=0;commit_count<=0;source_reserved<=0;commit_reserved<=0;
                output_wr<=0;output_rd<=0;output_count<=0;queue_wr<=0;queue_rd<=0;queue_count<=0;
                source_acks<=0;stage_acks<=0;read_acks<=0;output_acks<=0;decoded_words<=0;
                offered_cycles<=0;response_wait_cycles<=0;turnovers<=0;
            end
            if(busy) begin
                if(cmd_valid && !cmd_ready)offered_cycles<=offered_cycles+1;
                if(pending && !rsp_valid)response_wait_cycles<=response_wait_cycles+1;
                if(response && fire)turnovers<=turnovers+1;
                if(!stop && queue_count!=0 && (!cmd_valid || fire) && !offer_credit)
                    accepted_credit_stalls<=accepted_credit_stalls+1;
                if(accepted_after_edge>accepted_queue_peak) accepted_queue_peak<=accepted_after_edge;
                case({fire,response})
                    2'b10:accepted_count<=accepted_count+1'b1;
                    2'b01:accepted_count<=accepted_count-1'b1;
                endcase
                case({enqueue,present})
                    2'b10:queue_count<=queue_count+1'b1;
                    2'b01:queue_count<=queue_count-1'b1;
                endcase
                if(enqueue) begin
                    queue_kind[queue_wr]<=enqueue_kind;queue_wr<=queue_wr+1'b1;
                    case(enqueue_kind)
                        K_SOURCE: begin
                            queue_addr[queue_wr]<=source_q+(source_next<<2);queue_data[queue_wr]<=0;
                            source_next<=source_next+1;
                        end
                        K_STAGE: begin
                            queue_addr[queue_wr]<=input_q+(stage_next<<2);queue_data[queue_wr]<=source_fifo[source_rd];
                            stage_next<=stage_next+1;source_rd<=source_rd+1'b1;
                        end
                        K_READ: begin
                            // read_next is strictly below the committed write prefix.
                            queue_addr[queue_wr]<=input_q+(read_next<<2);queue_data[queue_wr]<=0;
                            read_next<=read_next+1;
                        end
                        K_OUTPUT: begin
                            queue_addr[queue_wr]<=output_fifo_addr[output_rd];queue_data[queue_wr]<=output_fifo_data[output_rd];
                            output_rd<=output_rd+1'b1;
                        end
                    endcase
                end
                case({source_push,stage_enqueue})
                    2'b10:source_count<=source_count+1'b1;
                    2'b01:source_count<=source_count-1'b1;
                endcase
                case({source_enqueue,stage_enqueue})
                    2'b10:source_reserved<=source_reserved+1'b1;
                    2'b01:source_reserved<=source_reserved-1'b1;
                endcase
                case({commit_push,commit_pop})
                    2'b10:commit_count<=commit_count+1'b1;
                    2'b01:commit_count<=commit_count-1'b1;
                endcase
                case({stage_enqueue,commit_pop})
                    2'b10:commit_reserved<=commit_reserved+1'b1;
                    2'b01:commit_reserved<=commit_reserved-1'b1;
                endcase
                case({output_push,output_enqueue})
                    2'b10:output_count<=output_count+1'b1;
                    2'b01:output_count<=output_count-1'b1;
                endcase
                if(output_push) begin
                    output_fifo_addr[output_wr]<=output_addr;
                    output_wr<=output_wr+1'b1;
                end
                if(source_push) begin source_wr<=source_wr+1'b1;end
                if(commit_push) begin commit_wr<=commit_wr+1'b1;end
                if(commit_pop) begin commit_rd<=commit_rd+1'b1;decoded_words<=decoded_words+1;end
                if(response) begin
                    accepted_rd<=accepted_rd+1'b1;
                    if(!rsp_err) case(pending_kind)
                        K_SOURCE:source_acks<=source_acks+1;
                        K_STAGE:stage_acks<=stage_acks+1;
                        K_READ:read_acks<=read_acks+1;
                        K_OUTPUT:output_acks<=output_acks+1;
                    endcase
                end
                // Responses use the old FIFO head, including same-edge retirement/acceptance.
                if(fire) begin
                    cmd_valid<=0;
                    accepted_kind[accepted_wr]<=cmd_kind;accepted_addr[accepted_wr]<=cmd_addr;
                    accepted_wr<=accepted_wr+1'b1;
                end
                if(present) begin
                    cmd_valid<=1;cmd_addr<=queue_addr[queue_rd];cmd_wdata<=queue_data[queue_rd];
                    cmd_kind<=queue_kind[queue_rd];cmd_read<=queue_kind[queue_rd]==K_SOURCE || queue_kind[queue_rd]==K_READ;
                    queue_rd<=queue_rd+1'b1;
                end
                if(!stop && source_acks==words_q && stage_acks==words_q && read_acks==words_q && decoded_words==words_q &&
                   output_acks==12672 && empty) begin busy<=0;done<=1;end
                if(cancel || bus_fault) begin
                    stopping<=1;
                    // Discard unpresented descriptors; an already offered valid
                    // must survive cancellation until it is accepted and drained.
                    queue_count<=0;queue_rd<=queue_wr;
                end
                if(bus_fault && !error) begin error<=1;error_addr<=pending_addr;error_kind<=pending_kind;end
                if(stopping && !pending && !cmd_valid) begin
                    busy<=0;stopping<=0;aborted<=1;queue_count<=0;
                    source_count<=0;commit_count<=0;output_count<=0;source_reserved<=0;commit_reserved<=0;
                end
            end
        end
    end
endmodule
