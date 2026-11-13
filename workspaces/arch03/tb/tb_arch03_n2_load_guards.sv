`timescale 1ns/1ps
// Direct core checks deliberately bypass the decoder's independent guards.
module tb_arch03_n2_load_guards;
    reg clk=0,rst_n=0,start_valid=0,cancel=0,prefetch_enable=1,layout_v3=1;
    reg [4:0] shift=10;
    reg load_valid=0,out_ready=1;
    reg [63:0] load_data=0;
    reg [2:0] load_count=0;
    wire start_ready,load_ready,out_valid,busy,done,error;
    wire [6:0] out_row;
    wire [7:0] out_column;
    wire [31:0] result;
    wire [1:0] saturated;
    integer tick=0,tests=0,epoch=0,lane;
    arch03_n2_linear16x5 dut(.*);
    always #5 clk=~clk;
    always @(posedge clk)begin tick=tick+1;if(tick>20000)$fatal(1,"load-guard timeout");end
    function signed [31:0] bias_value(input integer column);
        begin
            case((column+epoch)%4)
                0:bias_value=32'sh80000000;
                1:bias_value=32'sh7fffffff;
                2:bias_value=-1;
                default:bias_value=0;
            endcase
        end
    endfunction
    function [15:0] bias_half(input integer index);
        reg signed [31:0] value;
        begin
            value=bias_value(index/3);
            case(index%3)
                0:bias_half=value[15:0];
                1:bias_half=value[31:16];
                default:bias_half={8'b0,{8{value[31]}}};
            endcase
        end
    endfunction
    task begin_task(input bit dma_order,input [4:0] shift_value);
        begin
            @(negedge clk);cancel=1;load_valid=0;start_valid=0;
            repeat(3)@(negedge clk);cancel=0;
            wait(start_ready);@(negedge clk);
            layout_v3=dma_order;shift=shift_value;start_valid=1;
            @(negedge clk);start_valid=0;
        end
    endtask
    task send(input [63:0] value,input [2:0] count);
        begin
            @(negedge clk);load_data=value;load_count=count;load_valid=1;
            @(posedge clk);while(!load_ready)@(posedge clk);
            @(negedge clk);load_valid=0;
        end
    endtask
    task zeros(input integer count);
        integer n;
        begin for(n=0;n<count;n=n+4)send(0,4);end
    endtask
    task biases;
        integer n;
        begin
            for(n=0;n<48;n=n+4)send({bias_half(n+3),bias_half(n+2),bias_half(n+1),bias_half(n)},4);
            wait(dut.bank_valid[0] || error);
            if(error)$fatal(1,"Valid signed32 bias rejected epoch=%0d",epoch);
            for(lane=0;lane<16;lane=lane+1)
                if(dut.biases[lane]!==bias_value(lane))$fatal(1,"Bias32 assembly differs lane=%0d",lane);
        end
    endtask
    task rejected(input integer number);
        begin
            wait(error);repeat(3)@(negedge clk);
            if(dut.bank_valid!=0 || dut.x_valid || dut.x_group_valid!=0)
                $fatal(1,"Invalid numeric data published a valid cache case=%0d",number);
            tests=tests+1;$display("N1_CORE_LOAD_REJECT_PASS case=%0d",number);
        end
    endtask
    initial begin
        repeat(4)@(negedge clk);rst_n=1;
        begin_task(0,10);send(64'h2000,1);rejected(1); // invalid X14 container
        begin_task(1,10);send(64'h0800,1);rejected(2); // invalid W12 container
        begin_task(1,10);zeros(1024);
        send(64'h0000_0000_8000_0000,4);rejected(3); // negative b high must 00ff
        begin_task(1,10);zeros(1024);
        send(64'h0000_01ff_8000_0000,4);rejected(4); // b padding must zero
        begin_task(1,12);rejected(5); // direct core must not silently accept old shift
        begin_task(1,10);send(0,0);rejected(6); // malformed vector length
        // Same-beat middle/high sign plus a later high half in the next beat.
        begin_task(1,10);zeros(1024);biases;
        tests=tests+1;$display("N1_CORE_BIAS_PASS order=dma epoch=0");
        send(64'h2000,1);wait(error);
        if(dut.x_valid || dut.x_group_valid!=0)$fatal(1,"Bad X published after W/b commit");
        tests=tests+1;$display("N1_CORE_LOAD_REJECT_PASS case=8");
        // Biases deliberately retain opposite signs from the prior task, so
        // same-beat validation must use the new middle half, not stale state.
        epoch=1;begin_task(0,10);zeros(6336);zeros(1024);biases;
        tests=tests+1;$display("N1_CORE_BIAS_PASS order=debug epoch=1");
        @(negedge clk);cancel=1;repeat(3)@(negedge clk);cancel=0;
        wait(start_ready);
        $display("N2_CORE_LOAD_GUARDS_PASS tests=%0d decoder_bypassed=true",tests);
        $finish;
    end
endmodule
