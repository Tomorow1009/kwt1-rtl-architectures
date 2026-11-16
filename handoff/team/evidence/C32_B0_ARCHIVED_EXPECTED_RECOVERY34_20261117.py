"""Fresh bounded cleanup of the 832 generated references retained by recovery32 and recovery33.

Reuse its unchanged archive, path, byte/hash and idle guards, never its main
against the old scope. Stop at the existing shared lock. No summary/log/source,
final netlist, activity, archive, old8, T80 or frozen S0/P80/C80 is removed.
"""
import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path('/tmp/s4_21usr_c32_20261116_2010')
SOURCE=ROOT/'c32_recovery32.py'
SOURCE_SHA='ef70a9db4d61f9e286dd5bd994556d12639a141eadf10fe6d33ce65dd13e5519'
STATE_SHA='9e611c92d59228486b163e9ce624867ebf4a93a5b0b47dae3666e70b9973b951'


def main():
    def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
    assert sha(SOURCE)==SOURCE_SHA
    state=ROOT/'b0_archived_expected32/state.json'
    assert sha(state)==STATE_SHA
    prior=json.loads(state.read_text())
    assert prior['status']=='query_started_remaining_captures_preserved' and prior['removed_files']==304 and prior['removed_bytes']==46085943
    journal=state.with_name('removal_journal.jsonl')
    assert sha(journal)==prior['journal_sha256']
    removed=[r['path'] for r in map(json.loads,journal.read_text().splitlines()) if r['action']=='removed']
    assert len(removed)==len(set(removed))==304
    state33=ROOT/'b0_archived_expected33/state.json'
    assert sha(state33)=='8f4d2d6fd2db747d1402b98d07fdabf84b01ec2816a7b1e602bbcd8691f5f441'
    prior33=json.loads(state33.read_text());journal33=state33.with_name('removal_journal.jsonl')
    assert prior33['status']=='query_started_remaining_captures_preserved' and prior33['removed_files']==64 and prior33['removed_bytes']==9718967
    assert sha(journal33)==prior33['journal_sha256']
    extra=[r['path'] for r in map(json.loads,journal33.read_text().splitlines()) if r['action']=='removed']
    assert len(extra)==len(set(extra))==64 and not set(extra)&set(removed)
    removed+=extra
    launch=json.loads((ROOT/'c32_finish_repair04_launch.json').read_text())
    expected=ROOT/'light-light126-c32-repair-5828804'
    assert sha(expected/'manifest.json')==launch['manifest_sha256']
    request=json.loads((ROOT/'c32_finish_repair04_request.json').read_text())
    assert request['bundle']==str(expected) and sha(ROOT/'c32_finish_repair04_request.json')==launch['request_sha256']
    driver=ROOT/'c32_finish04_driver.py'
    assert sha(driver)==launch['source_sha256']=='69d8a2cfa69b692953ce1dbddea77f491f85d288cd5a077ccaa5e4d0bc3ceeac'
    proc=Path('/proc/%d'%launch['pid'])
    assert proc.exists() and str(driver).encode()+b'\0' in (proc/'cmdline').read_bytes()
    pending=json.loads((expected/'runs/c32_finish_repair04/state.json').read_text())
    assert pending['status']=='acquiring_lock' and pending['pid']==launch['pid'] and pending['completed']==[]
    text=SOURCE.read_text()
    def once(old,new):
        nonlocal text
        assert text.count(old)==1, 'Changed cleanup guard template'
        text=text.replace(old,new)
    once("out=ROOT/'b0_archived_expected32'", "out=ROOT/'b0_archived_expected34'")
    once("'Wrong/repeated recovery32'", "'Wrong/repeated recovery34'")
    once('    rows=[];files=[]', '''    done=set(REMOVED)
    need(done<=set(selected),'Removed captures outside original archive')
    need(all(not (project/n).exists() for n in done),'Previously removed capture reappeared; preserve it')
    selected={n:r for n,r in selected.items() if n not in done}
    need(len(selected)==832 and sum(r['bytes'] for r in selected.values())==126351144,'Wrong remaining capture set')
    rows=[];files=[]''')
    old="""    proc=Path('/proc/78851');need(proc.exists() and b'/light-light126-c32-repair-b9f0127/workspaces/arch03/scripts/c32_mapped_repair.py\\x00' in
        (proc/'cmdline').read_bytes(),'Expected waiting query changed')
    need(not (ROOT/'light-light126-c32-repair-b9f0127/runs/c32_repair02').exists(),'Query already started; no cleanup needed')"""
    new="""    proc=Path('/proc/%d'%WAITING_PID)
    need(proc.exists() and WAITING_TOOL.encode()+b'\\x00' in (proc/'cmdline').read_bytes(),'Expected waiting repair changed')
    need(read(Path(WAITING_BUNDLE)/'runs/c32_finish_repair04/state.json')['status']=='acquiring_lock','Finish started; no cleanup needed')"""
    once(old,new)
    once("state['removed_files']==1200", "state['removed_files']==832")
    once("'RECOVERY32_COMPLETE'", "'RECOVERY34_COMPLETE'")
    namespace=dict(__name__='recovery34_checked_logic',__file__=str(Path(__file__).resolve()),
        REMOVED=removed,WAITING_PID=launch['pid'],WAITING_TOOL=str(driver),
        WAITING_BUNDLE=str(expected))
    exec(compile(text,'recovery34_from_pinned32','exec'),namespace)
    namespace['main']()


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--execute-verified-remaining-captures',action='store_true',required=True)
    p.parse_args();main()
