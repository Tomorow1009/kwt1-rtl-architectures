"""Compact read-only observation of the one corrected C32 queue.

No process launch, lock changes, retries, file writes or acceptance.
"""
from pathlib import Path
import datetime
import hashlib
import json
import os

ROOT=Path('/tmp/s4_21usr_c32_20261116_2010')
BUNDLE=ROOT/'light-light126-c32-91135f6'


def read(path):return json.loads(Path(path).read_text())


def main():
    print('OBSERVED',datetime.datetime.now().isoformat())
    queue=BUNDLE/'runs/c32_initial03'
    finish=BUNDLE/'runs/c32_finish01'
    if (finish/'state.json').exists():queue=finish
    state=read(queue/'state.json')
    print('QUEUE',queue.name,state['pid'],state['status'],state.get('stage'))
    print('COMPLETED',[row['stage'] for row in state.get('completed',[])])
    if state.get('error'):print('ERROR',state['error'][:500])
    if state.get('finished'):
        digest=hashlib.sha256((queue/'state.json').read_bytes()).hexdigest().upper()
        print('TERMINAL_SHA',' '.join(digest[i:i+8] for i in range(0,64,8)))
        print('OWNER_ALIVE',Path('/proc/%d'%state['pid']).exists())
    records=sorted((queue/'process_ledger').glob('child_*.json'))
    if records:
        child=read(records[-1]);pid=child.get('pid')
        print('CHILD',pid,child['status'],'alive',bool(pid and Path('/proc/%d'%pid).exists()))
        log=Path(child['log']);print('LOG',str(log.relative_to(BUNDLE/'runs')))
        print('LOG_UPDATED',datetime.datetime.fromtimestamp(log.stat().st_mtime).isoformat())
        # A handful of nonempty lines fits in the existing 800x450 VNC view.
        print('\n'.join([line[:170] for line in log.read_text(errors='replace').splitlines() if line.strip()][-4:]))
    if state.get('stage')=='synth':
        run=Path(state['current_run'])
        for path in sorted(run.glob('blocks/*/cache.json')):
            block=read(path);print('MAPPED',path.parent.name,round(block['elapsed_seconds'],2))
    stats=os.statvfs(str(ROOT));print('TMP_FREE_GIB',round(stats.f_bavail*stats.f_frsize/float(1024**3),2))


if __name__=='__main__':main()
