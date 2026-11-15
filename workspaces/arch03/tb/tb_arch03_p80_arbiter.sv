`timescale 1ns/1ps
module tb_arch03_p80_arbiter #(parameter DEPTH=4);
    reg clk=0,rst_n=0,send_enabled=1;
    always #5 clk=~clk;
    reg cv=0,dv=0,cr=0,dr=0,rr=0;
    reg [31:0] ca=0,da=0,cw=0,dw=0,rd=0;
    reg cread=0,dread=0,re=0,rv=0;
    reg [3:0] cm=0,dm=0;
    wire cready,dready,crv,drv,cerr,derr,v,ready,pending,rready;
    wire [31:0] crdata,drdata,a,w;
    wire read_cmd;wire [3:0] mask,occupancy;
    reg bus_ready=0;
    assign ready=bus_ready;
    arch03_icb_arb2_queued #(.TRANSACTION_DEPTH(DEPTH)) dut(
        .clk(clk),.rst_n(rst_n),.cpu_cmd_valid(cv),.cpu_cmd_ready(cready),
        .cpu_cmd_addr(ca),.cpu_cmd_read(cread),.cpu_cmd_wdata(cw),.cpu_cmd_wmask(cm),
        .cpu_rsp_valid(crv),.cpu_rsp_ready(cr),.cpu_rsp_rdata(crdata),.cpu_rsp_err(cerr),
        .dma_cmd_valid(dv),.dma_cmd_ready(dready),.dma_cmd_addr(da),.dma_cmd_read(dread),
        .dma_cmd_wdata(dw),.dma_cmd_wmask(dm),.dma_rsp_valid(drv),.dma_rsp_ready(dr),
        .dma_rsp_rdata(drdata),.dma_rsp_err(derr),.cmd_valid(v),.cmd_ready(ready),
        .cmd_addr(a),.cmd_read(read_cmd),.cmd_wdata(w),.cmd_wmask(mask),
        .rsp_valid(rv),.rsp_ready(rready),.rsp_rdata(rd),.rsp_err(re),
        .transaction_pending(pending),.accepted_queue_count(occupancy));

    // Independent accepted-command ledger, not a read of the DUT's owner FIFO.
    reg owners[0:8191],errors[0:8191];
    reg [31:0] values[0:8191];
    integer release_at[0:8191];
    integer head=0,tail=0,count=0,tick=0,cseq=0,dseq=0;
    integer accepted=0,returned=0,cpu_returns=0,dma_returns=0;
    integer full_turnover=0,held_cycles=0,error_returns=0,reset_pending=0,max_count=0;
    reg c_taken=0,d_taken=0,grant_held=0,next_owner=0;
    reg [68:0] held_command;
    reg held_response=0;
    reg [34:0] held_response_payload;
    reg [31:0] rng=32'h80c32a91;
    reg got_owner;

    always @(posedge clk) begin
        if(!rst_n) begin
            if(count!=0)reset_pending=reset_pending+1;
            head=0;tail=0;count=0;tick=0;cseq=0;dseq=0;
            accepted=0;returned=0;cpu_returns=0;dma_returns=0;
            c_taken=0;d_taken=0;grant_held=0;held_response=0;next_owner=0;
        end else begin
            tick=tick+1;
            if(occupancy!==count)$fatal(1,"P80 arbiter queue occupancy differs");
            if(grant_held && (!v || {a,read_cmd,w,mask}!==held_command))
                $fatal(1,"P80 arbiter changed a held command");
            if(held_response && {crv,drv,rd,re}!==held_response_payload)
                $fatal(1,"P80 arbiter changed response owner/payload during backpressure");
            if(crv && drv)$fatal(1,"Response routed to two masters");
            if(rv) begin
                if(count==0 || crv!==!owners[head] || drv!==owners[head])
                    $fatal(1,"Wrong ordered response owner");
                if(rd!==values[head] || re!==errors[head] || crdata!==rd || drdata!==rd || cerr!==re || derr!==re)
                    $fatal(1,"Wrong response payload/error");
            end
            if(count==DEPTH && rv && rready && v && ready)full_turnover=full_turnover+1;
            if(rv && rready) begin
                if(owners[head])dma_returns=dma_returns+1;else cpu_returns=cpu_returns+1;
                if(errors[head])error_returns=error_returns+1;
                head=head+1;count=count-1;returned=returned+1;
            end
            c_taken=cv && cready;d_taken=dv && dready;
            if(c_taken && d_taken)$fatal(1,"Two upstream commands accepted in one cycle");
            if((c_taken || d_taken)!==(v && ready))$fatal(1,"Command handshake mismatch");
            if(v && ready) begin
                got_owner=d_taken;
                if(cv && dv && !grant_held && got_owner!==next_owner)$fatal(1,"Accepted-request fairness failed");
                if(got_owner) begin
                    if({a,read_cmd,w,mask}!=={da,dread,dw,dm})$fatal(1,"DMA request corrupted");
                end else if({a,read_cmd,w,mask}!=={ca,cread,cw,cm})$fatal(1,"CPU request corrupted");
                next_owner=!got_owner;
                if(tail>=8192)$fatal(1,"Test ledger overflow");
                owners[tail]=got_owner;values[tail]=a^w^32'h13579bdf;
                errors[tail]=(tail%29)==7;
                release_at[tail]=(tick<64) ? 64 : tick+2+(rng[5:3]);
                tail=tail+1;count=count+1;accepted=accepted+1;
            end
            if(c_taken)cseq=cseq+1;
            if(d_taken)dseq=dseq+1;
            if(count>DEPTH)$fatal(1,"Accepted beyond configured metadata capacity");
            if(count>max_count)max_count=count;
            grant_held=v && !ready;held_command={a,read_cmd,w,mask};
            if(grant_held)held_cycles=held_cycles+1;
            held_response=rv && !rready;held_response_payload={crv,drv,rd,re};
        end
    end

    // Update stimuli between rising edges. A stalled master's VALID and payload
    // remain unchanged even when the random generator wants to stop issuing.
    always @(negedge clk) begin
        if(!rst_n) begin
            cv=0;dv=0;rv=0;cr=0;dr=0;bus_ready=0;rd=0;re=0;
        end else begin
            rng={rng[30:0],rng[31]^rng[21]^rng[1]^rng[0]};
            if(!cv || c_taken) begin
                cv=send_enabled && (tick<64 || rng[0]);
                ca=32'h10000000+cseq*4;cw=32'hc0000000^cseq;cread=cseq%2;cm=cread ? 0 : 15;
            end
            if(!dv || d_taken) begin
                dv=send_enabled && (tick<64 || rng[1]);
                da=32'h20000000+dseq*4;dw=32'hd0000000^dseq;dread=dseq%2;dm=dread ? 0 : 15;
            end
            bus_ready=!send_enabled || tick<64 || rng[2] || rng[3];
            cr=!send_enabled || ((tick<150 || tick>210) && (rng[4] || rng[5]));
            dr=!send_enabled || ((tick<280 || tick>345) && (rng[6] || rng[7]));
            rv=count!=0 && tick>=release_at[head];
            if(count!=0) begin rd=values[head];re=errors[head];end
        end
    end

    initial begin
        repeat(4)@(negedge clk);#1;rst_n=1;
        repeat(1030)@(negedge clk);#1;rst_n=0;
        repeat(3)@(negedge clk);#1;rst_n=1;
        repeat(2500)@(negedge clk);#1;send_enabled=0;
        wait(count==0 && !cv && !dv);repeat(3)@(negedge clk);
        if(pending || accepted!=returned || accepted<300 || cpu_returns==0 || dma_returns==0 ||
            full_turnover==0 || held_cycles==0 || error_returns==0 || reset_pending==0 || max_count!=DEPTH)
            $fatal(1,"P80 arbiter coverage incomplete depth=%0d a=%0d r=%0d full=%0d held=%0d errors=%0d reset=%0d peak=%0d",DEPTH,accepted,returned,full_turnover,held_cycles,error_returns,reset_pending,max_count);
        $display("P80_ARBITER_PASS depth=%0d accepted=%0d returned=%0d cpu=%0d dma=%0d full_turnover=%0d held=%0d errors=%0d reset_pending=%0d",DEPTH,accepted,returned,cpu_returns,dma_returns,full_turnover,held_cycles,error_returns,reset_pending);
        $finish;
    end
    initial begin #200000;$fatal(1,"P80 arbiter timeout");end
endmodule
module tb_p80_arb2;tb_arch03_p80_arbiter #(.DEPTH(2)) test();endmodule
module tb_p80_arb4;tb_arch03_p80_arbiter #(.DEPTH(4)) test();endmodule
module tb_p80_arb8;tb_arch03_p80_arbiter #(.DEPTH(8)) test();endmodule
