"""Wait for the existing S0 queue, then export and inspect its own activity.

No EDA, new hardware, shared-lock change, source mutation or deletion. The
existing finish queue must exit successfully before any report is exported.
"""
import datetime
import hashlib
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import time

ROOT=Path('/tmp/s4_21usr_t80_20261115_1830')
BUNDLE=ROOT/'light-light126-t80-s0-66b9496'
MANIFEST='2afb9a79e600e4bd1a0493699b50d463f7df8ebef666d99290cde2efbf0426b4'
QUEUE=BUNDLE/'runs/s0_finish03'
OPS=ROOT/'ops-66b9496'
CONTROL=OPS/'s0_export01_control'
BUILDER=OPS/'S0_BUILD_REPORT_REQUEST04_20261115.py'
OUTPUT=BUNDLE/'runs/s0_report01/t80_s0_report'
OWNER=172535
STARTED='2026-11-15T23:11:48.772018'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text())
def now():return datetime.datetime.now().isoformat()


def save(path,value):
    with Path(path).open('x') as stream:
        json.dump(value,stream,indent=2,sort_keys=True);stream.write('\n')
        stream.flush();os.fsync(stream.fileno())


def checked_state():
    state=read(QUEUE/'state.json')
    assert state.get('pid')==OWNER and state.get('started')==STARTED,'Original queue identity changed'
    assert state.get('status') in ('running','reports_ready_review_required','failed'),'Unknown queue state'
    assert sha(BUNDLE/'manifest.json')==MANIFEST,'Operations bundle changed'
    return state


def wait_for_queue():
    previous=None
    while True:
        state=checked_state();status=state['status'];mark=(status,state.get('stage'),len(state['completed']))
        if mark!=previous:
            print('S0_EXPORT_WAIT',now(),mark,flush=True);previous=mark
        if status=='failed':raise RuntimeError('Original queue failed: '+state.get('error',''))
        if status=='reports_ready_review_required' and state.get('finished'):break
        cmd=Path('/proc/%d/cmdline'%OWNER)
        assert cmd.exists(),'Queue disappeared before its terminal receipt'
        command=cmd.read_bytes().split(b'\x00')
        assert str(BUNDLE/'workspaces/arch03/scripts/s0_finish.py').encode() in command,'Queue PID reused'
        time.sleep(20)
    for _ in range(60):
        if not Path('/proc/%d'%OWNER).exists():return state
        time.sleep(1)
    raise RuntimeError('Queue owner did not exit after its terminal receipt')


def run(name,command):
    save(CONTROL/(name+'_command.json'),command)
    with (CONTROL/(name+'.log')).open('x') as log:
        child=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT)
        save(CONTROL/(name+'_process.json'),dict(pid=child.pid,started=now(),command_sha256=sha(CONTROL/(name+'_command.json'))))
        code=child.wait()
    save(CONTROL/(name+'_exit.json'),dict(returncode=code,finished=now()))
    assert code==0,name+' failed; preserve logs and earlier results'


def main(expected_builder):
    assert sha(BUILDER)==expected_builder,'Report builder changed'
    assert not CONTROL.exists() and not OUTPUT.exists(),'Preserve old export'
    checked_state();CONTROL.mkdir()
    save(CONTROL/'identity.json',dict(pid=os.getpid(),started=now(),source_sha256=sha(__file__),
        builder_sha256=expected_builder,queue=str(QUEUE),queue_pid=OWNER,queue_started=STARTED,
        no_eda=True,protected_t80_modified=False,old8_modified=False))
    try:
        wait_for_queue()
        sys.path.insert(0,str(BUNDLE/'workspaces/arch03/scripts'))
        import s0_finish
        state=checked_state()
        assert [row['stage'] for row in state['completed']]==list(s0_finish.ORDER),'Incomplete S0 stages'
        frozen=sha(QUEUE/'state.json')
        assert sha(BUILDER)==expected_builder
        runpy.run_path(str(BUILDER),run_name='__main__')
        request=OPS/'s0_report01_request.json'
        evidence=read(QUEUE/'request.json')['runtime_evidence']
        command=[sys.executable,'-B','-u',str(BUNDLE/'workspaces/arch03/scripts/s0_report.py'),
            '--request',str(request),'--output',str(OUTPUT),'--runtime-root',str(ROOT),
            '--runtime-manifest-sha256',MANIFEST]
        for path,digest in evidence:command+=['--runtime-evidence',path,digest]
        run('report',command)
        report=OUTPUT/'report.json';digest=sha(report)
        assert sha(QUEUE/'state.json')==frozen,'Queue changed after completion'
        inventory=BUNDLE/'runs/s0_unknown_inventory01'
        run('unknown_inventory',[sys.executable,'-B','-u',str(BUNDLE/'workspaces/arch03/scripts/b0_saif_unknown_inventory.py'),
            '--report',str(report),'--report-sha256',digest,'--scope-root',str(ROOT),'--output',str(inventory)])
        assert sha(report)==digest and sha(QUEUE/'state.json')==frozen,'Frozen evidence changed'
        save(CONTROL/'result.json',dict(status='export_and_unknown_inventory_ready',finished=now(),
            report=str(report),report_sha256=digest,queue_state_sha256=frozen,
            unknown_inventory=str(inventory),unknown_summary_sha256=sha(inventory/'summary.json'),
            stage_accepted=False,no_eda=True,protected_t80_modified=False,old8_modified=False))
        print('S0_EXPORT_AND_UNKNOWN_READY',digest,'stage_accepted=false',flush=True)
    except BaseException as error:
        save(CONTROL/'result.json',dict(status='failed_preserved',error=str(error),finished=now(),
            stage_accepted=False,no_eda=True));raise


if __name__=='__main__':
    assert len(sys.argv)==2,'Pass the committed builder SHA256'
    main(sys.argv[1])
