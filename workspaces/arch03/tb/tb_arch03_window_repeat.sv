`timescale 1ns/1fs
module tb_arch03_window_repeat;
    reg clk=0,rst_n=0,cmd_valid=0,cmd_ready=0,cmd_read=0;
    reg [31:0] cmd_addr=0,cmd_wdata=0;
    reg [3:0] cmd_wmask=0;
    reg rsp_valid=0,rsp_ready=0,rsp_err=0;
    wire active,finished;
    wire [63:0] start_cycle,end_cycle,read_commands,write_commands,command_wait_cycles,response_wait_cycles;
    reg [63:0] previous_end=0;
    integer task_index,n;
    always #3.333333 clk=~clk;
    arch03_task_window #(.INPUT_WORDS(4),.OUTPUT_WORDS(4),.REPEAT_TASKS(1)) dut(.*);
    task store(input [31:0] address,input [31:0] data,input [3:0] mask);
        begin
            @(negedge clk);cmd_addr=address;cmd_wdata=data;cmd_wmask=mask;cmd_valid=1;cmd_ready=1;
            @(negedge clk);cmd_valid=0;cmd_ready=0;
            @(negedge clk);rsp_valid=1;rsp_ready=1;
            @(negedge clk);rsp_valid=0;rsp_ready=0;
        end
    endtask
    initial begin
        repeat(2) @(negedge clk);rst_n=1;
        for(task_index=0;task_index<3;task_index=task_index+1)begin
            store(32'ha001f020,32'h4b575442,4'hf);
            if(!active || finished || start_cycle<=previous_end || write_commands!=0)
                $fatal(1,"Repeat task did not start with fresh observer state");
            if($test$plusargs("NEGATIVE_ACTIVE_BEGIN"))begin
                store(32'ha001f020,32'h4b575442,4'hf);$fatal(1,"Active duplicate BEGIN was accepted");
            end
            for(n=0;n<4;n=n+1)store(32'ha0000000+2*n,n,n[0] ? 4'hc : 4'h3);
            for(n=0;n<4;n=n+1)store(32'ha000c000+2*n,n,n[0] ? 4'hc : 4'h3);
            if(!finished || active || dut.completed_tasks!=task_index+1 || write_commands!=8 ||
               command_wait_cycles!=0 || response_wait_cycles!=0)$fatal(1,"Repeat task observer count mismatch");
            previous_end=end_cycle;
            // Recovery-phase mailbox accesses happen outside measured tasks.
            store(32'ha001f028,32'h504f4931,4'hf);
        end
        $display("ARCH03_REPEAT_WINDOW_PASS tasks=3 reset_between_tasks=false");$finish;
    end
    initial begin #10000;$fatal(1,"Repeated-window test timeout");end
endmodule
