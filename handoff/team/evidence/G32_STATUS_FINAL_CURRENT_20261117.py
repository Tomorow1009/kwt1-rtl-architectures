"""Read-only current G32 final-netlist progress; no dispatch or acceptance."""
import datetime
import hashlib
import json
from pathlib import Path
import shutil

ROOT=Path('/tmp/s4_21usr_g32_20261117_0810')
BUNDLE=ROOT/'light-light126-g32-0e16994'


def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    print('NOW',datetime.datetime.now().isoformat())
    q=BUNDLE/'runs/g32_finish01';p=q/'state.json';s=read(p)
    print('FINISH',{k:s.get(k) for k in ('status','stage','pid','error','finished')})
    print('PASSED_STAGES',len(s['completed']),[v['stage'] for v in s['completed']][-3:])
    if s.get('finished'):print('TERMINAL_SHA',sha(p),'OWNER_ALIVE',Path('/proc/%s'%s['pid']).exists())
    ledgers=sorted((q/'process_ledger').glob('child_*.json'))
    if ledgers:
        d=read(ledgers[-1]);print('CHILD',{k:d.get(k) for k in ('pid','status','returncode','started')})
    for kind in ('gate','saif'):
        p=BUNDLE/('runs/g32_finish01_'+kind)/('g32_'+kind)/'case_progress.json'
        if p.exists():
            rows=read(p);print(kind.upper(),'PASSED',len(rows),'LAST',rows[-1]['case'] if rows else None)
    power=[v for v in s['completed'] if v['stage'].startswith('power_')]
    if power:
        v=power[-1];p=Path(v['reference']['run'])/'summary.json'
        assert sha(p)==v['reference']['sha256']
        d=read(p);print('POWER_LAYERS',len(power),'LAST',d['case'],'PRELIMINARY',d['numbers']['average_power_w'])
    p=ROOT/'g32_export_review01/state.json'
    if p.exists():
        d=read(p);print('EXPORT',{k:d.get(k) for k in ('status','pid','error','finished')})
    lock=Path('/storage2/2026contest/server4/s4_21usr/Desktop/IC/.arch02_team_lock/owner.json')
    print('LOCK',read(lock).get('pid') if lock.exists() else 'absent')
    print('FREE_BYTES',{'shared':shutil.disk_usage('/storage2').free,'tmp':shutil.disk_usage('/tmp').free})


if __name__=='__main__':main()
