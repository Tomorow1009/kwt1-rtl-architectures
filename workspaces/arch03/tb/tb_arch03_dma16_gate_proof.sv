`timescale 1ns/1fs
module tb_arch03_dma16_gate_proof;
    reg clk=0,rst_n=0;always #3.333333 clk=~clk;
    reg cv=0,cr=0,rd=1,rv=0,rr=0,re=0,dv=0,of=0;
    reg [31:0] addr=0,wd=0,data=0,outputs=0;
    reg [3:0] mask=15;
    reg acv=0,acr=0,arv=0,arr=0,rcv=0,rcr=0,rrv=0,rrr=0;
    wire pending,empty,done,complete,failed;
    integer passed=0;
    arch03_dma16_gate_proof dut(.clk(clk),.rst_n(rst_n),
        .mmio_cmd_valid(cv),.mmio_cmd_ready(cr),.mmio_cmd_read(rd),.mmio_cmd_addr(addr),
        .mmio_cmd_wdata(wd),.mmio_cmd_wmask(mask),.mmio_rsp_valid(rv),.mmio_rsp_ready(rr),
        .mmio_rsp_err(re),.mmio_rsp_rdata(data),.dma_cmd_valid(dv),.core_output_fire(of),
        .output_acks(outputs),.arb_cmd_valid(acv),.arb_cmd_ready(acr),.arb_rsp_valid(arv),.arb_rsp_ready(arr),
        .router_cmd_valid(rcv),.router_cmd_ready(rcr),.router_rsp_valid(rrv),.router_rsp_ready(rrr),
        .global_pending(pending),.fifo_empty_proven(empty),.core_done_proven(done),
        .proof_complete(complete),.proof_failed(failed));
    task reset;
        begin
            @(negedge clk);rst_n=0;cv=0;cr=0;rv=0;rr=0;re=0;dv=0;of=0;outputs=0;
            acv=0;acr=0;arv=0;arr=0;rcv=0;rcr=0;rrv=0;rrr=0;
            repeat(2)@(negedge clk);rst_n=1;@(negedge clk);
            if(empty || complete || failed)$fatal(1,"Reset must not fabricate empty proof");
        end
    endtask
    task request(input [11:0] offset,input reading,input [31:0] value);
        begin
            @(negedge clk);cv=1;cr=1;addr=32'h40000000+offset;rd=reading;wd=value;
            @(negedge clk);cv=0;cr=0;
        end
    endtask
    task response(input [31:0] value,input error);
        begin
            @(negedge clk);rv=1;rr=1;data=value;re=error;
            @(negedge clk);rv=0;rr=0;re=0;
        end
    endtask
    task readreg(input [11:0] offset,input [31:0] value);
        begin request(offset,1,0);response(value,0);end
    endtask
    task writereg(input [11:0] offset,input [31:0] value);
        begin request(offset,0,value);response(0,0);end
    endtask
    task begin_task;
        begin
            reset;readreg(12'h058,0);readreg(12'h008,32'h4000);
            if(!empty)$fatal(1,"Observed idle empty proof missing");
            writereg(12'h004,4);
            if(empty)$fatal(1,"CLEAR needs fresh ready STATUS");
            readreg(12'h008,32'h4000);writereg(12'h004,1);
            if(empty || complete || failed)$fatal(1,"START must invalidate terminal proof");
        end
    endtask
    task final_reads;
        begin
            readreg(12'h008,32'h4608);readreg(12'h05c,31);readreg(12'h058,0);
            if(empty || complete)$fatal(1,"Missing ERROR response fabricated completion");
            readreg(12'h020,0);
        end
    endtask
    task accepted;
        begin if(!complete || !empty || !done || failed)$fatal(1,"Fresh terminal proof not accepted");passed=passed+1;end
    endtask
    task rejected;
        begin if(!failed || complete)$fatal(1,"Protocol/error was not rejected");passed=passed+1;end
    endtask
    initial begin
        begin_task;outputs=12672;final_reads;accepted;
        // A later CPU mailbox transaction must not erase the MMIO proof, but
        // held/accepted requests must still mark fabric pending accurately.
        @(negedge clk);acv=1;rcv=1;#0.001;if(!pending || !complete)$fatal(1,"Held grant proof");
        @(negedge clk);acr=1;rcr=1;
        @(negedge clk);acv=0;rcv=0;acr=0;rcr=0;
        if(!pending || !complete)$fatal(1,"Accepted fabric pending proof");
        arv=1;arr=1;rrv=1;rrr=1;
        @(negedge clk);arv=0;arr=0;rrv=0;rrr=0;
        if(pending || !complete)$fatal(1,"Fabric response did not drain");passed=passed+1;
        begin_task;
        request(12'h058,1,0);outputs=12672;response(0,0);
        readreg(12'h008,32'h4608);readreg(12'h05c,31);readreg(12'h020,0);
        if(complete || empty)$fatal(1,"Stale PENDING response was accepted");
        readreg(12'h058,0);accepted;
        begin_task;outputs=12672;final_reads;readreg(12'h058,32'h100);
        if(complete || empty)$fatal(1,"Nonempty FIFO was accepted");passed=passed+1;
        begin_task;outputs=12672;final_reads;readreg(12'h05c,63);
        if(complete)$fatal(1,"Aborted COMPLETION accepted");passed=passed+1;
        begin_task;outputs=12672;final_reads;readreg(12'h008,32'h6608);
        if(complete)$fatal(1,"Core busy STATUS accepted");passed=passed+1;
        reset;readreg(12'h008,32'h4000);writereg(12'h004,1);rejected;
        begin_task;request(12'h020,1,0);response(0,1);rejected;
        begin_task;readreg(12'h020,7);rejected;
        begin_task;readreg(12'h020,32'hxxxxxxxx);rejected;
        begin_task;outputs=12672;final_reads;@(negedge clk);dv=1;@(negedge clk);dv=0;rejected;
        begin_task;writereg(12'h004,2);rejected;
        reset;@(negedge clk);arv=1;arr=1;@(negedge clk);arv=0;arr=0;rejected;
        reset;@(negedge clk);rcv=1;rcr=1;repeat(2)@(negedge clk);rcv=0;rcr=0;rejected;
        $display("DMA16_GATE_PROOF_SUITE_PASS cases=%0d cpu_executed=false mapped_gates=false",passed);$finish;
    end
    initial begin #100000;$fatal(1,"Gate proof test timeout");end
endmodule
