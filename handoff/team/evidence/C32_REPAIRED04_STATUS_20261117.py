"""Compact read-only observation of the one active repaired C32 queue."""
from pathlib import Path
import datetime
import json
import shutil

ROOT=Path('/tmp/s4_21usr_c32_20261116_2010')
BUNDLE=ROOT/'light-light126-c32-repair-5828804'
QUEUE=BUNDLE/'runs/c32_finish_repair04'


def read(p):return json.loads(p.read_text())


def main():
    print('AT',datetime.datetime.now().isoformat(),flush=True)
    print('FREE',shutil.disk_usage('/storage2').free,shutil.disk_usage('/tmp').free,flush=True)
    d=read(QUEUE/'state.json')
    print('QUEUE',d['pid'],d['status'],d.get('stage'),d.get('error'),flush=True)
    print('DONE',[x['stage'] for x in d.get('completed',[])],flush=True)
    for kind in ('gate','saif'):
        p=QUEUE.with_name(QUEUE.name+'_'+kind)/('c32_'+kind)/'case_progress.json'
        rows=read(p) if p.exists() else []
        print(kind.upper(),len(rows),[x.get('case',x.get('layer')) for x in rows],flush=True)
    children=sorted((QUEUE/'process_ledger').glob('child_*.json'))
    if children:
        d=read(children[-1]);print('CHILD',d['sequence'],d.get('pid'),d['status'],d.get('started'),flush=True)
        print('CHILD_LOG',str(Path(d['log']).relative_to(BUNDLE)),flush=True)
    launch=read(ROOT/'c32_finish_repair04_launch.json')
    print('OWNER_LIVE',Path('/proc/%d'%launch['pid']).exists(),flush=True)


if __name__=='__main__':main()
