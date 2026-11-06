# Source after opening dot64.wdb or launching behavioral simulation.
if {[llength [get_wave_configs]] == 0} { create_wave_config }
add_wave /tb_dot64/test_case /tb_dot64/active_case
add_wave /tb_dot64/dut/clk /tb_dot64/dut/rst_n
add_wave /tb_dot64/dut/start_valid /tb_dot64/dut/start_ready /tb_dot64/dut/busy
add_wave /tb_dot64/dut/in_valid /tb_dot64/dut/in_ready
add_wave -radix dec /tb_dot64/dut/x /tb_dot64/dut/w
add_wave -radix unsigned /tb_dot64/dut/state /tb_dot64/dut/accepted_count
add_wave -radix dec /tb_dot64/dut/product /tb_dot64/dut/accumulator
add_wave -radix dec /tb_dot64/dut/bias_reg /tb_dot64/dut/sum_with_bias
add_wave -radix unsigned /tb_dot64/dut/shift_reg
add_wave /tb_dot64/dut/out_valid /tb_dot64/dut/out_ready
add_wave -radix dec /tb_dot64/dut/result
add_wave /tb_dot64/dut/saturated
