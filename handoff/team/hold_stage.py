import os
from pathlib import Path
import datetime,json,hashlib,subprocess,shutil,re
root=Path.cwd();base=Path(os.environ['HANDOFF_SYNTH_RUN'])
run=root/'dc_runs'/('hold_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'));run.mkdir()
std=base/'libs/scc40nll_vhsc40_rvt_ss_v0p99_125c_basic.db'
dbs=[base/('libs/RAMSP%dX16_ss_0p99v_0p99v_125c.db'%s) for s in (128,4096)]
ddc=base/'arch02_mapped.ddc'
for p in [std,ddc]+dbs:
 if not p.is_file():raise RuntimeError('Missing '+str(p))
(run/'inputs.json').write_text(json.dumps({'parent':str(base),'purpose':'incremental hold repair, same slow corner and interface assumptions','hashes':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [std,ddc]+dbs}},indent=2))
tcl='''set_app_var target_library [list {STD}]
set_app_var link_library [concat [list *] $target_library [list MACROS]]
read_ddc {DDC}
current_design arch02_linear
if {![link]} {error "Link failed"}
set_fix_hold [all_clocks]
compile -incremental_mapping -map_effort high
redirect area.rpt {report_area -hierarchy}
redirect qor.rpt {report_qor}
redirect constraints.rpt {report_constraint -all_violators}
redirect timing_max.rpt {report_timing -delay_type max -max_paths 20 -significant_digits 6}
redirect timing_min.rpt {report_timing -delay_type min -max_paths 20 -significant_digits 6}
redirect check_design.rpt {check_design}
redirect check_timing.rpt {check_timing}
redirect references.rpt {report_reference -hierarchy}
write -format verilog -hierarchy -output arch02_mapped.v
write -format ddc -hierarchy -output arch02_mapped.ddc
write_sdc arch02.sdc
set summary [open summary.txt w]
foreach type {RAMSP128X16 RAMSP4096X16} {
 set cells [get_cells -hierarchical -filter "ref_name == $type"]
 puts $summary "$type count=[sizeof_collection $cells]"
 foreach_in_collection c $cells {puts $summary "  [get_object_name $c] area=[get_attribute $c area]"}
}
foreach delay {max min} {
 set paths [get_timing_paths -delay_type $delay -max_paths 1]
 foreach_in_collection path $paths {
  puts $summary "$delay slack=[get_attribute $path slack] start=[get_object_name [get_attribute $path startpoint]] end=[get_object_name [get_attribute $path endpoint]]"
 }
}
close $summary
puts "HOLD_REPAIR_FINISHED"
quit
'''.replace('STD',str(std)).replace('MACROS',' '.join('{%s}'%p for p in dbs)).replace('DDC',str(ddc))
(run/'hold.tcl').write_text(tcl)
print('HOLD_RUN',run,flush=True)
with (run/'dc.log').open('w') as f:rc=subprocess.call([shutil.which('dc_shell'),'-f',str(run/'hold.tcl')],cwd=str(run),stdout=f,stderr=subprocess.STDOUT)
text=(run/'dc.log').read_text(errors='replace')
print('DC_EXIT',rc,flush=True)
if rc or re.search(r'(?m)^Error:',text) or 'HOLD_REPAIR_FINISHED' not in text:
 print('\n'.join(text.splitlines()[-80:]),flush=True);raise SystemExit(1)
print((run/'qor.rpt').read_text(),flush=True)
print((run/'summary.txt').read_text(),flush=True)
print('HOLD_REPORTS_READY',run,flush=True)
