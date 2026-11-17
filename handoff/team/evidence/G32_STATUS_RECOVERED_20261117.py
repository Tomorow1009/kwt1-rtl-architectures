"""Compact read-only snapshot of the G32 recovery and completion jobs."""
import datetime
import hashlib
import json
from pathlib import Path
import shutil

ROOT=Path('/tmp/s4_21usr_g32_20261117_0810')
BUNDLE=ROOT/'light-light126-g32-0e16994'


def read(p):return json.loads(p.read_text())
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    print('NOW',datetime.datetime.now().isoformat())
    for name in ('g32_recovery01','g32_finish01'):
        q=BUNDLE/'runs'/name;p=q/'state.json'
        if not p.exists():continue
        s=read(p);print(name,{k:s.get(k) for k in ('status','stage','pid','error','finished')})
        print('COMPLETED',len(s['completed']),[x['stage'] for x in s['completed']][-3:])
        if s.get('finished'):
            print('TERMINAL_SHA',digest(p),'OWNER_ALIVE',Path('/proc/%s'%s['pid']).exists())
        else:
            ledgers=sorted((q/'process_ledger').glob('child_*.json'))
            if ledgers:
                child=read(ledgers[-1]);print('CHILD',{k:child.get(k) for k in ('pid','status','returncode','started')})
    p=BUNDLE/'runs/g32_recovery01_batch20/g32_batch20/batch_progress.json'
    if p.exists():
        s=read(p);print('BATCH',{k:s.get(k) for k in ('status','completed','failed','checked_outputs',
            'host_elapsed_seconds','estimated_remaining_seconds_with_20percent_margin')})
    p=ROOT/'g32_export_review01/state.json'
    if p.exists():
        s=read(p);print('EXPORT',{k:s.get(k) for k in ('status','pid','error','finished')})
    p=Path('/tmp/s4_21usr_r4_l04_xzmigrate01_20261117/state.json')
    if p.exists():
        s=read(p);print('L04_MIGRATION',{k:s.get(k) for k in ('status','pid','source_deleted','error','finished')})
    lock=Path('/storage2/2026contest/server4/s4_21usr/Desktop/IC/.arch02_team_lock/owner.json')
    print('LOCK',read(lock).get('pid') if lock.exists() else 'absent')
    print('FREE_BYTES',{'shared':shutil.disk_usage('/storage2').free,'tmp':shutil.disk_usage('/tmp').free})


if __name__=='__main__':main()
