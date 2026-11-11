`timescale 1ns/1ps
// Procedural MMIO debug traffic, not an E203 execution test.
module tb_arch03_systolic_b_debug;
    reg clk=0;always #5 clk=~clk;
    reg rst_n=0,cmd_valid=0,cmd_read=0,rsp_ready=0;
    reg [31:0] cmd_addr=0,cmd_wdata=0;
    reg [3:0] cmd_wmask=15;
    wire cmd_ready,rsp_valid,rsp_err,irq,dma_cmd_valid,dma_cmd_read,dma_rsp_ready;
    wire [31:0] rsp_rdata,dma_cmd_addr,dma_cmd_wdata;
    wire [3:0] dma_cmd_wmask;
    wire dma_cmd_ready=1,dma_rsp_valid=0,dma_rsp_err=0;
    wire [31:0] dma_rsp_rdata=0;
    arch03_systolic_b_accel dut(.*);
    reg [15:0] stream[0:23487],expected[0:25343];
    reg expected_sat[0:25343],seen[0:25343];
    integer n=0,outputs=0,i,idx,sats=0,shift_arg,held_cycles=0;
    reg [31:0] value,status_value;
    reg [4095:0] filename;
    string data_dir;
    task access(input reg reading,input [11:0] offset,input [31:0] data,
                input reg expect_error,output reg [31:0] answer);
        reg [31:0] held;
        integer wait_n;
        begin
            @(negedge clk);cmd_valid=1;cmd_read=reading;cmd_addr=32'h40000000+offset;cmd_wdata=data;
            @(posedge clk);while(!cmd_ready)@(posedge clk);
            @(negedge clk);cmd_valid=0;while(!rsp_valid)@(negedge clk);
            answer=rsp_rdata;held=rsp_rdata;
            if(rsp_err!==expect_error)$fatal(1,"DEBUG response error offset=%h",offset);
            if(reading && offset==12'h014 && outputs%313==0)begin
                for(wait_n=0;wait_n<11;wait_n=wait_n+1)begin
                    @(negedge clk);held_cycles=held_cycles+1;
                    if(!rsp_valid || rsp_rdata!==held || rsp_err)$fatal(1,"DEBUG response changed under hold");
                end
            end
            rsp_ready=1;@(negedge clk);rsp_ready=0;
        end
    endtask
    always @(posedge clk)if(rst_n && dma_cmd_valid)$fatal(1,"Scalar debug unexpectedly issued DMA");
    initial begin
        if(!$value$plusargs("DATA_DIR=%s",data_dir))$fatal(1,"DATA_DIR required");
        if(!$value$plusargs("SHIFT=%d",shift_arg))shift_arg=12;
        $sformat(filename,"%s/load.hex",data_dir);$readmemh(filename,stream);
        $sformat(filename,"%s/result.hex",data_dir);$readmemh(filename,expected);
        $sformat(filename,"%s/saturated.hex",data_dir);$readmemh(filename,expected_sat);
        for(i=0;i<25344;i=i+1)seen[i]=0;
        repeat(4)@(negedge clk);rst_n=1;
        access(1,0,0,0,value);if(value!=32'h4b575305)$fatal(1,"B identity");
        access(1,12'h074,0,0,value);if(value!=32'h0003053f)$fatal(1,"B capabilities");
        // Explicitly reject v3 until the new decoder is actually implemented.
        access(0,12'h03c,32'h00100003,0,value);access(0,4,1,1,value);
        access(1,12'h020,0,0,value);if(value!=3)$fatal(1,"Unsupported layout accepted");
        access(0,4,4,0,value);access(0,12'h03c,32'h00100002,0,value);
        access(0,12'h024,2,0,value);access(0,12'h00c,shift_arg,0,value);
        access(0,12'h040,7,0,value);access(0,4,1,0,value);
        while(n<23488 || outputs<25344)begin
            access(1,8,0,0,status_value);
            if(status_value[4])$fatal(1,"DEBUG core fault");
            if(status_value[1] && n<23488)begin access(0,12'h010,stream[n],0,value);n=n+1;end
            if(status_value[2] && outputs<25344)begin
                access(1,12'h014,0,0,value);
                idx=value[22:16]*256+value[30:23];
                if(value[22:16]>98 || seen[idx] || value[15:0]!==expected[idx] || value[31]!==expected_sat[idx])
                    $fatal(1,"DEBUG scalar pair adapter mismatch output=%0d idx=%0d",outputs,idx);
                if(value[22:16]!=(outputs%1584)/16 || value[30:23]!=(outputs/1584)*16+outputs%16)
                    $fatal(1,"DEBUG scalar coordinate order");
                seen[idx]=1;outputs=outputs+1;sats=sats+value[31];
            end
        end
        access(1,8,0,0,value);if(!value[3] || value[0] || !irq)$fatal(1,"DEBUG done/IRQ");
        access(1,12'h01c,0,0,value);if(value!=25344)$fatal(1,"DEBUG output count");
        access(1,12'h070,0,0,value);if(value!=sats)$fatal(1,"DEBUG saturation count");
        for(i=0;i<25344;i=i+1)if(!seen[i])$fatal(1,"DEBUG missing coordinate");
        $display("SYSTOLIC_B_DEBUG_PASS outputs=25344 held_cycles=%0d no_dma=true v3_rejected=true cpu_executed=false",held_cycles);
        $finish;
    end
    initial begin #10000000;$fatal(1,"DEBUG timeout");end
endmodule
