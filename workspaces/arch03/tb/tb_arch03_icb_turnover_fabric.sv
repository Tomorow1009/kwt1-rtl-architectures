`timescale 1ns/1ps
// Protocol-only independent targets. This does not stand in for SRAM or CPU acceptance.
module fabric_turnover_test_target #(parameter [31:0] SALT=0)(
    input wire clk,rst_n,allow_cmd,cmd_valid,output wire cmd_ready,
    input wire [31:0] cmd_addr,cmd_wdata,input wire cmd_read,input wire [3:0] cmd_wmask,
    output reg rsp_valid,input wire rsp_ready,output reg [31:0] rsp_rdata,output reg rsp_err
);
    reg busy;
    integer delay_count;
    reg [31:0] rng;
    assign cmd_ready=rst_n && allow_cmd && !busy && (!rsp_valid || rsp_ready) && (rng[0] || rng[2]);
    always @(posedge clk or negedge rst_n) begin
        if(!rst_n) begin
            rng<=32'hb05156a9 ^ SALT;busy<=0;delay_count<=0;
            rsp_valid<=0;rsp_rdata<=0;rsp_err<=0;
        end else begin
            rng<={rng[30:0],rng[31]^rng[21]^rng[1]^rng[0]};
            if(rsp_valid && rsp_ready) rsp_valid<=0;
            if(busy) begin
                if(delay_count==0) begin busy<=0;rsp_valid<=1;end
                else delay_count<=delay_count-1;
            end
            if(cmd_valid && cmd_ready) begin
                busy<=1;delay_count<={1'b0,rng[5:3]};
                rsp_rdata<=SALT ^ cmd_addr ^ (cmd_read ? 32'h369ace01 : cmd_wdata) ^ {28'b0,cmd_wmask};
                rsp_err<=cmd_addr[7:0]==8'h80;
            end
        end
    end
endmodule

module tb_arch03_icb_turnover_fabric;
    reg clk=0;always #5 clk=~clk;
    reg rst_n=0,allow_targets=1,saturation_phase=0;
    integer fabric_cycles=0;
    reg cpu_cmd_valid=0,cpu_cmd_read=1,cpu_rsp_ready=0;
    reg [31:0] cpu_cmd_addr=0,cpu_cmd_wdata=0;
    reg [3:0] cpu_cmd_wmask=15;
    wire cpu_cmd_ready,cpu_rsp_valid,cpu_rsp_err;
    wire [31:0] cpu_rsp_rdata;
    reg dma_cmd_valid=0,dma_cmd_read=1,dma_rsp_ready=0;
    reg [31:0] dma_cmd_addr=0,dma_cmd_wdata=0;
    reg [3:0] dma_cmd_wmask=15;
    wire dma_cmd_ready,dma_rsp_valid,dma_rsp_err;
    wire [31:0] dma_rsp_rdata;
    wire cmd_valid,cmd_ready,cmd_read,rsp_valid,rsp_ready,rsp_err;
    wire [31:0] cmd_addr,cmd_wdata,rsp_rdata;
    wire [3:0] cmd_wmask;
    wire arb_pending,router_pending;
    wire mem_cmd_valid,mem_cmd_ready,mem_cmd_read,mem_rsp_valid,mem_rsp_ready,mem_rsp_err;
    wire [31:0] mem_cmd_addr,mem_cmd_wdata,mem_rsp_rdata;
    wire [3:0] mem_cmd_wmask;
    wire src_cmd_valid,src_cmd_ready,src_cmd_read,src_rsp_valid,src_rsp_ready,src_rsp_err;
    wire [31:0] src_cmd_addr,src_cmd_wdata,src_rsp_rdata;
    wire [3:0] src_cmd_wmask;
    always @(posedge clk) fabric_cycles=fabric_cycles+1;
    always @(negedge clk) if(saturation_phase) begin
        cpu_rsp_ready=(fabric_cycles%7)>=3;
        dma_rsp_ready=(fabric_cycles%5)>=2;
    end
    arch03_icb_arb2_turnover arb(
        .clk(clk),.rst_n(rst_n),
        .cpu_cmd_valid(cpu_cmd_valid),.cpu_cmd_ready(cpu_cmd_ready),.cpu_cmd_addr(cpu_cmd_addr),
        .cpu_cmd_read(cpu_cmd_read),.cpu_cmd_wdata(cpu_cmd_wdata),.cpu_cmd_wmask(cpu_cmd_wmask),
        .cpu_rsp_valid(cpu_rsp_valid),.cpu_rsp_ready(cpu_rsp_ready),.cpu_rsp_rdata(cpu_rsp_rdata),.cpu_rsp_err(cpu_rsp_err),
        .dma_cmd_valid(dma_cmd_valid),.dma_cmd_ready(dma_cmd_ready),.dma_cmd_addr(dma_cmd_addr),
        .dma_cmd_read(dma_cmd_read),.dma_cmd_wdata(dma_cmd_wdata),.dma_cmd_wmask(dma_cmd_wmask),
        .dma_rsp_valid(dma_rsp_valid),.dma_rsp_ready(dma_rsp_ready),.dma_rsp_rdata(dma_rsp_rdata),.dma_rsp_err(dma_rsp_err),
        .cmd_valid(cmd_valid),.cmd_ready(cmd_ready),.cmd_addr(cmd_addr),.cmd_read(cmd_read),
        .cmd_wdata(cmd_wdata),.cmd_wmask(cmd_wmask),.rsp_valid(rsp_valid),.rsp_ready(rsp_ready),
        .rsp_rdata(rsp_rdata),.rsp_err(rsp_err),.transaction_pending(arb_pending));
    arch03_icb_memory_router_turnover router(
        .clk(clk),.rst_n(rst_n),.cmd_valid(cmd_valid),.cmd_ready(cmd_ready),.cmd_addr(cmd_addr),
        .cmd_read(cmd_read),.cmd_wdata(cmd_wdata),.cmd_wmask(cmd_wmask),
        .rsp_valid(rsp_valid),.rsp_ready(rsp_ready),.rsp_rdata(rsp_rdata),.rsp_err(rsp_err),
        .mem_cmd_valid(mem_cmd_valid),.mem_cmd_ready(mem_cmd_ready),.mem_cmd_addr(mem_cmd_addr),
        .mem_cmd_read(mem_cmd_read),.mem_cmd_wdata(mem_cmd_wdata),.mem_cmd_wmask(mem_cmd_wmask),
        .mem_rsp_valid(mem_rsp_valid),.mem_rsp_ready(mem_rsp_ready),.mem_rsp_rdata(mem_rsp_rdata),.mem_rsp_err(mem_rsp_err),
        .src_cmd_valid(src_cmd_valid),.src_cmd_ready(src_cmd_ready),.src_cmd_addr(src_cmd_addr),
        .src_cmd_read(src_cmd_read),.src_cmd_wdata(src_cmd_wdata),.src_cmd_wmask(src_cmd_wmask),
        .src_rsp_valid(src_rsp_valid),.src_rsp_ready(src_rsp_ready),.src_rsp_rdata(src_rsp_rdata),.src_rsp_err(src_rsp_err),
        .transaction_pending(router_pending));
    fabric_turnover_test_target #(.SALT(32'h1a000000)) mem(
        .clk(clk),.rst_n(rst_n),.allow_cmd(allow_targets),.cmd_valid(mem_cmd_valid),.cmd_ready(mem_cmd_ready),
        .cmd_addr(mem_cmd_addr),.cmd_read(mem_cmd_read),.cmd_wdata(mem_cmd_wdata),.cmd_wmask(mem_cmd_wmask),
        .rsp_valid(mem_rsp_valid),.rsp_ready(mem_rsp_ready),.rsp_rdata(mem_rsp_rdata),.rsp_err(mem_rsp_err));
    fabric_turnover_test_target #(.SALT(32'h2b000000)) src(
        .clk(clk),.rst_n(rst_n),.allow_cmd(allow_targets),.cmd_valid(src_cmd_valid),.cmd_ready(src_cmd_ready),
        .cmd_addr(src_cmd_addr),.cmd_read(src_cmd_read),.cmd_wdata(src_cmd_wdata),.cmd_wmask(src_cmd_wmask),
        .rsp_valid(src_rsp_valid),.rsp_ready(src_rsp_ready),.rsp_rdata(src_rsp_rdata),.rsp_err(src_rsp_err));
    integer turnovers=0;
    integer accepted=0,responses=0,mem_requests=0,src_requests=0,error_requests=0;
    integer target_errors=0,ties=0,command_stalls=0,response_stalls=0,cpu_count=0,dma_count=0;
    integer master_pending[0:1];
    reg [31:0] expected_data[0:1];
    reg expected_error[0:1];
    reg command_held=0;
    reg [68:0] command_payload;
    reg [1:0] response_held=0;
    reg [32:0] response_payload[0:1];
    reg last_completed_owner=1;
    integer owner,dest,m;
    reg [31:0] a,d;
    reg r;
    reg [3:0] mask;
    function integer destination(input [31:0] address,input reading);
        begin
            if(address>=32'ha0000000 && address<=32'ha007ffff) destination=0;
            else if(address>=32'hb0000000 && address<=32'hb000bffc && reading && address[1:0]==0) destination=1;
            else destination=2;
        end
    endfunction
    always @(posedge clk) begin
        if(!rst_n) begin
            master_pending[0]=0;master_pending[1]=0;command_held=0;response_held=0;
            last_completed_owner=1;
        end else begin
            // Retire the OLD response before recording a replacement command.
            for(m=0;m<2;m=m+1) begin
                if(response_held[m] &&
                    (m ? (!dma_rsp_valid || {dma_rsp_err,dma_rsp_rdata}!==response_payload[m]) :
                         (!cpu_rsp_valid || {cpu_rsp_err,cpu_rsp_rdata}!==response_payload[m])))
                    $fatal(1,"Fabric changed held response owner=%0d",m);
                if(m ? dma_rsp_valid : cpu_rsp_valid) begin
                    if(!master_pending[m]) $fatal(1,"Fabric orphan response owner=%0d",m);
                    if((m ? dma_rsp_rdata : cpu_rsp_rdata)!==expected_data[m] ||
                       (m ? dma_rsp_err : cpu_rsp_err)!==expected_error[m])
                        $fatal(1,"Fabric response payload/owner mismatch owner=%0d",m);
                    if(m ? dma_rsp_ready : cpu_rsp_ready) begin
                        master_pending[m]=0;responses=responses+1;last_completed_owner=m;
                    end else response_stalls=response_stalls+1;
                end
                response_held[m]=m ? (dma_rsp_valid && !dma_rsp_ready) : (cpu_rsp_valid && !cpu_rsp_ready);
                response_payload[m]=m ? {dma_rsp_err,dma_rsp_rdata} : {cpu_rsp_err,cpu_rsp_rdata};
            end
            if(command_held && (!cmd_valid || {cmd_addr,cmd_read,cmd_wdata,cmd_wmask}!==command_payload))
                $fatal(1,"Fabric changed granted command under backpressure");
            // Round-robin checked at the initial grant, before a stalled grant
            // is reserved. Later arriving competitors cannot revoke it.
            if(cmd_valid && !command_held && cpu_cmd_valid && dma_cmd_valid) begin
                ties=ties+1;
                if(arb.selected!==!last_completed_owner) $fatal(1,"Fabric unfair round-robin grant");
            end
            command_held=cmd_valid && !cmd_ready;
            command_payload={cmd_addr,cmd_read,cmd_wdata,cmd_wmask};
            if(command_held) command_stalls=command_stalls+1;
            if(cpu_cmd_valid && cpu_cmd_ready && dma_cmd_valid && dma_cmd_ready)
                $fatal(1,"Fabric accepted two masters");
            if(cmd_valid && cmd_ready) begin
                if(rsp_valid && rsp_ready)turnovers=turnovers+1;
                if(master_pending[0] || master_pending[1]) $fatal(1,"Fabric multiple outstanding commands");
                owner=dma_cmd_valid && dma_cmd_ready;
                if(owner ? !(dma_cmd_valid && dma_cmd_ready) : !(cpu_cmd_valid && cpu_cmd_ready))
                    $fatal(1,"Fabric command ownership");
                a=owner ? dma_cmd_addr : cpu_cmd_addr;
                d=owner ? dma_cmd_wdata : cpu_cmd_wdata;
                r=owner ? dma_cmd_read : cpu_cmd_read;
                mask=owner ? dma_cmd_wmask : cpu_cmd_wmask;
                if({cmd_addr,cmd_read,cmd_wdata,cmd_wmask}!=={a,r,d,mask}) $fatal(1,"Fabric request payload routing");
                dest=destination(a,r);
                if(dest==0) begin
                    if(!mem_cmd_valid || !mem_cmd_ready || src_cmd_valid) $fatal(1,"Fabric memory destination");
                    expected_data[owner]=32'h1a000000 ^ a ^ (r ? 32'h369ace01 : d) ^ {28'b0,mask};
                    expected_error[owner]=a[7:0]==8'h80;mem_requests=mem_requests+1;
                end else if(dest==1) begin
                    if(!src_cmd_valid || !src_cmd_ready || mem_cmd_valid) $fatal(1,"Fabric source destination");
                    expected_data[owner]=32'h2b000000 ^ a ^ 32'h369ace01 ^ {28'b0,mask};
                    expected_error[owner]=a[7:0]==8'h80;src_requests=src_requests+1;
                end else begin
                    if(mem_cmd_valid || src_cmd_valid) $fatal(1,"Fabric illegal access reached a target");
                    expected_data[owner]=0;expected_error[owner]=1;error_requests=error_requests+1;
                end
                if(dest!=2 && expected_error[owner]) target_errors=target_errors+1;
                master_pending[owner]=1;accepted=accepted+1;
                if(owner) dma_count=dma_count+1;else cpu_count=cpu_count+1;
            end
            if(cpu_rsp_valid && dma_rsp_valid) $fatal(1,"Fabric delivered response to both masters");
            if(src_cmd_valid && !src_cmd_read) $fatal(1,"Fabric forwarded source write");
        end
    end
    task automatic transaction(input integer who,input [31:0] address,input reading,
        input [31:0] data,input [3:0] byte_mask,input integer hold_response);
        begin
            @(negedge clk);
            if(who) begin dma_cmd_valid=1;dma_cmd_addr=address;dma_cmd_read=reading;dma_cmd_wdata=data;dma_cmd_wmask=byte_mask;dma_rsp_ready=0;end
            else begin cpu_cmd_valid=1;cpu_cmd_addr=address;cpu_cmd_read=reading;cpu_cmd_wdata=data;cpu_cmd_wmask=byte_mask;cpu_rsp_ready=0;end
            @(posedge clk);while(!(who ? dma_cmd_ready : cpu_cmd_ready)) @(posedge clk);
            @(negedge clk);if(who) dma_cmd_valid=0;else cpu_cmd_valid=0;
            // Hold until an actual response exists, then keep it blocked.
            while(!(who ? dma_rsp_valid : cpu_rsp_valid)) @(negedge clk);
            repeat(hold_response) @(negedge clk);
            if(who) dma_rsp_ready=1;else cpu_rsp_ready=1;
            @(posedge clk);
            @(negedge clk);if(who) dma_rsp_ready=0;else cpu_rsp_ready=0;
        end
    endtask
    task automatic traffic(input integer who);
        integer n;
        reg [31:0] address;
        reg reading;
        begin
            for(n=0;n<128;n=n+1) begin
                reading=1;
                case(n%12)
                    0: begin address=32'ha0000000+n*4+who*1024;reading=0;end
                    1: address=32'ha007fffc;
                    2: address=32'hb0000000;
                    3: address=32'hb000bffc;
                    4: address=32'hb000c000;
                    5: begin address=32'hb0000000;reading=0;end
                    6: address=32'hb0000001;
                    7: address=32'hc0000000+n*4;
                    8: address=32'hb0000080;
                    9: address=32'ha0000080;
                    10: address=32'haffffffc;
                    default: address=32'ha0080000;
                endcase
                transaction(who,address,reading,32'habcd0000+n+who*512,(n%15)+1,n%5);
            end
        end
    endtask
    task automatic saturated_traffic(input integer who);
        integer n;
        begin
            @(negedge clk);
            for(n=0;n<64;n=n+1) begin
                // Keep a following request queued while the previous response
                // is outstanding. Both masters now contend at every new grant.
                if(who) begin
                    dma_cmd_valid=1;dma_cmd_addr=32'ha0002400+n*4;
                    dma_cmd_read=1;dma_cmd_wdata=0;dma_cmd_wmask=15;
                end else begin
                    cpu_cmd_valid=1;cpu_cmd_addr=32'ha0002000+n*4;
                    cpu_cmd_read=1;cpu_cmd_wdata=0;cpu_cmd_wmask=15;
                end
                @(posedge clk);while(!(who ? dma_cmd_ready : cpu_cmd_ready)) @(posedge clk);
                @(negedge clk);
            end
            if(who) dma_cmd_valid=0;else cpu_cmd_valid=0;
            while(master_pending[who]) @(negedge clk);
        end
    endtask
    initial begin
        repeat(4) @(negedge clk);rst_n=1;
        // DMA is granted while CPU is absent. A later CPU request must not
        // displace that stalled grant even though reset gives CPU first turn.
        allow_targets=0;
        fork
            transaction(1,32'ha0000040,1,0,15,11);
            begin repeat(3) @(negedge clk);transaction(0,32'hb000bffc,1,0,15,7);end
            begin repeat(9) @(negedge clk);allow_targets=1;end
        join
        $display("FABRIC_STALLED_GRANT_PASS");
        fork traffic(0);traffic(1);join
        saturation_phase=1;
        fork saturated_traffic(0);saturated_traffic(1);join
        saturation_phase=0;cpu_rsp_ready=0;dma_rsp_ready=0;
        repeat(5) @(negedge clk);
        if(accepted!=386 || responses!=accepted || cpu_count!=193 || dma_count!=193 ||
            master_pending[0] || master_pending[1] || arb_pending || router_pending)
            $fatal(1,"Fabric final count/drain accepted=%0d responses=%0d",accepted,responses);
        if(ties<100 || command_stalls<5 || response_stalls<20 ||
            mem_requests<20 || src_requests<20 || error_requests<50 || target_errors<20)
            $fatal(1,"Fabric coverage missing ties=%0d command_stalls=%0d response_stalls=%0d",ties,command_stalls,response_stalls);
        if(turnovers<50)$fatal(1,"Missing same-edge coverage turnovers=%0d",turnovers);
        $display("FABRIC_TURNOVER_PASS turnovers=%0d",turnovers);
        $display("FABRIC_PROTOCOL_PASS transactions=%0d cpu=%0d dma=%0d ties=%0d command_stalls=%0d response_stalls=%0d memory=%0d source=%0d rejected=%0d target_errors=%0d",accepted,cpu_count,dma_count,ties,command_stalls,response_stalls,mem_requests,src_requests,error_requests,target_errors);
        $finish;
    end
    initial begin #2000000;$fatal(1,"Fabric global timeout");end
endmodule
