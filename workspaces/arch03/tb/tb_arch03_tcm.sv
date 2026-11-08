`timescale 1ns/1ps
module tcm_check #(parameter DW=64,AW=15,DP=32768)(output reg done=0);
    localparam MW=DW/8;
    reg clk=0,rst_n=0,cs=0,we=0,sd=0,ds=0,ls=0;
    reg [AW-1:0] addr=0;
    reg [DW-1:0] din=0;
    reg [MW-1:0] wem=0;
    wire [DW-1:0] dout;
    reg [DW-1:0] expected[0:DP-1];
    reg [DW-1:0] held,pattern;
    integer b,k,m,a,j,checks=0;
    always #3.333 clk=~clk;
    arch03_tcm_ram #(.DP(DP),.DW(DW),.MW(MW),.AW(AW)) dut(.*);
    task write_word(input integer address,input [DW-1:0] value,input [MW-1:0] mask);
        integer n;
        begin
            @(negedge clk);cs=1;we=1;addr=address;din=value;wem=mask;
            @(posedge clk);#0.01;
            for(n=0;n<MW;n=n+1) if(mask[n]) expected[address][n*8+:8]=value[n*8+:8];
        end
    endtask
    task read_word(input integer address);
        begin
            @(negedge clk);cs=1;we=0;addr=address;wem=0;
            @(posedge clk);#0.01;
            if(dout!==expected[address])
                $fatal(1,"TCM DW=%0d addr=%0d got=%h expected=%h",DW,address,dout,expected[address]);
            checks=checks+1;
        end
    endtask
    initial begin
        repeat(2) @(negedge clk);rst_n=1;
        // Every bank, first/last word and both sides of each address boundary.
        for(b=0;b<DP/4096;b=b+1) begin
            for(k=0;k<2;k=k+1) begin
                a=b*4096+(k ? 4095 : 0);
                for(j=0;j<MW;j=j+1) pattern[j*8+:8]=(a+j*37) & 255;
                write_word(a,pattern,{MW{1'b1}});
            end
        end
        for(b=DP/4096-1;b>=0;b=b-1) begin read_word(b*4096);read_word(b*4096+4095);end
        // Exhaust all byte masks, including no-op and disjoint partial updates.
        for(m=0;m<(1<<MW);m=m+1) begin
            a=(m%(DP/4096))*4096;
            for(j=0;j<MW;j=j+1) pattern[j*8+:8]=(m*13+j*29) & 255;
            write_word(a,pattern,m);read_word(a);
        end
        read_word(DP-1);held=dout;
        @(negedge clk);cs=0;we=1;addr=0;din=0;wem={MW{1'b1}};
        repeat(3) begin @(posedge clk);#0.01;if(dout!==held)$fatal(1,"Disabled TCM output changed");end
        read_word(0);
        // Writes into another bank must not select its stale read output.
        held=dout;write_word(DP-1,{DW{1'b1}},{MW{1'b1}});
        if(dout!==held)$fatal(1,"Write changed read-bank selection");
        read_word(DP-1);
        // Control reset inhibits writes but never clears physical memory.
        @(negedge clk);rst_n=0;cs=1;we=1;addr=0;din=0;wem={MW{1'b1}};
        repeat(2) @(negedge clk);cs=0;rst_n=1;
        read_word(0);read_word(DP-1);
        // Upstream clock gating/low power requests retain contents.
        @(negedge clk);cs=0;sd=1;ds=1;ls=1;held=dout;
        repeat(3) begin @(posedge clk);#0.01;if(dout!==held)$fatal(1,"Idle retention changed data");end
        @(negedge clk);sd=0;ds=0;ls=0;
        for(b=0;b<DP/4096;b=b+1) begin read_word(b*4096);read_word(b*4096+4095);end
        // Unique full-width data for EVERY address, then read in reverse order.
        // This detects capacity truncation, swapped/missing address bits and bank aliasing.
        for(a=0;a<DP;a=a+1) write_word(a,64'h9e3779b97f4a7c15*(a+1),{MW{1'b1}});
        for(a=DP-1;a>=0;a=a-1) read_word(a);
        @(negedge clk);cs=0;
        $display("TCM_GEOMETRY_PASS DW=%0d DP=%0d checks=%0d macros=32",DW,DP,checks);
        done=1;
    end
endmodule
module tb_arch03_tcm;
    wire itcm_done,dtcm_done;
    tcm_check #(.DW(64),.AW(15),.DP(32768)) itcm(itcm_done);
    tcm_check #(.DW(32),.AW(16),.DP(65536)) dtcm(dtcm_done);
    initial begin wait(itcm_done && dtcm_done);$display("ARCH03_TCM_PASS macros=64 cpu_executed=false");$finish;end
    initial begin #2000000;$fatal(1,"TCM test timeout");end
endmodule
