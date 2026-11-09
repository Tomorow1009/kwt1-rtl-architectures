`timescale 1ns/1fs
// Passive task metrics, for simulation only. No output drives a DUT signal.
// Counts are event observations, not a latency model or power estimate.
module arch03_dma16_bus_metrics #(
    parameter [31:0] SOURCE_BASE=32'hb0000000,
    parameter [31:0] INPUT_BASE=32'ha0000000,
    parameter [31:0] OUTPUT_BASE=32'ha000c000,
    parameter integer INPUT_WORDS=11744, OUTPUT_WORDS=12672
)(
    input wire clk,rst_n,task_arm,task_cancel,task_end,
    input wire dma_cmd_valid,dma_cmd_ready,
    input wire [31:0] dma_cmd_addr,dma_cmd_wdata,
    input wire dma_cmd_read,
    input wire [3:0] dma_cmd_wmask,
    input wire dma_rsp_valid,dma_rsp_ready,dma_rsp_err,
    input wire cpu_cmd_valid,cpu_cmd_ready,
    input wire arb_cmd_valid,arb_cmd_ready,arb_rsp_valid,arb_rsp_ready
);
    localparam PH_SOURCE=0,PH_STAGE=1,PH_LOAD=2,PH_OUTPUT=3;
    localparam ST_WAIT=0,ST_GAP=1,ST_RESPONSE=2;
    reg armed=0,started=0,reported=0,counting=0,cancelled=0,had_error=0;
    reg offer_live=0,pending=0,global_pending=0,global_cpu=0;
    reg [31:0] offered_addr,offered_data;
    reg offered_read,previous_read;
    reg [3:0] offered_mask;
    integer offered_phase,pending_phase,previous_transition;
    longint unsigned cycle_index=0,offer_cycle=0,accept_cycle=0,first_cycle=0,last_ack_cycle=0,previous_accept=0;
    reg have_previous_accept=0;
    longint unsigned issued[0:3],accepted[0:3],successes[0:3],errors[0:3],cancel_acks[0:3],phase_previous[0:3];
    longint unsigned stat_count[0:3][0:2],stat_sum[0:3][0:2],stat_min[0:3][0:2],stat_max[0:3][0:2];
    longint unsigned hist[0:3][0:2][0:8];
    longint unsigned switch_count[0:3],switch_sum[0:3],switch_min[0:3],switch_max[0:3],switch_hist[0:3][0:8];
    longint unsigned contention_cycles,cpu_grants,dma_grants,contention_cpu_grants,contention_dma_grants,contention_blocked;
    longint unsigned arb_grants,arb_acks,ready_wait_cycles,response_backpressure_cycles,cpu_owned_wait_cycles;
    reg initial_global_pending,initial_global_cpu;
    integer i,j,k,phase_now,switch_now,ack_phase;
    reg cmd_fire,rsp_fire,cpu_fire,bus_fire,bus_ack,old_pending,old_global_pending;
    longint unsigned old_accept,elapsed,total_issued,total_accepted,total_success,total_error,total_cancel;

    function integer phase_of(input [31:0] addr,input read_command);
        begin
            phase_of=-1;
            if(addr[1:0]==0)begin
                if(read_command && {1'b0,addr}>={1'b0,SOURCE_BASE} &&
                   {1'b0,addr}<{1'b0,SOURCE_BASE}+INPUT_WORDS*4)phase_of=PH_SOURCE;
                else if({1'b0,addr}>={1'b0,INPUT_BASE} &&
                        {1'b0,addr}<{1'b0,INPUT_BASE}+INPUT_WORDS*4)phase_of=read_command?PH_LOAD:PH_STAGE;
                else if(!read_command && {1'b0,addr}>={1'b0,OUTPUT_BASE} &&
                        {1'b0,addr}<{1'b0,OUTPUT_BASE}+OUTPUT_WORDS*4)phase_of=PH_OUTPUT;
            end
        end
    endfunction
    function integer bucket(input longint unsigned value);
        begin
            if(value<4)bucket=value;
            else if(value<8)bucket=4;
            else if(value<16)bucket=5;
            else if(value<32)bucket=6;
            else if(value<64)bucket=7;
            else bucket=8;
        end
    endfunction
    function automatic string phase_name(input integer p);
        case(p) 0:phase_name="source_read";1:phase_name="stage_write";2:phase_name="shared_read";3:phase_name="output_write";endcase
    endfunction
    function automatic string stat_name(input integer s);
        case(s) 0:stat_name="offer_wait";1:stat_name="accept_gap";2:stat_name="response_latency";endcase
    endfunction
    function automatic string switch_name(input integer s);
        case(s) 0:switch_name="RR";1:switch_name="RW";2:switch_name="WR";3:switch_name="WW";endcase
    endfunction
    task fail(input integer code);
        $fatal(1,"DMA16_BUS_METRICS_PROTOCOL_ERROR code=%0d cycle=%0d",code,cycle_index);
    endtask
    task add_stat(input integer p,input integer s,input longint unsigned value);
        begin
            if(stat_count[p][s]==0 || value<stat_min[p][s])stat_min[p][s]=value;
            if(value>stat_max[p][s])stat_max[p][s]=value;
            stat_count[p][s]=stat_count[p][s]+1;stat_sum[p][s]=stat_sum[p][s]+value;
            hist[p][s][bucket(value)]=hist[p][s][bucket(value)]+1;
        end
    endtask
    task add_switch(input integer s,input longint unsigned value);
        begin
            if(switch_count[s]==0 || value<switch_min[s])switch_min[s]=value;
            if(value>switch_max[s])switch_max[s]=value;
            switch_count[s]=switch_count[s]+1;switch_sum[s]=switch_sum[s]+value;
            switch_hist[s][bucket(value)]=switch_hist[s][bucket(value)]+1;
        end
    endtask
    task clear_task;
        begin
            started=0;reported=0;counting=0;cancelled=0;had_error=0;offer_live=0;pending=0;
            first_cycle=0;last_ack_cycle=0;have_previous_accept=0;
            contention_cycles=0;cpu_grants=0;dma_grants=0;contention_cpu_grants=0;contention_dma_grants=0;contention_blocked=0;
            arb_grants=0;arb_acks=0;ready_wait_cycles=0;response_backpressure_cycles=0;cpu_owned_wait_cycles=0;
            initial_global_pending=0;initial_global_cpu=0;
            for(i=0;i<4;i=i+1)begin
                issued[i]=0;accepted[i]=0;successes[i]=0;errors[i]=0;cancel_acks[i]=0;phase_previous[i]=0;
                switch_count[i]=0;switch_sum[i]=0;switch_min[i]=0;switch_max[i]=0;
                for(k=0;k<9;k=k+1)switch_hist[i][k]=0;
                for(j=0;j<3;j=j+1)begin
                    stat_count[i][j]=0;stat_sum[i][j]=0;stat_min[i][j]=0;stat_max[i][j]=0;
                    for(k=0;k<9;k=k+1)hist[i][j][k]=0;
                end
            end
        end
    endtask
    task capture_offer;
        integer p;
        begin
            if(cancelled || had_error || reported)fail(10);
            if($isunknown({dma_cmd_addr,dma_cmd_read,dma_cmd_wdata,dma_cmd_wmask}))fail(11);
            p=phase_of(dma_cmd_addr,dma_cmd_read);
            if(p<0 || (!dma_cmd_read && dma_cmd_wmask!=15))fail(12);
            if(!started)begin
                if(p!=PH_SOURCE)fail(13);
                started=1;counting=1;first_cycle=cycle_index;
                initial_global_pending=global_pending;initial_global_cpu=global_pending && global_cpu;
            end else if(!counting)fail(14);
            offer_live=1;offer_cycle=cycle_index;offered_phase=p;
            offered_addr=dma_cmd_addr;offered_read=dma_cmd_read;offered_data=dma_cmd_wdata;offered_mask=dma_cmd_wmask;
            issued[p]=issued[p]+1;
        end
    endtask

    // Capture the actual sending-edge event, matching the full-task observer.
    // Payload changes also expose a next request if VALID remains asserted.
    always @(dma_cmd_valid or dma_cmd_addr or dma_cmd_read or dma_cmd_wdata or dma_cmd_wmask)begin
        if(rst_n && armed && !reported && dma_cmd_valid)begin
            if(!offer_live)capture_offer();
            else if({dma_cmd_addr,dma_cmd_read,dma_cmd_wdata,dma_cmd_wmask} !==
                    {offered_addr,offered_read,offered_data,offered_mask})fail(15);
        end
    end
    // Identical consecutive payloads with continuous VALID have no value event.
    // A half-cycle check records their offer in the preceding sending cycle.
    always @(negedge clk)if(rst_n && armed && !reported && dma_cmd_valid && !offer_live)capture_offer();

    task publish;
        string outcome;
        begin
            if(offer_live || pending)fail(16);
            total_issued=0;total_accepted=0;total_success=0;total_error=0;total_cancel=0;
            for(i=0;i<4;i=i+1)begin
                total_issued=total_issued+issued[i];total_accepted=total_accepted+accepted[i];
                total_success=total_success+successes[i];total_error=total_error+errors[i];total_cancel=total_cancel+cancel_acks[i];
            end
            outcome=had_error ? "error" : cancelled ? "cancelled" : "complete";
            if(outcome=="complete" && (successes[0]!=INPUT_WORDS || successes[1]!=INPUT_WORDS ||
                successes[2]!=INPUT_WORDS || successes[3]!=OUTPUT_WORDS || total_error!=0))fail(17);
            elapsed=started ? last_ack_cycle-first_cycle : 0;
            $display("DMA16_BUS_HEADER schema=dma16_bus_metrics_v1 outcome=%s started=%0d cancelled=%0d first_offer_cycle=%0d last_ack_cycle=%0d published_cycle=%0d total_cycles=%0d issued=%0d accepted=%0d successes=%0d errors=%0d cancelled_acks=%0d committed_bytes=%0d input_words=%0d output_words=%0d",outcome,started,cancelled,first_cycle,last_ack_cycle,cycle_index,elapsed,total_issued,total_accepted,total_success,total_error,total_cancel,total_success*4,INPUT_WORDS,OUTPUT_WORDS);
            for(i=0;i<4;i=i+1)begin
                $display("DMA16_BUS_PHASE phase=%s issued=%0d accepted=%0d successes=%0d errors=%0d cancelled_acks=%0d committed_bytes=%0d",phase_name(i),issued[i],accepted[i],successes[i],errors[i],cancel_acks[i],successes[i]*4);
                for(j=0;j<3;j=j+1)
                    $display("DMA16_BUS_STAT phase=%s metric=%s count=%0d min=%0d max=%0d sum=%0d hist=%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d",phase_name(i),stat_name(j),stat_count[i][j],stat_min[i][j],stat_max[i][j],stat_sum[i][j],hist[i][j][0],hist[i][j][1],hist[i][j][2],hist[i][j][3],hist[i][j][4],hist[i][j][5],hist[i][j][6],hist[i][j][7],hist[i][j][8]);
                $display("DMA16_BUS_SWITCH transition=%s count=%0d min=%0d max=%0d sum=%0d hist=%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d",switch_name(i),switch_count[i],switch_min[i],switch_max[i],switch_sum[i],switch_hist[i][0],switch_hist[i][1],switch_hist[i][2],switch_hist[i][3],switch_hist[i][4],switch_hist[i][5],switch_hist[i][6],switch_hist[i][7],switch_hist[i][8]);
            end
            $display("DMA16_BUS_CONTENTION competing_cycles=%0d cpu_grants=%0d dma_grants=%0d competing_cpu_grants=%0d competing_dma_grants=%0d competing_blocked=%0d arb_grants=%0d arb_acks=%0d ready_wait_cycles=%0d response_backpressure_cycles=%0d cpu_owned_wait_cycles=%0d initial_global_pending=%0d initial_global_cpu=%0d",contention_cycles,cpu_grants,dma_grants,contention_cpu_grants,contention_dma_grants,contention_blocked,arb_grants,arb_acks,ready_wait_cycles,response_backpressure_cycles,cpu_owned_wait_cycles,initial_global_pending,initial_global_cpu);
            $display("DMA16_BUS_END schema=dma16_bus_metrics_v1");
            reported=1;counting=0;armed=0;
        end
    endtask

    always @(posedge clk or negedge rst_n)begin
        if(!rst_n)begin
            armed=0;cycle_index=0;global_pending=0;global_cpu=0;clear_task();
        end else begin
            cycle_index=cycle_index+1;
            old_global_pending=global_pending;
            cmd_fire=dma_cmd_valid && dma_cmd_ready;rsp_fire=dma_rsp_valid && dma_rsp_ready;
            cpu_fire=cpu_cmd_valid && cpu_cmd_ready;bus_fire=arb_cmd_valid && arb_cmd_ready;bus_ack=arb_rsp_valid && arb_rsp_ready;
            if(cpu_fire && cmd_fire)fail(1);
            if(bus_fire !== (cpu_fire || cmd_fire))fail(2);
            if(bus_fire && global_pending && !bus_ack)fail(3);
            if(bus_ack && !global_pending && !bus_fire)fail(4);
            if(task_arm)begin
                if(armed || offer_live || pending || dma_cmd_valid)fail(5);
                clear_task();armed=1;
            end
            if(armed && !reported)begin
                if(task_cancel)cancelled=1;
                if($isunknown({dma_cmd_valid,dma_rsp_valid}) ||
                   (dma_cmd_valid && $isunknown(dma_cmd_ready)) ||
                   (dma_rsp_valid && $isunknown({dma_rsp_ready,dma_rsp_err})))fail(6);
                if(offer_live && !dma_cmd_valid)fail(7);
                if(counting)begin
                    if(cpu_fire)cpu_grants=cpu_grants+1;
                    if(cmd_fire)dma_grants=dma_grants+1;
                    if(bus_fire)arb_grants=arb_grants+1;
                    if(bus_ack)arb_acks=arb_acks+1;
                    if(dma_cmd_valid && !dma_cmd_ready)ready_wait_cycles=ready_wait_cycles+1;
                    if(dma_cmd_valid && !dma_cmd_ready && global_pending && global_cpu)cpu_owned_wait_cycles=cpu_owned_wait_cycles+1;
                    if(dma_rsp_valid && !dma_rsp_ready)response_backpressure_cycles=response_backpressure_cycles+1;
                    if(cpu_cmd_valid && dma_cmd_valid)begin
                        contention_cycles=contention_cycles+1;
                        if(cpu_fire)contention_cpu_grants=contention_cpu_grants+1;
                        else if(cmd_fire)contention_dma_grants=contention_dma_grants+1;
                        else contention_blocked=contention_blocked+1;
                    end
                end
                old_pending=pending;old_accept=accept_cycle;ack_phase=pending_phase;
                if(cmd_fire)begin
                    if(!offer_live)fail(8);
                    if(pending && !rsp_fire)fail(9);
                    phase_now=offered_phase;
                    add_stat(phase_now,ST_WAIT,cycle_index-offer_cycle);
                    if(accepted[phase_now]!=0)add_stat(phase_now,ST_GAP,cycle_index-phase_previous[phase_now]);
                    if(have_previous_accept)begin
                        switch_now=previous_read ? (offered_read ? 0 : 1) : (offered_read ? 2 : 3);
                        add_switch(switch_now,cycle_index-previous_accept);
                    end
                    have_previous_accept=1;previous_accept=cycle_index;previous_read=offered_read;
                    accepted[phase_now]=accepted[phase_now]+1;phase_previous[phase_now]=cycle_index;
                    pending=1;pending_phase=phase_now;accept_cycle=cycle_index;offer_live=0;
                end
                if(rsp_fire)begin
                    if(!old_pending && !cmd_fire)fail(18);
                    if(!old_pending)begin ack_phase=phase_now;old_accept=cycle_index;end
                    add_stat(ack_phase,ST_RESPONSE,cycle_index-old_accept);
                    if(dma_rsp_err)begin errors[ack_phase]=errors[ack_phase]+1;had_error=1;end
                    else successes[ack_phase]=successes[ack_phase]+1;
                    if(cancelled)cancel_acks[ack_phase]=cancel_acks[ack_phase]+1;
                    last_ack_cycle=cycle_index;
                    pending=old_pending && cmd_fire;
                    if(!dma_rsp_err && ack_phase==PH_OUTPUT && successes[PH_OUTPUT]==OUTPUT_WORDS)counting=0;
                end
                if((cancelled || had_error) && !pending && !offer_live)counting=0;
                // The prior window's finished level may still be high at the
                // new ARM sampling edge; its observer clears it that edge.
                if(task_end && !task_arm)publish();
            end
            if(bus_ack)global_pending=0;
            if(bus_fire && (old_global_pending || !bus_ack))begin global_pending=1;global_cpu=cpu_fire;end
        end
    end
endmodule
