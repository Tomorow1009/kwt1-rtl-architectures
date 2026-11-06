`timescale 1ns/1ps
// One-task loader, independent of the regression case IDs and coverage counts.
module tb_single_hex;
    reg clk=0;
    always #5 clk=~clk;
    reg rst_n=0,start_valid=0,in_valid=0,out_ready=0;
    reg signed [39:0] bias=0;
    reg [4:0] shift=12;
    reg signed [15:0] x=0,w=0;
    wire start_ready,in_ready,busy,out_valid,saturated;
    wire signed [15:0] result;
    dot64 dut(.*);
    reg signed [15:0] xm[0:63],wm[0:63],ym[0:0];
    reg signed [39:0] bm[0:0];
    reg signed [40:0] tm[0:0];
    reg [4:0] sm[0:0];
    reg satm[0:0];
    string data_dir;
    reg [8191:0] filename;
    integer k;
    initial begin
        if (!$value$plusargs("DATA_DIR=%s",data_dir)) data_dir="input";
        $sformat(filename,"%s/x.hex",data_dir); $readmemh(filename,xm);
        $sformat(filename,"%s/w.hex",data_dir); $readmemh(filename,wm);
        $sformat(filename,"%s/bias.hex",data_dir); $readmemh(filename,bm);
        $sformat(filename,"%s/shift.hex",data_dir); $readmemh(filename,sm);
        $sformat(filename,"%s/total.hex",data_dir); $readmemh(filename,tm);
        $sformat(filename,"%s/result.hex",data_dir); $readmemh(filename,ym);
        $sformat(filename,"%s/saturated.hex",data_dir); $readmemh(filename,satm);
        for(k=0;k<64;k=k+1)
            if ((^{xm[k],wm[k]})===1'bx) $fatal(1,"Missing x/w data");
        if ((^{bm[0],sm[0],tm[0],ym[0],satm[0]})===1'bx) $fatal(1,"Missing metadata/answer");
        if ($test$plusargs("VCD")) begin
            $dumpfile("single.vcd"); $dumpvars(0,dut);
        end
        repeat(3) @(negedge clk);
        rst_n=1;
        @(negedge clk); bias=bm[0]; shift=sm[0]; start_valid=1;
        @(posedge clk); while(!start_ready) @(posedge clk);
        @(negedge clk); start_valid=0;
        for(k=0;k<64;k=k+1) begin
            in_valid=1; x=xm[k]; w=wm[k];
            @(posedge clk); while(!in_ready) @(posedge clk);
            @(negedge clk);
        end
        in_valid=0;
        while(!out_valid) @(negedge clk);
        repeat(4) begin
            if(out_valid !== 1'b1 || result !== ym[0] || saturated !== satm[0] ||
                dut.sum_with_bias !== tm[0] || dut.accepted_count !== 7'd64)
                $fatal(1,"Single-dot mismatch: result=%0d expected=%0d",result,ym[0]);
            @(negedge clk);
        end
        out_ready=1;
        @(posedge clk); #1;
        if(out_valid || busy || !start_ready) $fatal(1,"Output handshake did not finish");
        $display("PASS: single HEX dot result=%0d saturated=%0b total=%0d",result,saturated,tm[0]);
        $finish;
    end
    initial begin #100000; $fatal(1,"Timeout"); end
endmodule
