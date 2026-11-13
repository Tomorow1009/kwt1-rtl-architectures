"""Replay frozen R4 L01 into native SAIF without creating another VCD.

Only debug visibility/output locations change. Original mapped HDL, firmware,
source, timing and integer expectations stay pinned. The old run is read-only.
This first entry is restricted to the required R4 cross-check, not B power.
"""
import json
import re
import shutil
from decimal import Decimal
from pathlib import Path
from server_run import sha,save
from icb32_activity import audit_header
from icb32_power import stream_sha,window_values
from icb32_soc import MARKERS
import icb32_data as data
from native_saif_activity import audit


def read(path):return json.loads(Path(path).read_text())


def verify_inputs(receipts):
    for name,digest in receipts.items():
        if stream_sha(Path(name))!=digest:raise ValueError('Frozen activity input changed: '+name)


def capture_commands(gate,run,row,window_reader=window_values):
    gate,run=Path(gate),Path(run);case=row['case']
    original=read(gate/'compile_command.json')
    if (original.count('-o')!=1 or original.count('-top')!=1 or
        original[original.index('-o')+1]!=str(gate/'simv') or
        original[original.index('-top')+1]!='tb_top' or
        any('SDF' in item.upper() or 'DEFINE+FPGA' in item.upper() for item in original)):
        raise ValueError('Unreviewed frozen gate compile command')
    compile_command=list(original);compile_command[compile_command.index('-o')+1]=str(run/'simv')
    if '-debug_access+all' not in compile_command:compile_command.insert(1,'-debug_access+all')
    original_run=read(gate/(case+'_command.json'))
    if original_run[0]!=str(gate/'simv') or sum(x.startswith('+CAPTURE=') for x in original_run)!=1:
        raise ValueError('Wrong frozen runtime command')
    runtime=[str(run/'simv')]
    for arg in original_run[1:]:
        if arg.startswith('+ACTIVITY='):continue
        if arg.startswith('+CAPTURE='):arg='+CAPTURE='+str(run/(case+'.csv'))
        runtime.append(arg)
    runtime+=['-ucli','-i',str(run/'capture.tcl')]
    start,end,duration=window_reader(row['task_window'])
    # The observer independently rechecks that this replay has exactly the
    # original first-VALID/final-ACK/drain window and all original outputs.
    script=('saif -region soc -depth 0 tb_top.u_e203_soc_top\n'
            'run '+start+'ns\nsaif -start soc\nrun '+duration+'ns\n'
            'saif -stop soc\nsaif -report '+case+'.saif -region soc -tres 1e-15\n'
            'run\nquit\n')
    return compile_command,runtime,script


def verify_probe(probe,expected_sha,cfg):
    probe=Path(probe).resolve();probe.relative_to(Path(cfg['server_root']).resolve())
    if sha(probe/'summary.json')!=expected_sha:raise ValueError('Native SAIF probe digest mismatch')
    report=read(probe/'summary.json')
    stage=read(probe.parent/'state.json')['stages']['systolic_b_saif_probe']
    if stage.get('status')!='passed' or stage.get('summary_sha256')!=expected_sha or report.get('status')!='tiny_native_saif_vcs_pt_passed':
        raise ValueError('Native SAIF VCS/PT tiny check has not passed')
    verify_inputs({str(probe/name):digest for name,digest in report['artifacts'].items()})
    return report


def verify(cfg,run,gate,expected_sha,probe,probe_sha,call):
    run,gate=Path(run),Path(gate).resolve();gate.relative_to(Path(cfg['server_root']).resolve())
    # A single pilot, without a VCD: reserve 1 GiB for compilation/activity,
    # plus 20% margin and 2 GiB for other users. Do not remove old evidence.
    free=shutil.disk_usage(str(run)).free
    required=(12*1024**3+9)//10+2*1024**3
    save(run/'storage_budget.json',dict(free_bytes=free,required_bytes=required,
        pilot_budget_bytes=1024**3,margin=1.2,reserve_bytes=2*1024**3))
    if free<required:raise ValueError('Insufficient free space for native SAIF pilot')
    verify_probe(probe,probe_sha,cfg)
    if sha(gate/'summary.json')!=expected_sha:raise ValueError('R4 gate summary digest mismatch')
    report=read(gate/'summary.json');state=read(gate.parent/'state.json')['stages']['icb32_gate']
    if (state.get('status')!='passed' or state.get('summary_sha256')!=expected_sha or
        report.get('scope')!='icb32_whole_soc_mapped_functional_without_SDF' or
        report.get('gate_simulation_verified') is not True or report.get('sdf_annotated') is not False):
        raise ValueError('Native SAIF pilot requires the frozen R4 functional gate result')
    rows=[r for r in report['cases'] if r['case']=='layer_01']
    if len(rows)!=1:raise ValueError('Missing frozen R4 L01')
    row=rows[0];window_values(row['task_window'])
    if row['outputs']!=25344 or row.get('activity',{}).get('status')!='scope_and_window_verified':
        raise ValueError('No verified original full-window VCD reference')
    if sha(gate/'source_inputs.json')!=report['source_inputs_sha256']:raise ValueError('Frozen gate receipt changed')
    before=read(gate/'source_inputs.json');verify_inputs(before)
    # Recheck original VCD identity by streaming, without copying or changing it.
    vcd=gate/row['activity']['file']
    if vcd.name!=row['activity']['file'] or vcd.stat().st_size!=row['activity']['bytes'] or stream_sha(vcd)!=row['activity']['sha256']:
        raise ValueError('Original R4 VCD changed')
    if audit_header(vcd)!=row['activity']['icb32_header']:raise ValueError('Original VCD scope changed')
    for name in ('compile_command.json','layer_01_command.json','layer_01.csv'):
        if str(gate/name) not in before:raise ValueError('Untracked frozen replay input '+name)
    compile_command,runtime,ucli=capture_commands(gate,run,row)
    if compile_command[0]!=cfg['tools']['vcs']:raise ValueError('VCS executable changed')
    save(run/'compile_command.json',compile_command);save(run/'replay_command.json',runtime)
    (run/'capture.tcl').write_text(ucli)
    log=call(compile_command,run,'compile.log')
    if re.search(r'Warning-\[(?:IPDW|PCWM-W|INAV|SIOB)\]',log):raise ValueError('Replay declaration/width mismatch')
    log=call(runtime,run,'replay.log')
    captured=data.check_capture(run/'layer_01.csv',gate/'layer_01_data')
    result=data.parse_result(log,captured['saturated'],MARKERS)
    replay=data.read_window(log,result,row['task_window']['encoded_bytes'])
    if replay!=row['task_window'] or stream_sha(run/'layer_01.csv')!=stream_sha(gate/'layer_01.csv'):
        raise ValueError('Debug replay changed the full timing window or integer output sequence')
    # Completion and IRQ proofs must still be actual execution, not copied rows.
    irq=re.findall(r'^ARCH03_ICB32_IRQ_PROOF enabled=(\d+) external=(\d+) timer=(\d+) wfi=(\d+) events=(\d+) unhandled=(\d+)$',log,re.M)
    if len(irq)!=1 or int(irq[0][0])!=1 or any(int(irq[0][i])<=0 for i in (1,2,3)) or int(irq[0][4])&1!=1 or int(irq[0][5]):
        raise ValueError('Replay did not reproduce real IRQ/WFI completion')
    activity=audit(run/'layer_01.saif',replay)
    verify_inputs(before);verify_probe(probe,probe_sha,cfg)
    evidence=dict(status='R4_native_saif_replay_function_and_window_passed',
        gate_run=str(gate),gate_summary_sha256=expected_sha,
        probe_run=str(probe),probe_summary_sha256=probe_sha,
        synthesis_run=report['synthesis_run'],synthesis_summary_sha256=report['synthesis_summary_sha256'],
        task_window=replay,outputs=25344,integer_capture_sha256=stream_sha(run/'layer_01.csv'),
        activity=activity,source_inputs=before,source_netlist_unchanged=True,
        debug_visibility_only=True,new_VCD_created=False,
        reference_vcd_sha256=row['activity']['sha256'],
        full_power_crosscheck_verified=False,system_power_verified=False,
        artifacts={p.name:stream_sha(p) for p in run.iterdir() if p.is_file()})
    return evidence
