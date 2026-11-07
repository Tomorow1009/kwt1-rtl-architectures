`timescale 1ns/1ps
module tb_sram_guard;
    reg clk=0;always #5 clk=~clk;
    reg rst_n=0,cs=0;wire [15:0] rdata;wire rvalid;
    arch02_sram_port #(.AW(7)) memory(.clk(clk),.rst_n(rst_n),.cs(cs),.we(1'b0),.addr(7'd0),.wdata(16'd0),.rdata(rdata),.rvalid(rvalid));
    initial begin repeat(3) @(negedge clk);rst_n=1;cs=1;repeat(5) @(negedge clk);$fatal(1,"Guard failed to reject read");end
endmodule
