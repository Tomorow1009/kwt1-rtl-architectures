`timescale 1ns/1ps
module tb_arch03_n1_decoder;
    reg clk=0;always #5 clk=~clk;
    reg rst_n=0,start=0,cancel=0,in_valid=0,out_ready=0;
    reg [31:0] encoded_bytes=0,in_data=0;
    wire in_ready,out_valid,busy,done,error;
    wire [63:0] out_data;
    wire [2:0] out_count;
    wire [3:0] error_code;
    wire [31:0] accepted_bytes,decoded_halfwords;
    arch03_n1_decoder dut(.*);
    reg [31:0] source[0:12287];reg [15:0] expected[0:23487];
    reg [4095:0] folder;
    integer words,bad,cycles=0,ip=0,op=0,lane,attempt;
    reg stalled=0;reg [63:0] held_data;reg [2:0] held_count;
    initial begin
        if(!$value$plusargs("DATA=%s",folder))$fatal(1,"DATA missing");
        if(!$value$plusargs("WORDS=%d",words))$fatal(1,"WORDS missing");
        if(!$value$plusargs("BAD=%d",bad))bad=0;
        $readmemh({folder,"/load32.hex"},source,0,words-1);
        $readmemh({folder,"/raw16.hex"},expected,0,23487);
        encoded_bytes=words*4;
        repeat(4)@(negedge clk);rst_n=1;
        for(attempt=0;attempt<3;attempt=attempt+1)begin
            @(negedge clk);start=1;ip=0;op=0;cycles=0;stalled=0;
            @(negedge clk);start=0;
            while(!done && !error && (attempt!=0 || cycles<32))begin
                @(negedge clk);
                cycles=cycles+1;
                if(!in_valid || in_ready)begin
                    in_valid=ip<words && cycles%7!=2;
                    in_data=source[ip<words ? ip : 0];
                end
                out_ready=cycles%11!=4 && cycles%11!=5 && cycles%11!=6 && !(cycles>=200 && cycles<387);
                if(cycles>100000)$fatal(1,"decoder timeout");
            end
            @(negedge clk);in_valid=0;out_ready=0;
            if(attempt==0 && !error)begin
                cancel=1;@(negedge clk);cancel=0;
                if(busy || done || error)$fatal(1,"cancel did not invalidate decoder");
                $display("DECODER_CANCEL_PASS");
            end else if(bad!=0)begin
                if(!error || error_code!=bad)$fatal(1,"expected error %0d got %0d",bad,error_code);
                $display("DECODER_ERROR_PASS code=%0d",error_code);$finish;
            end else begin
                if(error || op!=23488 || ip!=words || decoded_halfwords!=23488 || accepted_bytes!=words*4)
                    $fatal(1,"decoder result error=%0d code=%0d out=%0d in=%0d",error,error_code,op,ip);
                $display("DECODER_TASK_PASS attempt=%0d outputs=%0d cycles=%0d",attempt,op,cycles);
            end
        end
        $display("DECODER_SUITE_PASS");$finish;
    end
    always @(posedge clk)if(rst_n && !start && !cancel)begin
        if(in_valid && in_ready)ip=ip+1;
        if(stalled && (out_valid!==1'b1 || out_data!==held_data || out_count!==held_count))
            $fatal(1,"output changed during backpressure");
        stalled=out_valid && !out_ready;
        held_data=out_data;held_count=out_count;
        if(out_valid && out_ready)begin
            if(out_count<1 || out_count>4 || op+out_count>23488)$fatal(1,"invalid vector count");
            for(lane=0;lane<4;lane=lane+1)if(lane<out_count)begin
                if(bad==0 && out_data[lane*16+:16]!==expected[op+lane])
                    $fatal(1,"mismatch half=%0d actual=%h expected=%h",op+lane,out_data[lane*16+:16],expected[op+lane]);
            end
            op=op+out_count;
        end
    end
endmodule
