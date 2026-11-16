`timescale 1ns/1ps
module tb_arch03_c80_decoder;
    reg clk=0;always #5 clk=~clk;
    reg rst_n=0,start=0,cancel=0,in_valid=0,out_ready=0;
    reg [31:0] encoded_bytes=0,in_data=0;
    wire in_ready,out_valid,busy,done,error;
    wire [63:0] out_data;wire [2:0] out_count;wire [3:0] error_code;
    wire [31:0] accepted_bytes,decoded_halfwords;
    arch03_c80_decoder dut(.*);
    reg [31:0] source[0:12287];reg [15:0] expected[0:23487];
    reg [4095:0] folder;
    integer words,bad,cycles=0,ip=0,op=0,attempt,stop_at;
    reg stalled=0,input_accepted=0;reg [63:0] held_data;reg [2:0] held_count;
    initial begin
        if(!$value$plusargs("DATA=%s",folder))$fatal(1,"DATA missing");
        if(!$value$plusargs("WORDS=%d",words))$fatal(1,"WORDS missing");
        if(!$value$plusargs("BAD=%d",bad))bad=0;
        $readmemh({folder,"/load32.hex"},source,0,words-1);
        $readmemh({folder,"/raw16.hex"},expected,0,23487);
        encoded_bytes=words*4;
        repeat(4)@(negedge clk);rst_n=1;
        for(attempt=0;attempt<5;attempt=attempt+1)begin
            @(negedge clk);start=1;ip=0;op=0;cycles=0;stalled=0;input_accepted=0;
            @(negedge clk);start=0;
            stop_at=attempt==0 ? 32 : attempt==1 ? 211 : attempt==2 ? 3111 : 200000;
            while(!done && !error && cycles<stop_at)begin
                @(negedge clk);
                cycles=cycles+1;
                // Use the sampled handshake, not ready AFTER the active edge.
                if(!in_valid || input_accepted)begin
                    in_valid=ip<words && cycles%7!=2 && !(cycles>=101 && cycles<144);
                    in_data=source[ip<words ? ip : 0];
                end
                out_ready=cycles%11!=4 && cycles%11!=5 && cycles%11!=6 && !(cycles>=200 && cycles<387);
            end
            @(negedge clk);in_valid=0;out_ready=0;
            if(attempt<3 && !error)begin
                if(attempt==1)begin rst_n=0;@(negedge clk);rst_n=1;end
                else begin cancel=1;@(negedge clk);cancel=0;end
                if(busy || done || error)$fatal(1,"cancel/reset retained state");
                $display("C80_DECODER_RESTART_PASS attempt=%0d",attempt);
            end else if(bad!=0)begin
                if(!error || error_code!=bad)$fatal(1,"expected error %0d got %0d",bad,error_code);
                $display("C80_DECODER_ERROR_PASS code=%0d",error_code);$finish;
            end else begin
                if(!done || error || op!=23488 || ip!=words || decoded_halfwords!=23488 || accepted_bytes!=words*4)
                    $fatal(1,"decoder result done=%0d error=%0d code=%0d out=%0d in=%0d cycle=%0d state=%0d bits=%0d",done,error,error_code,op,ip,cycles,dut.state,dut.bit_count);
                $display("C80_DECODER_TASK_PASS attempt=%0d outputs=%0d cycles=%0d",attempt,op,cycles);
            end
        end
        $display("C80_DECODER_SUITE_PASS");$finish;
    end
    always @(posedge clk)begin
        input_accepted=rst_n && !start && !cancel && in_valid && in_ready;
        if(rst_n && !start && !cancel)begin
            if(input_accepted)ip=ip+1;
            if(stalled && (out_valid!==1'b1 || out_data!==held_data || out_count!==held_count))
                $fatal(1,"output changed during backpressure");
            stalled=out_valid && !out_ready;held_data=out_data;held_count=out_count;
            if(out_valid && out_ready)begin
                if(out_count!=1 || op>=23488)$fatal(1,"invalid scalar count");
                if(bad==0 && out_data[15:0]!==expected[op])
                    $fatal(1,"mismatch half=%0d actual=%h expected=%h state=%0d",op,out_data[15:0],expected[op],dut.state);
                op=op+1;
            end
        end else stalled=0;
    end
endmodule
