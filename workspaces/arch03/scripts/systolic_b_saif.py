"""Capture complete B task windows only after the frozen R4 SAIF cross-check.

The existing B mapped gate run remains read-only. Compile once with extra
visibility, replay each frozen command, and independently check outputs/time.
No VCD or cross-task preloading is introduced.
"""
import json
import math
import re
import shutil
from pathlib import Path
from server_run import sha,save
from icb32_power import stream_sha,window_values
from native_saif_replay import capture_commands,verify_inputs
from native_saif_activity import audit
from systolic_b_gate import verify_synthesis,SCOPE
from systolic_b_soc import MARKERS
import systolic_b_data as data

LAYERS=tuple('layer_%02d'%i for i in range(1,13))


def read(path):return json.loads(Path(path).read_text())


def qualification(path,digest,cfg):
    path=Path(path).resolve();path.relative_to(Path(cfg['server_root']).resolve())
    if sha(path/'summary.json')!=digest:raise ValueError('SAIF qualification digest mismatch')
    report=read(path/'summary.json')
    state=read(path.parent/'state.json')['stages']['native_saif_r4_crosscheck']
    if (state.get('status')!='passed' or state.get('summary_sha256')!=digest or
        report.get('status')!='R4_SAIF_VCD_method_crosscheck_passed' or
        report.get('activity_method_qualified') is not True or
        report.get('comparison',{}).get('passed') is not True):
        raise ValueError('R4 native-SAIF method has not passed its real <=1% cross-check')
    verify_inputs({str(path/name):value for name,value in report['artifacts'].items()})
    return report


def storage_guard(run,remaining,maximum_bytes):
    free=shutil.disk_usage(str(run)).free
    required=math.ceil(remaining*maximum_bytes*1.2)+2*1024**3
    receipt=dict(free_bytes=free,required_bytes=required,remaining_cases=remaining,
        maximum_case_bytes=maximum_bytes,margin=1.2,reserve_bytes=2*1024**3)
    save(Path(run)/'storage_budget.json',receipt)
    if free<required:raise ValueError('Insufficient native-SAIF storage; preserve completed evidence')
    return receipt


def verify(cfg,run,gate,gate_sha,qualified,qualified_sha,cases,call):
    run,gate=Path(run),Path(gate).resolve();gate.relative_to(Path(cfg['server_root']).resolve())
    if not cases or len(cases)!=len(set(cases)) or not set(cases)<=set(LAYERS):
        raise ValueError('B SAIF needs distinct performance layer cases')
    method=qualification(qualified,qualified_sha,cfg)
    if sha(gate/'summary.json')!=gate_sha:raise ValueError('B gate digest mismatch')
    report=read(gate/'summary.json');state=read(gate.parent/'state.json')['stages']['systolic_b_gate']
    if (state.get('status')!='passed' or state.get('summary_sha256')!=gate_sha or
        report.get('scope')!=SCOPE or report.get('gate_simulation_verified') is not True or
        report.get('cpu_executed') is not True or report.get('sdf_annotated') is not False):
        raise ValueError('Require B own actual mapped gate pass')
    rows={r['case']:r for r in report['cases']}
    if set(rows)!=set(data.CASES14) or len(report['cases'])!=14:raise ValueError('B gate14 incomplete')
    synthesis=Path(report['synthesis_run'])
    verify_synthesis(synthesis,report['synthesis_summary_sha256'],cfg)
    if sha(gate/'source_inputs.json')!=report['source_inputs_sha256']:raise ValueError('B gate input receipt changed')
    before=read(gate/'source_inputs.json');verify_inputs(before)
    # Pilot size is measured from R4, with a 2x allowance for the larger B
    # design. Re-estimate from actual B files after every completed capture.
    maximum=max(2*method['activity']['bytes'],128*1024**2)
    storage_guard(run,len(cases),maximum)
    compile_command,_,_=capture_commands(gate,run,rows[cases[0]])
    if compile_command[0]!=cfg['tools']['vcs']:raise ValueError('VCS executable changed')
    save(run/'compile_command.json',compile_command)
    log=call(compile_command,run,'compile.log')
    if re.search(r'Warning-\[(?:IPDW|PCWM-W|INAV|SIOB)\]',log):raise ValueError('B SAIF compile width/declaration mismatch')
    results=[]
    for case in cases:
        row=rows[case];window_values(row['task_window'])
        _,runtime,ucli=capture_commands(gate,run,row)
        script=run/(case+'_capture.tcl');script.write_text(ucli)
        runtime[-1]=str(script)
        save(run/(case+'_command.json'),runtime)
        log=call(runtime,run,case+'.log')
        capture=data.check_capture(run/(case+'.csv'),gate/(case+'_data'))
        markers=MARKERS+['ARCH03_ICB32_SOURCE_READY words=%d scope=PC_file_only no_ITCM_task_data=true'%
                        (row['task_window']['encoded_bytes']//4)]
        result=data.parse_result(log,capture['saturated'],markers)
        window=data.read_window(log,result,row['task_window']['encoded_bytes'])
        if (window!=row['task_window'] or capture!=row['capture'] or result!=row['result'] or
            stream_sha(run/(case+'.csv'))!=stream_sha(gate/(case+'.csv'))):
            raise ValueError('B native replay changed outputs or full-task window')
        irq=re.findall(r'^ARCH03_ICB32_IRQ_PROOF enabled=(\d+) external=(\d+) timer=(\d+) wfi=(\d+) events=(\d+) unhandled=(\d+)$',log,re.M)
        cpu=re.findall(r'^ARCH03_ICB32_CPU_CYCLES (\d+)$',log,re.M)
        expected=row['irq_proof']
        if (len(irq)!=1 or len(cpu)!=1 or int(cpu[0])!=row['cpu_cycles'] or
            tuple(map(int,irq[0]))!=tuple(int(expected[k]) for k in ('enabled','external','timer','wfi','events','unhandled'))):
            raise ValueError('B native replay IRQ/WFI proof differs')
        activity=audit(run/(case+'.saif'),window)
        evidence=dict(case=case,outputs=25344,task_window=window,activity=activity,
            integer_capture_sha256=stream_sha(run/(case+'.csv')),layout_sha256=row['layout_sha256'],
            codec_sha256=row['codec_sha256'],irq_proof=expected,cpu_cycles=row['cpu_cycles'],
            result=result,capture=capture)
        results.append(evidence);save(run/'case_progress.json',results)
        maximum=max(sum(p.stat().st_size for p in run.glob(case+'*') if p.is_file()),
                    max(r['activity']['bytes'] for r in results))
        storage_guard(run,len(cases)-len(results),maximum)
        print('B_NATIVE_SAIF_CASE_PASS',case,'bytes',activity['bytes'],flush=True)
    verify_inputs(before);qualification(qualified,qualified_sha,cfg)
    verify_synthesis(synthesis,report['synthesis_summary_sha256'],cfg)
    return dict(status='B_native_saif_function_and_complete_windows_passed',cases=results,
        gate_run=str(gate),gate_summary_sha256=gate_sha,
        qualification_run=str(qualified),qualification_summary_sha256=qualified_sha,
        synthesis_run=str(synthesis),synthesis_summary_sha256=report['synthesis_summary_sha256'],
        firmware_sha256=report['firmware_sha256'],source_inputs_sha256=report['source_inputs_sha256'],
        source_netlist_unchanged=True,debug_visibility_only=True,new_VCD_created=False,
        system_power_verified=False,physical_signoff=False,
        artifacts={p.name:stream_sha(p) for p in run.iterdir() if p.is_file()})
