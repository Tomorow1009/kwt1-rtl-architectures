`timescale 1ns/1ps
module tb_lanes;
    `include "cases.vh"
    reg clk=0;always #5 clk=~clk;
    reg rst_n=0,start_valid=0,in_valid=0,out_ready=0;
    reg signed [15:0] x,w;
    reg signed [39:0] bias;
    reg [4:0] shift;
    wire [7:0] sr,ir,ov,sat,busy;
    wire signed [15:0] result[0:7];
    wire signed [40:0] total[0:7];
    reg [15:0] xs[0:CASES*64-1],ws[0:CASES*64-1],answers[0:CASES-1];
    reg [39:0] biases[0:CASES-1];reg [40:0] totals[0:CASES-1];
    reg [4:0] shifts[0:CASES-1];reg sats[0:CASES-1];
    integer n,k,j;string data_dir;reg [8191:0] filename;
    genvar g;
    generate for(g=0;g<8;g=g+1) begin:lanes
        dot64 mac(.clk(clk),.rst_n(rst_n),.start_valid(start_valid),.start_ready(sr[g]),.bias(bias),.shift(shift),
            .in_valid(in_valid),.in_ready(ir[g]),.x(x),.w(w),.out_valid(ov[g]),.out_ready(out_ready),.result(result[g]),.saturated(sat[g]),.busy(busy[g]));
        assign total[g]=mac.sum_with_bias;
    end endgenerate
    initial begin
        if(!$value$plusargs("DATA_DIR=%s",data_dir)) $fatal(1,"DATA_DIR required");
        $sformat(filename,"%s/x.hex",data_dir);$readmemh(filename,xs);
        $sformat(filename,"%s/w.hex",data_dir);$readmemh(filename,ws);
        $sformat(filename,"%s/bias.hex",data_dir);$readmemh(filename,biases);
        $sformat(filename,"%s/shift.hex",data_dir);$readmemh(filename,shifts);
        $sformat(filename,"%s/total.hex",data_dir);$readmemh(filename,totals);
        $sformat(filename,"%s/result.hex",data_dir);$readmemh(filename,answers);
        $sformat(filename,"%s/saturated.hex",data_dir);$readmemh(filename,sats);
        repeat(3) @(negedge clk);rst_n=1;
        for(n=0;n<CASES;n=n+1) begin
            start_valid=1;bias=biases[n];shift=shifts[n];
            @(posedge clk);if(!(&sr)) $fatal(1,"Start not ready");
            @(negedge clk);start_valid=0;
            for(k=0;k<64;k=k+1) begin
                in_valid=1;x=xs[n*64+k];w=ws[n*64+k];
                @(posedge clk);if(!(&ir)) $fatal(1,"Input not ready");@(negedge clk);
            end
            in_valid=0;while(!(&ov)) @(negedge clk);
            for(j=0;j<8;j=j+1) if(result[j]!==answers[n] || total[j]!==totals[n] || sat[j]!==sats[n]) $fatal(1,"Numerical lane=%0d case=%0d",j,n);
            repeat(2) @(negedge clk);out_ready=1;@(negedge clk);out_ready=0;
        end
        $display("PASS: numerical cases=%0d lanes=8 checks=%0d",CASES,CASES*8);$finish;
    end
    initial begin #2000000;$fatal(1,"Lane timeout");end
endmodule
