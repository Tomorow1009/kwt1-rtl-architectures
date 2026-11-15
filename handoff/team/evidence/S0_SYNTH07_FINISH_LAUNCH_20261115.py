"""Launch S0 remainder only after the pinned original synthesis has exited.

This script performs no cleanup and never edits the running/original bundle.
It is prepared ahead of time; executing it while mapping runs stops before
creating any queue or launching EDA. A prior failed launch is never retried.
"""
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path('/tmp/s4_21usr_t80_20261115_1830')
BUNDLE=ROOT/'light-light126-t80-s0-9ffb2a9'
OPS=ROOT/'ops-9ffb2a9'
MANIFEST='d397b97768c6ce5089aeda32a5e2e22d50e30f0b5a34c6edfae12e71ea9988ba'
MAPPING_BUNDLE=BUNDLE
SEED_BUNDLE=ROOT/'light-light126-t80-s0-05c923f'
SEED_MANIFEST='4473686ec4bb1b67edd4741fbf171a89788465140b8a1e7d3a9944f4847e7ff2'
MAPPING_MANIFEST=MANIFEST
SYNTH=MAPPING_BUNDLE/'runs/s0_synth07/t80_s0_synth'
SERVER=Path('/storage2/2026contest/server4/s4_21usr/Desktop/IC')


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for part in iter(lambda:stream.read(4*1024**2),b''):h.update(part)
    return h.hexdigest()


def save(path,value):
    with Path(path).open('x') as stream:
        json.dump(value,stream,indent=2,sort_keys=True);stream.write('\n')
        stream.flush();os.fsync(stream.fileno())


def main():
    assert sha(BUNDLE/'manifest.json')==MANIFEST
    assert sha(MAPPING_BUNDLE/'manifest.json')==MAPPING_MANIFEST
    state=json.loads((SYNTH.parent/'state.json').read_text())['stages']['t80_synth']
    launch=json.loads((OPS/'s0_synth07_launch/launch.json').read_text())
    assert sha(OPS/'s0_synth07_launch/command.json')==launch['command_sha256']
    assert state['pid']==launch['pid'] and state['status']=='passed' and state.get('finished'), 'Original S0 mapping not complete'
    assert not (Path('/proc')/str(state['pid'])).exists(), 'Original S0 mapping owner has not exited'
    assert sha(SYNTH/'summary.json')==state['summary_sha256']
    report=json.loads((SYNTH/'summary.json').read_text())
    assert report['scope']=='s0_t80_partitioned_whole_soc_task_mode'
    assert report['setup_hold_nonnegative'] is True, 'Read mapped timing before starting long functional/activity runs'
    assert report['area_summary']['conservative_budget_mm2']<=1.0, 'S0 conservative area exceeds new limit'
    assert not (SERVER/'.arch02_team_lock').exists(), 'Existing team owner; do not clear lock'
    commands=subprocess.check_output(['ps','-u','s4_21usr','-o','comm=']).decode().splitlines()
    assert not any(x.strip() in ('dc_shell','common_shell_ex','pt_shell','simv','vcs','vcs1','vcs2') for x in commands), 'Existing EDA process'
    sys.path.insert(0,str(BUNDLE/'workspaces/arch03/scripts'))
    import s0_finish
    from n1_process import ProcessLedger
    session='s0_finish01'
    assert not (BUNDLE/'runs'/session).exists(), 'Preserve existing S0 queue'
    control=OPS/'s0_finish01_launch';control.mkdir()
    qualification=SERVER/'light-light126-undergrad-d2-20261109/bundles/light-light126-systolic-b-v3-20261112_114355-ced0e139a01e/runs/systolic_b_r4_crosscheck02/native_saif_r4_crosscheck'
    request=dict(schema='s0-final-netlist-finish-v1',bundle=str(BUNDLE),bundle_manifest_sha256=MANIFEST,
        runtime_root=str(ROOT),runtime_evidence=[[str(SEED_BUNDLE),SEED_MANIFEST]],
        queue_sha256=sha(s0_finish.__file__),synthesis=dict(run=str(SYNTH),sha256=state['summary_sha256']),
        qualification=dict(run=str(qualification),sha256='a0a9bc6280e7fe5f35b666535157700aac1d9c0b4490873b6199ba9b5c662d26'))
    path=control/'request.json';save(path,request)
    command=[sys.executable,'-B','-u',s0_finish.__file__,'--request',str(path),
             '--request-sha256',sha(path),'--session',session]
    save(control/'command.json',command)
    child=None
    with (control/'driver.log').open('x') as log:
        try:
            child=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            save(control/'launch.json',dict(pid=child.pid,started=datetime.datetime.now().isoformat(),
                command_sha256=sha(control/'command.json'),request_sha256=sha(path),launcher_sha256=sha(__file__),
                synthesis_summary_sha256=state['summary_sha256'],synthesis_not_restarted=True,
                protected_desktop_written=False,old8_written=False))
        except BaseException:
            if child is not None:ProcessLedger.drain(None,child)
            raise
    print('S0_FINISH_LAUNCHED',child.pid,str(control),flush=True)


if __name__=='__main__':main()
