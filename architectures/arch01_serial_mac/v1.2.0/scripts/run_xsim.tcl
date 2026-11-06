log_wave -r /tb_dot64/dut/*
log_wave /tb_dot64/test_case /tb_dot64/active_case
source [file join [file dirname [info script]] waves.tcl]
save_wave_config dot64.wcfg
run all
quit
