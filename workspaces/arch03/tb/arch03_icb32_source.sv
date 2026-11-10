`timescale 1ns/1fs
// Loading environment, outside the synthesized SoC. Only this PC-side file
// pre-read is unmeasured. Every source request/response remains a timed ICB
// transaction through the original, restored sysmem interface.
// A request accepted at edge N registers response VALID/data immediately after
// that edge; N+1 is the earliest response handshake. No extra pending stage.
module arch03_icb32_source #(
    parameter [31:0] BASE=32'hb0000000,
    parameter MAX_WORDS=11752
)(
    input wire clk,rst_n,
    input wire cmd_valid,output wire cmd_ready,
    input wire [31:0] cmd_addr,input wire cmd_read,
    input wire [31:0] cmd_wdata,input wire [3:0] cmd_wmask,
    output reg rsp_valid,input wire rsp_ready,
    output reg [31:0] rsp_rdata,output reg rsp_err
);
    reg [31:0] words[0:MAX_WORDS-1];
    reg [4095:0] source_path;
    integer i,accepted=0,responded=0,encoded_bytes=0;
    integer word_count=0;
    wire mapped=cmd_addr>=BASE && {1'b0,cmd_addr}<({1'b0,BASE}+word_count*4) && cmd_addr[1:0]==0;
    assign cmd_ready=rst_n && !rsp_valid;
    initial begin
        if(!$value$plusargs("CODEC_BYTES=%d",encoded_bytes))$fatal(1,"Missing CODEC_BYTES");
        if(encoded_bytes<32 || encoded_bytes>MAX_WORDS*4 || encoded_bytes%4)$fatal(1,"Invalid codec source geometry");
        word_count=encoded_bytes/4;
        if(!$value$plusargs("LOAD32=%s",source_path)) $fatal(1,"Missing LOAD32 source file");
        for(i=0;i<word_count;i=i+1)words[i]=32'bx;
        $readmemh(source_path,words,0,word_count-1);
        for(i=0;i<word_count;i=i+1)
            if((^words[i])===1'bx)$fatal(1,"Incomplete/unknown loading-source word %0d",i);
        $display("ARCH03_ICB32_SOURCE_READY words=%0d scope=PC_file_only no_ITCM_task_data=true",word_count);
    end
    always @(posedge clk or negedge rst_n) begin
        if(!rst_n) begin
            rsp_valid<=0;rsp_err<=0;rsp_rdata<=0;accepted<=0;responded<=0;
        end else begin
            if(rsp_valid && rsp_ready) begin rsp_valid<=0;responded<=responded+1;end
            if(cmd_valid && cmd_ready) begin
                rsp_valid<=1;rsp_err<=!mapped || !cmd_read;accepted<=accepted+1;
                rsp_rdata<=mapped && cmd_read ? words[(cmd_addr-BASE)>>2] : 32'b0;
            end
        end
    end
endmodule
