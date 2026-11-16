"""Wait for the sole new-netlist queue, then export exactly once.

No EDA or report inheritance while the final queue remains live; failures
preserve the run and stop. This grants no acceptance and starts no new hardware.
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
    p=argparse.ArgumentParser();p.add_argument('--exporter-sha256',required=True);a=p.parse_args()
    exporter=ROOT/'c32_repaired04_export_review.py';assert sha(exporter)==a.exporter_sha256
    launch=read(ROOT/'c32_finish_repair04_launch.json');pid=launch['pid']
    driver=ROOT/'c32_finish04_driver.py'
    assert sha(driver)==launch['source_sha256']=='69d8a2cfa69b692953ce1dbddea77f491f85d288cd5a077ccaa5e4d0bc3ceeac'
    assert sha(BUNDLE/'manifest.json')==launch['manifest_sha256']
    assert sha(ROOT/'c32_finish_repair04_request.json')==launch['request_sha256']
    proc=Path('/proc/%d'%pid)
    while proc.exists():
        try:command=(proc/'cmdline').read_bytes()
        except (FileNotFoundError,ProcessLookupError):continue
        if command:assert str(driver).encode()+b'\0' in command and b'--worker\0' in command,'Finish PID changed'
        time.sleep(5)
    path=BUNDLE/'runs/c32_finish_repair04/state.json';state=read(path)
    assert state['status']=='reports_ready_review_required' and state.get('finished') and state['pid']==pid
    assert state['synthesis']==launch['synthesis']
    assert sha(exporter)==a.exporter_sha256
    print('C32_FINISH04_EXITED_REPORTS_READY',sha(path),datetime.datetime.now().isoformat(),flush=True)
    subprocess.check_call([sys.executable,'-B',str(exporter),'--finish-state-sha256',sha(path)])


if __name__=='__main__':main()
