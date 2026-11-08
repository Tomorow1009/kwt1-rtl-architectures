import os
from pathlib import Path
import json,tarfile,shutil,hashlib,subprocess,datetime,re
root=Path.cwd(); run=root/'dc_runs'/('synth_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
run.mkdir(); libs=run/'libs';libs.mkdir()
cfg=json.loads((root/'server_config.json').read_text())
archive=cfg['process_archive']
member=cfg['standard_library_member']
chosen={member:libs/Path(member).name,member[:-3]+'.lib':libs/(Path(member).stem+'.lib')}
print('SYNTH_RUN',run,flush=True)
with tarfile.open(archive,'r|gz') as tf:
 for m in tf:
  if m.name in chosen:
   if not m.isfile():raise RuntimeError('Not a regular library')
   with tf.extractfile(m) as src, chosen[m.name].open('wb') as dst:shutil.copyfileobj(src,dst)
   print('EXTRACTED',m.name,flush=True)
   if all(p.exists() for p in chosen.values()):break
std=next(p for p in chosen.values() if p.suffix=='.db')
stdlib=next(p for p in chosen.values() if p.suffix=='.lib')
if not all(p.exists() for p in chosen.values()):raise RuntimeError('Missing extracted library')
macros=[];lc=[]
for size in (128,4096):
 p=Path(cfg['sram_root'])/('RAMSP%dX16/lib/RAMSP%dX16_ss_0p99v_0p99v_125c.lib'%(size,size))
 text=p.read_text(); name=re.search(r'library\s*\(\s*"?([^\s")]+)',text).group(1)
 db=libs/(name+'.db');macros.append((p,db))
 lc.extend(['read_lib {%s}'%p,'write_lib {%s} -format db -output {%s}'%(name,db)])
lc.append('quit');(run/'compile_libs.tcl').write_text('\n'.join(lc)+'\n')
def tool(exe,script,log):
 path=shutil.which(exe)
 if not path:raise RuntimeError(exe+' unavailable')
 with log.open('w') as f:rc=subprocess.call([path,'-f',str(script)],cwd=str(run),stdout=f,stderr=subprocess.STDOUT)
 text=log.read_text(errors='replace')
 print(exe,'exit',rc,'log',log,flush=True)
 print('\n'.join(text.splitlines()[-35:]),flush=True)
 if rc or re.search(r'(?m)^Error:',text):raise RuntimeError('Tool failed '+str(log))
tool('lc_shell',run/'compile_libs.tcl',run/'lc.log')
if not all(p.exists() for _,p in macros):raise RuntimeError('Missing compiled SRAM database')
previous=Path(os.environ['HANDOFF_VCS_RUN'])
shutil.copy2(str(previous/'arch02_sram_config.vh'),str(run/'arch02_sram_config.vh'))
sources=[root/p for p in ['rtl/dot64.sv','rtl/requantize.sv','arch02/rtl/sram_macro_adapter.sv','arch02/rtl/sram_port.sv','arch02/rtl/arch02_linear.sv']]
hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources+[stdlib,std]+[p for pair in macros for p in pair]}
(run/'inputs.json').write_text(json.dumps({'hashes':hashes,'corner':'RVT SS 0.99V 125C; matching SRAM SS 0.99V 125C','clock_ns':6.667,'interface_assumptions':{'input_max_ns':1.0,'input_min_ns':0.0,'output_max_ns':1.0,'output_min_ns':0.0,'uncertainty_ns':0.1,'input_transition_ns':0.1,'output_load_pf':0.01},'physical_signoff':False},indent=2))
tcl='''set_app_var search_path [concat [list {RUN}] $search_path]
set_app_var target_library [list {STD}]
set_app_var link_library [concat [list *] $target_library [list MACROS]]
define_design_lib WORK -path ./work
analyze -format sverilog -define SYNTHESIS [list SOURCES]
elaborate arch02_linear
current_design arch02_linear
if {![link]} {error "Unresolved design references"}
uniquify
set memories [get_cells -hierarchical -filter "ref_name == RAMSP128X16 || ref_name == RAMSP4096X16"]
if {[sizeof_collection $memories] != 10} {error "Expected ten SRAM macros"}
set_dont_touch $memories true
create_clock -name core_clk -period 6.667 [get_ports clk]
set_clock_uncertainty 0.1 [get_clocks core_clk]
set ins [remove_from_collection [all_inputs] [get_ports {clk rst_n}]]
set_input_delay -max 1.0 -clock core_clk $ins
set_input_delay -min 0.0 -clock core_clk $ins
set_input_transition 0.1 $ins
set_output_delay -max 1.0 -clock core_clk [all_outputs]
set_output_delay -min 0.0 -clock core_clk [all_outputs]
set_load 0.01 [all_outputs]
# Reset release must be synchronized by integration; excluded from data timing here.
set_false_path -from [get_ports rst_n]
set_fix_multiple_port_nets -all -buffer_constants
redirect pre_check.rpt {check_design}
compile -map_effort high
redirect check_design.rpt {check_design}
redirect check_timing.rpt {check_timing}
redirect area.rpt {report_area -hierarchy}
redirect references.rpt {report_reference -hierarchy}
redirect timing_max.rpt {report_timing -delay_type max -max_paths 20 -nets -transition_time -capacitance}
redirect timing_min.rpt {report_timing -delay_type min -max_paths 20 -nets -transition_time -capacitance}
redirect constraints.rpt {report_constraint -all_violators}
redirect qor.rpt {report_qor}
redirect libraries.rpt {list_libs}
write -format verilog -hierarchy -output arch02_mapped.v
write -format ddc -hierarchy -output arch02_mapped.ddc
write_sdc arch02.sdc
puts "DC_SYNTHESIS_FINISHED"
report_area
report_timing -delay_type max -max_paths 1
report_timing -delay_type min -max_paths 1
quit
'''
tcl=tcl.replace('RUN',str(run)).replace('STD',str(std)).replace('MACROS',' '.join('{%s}'%p for _,p in macros)).replace('SOURCES',' '.join('{%s}'%p for p in sources))
(run/'synth.tcl').write_text(tcl)
tool('dc_shell',run/'synth.tcl',run/'dc.log')
if 'DC_SYNTHESIS_FINISHED' not in (run/'dc.log').read_text(errors='replace'):raise RuntimeError('No synthesis completion marker')
for p,h in hashes.items():
 if hashlib.sha256(Path(p).read_bytes()).hexdigest()!=h:raise RuntimeError('Input changed '+p)
print('SYNTHESIS_REPORTS_READY',run,flush=True)
for name in ['qor.rpt','constraints.rpt','check_design.rpt','check_timing.rpt']:
 print('REPORT',name,flush=True);print((run/name).read_text(errors='replace')[-10000:],flush=True)
