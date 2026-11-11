// Actual E203 execution, public ICB loading source, response-based result audit.
// Expected answers are consumed only by this observer, never by the SoC.
`define A3MEM u_e203_soc_top.u_e203_subsys_top.u_e203_subsys_main.u_e203_subsys_mems
`define A3DMA `A3MEM.u_arch03_accel
wire a3_mon_clk=`A3MEM.clk;
wire a3_mon_rst_n=`A3MEM.rst_n;
wire a3_window_active,a3_window_finished,a3_window_failed;
wire [31:0] a3_window_failure;
wire [63:0] a3_window_start,a3_window_end,a3_window_cycles,a3_cmd_wait,a3_rsp_wait;
wire [31:0] a3_source_acks,a3_input_acks,a3_read_acks,a3_output_acks;
wire a3_task_arm=`A3MEM.expl_axi_icb_cmd_valid && `A3MEM.expl_axi_icb_cmd_ready &&
    !`A3MEM.expl_axi_icb_cmd_read && `A3MEM.expl_axi_icb_cmd_addr==32'h40000004 &&
    `A3MEM.expl_axi_icb_cmd_wmask==15 && `A3MEM.expl_axi_icb_cmd_wdata==1;
wire a3_task_cancel=(`A3MEM.expl_axi_icb_cmd_valid && `A3MEM.expl_axi_icb_cmd_ready &&
    !`A3MEM.expl_axi_icb_cmd_read && `A3MEM.expl_axi_icb_cmd_addr==32'h40000004 &&
    `A3MEM.expl_axi_icb_cmd_wdata==2) || `A3DMA.error_q!=0;
arch03_icb32_source a3_loading_source(
    .clk(a3_mon_clk),.rst_n(a3_mon_rst_n),
    .cmd_valid(a3_source_cmd_valid),.cmd_ready(a3_source_cmd_ready),
    .cmd_addr(a3_source_cmd_addr),.cmd_read(a3_source_cmd_read),
    .cmd_wdata(a3_source_cmd_wdata),.cmd_wmask(a3_source_cmd_wmask),
    .rsp_valid(a3_source_rsp_valid),.rsp_ready(a3_source_rsp_ready),
    .rsp_rdata(a3_source_rsp_rdata),.rsp_err(a3_source_rsp_err));
arch03_task_window_icb32 a3_dma_window(
    .clk(a3_mon_clk),.rst_n(a3_mon_rst_n),.encoded_bytes(`A3DMA.input_bytes_q),.task_arm(a3_task_arm),.task_cancel(a3_task_cancel),
    .cmd_valid(`A3MEM.a3_dma_cmd_valid),.cmd_ready(`A3MEM.a3_dma_cmd_ready),
    .cmd_addr(`A3MEM.a3_dma_cmd_addr),.cmd_read(`A3MEM.a3_dma_cmd_read),
    .cmd_wmask(`A3MEM.a3_dma_cmd_wmask),.rsp_valid(`A3MEM.a3_dma_rsp_valid),
    .rsp_ready(`A3MEM.a3_dma_rsp_ready),.rsp_err(`A3MEM.a3_dma_rsp_err),
    .global_pending(`A3MEM.a3_arb_pending || `A3MEM.a3_router_pending),
    .fifo_empty(`A3DMA.transport.empty && !`A3DMA.half_q),
    .core_done(`A3DMA.core_done_q),.active(a3_window_active),.finished(a3_window_finished),
    .failed(a3_window_failed),.failure_code(a3_window_failure),
    .start_cycle(a3_window_start),.end_cycle(a3_window_end),.window_cycles(a3_window_cycles),
    .source_read_acks(a3_source_acks),.input_write_acks(a3_input_acks),
    .input_read_acks(a3_read_acks),.output_write_acks(a3_output_acks),
    .command_wait_cycles(a3_cmd_wait),.response_wait_cycles(a3_rsp_wait));

reg [4095:0] a3_activity_path,a3_dir,a3_capture,a3_load_path;
reg a3_activity_enabled=0;
reg [15:0] a3_expected[0:25343];
reg a3_sat_expected[0:25343],a3_actual_sat[0:25343];
reg a3_seen[0:25343],a3_core_seen[0:25343];
reg [31:0] a3_expected_input[0:11751];
reg [31:0] a3_mail[0:33];
reg a3_mem_pending=0,a3_mem_read;
reg [31:0] a3_mem_addr,a3_mem_data;
reg [3:0] a3_mem_mask;
integer a3_outputs=0,a3_input_words=0,a3_core_outputs=0,a3_sats=0;
integer a3_file,a3_i,a3_index,a3_lane,a3_encoded_bytes=0,a3_encoded_words=0;
reg [15:0] a3_raw_stream[0:23487];
reg [15:0] a3_value;
initial begin
    if(!$value$plusargs("DATA_DIR=%s",a3_dir))$fatal(1,"Missing DATA_DIR");
    if(!$value$plusargs("CAPTURE=%s",a3_capture))$fatal(1,"Missing CAPTURE");
    if(!$value$plusargs("LOAD32=%s",a3_load_path))$fatal(1,"Missing LOAD32");
    $readmemh({a3_dir,"/result.hex"},a3_expected);
    $readmemh({a3_dir,"/saturated.hex"},a3_sat_expected);
    if(!$value$plusargs("CODEC_BYTES=%d",a3_encoded_bytes))$fatal(1,"Missing CODEC_BYTES");
    if(a3_encoded_bytes<32 || a3_encoded_bytes>47008 || a3_encoded_bytes%4)$fatal(1,"Invalid encoded length");
    a3_encoded_words=a3_encoded_bytes/4;
    $readmemh(a3_load_path,a3_expected_input,0,a3_encoded_words-1);
    $readmemh({a3_dir,"/load.hex"},a3_raw_stream);
    for(a3_i=0;a3_i<25344;a3_i=a3_i+1) begin
        if((^a3_expected[a3_i])===1'bx || a3_sat_expected[a3_i]===1'bx)
            $fatal(1,"Missing DMA verification reference %0d",a3_i);
        a3_seen[a3_i]=0;a3_core_seen[a3_i]=0;a3_actual_sat[a3_i]=1'bx;
    end
    for(a3_i=0;a3_i<a3_encoded_words;a3_i=a3_i+1)
        if((^a3_expected_input[a3_i])===1'bx)$fatal(1,"Missing DMA source reference");
    for(a3_i=0;a3_i<34;a3_i=a3_i+1)a3_mail[a3_i]=0;
    a3_file=$fopen(a3_capture,"w");if(a3_file==0)$fatal(1,"Capture open");
    if($value$plusargs("ACTIVITY=%s",a3_activity_path))begin
        a3_activity_enabled=1;$dumpfile(a3_activity_path);$dumpvars(0,u_e203_soc_top);$dumpoff;
    end
end
always @(posedge a3_window_active) if(a3_activity_enabled)$dumpon;
// Stop activity on the final successful output ACK, not the later drain-proof
// publication. The window/firmware checks still reject any subsequent traffic.

always @(posedge a3_mon_clk) begin
    if(a3_mon_rst_n) begin
        if(`A3DMA.committed_valid && `A3DMA.committed_ready) begin
            if(`A3DMA.decoded_words>=a3_input_words || `A3DMA.committed_data!==a3_expected_input[`A3DMA.decoded_words])
                $fatal(1,"Decoder consumed a word before successful SRAM ACK or with wrong data");
        end
        if(`A3DMA.load_fire) begin
            for(a3_lane=0;a3_lane<`A3DMA.core_load_count;a3_lane=a3_lane+1)
                if(`A3DMA.core_load_data[a3_lane*16+:16]!==a3_raw_stream[`A3DMA.load_count_q+a3_lane])
                    $fatal(1,"Decoder halfword differs from original layout");
        end
        if(`A3DMA.core_out_valid && `A3DMA.core_out_ready)begin
            if(`A3DMA.core_col[0])$fatal(1,"B core pair starts at odd column");
            for(a3_lane=0;a3_lane<2;a3_lane=a3_lane+1)begin
                a3_index=`A3DMA.core_row*256+`A3DMA.core_col+a3_lane;
                if(a3_index<0 || a3_index>=25344 || a3_core_seen[a3_index])
                    $fatal(1,"Invalid/duplicate B core coordinate");
                if(`A3DMA.core_result[a3_lane*16+:16]!==a3_expected[a3_index] || `A3DMA.core_sat[a3_lane]!==a3_sat_expected[a3_index])
                    $fatal(1,"B core value/saturation mismatch index=%0d",a3_index);
                a3_core_seen[a3_index]=1;a3_actual_sat[a3_index]=`A3DMA.core_sat[a3_lane];
                a3_core_outputs=a3_core_outputs+1;a3_sats=a3_sats+`A3DMA.core_sat[a3_lane];
            end
        end
        if(`A3MEM.a3_mem_rsp_valid && `A3MEM.a3_mem_rsp_ready) begin
            if(!a3_mem_pending)$fatal(1,"Unowned shared SRAM response");
            if(`A3MEM.a3_mem_rsp_err)$fatal(1,"Shared SRAM error in positive CPU test");
            a3_mem_pending=0;
            if(!a3_mem_read) begin
                if(a3_mem_addr>=32'ha0000000 && a3_mem_addr<32'ha0000000+a3_encoded_bytes) begin
                    a3_index=(a3_mem_addr-32'ha0000000)>>2;
                    if(a3_mem_mask!==15 || a3_mem_addr[1:0]!=0 || a3_index!=a3_input_words ||
                       a3_mem_data!==a3_expected_input[a3_index])$fatal(1,"DMA initial SRAM copy mismatch");
                    a3_input_words=a3_input_words+1;
                end
                if(a3_mem_addr>=32'ha000c000 && a3_mem_addr<32'ha0018600) begin
                    if(a3_mem_mask!==15 || a3_mem_addr[1:0]!=0)$fatal(1,"DMA output packing mask/alignment");
                    for(a3_lane=0;a3_lane<2;a3_lane=a3_lane+1) begin
                        a3_index=((a3_mem_addr-32'ha000c000)>>1)+a3_lane;
                        a3_value=a3_lane==0 ? a3_mem_data[15:0] : a3_mem_data[31:16];
                        if(a3_seen[a3_index] || !a3_core_seen[a3_index] || a3_value!==a3_expected[a3_index])
                            $fatal(1,"DMA actual writeback mismatch index=%0d",a3_index);
                        a3_seen[a3_index]=1;a3_outputs=a3_outputs+1;
                        $fdisplay(a3_file,"%0d,%0d,%0d,%0d",a3_index/256,a3_index%256,$signed(a3_value),a3_actual_sat[a3_index]);
                    end
                    if(a3_outputs==25344 && a3_activity_enabled)begin $dumpoff;$dumpflush;end
                end
                if(a3_mem_addr>=32'ha001f000 && a3_mem_addr<32'ha001f088) begin
                    if(a3_mem_mask!==15 || a3_mem_addr[1:0]!=0)$fatal(1,"CPU mailbox mask");
                    a3_index=(a3_mem_addr-32'ha001f000)>>2;a3_mail[a3_index]=a3_mem_data;
                    if(a3_index==0 && a3_mem_data!=0)begin
                        if(a3_mail[0]!==32'h4b575450 || a3_mail[1]!==0)
                            $fatal(1,"DMA firmware failed magic=%h rc/cause=%h epc/count=%h",a3_mail[0],a3_mail[1],a3_mail[2]);
                        if(a3_outputs!=25344 || a3_input_words!=a3_encoded_words || a3_core_outputs!=25344 ||
                           a3_mail[2]!=23488 || a3_mail[3]!=25344 || a3_mail[6]!=a3_sats)
                            $fatal(1,"DMA CPU counts/saturation incomplete");
                        if(!a3_window_finished || a3_window_failed || a3_window_active)
                            $fatal(1,"DMA timing window incomplete/failed code=%0d",a3_window_failure);
                        if(a3_source_acks!=a3_encoded_words || a3_input_acks!=a3_encoded_words || a3_read_acks!=0 || a3_output_acks!=12672)
                            $fatal(1,"ICB32 three-stage transaction counts incomplete");
                        if(a3_mail[32]!=a3_encoded_bytes || (a3_mail[33]!=5) ||
                           a3_mail[8]!=32'h00100002 || a3_mail[7]!=32'h4b575305)$fatal(1,"ICB32 firmware metadata/identity");
                        if(a3_mail[30]==1 && (a3_mail[22]==0 || a3_mail[23]==0 || a3_mail[24]==0 ||
                           a3_mail[25]!=0 || (a3_mail[21]&1)==0))
                            $fatal(1,"IRQ firmware did not prove real external/timer interrupts and WFI");
                        for(a3_i=0;a3_i<25344;a3_i=a3_i+1)if(!a3_seen[a3_i])$fatal(1,"Missing output");
                        $fclose(a3_file);
                        $display("ARCH03_ICB32_BATCH_RESULT {\"status\":\"passed\",\"outputs\":25344,\"cpu_executed\":true,\"first_request_cycle\":%0d,\"final_response_cycle\":%0d,\"cycles\":%0d,\"saturated\":%0d,\"pending_transactions\":0,\"all_writes_responded\":true}",a3_window_start,a3_window_end,a3_window_cycles,a3_sats);
                        $display("ARCH03_ICB32_CPU_CYCLES %0d",{a3_mail[5],a3_mail[4]});
                        $display("ARCH03_ICB32_IRQ_PROOF enabled=%0d external=%0d timer=%0d wfi=%0d events=%0d unhandled=%0d",a3_mail[30],a3_mail[22],a3_mail[23],a3_mail[24],a3_mail[21],a3_mail[25]);
                        $finish;
                    end
                end
            end
        end
        if(`A3MEM.a3_mem_cmd_valid && `A3MEM.a3_mem_cmd_ready)begin
            if(a3_mem_pending)$fatal(1,"Shared SRAM single-outstanding violated");
            a3_mem_pending=1;a3_mem_read=`A3MEM.a3_mem_cmd_read;
            a3_mem_addr=`A3MEM.a3_mem_cmd_addr;a3_mem_data=`A3MEM.a3_mem_cmd_wdata;
            a3_mem_mask=`A3MEM.a3_mem_cmd_wmask;
        end
    end
end
initial begin #1000000000;$fatal(1,"ICB32 SoC timeout outputs=%0d inputs=%0d",a3_outputs,a3_input_words);end
`undef A3DMA
`undef A3MEM
