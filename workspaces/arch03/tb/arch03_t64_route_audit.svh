// Passive proof of the four DMA paths through the original mem_fab pins.
// a3_bus_* connects only to the original i_icb_*; a3_cpu_* is original O4.
reg t64_route_pending=0,t64_route_forwarded=0,t64_route_served=0;
reg [68:0] t64_route_payload;
integer t64_route_kind=0,t64_route_counts[0:3],t64_route_i;
wire t64_dma_fire=`A3MEM.a3_dma_cmd_valid && `A3MEM.a3_dma_cmd_ready;
always @(posedge a3_mon_clk or negedge a3_mon_rst_n) begin
    if(!a3_mon_rst_n || a3_task_arm) begin
        t64_route_pending=0;t64_route_forwarded=0;t64_route_served=0;
        for(t64_route_i=0;t64_route_i<4;t64_route_i=t64_route_i+1)t64_route_counts[t64_route_i]=0;
    end else begin
        if(`A3MEM.a3_dma_rsp_valid && `A3MEM.a3_dma_rsp_ready)begin
            if(!t64_route_pending || !t64_route_forwarded || !t64_route_served)
                $fatal(1,"T64 response without original System Bus and slave acceptance");
            t64_route_counts[t64_route_kind]=t64_route_counts[t64_route_kind]+1;
            t64_route_pending=0;
        end
        if(t64_dma_fire)begin
            if(t64_route_pending)$fatal(1,"T64 multiple DMA owners");
            t64_route_payload={`A3MEM.a3_dma_cmd_addr,`A3MEM.a3_dma_cmd_read,
                `A3MEM.a3_dma_cmd_wdata,`A3MEM.a3_dma_cmd_wmask};
            if(!(`A3MEM.a3_bus_cmd_valid && `A3MEM.a3_bus_cmd_ready) ||
                {`A3MEM.a3_bus_cmd_addr,`A3MEM.a3_bus_cmd_read,`A3MEM.a3_bus_cmd_wdata,
                    `A3MEM.a3_bus_cmd_wmask}!==t64_route_payload)
                $fatal(1,"T64 DMA bypassed original mem_fab input");
            t64_route_kind=`A3MEM.a3_dma_cmd_read ?
                (`A3MEM.a3_dma_cmd_addr>=32'hb0000000 ? 0 : 2) :
                (`A3MEM.a3_dma_cmd_addr<32'ha000c000 ? 1 : 3);
            t64_route_pending=1;t64_route_forwarded=0;t64_route_served=0;
        end
        if(t64_route_pending && `A3MEM.a3_cpu_cmd_valid && `A3MEM.a3_cpu_cmd_ready)begin
            if(t64_route_forwarded || {`A3MEM.a3_cpu_cmd_addr,`A3MEM.a3_cpu_cmd_read,
                `A3MEM.a3_cpu_cmd_wdata,`A3MEM.a3_cpu_cmd_wmask}!==t64_route_payload)
                $fatal(1,"T64 original mem_fab O4 payload/duplicate");
            t64_route_forwarded=1;
        end
        if(t64_route_pending && ((`A3MEM.a3_mem_cmd_valid && `A3MEM.a3_mem_cmd_ready) ||
            (a3_source_cmd_valid && a3_source_cmd_ready)))begin
            if(!t64_route_forwarded || t64_route_served)
                $fatal(1,"T64 slave bypass/duplicate");
            t64_route_served=1;
        end
    end
end
task t64_report_route;
    begin
        if(t64_route_pending || t64_route_counts[0]!=a3_encoded_words ||
            t64_route_counts[1]!=a3_encoded_words || t64_route_counts[2]!=a3_encoded_words ||
            t64_route_counts[3]!=12672)$fatal(1,"T64 original bus path coverage incomplete");
        $display("T64_BUS_ROUTE_PASS source=%0d input_write=%0d input_read=%0d output_write=%0d original_mem_fab=true",t64_route_counts[0],t64_route_counts[1],t64_route_counts[2],t64_route_counts[3]);
    end
endtask
