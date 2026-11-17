"""Free at most 88 verified archived B0 reference duplicates for G32's lock.

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
    (35,'8778b950c3c8981257fa859e3d33d0c22276acecf993b81b7c80cb5472e3edeb',128,19387868),
    (36,'8f08fc401e7fc262176d2265b824ab4483ba176c7b2d6bc9075befd0cb5e085d',128,19398857),
    (37,'850220e04bf6018a6011ba367ee40052bd64dc23f2d56b4b23efc4e3a58e7ead',128,19454666),
    (38,'4337023c8976f16d9a83d09fa701a2bf507005b8ff882dd88ad15879c1fb24e3',32,4866429),
    (39,'40c51722a13dba88fc0f0d2745436b13805488ca3e3a6405578026f1deff128b',32,4864624))


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())


def waiting():
    manifest='3524e2726880684c1c5681ef90da3a1ca41d78daf20d0df5b648e633b6e42f4a'
    assert sha(GBUNDLE/'manifest.json')==manifest
    control=GROOT/'g32_export_review01';state=read(control/'state.json')
    assert state['status']=='querying_own_mapped_connections' and state['pid']==4543
    assert state['report_sha256']=='f95e15e701e08bf8cd0bb091307b93c3c71af71705a5a998f4a84bb2e8af0183'
    script=GBUNDLE/'workspaces/arch03/scripts/g32_unknown_connections.py'
    assert sha(script)==read(GBUNDLE/'manifest.json')['files']['workspaces/arch03/scripts/g32_unknown_connections.py']
    request=control/'connection_request.json';req=read(request)
    assert req['session']=='g32_unknown_connections01' and req['transport_stage']=='G32'
    assert req['bundle_manifest_sha256']==manifest and req['runtime_root']==str(GROOT)
    process=read(control/'connections_process.json')
    assert process['pid']==22550 and process['driver_pid']==4543
    command=process['command']
    assert command==read(control/'connections_command.json')
    assert command[-5:]==[str(script),'--request',str(request),'--request-sha256',sha(request)]
    actual=(Path('/proc/22550')/'cmdline').read_bytes().split(b'\0')[:-1]
    assert actual==[x.encode() for x in command]
    assert b'G32_EXPORT_RECOVERED_REVIEW01_20261117.py' in (Path('/proc/4543')/'cmdline').read_bytes()
    assert not (GBUNDLE/'runs/g32_unknown_connections01').exists()
    assert (control/'connections.log').read_text().rstrip().endswith('WAIT_INITIAL_SHARED_LOCK_STORAGE')


def adapt(text):
    def once(a,b):
        nonlocal text
        assert text.count(a)==1,'Changed pinned cleanup logic'
        text=text.replace(a,b)
    once("out=ROOT/'b0_archived_expected32'","out=GROOT/'b0_archived_expected40'")
    once("'Wrong/repeated recovery32'","'Wrong/repeated recovery40'")
    once('    rows=[];files=[]', '''    done=set(REMOVED)
    need(done<=set(selected),'Prior journal outside the exact archive')
    need(all(not (project/n).exists() for n in done),'Previously removed file reappeared')
    selected={n:r for n,r in selected.items() if n not in done}
    need(len(selected)==88 and sum(r['bytes'] for r in selected.values())==13391630,'Wrong remaining set')
    selected=dict(sorted(selected.items())[:88])
    rows=[];files=[]''')
    old="""    proc=Path('/proc/78851');need(proc.exists() and b'/light-light126-c32-repair-b9f0127/workspaces/arch03/scripts/c32_mapped_repair.py\\x00' in
        (proc/'cmdline').read_bytes(),'Expected waiting query changed')
    need(not (ROOT/'light-light126-c32-repair-b9f0127/runs/c32_repair02').exists(),'Query already started; no cleanup needed')"""
    once(old,'    WAITING()')
    once("state['removed_files']==1200","state['removed_files']==88")
    once("'RECOVERY32_COMPLETE'","'RECOVERY40_COMPLETE'")
    return text


def main():
    assert sha(SOURCE)==SOURCE_SHA
    removed=[]
    for number,want,count,size in PRIORS:
        state=(GROOT if number>=36 else ROOT)/('b0_archived_expected%d/state.json'%number)
        assert sha(state)==want
        prior=read(state);journal=state.with_name('removal_journal.jsonl')
        assert prior['status']==('verified_duplicates_removed_archive_retained' if number in (35,36,37,38,39) else 'query_started_remaining_captures_preserved')
        assert prior['removed_files']==count and prior['removed_bytes']==size
        assert sha(journal)==prior['journal_sha256']
        rows=[r['path'] for r in map(json.loads,journal.read_text().splitlines()) if r['action']=='removed']
        assert len(rows)==len(set(rows))==count and not set(rows)&set(removed)
        removed+=rows
    waiting()
    namespace=dict(__name__='recovery40_pinned_guards',__file__=str(Path(__file__).resolve()),
                   REMOVED=removed,WAITING=waiting,GROOT=GROOT)
    exec(compile(adapt(SOURCE.read_text()),'recovery40_from_pinned32','exec'),namespace)
    namespace['main']()


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--execute-verified-remaining-captures',action='store_true',required=True)
    p.parse_args();main()
