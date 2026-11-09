`timescale 1ns/1ps
// Two original-system ICB masters, one transaction globally outstanding.
// A stalled grant is retained through acceptance, and response ownership is
// retained through response consumption. No zero-cycle slave response assumed.
module arch03_icb_arb2(
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
    output wire transaction_pending
);
    reg pending, owner, next_owner, held, held_owner;
    wire selected=held ? held_owner :
        ((cpu_cmd_valid && dma_cmd_valid) ? next_owner : dma_cmd_valid);
    wire selected_valid=selected ? dma_cmd_valid : cpu_cmd_valid;
    assign cmd_valid=rst_n && !pending && selected_valid;
    assign cmd_addr=selected ? dma_cmd_addr : cpu_cmd_addr;
    assign cmd_read=selected ? dma_cmd_read : cpu_cmd_read;
    assign cmd_wdata=selected ? dma_cmd_wdata : cpu_cmd_wdata;
    assign cmd_wmask=selected ? dma_cmd_wmask : cpu_cmd_wmask;
    assign cpu_cmd_ready=rst_n && !pending && !selected && cmd_ready;
    assign dma_cmd_ready=rst_n && !pending && selected && cmd_ready;
    assign cpu_rsp_valid=rst_n && pending && !owner && rsp_valid;
    assign dma_rsp_valid=rst_n && pending && owner && rsp_valid;
    assign cpu_rsp_rdata=rsp_rdata;
    assign dma_rsp_rdata=rsp_rdata;
    assign cpu_rsp_err=rsp_err;
    assign dma_rsp_err=rsp_err;
    assign rsp_ready=rst_n && pending && (owner ? dma_rsp_ready : cpu_rsp_ready);
    assign transaction_pending=pending || held;
    always @(posedge clk or negedge rst_n) begin
        if(!rst_n) begin pending<=0;owner<=0;next_owner<=0;held<=0;held_owner<=0;end
        else begin
            if(cmd_valid) begin
                if(cmd_ready) begin pending<=1;owner<=selected;held<=0;end
                else begin held<=1;held_owner<=selected;end
            end
            if(rsp_valid && rsp_ready) begin
                pending<=0;next_owner<=!owner;
            end
        end
    end
endmodule
