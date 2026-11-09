`timescale 1ns/1fs
// Protocol-only fixture: actual arbiter, synthetic latency/backpressure slave.
// No CPU or arithmetic execution is claimed by this testbench.
module tb_arch03_dma16_bus_metrics;
    reg clk=0,rst_n=0,arm=0,cancel=0,finish=0;
    always #5 clk=~clk;
    integer mode=0,cycles=0,transactions=0,n,delay_left=0;
    reg dv=0,dr=1;reg[31:0]da=0,dd=0;reg[3:0]dm=15;
    wire dq,rv,rr,re;wire[31:0]rd;
    reg cv=0;wire cq,crv;wire[31:0]crd;wire cre;
    wire bv,bq,br,bsv,bsq,bse;wire[31:0]ba,bd,bsd;wire[3:0]bm;
    wire global_pending;
    reg slave_pending=0,slave_rsp=0,slave_error=0,force_block=0,force_second=0,force_orphan=0;
    assign bq=!slave_pending && !force_block && cycles%5!=0;
    assign bsv=slave_rsp;assign bsd=0;assign bse=slave_error;
    assign rr=cycles%7!=0 || force_orphan;
    arch03_icb_arb2 arb(.clk(clk),.rst_n(rst_n),
        .cpu_cmd_valid(cv),.cpu_cmd_ready(cq),.cpu_cmd_addr(32'ha001f000),.cpu_cmd_read(1'b1),.cpu_cmd_wdata(32'b0),.cpu_cmd_wmask(4'hf),
        .cpu_rsp_valid(crv),.cpu_rsp_ready(1'b1),.cpu_rsp_rdata(crd),.cpu_rsp_err(cre),
        .dma_cmd_valid(dv),.dma_cmd_ready(dq),.dma_cmd_addr(da),.dma_cmd_read(dr),.dma_cmd_wdata(dd),.dma_cmd_wmask(dm),
        .dma_rsp_valid(rv),.dma_rsp_ready(rr),.dma_rsp_rdata(rd),.dma_rsp_err(re),
        .cmd_valid(bv),.cmd_ready(bq),.cmd_addr(ba),.cmd_read(br),.cmd_wdata(bd),.cmd_wmask(bm),
        .rsp_valid(bsv),.rsp_ready(bsq),.rsp_rdata(bsd),.rsp_err(bse),.transaction_pending(global_pending));
    arch03_dma16_bus_metrics metrics(.clk(clk),.rst_n(rst_n),.task_arm(arm),.task_cancel(cancel),.task_end(finish),
        .dma_cmd_valid(dv),.dma_cmd_ready(force_second?1'b1:dq),.dma_cmd_addr(da),.dma_cmd_read(dr),.dma_cmd_wdata(dd),.dma_cmd_wmask(dm),
        .dma_rsp_valid(force_orphan?1'b1:rv),.dma_rsp_ready(rr),.dma_rsp_err(re),
        .cpu_cmd_valid(cv),.cpu_cmd_ready(cq),.arb_cmd_valid(force_second?1'b1:bv),.arb_cmd_ready(force_second?1'b1:bq),
        .arb_rsp_valid(bsv),.arb_rsp_ready(bsq));
    always @(posedge clk)begin
        if(!rst_n)begin cycles=0;cv<=0;slave_pending<=0;slave_rsp<=0;slave_error<=0;transactions=0;end
        else begin
            cycles=cycles+1;
            if(cv && cq)cv<=0;
            else if(!cv && cycles%11==0)cv<=1;
            if(bv && bq)begin
                slave_pending<=1;delay_left<=transactions%3+1;
                slave_error<=(mode==2 && ba==32'hb0000004);transactions=transactions+1;
            end
            if(slave_pending && !slave_rsp)begin
                if(delay_left==0)slave_rsp<=1;
                else delay_left<=delay_left-1;
            end
            if(bsv && bsq)begin slave_pending<=0;slave_rsp<=0;slave_error<=0;end
            if(dv && dq)$display("BUS_ORACLE_ACCEPT time_ns=%.0f addr=%08h read=%0d",$realtime,da,dr);
            if(rv && rr)$display("BUS_ORACLE_ACK time_ns=%.0f error=%0d",$realtime,re);
            if(cv && cq)$display("BUS_ORACLE_CPU_ACCEPT time_ns=%.0f",$realtime);
            if(crv)$display("BUS_ORACLE_CPU_ACK time_ns=%.0f",$realtime);
        end
    end
    always @(posedge dv)if(rst_n)$display("BUS_ORACLE_OFFER time_ns=%.0f addr=%08h read=%0d",$realtime,da,dr);
    task send(input[31:0]addr,input read_command);
        begin
            @(posedge clk);da<=addr;dr<=read_command;dd<=addr^32'h5a5a1234;dv<=1;
            @(posedge clk);while(!dq)@(posedge clk);
            dv<=0;
            @(posedge clk);while(!(rv && rr))@(posedge clk);
        end
    endtask
    task partial_cancel;
        begin
            send(32'hb0000000,1);send(32'ha0000000,0);send(32'ha0000000,1);
            force_block=1;
            fork
                send(32'hb0000004,1);
                begin repeat(4)@(posedge clk);cancel<=1;repeat(2)@(posedge clk);force_block<=0;end
            join
        end
    endtask
    initial begin
        if(!$value$plusargs("CASE=%d",mode))mode=0;
        #40;rst_n=1;
        @(posedge clk);arm<=1;
        @(posedge clk);arm<=0;
        if(mode==0)begin
            for(n=0;n<11744;n=n+1)begin send(32'hb0000000+n*4,1);send(32'ha0000000+n*4,0);end
            for(n=0;n<11744;n=n+1)send(32'ha0000000+n*4,1);
            for(n=0;n<12672;n=n+1)send(32'ha000c000+n*4,0);
        end else if(mode==1 || mode==6)begin
            partial_cancel();
            if(mode==6)begin
                repeat(3)@(posedge clk);finish<=1;
                @(posedge clk);#1;
                @(posedge clk);arm<=1;cancel<=0;
                // The previous finished signal clears at the next ARM edge.
                // A passive observer must not publish a second empty task.
                @(posedge clk);arm<=0;finish<=0;
                partial_cancel();
            end
        end else if(mode==2)begin
            send(32'hb0000000,1);send(32'hb0000004,1);
        end else if(mode==3)begin
            force_block=1;
            @(posedge clk);da<=32'hb0000000;dv<=1;
            repeat(2)@(posedge clk);da<=32'hb0000004;
            repeat(4)@(posedge clk);$fatal(1,"Expected held-payload rejection");
        end else if(mode==4)begin
            @(posedge clk);da<=32'hb0000000;dv<=1;
            @(posedge clk);while(!dq)@(posedge clk);
            dv<=0;
            @(posedge clk);da<=32'hb0000004;dv<=1;force_second<=1;
            repeat(3)@(posedge clk);$fatal(1,"Expected single-outstanding rejection");
        end else if(mode==5)begin
            @(posedge clk);force_orphan<=1;
            repeat(3)@(posedge clk);$fatal(1,"Expected orphan-response rejection");
        end
        repeat(3)@(posedge clk);finish<=1;
        @(posedge clk);#1;
        $display("BUS_METRICS_FIXTURE_PASS case=%0d cpu_executed=false arithmetic_executed=false",mode);
        $finish;
    end
    initial begin #20000000;$fatal(1,"Bus metrics fixture timeout");end
endmodule
