// Independent ten-phase DMA16 sequence observer. Only final sequence mailbox
// ends the run. PC input banks feed real source requests, never DUT memories.
`define S16M u_e203_soc_top.u_e203_subsys_top.u_e203_subsys_main.u_e203_subsys_mems
`define S16A `S16M.u_arch03_accel
wire s16_clk=`S16A.clk,s16_rst_n=`S16A.rst_n;
wire s16_start=`S16A.cmd_valid && `S16A.cmd_ready && !`S16A.cmd_read &&
 `S16A.cmd_addr==32'h40000004 && `S16A.cmd_wmask==15 && `S16A.cmd_wdata==1;
wire s16_cancel=`S16A.cmd_valid && `S16A.cmd_ready && !`S16A.cmd_read &&
 `S16A.cmd_addr==32'h40000004 && `S16A.cmd_wmask==15 && `S16A.cmd_wdata==2;
reg s16_select=0;
reg [31:0] s16_descriptor=0,s16_first_descriptor,s16_second_descriptor,s16_fault_epc;
reg [31:0] s16_timeout=8192;
wire s16_source_selected,s16_source_bank;
arch03_icb32_sequence_source s16_source(
 .clk(s16_clk),.rst_n(s16_rst_n),.select_valid(s16_select),.select_descriptor(s16_descriptor),
 .cmd_valid(a3_source_cmd_valid),.cmd_ready(a3_source_cmd_ready),.cmd_addr(a3_source_cmd_addr),
 .cmd_read(a3_source_cmd_read),.cmd_wdata(a3_source_cmd_wdata),.cmd_wmask(a3_source_cmd_wmask),
 .rsp_valid(a3_source_rsp_valid),.rsp_ready(a3_source_rsp_ready),.rsp_rdata(a3_source_rsp_rdata),
 .rsp_err(a3_source_rsp_err),.selected(s16_source_selected),.selected_bank(s16_source_bank));
reg s16_phase_error=0;
wire s16_window_active,s16_window_finished,s16_window_failed;
wire [31:0] s16_window_failure,s16_w_source,s16_w_stage,s16_w_read,s16_w_output;
wire [63:0] s16_window_start,s16_window_end,s16_window_cycles,s16_cmd_wait,s16_rsp_wait;
arch03_task_window_icb32 s16_window(
 .clk(s16_clk),.rst_n(s16_rst_n),.encoded_bytes((s16_descriptor>>17)*4),.task_arm(s16_start),.task_cancel(s16_cancel || s16_phase_error),
 .cmd_valid(`S16A.dma_cmd_valid),.cmd_ready(`S16A.dma_cmd_ready),.cmd_addr(`S16A.dma_cmd_addr),
 .cmd_read(`S16A.dma_cmd_read),.cmd_wmask(`S16A.dma_cmd_wmask),
 .rsp_valid(`S16A.dma_rsp_valid),.rsp_ready(`S16A.dma_rsp_ready),.rsp_err(`S16A.dma_rsp_err),
 .global_pending(`S16M.a3_arb_pending || `S16M.a3_router_pending),
 .fifo_empty(`S16A.transport.empty && !`S16A.half_q),
 .core_done(`S16A.core_done_q),.active(s16_window_active),.finished(s16_window_finished),
 .failed(s16_window_failed),.failure_code(s16_window_failure),
 .start_cycle(s16_window_start),.end_cycle(s16_window_end),.window_cycles(s16_window_cycles),
 .source_read_acks(s16_w_source),.input_write_acks(s16_w_stage),
 .input_read_acks(s16_w_read),.output_write_acks(s16_w_output),
 .command_wait_cycles(s16_cmd_wait),.response_wait_cycles(s16_rsp_wait));
reg [4095:0] s16_first_dir,s16_second_dir,s16_first_load,s16_second_load,s16_prefix;
reg [31:0] s16_first_words[0:11751],s16_second_words[0:11751];
wire [31:0] s16_words=s16_descriptor>>17;
reg [15:0] s16_first_raw[0:23487],s16_second_raw[0:23487];
reg [15:0] s16_first_result[0:25343],s16_second_result[0:25343];
reg s16_first_sat[0:25343],s16_second_sat[0:25343];
reg s16_core_seen[0:25343],s16_output_seen[0:25343];
reg [31:0] s16_receipt[0:32],s16_mail[0:34],s16_snapshot[0:28];
reg s16_receipt_seen[0:32],s16_snapshot_seen[0:28];
integer s16_receipt_reg[0:17];
integer s16_phase=0,s16_completed=0,s16_successes=0,s16_file=0,s16_bank=0;
integer s16_sources=0,s16_stages=0,s16_reads=0,s16_outputs=0,s16_core_outputs=0,s16_loads=0,s16_sats=0;
integer s16_starts=0,s16_cancels=0,s16_mmio_errors=0;
integer s16_i,s16_index,s16_lane,s16_receipt_index,s16_kind,s16_dma_index;
reg s16_committed=1,s16_selected_for_phase=0,s16_started=0,s16_cold_cancel_seen=0,s16_first_source_seen=0;
reg s16_dma_pending=0,s16_mmio_pending=0,s16_mmio_read,s16_cpu_pending=0,s16_cpu_read;
reg [31:0] s16_dma_addr,s16_dma_data,s16_mmio_addr,s16_mmio_data,s16_cpu_addr,s16_cpu_data;
reg [3:0] s16_dma_mask,s16_mmio_mask,s16_cpu_mask;
reg [31:0] s16_pre_source=0,s16_pre_stage=0,s16_pre_status=0;
reg [15:0] s16_value;
function [31:0] s16_word(input integer index);
 begin s16_word=s16_bank ? s16_second_words[index] : s16_first_words[index];end
endfunction
function [15:0] s16_result(input integer index);
 begin s16_result=s16_bank ? s16_second_result[index] : s16_first_result[index];end
endfunction
function s16_sat(input integer index);
 begin s16_sat=s16_bank ? s16_second_sat[index] : s16_first_sat[index];end
endfunction
initial begin
 if(!$value$plusargs("DATA_DIR=%s",s16_first_dir) || !$value$plusargs("SECOND_DIR=%s",s16_second_dir) ||
    !$value$plusargs("FIRST_LOAD32=%s",s16_first_load) || !$value$plusargs("SECOND_LOAD32=%s",s16_second_load) ||
    !$value$plusargs("CAPTURE_PREFIX=%s",s16_prefix) ||
    !$value$plusargs("FIRST_DESCRIPTOR=%h",s16_first_descriptor) ||
    !$value$plusargs("SECOND_DESCRIPTOR=%h",s16_second_descriptor) ||
    !$value$plusargs("EXPECTED_FAULT_EPC=%h",s16_fault_epc))$fatal(1,"Missing sequence observer configuration");
 if(!$value$plusargs("SHORT_TIMEOUT=%d",s16_timeout))s16_timeout=8192;
 if(s16_first_descriptor[16]!=0 || s16_second_descriptor[16]!=1 ||
    (s16_first_descriptor>>17)<8 || (s16_first_descriptor>>17)>11752 || (s16_second_descriptor>>17)<8 || (s16_second_descriptor>>17)>11752 ||
    s16_first_descriptor[15:5]!=0 || s16_second_descriptor[15:5]!=0 ||
    s16_fault_epc<32'h80000000 || s16_fault_epc>=32'h80010000 || s16_timeout<4096 || s16_timeout>32768)
  $fatal(1,"Invalid sequence observer metadata");
 $readmemh(s16_first_load,s16_first_words);$readmemh(s16_second_load,s16_second_words);
 $readmemh({s16_first_dir,"/result.hex"},s16_first_result);$readmemh({s16_second_dir,"/result.hex"},s16_second_result);
 $readmemh({s16_first_dir,"/saturated.hex"},s16_first_sat);$readmemh({s16_second_dir,"/saturated.hex"},s16_second_sat);
 for(s16_i=0;s16_i<(s16_first_descriptor>>17);s16_i=s16_i+1)if((^s16_first_words[s16_i])===1'bx)$fatal(1,"Unknown A encoded input");
 for(s16_i=0;s16_i<(s16_second_descriptor>>17);s16_i=s16_i+1)if((^s16_second_words[s16_i])===1'bx)$fatal(1,"Unknown B encoded input");
 $readmemh({s16_first_dir,"/load.hex"},s16_first_raw);$readmemh({s16_second_dir,"/load.hex"},s16_second_raw);
 for(s16_i=0;s16_i<25344;s16_i=s16_i+1)
  if((^{s16_first_result[s16_i],s16_second_result[s16_i],s16_first_sat[s16_i],s16_second_sat[s16_i]})===1'bx)
   $fatal(1,"Unknown sequence reference");
 for(s16_i=0;s16_i<35;s16_i=s16_i+1)s16_mail[s16_i]=0;
 s16_receipt_reg[3]=2;s16_receipt_reg[4]=23;s16_receipt_reg[5]=22;s16_receipt_reg[6]=8;
 s16_receipt_reg[7]=18;s16_receipt_reg[8]=19;s16_receipt_reg[9]=24;s16_receipt_reg[10]=25;
 s16_receipt_reg[11]=26;s16_receipt_reg[12]=27;s16_receipt_reg[13]=20;s16_receipt_reg[14]=21;
 s16_receipt_reg[15]=6;s16_receipt_reg[16]=7;s16_receipt_reg[17]=28;
end
always @(negedge s16_rst_n)if(s16_phase!=0)$fatal(1,"Sequence DUT reset after phase start");
always @(`S16A.dma_cmd_valid or `S16A.dma_cmd_addr or `S16A.dma_cmd_read)begin
 if(s16_rst_n && `S16A.dma_cmd_valid && `S16A.dma_cmd_read &&
    `S16A.dma_cmd_addr>=32'hb0000000 && `S16A.dma_cmd_addr<(32'hb0000000+s16_words*4) && !s16_first_source_seen)begin
  if(s16_phase<6 || s16_committed || !s16_started || !s16_source_selected ||
     s16_source_bank!=s16_bank || !s16_cold_cancel_seen || `S16A.core.busy!==1'b1 || `S16A.load_count_q!=0)
   $fatal(1,"Sequence source before selection/phase/start/PREPARE cold invalidation");
  s16_first_source_seen=1;
 end
end
task s16_arm_phase(input integer phase);
 begin
  if(!s16_committed || !s16_selected_for_phase || phase!=s16_completed+1 || phase>10 ||
     s16_dma_pending || `S16A.dma_cmd_valid || `S16A.core.busy!==1'b0 || `S16A.core.start_ready!==1'b1 ||
     !s16_source_selected || s16_source_bank!=s16_descriptor[16])$fatal(1,"Sequence phase arm before drain/selection");
  s16_phase=phase;s16_committed=0;s16_selected_for_phase=0;s16_bank=s16_descriptor[16];
  s16_sources=0;s16_stages=0;s16_reads=0;s16_outputs=0;s16_core_outputs=0;s16_loads=0;s16_sats=0;
  s16_starts=0;s16_cancels=0;s16_mmio_errors=0;s16_started=0;s16_phase_error=0;
  s16_cold_cancel_seen=0;s16_first_source_seen=0;s16_pre_source=0;s16_pre_stage=0;s16_pre_status=0;
  for(s16_i=0;s16_i<33;s16_i=s16_i+1)begin s16_receipt[s16_i]=0;s16_receipt_seen[s16_i]=0;end
  for(s16_i=0;s16_i<29;s16_i=s16_i+1)begin s16_snapshot[s16_i]=0;s16_snapshot_seen[s16_i]=0;end
  for(s16_i=0;s16_i<25344;s16_i=s16_i+1)begin s16_core_seen[s16_i]=0;s16_output_seen[s16_i]=0;end
  if(phase>=8)begin
   s16_file=$fopen($sformatf("%0s__task%0d.csv",s16_prefix,phase-7),"w");
   if(!s16_file)$fatal(1,"Sequence capture open");
  end
  $display("ICB32_SEQUENCE_PHASE_ARM phase=%0d descriptor=%08h",phase,s16_descriptor);
 end
endtask
task s16_commit_phase;
 begin
  if(s16_committed || !s16_phase || s16_dma_pending || `S16A.dma_cmd_valid || a3_source_rsp_valid ||
     `S16A.core.busy!==1'b0 || `S16A.core.start_ready!==1'b1 || !s16_window_finished || s16_window_active || s16_starts!=1)
   $fatal(1,"Sequence phase commit before actual drain/window");
  for(s16_i=0;s16_i<33;s16_i=s16_i+1)if(!s16_receipt_seen[s16_i])$fatal(1,"Missing phase receipt field %0d",s16_i);
  for(s16_i=3;s16_i<=17;s16_i=s16_i+1)
   if(!s16_snapshot_seen[s16_receipt_reg[s16_i]] || s16_receipt[s16_i]!==s16_snapshot[s16_receipt_reg[s16_i]])
    $fatal(1,"Sequence receipt differs from actual MMIO snapshot phase=%0d field=%0d",s16_phase,s16_i);
  if(s16_receipt[0]!=s16_phase || s16_receipt[25]!=s16_descriptor || s16_receipt[28]!=s16_timeout ||
     s16_receipt[21]!=(s16_phase<=5 ? s16_phase : 5) || s16_receipt[22]!=7 ||
     s16_receipt[23]!=s16_fault_epc || s16_receipt[24]!=32'h40000004 ||
     s16_receipt[9]!=s16_sources || s16_receipt[10]!=s16_stages || s16_receipt[11]!=s16_reads || s16_receipt[12]!=s16_outputs ||
     s16_receipt[13]!=s16_stages*4 || s16_receipt[14]!=s16_outputs*4 ||
     s16_receipt[15]!=s16_loads || s16_receipt[16]!=s16_core_outputs || s16_receipt[17]!=s16_sats ||
     (s16_receipt[5]&32'h3f1f)!=0 || !s16_receipt[3][14] || (s16_receipt[3]&32'h39a1)!=0)
   $fatal(1,"Sequence receipt identity/count/drain mismatch phase=%0d",s16_phase);
  if(s16_phase<=5)begin
   if(s16_receipt[1]!=1 || s16_receipt[2]!=0 || s16_receipt[32]!=0 || s16_receipt[20]!=1 ||
      s16_mmio_errors!=1 || s16_cancels<1 || s16_sources || s16_stages || s16_reads || s16_outputs ||
      s16_receipt[6]!=3 || s16_receipt[7]!=32'h40000004 || s16_receipt[8]!=2 ||
      (s16_receipt[4]&63)!=48 || s16_receipt[3][3])$fatal(1,"Configuration rejection evidence incomplete");
   case(s16_phase)
    1:if(s16_receipt[26]!=32'h28 || s16_receipt[27]!=32'hb0000002)$fatal(1,"Wrong source misalignment mutation");
    2:if(s16_receipt[26]!=32'h2c || s16_receipt[27]!=32'ha007f000)$fatal(1,"Wrong input bounds mutation");
    3:if(s16_receipt[26]!=32'h30 || s16_receipt[27]!=32'ha0000000)$fatal(1,"Wrong overlap mutation");
    4:if(s16_receipt[26]!=32'h34 || s16_receipt[27]!=28)$fatal(1,"Wrong input length mutation");
    5:if(s16_receipt[26]!=32'h38 || s16_receipt[27]!=50684)$fatal(1,"Wrong output length mutation");
   endcase
  end else begin
   if(s16_receipt[26] || s16_receipt[27] || s16_mmio_errors || s16_receipt[6])$fatal(1,"Unexpected normal-phase error");
   if(s16_phase==6 || s16_phase==7)begin
    if(s16_receipt[1]!=(s16_phase==6 ? 2 : 3) || s16_receipt[2]!=(s16_phase==6 ? 0 : 32'hffffffff) ||
       s16_receipt[32]!==s16_receipt[2] || s16_receipt[20]!=1 || s16_cancels<1 ||
       s16_sources==0 || s16_sources>=s16_words || s16_stages>=s16_words || s16_reads || s16_outputs ||
       s16_loads>=23488 || s16_core_outputs || (s16_receipt[4]&63)!=48 || s16_receipt[3][3])
     $fatal(1,"Partial cancel/timeout was not a real incomplete loading task");
    if(s16_phase==6 && (s16_receipt[29]!=s16_pre_source || s16_receipt[30]!=s16_pre_stage ||
       s16_receipt[31]!=s16_pre_status || s16_pre_source<32 || !s16_pre_status[0]))
     $fatal(1,"Partial-cancel pre-request evidence mismatch");
    if(s16_phase==7 && ({s16_receipt[19],s16_receipt[18]}<s16_timeout ||
       s16_receipt[29] || s16_receipt[30] || s16_receipt[31]))$fatal(1,"Timeout budget/evidence missing");
   end else begin
    if(s16_receipt[1]!=4 || s16_receipt[2]!=0 || s16_receipt[32]!=0 || !s16_receipt[3][3] ||
       (s16_receipt[4]&63)!=31 || s16_cancels || s16_sources!=s16_words || s16_stages!=s16_words ||
       s16_reads!=0 || s16_outputs!=12672 || s16_loads!=23488 || s16_core_outputs!=25344 ||
       s16_receipt[29] || s16_receipt[30] || s16_receipt[31])$fatal(1,"Successful task incomplete");
    for(s16_i=0;s16_i<25344;s16_i=s16_i+1)if(!s16_output_seen[s16_i])$fatal(1,"Missing sequence output");
    if(s16_window_failed || s16_w_source!=s16_words || s16_w_stage!=s16_words || s16_w_read!=0 || s16_w_output!=12672)
     $fatal(1,"Successful sequence timing window failed");
    $fclose(s16_file);s16_successes=s16_successes+1;
   end
  end
  if(s16_phase<=7 && (!s16_window_failed || s16_window_failure!=11))$fatal(1,"Failed phase misreported as successful window");
  $write("ICB32_SEQUENCE_RECEIPT phase=%0d words=",s16_phase);
  for(s16_i=0;s16_i<33;s16_i=s16_i+1)begin
   $write("%08h",s16_receipt[s16_i]);if(s16_i<32)$write(",");
  end
  $display("");
  $display("ICB32_SEQUENCE_PHASE_PASS phase=%0d kind=%0d rc=%0d source_acks=%0d stage_acks=%0d read_acks=%0d output_acks=%0d start_cycle=%0d end_cycle=%0d cycles=%0d window_failed=%0d saturated=%0d",s16_phase,s16_receipt[1],$signed(s16_receipt[2]),s16_sources,s16_stages,s16_reads,s16_outputs,s16_window_start,s16_window_end,s16_window_cycles,s16_window_failed,s16_sats);
  s16_completed=s16_completed+1;s16_committed=1;
 end
endtask
always @(posedge s16_clk)if(s16_rst_n)begin
 s16_select<=0;
 if(s16_start)begin
  if(s16_phase==0 || s16_committed || s16_started)$fatal(1,"Unexpected sequence START");
  s16_started=1;s16_starts=s16_starts+1;s16_cold_cancel_seen=0;
 end else if(s16_started && `S16A.core.cancel)s16_cold_cancel_seen=1;
 if(s16_cancel && s16_started && !s16_committed)begin
  s16_cancels=s16_cancels+1;
  s16_pre_source=s16_snapshot[24];s16_pre_stage=s16_snapshot[25];s16_pre_status=s16_snapshot[2];
 end
 if(`S16A.committed_valid && `S16A.committed_ready)begin
  if(`S16A.decoded_words>=s16_stages || `S16A.committed_data!==s16_word(`S16A.decoded_words))
   $fatal(1,"Decoder consumed encoded word before successful SRAM ACK");
 end
 if(`S16A.load_fire)begin
  if(s16_phase<6 || s16_loads+`S16A.core_load_count>23488)$fatal(1,"Unexpected decoded halfword count");
  for(s16_lane=0;s16_lane<`S16A.core_load_count;s16_lane=s16_lane+1)
   if(`S16A.core_load_data[s16_lane*16+:16] !== (s16_bank ? s16_second_raw[s16_loads+s16_lane] : s16_first_raw[s16_loads+s16_lane]))
    $fatal(1,"Decoded halfword differs from independent raw reference");
  s16_loads=s16_loads+`S16A.core_load_count;
 end
 if(`S16A.core.out_valid && `S16A.core.out_ready)begin
  s16_index=`S16A.core.out_row*256+`S16A.core.out_column;
  if(s16_phase<8 || s16_index>=25344 || s16_core_seen[s16_index] ||
     `S16A.core.result!==s16_result(s16_index) || `S16A.core.saturated!==s16_sat(s16_index))
   $fatal(1,"Sequence core coordinate/value/saturation mismatch");
  s16_core_seen[s16_index]=1;s16_core_outputs=s16_core_outputs+1;s16_sats=s16_sats+`S16A.core.saturated;
 end
 if(`S16A.dma_rsp_valid && `S16A.dma_rsp_ready)begin
  if(!s16_dma_pending || `S16A.dma_rsp_err!==1'b0)$fatal(1,"Sequence unowned/error DMA response");
  s16_dma_pending=0;
  case(s16_kind)
   1:begin
    if(s16_dma_index!=s16_sources || `S16A.dma_rsp_rdata!==s16_word(s16_dma_index))$fatal(1,"Sequence source payload/order");
    s16_sources=s16_sources+1;
   end
   2:begin
    if(s16_dma_index!=s16_stages || s16_stages>=s16_sources || s16_dma_mask!==15 || s16_dma_data!==s16_word(s16_dma_index))
     $fatal(1,"Sequence initial shared copy mismatch");
    s16_stages=s16_stages+1;
   end
   3:$fatal(1,"ICB32 may not issue shared readback");
   4:begin
    if(s16_phase<8 || s16_dma_mask!==15)$fatal(1,"Unexpected sequence output write");
    for(s16_lane=0;s16_lane<2;s16_lane=s16_lane+1)begin
     s16_index=s16_dma_index*2+s16_lane;s16_value=s16_lane ? s16_dma_data[31:16] : s16_dma_data[15:0];
     if(s16_output_seen[s16_index] || !s16_core_seen[s16_index] || s16_value!==s16_result(s16_index))$fatal(1,"Sequence writeback mismatch");
     s16_output_seen[s16_index]=1;
     $fdisplay(s16_file,"%0d,%0d,%0d,%0d",s16_index/256,s16_index%256,$signed(s16_value),s16_sat(s16_index));
    end
    s16_outputs=s16_outputs+1;
   end
   default:$fatal(1,"Unknown sequence DMA response kind");
  endcase
 end
 if(`S16A.dma_cmd_valid && `S16A.dma_cmd_ready)begin
  if(s16_dma_pending || s16_committed || s16_phase<6 || !s16_started || `S16A.dma_cmd_addr[1:0]!=0)
   $fatal(1,"Sequence DMA request outside active task or multiple outstanding");
  s16_dma_pending=1;s16_dma_addr=`S16A.dma_cmd_addr;s16_dma_data=`S16A.dma_cmd_wdata;s16_dma_mask=`S16A.dma_cmd_wmask;
  if(s16_dma_addr>=32'hb0000000 && s16_dma_addr<(32'hb0000000+s16_words*4) && `S16A.dma_cmd_read)begin s16_kind=1;s16_dma_index=(s16_dma_addr-32'hb0000000)>>2;end
  else if(s16_dma_addr>=32'ha0000000 && s16_dma_addr<(32'ha0000000+s16_words*4))begin s16_kind=`S16A.dma_cmd_read ? 3 : 2;s16_dma_index=(s16_dma_addr-32'ha0000000)>>2;end
  else if(s16_dma_addr>=32'ha000c000 && s16_dma_addr<32'ha0018600 && !`S16A.dma_cmd_read)begin s16_kind=4;s16_dma_index=(s16_dma_addr-32'ha000c000)>>2;end
  else $fatal(1,"Unexpected sequence DMA address");
 end
 if(`S16A.rsp_valid && `S16A.rsp_ready)begin
  if(!s16_mmio_pending)$fatal(1,"Sequence unowned MMIO response");s16_mmio_pending=0;
  if(`S16A.rsp_err!==1'b0 && `S16A.rsp_err!==1'b1)$fatal(1,"Unknown sequence register error flag");
  if(`S16A.rsp_err===1'b1)begin
   if(s16_phase<1 || s16_phase>5 || s16_mmio_read || s16_mmio_addr!=32'h40000004 || s16_mmio_data!=1)
    $fatal(1,"Unexpected sequence register error");
   s16_mmio_errors=s16_mmio_errors+1;s16_phase_error=1;
  end else if(s16_mmio_read && s16_phase && !s16_committed && s16_mmio_addr>=32'h40000000 && s16_mmio_addr<=32'h40000070)begin
   if((^`S16A.rsp_rdata)===1'bx)$fatal(1,"Unknown sequence register read data");
   s16_index=(s16_mmio_addr-32'h40000000)>>2;s16_snapshot[s16_index]=`S16A.rsp_rdata;s16_snapshot_seen[s16_index]=1;
  end
 end
 if(`S16A.cmd_valid && `S16A.cmd_ready)begin
  if(s16_mmio_pending)$fatal(1,"Sequence MMIO multiple outstanding");
  s16_mmio_pending=1;s16_mmio_read=`S16A.cmd_read;s16_mmio_addr=`S16A.cmd_addr;s16_mmio_data=`S16A.cmd_wdata;s16_mmio_mask=`S16A.cmd_wmask;
 end
 if(`S16M.a3_cpu_rsp_valid && `S16M.a3_cpu_rsp_ready)begin
  if(!s16_cpu_pending || `S16M.a3_cpu_rsp_err!==1'b0)$fatal(1,"Sequence unowned/error CPU memory response");
  s16_cpu_pending=0;
  if(s16_cpu_read || s16_cpu_mask!==15 || s16_cpu_addr[1:0]!=0)$fatal(1,"Sequence CPU may only write aligned mail/receipt words");
  if(s16_cpu_addr>=32'ha0020000 && s16_cpu_addr<32'ha0020a00)begin
   if(s16_committed || ((s16_cpu_addr-32'ha0020000)>>8)!=s16_phase-1 || s16_cpu_addr[7:2]>32)
    $fatal(1,"Sequence receipt outside current phase");
   s16_receipt_index=s16_cpu_addr[7:2];if(s16_receipt_seen[s16_receipt_index])$fatal(1,"Duplicate sequence receipt word");
   s16_receipt[s16_receipt_index]=s16_cpu_data;s16_receipt_seen[s16_receipt_index]=1;
  end else if(s16_cpu_addr>=32'ha001f000 && s16_cpu_addr<32'ha001f08c)begin
   s16_index=(s16_cpu_addr-32'ha001f000)>>2;s16_mail[s16_index]=s16_cpu_data;
   if(s16_index==33)begin
    if(!s16_committed || s16_selected_for_phase || s16_dma_pending || `S16A.dma_cmd_valid || a3_source_rsp_valid ||
       `S16A.core.busy!==1'b0 || `S16A.core.start_ready!==1'b1 || s16_cpu_data!==(s16_completed==8 ? s16_second_descriptor : s16_first_descriptor))
     $fatal(1,"Sequence source switch before drain or wrong descriptor");
    s16_descriptor=s16_cpu_data;s16_select<=1;s16_selected_for_phase=1;
   end
   if(s16_index==32 && s16_cpu_data!=0)s16_arm_phase(s16_cpu_data);
   if(s16_index==34 && s16_cpu_data!=0)begin
    if(s16_cpu_data!=s16_phase)$fatal(1,"Wrong phase commit marker");s16_commit_phase;
   end
   if(s16_index==0 && s16_cpu_data!=0)begin
    if(s16_cpu_data!==32'h53363450 || !s16_committed || s16_completed!=10 || s16_successes!=3 ||
       s16_mail[1]!=0 || s16_mail[2]!=10 || s16_mail[3]!=10 || s16_mail[4]!=5 ||
       s16_mail[5]!=32'h53363431 || s16_mail[6]!=0 || s16_mail[7]!=s16_first_descriptor ||
       s16_mail[8]!=s16_second_descriptor || s16_mail[9]!=s16_timeout)$fatal(1,"DMA16 sequence final evidence failed");
`ifdef ARCH03_SEQUENCE_NO_CPU
    $display("ICB32_SEQUENCE_PASS phases=10 tasks=3 outputs=76032 cpu_executed=false actual_CPU_traps_verified=false actual_driver_timeout_verified=false");
`else
    $display("ICB32_SEQUENCE_PASS phases=10 tasks=3 outputs=76032 cpu_executed=true guarded_faults=5 timeout_recovery=true");
`endif
    $finish;
   end
  end else $fatal(1,"Unexpected sequence CPU shared-memory traffic");
 end
 if(`S16M.a3_cpu_cmd_valid && `S16M.a3_cpu_cmd_ready)begin
  if(s16_cpu_pending)$fatal(1,"Sequence CPU multiple outstanding");
  s16_cpu_pending=1;s16_cpu_addr=`S16M.a3_cpu_cmd_addr;s16_cpu_read=`S16M.a3_cpu_cmd_read;
  s16_cpu_data=`S16M.a3_cpu_cmd_wdata;s16_cpu_mask=`S16M.a3_cpu_cmd_wmask;
 end
end
initial begin #1000000000;$fatal(1,"DMA16 sequence timeout phase=%0d completed=%0d",s16_phase,s16_completed);end
`undef S16A
`undef S16M
