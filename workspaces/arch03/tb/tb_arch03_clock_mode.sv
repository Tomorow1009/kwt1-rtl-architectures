`timescale 1ns/1fs
module tb_arch03_clock_mode;
    reg clk=0,rst_n=0,active=0,finished=0;
    reg test_mode=0,pllbypass=1,plloutdivby1=1;
    reg [255:0] mode_case;
    always #3.333333 clk=~clk;
    arch03_clock_mode_guard guard(.clk(clk),.rst_n(rst_n),.active(active),.finished(finished),
        .test_mode(test_mode),.pllbypass(pllbypass),.plloutdivby1(plloutdivby1));
    initial begin
        if(!$value$plusargs("MODE_CASE=%s",mode_case))$fatal(1,"Missing mode case");
        @(negedge clk);rst_n=1;active=1;
        repeat(3) @(negedge clk);
        if(mode_case=="test") test_mode=1;
        else if(mode_case=="bypass") pllbypass=0;
        else if(mode_case=="divider") plloutdivby1=0;
        else if(mode_case=="unknown") pllbypass=1'bx;
        else if(mode_case!="positive") $fatal(1,"Unknown mode case");
        repeat(3) @(negedge clk);
        active=0;finished=1;
        @(negedge clk);
        $display("ARCH03_CLOCK_MODE_TEST_PASS cpu_executed=false");
        $finish;
    end
endmodule
