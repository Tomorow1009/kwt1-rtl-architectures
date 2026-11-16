"""One bounded dependency watcher, never retries a failed repair/finish queue.

No EDA before the sole repair parent has exited and its state is passed.
The pinned finish launcher checks netlist equivalence, actual DRC, area, timing,
method identity and the original shared lock before starting the serial queue.
"""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path('/tmp/s4_21usr_c32_20261116_2010')
BUNDLE=ROOT/'light-light126-c32-repair-5828804'


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())


def main():
    p=argparse.ArgumentParser();p.add_argument('--launcher-sha256',required=True);a=p.parse_args()
    launcher=ROOT/'c32_finish_repair03_tool.py'
    assert sha(launcher)==a.launcher_sha256
    launch=read(ROOT/'c32_repair03_launch.json')
    assert launch['bundle']==str(BUNDLE) and launch['source_commit']=='58288044bfbbe344fafc7550647bfc5c29eef0a7'
    assert sha(BUNDLE/'manifest.json')==launch['manifest_sha256']
    pid=launch['pid'];expected=BUNDLE/'workspaces/arch03/scripts/c32_mapped_repair.py'
    while Path('/proc/%d'%pid).exists():
        try:command=(Path('/proc/%d'%pid)/'cmdline').read_bytes()
        except (FileNotFoundError,ProcessLookupError):continue
        if not command:
            time.sleep(1);continue
        assert str(expected).encode()+b'\0' in command, 'Repair PID identity changed'
        time.sleep(5)
    state=BUNDLE/'runs/c32_repair03/state.json'
    assert state.is_file(), 'Repair exited before creating its independent state'
    row=read(state)['stages']['c32_synth']
    assert row['pid']==pid and row['status']=='passed' and row.get('finished'), 'Repair did not pass; preserve and stop'
    run=BUNDLE/'runs/c32_repair03/c32_synth'
    assert sha(run/'summary.json')==row['summary_sha256'] and sha(launcher)==a.launcher_sha256
    print('REPAIR03_EXITED_REPORT_READY',row['summary_sha256'],datetime.datetime.now().isoformat(),flush=True)
    subprocess.check_call([sys.executable,'-B',str(launcher),'--repair-summary-sha256',row['summary_sha256']])


if __name__=='__main__':main()
