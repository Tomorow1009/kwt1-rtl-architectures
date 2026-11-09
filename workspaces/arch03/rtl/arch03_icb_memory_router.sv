`timescale 1ns/1ps
// Restore the existing SysMem interface as a read-only loading source, while
// retaining CPU/DMA access to the prescribed shared SRAM through the same bus.
module arch03_icb_memory_router #(
    parameter [31:0] SHARED_BASE=32'ha0000000,
    parameter [31:0] SOURCE_BASE=32'hb0000000,
    parameter [31:0] SOURCE_BYTES=32'd46976
)(
    input wire clk,rst_n,
    input wire cmd_valid, output wire cmd_ready,
    input wire [31:0] cmd_addr, input wire cmd_read,
    input wire [31:0] cmd_wdata, input wire [3:0] cmd_wmask,
    output wire rsp_valid, input wire rsp_ready,
    output wire [31:0] rsp_rdata, output wire rsp_err,
    output wire mem_cmd_valid, input wire mem_cmd_ready,
    output wire [31:0] mem_cmd_addr, output wire mem_cmd_read,
    output wire [31:0] mem_cmd_wdata, output wire [3:0] mem_cmd_wmask,
    input wire mem_rsp_valid, output wire mem_rsp_ready,
    input wire [31:0] mem_rsp_rdata, input wire mem_rsp_err,
    output wire src_cmd_valid, input wire src_cmd_ready,
    output wire [31:0] src_cmd_addr, output wire src_cmd_read,
    output wire [31:0] src_cmd_wdata, output wire [3:0] src_cmd_wmask,
    input wire src_rsp_valid, output wire src_rsp_ready,
    input wire [31:0] src_rsp_rdata, input wire src_rsp_err,
    output wire transaction_pending
);
    localparam DEST_MEMORY=0,DEST_SOURCE=1,DEST_ERROR=2;
    reg pending;
    reg [1:0] destination;
    wire shared_selected=cmd_addr[31:19]==SHARED_BASE[31:19];
    wire source_selected=cmd_addr>=SOURCE_BASE &&
        ({1'b0,cmd_addr}<{1'b0,SOURCE_BASE}+{1'b0,SOURCE_BYTES}) &&
        cmd_read && cmd_addr[1:0]==0;
    wire [1:0] requested=shared_selected ? DEST_MEMORY :
        (source_selected ? DEST_SOURCE : DEST_ERROR);
    assign cmd_ready=rst_n && !pending &&
        (requested==DEST_MEMORY ? mem_cmd_ready :
         requested==DEST_SOURCE ? src_cmd_ready : 1'b1);
    assign mem_cmd_valid=rst_n && !pending && cmd_valid && requested==DEST_MEMORY;
    assign src_cmd_valid=rst_n && !pending && cmd_valid && requested==DEST_SOURCE;
    assign mem_cmd_addr=cmd_addr;
    assign src_cmd_addr=cmd_addr;
    assign mem_cmd_read=cmd_read;
    assign src_cmd_read=cmd_read;
    assign mem_cmd_wdata=cmd_wdata;
    assign src_cmd_wdata=cmd_wdata;
    assign mem_cmd_wmask=cmd_wmask;
    assign src_cmd_wmask=cmd_wmask;
    assign rsp_valid=rst_n && pending &&
        (destination==DEST_MEMORY ? mem_rsp_valid :
         destination==DEST_SOURCE ? src_rsp_valid : 1'b1);
    assign rsp_rdata=destination==DEST_MEMORY ? mem_rsp_rdata :
        destination==DEST_SOURCE ? src_rsp_rdata : 32'b0;
    assign rsp_err=destination==DEST_MEMORY ? mem_rsp_err :
        destination==DEST_SOURCE ? src_rsp_err : 1'b1;
    assign mem_rsp_ready=rst_n && pending && destination==DEST_MEMORY && rsp_ready;
    assign src_rsp_ready=rst_n && pending && destination==DEST_SOURCE && rsp_ready;
    assign transaction_pending=pending;
    always @(posedge clk or negedge rst_n) begin
        if(!rst_n) begin pending<=0;destination<=DEST_ERROR;end
        else begin
            if(cmd_valid && cmd_ready) begin pending<=1;destination<=requested;end
            if(rsp_valid && rsp_ready) pending<=0;
        end
    end
endmodule
