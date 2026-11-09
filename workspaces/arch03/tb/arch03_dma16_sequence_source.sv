`timescale 1ns/1fs
// PC-side pre-read only. Selecting a bank transfers no DUT data. The actual
// source still returns one synchronous ICB word per accepted DMA request.
module arch03_dma16_sequence_source #(
    parameter [31:0] BASE=32'hb0000000,parameter integer WORDS=11744
)(
    input wire clk,rst_n,select_valid,
    input wire [31:0] select_descriptor,
    input wire cmd_valid,output wire cmd_ready,
    input wire [31:0] cmd_addr,input wire cmd_read,
    input wire [31:0] cmd_wdata,input wire [3:0] cmd_wmask,
    output reg rsp_valid,input wire rsp_ready,
    output reg [31:0] rsp_rdata,output reg rsp_err,
    output reg selected=0,output reg selected_bank=0
);
    reg [31:0] first_words[0:WORDS-1],second_words[0:WORDS-1];
    reg [4095:0] first_path,second_path;
    integer i;
    wire mapped=cmd_addr>=BASE && {1'b0,cmd_addr}<({1'b0,BASE}+WORDS*4) && cmd_addr[1:0]==0;
    assign cmd_ready=rst_n && selected && !rsp_valid;
    initial begin
        if(!$value$plusargs("FIRST_LOAD32=%s",first_path) || !$value$plusargs("SECOND_LOAD32=%s",second_path))
            $fatal(1,"Missing sequence source file paths");
        for(i=0;i<WORDS;i=i+1)begin first_words[i]=32'bx;second_words[i]=32'bx;end
        $readmemh(first_path,first_words);$readmemh(second_path,second_words);
        for(i=0;i<WORDS;i=i+1)
            if((^{first_words[i],second_words[i]})===1'bx)$fatal(1,"Incomplete sequence source word %0d",i);
        $display("DMA16_SEQUENCE_SOURCE_READY words_per_bank=%0d scope=PC_file_only no_ITCM_task_data=true",WORDS);
    end
    always @(posedge clk or negedge rst_n)begin
        if(!rst_n)begin rsp_valid<=0;rsp_rdata<=0;rsp_err<=0;selected<=0;selected_bank<=0;end
        else begin
            if(select_valid)begin
                if(cmd_valid || rsp_valid || select_descriptor[31:16]>1 || select_descriptor[15:5]!=0)
                    $fatal(1,"Sequence source switch with pending request/response or invalid descriptor");
                selected<=1;selected_bank<=select_descriptor[16];
                $display("DMA16_SEQUENCE_SOURCE_SELECTED descriptor=%08h",select_descriptor);
            end
            if(rsp_valid && rsp_ready)rsp_valid<=0;
            if(cmd_valid && cmd_ready)begin
                rsp_valid<=1;rsp_err<=!mapped || !cmd_read;
                rsp_rdata<=mapped && cmd_read ?
                    (selected_bank ? second_words[(cmd_addr-BASE)>>2] : first_words[(cmd_addr-BASE)>>2]) : 0;
            end
        end
    end
endmodule
