`timescale 1ns/1fs
// No CPU. Exercise the production loader and TCM adapter against a physical
// layout substitute, then read every logical word through the normal RAM port.
module tb_arch03_asic_boot;
    reg clk=0,rst_n=0,cs=0;
    reg [14:0] addr=0;
    wire [63:0] dout;
    reg [7:0] expected[0:262143];
    reg [4095:0] image_path;
    integer word_index,lane;
    arch03_tcm_ram memory(.sd(1'b0),.ds(1'b0),.ls(1'b0),.rst_n(rst_n),.clk(clk),
        .cs(cs),.we(1'b0),.addr(addr),.din(64'b0),.wem(8'b0),.dout(dout));
    always #3.333333 clk=~clk;
`define ARCH03_ASIC_ITCM memory
`include "arch03_asic_boot.svh"
    initial begin
        if(!$value$plusargs("IMAGE=%s",image_path)) $fatal(1,"Missing IMAGE");
        for(word_index=0;word_index<262144;word_index=word_index+1) expected[word_index]=8'bx;
        $readmemh(image_path,expected);
        #1;
        if(!arch03_boot_ready) $fatal(1,"Loader did not complete");
        rst_n=1;
        for(word_index=0;word_index<32768;word_index=word_index+1) begin
            @(negedge clk);addr=word_index;cs=1;
            // Allow functional clock-to-Q delay, still inside the read cycle.
            @(posedge clk);#3;
            for(lane=0;lane<8;lane=lane+1) begin
                if((^expected[word_index*8+lane])===1'bx) $fatal(1,"Unknown source byte");
                if(dout[lane*8+:8] !== expected[word_index*8+lane])
                    $fatal(1,"Boot readback word=%d lane=%d actual=%h expected=%h",word_index,lane,dout[lane*8+:8],expected[word_index*8+lane]);
            end
        end
`ifdef ARCH03_VENDOR_BOOT_TEST
        $display("ARCH03_BOOT_MAPPING_PASS bytes=262144 words=32768 macros=32 cpu_executed=false vendor_verified=true");
`else
        $display("ARCH03_BOOT_MAPPING_PASS bytes=262144 words=32768 macros=32 cpu_executed=false vendor_verified=false");
`endif
        $finish;
    end
endmodule
