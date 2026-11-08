`timescale 1ns/1fs
// Compile/elaboration harness ONLY. No E203, SRAM, computation or CPU acceptance.
// Provides just the observed hierarchy/ports to catch monitor binding mistakes
// locally while the licensed complete platform remains on the server.
module monitor_mems(input wire clk,rst_n);
    reg a3_mem_cmd_valid=0,a3_mem_cmd_ready=0,a3_mem_cmd_read=0;
    reg [31:0] a3_mem_cmd_addr=0,a3_mem_cmd_wdata=0;
    reg [3:0] a3_mem_cmd_wmask=0;
    reg a3_mem_rsp_valid=0,a3_mem_rsp_ready=0,a3_mem_rsp_err=0;
    reg expl_axi_icb_cmd_valid=0,expl_axi_icb_cmd_ready=0,expl_axi_icb_cmd_read=0;
    reg [31:0] expl_axi_icb_cmd_addr=0,expl_axi_icb_cmd_wdata=0;
    reg [3:0] expl_axi_icb_cmd_wmask=0;
    reg expl_axi_icb_rsp_valid=0,expl_axi_icb_rsp_ready=0,expl_axi_icb_rsp_err=0;
endmodule
module tb_sequence_compile;
    reg clk=0,rst_n=0;
    monitor_soc u_e203_soc_top(.*);
    `include "arch03_sequence_monitor.svh"
endmodule
module monitor_main(input wire clk,rst_n);
    monitor_mems u_e203_subsys_mems(.*);
endmodule
module monitor_subsys(input wire clk,rst_n);
    monitor_main u_e203_subsys_main(.*);
endmodule
module monitor_soc(input wire clk,rst_n);
    monitor_subsys u_e203_subsys_top(.*);
endmodule
module tb_top;
    reg clk=0,rst_n=0;
    monitor_soc u_e203_soc_top(.*);
    `include "arch03_monitor.svh"
endmodule
