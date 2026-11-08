`timescale 1ns/1fs
// Test the OBSERVER using explicitly synthetic traffic. No CPU or arithmetic
// hardware exists in this hierarchy; expected data is stimulus, not a result.
// ARCH03_MONITOR_SELFTEST prevents any real-CPU acceptance marker being emitted.
module tb_arch03_sequence_observer;
    reg clk=0,rst_n=0;
    monitor_soc u_e203_soc_top(.*);
    always #3.333333 clk=~clk;
    `include "arch03_sequence_monitor.svh"
    `define MOCKMEM u_e203_soc_top.u_e203_subsys_top.u_e203_subsys_main.u_e203_subsys_mems
    reg [4095:0] first_dir,second_dir;
    reg [15:0] first_input[0:23487],second_input[0:23487];
    reg [15:0] first_result[0:25343],second_result[0:25343];
    reg [15:0] v;
    integer index,which;
    task store(input [31:0] address,input [31:0] value,input [3:0] mask);
        begin
            @(negedge clk);`MOCKMEM.a3_mem_cmd_valid=1;`MOCKMEM.a3_mem_cmd_ready=1;
            `MOCKMEM.a3_mem_cmd_addr=address;`MOCKMEM.a3_mem_cmd_wdata=value;`MOCKMEM.a3_mem_cmd_wmask=mask;
            @(negedge clk);`MOCKMEM.a3_mem_cmd_valid=0;`MOCKMEM.a3_mem_cmd_ready=0;
            `MOCKMEM.a3_mem_rsp_valid=1;`MOCKMEM.a3_mem_rsp_ready=1;
            @(negedge clk);`MOCKMEM.a3_mem_rsp_valid=0;`MOCKMEM.a3_mem_rsp_ready=0;
        end
    endtask
    task control(input [31:0] offset,input [31:0] value);
        begin
            @(negedge clk);`MOCKMEM.expl_axi_icb_cmd_valid=1;`MOCKMEM.expl_axi_icb_cmd_ready=1;
            `MOCKMEM.expl_axi_icb_cmd_addr=32'h40000000+offset;`MOCKMEM.expl_axi_icb_cmd_wdata=value;
            `MOCKMEM.expl_axi_icb_cmd_wmask=4'hf;
            @(negedge clk);`MOCKMEM.expl_axi_icb_cmd_valid=0;`MOCKMEM.expl_axi_icb_cmd_ready=0;
            `MOCKMEM.expl_axi_icb_rsp_valid=1;`MOCKMEM.expl_axi_icb_rsp_ready=1;
            @(negedge clk);`MOCKMEM.expl_axi_icb_rsp_valid=0;`MOCKMEM.expl_axi_icb_rsp_ready=0;
        end
    endtask
    initial begin
        if(!$value$plusargs("DATA_DIR=%s",first_dir) || !$value$plusargs("SECOND_DIR=%s",second_dir))$fatal(1,"Selftest input paths");
        $readmemh({first_dir,"/load.hex"},first_input);$readmemh({second_dir,"/load.hex"},second_input);
        $readmemh({first_dir,"/result.hex"},first_result);$readmemh({second_dir,"/result.hex"},second_result);
        for(index=0;index<23488;index=index+1)
            if((^{first_input[index],second_input[index]})===1'bx)$fatal(1,"Missing/unknown selftest input");
        for(index=0;index<25344;index=index+1)
            if((^{first_result[index],second_result[index]})===1'bx)$fatal(1,"Missing/unknown selftest result");
        repeat(3) @(negedge clk);rst_n=1;
        for(which=0;which<3;which=which+1)begin
            if(which==2)begin
                store(32'ha001f028,32'h504f4931,4'hf);control(12,31);control(4,1);
                for(index=0;index<17;index=index+1)control(16,index);
                if(!$test$plusargs("NEGATIVE_MISSING_ABORT"))control(4,2);
                store(32'ha001f028,32'h504f4932,4'hf);
                if(!$test$plusargs("NEGATIVE_SKIP_TIMEOUT"))begin
                    store(32'ha001f028,32'h54494d31,4'hf);control(4,2);control(12,12);control(4,1);
                    control(16,1);control(4,2);store(32'ha001f02c,32'hffffffff,4'hf);
                    store(32'ha001f028,32'h54494d32,4'hf);
                end
            end
            store(32'ha001f000,0,4'hf);store(32'ha001f020,32'h4b575442,4'hf);
            for(index=0;index<23488;index=index+1)begin
                v=which==1 ? second_input[index] : first_input[index];
                store(32'ha0000000+2*index,index[0] ? {v,16'b0} : {16'b0,v},index[0] ? 4'hc : 4'h3);
            end
            for(index=0;index<25344;index=index+1)begin
                v=which==1 ? second_result[index] : first_result[index];
                store(32'ha000c000+2*index,index[0] ? {v,16'b0} : {16'b0,v},index[0] ? 4'hc : 4'h3);
                if(index==0 && $test$plusargs("NEGATIVE_REPEAT_OUTPUT"))store(32'ha000c000,{16'b0,v},4'h3);
            end
            store(32'ha001f004,0,4'hf);store(32'ha001f008,23488,4'hf);store(32'ha001f00c,25344,4'hf);
            store(32'ha001f010,2000000,4'hf);store(32'ha001f014,0,4'hf);store(32'ha001f018,0,4'hf);
            store(32'ha001f01c,which+1,4'hf);store(32'ha001f000,32'h4b575450,4'hf);
        end
        $fatal(1,"Observer failed to finish after three tasks");
    end
    `undef MOCKMEM
endmodule
