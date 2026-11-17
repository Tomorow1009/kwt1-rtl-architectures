"""Free at most 128 verified archived B0 reference duplicates for G32's lock.

Preserves every archive, source, summary, log, netlist, activity file, old8,
desktop T80 and frozen S0/P80/C80/C32 evidence. Stops when the original lock
appears; never replaces a lock or restarts the waiting G32 queue.
"""
import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path('/tmp/s4_21usr_c32_20261116_2010')
SOURCE=ROOT/'c32_recovery32.py'
SOURCE_SHA='ef70a9db4d61f9e286dd5bd994556d12639a141eadf10fe6d33ce65dd13e5519'
GROOT=Path('/tmp/s4_21usr_g32_20261117_0810')
GBUNDLE=GROOT/'light-light126-g32-0e16994'
PRIORS=(
    (32,'9e611c92d59228486b163e9ce624867ebf4a93a5b0b47dae3666e70b9973b951',304,46085943),
    (33,'8f4d2d6fd2db747d1402b98d07fdabf84b01ec2816a7b1e602bbcd8691f5f441',64,9718967),
    (34,'a4130c4109113e6b3295b9bcc1bdfdaa787c2802be632233938da4ca8c4da51e',296,44987070),
    (35,'8778b950c3c8981257fa859e3d33d0c22276acecf993b81b7c80cb5472e3edeb',128,19387868))


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())


def waiting():
    launch=read(GROOT/'g32_initial01_process.json')
    assert launch['pid']==202586
    assert launch['bundle_manifest_sha256']=='3524e2726880684c1c5681ef90da3a1ca41d78daf20d0df5b648e633b6e42f4a'
    assert sha(GBUNDLE/'manifest.json')==launch['bundle_manifest_sha256']
    queue=GBUNDLE/'workspaces/arch03/scripts/g32_qualification.py'
    assert sha(queue)==launch['queue_sha256']==read(GBUNDLE/'manifest.json')['files']['workspaces/arch03/scripts/g32_qualification.py']
    assert sha(GROOT/'g32_initial01_request.json')==launch['request_sha256']
    s=read(GBUNDLE/'runs/g32_initial01/state.json')
    assert s['status']=='acquiring_lock' and s['completed']==[] and s['pid']==launch['pid']
    proc=Path('/proc/%d'%s['pid'])
    assert proc.exists() and str(queue).encode()+b'\0' in (proc/'cmdline').read_bytes()
    assert not (GBUNDLE/'runs/g32_initial01_soc').exists()


def adapt(text):
    def once(a,b):
        nonlocal text
        assert text.count(a)==1,'Changed pinned cleanup logic'
        text=text.replace(a,b)
    once("out=ROOT/'b0_archived_expected32'","out=GROOT/'b0_archived_expected36'")
    once("'Wrong/repeated recovery32'","'Wrong/repeated recovery36'")
    once('    rows=[];files=[]', '''    done=set(REMOVED)
    need(done<=set(selected),'Prior journal outside the exact archive')
    need(all(not (project/n).exists() for n in done),'Previously removed file reappeared')
    selected={n:r for n,r in selected.items() if n not in done}
    need(len(selected)==408 and sum(r['bytes'] for r in selected.values())==61976206,'Wrong remaining set')
    selected=dict(sorted(selected.items())[:128])
    rows=[];files=[]''')
    old="""    proc=Path('/proc/78851');need(proc.exists() and b'/light-light126-c32-repair-b9f0127/workspaces/arch03/scripts/c32_mapped_repair.py\\x00' in
        (proc/'cmdline').read_bytes(),'Expected waiting query changed')
    need(not (ROOT/'light-light126-c32-repair-b9f0127/runs/c32_repair02').exists(),'Query already started; no cleanup needed')"""
    once(old,'    WAITING()')
    once("state['removed_files']==1200","state['removed_files']==128")
    once("'RECOVERY32_COMPLETE'","'RECOVERY36_COMPLETE'")
    return text


def main():
    assert sha(SOURCE)==SOURCE_SHA
    removed=[]
    for number,want,count,size in PRIORS:
        state=ROOT/('b0_archived_expected%d/state.json'%number)
        assert sha(state)==want
        prior=read(state);journal=state.with_name('removal_journal.jsonl')
        assert prior['status']==('verified_duplicates_removed_archive_retained' if number==35 else 'query_started_remaining_captures_preserved')
        assert prior['removed_files']==count and prior['removed_bytes']==size
        assert sha(journal)==prior['journal_sha256']
        rows=[r['path'] for r in map(json.loads,journal.read_text().splitlines()) if r['action']=='removed']
        assert len(rows)==len(set(rows))==count and not set(rows)&set(removed)
        removed+=rows
    waiting()
    namespace=dict(__name__='recovery36_pinned_guards',__file__=str(Path(__file__).resolve()),
                   REMOVED=removed,WAITING=waiting,GROOT=GROOT)
    exec(compile(adapt(SOURCE.read_text()),'recovery36_from_pinned32','exec'),namespace)
    namespace['main']()


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--execute-verified-remaining-captures',action='store_true',required=True)
    p.parse_args();main()
