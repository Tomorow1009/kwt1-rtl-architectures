"""Own-netlist PT clock-gating setup/hold and static test-enable checks.

Uses the installed report_clock_gating_check and timing paths ending at the
actual enable pins. Does not disable checks, add exceptions or remap cells.
"""
from pathlib import Path
import re
from partition_synth_contract import require,digest
from server_run import save
from soc_power import power_databases,power_invocation,tcl_path
from soc_synth import require_tool_marker
from g32_power import precise_clock
from g32_validation import verify_synthesis
from g32_paths import allowed_run

MARKER='G32_CLOCK_GATING_TIMING_READY netlist_modified=false'


def script(synthesis,precise_sdc):
    libraries=power_databases(synthesis)
    text=r'''
proc g32_gating_audit {} {
    set_app_var link_path [list * @LIBS@]
    read_verilog @NETLIST@
    current_design e203_soc_top
    if {![link_design]} {error "G32 clock-gating link failed"}
    read_sdc @SDC@
    if {abs([get_attribute [get_clocks hf_clk] period]-6.666666)>1e-12} {error "Wrong G32 clock"}
    update_timing
    set cells [get_cells -hierarchical -filter "ref_name == CLKLANAQV4_12TR40 && full_name =~ */u_arch03_accel/*"]
    if {[sizeof_collection $cells] == 0} {error "Missing actual accelerator clock gates"}
    redirect clock_gating_checks.rpt {report_clock_gating_check -nosplit $cells}
    redirect timing_check.rpt {check_timing -verbose}
    redirect clocks.rpt {report_clock}
    redirect constraints.rpt {report_constraint -all_violators}
    set out [open clock_gating_paths.tsv w]
    puts $out "schema\tg32-clock-gating-paths-v1"
    foreach_in_collection cell $cells {
        set name [get_object_name $cell]
        set e [get_pins -of_objects $cell -filter "name == E"]
        set te [get_pins -of_objects $cell -filter "name == TE"]
        if {[sizeof_collection $e]!=1 || [sizeof_collection $te]!=1} {error "ICG enable pin mismatch"}
        set constant [get_attribute $te constant_value]
        if {$constant ne "0"} {error "G32 production test enable must be static zero: $name"}
        puts $out "test_enable\t$name\t$constant"
        foreach delay {max min} {
            set paths [get_timing_paths -to $e -delay_type $delay -max_paths 1]
            if {[sizeof_collection $paths]!=1} {error "Missing actual enable timing path $delay $name"}
            foreach_in_collection path $paths {
                set endpoint [get_object_name [get_attribute $path endpoint]]
                if {$endpoint ne [get_object_name $e]} {error "Clock-gating endpoint differs"}
                puts $out "path\t$name\t$delay\t[get_attribute $path slack]\t$endpoint"
            }
        }
    }
    puts $out "count\t[sizeof_collection $cells]"
    close $out
    set enables [get_pins -of_objects $cells -filter "name == E"]
    redirect clock_gating_setup.rpt {report_timing -to $enables -delay_type max -max_paths 1000 -significant_digits 10 -nosplit}
    redirect clock_gating_hold.rpt {report_timing -to $enables -delay_type min -max_paths 1000 -significant_digits 10 -nosplit}
    puts "@MARKER@"
}
if {[catch {g32_gating_audit} message]} {
    puts stderr "Error: G32_CLOCK_GATING_ABORT $message"
    exit 1
}
quit
'''
    return text.replace('@LIBS@',' '.join(tcl_path(p) for p in libraries)).replace(
        '@NETLIST@',tcl_path(synthesis/'mapped.v')).replace('@SDC@',tcl_path(precise_sdc)).replace('@MARKER@',MARKER)


def parse(text,mapping):
    lines=text.splitlines();require(lines and lines[0]=='schema\tg32-clock-gating-paths-v1','Wrong gating path schema')
    rows={};count=None
    for line in lines[1:]:
        f=line.split('\t')
        if f[0]=='test_enable':
            require(len(f)==3 and f[1] not in rows and f[2]=='0','Nonstatic/duplicate production TE')
            rows[f[1]]={}
        elif f[0]=='path':
            require(len(f)==5 and f[1] in rows and f[2] in ('max','min') and f[2] not in rows[f[1]],'Invalid enable timing row')
            require(re.fullmatch(r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?',f[3]) and f[4]==f[1]+'/E','Missing numeric slack or enable endpoint')
            rows[f[1]][f[2]]=float(f[3])
        elif f[0]=='count':
            require(len(f)==2 and count is None and f[1].isdigit(),'Invalid gating count');count=int(f[1])
        else:raise ValueError('Unknown gating timing row')
    require(count==len(rows)==mapping['actual_g32_cells'] and set(rows)==set(mapping['rows']),
            'Timing checks do not cover exactly the mapped accelerator ICGs')
    require(all(set(v)=={'max','min'} for v in rows.values()),'Incomplete setup/hold per ICG')
    setup=min(v['max'] for v in rows.values());hold=min(v['min'] for v in rows.values())
    return dict(actual_g32_cells=count,static_TE_zero=True,setup_slack_ns=setup,hold_slack_ns=hold,
        enable_path_setup_hold_nonnegative=setup>=0 and hold>=0,rows=rows)


def audit(cfg,run,synthesis,expected,call):
    run=allowed_run(run,cfg,'G32 clock-gating output');synthesis=allowed_run(synthesis,cfg,'G32 synthesis')
    report,_=verify_synthesis(synthesis,expected,cfg)
    sdc,clock=precise_clock(synthesis,run)
    tcl=run/'g32_clock_gating.tcl';tcl.write_text(script(synthesis,sdc))
    command,environment=power_invocation(cfg,tcl);save(run/'tool_environment.json',environment)
    tracked=[tcl,sdc,run/'tool_environment.json',synthesis/'mapped.v',synthesis/'summary.json',Path(__file__)]+power_databases(synthesis)
    before={str(p):digest(p) for p in tracked};save(run/'source_inputs.json',before)
    log=call(command,run,'clock_gating.log');require_tool_marker(log,MARKER)
    result=parse((run/'clock_gating_paths.tsv').read_text(),report['icg_mapping'])
    # Keep native reports, including the explicit gating-check designation.
    for name in ('clock_gating_checks.rpt','clock_gating_setup.rpt','clock_gating_hold.rpt'):
        require((run/name).is_file() and (run/name).stat().st_size,'Missing native clock-gating report')
    require(all(digest(Path(p))==h for p,h in before.items()),'G32 gating input changed')
    verify_synthesis(synthesis,expected,cfg)
    result.update(schema='g32-clock-gating-timing-v1',synthesis_run=str(synthesis),
        synthesis_summary_sha256=expected,netlist_sha256=report['artifacts']['mapped.v'],
        clock=clock,netlist_modified=False,checks_disabled=False,physical_signoff=False,
        native_report_review_required=True,energy_verified=False,
        artifacts={p.name:digest(p) for p in run.iterdir() if p.is_file()})
    return result
