// Passive A/B/A CPU regression monitor. References only check actual bus data.
// This include never drives DUT signals or changes DUT memory contents.
`define A3SEQMEM u_e203_soc_top.u_e203_subsys_top.u_e203_subsys_main.u_e203_subsys_mems
wire a3s_clk=`A3SEQMEM.clk,a3s_rst_n=`A3SEQMEM.rst_n;
wire a3s_cv=`A3SEQMEM.a3_mem_cmd_valid,a3s_cr=`A3SEQMEM.a3_mem_cmd_ready,a3s_read=`A3SEQMEM.a3_mem_cmd_read;
wire [31:0] a3s_addr=`A3SEQMEM.a3_mem_cmd_addr,a3s_data=`A3SEQMEM.a3_mem_cmd_wdata;
wire [3:0] a3s_mask=`A3SEQMEM.a3_mem_cmd_wmask;
wire a3s_av=`A3SEQMEM.expl_axi_icb_cmd_valid,a3s_ar=`A3SEQMEM.expl_axi_icb_cmd_ready,a3s_aread=`A3SEQMEM.expl_axi_icb_cmd_read;
wire [31:0] a3s_aaddr=`A3SEQMEM.expl_axi_icb_cmd_addr,a3s_adata=`A3SEQMEM.expl_axi_icb_cmd_wdata;
wire [3:0] a3s_amask=`A3SEQMEM.expl_axi_icb_cmd_wmask;
wire a3s_active,a3s_finished;
wire [63:0] a3s_start,a3s_end,a3s_reads,a3s_writes,a3s_cmd_wait,a3s_rsp_wait;
arch03_task_window #(.REPEAT_TASKS(1)) a3s_window(
    .clk(a3s_clk),.rst_n(a3s_rst_n),.cmd_valid(a3s_cv),.cmd_ready(a3s_cr),.cmd_read(a3s_read),
    .cmd_addr(a3s_addr),.cmd_wdata(a3s_data),.cmd_wmask(a3s_mask),
    .rsp_valid(`A3SEQMEM.a3_mem_rsp_valid),.rsp_ready(`A3SEQMEM.a3_mem_rsp_ready),.rsp_err(`A3SEQMEM.a3_mem_rsp_err),
    .active(a3s_active),.finished(a3s_finished),.start_cycle(a3s_start),.end_cycle(a3s_end),
    .read_commands(a3s_reads),.write_commands(a3s_writes),.command_wait_cycles(a3s_cmd_wait),.response_wait_cycles(a3s_rsp_wait));
reg [15:0] a3s_expected[0:25343],a3s_input[0:23487];
reg a3s_seen[0:25343];
reg [31:0] a3s_mail[0:11];
reg [4095:0] a3s_first_dir,a3s_second_dir,a3s_prefix;
integer a3s_task=0,a3s_loads=0,a3s_outputs=0,a3s_file,a3s_i,a3s_index;
integer a3s_phase=0,a3s_starts=0,a3s_aborts=0,a3s_partial_loads=0,a3s_output_reads=0;
reg a3s_poison_verified=0,a3s_timeout_verified=0;
reg [15:0] a3s_value;
task a3s_prepare_reference(input [4095:0] directory);
    begin
        for(a3s_i=0;a3s_i<25344;a3s_i=a3s_i+1)a3s_expected[a3s_i]=16'hxxxx;
        for(a3s_i=0;a3s_i<23488;a3s_i=a3s_i+1)a3s_input[a3s_i]=16'hxxxx;
        $readmemh({directory,"/result.hex"},a3s_expected);
        $readmemh({directory,"/load.hex"},a3s_input);
        for(a3s_i=0;a3s_i<25344;a3s_i=a3s_i+1)
            if((^a3s_expected[a3s_i])===1'bx)$fatal(1,"Missing/unknown sequence reference result");
        for(a3s_i=0;a3s_i<23488;a3s_i=a3s_i+1)
            if((^a3s_input[a3s_i])===1'bx)$fatal(1,"Missing/unknown sequence reference input");
        for(a3s_i=0;a3s_i<25344;a3s_i=a3s_i+1)a3s_seen[a3s_i]=0;
        for(a3s_i=0;a3s_i<12;a3s_i=a3s_i+1)a3s_mail[a3s_i]=0;
        a3s_loads=0;a3s_outputs=0;
        case(a3s_task)
            0:a3s_file=$fopen({a3s_prefix,"__task1.csv"},"w");
            1:a3s_file=$fopen({a3s_prefix,"__task2.csv"},"w");
            2:a3s_file=$fopen({a3s_prefix,"__task3.csv"},"w");
            default:$fatal(1,"Unexpected sequence capture index");
        endcase
        if(a3s_file==0)$fatal(1,"Sequence capture open failed");
    end
endtask
initial begin
    if(!$value$plusargs("DATA_DIR=%s",a3s_first_dir) || !$value$plusargs("SECOND_DIR=%s",a3s_second_dir) ||
       !$value$plusargs("CAPTURE_PREFIX=%s",a3s_prefix))$fatal(1,"Missing sequence input/capture paths");
    a3s_prepare_reference(a3s_first_dir);
end
always @(posedge a3s_clk) if(a3s_rst_n)begin
    if(`A3SEQMEM.expl_axi_icb_rsp_valid && `A3SEQMEM.expl_axi_icb_rsp_ready && `A3SEQMEM.expl_axi_icb_rsp_err)
        $fatal(1,"Sequence accelerator ICB response error");
    if(a3s_phase!=0 && a3s_av && a3s_ar)begin
        if(a3s_aread && a3s_aaddr==32'h40000014)a3s_output_reads=a3s_output_reads+1;
        if(!a3s_aread)begin
            if(a3s_amask!==4'hf)$fatal(1,"Sequence control mask error");
            if(a3s_aaddr==32'h40000004 && a3s_adata==1)a3s_starts=a3s_starts+1;
            if(a3s_aaddr==32'h40000004 && a3s_adata==2)a3s_aborts=a3s_aborts+1;
            if(a3s_aaddr==32'h40000010)a3s_partial_loads=a3s_partial_loads+1;
        end
    end
    if(a3s_cv && a3s_cr && !a3s_read)begin
        if(a3s_addr>=32'ha0000000 && a3s_addr<32'ha000b780)begin
            a3s_index=(a3s_addr-32'ha0000000)>>1;
            if(a3s_mask!==(a3s_addr[1] ? 4'hc : 4'h3))$fatal(1,"Sequence input mask");
            a3s_value=a3s_addr[1] ? a3s_data[31:16] : a3s_data[15:0];
            if(a3s_index!=a3s_loads || a3s_value!==a3s_input[a3s_index])$fatal(1,"Sequence CPU source copy mismatch");
            a3s_loads=a3s_loads+1;
        end
        if(a3s_addr>=32'ha000c000 && a3s_addr<32'ha0018600)begin
            a3s_index=(a3s_addr-32'ha000c000)>>1;
            if(a3s_mask!==(a3s_addr[1] ? 4'hc : 4'h3))$fatal(1,"Sequence output mask");
            a3s_value=a3s_addr[1] ? a3s_data[31:16] : a3s_data[15:0];
            if(a3s_seen[a3s_index] || a3s_value!==a3s_expected[a3s_index])$fatal(1,"Sequence CPU result mismatch");
            a3s_seen[a3s_index]=1;a3s_outputs=a3s_outputs+1;
            $fdisplay(a3s_file,"%0d,%0d",a3s_index,$signed(a3s_value));
        end
        if(a3s_addr>=32'ha001f000 && a3s_addr<32'ha001f030)begin
            if(a3s_mask!==4'hf || a3s_addr[1:0]!=0)$fatal(1,"Sequence mailbox alignment/mask");
            a3s_index=(a3s_addr-32'ha001f000)>>2;a3s_mail[a3s_index]=a3s_data;
            if(a3s_index==8 && a3s_task==2 && (!a3s_poison_verified || !a3s_timeout_verified || a3s_phase!=0))
                $fatal(1,"Recovery task began before abort/timeout evidence");
            if(a3s_index==10)begin
                case(a3s_data)
                    32'h504f4931,32'h54494d31:begin
                        if(a3s_task!=2 || a3s_phase!=0 || a3s_active)$fatal(1,"Recovery phase out of order");
                        if(a3s_data==32'h504f4931 && (a3s_poison_verified || a3s_timeout_verified))$fatal(1,"Duplicate poison phase");
                        if(a3s_data==32'h54494d31 && a3s_timeout_verified)$fatal(1,"Duplicate timeout phase");
                        if(a3s_data==32'h54494d31 && !a3s_poison_verified)$fatal(1,"Timeout before poison recovery");
                        a3s_phase=(a3s_data==32'h504f4931) ? 1 : 2;
                        a3s_starts=0;a3s_aborts=0;a3s_partial_loads=0;a3s_output_reads=0;
                    end
                    32'h504f4932:begin
                        if(a3s_phase!=1 || a3s_starts!=1 || a3s_aborts!=1 || a3s_partial_loads!=17 || a3s_output_reads!=0)
                            $fatal(1,"Poison/abort bus evidence incomplete");
                        a3s_poison_verified=1;a3s_phase=0;
                        $display("ARCH03_SEQUENCE_POISON_PASS starts=1 loads=17 aborts=1 output_reads=0");
                    end
                    32'h54494d32:begin
                        if(a3s_phase!=2 || a3s_starts!=1 || a3s_aborts!=2 || a3s_partial_loads<1 ||
                           a3s_partial_loads>=23488 || a3s_output_reads!=0 || a3s_mail[11]!==32'hffffffff)
                            $fatal(1,"Actual-driver timeout/abort bus evidence incomplete");
                        a3s_timeout_verified=1;a3s_phase=0;
                        $display("ARCH03_SEQUENCE_TIMEOUT_PASS starts=1 loads=%0d aborts=2 rc=-1 output_reads=0",a3s_partial_loads);
                    end
                    default:$fatal(1,"Unknown sequence phase marker");
                endcase
            end
            if(a3s_index==0 && a3s_data!=0)begin
                if(a3s_data!==32'h4b575450 || a3s_mail[1]!==0)$fatal(1,"Sequence firmware failure code=%h",a3s_mail[1]);
                if(a3s_mail[7]!=a3s_task+1 || a3s_loads!=23488 || a3s_outputs!=25344 ||
                   a3s_mail[2]!=23488 || a3s_mail[3]!=25344 || !a3s_finished || a3s_active ||
                   a3s_window.completed_tasks!=a3s_task+1)$fatal(1,"Sequence task/window counts incomplete");
                for(a3s_i=0;a3s_i<25344;a3s_i=a3s_i+1)if(!a3s_seen[a3s_i])$fatal(1,"Missing sequence output");
                $fclose(a3s_file);
`ifdef ARCH03_MONITOR_SELFTEST
                $display("ARCH03_SEQUENCE_OBSERVER_TASK index=%0d outputs=25344 cpu_executed=false",a3s_task+1);
`else
                $display("ARCH03_SOC_SEQUENCE_TASK index=%0d cycles=%0d saturated=%0d outputs=25344",a3s_task+1,{a3s_mail[5],a3s_mail[4]},a3s_mail[6]);
`endif
                a3s_task=a3s_task+1;
                if(a3s_task==3)begin
                    if(!a3s_poison_verified || !a3s_timeout_verified || a3s_phase!=0)$fatal(1,"Missing recovery evidence");
`ifdef ARCH03_MONITOR_SELFTEST
                    $display("ARCH03_SEQUENCE_OBSERVER_SELFTEST_PASS tasks=3 outputs=76032 cpu_executed=false");
`else
                    $display("ARCH03_SOC_SEQUENCE_PASS tasks=3 outputs=76032 cpu_executed=true abort_verified=true timeout_verified=true");
`endif
                    $finish;
                end else a3s_prepare_reference(a3s_task==1 ? a3s_second_dir : a3s_first_dir);
            end
        end
    end
end
initial begin #1000000000;$fatal(1,"Sequence SoC timeout completed_tasks=%0d",a3s_task);end
`undef A3SEQMEM
