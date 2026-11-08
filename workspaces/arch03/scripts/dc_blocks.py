"""DC checks for the new accelerator interface and shared SRAM (NOT whole SoC)."""
import hashlib,json,math,re,shutil,tarfile
from pathlib import Path

def review_design(text):
    """Accept only the arithmetic optimization warnings inspected on the server.

    The original core has unused carry/sign pins and sign-extension wiring in
    generated DesignWare operators. New wrapper/memory/interface warnings fail.
    Keep every warning in the report and bind the review to its SHA256.
    """
    counts={}
    for line in text.splitlines():
        if line.lstrip().startswith('Error:'):raise ValueError('DC structural error: '+line)
        if not line.lstrip().startswith('Warning:'):continue
        code=re.search(r'\((LINT-\d+)\)\s*$',line)
        fields=re.findall("'([^']+)'",line)
        if code is None or len(fields)<2:raise ValueError('Unreviewed DC warning: '+line)
        code=code.group(1);design,obj=fields[:2]
        arithmetic=bool(re.fullmatch(r'(?:dot64|requantize)(?:_\w+)*',design))
        operator=bool(re.fullmatch(r'(?:FS|add|mult|sll|srl|sub)_\d+',obj))
        ok=(code=='LINT-2' and design=='arch03_icb_accel' and
            re.fullmatch(r'core/lanes\[[0-7]\]\.mac/(?:add_\d+|quantizer/sub_\d+)/[AB]\[\d+\]',obj))
        ok=ok or (code=='LINT-8' and arithmetic and '_DW' in design and re.fullmatch(r'[AB]\[\d+\]',obj))
        ok=ok or (code=='LINT-28' and arithmetic and '_DW' in design and
                  (obj in ('CI','CO','TC','DATA_TC','SH_TC') or re.fullmatch(r'[AB]\[\d+\]',obj)))
        ok=ok or (code in ('LINT-32','LINT-33') and arithmetic and operator)
        # Shared SRAM selects a 32-bit word with addr[18:2]; byte lanes come
        # from wmask and load extraction is performed by the E203 LSU.
        ok=ok or (code=='LINT-28' and design=='arch03_shared_sram' and obj in ('cmd_addr[0]','cmd_addr[1]'))
        if not ok:raise ValueError('Unreviewed DC warning: '+line)
        counts[code]=counts.get(code,0)+1
    return counts

def measured_metrics(metrics_text,area_text):
    metrics={}
    for line in metrics_text.splitlines():
        values=line.split()
        if len(values)!=2 or values[0] in metrics:raise ValueError('Malformed/duplicate DC metric: '+line)
        metrics[values[0]]=values[1]
    area=re.findall(r'(?m)^Total cell area:\s*([0-9.eE+-]+)\s*$',area_text)
    if len(area)!=1:raise ValueError('Missing or ambiguous measured total cell area')
    metrics['area']=area[0]
    if any(not math.isfinite(float(metrics[k])) for k in ('max','min','area')):
        raise ValueError('Non-finite DC metrics')
    if float(metrics['area'])<=0:raise ValueError('Non-positive DC area')
    return metrics
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
# DC T-2022.03 does not expose an area attribute on the design object.
# Python reads the measured Total cell area from report_area instead.
puts $out "latches [sizeof_collection [all_registers -level_sensitive]]"
close $out
set hf_out [open high_fanout.txt w]
foreach_in_collection net [all_high_fanout -nets -threshold 1000] {
  puts $hf_out [get_object_name $net]
}
close $hf_out
puts "ARCH03_DC_REPORTS_READY"
quit
'''
    for key,value in {'RUN':'{%s}'%run,'STD':'{%s}'%std,'DBS':' '.join('{%s}'%p for p in databases),
                      'SOURCES':' '.join('{%s}'%p for p in sources),'TOP':top}.items():script=script.replace('@'+key+'@',value)
    (run/'synth.tcl').write_text(script)
    text=call([cfg['tools']['dc_shell'],'-f',run/'synth.tcl'],run,'dc.log')
    if 'ARCH03_DC_REPORTS_READY' not in text:raise ValueError('Missing DC completion')
    metrics=measured_metrics((run/'metrics.txt').read_text(),(run/'area.rpt').read_text())
    if int(metrics['RAMSP128X16'])!=expect128 or int(metrics['RAMSP4096X16'])!=expect4096:
        raise ValueError('Wrong mapped SRAM count '+str(metrics))
    if min(float(metrics['max']),float(metrics['min']))<0:raise ValueError('Timing violation '+str(metrics))
    if int(metrics['latches'])!=0:raise ValueError('Unexpected inferred latches')
    if top=='arch03_icb_accel' and float(metrics['area'])>2250000:raise ValueError('Accelerator area exceeds 2.25 mm2')
    for path,digest in before.items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest()!=digest:raise ValueError('DC input changed '+path)
    reviewed=review_design((run/'check_design.rpt').read_text())
    # The only reviewed timing warning is this block's ideal clock fanout.
    # Check actual mapped nets every run: a high-fanout data/reset net still fails.
    high_fanout=set((run/'high_fanout.txt').read_text().splitlines())
    timing_review=[]
    for line in (run/'check_timing.rpt').read_text().splitlines():
        if not re.match(r'\s*(Warning:|Error:)',line):continue
        expected="Warning: Design '%s' contains 1 high-fanout nets."%top
        if line.startswith(expected) and line.endswith('(TIM-134)') and high_fanout=={'clk'}:
            timing_review.append(dict(code='TIM-134',nets=['clk'],reason='Ideal clock; clock tree implementation remains outside block synthesis'))
        else:raise ValueError('Unreviewed DC timing warning: '+line)
    return dict(status='passed',top=top,metrics=metrics,clock_ns=6.667,physical_signoff=False,
                scope='block_only_not_whole_soc',gate_simulation_verified=False,reviewed_structural_warnings=reviewed,
                reviewed_timing_warnings=timing_review,high_fanout_nets=sorted(high_fanout),
                artifacts={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in run.iterdir() if p.is_file()},
                library_inputs={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in library_inputs+databases})
