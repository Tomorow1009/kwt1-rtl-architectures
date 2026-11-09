`timescale 1ns/1fs
module tb_arch03_task_window16;
    reg clk=0;always #3.333333 clk=~clk;
    reg rst_n=0,task_arm=0,task_cancel=0;
    reg cmd_valid=0,cmd_ready=0,cmd_read=1;
    reg [31:0] cmd_addr=0;
    reg [3:0] cmd_wmask=15;
    reg rsp_valid=0,rsp_ready=0,rsp_err=0;
    reg global_pending=0,fifo_empty=1,core_done=0;
    wire active,finished,failed;
    wire [31:0] failure_code,source_read_acks,input_write_acks,input_read_acks,output_write_acks;
    wire [63:0] start_cycle,end_cycle,window_cycles,command_wait_cycles,response_wait_cycles;
    arch03_task_window16 dut(.*);
    reg [63:0] ticks=0;
    always @(posedge clk) if(!rst_n) ticks<=0;else ticks<=ticks+1;
    reg first_request=1;
    reg [63:0] expected_start=0,last_ack=0,baseline_cycles=0;
    realtime expected_start_ns=0;
    integer task_number=0,pass_tasks=0,fail_tasks=0,i;
    task arm_task;
        begin
            @(negedge clk);task_arm=1;task_cancel=0;cmd_valid=0;cmd_ready=0;
            rsp_valid=0;rsp_ready=0;rsp_err=0;global_pending=0;fifo_empty=1;
            // core_done may still be high from the previous task at ARM.
            @(posedge clk);
            @(negedge clk);task_arm=0;core_done=0;first_request=1;
            if(active || finished || failed || window_cycles || source_read_acks ||
                input_write_acks || input_read_acks || output_write_acks)
                $fatal(1,"DMA16 window ARM did not cold-clear state");
            task_number=task_number+1;
        end
    endtask
    task transfer(input [31:0] address,input reading,input [3:0] mask,
        input integer command_delay,input integer response_stall,input error_response,
        input last_output,input integer global_delay,input integer fifo_delay);
        begin
            @(negedge clk);cmd_addr=address;cmd_read=reading;cmd_wmask=mask;cmd_ready=0;
            // Deliberately generate VALID via NBA at a sending posedge, as RTL
            // does. A posedge-only observer sees it one cycle too late.
            @(posedge clk);cmd_valid<=1;global_pending<=1;
            if(first_request && reading && address>=32'hb0000000 && address<32'hb000b780) begin
                first_request=0;expected_start=ticks+1;expected_start_ns=$realtime;
                #0.000001;
                if(!active || start_cycle!==expected_start || dut.start_ns!=expected_start_ns)
                    $fatal(1,"DMA16 window missed sending edge: got=%0d expected=%0d",start_cycle,expected_start);
            end
            repeat(command_delay) begin @(negedge clk);@(posedge clk);end
            @(negedge clk);cmd_ready=1;
            @(posedge clk);
            @(negedge clk);cmd_valid=0;cmd_ready=0;
            @(posedge clk);
            @(negedge clk);rsp_valid=1;rsp_ready=(response_stall==0);rsp_err=error_response;
            if(response_stall>0) begin
                repeat(response_stall) @(posedge clk);
                @(negedge clk);rsp_ready=1;
            end
            @(posedge clk);last_ack=ticks+1;
            if(!last_output || global_delay==0) global_pending<=0;
            if(last_output && fifo_delay==0) fifo_empty<=1;
            @(negedge clk);rsp_valid=0;rsp_ready=0;rsp_err=0;
        end
    endtask
    task assert_failed(input integer expected_code);
        begin
            repeat(2) @(negedge clk);
            if(!finished || !failed || active || failure_code!=expected_code)
                $fatal(1,"DMA16 window expected failed completion code=%0d got finished=%0d failed=%0d active=%0d code=%0d",expected_code,finished,failed,active,failure_code);
            fail_tasks=fail_tasks+1;
            $display("WINDOW16_NEGATIVE_PASS task=%0d code=%0d",task_number,expected_code);
        end
    endtask
    task full_task(input integer first_wait,input integer last_wait,input integer global_delay,input integer fifo_delay);
        integer n,extra;
        reg [63:0] expected_end;
        realtime duration_error;
        begin
            arm_task();
            for(n=0;n<11744;n=n+1) transfer(32'hb0000000+4*n,1,15,n==0 ? first_wait : 0,0,0,0,0,0);
            for(n=0;n<11744;n=n+1) transfer(32'ha0000000+4*n,0,15,0,0,0,0,0,0);
            for(n=0;n<11744;n=n+1) transfer(32'ha0000000+4*n,1,15,0,0,0,0,0,0);
            core_done=1;fifo_empty=0;
            @(posedge clk);@(negedge clk);
            if(finished) $fatal(1,"DMA16 window ended at core DONE before output writes");
            for(n=0;n<12672;n=n+1)
                transfer(32'ha000c000+4*n,0,15,0,n==12671 ? last_wait : 0,0,n==12671,global_delay,fifo_delay);
            extra=global_delay>fifo_delay ? global_delay : fifo_delay;
            expected_end=last_ack;
            if(extra && finished) $fatal(1,"DMA16 window ignored pending/FIFO drain");
            fork
                begin if(global_delay) begin repeat(global_delay) @(posedge clk);global_pending<=0;end end
                begin if(fifo_delay) begin repeat(fifo_delay) @(posedge clk);fifo_empty<=1;end end
            join
            #0.000001;
            if(!finished || failed || active || end_cycle!==expected_end ||
                start_cycle!==expected_start || window_cycles!==expected_end-expected_start)
                $fatal(1,"DMA16 window timing mismatch start=%0d/%0d end=%0d/%0d cycles=%0d",start_cycle,expected_start,end_cycle,expected_end,window_cycles);
            if(extra && ticks!==last_ack+extra) $fatal(1,"DMA16 window drain proof timing");
            duration_error=(dut.end_ns-dut.start_ns)-window_cycles*6.666666;
            if(duration_error>0.00001 || duration_error< -0.00001)
                $fatal(1,"DMA16 window event-time/cycle mismatch");
            if(source_read_acks!=11744 || input_write_acks!=11744 || input_read_acks!=11744 || output_write_acks!=12672)
                $fatal(1,"DMA16 window successful task byte counts");
            if(command_wait_cycles!=first_wait || response_wait_cycles<last_wait)
                $fatal(1,"DMA16 window waits first=%0d/%0d last=%0d/%0d",command_wait_cycles,first_wait,response_wait_cycles,last_wait);
            if(pass_tasks==0) baseline_cycles=window_cycles;
            else if(window_cycles!=baseline_cycles+first_wait+last_wait)
                $fatal(1,"DMA16 window delay delta mismatch baseline=%0d measured=%0d",baseline_cycles,window_cycles);
            pass_tasks=pass_tasks+1;
            $display("WINDOW16_TIMING_PASS task=%0d cycles=%0d first_wait=%0d last_wait=%0d drain=%0d",task_number,window_cycles,first_wait,last_wait,extra);
        end
    endtask
    initial begin
        repeat(4) @(negedge clk);rst_n=1;
        full_task(0,0,0,0);
        full_task(7,31,0,0);
        full_task(3,5,4,6);
        // FINISHED does not authorize stray transfers before the next ARM.
        transfer(32'ha000c000,0,15,0,0,0,0,0,0);
        if(!finished || !failed || failure_code!=12) $fatal(1,"DMA16 ignored post-completion extra output");
        $display("WINDOW16_POST_DONE_REJECT_PASS");
        // Each failed task is cold-armed after the preceding one drained.
        arm_task();transfer(32'hb0000000,1,15,0,0,0,0,0,0);
        transfer(32'ha000c000,0,15,0,0,0,0,0,0);
        transfer(32'ha000c000,0,15,0,0,0,0,0,0);assert_failed(7);
        arm_task();transfer(32'hb0000000,1,15,0,0,1,0,0,0);assert_failed(5);
        arm_task();transfer(32'hb0000000,1,15,0,0,0,0,0,0);
        transfer(32'ha0000004,0,15,0,0,0,0,0,0);assert_failed(8);
        arm_task();transfer(32'hb0000000,1,15,0,0,0,0,0,0);
        transfer(32'ha0000000,0,3,0,0,0,0,0,0);assert_failed(6);
        arm_task();transfer(32'hb0000000,1,15,0,0,0,0,0,0);
        core_done=1;@(posedge clk);@(negedge clk);assert_failed(10);
        arm_task();
        fork
            transfer(32'hb0000000,1,15,8,0,0,0,0,0);
            begin wait(cmd_valid);repeat(2) @(negedge clk);task_cancel=1;@(negedge clk);task_cancel=0;end
        join
        assert_failed(11);
        arm_task();transfer(32'hb0000000,1,15,0,0,0,0,0,0);
        repeat(5) @(negedge clk);
        if(finished || !active) $fatal(1,"DMA16 window accepted missing outputs");
        task_cancel=1;@(negedge clk);task_cancel=0;assert_failed(11);
        arm_task();transfer(32'hb0000000,1,15,0,0,0,0,0,0);
        rsp_valid=1;rsp_ready=1;@(posedge clk);@(negedge clk);rsp_valid=0;rsp_ready=0;assert_failed(4);
        arm_task();transfer(32'hb0000000,1,15,0,0,0,0,0,0);
        for(i=0;i<12672;i=i+1) transfer(32'ha000c000+4*i,0,15,0,0,0,i==12671,0,0);
        assert_failed(9);
        // Two accepted requests before any response must fail, but the failed
        // task still drains both accepted responses before FINISHED.
        arm_task();@(negedge clk);cmd_addr=32'hb0000000;cmd_read=1;cmd_wmask=15;cmd_ready=1;
        @(posedge clk);cmd_valid<=1;global_pending<=1;
        @(posedge clk);cmd_addr<=32'hb0000004;
        @(posedge clk);cmd_valid<=0;cmd_ready<=0;
        @(negedge clk);rsp_valid=1;rsp_ready=1;
        @(posedge clk);
        @(negedge clk);if(finished) $fatal(1,"DMA16 failed task did not drain all accepted responses");
        @(posedge clk);global_pending<=0;rsp_valid<=0;rsp_ready<=0;
        @(negedge clk);assert_failed(3);
        arm_task();transfer(32'hb0000000,1,15,0,0,0,0,0,0);
        task_arm=1;@(posedge clk);@(negedge clk);task_arm=0;assert_failed(1);
        arm_task();transfer(32'ha0000000,0,15,0,0,0,0,0,0);assert_failed(2);
        if(pass_tasks!=3 || fail_tasks!=12) $fatal(1,"DMA16 window suite counts");
        $display("WINDOW16_SUITE_PASS successful_tasks=%0d rejected_tasks=%0d post_done_rejected=1 baseline_cycles=%0d clock_period_fs=6666666",pass_tasks,fail_tasks,baseline_cycles);
        $finish;
    end
    initial begin #20000000;$fatal(1,"DMA16 window global timeout");end
endmodule
