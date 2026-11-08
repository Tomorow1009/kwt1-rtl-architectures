"""DC checks for the new accelerator interface and shared SRAM (NOT whole SoC)."""
import hashlib,json,re,shutil,tarfile
from pathlib import Path
def synth(cfg,run,top,sources,call):
    libs=run/'libs';libs.mkdir()
    member=cfg['standard_library_member'];std=libs/Path(member).name
    with tarfile.open(cfg['process_archive'],'r|gz') as tf:
        for entry in tf:
            if entry.name==member:
                if not entry.isfile():raise ValueError('Invalid standard library member')
                with tf.extractfile(entry) as src,std.open('wb') as dst:shutil.copyfileobj(src,dst)
                break
    if not std.is_file():raise ValueError('Standard cell DB not found')
    databases=[];commands=[];library_inputs=[std]
    for size in (128,4096):
        lib=Path(cfg['sram_root'])/('RAMSP%dX16/lib/RAMSP%dX16_ss_0p99v_0p99v_125c.lib'%(size,size))
        name=re.search(r'library\s*\(\s*"?([^\s")]+)',lib.read_text()).group(1)
        db=libs/(name+'.db');databases.append(db);library_inputs.append(lib)
        commands+=['read_lib {%s}'%lib,'write_lib {%s} -format db -output {%s}'%(name,db)]
    (run/'libs.tcl').write_text('\n'.join(commands+['quit'])+'\n')
    call([cfg['tools']['lc_shell'],'-f',run/'libs.tcl'],run,'lc.log')
    if not all(p.is_file() for p in databases):raise ValueError('SRAM library compilation incomplete')
    before={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in library_inputs+databases+sources}
    expect128,expect4096=(8,2) if top=='arch03_icb_accel' else (0,64)
    script=r'''
set_app_var search_path [concat [list @RUN@] $search_path]
set_app_var target_library [list @STD@]
set_app_var link_library [concat [list *] $target_library [list @DBS@]]
define_design_lib WORK -path ./work
analyze -format sverilog -define SYNTHESIS [list @SOURCES@]
elaborate @TOP@
current_design @TOP@
if {![link]} {error "Unresolved references"}
uniquify
set memories [get_cells -hierarchical -filter "ref_name == RAMSP128X16 || ref_name == RAMSP4096X16"]
set_dont_touch $memories true
create_clock -name core_clk -period 6.667 [get_ports clk]
set_clock_uncertainty 0.1 [get_clocks core_clk]
set ins [remove_from_collection [all_inputs] [get_ports clk]]
set_input_delay -max 1.0 -clock core_clk $ins
set_input_delay -min 0.0 -clock core_clk $ins
set_input_transition 0.1 $ins
set_output_delay -max 1.0 -clock core_clk [all_outputs]
set_output_delay -min 0.0 -clock core_clk [all_outputs]
set_load 0.01 [all_outputs]
# Async reset assertion, synchronous release required from the platform reset synchronizer.
# This is the ONLY path exception; it is recorded in the exported SDC.
set_false_path -from [get_ports rst_n]
set_fix_multiple_port_nets -all -buffer_constants
compile -map_effort high
set_fix_hold [all_clocks]
compile -incremental_mapping -map_effort high
redirect check_design.rpt {check_design}
redirect check_timing.rpt {check_timing}
redirect area.rpt {report_area -hierarchy}
redirect references.rpt {report_reference -hierarchy}
redirect constraints.rpt {report_constraint -all_violators}
redirect timing_max.rpt {report_timing -delay_type max -max_paths 20 -significant_digits 8}
redirect timing_min.rpt {report_timing -delay_type min -max_paths 20 -significant_digits 8}
redirect qor.rpt {report_qor}
write -format verilog -hierarchy -output mapped.v
write -format ddc -hierarchy -output mapped.ddc
write_sdc mapped.sdc
set out [open metrics.txt w]
foreach kind {RAMSP128X16 RAMSP4096X16} {
  puts $out "$kind [sizeof_collection [get_cells -hierarchical -filter "ref_name == $kind"]]"
}
foreach delay {max min} {
  set paths [get_timing_paths -delay_type $delay -max_paths 1]
  if {[sizeof_collection $paths] != 1} {error "Missing constrained timing path"}
  foreach_in_collection path $paths {puts $out "$delay [get_attribute $path slack]"}
}
puts $out "area [get_attribute [current_design] area]"
puts $out "latches [sizeof_collection [all_registers -level_sensitive]]"
close $out
puts "ARCH03_DC_REPORTS_READY"
quit
'''
    for key,value in {'RUN':'{%s}'%run,'STD':'{%s}'%std,'DBS':' '.join('{%s}'%p for p in databases),
                      'SOURCES':' '.join('{%s}'%p for p in sources),'TOP':top}.items():script=script.replace('@'+key+'@',value)
    (run/'synth.tcl').write_text(script)
    text=call([cfg['tools']['dc_shell'],'-f',run/'synth.tcl'],run,'dc.log')
    if 'ARCH03_DC_REPORTS_READY' not in text:raise ValueError('Missing DC completion')
    metrics=dict(line.split() for line in (run/'metrics.txt').read_text().splitlines())
    if int(metrics['RAMSP128X16'])!=expect128 or int(metrics['RAMSP4096X16'])!=expect4096:
        raise ValueError('Wrong mapped SRAM count '+str(metrics))
    if min(float(metrics['max']),float(metrics['min']))<0:raise ValueError('Timing violation '+str(metrics))
    if int(metrics['latches'])!=0:raise ValueError('Unexpected inferred latches')
    if top=='arch03_icb_accel' and float(metrics['area'])>2250000:raise ValueError('Accelerator area exceeds 2.25 mm2')
    for path,digest in before.items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest()!=digest:raise ValueError('DC input changed '+path)
    # Warnings need review, never silently grant timing/structural acceptance.
    for name in ('check_design.rpt','check_timing.rpt'):
        if re.search(r'(?im)^\s*(Warning:|Error:)',(run/name).read_text()):
            raise ValueError('Review required: '+name)
    return dict(status='passed',top=top,metrics=metrics,clock_ns=6.667,physical_signoff=False,
                scope='block_only_not_whole_soc',gate_simulation_verified=False,
                artifacts={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in run.iterdir() if p.is_file()},
                library_inputs={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in library_inputs+databases})
