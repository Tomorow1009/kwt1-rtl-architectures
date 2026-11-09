// Repaired original MMIO8 reference, real SysMem source -> shared -> CPU MMIO.
// Count successful responses and observe OUTPUT_DATA saturation/coordinates.
`define M8MEM u_e203_soc_top.u_e203_subsys_top.u_e203_subsys_main.u_e203_subsys_mems
`define M8ACC `M8MEM.u_arch03_accel
wire a3_mon_clk=`M8MEM.clk;
wire a3_mon_rst_n=`M8MEM.rst_n;
reg a3_window_active=0,a3_window_finished=0;
reg [63:0] m8_cycle=0,m8_start_cycle=0,m8_end_cycle=0;
realtime m8_start_ns=0,m8_end_ns=0;
reg m8_armed=0,m8_cleared=0,m8_clear_command_seen=0,m8_finish_requested=0;
reg [15:0] m8_expected[0:25343],m8_input[0:23487];
reg m8_expected_sat[0:25343],m8_sat[0:25343],m8_seen[0:25343],m8_returned[0:25343];
reg [31:0] m8_mail[0:20];
reg m8_pending=0,m8_read,m8_mmio_pending=0,m8_mmio_read;
reg [31:0] m8_addr,m8_data,m8_mmio_addr,m8_mmio_data;
reg [3:0] m8_mask,m8_mmio_mask;
reg [4095:0] m8_dir,m8_capture,m8_activity;
reg m8_activity_enabled=0;
integer m8_sources=0,m8_copies=0,m8_reads=0,m8_loads=0,m8_returns=0,m8_outputs=0,m8_sats=0;
integer m8_i,m8_index,m8_file,m8_cmd_wait=0,m8_rsp_wait=0;
reg [15:0] m8_value;
arch03_dma16_source m8_source(
 .clk(a3_mon_clk),.rst_n(a3_mon_rst_n),
 .cmd_valid(a3_source_cmd_valid),.cmd_ready(a3_source_cmd_ready),
 .cmd_addr(a3_source_cmd_addr),.cmd_read(a3_source_cmd_read),
 .cmd_wdata(a3_source_cmd_wdata),.cmd_wmask(a3_source_cmd_wmask),
 .rsp_valid(a3_source_rsp_valid),.rsp_ready(a3_source_rsp_ready),
 .rsp_rdata(a3_source_rsp_rdata),.rsp_err(a3_source_rsp_err));
initial begin
 if(!$value$plusargs("DATA_DIR=%s",m8_dir))$fatal(1,"Missing MMIO8 DATA_DIR");
 if(!$value$plusargs("CAPTURE=%s",m8_capture))$fatal(1,"Missing MMIO8 CAPTURE");
 $readmemh({m8_dir,"/load.hex"},m8_input);
 $readmemh({m8_dir,"/result.hex"},m8_expected);
 $readmemh({m8_dir,"/saturated.hex"},m8_expected_sat);
 for(m8_i=0;m8_i<23488;m8_i=m8_i+1)if((^m8_input[m8_i])===1'bx)$fatal(1,"Missing MMIO8 input reference");
 for(m8_i=0;m8_i<25344;m8_i=m8_i+1)begin
  if((^m8_expected[m8_i])===1'bx || m8_expected_sat[m8_i]===1'bx)$fatal(1,"Missing MMIO8 output reference");
  m8_seen[m8_i]=0;m8_returned[m8_i]=0;m8_sat[m8_i]=1'bx;
 end
 for(m8_i=0;m8_i<21;m8_i=m8_i+1)m8_mail[m8_i]=0;
 m8_file=$fopen(m8_capture,"w");if(!m8_file)$fatal(1,"MMIO8 capture open");
 if($value$plusargs("ACTIVITY=%s",m8_activity))begin
  m8_activity_enabled=1;$dumpfile(m8_activity);$dumpvars(0,u_e203_soc_top);$dumpoff;
 end
end
// A reset invalidates an earlier clear certificate. This positive single-task
// monitor rejects an armed-task reset; it does not turn a cancelled task into
// a successful task or claim to validate a multi-task recovery program.
always @(negedge a3_mon_rst_n)begin
 m8_clear_command_seen=0;m8_cleared=0;
 if(m8_armed || a3_window_active || m8_finish_requested)
  $fatal(1,"MMIO8 reset during armed or active task");
end
// Request valid at the CPU-side arbitration boundary, before ready waiting.
always @(`M8MEM.a3_cpu_cmd_valid or `M8MEM.a3_cpu_cmd_addr or `M8MEM.a3_cpu_cmd_read)begin
 if(a3_mon_rst_n && !a3_window_active && !a3_window_finished &&
    `M8MEM.a3_cpu_cmd_valid && `M8MEM.a3_cpu_cmd_read &&
    `M8MEM.a3_cpu_cmd_addr>=32'hb0000000 && `M8MEM.a3_cpu_cmd_addr<32'hb000b780)begin
  if(!m8_armed || !m8_cleared)$fatal(1,"MMIO8 source before arm and observed accelerator clear");
  a3_window_active=1;m8_start_cycle=m8_cycle;m8_start_ns=$realtime;
  if(m8_activity_enabled)$dumpon;
 end
end
always @(m8_finish_requested or m8_pending or `M8MEM.a3_cpu_cmd_valid or
         `M8MEM.a3_arb_pending or `M8MEM.a3_router_pending)begin
 if(m8_finish_requested && !m8_pending && !`M8MEM.a3_cpu_cmd_valid &&
    !`M8MEM.a3_arb_pending && !`M8MEM.a3_router_pending && !a3_window_finished)begin
  a3_window_active=0;a3_window_finished=1;
  $display("MMIO8_SOURCE_WINDOW start_cycle=%0d end_cycle=%0d cycles=%0d start_ns=%.6f end_ns=%.6f source_read_acks=%0d input_write_acks=%0d input_read_acks=%0d output_write_acks=%0d command_wait=%0d response_wait=%0d",m8_start_cycle,m8_end_cycle,m8_end_cycle-m8_start_cycle,m8_start_ns,m8_end_ns,m8_sources,m8_copies,m8_reads,m8_outputs,m8_cmd_wait,m8_rsp_wait);
 end
end
always @(posedge a3_mon_clk)if(a3_mon_rst_n)begin
 m8_cycle=m8_cycle+1;
 if(a3_window_active && `M8MEM.a3_cpu_cmd_valid && !`M8MEM.a3_cpu_cmd_ready)m8_cmd_wait=m8_cmd_wait+1;
 if(a3_window_active && `M8MEM.a3_cpu_rsp_valid && !`M8MEM.a3_cpu_rsp_ready)m8_rsp_wait=m8_rsp_wait+1;
 if(`M8ACC.rsp_valid && `M8ACC.rsp_ready)begin
  if(!m8_mmio_pending || `M8ACC.rsp_err!==1'b0)$fatal(1,"MMIO8 unowned/error register response");
  m8_mmio_pending=0;
  if(!m8_mmio_read && m8_mmio_addr==32'h40000004 && m8_mmio_data==2)begin
   m8_clear_command_seen=1;m8_cleared=0;
  end
  if(m8_mmio_read && m8_mmio_addr==32'h40000008)
   m8_cleared=m8_clear_command_seen && ((`M8ACC.rsp_rdata&31)===32'b0);
  if(!m8_mmio_read && m8_mmio_addr==32'h40000010)begin
   if(m8_loads>=23488 || m8_mmio_mask!==15 || m8_mmio_data!=={16'b0,m8_input[m8_loads]})$fatal(1,"MMIO8 LOAD input mismatch");
   if(m8_reads<=m8_loads)$fatal(1,"MMIO8 LOAD bypassed shared read");
   m8_loads=m8_loads+1;
  end
  if(m8_mmio_read && m8_mmio_addr==32'h40000014)begin
   m8_index=((`M8ACC.rsp_rdata>>16)&127)*256+((`M8ACC.rsp_rdata>>23)&255);
   if(m8_index<0 || m8_index>=25344 || m8_returned[m8_index])$fatal(1,"MMIO8 result coordinate");
   if(`M8ACC.rsp_rdata[15:0]!==m8_expected[m8_index] || `M8ACC.rsp_rdata[31]!==m8_expected_sat[m8_index])$fatal(1,"MMIO8 result/saturation mismatch");
   m8_returned[m8_index]=1;m8_sat[m8_index]=`M8ACC.rsp_rdata[31];m8_returns=m8_returns+1;m8_sats=m8_sats+`M8ACC.rsp_rdata[31];
  end
 end
 if(`M8ACC.cmd_valid && `M8ACC.cmd_ready)begin
  if(m8_mmio_pending)$fatal(1,"MMIO8 register outstanding");
  m8_mmio_pending=1;m8_mmio_addr=`M8ACC.cmd_addr;m8_mmio_read=`M8ACC.cmd_read;
  m8_mmio_data=`M8ACC.cmd_wdata;m8_mmio_mask=`M8ACC.cmd_wmask;
  if(!`M8ACC.cmd_read && `M8ACC.cmd_addr==32'h40000004 &&
     (`M8ACC.cmd_wdata==1 || `M8ACC.cmd_wdata==2))begin
   // An accepted replacement clear is not a successful clear until its ACK;
   // START consumes the prior idle certificate before it can arm a new task.
   m8_clear_command_seen=0;m8_cleared=0;
  end
 end
 if(`M8MEM.a3_cpu_rsp_valid && `M8MEM.a3_cpu_rsp_ready)begin
  if(!m8_pending || `M8MEM.a3_cpu_rsp_err!==1'b0)$fatal(1,"MMIO8 unowned/error memory response");
  m8_pending=0;
  if(m8_addr>=32'hb0000000 && m8_addr<32'hb000b780)begin
   if(!a3_window_active || !m8_read || m8_addr!=32'hb0000000+m8_sources*4 ||
      `M8MEM.a3_cpu_rsp_rdata!=={m8_input[2*m8_sources+1],m8_input[2*m8_sources]})$fatal(1,"MMIO8 source sequence/data");
   m8_sources=m8_sources+1;
  end else if(m8_addr>=32'ha0000000 && m8_addr<32'ha000b780)begin
   if(a3_window_finished)$fatal(1,"MMIO8 extra input traffic after completion");
   if(m8_read)begin
    if(m8_reads>=23488 || m8_addr!=32'ha0000000+2*m8_reads || m8_reads/2>=m8_copies ||
       `M8MEM.a3_cpu_rsp_rdata!=={m8_input[2*(m8_reads/2)+1],m8_input[2*(m8_reads/2)]})$fatal(1,"MMIO8 shared read sequence/data");
    m8_reads=m8_reads+1;
   end else begin
    if(m8_copies>=11744 || m8_copies>=m8_sources || m8_addr!=32'ha0000000+m8_copies*4 || m8_mask!==15 ||
       m8_data!=={m8_input[2*m8_copies+1],m8_input[2*m8_copies]})$fatal(1,"MMIO8 initial shared write");
    m8_copies=m8_copies+1;
   end
  end else if(m8_addr>=32'ha000c000 && m8_addr<32'ha0018600)begin
   m8_index=(m8_addr-32'ha000c000)>>1;m8_value=m8_addr[1] ? m8_data[31:16] : m8_data[15:0];
   if(m8_read || m8_addr[0] || m8_mask!==(m8_addr[1] ? 4'hc : 4'h3) || m8_seen[m8_index] ||
      !m8_returned[m8_index] || m8_value!==m8_expected[m8_index])$fatal(1,"MMIO8 actual output writeback");
   m8_seen[m8_index]=1;m8_outputs=m8_outputs+1;
   $fdisplay(m8_file,"%0d,%0d,%0d,%0d",m8_index/256,m8_index%256,$signed(m8_value),m8_sat[m8_index]);
   if(m8_outputs==25344)begin
    if(m8_sources!=11744 || m8_copies!=11744 || m8_reads!=23488 || m8_loads!=23488 || m8_returns!=25344)$fatal(1,"MMIO8 final counts");
    m8_end_cycle=m8_cycle;m8_end_ns=$realtime;m8_finish_requested=1;
    if(m8_activity_enabled)begin $dumpoff;$dumpflush;end
   end
  end else if(m8_addr>=32'ha001f000 && m8_addr<32'ha001f054 && !m8_read)begin
   if(m8_mask!==15 || m8_addr[1:0]!=0)$fatal(1,"MMIO8 mailbox mask");
   m8_index=(m8_addr-32'ha001f000)>>2;m8_mail[m8_index]=m8_data;
   if(m8_index==8 && m8_data==32'h4b575442)begin
    if(m8_armed || a3_window_active || !m8_clear_command_seen || !m8_cleared)
     $fatal(1,"MMIO8 invalid arm: successful clear ACK and fresh idle STATUS required");
    m8_armed=1;
   end
   if(m8_index==0 && m8_data!=0)begin
    if(m8_data!==32'h4b575450 || m8_mail[1]!=0)$fatal(1,"MMIO8 CPU failed rc=%h",m8_mail[1]);
    if(!a3_window_finished || a3_window_active || m8_mail[2]!=23488 || m8_mail[3]!=25344 || m8_mail[6]!=m8_sats ||
       m8_mail[9]!=11744 || m8_mail[10]!=32'h00080001 || m8_mail[11]!=32'hb0000000 || m8_mail[20]!=32'h4d385331)$fatal(1,"MMIO8 CPU completion evidence");
    for(m8_i=0;m8_i<25344;m8_i=m8_i+1)if(!m8_seen[m8_i])$fatal(1,"MMIO8 missing output");
    $fclose(m8_file);
    $display("ARCH03_MMIO8_SOURCE_PASS outputs=25344 cpu_executed=true cycles=%0d cpu_cycles=%0d saturated=%0d",m8_end_cycle-m8_start_cycle,{m8_mail[5],m8_mail[4]},m8_sats);
    $finish;
   end
  end
 end
 if(`M8MEM.a3_cpu_cmd_valid && `M8MEM.a3_cpu_cmd_ready)begin
  if(m8_pending)$fatal(1,"MMIO8 memory outstanding");
  m8_pending=1;m8_addr=`M8MEM.a3_cpu_cmd_addr;m8_read=`M8MEM.a3_cpu_cmd_read;
  m8_data=`M8MEM.a3_cpu_cmd_wdata;m8_mask=`M8MEM.a3_cpu_cmd_wmask;
 end
end
initial begin #1000000000;$fatal(1,"MMIO8 source SoC timeout outputs=%0d",m8_outputs);end
`undef M8ACC
`undef M8MEM
