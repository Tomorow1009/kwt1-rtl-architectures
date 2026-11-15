`timescale 1ns/1ps
// P80 team-added arbiter. The original fabric parameters remain unchanged.
// Accepted commands own an ordered response slot; grants rotate on acceptance.
// Only power-of-two metadata depths 2/4/8 are supported by the build contract.
module arch03_icb_arb2_queued #(parameter TRANSACTION_DEPTH=4)(
    input wire clk, rst_n,
    input wire cpu_cmd_valid, output wire cpu_cmd_ready,
    input wire [31:0] cpu_cmd_addr, input wire cpu_cmd_read,
    input wire [31:0] cpu_cmd_wdata, input wire [3:0] cpu_cmd_wmask,
    output wire cpu_rsp_valid, input wire cpu_rsp_ready,
    output wire [31:0] cpu_rsp_rdata, output wire cpu_rsp_err,
    input wire dma_cmd_valid, output wire dma_cmd_ready,
    input wire [31:0] dma_cmd_addr, input wire dma_cmd_read,
    input wire [31:0] dma_cmd_wdata, input wire [3:0] dma_cmd_wmask,
    output wire dma_rsp_valid, input wire dma_rsp_ready,
    output wire [31:0] dma_rsp_rdata, output wire dma_rsp_err,
    output wire cmd_valid, input wire cmd_ready,
    output wire [31:0] cmd_addr, output wire cmd_read,
    output wire [31:0] cmd_wdata, output wire [3:0] cmd_wmask,
    input wire rsp_valid, output wire rsp_ready,
    input wire [31:0] rsp_rdata, input wire rsp_err,
    output wire transaction_pending,
    output wire [3:0] accepted_queue_count
);
    localparam PTR_W=(TRANSACTION_DEPTH==2) ? 1 : (TRANSACTION_DEPTH==4) ? 2 : 3;
    reg owners[0:TRANSACTION_DEPTH-1];
    reg [PTR_W-1:0] write_ptr,read_ptr;
    reg [PTR_W:0] count;
    reg next_owner,held,held_owner;
    wire pending=count!=0;
    wire owner=pending ? owners[read_ptr] : 1'b0;
    wire retire=rsp_valid && rsp_ready;
    wire available=(count<TRANSACTION_DEPTH) || retire;
    wire selected=held ? held_owner :
        ((cpu_cmd_valid && dma_cmd_valid) ? next_owner : dma_cmd_valid);
    wire selected_valid=selected ? dma_cmd_valid : cpu_cmd_valid;
    wire accept=cmd_valid && cmd_ready;
    assign cmd_valid=rst_n && available && selected_valid;
    assign cmd_addr=selected ? dma_cmd_addr : cpu_cmd_addr;
    assign cmd_read=selected ? dma_cmd_read : cpu_cmd_read;
    assign cmd_wdata=selected ? dma_cmd_wdata : cpu_cmd_wdata;
    assign cmd_wmask=selected ? dma_cmd_wmask : cpu_cmd_wmask;
    assign cpu_cmd_ready=rst_n && available && !selected && cmd_ready;
    assign dma_cmd_ready=rst_n && available && selected && cmd_ready;
    assign cpu_rsp_valid=rst_n && pending && !owner && rsp_valid;
    assign dma_rsp_valid=rst_n && pending && owner && rsp_valid;
    assign cpu_rsp_rdata=rsp_rdata;
    assign dma_rsp_rdata=rsp_rdata;
    assign cpu_rsp_err=rsp_err;
    assign dma_rsp_err=rsp_err;
    assign rsp_ready=rst_n && pending && (owner ? dma_rsp_ready : cpu_rsp_ready);
    assign transaction_pending=pending || held;
    assign accepted_queue_count=count;

    always @(posedge clk or negedge rst_n) begin
        if(!rst_n) begin
            write_ptr<=0;read_ptr<=0;count<=0;
            next_owner<=0;held<=0;held_owner<=0;
        end else begin
            case({accept,retire})
                2'b10:count<=count+1'b1;
                2'b01:count<=count-1'b1;
            endcase
            if(retire) read_ptr<=read_ptr+1'b1;
            if(accept) begin
                owners[write_ptr]<=selected;write_ptr<=write_ptr+1'b1;
                next_owner<=!selected;held<=0;
            end else if(cmd_valid) begin
                held<=1;held_owner<=selected;
            end
        end
    end
endmodule
