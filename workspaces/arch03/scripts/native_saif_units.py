"""Isolated VCS time-unit diagnostics; never qualifies whole-system power.

Run only through server_run under the team lock. Each spelling gets a fresh
directory and preserved log; rejected options remain explicit failed trials.
"""
import re
from pathlib import Path
from native_saif_probe import FIXTURE, parse_small_saif
from server_run import sha, save


def diagnose(cfg, run, call):
    run=Path(run)
    source=run/'probe.sv';source.write_text(FIXTURE)
    command=[cfg['tools']['vcs'],'-full64','-sverilog','-debug_access+all',
             '-top','tb_saif','-o',run/'simv',source]
    save(run/'compile_command.json',[str(x) for x in command])
    log=call(command,run,'compile.log')
    if re.search(r'(?im)^\s*(Error-|Error:|Fatal:)',log):
        raise ValueError('Time-unit diagnostic fixture compile failed')
    frozen={str(x):sha(x) for x in (source,run/'simv',Path(__file__))}
    results=[]
    candidates=[('default',None),('one_ns','1ns'),('one_ps','1ps'),('bare_ps','ps'),
                ('one_fs','1fs'),('bare_fs','fs'),('exp_ps','1e-12'),('exp_fs','1e-15'),
                ('spaced_ps','1 ps'),('spaced_fs','1 fs')]
    for label,unit in candidates:
        trial=run/label;trial.mkdir(exist_ok=False)
        tcl=trial/'capture.tcl'
        option='' if unit is None else ' -tres {'+unit+'}'
        tcl.write_text('saif -region r1 -depth 0 tb_saif.dut\nrun 12ns\nsaif -start r1\n'
                       'run 60ns\nsaif -stop r1\nsaif -report native.saif -region r1'+option+'\nquit\n')
        row=dict(label=label,requested_timeunit=unit,status='not_run')
        try:
            text=call([run/'simv','-ucli','-i',tcl],trial,'capture.log')
            if re.search(r'(?im)^\s*(Error-|Error:|Fatal:)',text):
                raise ValueError('Capture log contains tool errors')
            receipt=parse_small_saif((trial/'native.saif').read_text())
            row.update(status='tiny_capture_counts_passed',capture=receipt)
        except Exception as error:
            row.update(status='failed',error=str(error))
        row['artifacts']={x.name:sha(x) for x in trial.iterdir() if x.is_file()}
        results.append(row);save(run/'trial_progress.json',results)
    if any(sha(path)!=digest for path,digest in frozen.items()):
        raise ValueError('Time-unit diagnostic fixture changed')
    return dict(status='timeunit_diagnostics_complete_review_required',
        scope='isolated_VCS_tiny_fixture_not_PT_or_system_power',trials=results,
        inputs_sha256=frozen,native_saif_qualified=False,system_power_verified=False,
        review='Select syntax from actual results, then rerun formal tiny VCS/PT probe and R4 full-window cross-check')
