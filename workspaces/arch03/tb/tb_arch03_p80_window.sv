`timescale 1ns/1fs
module tb_arch03_p80_window #(parameter integer DEPTH=4);
    reg clk=0;always #3.333333 clk=~clk;
    reg rst_n=0,task_arm=0,task_cancel=0;
    reg [31:0] encoded_bytes=32;
    reg cmd_valid=0,cmd_ready=0,cmd_read=1;
    reg [31:0] cmd_addr=0;reg [3:0] cmd_wmask=15;
    reg rsp_valid=0,rsp_ready=0,rsp_err=0;
    reg global_pending=0,fifo_empty=1,core_done=0;
    wire active,finished,failed;
    wire [31:0] failure_code,source_read_acks,input_write_acks,input_read_acks,output_write_acks;
    wire [63:0] start_cycle,end_cycle,window_cycles,command_wait_cycles,response_wait_cycles;
    arch03_task_window_p80 #(.MAX_INPUT_WORDS(8),.OUTPUT_BYTES(32),.MAX_OUTSTANDING(DEPTH)) dut(.*);
    reg [63:0] tick=0,expected_start,last_ack,baseline;
    realtime expected_ns,last_ns;
    integer good=0,bad=0,j;
    always @(posedge clk) if(!rst_n)tick<=0;else tick<=tick+1;
    task step(input cv,input [31:0] addr,input rd,input rv,input rr);
        begin
            @(negedge clk);cmd_valid=cv;cmd_ready=1;cmd_addr=addr;cmd_read=rd;
            rsp_valid=rv;rsp_ready=rr;
            @(posedge clk);#0.000001;
            if(rv && rr)begin last_ack=tick;last_ns=$realtime-0.000001;end
        end
    endtask
    task arm;
        begin
            @(negedge clk);task_arm=1;task_cancel=0;cmd_valid=0;cmd_ready=0;
            rsp_valid=0;rsp_ready=0;rsp_err=0;global_pending=0;fifo_empty=1;core_done=0;cmd_wmask=15;
            @(posedge clk);#0.000001;
            if(active||finished||failed||source_read_acks||input_read_acks||output_write_acks)
                $fatal(1,"P80 cold arm state");
            @(negedge clk);task_arm=0;
        end
    endtask
    task start_request(input integer waits);
        begin
            @(negedge clk);cmd_addr=32'hb0000000;cmd_read=1;cmd_ready=0;
            @(posedge clk);cmd_valid<=1;global_pending<=1;
            expected_start=tick+1;expected_ns=$realtime;
            #0.000001;
            if(!active||start_cycle!=expected_start||dut.start_ns!=expected_ns)
                $fatal(1,"P80 first VALID missed sending edge");
            repeat(waits)begin @(posedge clk);#0.000001;end
        end
    endtask
    task phase(input [31:0] base,input reading,input integer tail_wait);
        integer n;
        begin
            // Fill the queue; then retire OLD head and enqueue at full capacity.
            for(n=0;n<DEPTH;n=n+1)step(1,base+4*n,reading,0,0);
            for(n=DEPTH;n<8;n=n+1)step(1,base+4*n,reading,1,1);
            for(n=1;n<DEPTH;n=n+1)step(0,0,1,1,1);
            repeat(tail_wait)step(0,0,1,1,0);
            step(0,0,1,1,1);step(0,0,1,0,0);
        end
    endtask
    task full(input integer first_wait,input integer tail_wait,input integer drain_wait);
        reg [63:0] end_expected;
        realtime end_time,diff;
        begin
            arm();start_request(first_wait);
            phase(32'hb0000000,1,0);phase(32'ha0000000,0,0);phase(32'ha0000000,1,0);
            @(negedge clk);core_done=1;fifo_empty=0;
            phase(32'ha000c000,0,tail_wait);end_expected=last_ack;end_time=last_ns;
            if(finished)$fatal(1,"P80 finished without global/FIFO drain");
            repeat(drain_wait)step(0,0,1,0,0);
            @(negedge clk);global_pending=0;fifo_empty=1;#0.000001;
            if(!finished||failed||active||start_cycle!=expected_start||end_cycle!=end_expected||
                window_cycles!=end_expected-expected_start)
                $fatal(1,"P80 window endpoint mismatch start=%0d/%0d end=%0d/%0d failed=%0d",start_cycle,expected_start,end_cycle,end_expected,failed);
            diff=dut.end_ns-end_time;
            if(diff>0.0000005||diff< -0.0000005)$fatal(1,"P80 final ACK event timestamp mismatch");
            diff=(dut.end_ns-dut.start_ns)-window_cycles*6.666666;
            if(diff>0.00001||diff< -0.00001)$fatal(1,"P80 event duration mismatch");
            if(source_read_acks!=8||input_write_acks!=8||input_read_acks!=8||output_write_acks!=8)
                $fatal(1,"P80 four-phase coverage");
            if(command_wait_cycles!=first_wait||response_wait_cycles!=tail_wait)
                $fatal(1,"P80 waits dropped");
            if(good==0)baseline=window_cycles;
            else if(window_cycles!=baseline+first_wait+tail_wait)$fatal(1,"P80 delay included wrong span");
            good=good+1;
        end
    endtask
    task expect_bad(input integer code,input integer pending);
        integer n;
        begin
            step(0,0,1,0,0);
            for(n=0;n<pending;n=n+1)begin
                if(finished)$fatal(1,"P80 rejected task finished before accepted responses drained");
                step(0,0,1,1,1);
            end
            step(0,0,1,0,0);
            @(negedge clk);global_pending=0;fifo_empty=1;#0.000001;
            if(!failed||!finished||failure_code!=code)
                $fatal(1,"P80 rejection code expected=%0d actual=%0d finished=%0d",code,failure_code,finished);
            bad=bad+1;
        end
    endtask
    initial begin
        repeat(4)@(negedge clk);rst_n=1;
        full(0,0,0);full(7,31,0);full(3,5,9);
        // Post-DONE traffic is independently rejected.
        step(1,32'ha000c000,0,0,0);
        if(!failed||failure_code!=12)$fatal(1,"P80 post-DONE traffic accepted");
        arm();start_request(0);step(1,32'hb0000000,1,0,0);
        step(1,32'ha0000000,1,0,0);expect_bad(8,2);
        arm();start_request(0);step(1,32'hb0000000,1,0,0);
        step(1,32'hb0000000,1,0,0);expect_bad(7,2);
        arm();start_request(0);step(1,32'hb0000000,1,0,0);
        rsp_err=1;expect_bad(5,1);
        arm();start_request(0);cmd_wmask=3;step(1,32'ha0000000,0,0,0);expect_bad(6,1);
        arm();start_request(0);step(1,32'hb0000000,1,0,0);
        core_done=1;expect_bad(10,1);
        arm();start_request(0);
        for(j=0;j<DEPTH;j=j+1)step(1,32'hb0000000+4*j,1,0,0);
        task_cancel=1;expect_bad(11,DEPTH);
        arm();start_request(0);
        for(j=0;j<=DEPTH;j=j+1)step(1,32'hb0000000+4*(j%8),1,0,0);
        expect_bad(3,DEPTH+1);
        arm();start_request(0);step(0,0,1,1,1);expect_bad(4,0);
        arm();start_request(0);step(1,32'hb0000000,1,0,0);
        @(negedge clk);task_arm=1;cmd_valid=0;@(posedge clk);#0.000001;
        @(negedge clk);task_arm=0;expect_bad(1,1);
        // Reset clears all metadata, then a no-reset pair of complete tasks.
        arm();start_request(0);step(1,32'hb0000000,1,0,0);
        @(negedge clk);rst_n=0;cmd_valid=0;global_pending=0;
        repeat(2)@(negedge clk);rst_n=1;
        full(0,0,2);full(0,0,4);
        $display("P80_WINDOW_PASS depth=%0d successful=%0d rejected=%0d post_done=1 reset_pending=1",DEPTH,good,bad);
        $finish;
    end
    initial begin #100000;$fatal(1,"P80 window timeout");end
endmodule
module tb_p80_window2;tb_arch03_p80_window #(.DEPTH(2)) t();endmodule
module tb_p80_window4;tb_arch03_p80_window #(.DEPTH(4)) t();endmodule
module tb_p80_window8;tb_arch03_p80_window #(.DEPTH(8)) t();endmodule
