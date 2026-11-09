"""Collect whole-SoC mapped netlist, strict-clock reports and area inventory.

This stage produces REVIEWABLE REPORTS, never automatic timing/area acceptance.
Clock mode and I/O budgets are explicit assumptions. Cross-clock paths remain
analyzed except four reviewed first-stage timer synchronizer input pins.
Official scoring treatment of the shared SRAM remains unresolved.
"""
import json
import math
import re
import shutil
from pathlib import Path
from asic_link import link_soc,sha
from dc_blocks import measured_metrics
from timing_contract import CLOCK_PERIOD_NS,validate_period


def output_constraints():
    return r'''
# Pinned-platform AON control outputs are launched by lf_clk, not hf_clk.
# This is a 1 ns interface budget in their source domain, not an external
# receiver specification. Keep every output timed; do not false-path them.
set lf_outputs [get_ports -quiet __arch03_no_such_port__]
foreach name {io_pads_aon_pmu_padrst_o_oval io_pads_aon_pmu_vddpaden_o_oval lfxoscen} {
    set port [get_ports $name]
    if {[sizeof_collection $port] != 1} {error "Missing/ambiguous LF control output $name"}
    set lf_outputs [add_to_collection $lf_outputs $port]
}
if {[sizeof_collection $lf_outputs] != 3} {error "Expected three LF control outputs"}
set hf_outputs [remove_from_collection [all_outputs] $lf_outputs]
set_output_delay -max 1.0 -clock hf_clk $hf_outputs
set_output_delay -min 0.0 -clock hf_clk $hf_outputs
set_output_delay -max 1.0 -clock lf_clk $lf_outputs
set_output_delay -min 0.0 -clock lf_clk $lf_outputs
puts "ARCH03_LF_OUTPUT_BUDGET [get_object_name $lf_outputs]"
'''


def constraints():
    return r'''
# Measured-task mode of the pinned platform; not all software/JTAG modes.
# hfextclk drives the bypassed PLL path. LF period is the original TB's 66 ns.
# I/O budgets (1 ns max, 0 ns min, 0.1 ns transition, 0.01 load) are assumptions.
create_clock -name hf_clk -period @PERIOD@ [get_ports hfextclk]
create_clock -name lf_clk -period 66.0 [get_ports lfextclk]
set_clock_uncertainty 0.1 [all_clocks]
foreach {name value} {
    io_pads_aon_erst_n_i_ival 1
    io_pads_aon_pmu_dwakeup_n_i_ival 1
    io_pads_bootrom_n_i_ival 0
    io_pads_dbgmode0_n_i_ival 1
    io_pads_dbgmode1_n_i_ival 1
    io_pads_dbgmode2_n_i_ival 1
    io_pads_jtag_TCK_i_ival 0
    io_pads_jtag_TMS_i_ival 0
    io_pads_jtag_TDI_i_ival 0
} {
    set port [get_ports $name]
    if {[sizeof_collection $port] != 1} {error "Missing task-mode port $name"}
    set_case_analysis $value $port
}
# Both registers reset to one (sirv_gnrl_dfflrs); firmware does not change them.
foreach control {pllbypass plloutdivby1} {
    set pin [get_pins -hierarchical -filter "full_name =~ */u_e203_subsys_hclkgen/$control"]
    if {[sizeof_collection $pin] != 1} {error "Missing/ambiguous clock mode pin $control"}
    set_case_analysis 1 $pin
}
# Fixed active-low boot strap, deglitched for four LF edges before the task.
# The complete-task observer requires this exact output to remain one.
# Startup and strap changes are outside this steady-state task mode.
set bootrom [get_pins -hierarchical -filter "full_name =~ */u_sirv_aon_wrapper/bootrom_deglitch/io_q"]
if {[sizeof_collection $bootrom] != 1} {error "Missing/ambiguous bootrom task-mode pin"}
set_case_analysis 1 $bootrom
set ins [remove_from_collection [all_inputs] [get_ports {hfextclk lfextclk}]]
set_input_delay -max 1.0 -clock hf_clk $ins
set_input_delay -min 0.0 -clock hf_clk $ins
set_input_transition 0.1 $ins
@OUTPUT_CONSTRAINTS@
set_load 0.01 [all_outputs]
# No blanket clock groups or forced TCM/core clock-enable values.
# Four first-stage timer CDC pins are constrained after mapping below.
# Reset assertion is outside this task mode;
# reset release/synchronizers must be reviewed separately.
'''.replace('@PERIOD@',CLOCK_PERIOD_NS).replace('@OUTPUT_CONSTRAINTS@',output_constraints())


def mapped_exceptions():
    return r'''
# The pinned APB timer input_stage.v has a 3-FF LF clock synchronizer.
# Stage 0 drives only stage 1; edge detection uses stages 1 and 2.
# Exempt only external LF -> stage-0 D, preserving all downstream timing.
# Exact mapped endpoints and count are mandatory; no asynchronous groups.
set sync0 [get_pins -quiet __arch03_no_such_pin__]
set sync_names {}
foreach_in_collection pin [get_pins -hierarchical -filter "full_name =~ */u_in_stage/*/D"] {
    set name [get_object_name $pin]
    if {[regexp {/u_perips_apb_pwm/u_tim([0-3])/u_in_stage/r_ls_clk_sync_reg\[0\]/D$} $name]} {
        set sync0 [add_to_collection $sync0 $pin]
        lappend sync_names $name
    }
}
if {[sizeof_collection $sync0] != 4 || [llength [lsort -unique $sync_names]] != 4} {
    error "Expected four reviewed LF timer first-stage synchronizer D pins"
}
set_false_path -from [get_ports lfextclk] -to $sync0
puts "ARCH03_REVIEWED_CDC_ENDPOINTS $sync_names"
'''


def script(run,cfg):
    standard=run/'libs'/Path(cfg['standard_library_member']).name
    databases=sorted(p for p in (run/'libs').glob('*.db') if p!=standard)
    if len(databases)!=2:raise ValueError('Expected two compiled SRAM databases')
    text=r'''
proc arch03_collect_reports {} {
global target_library
# DC source honors this process setting; its default/startup value may allow
# subsequent lines after a failed guard. A bad SDC must abort before compile.
set_app_var sh_continue_on_error false
set_app_var target_library [list @STANDARD@]
set_app_var link_library [concat [list *] $target_library [list @DATABASES@]]
read_ddc linked.ddc
current_design e203_soc_top
if {![link]} {error "Mapped-flow whole-SoC link failed"}
set memories [get_cells -hierarchical -filter "ref_name == RAMSP128X16 || ref_name == RAMSP4096X16"]
if {[sizeof_collection $memories] != 138} {error "Initial SRAM inventory mismatch"}
set_dont_touch $memories true
source task_mode.sdc
set_fix_multiple_port_nets -all -buffer_constants
compile -map_effort high
@EXCEPTIONS@
set_fix_hold [all_clocks]
compile -incremental_mapping -map_effort high
redirect check_design_mapped.rpt {check_design}
redirect check_timing.rpt {check_timing}
redirect area.rpt {report_area -hierarchy}
redirect references_mapped.rpt {report_reference -hierarchy}
redirect constraints.rpt {report_constraint -all_violators}
redirect timing_max.rpt {report_timing -delay_type max -max_paths 100 -significant_digits 8}
redirect timing_min.rpt {report_timing -delay_type min -max_paths 100 -significant_digits 8}
redirect qor.rpt {report_qor}
write -format verilog -hierarchy -output mapped.v
write -format ddc -hierarchy -output mapped.ddc
write_sdc mapped.sdc
set out [open metrics.txt w]
puts $out "period_ns [format %.12f [get_attribute [get_clocks hf_clk] period]]"
puts $out "lf_period_ns [format %.12f [get_attribute [get_clocks lf_clk] period]]"
foreach kind {RAMSP128X16 RAMSP4096X16} {
    puts $out "$kind [sizeof_collection [get_cells -hierarchical -filter "ref_name == $kind"]]"
}
foreach delay {max min} {
    set paths [get_timing_paths -delay_type $delay -max_paths 1]
    # DC returns up to max_paths PER GROUP; a complete SoC has multiple groups.
    if {[sizeof_collection $paths] < 1} {error "Missing constrained whole-SoC timing path"}
    set worst {}
    foreach_in_collection path $paths {
        set slack [get_attribute $path slack]
        if {$worst eq {} || $slack < $worst} {set worst $slack}
    }
    puts $out "$delay $worst"
    puts $out "${delay}_path_groups [sizeof_collection $paths]"
}
puts $out "latches [sizeof_collection [all_registers -level_sensitive]]"
close $out
# Library area is counted exactly once for each mapped LEAF instance.
set out [open leaf_area.tsv w]
foreach_in_collection cell [get_cells -hierarchical -filter "is_hierarchical == false"] {
    set reference [get_attribute $cell ref_name]
    # DC logical constant sources are virtual nodes, not physical tie cells.
    # Only these exact built-ins have zero area; all other leaves need a library.
    if {$reference eq "**logic_0**" || $reference eq "**logic_1**"} {
        puts $out "[get_object_name $cell]\t$reference\t0\tbuiltin_logic_constant"
        continue
    }
    set libcell [get_lib_cells */$reference]
    if {[sizeof_collection $libcell] != 1} {error "Unmapped/ambiguous leaf $reference"}
    puts $out "[get_object_name $cell]\t$reference\t[get_attribute $libcell area]\t[get_object_name $libcell]"
}
close $out
set out [open latch_inventory.txt w]
foreach_in_collection cell [all_registers -level_sensitive] {puts $out [get_object_name $cell]}
close $out
puts "ARCH03_SOC_SYNTH_REPORTS_READY timing_verified=false scoring_area_verified=false"
}
if {[catch {arch03_collect_reports} message]} {
    puts stderr "Error: ARCH03_SYNTH_ABORT $message"
    exit 1
}
quit
'''
    for key,value in {'STANDARD':'{%s}'%standard,'DATABASES':' '.join('{%s}'%p for p in databases),
                      'EXCEPTIONS':mapped_exceptions()}.items():
        text=text.replace('@'+key+'@',value)
    return text


def owner(name):
    if 'u_e203_itcm_gnrl_ram/' in name:return 'itcm'
    if 'u_e203_dtcm_gnrl_ram/' in name:return 'dtcm'
    if 'u_arch03_shared/' in name:return 'shared'
    if 'u_arch03_accel/' in name:return 'accelerator'
    return 'platform_other'


def area_inventory(text,reported_total):
    rows=[];seen=set();groups={}
    for line in text.splitlines():
        fields=line.split('\t')
        if len(fields)!=4:raise ValueError('Malformed leaf area row')
        name,reference,value,library=fields
        if not name or name in seen:raise ValueError('Duplicate/missing leaf instance')
        seen.add(name);area=float(value)
        if reference in ('**logic_0**','**logic_1**'):
            if area!=0 or library!='builtin_logic_constant':
                raise ValueError('Invalid virtual constant area/source')
            kind='virtual_constant'
        else:
            if not math.isfinite(area) or area<=0 or library=='builtin_logic_constant':
                raise ValueError('Missing/invalid leaf library area')
            kind='sram' if reference in ('RAMSP128X16','RAMSP4096X16') else 'standard_cell'
        category=owner(name)
        group=groups.setdefault(category,dict(standard_cell_area=0.,sram_area=0.,standard_cell_count=0,sram_count=0,
                                             virtual_constant_area=0.,virtual_constant_count=0))
        group[kind+'_area']+=area;group[kind+'_count']+=1
        rows.append(dict(instance=name,reference=reference,library=library,area=area,owner=category,kind=kind))
    expected={('itcm','RAMSP4096X16'):32,('dtcm','RAMSP4096X16'):32,
              ('shared','RAMSP4096X16'):64,('accelerator','RAMSP4096X16'):2,('accelerator','RAMSP128X16'):8}
    actual={}
    for row in rows:
        if row['kind']=='sram':
            key=(row['owner'],row['reference']);actual[key]=actual.get(key,0)+1
    if actual!=expected:raise ValueError('Mapped SRAM ownership/count mismatch')
    total=sum(row['area'] for row in rows)
    if not math.isfinite(float(reported_total)) or abs(total-float(reported_total))>max(1.,total*1e-5):
        raise ValueError('Leaf area sum disagrees with whole-SoC report')
    return dict(whole_system_library_area=total,reported_total=float(reported_total),groups=groups,
                leaf_count=len(rows),physical_sram_bytes=1042*1024,
                virtual_constant_note='DC built-in logical sources have zero synthesis area; no physical tie-cell insertion or area is claimed',
                units='library area units; physical unit basis requires review',
                official_scoring_area=None,scoring_area_verified=False,
                shared_memory_treatment='unresolved; no exemption or inclusion assumed',
                rows=rows)


def require_tool_marker(text,marker):
    # DC echoes proc definitions. Only the emitted whole line is completion,
    # not the marker literal appearing inside a Tcl puts command.
    if sum(line.strip()==marker for line in text.splitlines())!=1:
        raise ValueError('Whole-SoC report collection incomplete')
    if re.search(r'(?im)^\s*(Error-|Fatal:|Error:)',text):
        raise ValueError('Tool errors prevent report collection')


def synth(cfg,run,platform_source,team_sources,call):
    linked=link_soc(cfg,run,platform_source,team_sources,call)
    (run/'task_mode.sdc').write_text(constraints())
    tcl=run/'soc_synth.tcl';tcl.write_text(script(run,cfg))
    before=json.loads((run/'source_inputs.json').read_text())
    before[str(run/'linked.ddc')]=sha(run/'linked.ddc')
    before[str(run/'task_mode.sdc')]=sha(run/'task_mode.sdc')
    before[str(tcl)]=sha(tcl)
    text=call([cfg['tools']['dc_shell'],'-f',tcl],run,'soc_synth.log')
    return collect_reports(run,linked,before,text)


def collect_reports(run,linked,before,text):
    marker='ARCH03_SOC_SYNTH_REPORTS_READY timing_verified=false scoring_area_verified=false'
    require_tool_marker(text,marker)
    metrics=measured_metrics((run/'metrics.txt').read_text(),(run/'area.rpt').read_text())
    validate_period(metrics['period_ns'])
    if float(metrics['lf_period_ns'])!=66.0:raise ValueError('Unexpected LF mode clock')
    if int(metrics['RAMSP128X16'])!=8 or int(metrics['RAMSP4096X16'])!=130:raise ValueError('Mapped SRAM count changed')
    area=area_inventory((run/'leaf_area.tsv').read_text(),metrics['area'])
    (run/'area_inventory.json').write_text(json.dumps(area,indent=2)+'\n')
    for name in ('mapped.v','mapped.ddc','mapped.sdc','check_timing.rpt','constraints.rpt','timing_max.rpt','timing_min.rpt'):
        if not (run/name).is_file() or not (run/name).stat().st_size:raise ValueError('Missing synthesis artifact '+name)
    for path,digest in before.items():
        if sha(Path(path))!=digest:raise ValueError('Whole-SoC synthesis input changed')
    return dict(status='reports_ready_review_required',scope='whole_soc_task_mode_preliminary_synthesis',
                synthesis_completed=True,timing_verified=False,scoring_area_verified=False,
                setup_hold_nonnegative=min(float(metrics['max']),float(metrics['min']))>=0,
                metrics=metrics,area_summary={k:v for k,v in area.items() if k!='rows'},
                required_reviews=['clock propagation and gated-clock coverage','all check_timing and structural warnings',
                                  'unconstrained paths and LF/HF crossings, including four explicit timer CDC pins',
                                  'reset/clock/boot strap mode and I/O assumptions',
                                  'library area units and official shared SRAM treatment','post-synthesis functionality'],
                gate_simulation_verified=False,system_power_verified=False,physical_signoff=False,
                link_report=linked,artifacts={p.name:sha(p) for p in run.iterdir() if p.is_file()})


def recover_reports(cfg,run,origin,current_bundle):
    """Re-audit a marker-only failed run in a NEW directory; never edit it."""
    origin=origin.resolve();origin.relative_to(Path(cfg['server_root']).resolve())
    state=json.loads((origin.parent/'state.json').read_text())['stages']['asic_synth']
    if state.get('status')!='failed' or state.get('error')!='Whole-SoC report collection incomplete':
        raise ValueError('Only the known completion-marker parser failure can be recovered')
    text=(origin/'soc_synth.log').read_text()
    require_tool_marker(text,'ARCH03_SOC_SYNTH_REPORTS_READY timing_verified=false scoring_area_verified=false')
    require_tool_marker((origin/'dc_link.log').read_text(),'ARCH03_ASIC_LINK_READY whole_soc=true synthesis_verified=false timing_verified=false')
    source_bundle=origin.parents[2]
    manifest=json.loads((source_bundle/'manifest.json').read_text())
    for name,digest in manifest['files'].items():
        if sha(source_bundle/name)!=digest:raise ValueError('Original synthesis bundle changed')
    before=json.loads((origin/'source_inputs.json').read_text())
    for name,digest in before.items():
        path=Path(name)
        if sha(path)!=digest:raise ValueError('Original synthesis input changed')
        try:relative=path.relative_to(source_bundle)
        except ValueError:continue
        if relative.parts[0]=='workspaces' and sha(current_bundle/relative)!=digest:
            raise ValueError('Current synthesis RTL differs from original')
    # Installer and technology selection are not in the tool's source file list.
    preparation=['workspaces/arch03/scripts/'+name for name in
                 ('install_platform.py','technology_binding.py','memory_technology.py','timing_contract.py')]
    preparation+=['workspaces/arch03/'+name for name in ('technology_bindings.json','memory_technology.json')]
    relevant=('workspaces/arch02/rtl/','workspaces/arch02/arch02/rtl/',
              'workspaces/arch03/rtl/','workspaces/arch03/sw/')
    current_manifest=json.loads((current_bundle/'manifest.json').read_text())
    old={p:h for p,h in manifest['files'].items() if p.startswith(relevant)}
    new={p:h for p,h in current_manifest['files'].items() if p.startswith(relevant)}
    if old!=new:raise ValueError('Current runtime source inventory differs from original')
    for relative in preparation+list(old):
        if relative not in manifest['files'] or sha(current_bundle/relative)!=manifest['files'][relative]:
            raise ValueError('Current synthesis preparation differs: '+relative)
    if (origin/'task_mode.sdc').read_text()!=constraints():raise ValueError('Task constraints differ')
    original_files={p.name:sha(p) for p in origin.iterdir() if p.is_file()}
    for name in original_files:
        if name=='summary.json':raise ValueError('Refusing to replace an existing synthesis summary')
        shutil.copy2(str(origin/name),str(run/name))
    (run/'libs').mkdir()
    databases=list((origin/'libs').glob('*.db'))
    if len(databases)!=3:raise ValueError('Incomplete original synthesis library databases')
    for source in databases:shutil.copy2(str(source),str(run/'libs'/source.name))
    origin_receipt=dict(origin=str(origin),source_commit=manifest['source_commit'],
                        original_state=state,original_artifacts=original_files,
                        synthesis_reexecuted=False,reason='Completion marker echoed in Tcl proc definition was counted twice')
    (run/'report_recovery.json').write_text(json.dumps(origin_receipt,indent=2)+'\n')
    linked=dict(status='linked',scope='original_whole_soc_link_and_mapping_preserved',report_recovery=origin_receipt)
    result=collect_reports(run,linked,before,text)
    for name,digest in original_files.items():
        if sha(origin/name)!=digest:raise ValueError('Original report changed during re-audit')
    result['report_recovery']=origin_receipt
    return result
