"""Launch only final linking/reports from fully checked synth07 block caches."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path('/tmp/s4_21usr_t80_20261115_1830')
BUNDLE=ROOT/'light-light126-t80-s0-a5f138e'
MANIFEST='c4774571c8aebe323657a5aaebc017f24324396b28ea6b2852e32e40a213b924'
OPS=ROOT/'ops-a5f138e'
CACHE=ROOT/'light-light126-t80-s0-9ffb2a9'
CACHE_MANIFEST='d397b97768c6ce5089aeda32a5e2e22d50e30f0b5a34c6edfae12e71ea9988ba'
SEED=ROOT/'light-light126-t80-s0-05c923f'
SEED_MANIFEST='4473686ec4bb1b67edd4741fbf171a89788465140b8a1e7d3a9944f4847e7ff2'
STATE='43294b528a89c8d0239ccd5e92ee597fc26531217fe3c5245052112030744405'
SERVER=Path('/storage2/2026contest/server4/s4_21usr/Desktop/IC')


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save(path,value):
    with Path(path).open('x') as f:
        json.dump(value,f,indent=2,sort_keys=True);f.write('\n');f.flush();os.fsync(f.fileno())


def main():
    assert sha(BUNDLE/'manifest.json')==MANIFEST
    sys.path.insert(0,str(BUNDLE/'workspaces/arch03/scripts'))
    import s0_relink,t80_paths
    from n1_process import ProcessLedger
    evidence=[(str(CACHE),CACHE_MANIFEST),(str(SEED),SEED_MANIFEST)]
    cfg=t80_paths.configure(json.loads((BUNDLE/'handoff/team/server_config.json').read_text()),
        BUNDLE,ROOT,MANIFEST,evidence)
    failed=CACHE/'runs/s0_synth07/t80_s0_synth'
    t80_paths.allowed_run(failed,cfg,'Completed synth07 block caches')
    proof=s0_relink.verify(failed,STATE,cfg,BUNDLE)
    assert not (SERVER/'.arch02_team_lock').exists(),'Existing owner; preserve lock'
    commands=subprocess.check_output(['ps','-u','s4_21usr','-o','comm=']).decode().splitlines()
    assert not any(x.strip() in ('dc_shell','common_shell_ex','pt_shell','simv','vcs','vcs1','vcs2') for x in commands),'Existing EDA'
    assert not (BUNDLE/'runs/s0_synth08').exists(),'Preserve any earlier attempt'
    command=[sys.executable,'-B','-u',str(BUNDLE/'workspaces/arch03/scripts/s0_server.py'),
        'synth','--session','s0_synth08','--origin',proof['origin']['origin'],
        '--runtime-root',str(ROOT),'--runtime-manifest-sha256',MANIFEST,
        '--runtime-evidence',str(CACHE),CACHE_MANIFEST,'--runtime-evidence',str(SEED),SEED_MANIFEST,
        '--reuse-blocks-run',str(failed),'--reuse-blocks-state-sha256',STATE]
    control=OPS/'s0_synth08_launch';control.mkdir()
    save(control/'cache_preflight.json',proof);save(control/'command.json',command)
    child=None
    with (control/'driver.log').open('x') as log:
        try:
            child=subprocess.Popen(command,cwd=str(OPS),stdin=subprocess.DEVNULL,
                stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            save(control/'launch.json',dict(pid=child.pid,started=datetime.datetime.now().isoformat(),
                command_sha256=sha(control/'command.json'),launcher_sha256=sha(__file__),
                cache_receipt_sha256=sha(control/'cache_preflight.json'),failed_state_sha256=STATE,
                original_failure_unchanged=True,mapping_repeated=False,
                protected_desktop_written=False,old8_written=False))
        except BaseException:
            if child is not None:ProcessLedger.drain(None,child)
            raise
    print('S0_RELINK_STARTED',child.pid,str(control),'mapping_repeated=false',flush=True)


if __name__=='__main__':main()
