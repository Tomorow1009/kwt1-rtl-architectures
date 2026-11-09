`timescale 1ns/1fs
module tb_arch03_dma16_source;
    reg clk=0;always #3.333333 clk=~clk;
    reg rst_n=0,cmd_valid=0,cmd_read=1,rsp_ready=0;
    reg [31:0] cmd_addr=0,cmd_wdata=0;
    reg [3:0] cmd_wmask=0;
    wire cmd_ready,rsp_valid,rsp_err;
    wire [31:0] rsp_rdata;
    arch03_dma16_source dut(.*);
    reg [31:0] expected[0:11743];
    reg [4095:0] path;
    reg held=0;
    reg [32:0] held_response;
    integer i,completed=0,error_responses=0,held_cycles=0;
    realtime accepted_ns,elapsed_error;
    always @(posedge clk) begin
        if(!rst_n) held=0;
        else begin
            if(held && (!rsp_valid || {rsp_err,rsp_rdata}!==held_response))
                $fatal(1,"Source response changed while blocked");
            held=rsp_valid && !rsp_ready;
            held_response={rsp_err,rsp_rdata};
            if(held) held_cycles=held_cycles+1;
            if(rsp_valid && cmd_ready) $fatal(1,"Source accepted a second outstanding transaction");
        end
    end
    task request(input [31:0] address,input reading,input [31:0] value,input error_value,input integer hold_cycles);
        begin
            @(negedge clk);cmd_addr=address;cmd_read=reading;cmd_wdata=32'h87654321;
            cmd_wmask=15;cmd_valid=1;rsp_ready=(hold_cycles==0);
            @(posedge clk);while(!cmd_ready)@(posedge clk);
            accepted_ns=$realtime;
            #0.000001;
            // Response must be registered by the acceptance edge N itself,
            // and therefore eligible for consumption at edge N+1.
            if(!rsp_valid || rsp_rdata!==value || rsp_err!==error_value)
                $fatal(1,"Source registered response missing/wrong at acceptance edge addr=%h",address);
            @(negedge clk);cmd_valid=0;
            if(hold_cycles>0) begin
                repeat(hold_cycles)@(posedge clk);
                @(negedge clk);rsp_ready=1;
            end
            @(posedge clk);
            if(!rsp_valid || !rsp_ready) $fatal(1,"Source ACK missing");
            elapsed_error=($realtime-accepted_ns)-(hold_cycles+1)*6.666666;
            if(elapsed_error>0.00001 || elapsed_error< -0.00001)
                $fatal(1,"Source ACK latency differs from N+1 plus explicit stalls");
            completed=completed+1;if(error_value)error_responses=error_responses+1;
            #0.000001;if(rsp_valid) $fatal(1,"Source response not retired");
        end
    endtask
    initial begin
        if(!$value$plusargs("LOAD32=%s",path))$fatal(1,"LOAD32 required");
        for(i=0;i<11744;i=i+1)expected[i]=32'bx;
        $readmemh(path,expected);
        for(i=0;i<11744;i=i+1)if((^expected[i])===1'bx)$fatal(1,"Missing source reference");
        repeat(3)@(negedge clk);rst_n=1;
        for(i=0;i<11744;i=i+1)request(32'hb0000000+4*i,1,expected[i],0,i==0 ? 3 : 0);
        request(32'hb000b77c,1,expected[11743],0,17);
        request(32'hb0000000,0,0,1,0);
        request(32'haffffffc,1,0,1,0);
        request(32'hb000b780,1,0,1,0);
        request(32'hb0000002,1,0,1,0);
        request(32'hffffffff,1,0,1,0);
        if(dut.accepted!=11750 || dut.responded!=11750 || completed!=11750 || error_responses!=5)
            $fatal(1,"Source completed request accounting");
        // Reset cancels an outstanding response without changing PC-side file bytes.
        @(negedge clk);cmd_addr=32'hb0000000;cmd_read=1;cmd_valid=1;rsp_ready=0;
        @(posedge clk);#0.000001;if(!rsp_valid)$fatal(1,"Source reset probe response absent");
        @(negedge clk);cmd_valid=0;rst_n=0;
        #0.000001;if(rsp_valid || cmd_ready)$fatal(1,"Source reset did not suppress interface");
        repeat(2)@(negedge clk);rst_n=1;
        request(32'hb0000000,1,expected[0],0,0);
        request(32'hb000b77c,1,expected[11743],0,0);
        if(dut.accepted!=2 || dut.responded!=2 || held_cycles<20)
            $fatal(1,"Source reset recovery/accounting");
        $display("DMA16_SOURCE_UNIT_PASS completed=%0d error_responses=%0d response_stalls=%0d reset_cancelled=1 earliest_ack_cycles=1",completed,error_responses,held_cycles);
        $finish;
    end
    initial begin #2000000;$fatal(1,"Source unit timeout");end
endmodule
