`timescale 1ns/1fs
// Protocol-only substitute. This is deliberately NOT a MAC or E203 test.
// The production arch03_linear16 must not be compiled with this file.
module arch03_linear16(
    input wire clk,rst_n,cancel,prefetch_enable,start_valid,
    output wire start_ready,input wire [4:0] shift,
    input wire load_valid,output wire load_ready,input wire [15:0] load_data,
    output wire out_valid,input wire out_ready,output wire [6:0] out_row,
    output wire [7:0] out_column,output wire signed [15:0] result,
    output wire saturated,output reg busy,done,error
);
    integer loaded,emitted,tick,flush;
    reg load_stalls=1;
    reg coordinate_fault=0;
    wire [31:0] expected_word=32'h5a5a0000 ^ (loaded/2);
    assign start_ready=rst_n && !busy && !error && flush==0;
    assign load_ready=rst_n && busy && loaded<23488 && (!load_stalls || tick%7!=0);
    assign out_row=(emitted%1584)/16;
    assign out_column=(emitted/1584)*16+(emitted%16)+(coordinate_fault && emitted==0 ? 1 : 0);
    assign out_valid=rst_n && busy && emitted<25344 && loaded>=6336+((emitted/1584)+1)*1072;
    assign result=out_row*256+out_column;
    assign saturated=(emitted%113)==0;
    always @(posedge clk or negedge rst_n) begin
        if(!rst_n) begin loaded<=0;emitted<=0;tick<=0;flush<=0;busy<=0;done<=0;error<=0;coordinate_fault<=0;end
        else begin
            tick<=tick+1;done<=0;
            if(flush!=0) flush<=flush-1;
            if(cancel) begin loaded<=0;emitted<=0;busy<=0;error<=0;flush<=1;end
            else begin
                if(start_valid && start_ready) begin loaded<=0;emitted<=0;busy<=1;end
                if(load_valid && load_ready) begin
                    if(load_data !== (loaded%2 ? expected_word[31:16] : expected_word[15:0]))
                        $fatal(1,"DMA input half order/value mismatch index=%0d got=%h expected=%h",loaded,load_data,expected_word);
                    loaded<=loaded+1;
                end
                if(out_valid && out_ready) begin
                    emitted<=emitted+1;
                    if(emitted==25343) begin busy<=0;done<=1;end
                end
            end
        end
    end
endmodule

module tb_arch03_dma16_protocol;
    reg clk=0,rst_n=0,cmd_valid=0,cmd_read=0,rsp_ready=0;
    reg [31:0] cmd_addr=0,cmd_wdata=0;
    reg [3:0] cmd_wmask=0;
    wire cmd_ready,rsp_valid,rsp_err;
    wire [31:0] rsp_rdata;
    wire dma_cmd_valid,dma_cmd_read,dma_rsp_ready,irq;
    wire [31:0] dma_cmd_addr,dma_cmd_wdata;
    wire [3:0] dma_cmd_wmask;
    reg dma_rsp_valid=0,dma_rsp_err=0;
    reg [31:0] dma_rsp_rdata=0;
    reg hold_commands=0,hold_stage_response=0,hold_output_response=0;
    integer inject_error_kind=0,tick=0,bus_pending=0,delay_count=0,bus_kind=0;
    reg bus_read;
    reg [31:0] bus_addr,bus_data;
    reg bus_error;
    wire dma_cmd_ready=rst_n && !bus_pending && !hold_commands && tick%5!=0;
    reg [31:0] shared_words[0:11743];
    reg output_seen[0:12671];
    integer output_acks,source_acks,stage_acks,load_acks,commands,max_fifo,core_cancels;
    integer index,i,j,pass_count=0;
    reg last_output_pending;
    reg held_cmd;
    reg [68:0] held_payload;
    reg [31:0] value,saved_addr;
    always #3.333333 clk=~clk;
    arch03_dma16_accel dut(.*);
    always @(posedge clk or negedge rst_n) begin
        if(!rst_n) begin
            tick<=0;bus_pending<=0;delay_count<=0;bus_kind<=0;
            dma_rsp_valid<=0;dma_rsp_err<=0;dma_rsp_rdata<=0;
            output_acks<=0;source_acks<=0;stage_acks<=0;load_acks<=0;commands<=0;
            last_output_pending<=0;held_cmd<=0;held_payload<=0;max_fifo<=0;core_cancels<=0;
        end else begin
            tick<=tick+1;
            if(dut.fifo_count_q>max_fifo) max_fifo<=dut.fifo_count_q;
            if(dut.core_cancel_q) core_cancels<=core_cancels+1;
            if(held_cmd && (!dma_cmd_valid || {dma_cmd_read,dma_cmd_addr,dma_cmd_wdata,dma_cmd_wmask}!==held_payload))
                $fatal(1,"DMA command changed while waiting, including cancellation");
            held_cmd<=dma_cmd_valid && !dma_cmd_ready;
            held_payload<={dma_cmd_read,dma_cmd_addr,dma_cmd_wdata,dma_cmd_wmask};
            if(dma_cmd_valid && dma_cmd_ready) begin
                if(bus_pending)$fatal(1,"More than one DMA transaction in flight");
                bus_pending<=1;bus_addr<=dma_cmd_addr;bus_data<=dma_cmd_wdata;bus_read<=dma_cmd_read;
                bus_kind<=dut.kind_q;bus_error<=inject_error_kind==dut.kind_q;
                delay_count<=2+(tick%4);commands<=commands+1;
                if(dma_cmd_addr[1:0]!=0)$fatal(1,"Unaligned DMA command");
                if(!dma_cmd_read && dma_cmd_wmask!=15)$fatal(1,"DMA write is not a full word");
                if(dut.kind_q==1) begin
                    if(!dma_cmd_read || dma_cmd_addr<32'hb0000000 || dma_cmd_addr>=32'hb000b780)
                        $fatal(1,"Bad source command");
                    dma_rsp_rdata<=32'h5a5a0000 ^ ((dma_cmd_addr-32'hb0000000)/4);
                end else if(dut.kind_q==2) begin
                    if(dma_cmd_read || dma_cmd_addr!=32'ha0000000+stage_acks*4 ||
                        dma_cmd_wdata!==(32'h5a5a0000 ^ stage_acks))$fatal(1,"Bad initial shared write");
                    dma_rsp_rdata<=0;
                end else if(dut.kind_q==3) begin
                    if(!dma_cmd_read || stage_acks!=11744 || dma_cmd_addr!=32'ha0000000+load_acks*4)
                        $fatal(1,"Shared input read preceded complete initial load or reordered");
                    dma_rsp_rdata<=shared_words[(dma_cmd_addr-32'ha0000000)/4];
                end else if(dut.kind_q==4) begin
                    index=(dma_cmd_addr-32'ha000c000)/4;
                    if(dma_cmd_read || dma_cmd_addr<32'ha000c000 || dma_cmd_addr>=32'ha0018600 ||
                        output_seen[index] || dma_cmd_wdata!==(((index*2+1)<<16)|(index*2)))
                        $fatal(1,"Bad/duplicate result word addr=%h data=%h index=%0d",dma_cmd_addr,dma_cmd_wdata,index);
                    if(output_acks==12671) begin delay_count<=30;last_output_pending<=1;end
                    dma_rsp_rdata<=0;
                end else $fatal(1,"Unknown DMA transaction kind");
            end
            if(bus_pending && !dma_rsp_valid && !(hold_stage_response && bus_kind==2) &&
                !(hold_output_response && bus_kind==4)) begin
                if(delay_count!=0) delay_count<=delay_count-1;
                else begin dma_rsp_valid<=1;dma_rsp_err<=bus_error;end
            end
            if(last_output_pending && dut.done_q)$fatal(1,"DONE preceded final output response");
            if(dma_rsp_valid && dma_rsp_ready) begin
                dma_rsp_valid<=0;bus_pending<=0;dma_rsp_err<=0;
                if(!dma_rsp_err) begin
                    case(bus_kind)
                        1: source_acks<=source_acks+1;
                        2: begin shared_words[(bus_addr-32'ha0000000)/4]<=bus_data;stage_acks<=stage_acks+1;end
                        3: load_acks<=load_acks+1;
                        4: begin output_seen[(bus_addr-32'ha000c000)/4]<=1;output_acks<=output_acks+1;last_output_pending<=0;end
                    endcase
                end
            end
        end
    end
    task reset_test;
        begin
            @(negedge clk);rst_n=0;cmd_valid=0;rsp_ready=0;hold_commands=0;
            hold_stage_response=0;hold_output_response=0;inject_error_kind=0;
            for(i=0;i<11744;i=i+1)shared_words[i]=32'hxxxxxxxx;
            for(i=0;i<12672;i=i+1)output_seen[i]=0;
            repeat(4)@(negedge clk);rst_n=1;repeat(3)@(negedge clk);
        end
    endtask
    task mmio(input bit rd,input [31:0] addr,input [31:0] data,input [3:0] mask,input bit expected_error,output [31:0] result);
        reg [31:0] held;
        reg held_err;
        begin
            @(negedge clk);cmd_valid=1;cmd_read=rd;cmd_addr=addr;cmd_wdata=data;cmd_wmask=mask;
            @(posedge clk);while(!cmd_ready)@(posedge clk);
            @(negedge clk);cmd_valid=0;
            while(!rsp_valid)@(negedge clk);
            held=rsp_rdata;held_err=rsp_err;
            repeat(2) begin @(negedge clk);if(!rsp_valid || rsp_rdata!==held || rsp_err!==held_err)$fatal(1,"MMIO response unstable under backpressure");end
            if(rsp_err!==expected_error)$fatal(1,"MMIO error mismatch addr=%h read=%d got=%d",addr,rd,rsp_err);
            result=rsp_rdata;rsp_ready=1;
            @(negedge clk);rsp_ready=0;
        end
    endtask
    task wr(input [11:0] offset,input [31:0] data);
        reg [31:0] ignored;
        begin mmio(0,32'h40000000+offset,data,15,0,ignored);end
    endtask
    task rd(input [11:0] offset,output [31:0] result);
        begin mmio(1,32'h40000000+offset,0,0,0,result);end
    endtask
    task await_idle;
        begin
            j=0;
            while(dut.active || bus_pending || dut.core_cancel_q || !dut.core_start_ready) begin
                @(negedge clk);j=j+1;if(j>10000)$fatal(1,"Cancel did not drain");
            end
            rd(12'h008,value);if(!value[14] || value[0])$fatal(1,"Software-visible ready did not reflect drained core");
        end
    endtask
    task bad_config(input [11:0] offset,input [31:0] data);
        begin
            reset_test();wr(offset,data);mmio(0,32'h40000004,1,15,1,value);
            rd(12'h020,value);if(value!=3 || commands!=0)$fatal(1,"Bad configuration issued traffic offset=%h",offset);
        end
    endtask
    initial begin
        reset_test();wr(12'h040,7);wr(12'h004,1);
        wait(dut.done_q);repeat(3)@(negedge clk);
        if(source_acks!=11744 || stage_acks!=11744 || load_acks!=11744 || output_acks!=12672 ||
            dut.load_count_q!=23488 || dut.output_count_q!=25344 || dut.output_committed_q!=50688 || !irq || max_fifo!=16)
            $fatal(1,"Full DMA counters/IRQ/backpressure incorrect");
        for(i=0;i<12672;i=i+1)if(!output_seen[i])$fatal(1,"Missing output address");
        rd(12'h05c,value);if(value[4:0]!=31)$fatal(1,"Incomplete final completion bitmap");
        wr(12'h044,1);if(irq)$fatal(1,"IRQ W1C failed");
        pass_count=pass_count+1;$display("DMA16_PROTOCOL_CASE full_dma PASS commands=%0d fifo_max=%0d",commands,max_fifo);

        reset_test();hold_commands=1;wr(12'h004,1);wait(dma_cmd_valid);saved_addr=dma_cmd_addr;
        wr(12'h004,2);repeat(7)@(negedge clk);
        if(!dma_cmd_valid || dma_cmd_addr!=saved_addr || !dut.cancel_q || dut.core_cancel_q)$fatal(1,"Cancelled a held request before handshake");
        hold_commands=0;await_idle();
        if(commands!=1 || source_acks!=1 || stage_acks!=0 || !dut.aborted_q || dut.done_q || core_cancels!=2)
            $fatal(1,"Held request cancellation accounting failed");
        pass_count=pass_count+1;$display("DMA16_PROTOCOL_CASE cancel_held_valid PASS");

        reset_test();hold_commands=1;wr(12'h004,1);wait(dma_cmd_valid);
        @(negedge clk);dma_rsp_valid=1;
        @(negedge clk);
        if(dut.error_q!=9 || dma_rsp_ready || source_acks!=0 || !dut.cancel_q)
            $fatal(1,"Response before held command acceptance was not rejected");
        dma_rsp_valid=0;hold_commands=0;await_idle();
        if(source_acks!=1 || stage_acks!=0 || !dut.aborted_q || dut.error_q!=9)
            $fatal(1,"Premature response fault corrupted real request drain");
        pass_count=pass_count+1;$display("DMA16_PROTOCOL_CASE response_before_command_acceptance PASS");

        reset_test();hold_stage_response=1;wr(12'h004,1);wait(bus_pending && bus_kind==2);
        wr(12'h004,2);repeat(7)@(negedge clk);
        if(!dut.pending_q || !dut.cancel_q || dut.core_cancel_q || dut.load_committed_q!=0)$fatal(1,"Cancelled pending write before ACK");
        hold_stage_response=0;await_idle();
        if(commands!=2 || dut.load_committed_q!=4 || !dut.aborted_q || dut.done_q)$fatal(1,"Write cancellation accounting failed");
        pass_count=pass_count+1;$display("DMA16_PROTOCOL_CASE cancel_inflight_write PASS");

        reset_test();hold_output_response=1;wr(12'h004,1);wait(bus_pending && bus_kind==4);
        wr(12'h004,2);repeat(7)@(negedge clk);
        if(!dut.pending_q || !dut.cancel_q || dut.core_cancel_q || dut.output_committed_q!=0)
            $fatal(1,"Output cancellation failed to retain transaction owner");
        hold_output_response=0;await_idle();
        if(dut.output_committed_q!=4 || !dut.aborted_q || dut.done_q || dut.fifo_count_q!=0)
            $fatal(1,"Output cancellation accounting/FIFO clear failed");
        pass_count=pass_count+1;$display("DMA16_PROTOCOL_CASE cancel_inflight_output PASS");

        for(integer k=1;k<=4;k=k+1) begin
            reset_test();inject_error_kind=k;wr(12'h004,1);wait(dut.error_q!=0);await_idle();
            rd(12'h020,value);if(value!=k+3)$fatal(1,"Wrong DMA first error kind=%0d got=%0d",k,value);
            mmio(1,32'h40000ffc,0,0,1,value);rd(12'h020,value);
            if(value!=k+3 || dut.done_q || !dut.aborted_q)$fatal(1,"First error was lost or task completed");
            wr(12'h004,4);await_idle();rd(12'h020,value);if(value!=0)$fatal(1,"CLEAR failed");
            pass_count=pass_count+1;$display("DMA16_PROTOCOL_CASE error_response_%0d PASS",k);
        end

        reset_test();dut.core.coordinate_fault=1;wr(12'h004,1);wait(dut.error_q!=0);await_idle();
        if(dut.error_q!=8 || dut.error_phase_q!=6 || output_acks!=0 || dut.done_q)
            $fatal(1,"Core coordinate violation was not rejected before output commit");
        pass_count=pass_count+1;$display("DMA16_PROTOCOL_CASE coordinate_rejection PASS");

        reset_test();wr(12'h02c,32'ha007ffff);mmio(0,32'h40000004,1,15,1,value);
        rd(12'h020,value);if(value!=3 || commands!=0)$fatal(1,"Bad address configuration accepted");
        wr(12'h004,4);await_idle();wr(12'h02c,32'ha0000000);wr(12'h030,32'ha0000004);
        mmio(0,32'h40000004,1,15,1,value);if(commands!=0)$fatal(1,"Overlapping buffers issued traffic");
        bad_config(12'h028,32'hfffffff0);
        bad_config(12'h028,32'ha0000000);
        bad_config(12'h02c,32'ha0078000);
        bad_config(12'h030,32'ha0078000);
        bad_config(12'h034,46975);
        bad_config(12'h038,0);
        bad_config(12'h03c,32'h00100002);
        reset_test();mmio(0,32'h4000000c,32,15,1,value);
        reset_test();mmio(0,32'h4000000c,12,3,1,value);
        reset_test();mmio(1,32'h40000001,0,0,1,value);
        reset_test();mmio(1,32'h40001000,0,0,1,value);
        pass_count=pass_count+1;$display("DMA16_PROTOCOL_CASE address_length_guards PASS");

        reset_test();mmio(1,32'h40000ffc,0,0,1,value);
        @(negedge clk);cmd_valid=1;cmd_read=0;cmd_addr=32'h40000004;cmd_wdata=4;cmd_wmask=15;dma_rsp_valid=1;
        @(posedge clk);if(!cmd_ready)$fatal(1,"CLEAR fault-race setup not ready");
        @(negedge clk);cmd_valid=0;dma_rsp_valid=0;rsp_ready=1;
        @(negedge clk);rsp_ready=0;
        rd(12'h020,value);if(value!=9 || dut.error_phase_q!=8)$fatal(1,"CLEAR hid a simultaneous new bus fault");
        pass_count=pass_count+1;$display("DMA16_PROTOCOL_CASE clear_new_fault_priority PASS");

        reset_test();hold_stage_response=1;wr(12'h004,1);wait(bus_pending && bus_kind==2);
        reset_test();
        if(dma_cmd_valid || dut.pending_q || dut.active || irq)$fatal(1,"Common reset retained a transaction");
        wr(12'h004,1);wait(dut.done_q);repeat(3)@(negedge clk);
        if(output_acks!=12672 || dut.output_committed_q!=50688)$fatal(1,"Common reset task recovery failed");
        pass_count=pass_count+1;$display("DMA16_PROTOCOL_CASE common_reset_inflight_recovery PASS");

        // MMIO is a checked access, not a reserved streaming handshake. Keep
        // readiness stable between the software-style poll and the write.
        reset_test();dut.core.load_stalls=0;wr(12'h024,2);wr(12'h004,1);
        for(i=0;i<23488;i=i+1) begin
            while(!dut.core_load_ready)@(negedge clk);
            value=32'h5a5a0000 ^ (i/2);wr(12'h010,i%2 ? {16'b0,value[31:16]} : {16'b0,value[15:0]});
        end
        for(i=0;i<25344;i=i+1) begin
            while(!dut.core_out_valid)@(negedge clk);
            rd(12'h014,value);
            if(value[15:0]!==(((i%1584)/16)*256+(i/1584)*16+(i%16)))
                $fatal(1,"MMIO debug output mismatch index=%0d",i);
        end
        wait(dut.done_q);if(commands!=0 || dut.load_count_q!=23488 || dut.output_count_q!=25344)
            $fatal(1,"MMIO debug unexpectedly used DMA or had wrong counts");
        pass_count=pass_count+1;$display("DMA16_PROTOCOL_CASE mmio_debug PASS");
        $display("ARCH03_DMA16_PROTOCOL_PASS cases=%0d cpu_executed=false arithmetic_core_stub=true",pass_count);
        $finish;
    end
    initial begin #100000000;$fatal(1,"DMA16 protocol test timeout");end
endmodule

// A separate full task with same-cycle accepted command and response. This
// catches ownership/count bugs that a registered bus model cannot exercise.
module tb_arch03_dma16_zero;
    reg clk=0,rst_n=0,cmd_valid=0,cmd_read=0,rsp_ready=0;
    reg [31:0] cmd_addr=0,cmd_wdata=0;
    reg [3:0] cmd_wmask=0;
    wire cmd_ready,rsp_valid,rsp_err,irq;
    wire [31:0] rsp_rdata;
    wire dma_cmd_valid,dma_cmd_read,dma_rsp_ready;
    wire [31:0] dma_cmd_addr,dma_cmd_wdata;
    wire [3:0] dma_cmd_wmask;
    integer tick=0,requests=0,outputs=0,index,n;
    reg [31:0] memory[0:11743];
    reg seen[0:12671];
    wire dma_cmd_ready=rst_n && tick%6!=0;
    wire dma_rsp_valid=dma_cmd_valid && dma_cmd_ready;
    wire dma_rsp_err=0;
    wire [31:0] dma_rsp_rdata=dma_cmd_addr>=32'hb0000000 ?
        (32'h5a5a0000 ^ ((dma_cmd_addr-32'hb0000000)/4)) :
        (dma_cmd_read ? memory[(dma_cmd_addr-32'ha0000000)/4] : 0);
    always #3.333333 clk=~clk;
    arch03_dma16_accel dut(.*);
    always @(posedge clk) if(rst_n) begin
        tick<=tick+1;
        if(dma_cmd_valid && dma_cmd_ready) begin
            if(!dma_rsp_ready)$fatal(1,"Zero-latency response not accepted");
            requests=requests+1;
            if(!dma_cmd_read && dma_cmd_addr<32'ha000b780)
                memory[(dma_cmd_addr-32'ha0000000)/4]=dma_cmd_wdata;
            if(!dma_cmd_read && dma_cmd_addr>=32'ha000c000) begin
                index=(dma_cmd_addr-32'ha000c000)/4;
                if(index<0 || index>12671 || seen[index] || dma_cmd_wdata!==(((index*2+1)<<16)|(index*2)))
                    $fatal(1,"Zero-latency output incorrect");
                seen[index]=1;outputs=outputs+1;
            end
        end
        if(dut.error_q)$fatal(1,"Zero-latency engine fault %0d",dut.error_q);
        if(tick>1000000)$fatal(1,"Zero-latency test timeout");
    end
    initial begin
        for(n=0;n<12672;n=n+1)seen[n]=0;
        repeat(4)@(negedge clk);rst_n=1;
        @(negedge clk);cmd_valid=1;cmd_addr=32'h40000004;cmd_wdata=1;cmd_wmask=15;
        @(posedge clk);while(!cmd_ready)@(posedge clk);
        @(negedge clk);cmd_valid=0;rsp_ready=1;
        wait(dut.done_q);repeat(2)@(negedge clk);
        if(requests!=47904 || outputs!=12672 || dut.output_committed_q!=50688 || dut.pending_q)
            $fatal(1,"Zero-latency completion accounting");
        $display("ARCH03_DMA16_ZERO_PASS requests=47904 outputs=25344 cpu_executed=false arithmetic_core_stub=true");
        $finish;
    end
endmodule
