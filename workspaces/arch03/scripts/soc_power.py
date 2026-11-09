"""Collect reviewable full-task mapped-SoC PrimeTime PX power reports.

This is pre-layout estimation, not power acceptance. Unannotated activity,
unknown values, macro models, wire/clock capacitance and report units must be
reviewed. No missing contribution is silently replaced by zero.
"""
import json
import re
from decimal import Decimal
from pathlib import Path
from gate_soc import verify_synthesis
from soc_synth import require_tool_marker
from server_run import ROOT,sha,save

PT_SHELL='/eda/synopsys/prime/prime_2022.03-SP5-1/bin/pt_shell'


def power_databases(synthesis):
    databases=sorted((synthesis/'libs').glob('*.db'))
    if len(databases)!=3:raise ValueError('Power requires one standard and two SRAM databases')
    expected={}
    for path,digest in json.loads((synthesis/'source_inputs.json').read_text()).items():
        name=Path(path)
        if name.suffix!='.db':continue
        if name.name in expected and expected[name.name]!=digest:
            raise ValueError('Conflicting synthesis database provenance')
        expected[name.name]=digest
    if set(expected)!={p.name for p in databases}:
        raise ValueError('Active power databases lack complete synthesis provenance')
    for path in databases:
        if sha(path)!=expected[path.name]:raise ValueError('Active power database changed: '+path.name)
    return databases


def power_invocation(cfg,tcl):
    # PrimeTime emits PT-063 before its banner when this installation root is
    # absent. Set it only for the child process, from the pinned LC executable.
    compiler=Path(cfg['tools']['lc_shell'])
    if not compiler.is_absolute() or compiler.name!='lc_shell' or compiler.parent.name!='bin' or not compiler.is_file():
        raise ValueError('Invalid pinned Library Compiler executable')
    environment={'SYNOPSYS_LC_ROOT':str(compiler.parent.parent)}
    command=['/usr/bin/env','SYNOPSYS_LC_ROOT='+environment['SYNOPSYS_LC_ROOT'],PT_SHELL,'-f',tcl]
    return command,dict(environment=environment,lc_shell=str(compiler),lc_launcher_sha256=sha(compiler))


def window_values(window):
    start=Decimal(str(window['start_ns']));end=Decimal(str(window['end_ns']))
    period=Decimal(str(window['period_ns']));cycles=int(window['cycles'])
    if not all(x.is_finite() for x in (start,end,period)) or not 0<=start<end or period<=0 or cycles<=0:
        raise ValueError('Invalid power task interval')
    if abs(end-start-period*cycles)>Decimal('0.000002'):
        raise ValueError('Power task duration disagrees with cycles')
    # Installed PrimeTime 2022.03 read_vcd manual explicitly defines -time in ns,
    # independently of the VCD timescale. Never pass raw femtosecond ticks here.
    return str(start),str(end),str(end-start)


def tcl_path(path):
    value=str(path)
    if re.search(r'[{}\r\n]',value):raise ValueError('Unsafe Tcl path')
    return '{'+value+'}'


def script(cfg,synthesis,vcd,window):
    start,end,_=window_values(window)
    databases=power_databases(synthesis)
    text=r'''
proc arch03_power_reports {} {
    set_app_var power_enable_analysis true
    set_app_var power_analysis_mode averaged
    set_app_var link_path [list * @LIBS@]
    read_verilog @NETLIST@
    current_design e203_soc_top
    if {![link_design]} {error "Whole-SoC power link failed"}
    read_sdc @SDC@
    set memories [get_cells -hierarchical -filter "ref_name == RAMSP128X16 || ref_name == RAMSP4096X16"]
    if {[sizeof_collection $memories] != 138} {error "Power SRAM count mismatch"}
    redirect units.rpt {report_units}
    redirect timing_check.rpt {check_timing}
    redirect clocks.rpt {report_clock}
    # Functional gate simulation without SDF: explicitly invoke zero-delay
    # interpretation. Wire/clock network estimation remains a review item.
    read_vcd -zero_delay -strip_path tb_top/u_e203_soc_top -time {@START@ @END@} @VCD@
    redirect activity_coverage_before.rpt {report_switching_activity -coverage -hierarchy}
    redirect activity_unannotated_before.rpt {report_switching_activity -list_not_annotated -show_pin}
    update_power
    redirect power.rpt {report_power -nosplit -significant_digits 8}
    redirect power_hierarchy.rpt {report_power -hierarchy -levels 30 -nosplit -significant_digits 8}
    redirect power_sram.rpt {report_power -cell_power -nosplit -significant_digits 8 $memories}
    redirect activity_coverage_after.rpt {report_switching_activity -coverage -hierarchy}
    redirect activity_unannotated_after.rpt {report_switching_activity -list_not_annotated -show_pin}
    redirect activity_sources.rpt {report_switching_activity -hierarchy -include_mapping_types}
    puts "ARCH03_SYSTEM_POWER_REPORTS_READY system_power_verified=false"
}
if {[catch {arch03_power_reports} message]} {
    puts stderr "Error: ARCH03_POWER_ABORT $message"
    exit 1
}
quit
'''
    values={'LIBS':' '.join(tcl_path(p) for p in databases),'NETLIST':tcl_path(synthesis/'mapped.v'),
            'SDC':tcl_path(synthesis/'mapped.sdc'),'VCD':tcl_path(vcd),'START':start,'END':end}
    for k,v in values.items():text=text.replace('@'+k+'@',v)
    return text


def gate_activity(gate,expected_sha,case,cfg):
    gate=gate.resolve();gate.relative_to(Path(cfg['server_root']).resolve())
    summary_path=gate/'summary.json'
    if not re.fullmatch('[a-f0-9]{64}',expected_sha) or sha(summary_path)!=expected_sha:
        raise ValueError('Gate summary digest mismatch')
    report=json.loads(summary_path.read_text())
    state=json.loads((gate.parent/'state.json').read_text())['stages']['gate_soc']
    if state['status']!='passed' or state['summary_sha256']!=expected_sha or not report.get('gate_simulation_verified'):
        raise ValueError('Gate functional stage not passed')
    if report.get('scope')!='whole_soc_mapped_functional_without_SDF':raise ValueError('Unsupported gate activity scope')
    rows=[r for r in report['cases'] if r['case']==case]
    if len(rows)!=1:raise ValueError('Missing/duplicate gate activity case')
    row=rows[0];activity=row.get('activity',{})
    if activity.get('status')!='scope_and_window_verified':raise ValueError('Gate case has no audited full-window VCD')
    start,end,duration=window_values(row['task_window'])
    if any(abs(Decimal(a)-Decimal(b))>Decimal('0.000002') for a,b in
           ((start,activity['start_ns']),(end,activity['end_ns']))):raise ValueError('Gate activity interval mismatch')
    filename=activity['file']
    if Path(filename).name!=filename or not filename.endswith('.vcd'):raise ValueError('Unsafe gate activity filename')
    vcd=gate/filename
    # Stream the large activity file; do not load gigabytes into memory.
    import hashlib
    h=hashlib.sha256()
    with vcd.open('rb') as stream:
        for chunk in iter(lambda:stream.read(4*1024*1024),b''):h.update(chunk)
    if h.hexdigest()!=activity['sha256'] or vcd.stat().st_size!=activity['bytes']:
        raise ValueError('Gate activity changed')
    for name,digest in json.loads((gate/'source_inputs.json').read_text()).items():
        if sha(Path(name))!=digest:raise ValueError('Gate simulation input changed')
    synthesis=Path(report['synthesis_run'])
    verify_synthesis(synthesis,report['synthesis_summary_sha256'],cfg)
    return report,row,vcd,synthesis,duration


def estimate(cfg,run,gate,expected_sha,case,call):
    if not Path(PT_SHELL).is_file():raise ValueError('Pinned PrimeTime executable missing')
    report,row,vcd,synthesis,duration=gate_activity(gate,expected_sha,case,cfg)
    tcl=run/'soc_power.tcl';tcl.write_text(script(cfg,synthesis,vcd,row['task_window']))
    command,environment=power_invocation(cfg,tcl)
    environment_file=run/'power_environment.json';save(environment_file,environment)
    tracked=[tcl,environment_file,synthesis/'mapped.v',synthesis/'mapped.sdc',synthesis/'summary.json',gate/'summary.json']
    tracked+=power_databases(synthesis)
    before={str(p):sha(p) for p in tracked}
    save(run/'source_inputs.json',before)
    text=call(command,run,'power.log')
    require_tool_marker(text,'ARCH03_SYSTEM_POWER_REPORTS_READY system_power_verified=false')
    required=('units.rpt','power.rpt','power_hierarchy.rpt','power_sram.rpt','activity_coverage_after.rpt',
              'activity_unannotated_after.rpt','activity_sources.rpt','timing_check.rpt','clocks.rpt')
    for name in required:
        if not (run/name).is_file() or not (run/name).stat().st_size:raise ValueError('Missing power artifact '+name)
    for name,digest in before.items():
        if sha(Path(name))!=digest:raise ValueError('Power input changed')
    gate_activity(gate,expected_sha,case,cfg)
    return dict(status='reports_ready_review_required',scope='whole_soc_gate_activity_pre_layout_power',
                system_power_verified=False,timing_verified=False,physical_signoff=False,
                gate_run=str(gate),gate_summary_sha256=expected_sha,case=case,
                synthesis_run=str(synthesis),synthesis_summary_sha256=report['synthesis_summary_sha256'],
                task_window=row['task_window'],duration_ns=duration,activity=row['activity'],
                tool=PT_SHELL,tool_environment=environment,analysis='averaged; zero-delay gate activity; no extracted parasitics',
                required_reviews=['license/tool run and library units','SRAM internal and conditional leakage power',
                                  'all unmapped and unannotated objects, including unknown activity',
                                  'wire/load and clock network capacitance assumptions','six-component coverage and report sums',
                                  'power unit conversion and energy over this exact full-task window'],
                artifacts={p.name:sha(p) for p in run.iterdir() if p.is_file()})
