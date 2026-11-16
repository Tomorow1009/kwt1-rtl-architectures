"""Start the prepared C80 continuation once verified B0 cleanup has exited."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT=Path('/tmp/s4_21usr_c80_20261116_1245')
OPS=ROOT/'ops-followup02-3502772'
CLEAN=ROOT/'ops-b0-cleanup14-d6eadfb'
CONTROL=ROOT/'c80_after_cleanup14'
SOURCE='d5f012fefa01db49de5cb093774d7afee2547692a3f4611c7a2e25e73221cdc5'
PAYLOAD='c37fc7f142d064f0d490289a5413b8250a59295aa7b1b8ba8e4d01104b0805c7'
CLEAN_SOURCE='122dc4476cd2e1972c7187fdbab91c1be15770f53c4b72697b14309c535a1798'


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def need(ok,message):
    if not ok:raise ValueError(message)
def save(p,v):
    with Path(p).open('x') as f:
        json.dump(v,f,indent=2,sort_keys=True);f.write('\n');f.flush();os.fsync(f.fileno())


def main():
    sys.dont_write_bytecode=True
    need(not CONTROL.exists(),'Preserve earlier continuation launcher')
    entry=OPS/'C80_FINAL_FOLLOWUP02_20261116.py'
    need(sha(entry)==SOURCE and sha(OPS/'payload.json')==PAYLOAD,'Changed prepared followup')
    launch=read(CLEAN/'launch.json');launch_sha=sha(CLEAN/'launch.json')
    need(launch['pid']==56033 and launch['source_sha256']==CLEAN_SOURCE and
         sha(CLEAN/'C80_B0_ARCHIVED_INPUT_CLEANUP14_20261116.py')==CLEAN_SOURCE,'Wrong cleanup owner/source')
    CONTROL.mkdir(mode=0o700);save(CONTROL/'started.json',dict(pid=os.getpid(),source_sha256=sha(__file__)))
    try:
        deadline=time.monotonic()+1800
        while Path('/proc/56033').exists():
            need(sha(CLEAN/'launch.json')==launch_sha,'Cleanup launch changed')
            need(str(CLEAN/'C80_B0_ARCHIVED_INPUT_CLEANUP14_20261116.py').encode() in
                 Path('/proc/56033/cmdline').read_bytes().split(b'\0'),'Cleanup PID reused')
            need(time.monotonic()<deadline,'Cleanup wait timed out; no C80 job launched')
            time.sleep(5)
        receipt=ROOT/'b0_archived_batch_cleanup14/state.json';r=read(receipt)
        need(r['status']=='verified_duplicates_removed_backup_retained' and r['removed_files']==49200 and
             r['removed_bytes']==2616732144 and r['script_sha256']==CLEAN_SOURCE,'Cleanup did not complete')
        lock=Path('/storage2/2026contest/server4/s4_21usr/Desktop/IC/.arch02_team_lock')
        need(not lock.exists() and shutil.disk_usage(str(lock.parent)).free>=1024**3,
             'Shared lock or space prevents launch')
        for n,v in read(OPS/'payload.json')['files'].items():
            need(Path(n).name==n and sha(OPS/n)==v['sha256'],'Changed new operation source')
        sys.path.insert(0,str(OPS));import c80_space_retry_contract as check
        files=[ROOT/'c80_followup01.json',ROOT/'light-light126-c80-74f3ae7/runs/c80_precision03/state.json',ROOT/'c80_export_review01/state.json']
        rows=[read(p) for p in files]
        check.validate(rows[0],rows[1],rows[2],lambda pid:Path('/proc/%d'%pid).exists(),lock)
        need(not (ROOT/'c80_followup02.json').exists(),'New followup already started')
        save(OPS/'import_receipt.json',dict(source_commit='350277245626e8c54df6ef13ad685e5b7c3d52b2',
             source_sha256=SOURCE,payload_sha256=PAYLOAD,cleanup_receipt_sha256=sha(receipt),
             failed_attempts={str(p):sha(p) for p in files},source_modified=False))
        command=[sys.executable,'-B','-u',str(entry)]
        with (ROOT/'c80_followup02.log').open('x') as log:
            child=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        record=dict(pid=child.pid,source_sha256=SOURCE,command=command,started=datetime.datetime.now().isoformat(),
             source_commit='350277245626e8c54df6ef13ad685e5b7c3d52b2',import_sha256=sha(OPS/'import_receipt.json'))
        save(ROOT/'c80_followup02_launch.json',record);save(CONTROL/'completed.json',record)
        print('C80_FOLLOWUP02_STARTED_AFTER_VERIFIED_CLEANUP',child.pid,flush=True)
    except BaseException as error:
        save(CONTROL/'failed.json',dict(error=str(error),source_modified=False));raise


if __name__=='__main__':main()
