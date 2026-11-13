// Simulation-only counters. No assignment/force to the DUT, no dumped scope.
// Arm before the first source request and report at the CPU completion mailbox.
// DMA and cache accesses are absent outside the task; CPU traffic is not counted.
localparam integer A3_METRIC_ROWS=@ROWS@;
reg a3_metrics_armed=0;
reg [63:0] a3_metric_tick=0,a3_accept_tick=0;
integer a3_metric_owner=0,a3_metric_kind=0,a3_metric_i;
reg a3_metric_pending=0;
reg [63:0] a3_phase_acks[0:3],a3_phase_latency_sum[0:3],a3_phase_latency_max[0:3];
reg [63:0] a3_x_reads[0:59],a3_x_writes[0:59];
reg [63:0] a3_w_reads[0:31],a3_w_writes[0:31];
reg [63:0] a3_mac_updates[0:A3_METRIC_ROWS*16-1];
reg [63:0] a3_result_stalls=0,a3_delta;
// Scheduler diagnostics only. Overlapping wait reasons are not additive.
reg [63:0] a3_schedule_blocks=0,a3_schedule_feeds=0,a3_schedule_results=0;
reg [63:0] a3_schedule_empty=0,a3_schedule_xwait=0,a3_schedule_wwait=0;
reg [63:0] a3_schedule_slotwait=0,a3_schedule_creditwait=0;
reg [63:0] a3_schedule_previous_start=0,a3_schedule_gap;
reg [63:0] a3_schedule_intervals=0,a3_schedule_sum=0,a3_schedule_min=0,a3_schedule_max=0;
reg [63:0] a3_schedule_tile_intervals=0,a3_schedule_tile_sum=0;
realtime a3_schedule_first_feed=0,a3_schedule_last_feed=0;
realtime a3_schedule_first_result=0,a3_schedule_last_result=0;
realtime a3_schedule_first_output=0,a3_schedule_last_output=0;
genvar a3_mg,a3_mr,a3_mc;
generate
    for(a3_mg=0;a3_mg<60;a3_mg=a3_mg+1) begin:a3_metrics_x
        always @(posedge a3_mon_clk or negedge a3_mon_rst_n) begin
            if(!a3_mon_rst_n || a3_task_arm) begin a3_x_reads[a3_mg]<=0;a3_x_writes[a3_mg]<=0;end
            else if(a3_metrics_armed && `A3DMA.core.x_banks[a3_mg].ram.cs) begin
                if(`A3DMA.core.x_banks[a3_mg].ram.we) a3_x_writes[a3_mg]<=a3_x_writes[a3_mg]+1;
                else a3_x_reads[a3_mg]<=a3_x_reads[a3_mg]+1;
            end
        end
    end
    for(a3_mg=0;a3_mg<32;a3_mg=a3_mg+1) begin:a3_metrics_w
        always @(posedge a3_mon_clk or negedge a3_mon_rst_n) begin
            if(!a3_mon_rst_n || a3_task_arm) begin a3_w_reads[a3_mg]<=0;a3_w_writes[a3_mg]<=0;end
            else if(a3_metrics_armed && `A3DMA.core.weight_banks[a3_mg].ram.cs) begin
                if(`A3DMA.core.weight_banks[a3_mg].ram.we) a3_w_writes[a3_mg]<=a3_w_writes[a3_mg]+1;
                else a3_w_reads[a3_mg]<=a3_w_reads[a3_mg]+1;
            end
        end
    end
    for(a3_mr=0;a3_mr<A3_METRIC_ROWS;a3_mr=a3_mr+1) begin:a3_metrics_rows
        for(a3_mc=0;a3_mc<16;a3_mc=a3_mc+1) begin:a3_metrics_lanes
            always @(posedge a3_mon_clk or negedge a3_mon_rst_n) begin
                if(!a3_mon_rst_n || a3_task_arm) a3_mac_updates[a3_mr*16+a3_mc]<=0;
                else if(a3_metrics_armed && `A3DMA.core.array.rows[a3_mr].columns[a3_mc].pe.advance &&
                        `A3DMA.core.array.rows[a3_mr].columns[a3_mc].pe.x_in[25] &&
                        `A3DMA.core.array.rows[a3_mr].columns[a3_mc].pe.w_in[23])
                    a3_mac_updates[a3_mr*16+a3_mc]<=a3_mac_updates[a3_mr*16+a3_mc]+1;
            end
        end
    end
endgenerate
always @(posedge a3_mon_clk or negedge a3_mon_rst_n) begin
    if(!a3_mon_rst_n || a3_task_arm) begin
        a3_metrics_armed<=a3_mon_rst_n;a3_metric_tick=0;a3_accept_tick=0;
        a3_metric_pending=0;a3_metric_owner=0;a3_result_stalls=0;
        a3_schedule_blocks=0;a3_schedule_feeds=0;a3_schedule_results=0;
        a3_schedule_empty=0;a3_schedule_xwait=0;a3_schedule_wwait=0;
        a3_schedule_slotwait=0;a3_schedule_creditwait=0;
        a3_schedule_previous_start=0;a3_schedule_intervals=0;a3_schedule_sum=0;
        a3_schedule_min=0;a3_schedule_max=0;a3_schedule_tile_intervals=0;a3_schedule_tile_sum=0;
        a3_schedule_first_feed=0;a3_schedule_last_feed=0;
        a3_schedule_first_result=0;a3_schedule_last_result=0;
        a3_schedule_first_output=0;a3_schedule_last_output=0;
        for(a3_metric_i=0;a3_metric_i<4;a3_metric_i=a3_metric_i+1) begin
            a3_phase_acks[a3_metric_i]=0;a3_phase_latency_sum[a3_metric_i]=0;a3_phase_latency_max[a3_metric_i]=0;
        end
    end else if(a3_metrics_armed) begin
        a3_metric_tick=a3_metric_tick+1;
        if(`A3DMA.core.enabled && !`A3DMA.core.compute_finished) begin
            if(!(`A3DMA.core.v3_q ? `A3DMA.core.x_window_valid : `A3DMA.core.x_valid))
                a3_schedule_xwait=a3_schedule_xwait+1;
            if(!`A3DMA.core.bank_valid[`A3DMA.core.compute_bank] ||
                `A3DMA.core.bank_tile[`A3DMA.core.compute_bank]!=`A3DMA.core.compute_tile)
                a3_schedule_wwait=a3_schedule_wwait+1;
            if(`A3DMA.core.issue_k==0 && `A3DMA.core.occupied[`A3DMA.core.issue_block[0]])
                a3_schedule_slotwait=a3_schedule_slotwait+1;
            if(`A3DMA.core.response_credit>=`A3DMA.core.RESPONSE_DEPTH)
                a3_schedule_creditwait=a3_schedule_creditwait+1;
        end
        if(`A3DMA.core.array_feed) begin
            if(a3_schedule_feeds==0) a3_schedule_first_feed=$realtime;
            a3_schedule_last_feed=$realtime;a3_schedule_feeds=a3_schedule_feeds+1;
            if(`A3DMA.core.read_k==0) begin
                if(`A3DMA.core.read_block!=a3_schedule_blocks) $fatal(1,"B schedule block sequence");
                if(a3_schedule_blocks!=0) begin
                    a3_schedule_gap=a3_metric_tick-a3_schedule_previous_start;
                    if(a3_schedule_blocks%25==0) begin
                        a3_schedule_tile_intervals=a3_schedule_tile_intervals+1;
                        a3_schedule_tile_sum=a3_schedule_tile_sum+a3_schedule_gap;
                    end else begin
                        if(a3_schedule_intervals==0 || a3_schedule_gap<a3_schedule_min) a3_schedule_min=a3_schedule_gap;
                        if(a3_schedule_gap>a3_schedule_max) a3_schedule_max=a3_schedule_gap;
                        a3_schedule_intervals=a3_schedule_intervals+1;a3_schedule_sum=a3_schedule_sum+a3_schedule_gap;
                    end
                end
                a3_schedule_previous_start=a3_metric_tick;a3_schedule_blocks=a3_schedule_blocks+1;
            end
        end else if(`A3DMA.core.enabled && a3_schedule_feeds!=0 && a3_schedule_feeds<25600)
            a3_schedule_empty=a3_schedule_empty+1;
        if(`A3DMA.core.enabled) begin
            for(a3_metric_i=0;a3_metric_i<64;a3_metric_i=a3_metric_i+1) begin
                if(`A3DMA.core.pe_valid[a3_metric_i]) begin
                    if(a3_schedule_results==0) a3_schedule_first_result=$realtime;
                    a3_schedule_last_result=$realtime;a3_schedule_results=a3_schedule_results+1;
                end
            end
        end
        if(`A3DMA.core_out_valid && `A3DMA.core_out_ready) begin
            if(a3_schedule_first_output==0) a3_schedule_first_output=$realtime;
            a3_schedule_last_output=$realtime;
        end
        if(`A3DMA.core_out_valid && !`A3DMA.core_out_ready) a3_result_stalls=a3_result_stalls+1;
        // Retire the OLD owner before accepting a same-edge new request.
        if(`A3MEM.a3_dma_rsp_valid && `A3MEM.a3_dma_rsp_ready) begin
            if(!a3_metric_pending || `A3MEM.a3_dma_rsp_err) $fatal(1,"ICB32 metrics unexpected response");
            a3_delta=a3_metric_tick-a3_accept_tick;
            a3_phase_acks[a3_metric_owner]=a3_phase_acks[a3_metric_owner]+1;
            a3_phase_latency_sum[a3_metric_owner]=a3_phase_latency_sum[a3_metric_owner]+a3_delta;
            if(a3_delta>a3_phase_latency_max[a3_metric_owner]) a3_phase_latency_max[a3_metric_owner]=a3_delta;
            a3_metric_pending=0;
        end
        if(`A3MEM.a3_dma_cmd_valid && `A3MEM.a3_dma_cmd_ready) begin
            if(a3_metric_pending) $fatal(1,"ICB32 metrics multiple outstanding");
            a3_metric_kind=`A3MEM.a3_dma_cmd_read ? (`A3MEM.a3_dma_cmd_addr>=32'hb0000000 ? 0 : 2) : (`A3MEM.a3_dma_cmd_addr<32'ha000c000 ? 1 : 3);
            a3_metric_owner=a3_metric_kind;a3_accept_tick=a3_metric_tick;a3_metric_pending=1;
        end
    end
end
task a3_report_metrics;
    reg [63:0] xr,xw,wr,ww,macs;
    integer k;
    begin
        xr=0;xw=0;wr=0;ww=0;macs=0;
        for(k=0;k<60;k=k+1) begin xr=xr+a3_x_reads[k];xw=xw+a3_x_writes[k];end
        for(k=0;k<32;k=k+1) begin wr=wr+a3_w_reads[k];ww=ww+a3_w_writes[k];end
        for(k=0;k<A3_METRIC_ROWS*16;k=k+1) macs=macs+a3_mac_updates[k];
        if(a3_metric_pending) $fatal(1,"ICB32 metrics unfinished transaction");
        $display("ICB32_METRICS schema=t64_passive_v1 rows=%0d cycles=%0d encoded_bytes=%0d x_reads=%0d x_writes=%0d w_reads=%0d w_writes=%0d mac_updates=%0d command_ready_wait=%0d response_backpressure=%0d pending_response_wait=%0d turnovers=%0d result_stalls=%0d",A3_METRIC_ROWS,a3_window_cycles,a3_encoded_bytes,xr,xw,wr,ww,macs,a3_cmd_wait,a3_rsp_wait,`A3DMA.response_wait_cycles,`A3DMA.turnovers,a3_result_stalls);
        for(k=0;k<4;k=k+1) $display("ICB32_METRIC_PHASE phase=%0d acks=%0d latency_sum=%0d latency_max=%0d",k,a3_phase_acks[k],a3_phase_latency_sum[k],a3_phase_latency_max[k]);
        $display("N1_SCHEDULE schema=n1_schedule_v1 blocks=%0d feeds=%0d results=%0d supply_empty=%0d x_wait=%0d w_wait=%0d slot_wait=%0d credit_wait=%0d intervals=%0d interval_sum=%0d interval_min=%0d interval_max=%0d tile_intervals=%0d tile_interval_sum=%0d first_feed_ns=%.6f last_feed_ns=%.6f first_result_ns=%.6f last_result_ns=%.6f first_output_ns=%.6f last_output_ns=%.6f",a3_schedule_blocks,a3_schedule_feeds,a3_schedule_results,a3_schedule_empty,a3_schedule_xwait,a3_schedule_wwait,a3_schedule_slotwait,a3_schedule_creditwait,a3_schedule_intervals,a3_schedule_sum,a3_schedule_min,a3_schedule_max,a3_schedule_tile_intervals,a3_schedule_tile_sum,a3_schedule_first_feed,a3_schedule_last_feed,a3_schedule_first_result,a3_schedule_last_result,a3_schedule_first_output,a3_schedule_last_output);
    end
endtask
