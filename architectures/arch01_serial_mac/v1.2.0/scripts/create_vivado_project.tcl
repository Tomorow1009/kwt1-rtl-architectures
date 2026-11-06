# From the Vivado Tcl Console: source D:/IC_compeyition/Fast_coding/scripts/create_vivado_project.tcl
set root [file normalize [file join [file dirname [info script]] ..]]
set project_dir [file join $root sim vivado_project]
# A simulation-only project needs a device selection, but no board or hardware.
if {[llength [get_projects -quiet]] != 0} { error "Close the current project before sourcing this script." }
if {[file exists [file join $project_dir dot64_demo.xpr]]} {
    open_project [file join $project_dir dot64_demo.xpr]
} else {
    create_project dot64_demo $project_dir -part xc7a35tcpg236-1
}
foreach source [list [file join $root rtl requantize.sv] [file join $root rtl dot64.sv]] {
    if {[llength [get_files -quiet $source]] == 0} { add_files $source }
}
set_property top dot64 [get_filesets sources_1]
if {[llength [get_files -quiet [file join $root tb tb_dot64.sv]]] == 0} {
    add_files -fileset sim_1 [file join $root tb tb_dot64.sv]
}
set_property top tb_dot64 [get_filesets sim_1]
set_property include_dirs [list [file join $root vectors]] [get_filesets sim_1]
set_property -dict [list xsim.simulate.xsim.more_options "-testplusarg DATA_DIR=$root/vectors"] [get_filesets sim_1]
set_property xsim.simulate.runtime 0ns [get_filesets sim_1]
update_compile_order -fileset sources_1
update_compile_order -fileset sim_1
launch_simulation
log_wave -r /tb_dot64/dut/*
log_wave /tb_dot64/test_case /tb_dot64/active_case
source [file join $root scripts waves.tcl]
save_wave_config [file join $project_dir dot64.wcfg]
run all
