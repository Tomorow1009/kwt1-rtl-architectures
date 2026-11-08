`timescale 1ns/1fs
module tb_arch03_window;
    reg clk=0,rst_n=0,cmd_valid=0,cmd_ready=0,cmd_read=0;
    reg [31:0] cmd_addr=0,cmd_wdata=0;
    reg [3:0] cmd_wmask=0;
    reg rsp_valid=0,rsp_ready=0,rsp_err=0;
    wire active,finished;
    wire [63:0] start_cycle,end_cycle,read_commands,write_commands,command_wait_cycles,response_wait_cycles;
    reg [63:0] expected_start,expected_end;
    integer n;
    always #3.333333 clk=~clk;
    arch03_task_window #(.INPUT_WORDS(4),.OUTPUT_WORDS(4)) dut(.*);
    task issue(input [31:0] address,input [31:0] data,input [3:0] mask);
        begin
            @(negedge clk);cmd_addr=address;cmd_wdata=data;cmd_wmask=mask;cmd_valid=1;cmd_ready=0;
            repeat(2) @(negedge clk);
            cmd_ready=1;
            @(negedge clk);cmd_valid=0;cmd_ready=0;
        end
    endtask
    task respond;
        begin
            @(negedge clk);rsp_valid=1;rsp_ready=0;
            repeat(3) @(negedge clk);
            rsp_ready=1;
            @(negedge clk);rsp_valid=0;rsp_ready=0;
        end
    endtask
    initial begin
        repeat(2) @(negedge clk);rst_n=1;
        if($test$plusargs("NEGATIVE_BEFORE_BEGIN"))begin
            issue(32'ha0000000,0,4'h3);$fatal(1,"Negative test failed to reject early data");
        end
        issue(32'ha001f020,32'h4b575442,4'hf);
        if(active)$fatal(1,"Window began on command rather than response");
        respond();expected_start=dut.cycles;
        if(!active || start_cycle!=expected_start)$fatal(1,"Wrong start response boundary");
        if($test$plusargs("NEGATIVE_RESPONSE_ERROR"))begin
            issue(32'ha0000000,0,4'h3);rsp_err=1;respond();$fatal(1,"Negative test failed to reject error");
        end
        for(n=0;n<4;n=n+1)begin issue(32'ha0000000+2*n,n,n[0] ? 4'hc : 4'h3);respond();end
        // Mix 32-bit and 16-bit output stores; final command is delayed/blocked.
        issue(32'ha000c000,0,4'hf);respond();
        issue(32'ha000c004,0,4'h3);respond();
        issue(32'ha000c006,0,4'hc);
        if(finished || !active)$fatal(1,"Window ended before final response");
        repeat(5) @(negedge clk);
        respond();expected_end=dut.cycles;
        if(!finished || active || end_cycle!=expected_end)$fatal(1,"Wrong final response boundary");
        if(command_wait_cycles!=14 || response_wait_cycles!=21 || write_commands!=7 || read_commands!=0)
            $fatal(1,"Wait/transaction accounting mismatch cmd=%0d rsp=%0d writes=%0d",command_wait_cycles,response_wait_cycles,write_commands);
        if(dut.period_ns<6.666665 || dut.period_ns>6.666667)$fatal(1,"Incorrect measured simulation period");
        $display("ARCH03_WINDOW_PASS final_response_checked=true waits_checked=true");$finish;
    end
    initial begin #10000;$fatal(1,"Window test timeout");end
endmodule
