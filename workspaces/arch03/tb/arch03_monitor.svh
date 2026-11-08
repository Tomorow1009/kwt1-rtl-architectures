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
// Passive profiling: never drives DUT signals and adds no firmware MMIO/CSR.
// All counts are in a3_mon_clk cycles, not inferred CPU retired instructions.
wire a3_prof_valid = `A3MEM.u_arch03_accel.cmd_valid;
wire a3_prof_ready = `A3MEM.u_arch03_accel.cmd_ready;
wire a3_prof_read = `A3MEM.u_arch03_accel.cmd_read;
wire [31:0] a3_prof_addr = `A3MEM.u_arch03_accel.cmd_addr;
wire [31:0] a3_prof_wdata = `A3MEM.u_arch03_accel.cmd_wdata;
wire a3_prof_busy = `A3MEM.u_arch03_accel.busy;
wire a3_prof_load_ready = `A3MEM.u_arch03_accel.load_ready;
wire a3_prof_out_valid = `A3MEM.u_arch03_accel.out_valid;
reg [63:0] a3_prof_tick=0,a3_prof_first_copy=0,a3_prof_last_copy=0;
reg [63:0] a3_prof_start=0,a3_prof_last_write=0;
reg [63:0] a3_prof_polls=0,a3_prof_loads=0,a3_prof_pops=0;
reg [63:0] a3_prof_accel_wait=0,a3_prof_mem_wait=0;
reg [63:0] a3_prof_load_cycles=0,a3_prof_output_cycles=0,a3_prof_other_busy=0;
reg a3_prof_copy_seen=0,a3_prof_started=0;
always @(posedge a3_mon_clk) begin
    if(!a3_mon_rst_n) begin
        a3_prof_tick<=0;a3_prof_first_copy<=0;a3_prof_last_copy<=0;
        a3_prof_start<=0;a3_prof_last_write<=0;
        a3_prof_polls<=0;a3_prof_loads<=0;a3_prof_pops<=0;
        a3_prof_accel_wait<=0;a3_prof_mem_wait<=0;
        a3_prof_load_cycles<=0;a3_prof_output_cycles<=0;a3_prof_other_busy<=0;
        a3_prof_copy_seen<=0;a3_prof_started<=0;
    end else begin
        a3_prof_tick<=a3_prof_tick+1;
        if(a3_prof_valid && !a3_prof_ready) a3_prof_accel_wait<=a3_prof_accel_wait+1;
        if(a3_mon_cmd_valid && !a3_mon_cmd_ready) a3_prof_mem_wait<=a3_prof_mem_wait+1;
        if(a3_prof_busy) begin
            if(a3_prof_load_ready) a3_prof_load_cycles<=a3_prof_load_cycles+1;
            else if(a3_prof_out_valid) a3_prof_output_cycles<=a3_prof_output_cycles+1;
            else a3_prof_other_busy<=a3_prof_other_busy+1;
        end
        if(a3_prof_valid && a3_prof_ready) begin
            if(a3_prof_read && a3_prof_addr==32'h40000008) a3_prof_polls<=a3_prof_polls+1;
            if(!a3_prof_read && a3_prof_addr==32'h40000010) a3_prof_loads<=a3_prof_loads+1;
            if(a3_prof_read && a3_prof_addr==32'h40000014) a3_prof_pops<=a3_prof_pops+1;
            if(!a3_prof_read && a3_prof_addr==32'h40000004 && a3_prof_wdata==1) begin
                a3_prof_start<=a3_prof_tick;a3_prof_started<=1;
            end
        end
        if(a3_mon_cmd_valid && a3_mon_cmd_ready && !a3_mon_cmd_read) begin
            if(a3_mon_cmd_addr>=32'ha0000000 && a3_mon_cmd_addr<32'ha000b780) begin
                if(!a3_prof_copy_seen) a3_prof_first_copy<=a3_prof_tick;
                a3_prof_copy_seen<=1;a3_prof_last_copy<=a3_prof_tick;
            end
            if(a3_mon_cmd_addr>=32'ha000c000 && a3_mon_cmd_addr<32'ha0018600)
                a3_prof_last_write<=a3_prof_tick;
        end
    end
end
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
                for(a3_i=0;a3_i<25344;a3_i=a3_i+1)if(!a3_seen[a3_i])$fatal(1,"missing CPU output");
                $fclose(a3_file);
                if(!a3_prof_copy_seen || !a3_prof_started || a3_prof_loads!=23488 || a3_prof_pops!=25344)
                    $fatal(1,"profile transaction counts incomplete");
                $display("ARCH03_PROFILE polls=%0d loads=%0d pops=%0d accel_cmd_wait=%0d mem_cmd_wait=%0d load_ready_cycles=%0d output_valid_cycles=%0d other_busy_cycles=%0d copy_span=%0d start_to_last_write=%0d",
                    a3_prof_polls,a3_prof_loads,a3_prof_pops,a3_prof_accel_wait,a3_prof_mem_wait,
                    a3_prof_load_cycles,a3_prof_output_cycles,a3_prof_other_busy,
                    a3_prof_last_copy-a3_prof_first_copy+1,a3_prof_last_write-a3_prof_start+1);
                $display("ARCH03_SOC_PASS outputs=25344 cpu_executed=true cycles=%0d saturated=%0d",{a3_mail[5],a3_mail[4]},a3_mail[6]);
                $finish;
            end
        end
    end
end
initial begin #1000000000;$fatal(1,"ARCH03 SoC timeout outputs=%0d loads=%0d",a3_outputs,a3_loads);end
`undef A3MEM
