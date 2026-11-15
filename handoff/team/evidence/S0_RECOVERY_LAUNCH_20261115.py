"""Start one new S0 incremental recovery; old failed run and deliveries stay read-only."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path('/tmp/s4_21usr_t80_20261115_1830')
BUNDLE=ROOT/'light-light126-t80-s0-a5ce90a'
OPS=ROOT/'ops-a5ce90a'
MANIFEST='6d40f4d67fc94a3b10fe3e1ece27076cf7affc33297602078721397165ca8d78'
OLD=ROOT/'light-light126-t80-s0-05c923f'
OLD_MANIFEST='4473686ec4bb1b67edd4741fbf171a89788465140b8a1e7d3a9944f4847e7ff2'
STATE='83a9b896cb541a0631f7888ea796a10a5dcd7fe863b2fdeb91756a57e0e3783d'
SERVER=Path('/storage2/2026contest/server4/s4_21usr/Desktop/IC')


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(4*1024**2),b''):h.update(block)
    return h.hexdigest()


def save(path,value):
    with Path(path).open('x') as f:
        json.dump(value,f,indent=2,sort_keys=True);f.write('\n');f.flush();os.fsync(f.fileno())


def main():
    assert sha(BUNDLE/'manifest.json')==MANIFEST
    assert sha(OLD/'manifest.json')==OLD_MANIFEST
    sys.path.insert(0,str(BUNDLE/'workspaces/arch03/scripts'))
    import s0_recovery,t80_paths
    from n1_process import ProcessLedger
    cfg=t80_paths.configure(json.loads((BUNDLE/'handoff/team/server_config.json').read_text()),
        BUNDLE,ROOT,MANIFEST,[(str(OLD),OLD_MANIFEST)])
    failed=OLD/'runs/s0_synth03/t80_s0_synth'
    t80_paths.allowed_run(failed,cfg,'S0 failed seed')
    seed=s0_recovery.verify_seed(failed,STATE)
    assert not (SERVER/'.arch02_team_lock').exists(),'Existing owner; preserve lock'
    commands=subprocess.check_output(['ps','-u','s4_21usr','-o','comm=']).decode().splitlines()
    assert not any(x.strip() in ('dc_shell','common_shell_ex','pt_shell','simv','vcs','vcs1','vcs2') for x in commands),'Existing EDA'
    assert not (BUNDLE/'runs/s0_synth04').exists(),'Preserve earlier attempt'
    origin=SERVER/'light-light126-undergrad-d2-20261109/bundles/light-light126-t80-v4-9196556-delta03/runs/t80_finish02_synth/t80_synth'
    command=[sys.executable,'-B','-u',str(BUNDLE/'workspaces/arch03/scripts/s0_server.py'),
        'synth','--session','s0_synth04','--origin',str(origin),'--runtime-root',str(ROOT),
        '--runtime-manifest-sha256',MANIFEST,'--runtime-evidence',str(OLD),OLD_MANIFEST,
        '--recovery-run',str(failed),'--recovery-state-sha256',STATE]
    control=OPS/'s0_synth04_launch';control.mkdir()
    save(control/'seed.json',seed);save(control/'command.json',command)
    child=None
    with (control/'driver.log').open('x') as log:
        try:
            child=subprocess.Popen(command,cwd=str(OPS),stdin=subprocess.DEVNULL,
                stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            save(control/'launch.json',dict(pid=child.pid,started=datetime.datetime.now().isoformat(),
                command_sha256=sha(control/'command.json'),launcher_sha256=sha(__file__),
                seed_receipt_sha256=sha(control/'seed.json'),failed_state_sha256=STATE,
                original_failure_unchanged=True,protected_desktop_written=False,old8_written=False))
        except BaseException:
            if child is not None:ProcessLedger.drain(None,child)
            raise
    print('S0_RECOVERY_STARTED',child.pid,str(control),flush=True)


if __name__=='__main__':main()
