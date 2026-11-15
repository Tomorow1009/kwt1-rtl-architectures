from pathlib import Path
import os,signal,json,datetime,time,hashlib
root=Path('/tmp/s4_21usr_t64_20261115_1510')
b=root/'light-light126-t64-resume-3552163';q=b/'runs/t64_serial03'
lock=Path('/storage2/2026contest/server4/s4_21usr/Desktop/IC/.arch02_team_lock')
read=lambda p:json.loads(p.read_text())
def proc(pid):
 p=Path('/proc/%d'%pid);assert p.stat().st_uid==os.getuid()
 raw=(p/'stat').read_text();fields=raw[raw.rindex(')')+2:].split()
 return dict(pid=pid,state=fields[0],ppid=int(fields[1]),start_ticks=int(fields[19]),command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode())
s=read(q/'state.json');owner=read(lock/'owner.json')
assert s['pid']==owner['pid']==325056 and s['status']=='running' and s['stage']=='t64_synth'
assert owner['bundle']==str(b) and owner['session']=='t64_serial03'
d=proc(s['pid']);assert 't64_singlelock_queue.py' in d['command'] and 't64_serial03' in d['command']
files=sorted((q/'process_ledger').glob('child_*.json'));row=read(files[-1]);c=proc(row['pid'])
assert row['status']=='running' and row['driver_pid']==d['pid'] and c['ppid']==d['pid']
assert Path(row['log'])==b/'runs/t64_serial03_synth/t64_synth/icb32_synth.log'
assert 'dc_shell' in c['command'] and 'icb32_synth.tcl' in c['command']
assert Path(os.readlink('/proc/%d/fd/1'%c['pid']))==Path(row['log'])
receipt=root/'ops-3552163/user_pause_20261115_1724.json'
assert not receipt.exists() and read(q/'state.json')['stage']=='t64_synth'
before=dict(time=datetime.datetime.now().isoformat(),driver=d,child=c,queue=str(q),stage='t64_synth',lock_owner_sha256=hashlib.sha256((lock/'owner.json').read_bytes()).hexdigest(),child_log=str(row['log']))
os.kill(d['pid'],signal.SIGSTOP)
for attempt in range(20):
 after=proc(d['pid'])
 if after['state']=='T':break
 time.sleep(.05)
assert after['state']=='T' and after['start_ticks']==d['start_ticks']
before.update(driver_stopped=True,child_signal_sent=False,lock_retained=True,new_dispatch_blocked=True,child_after=proc(c['pid']))
with receipt.open('x') as f:json.dump(before,f,indent=2,sort_keys=True);f.write('\n')
print('USER_PAUSE_CONFIRMED',datetime.datetime.now().isoformat(),'DRIVER',d['pid'],after['state'],'CHILD',c['pid'],before['child_after']['state'],'LOCK_RETAINED',True,'RECEIPT',str(receipt),flush=True)
