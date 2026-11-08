// Included inside the official tb_top. Observe only actual E203 bus transactions.
`define A3MEM u_e203_soc_top.u_e203_subsys_top.u_e203_subsys_main.u_e203_subsys_mems
// Typed aliases defer cross-module binding to elaboration before bit selects.
wire a3_mon_clk = `A3MEM.clk;
wire a3_mon_rst_n = `A3MEM.rst_n;
wire a3_mon_cmd_valid = `A3MEM.a3_mem_cmd_valid;
wire a3_mon_cmd_ready = `A3MEM.a3_mem_cmd_ready;
wire a3_mon_cmd_read = `A3MEM.a3_mem_cmd_read;
wire [31:0] a3_mon_cmd_addr = `A3MEM.a3_mem_cmd_addr;
wire [31:0] a3_mon_cmd_wdata = `A3MEM.a3_mem_cmd_wdata;
wire [3:0] a3_mon_cmd_wmask = `A3MEM.a3_mem_cmd_wmask;
wire a3_window_active,a3_window_finished;
wire [63:0] a3_window_start,a3_window_end,a3_window_reads,a3_window_writes,a3_window_cmd_wait,a3_window_rsp_wait;
arch03_task_window a3_task_window(
    .clk(a3_mon_clk),.rst_n(a3_mon_rst_n),.cmd_valid(a3_mon_cmd_valid),.cmd_ready(a3_mon_cmd_ready),
    .cmd_read(a3_mon_cmd_read),.cmd_addr(a3_mon_cmd_addr),.cmd_wdata(a3_mon_cmd_wdata),.cmd_wmask(a3_mon_cmd_wmask),
    .rsp_valid(`A3MEM.a3_mem_rsp_valid),.rsp_ready(`A3MEM.a3_mem_rsp_ready),.rsp_err(`A3MEM.a3_mem_rsp_err),
    .active(a3_window_active),.finished(a3_window_finished),.start_cycle(a3_window_start),.end_cycle(a3_window_end),
    .read_commands(a3_window_reads),.write_commands(a3_window_writes),
    .command_wait_cycles(a3_window_cmd_wait),.response_wait_cycles(a3_window_rsp_wait));
reg [4095:0] a3_activity_path;
reg a3_activity_enabled=0;
initial begin
    if($value$plusargs("ACTIVITY=%s",a3_activity_path))begin
        a3_activity_enabled=1;
        $dumpfile(a3_activity_path);
        $dumpvars(0,u_e203_soc_top);
        $dumpoff;
    end
end
always @(posedge a3_window_active) if(a3_activity_enabled)$dumpon;
always @(posedge a3_window_finished) if(a3_activity_enabled)begin $dumpoff;$dumpflush;end
reg [15:0] a3_expected[0:25343],a3_input_expected[0:23487];
reg a3_seen[0:25343];
reg [31:0] a3_mail[0:6];
reg [4095:0] a3_dir,a3_capture;
integer a3_outputs=0,a3_loads=0,a3_file,a3_i,a3_index;
reg [15:0] a3_value;
initial begin
    if(!$value$plusargs("DATA_DIR=%s",a3_dir))$fatal(1,"missing DATA_DIR");
    if(!$value$plusargs("CAPTURE=%s",a3_capture))$fatal(1,"missing CAPTURE");
    $readmemh({a3_dir,"/result.hex"},a3_expected);
    $readmemh({a3_dir,"/load.hex"},a3_input_expected);
    for(a3_i=0;a3_i<25344;a3_i=a3_i+1)a3_seen[a3_i]=0;
    for(a3_i=0;a3_i<7;a3_i=a3_i+1)a3_mail[a3_i]=0;
    a3_file=$fopen(a3_capture,"w");if(a3_file==0)$fatal(1,"capture open");
end
always @(posedge a3_mon_clk) begin
    if(a3_mon_rst_n && a3_mon_cmd_valid && a3_mon_cmd_ready && !a3_mon_cmd_read) begin
        if(a3_mon_cmd_addr>=32'ha0000000 && a3_mon_cmd_addr<32'ha000b780) begin
            a3_index=(a3_mon_cmd_addr-32'ha0000000)>>1;
            if(a3_mon_cmd_wmask!==(a3_mon_cmd_addr[1] ? 4'hc : 4'h3))$fatal(1,"load mask");
            a3_value=a3_mon_cmd_addr[1] ? a3_mon_cmd_wdata[31:16] : a3_mon_cmd_wdata[15:0];
            if(a3_index!=a3_loads || a3_value!==a3_input_expected[a3_index])$fatal(1,"CPU input copy mismatch");
            a3_loads=a3_loads+1;
        end
        if(a3_mon_cmd_addr>=32'ha000c000 && a3_mon_cmd_addr<32'ha0018600) begin
            a3_index=(a3_mon_cmd_addr-32'ha000c000)>>1;
            if(a3_mon_cmd_wmask!==(a3_mon_cmd_addr[1] ? 4'hc : 4'h3))$fatal(1,"output mask");
            a3_value=a3_mon_cmd_addr[1] ? a3_mon_cmd_wdata[31:16] : a3_mon_cmd_wdata[15:0];
            if(a3_seen[a3_index] || a3_value!==a3_expected[a3_index])
                $fatal(1,"CPU writeback mismatch index=%0d got=%h expected=%h",a3_index,a3_value,a3_expected[a3_index]);
            a3_seen[a3_index]=1;a3_outputs=a3_outputs+1;
            $fdisplay(a3_file,"%0d,%0d",a3_index,$signed(a3_value));
        end
        if(a3_mon_cmd_addr>=32'ha001f000 && a3_mon_cmd_addr<32'ha001f01c) begin
            if(a3_mon_cmd_wmask!==15)$fatal(1,"mailbox mask");
            a3_index=(a3_mon_cmd_addr-32'ha001f000)>>2;
            a3_mail[a3_index]=a3_mon_cmd_wdata;
            if(a3_index==0 && a3_mail[0]!=0) begin
                if(a3_mail[0]!==32'h4b575450 || a3_mail[1]!==0)
                    $fatal(1,"firmware failed magic=%h rc/cause=%h epc/count=%h mtval/count=%h",a3_mail[0],a3_mail[1],a3_mail[2],a3_mail[3]);
                if(a3_loads!=23488 || a3_outputs!=25344 || a3_mail[2]!=23488 || a3_mail[3]!=25344)
                    $fatal(1,"CPU task counts incomplete");
                if(!a3_window_finished || a3_window_active)$fatal(1,"Missing final-write-response timing boundary");
                $display("ARCH03_WINDOW_BUS reads=%0d writes=%0d command_wait=%0d response_wait=%0d",a3_window_reads,a3_window_writes,a3_window_cmd_wait,a3_window_rsp_wait);
                for(a3_i=0;a3_i<25344;a3_i=a3_i+1)if(!a3_seen[a3_i])$fatal(1,"missing CPU output");
                $fclose(a3_file);
                $display("ARCH03_SOC_PASS outputs=25344 cpu_executed=true cycles=%0d saturated=%0d",{a3_mail[5],a3_mail[4]},a3_mail[6]);
                $finish;
            end
        end
    end
end
initial begin #1000000000;$fatal(1,"ARCH03 SoC timeout outputs=%0d loads=%0d",a3_outputs,a3_loads);end
`undef A3MEM
