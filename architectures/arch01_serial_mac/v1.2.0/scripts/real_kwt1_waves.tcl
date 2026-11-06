if {[llength [get_wave_configs]] == 0} { create_wave_config }
add_wave /tb_single_hex/dut/clk /tb_single_hex/dut/rst_n
add_wave /tb_single_hex/dut/start_valid /tb_single_hex/dut/start_ready /tb_single_hex/dut/busy
add_wave /tb_single_hex/dut/in_valid /tb_single_hex/dut/in_ready
add_wave -radix dec /tb_single_hex/dut/x /tb_single_hex/dut/w /tb_single_hex/dut/product
add_wave -radix unsigned /tb_single_hex/dut/state /tb_single_hex/dut/accepted_count /tb_single_hex/dut/shift_reg
add_wave -radix dec /tb_single_hex/dut/accumulator /tb_single_hex/dut/bias_reg /tb_single_hex/dut/sum_with_bias
add_wave /tb_single_hex/dut/out_valid /tb_single_hex/dut/out_ready
add_wave -radix dec /tb_single_hex/dut/result
add_wave /tb_single_hex/dut/saturated
