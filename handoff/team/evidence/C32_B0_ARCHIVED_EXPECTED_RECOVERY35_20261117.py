"""Free at most 128 still-present, fully archived B0 generated references.

Stop immediately when the original team lock appears. All prior cleanup
journals are verified and excluded. Only enables the separately reviewed
R4 L03 lossless migration after its first attempt made no deletion.
No T80/old8/frozen S0/P80/C80, source, summary, netlist or waveform is selected.
"""
import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path('/tmp/s4_21usr_c32_20261116_2010')
SOURCE=ROOT/'c32_recovery32.py'
SOURCE_SHA='ef70a9db4d61f9e286dd5bd994556d12639a141eadf10fe6d33ce65dd13e5519'
PRIORS=(
    (32,'9e611c92d59228486b163e9ce624867ebf4a93a5b0b47dae3666e70b9973b951',304,46085943),
    (33,'8f4d2d6fd2db747d1402b98d07fdabf84b01ec2816a7b1e602bbcd8691f5f441',64,9718967),
    (34,'a4130c4109113e6b3295b9bcc1bdfdaa787c2802be632233938da4ca8c4da51e',296,44987070))
MIGRATION=Path('/tmp/s4_21usr_r4_l03_xzmigrate03_20261117.py')
MIGRATION_SHA='cdd422679ce3084b0397306bd1446b492dda11f231cd295c89927b2dda9b163d'


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())


def waiting():
    assert sha(MIGRATION)==MIGRATION_SHA
    p=Path('/tmp/s4_21usr_r4_l03_xzmigrate03_20261117/state.json');s=read(p)
    assert s['status']=='waiting_for_team_lock' and not s['source_deleted']
    assert s['source_script_sha256']==MIGRATION_SHA
    proc=Path('/proc/%d'%s['pid'])
    assert proc.exists() and str(MIGRATION).encode()+b'\0' in (proc/'cmdline').read_bytes()
    return s


def main():
    assert sha(SOURCE)==SOURCE_SHA
    removed=[]
    for number,want,count,size in PRIORS:
        state=ROOT/('b0_archived_expected%d/state.json'%number)
        assert sha(state)==want
        prior=read(state);journal=state.with_name('removal_journal.jsonl')
        assert prior['status']=='query_started_remaining_captures_preserved'
        assert prior['removed_files']==count and prior['removed_bytes']==size
        assert sha(journal)==prior['journal_sha256']
        rows=[r['path'] for r in map(json.loads,journal.read_text().splitlines()) if r['action']=='removed']
        assert len(rows)==len(set(rows))==count and not set(rows)&set(removed)
        removed+=rows
    old=read('/tmp/s4_21usr_r4_l03_xzmigrate02_20261117/state.json')
    assert old['status']=='preflight' and not old['source_deleted'] and not Path('/proc/%d'%old['pid']).exists()
    assert Path(old['source']).exists()
    log=Path('/tmp/s4_21usr_r4_l03_migrate02_20261117.log').read_text()
    assert 'OSError: [Errno 28]' in log and '.arch02_team_lock' in log
    waiting()
    text=SOURCE.read_text()
    def once(a,b):
        nonlocal text
        assert text.count(a)==1,'Changed pinned cleanup logic'
        text=text.replace(a,b)
    once("out=ROOT/'b0_archived_expected32'","out=ROOT/'b0_archived_expected35'")
    once("'Wrong/repeated recovery32'","'Wrong/repeated recovery35'")
    once('    rows=[];files=[]', '''    done=set(REMOVED)
    need(done<=set(selected),'Prior journal outside the exact archive')
    need(all(not (project/n).exists() for n in done),'Previously removed file reappeared')
    selected={n:r for n,r in selected.items() if n not in done}
    need(len(selected)==536 and sum(r['bytes'] for r in selected.values())==81364074,'Wrong remaining set')
    selected=dict(sorted(selected.items())[:128])
    rows=[];files=[]''')
    a="""    proc=Path('/proc/78851');need(proc.exists() and b'/light-light126-c32-repair-b9f0127/workspaces/arch03/scripts/c32_mapped_repair.py\\x00' in
        (proc/'cmdline').read_bytes(),'Expected waiting query changed')
    need(not (ROOT/'light-light126-c32-repair-b9f0127/runs/c32_repair02').exists(),'Query already started; no cleanup needed')"""
    once(a,'    WAITING()')
    once("state['removed_files']==1200","state['removed_files']==128")
    once("'RECOVERY32_COMPLETE'","'RECOVERY35_COMPLETE'")
    namespace=dict(__name__='recovery35_pinned_guards',__file__=str(Path(__file__).resolve()),REMOVED=removed,WAITING=waiting)
    exec(compile(text,'recovery35_from_pinned32','exec'),namespace)
    namespace['main']()


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--execute-verified-remaining-captures',action='store_true',required=True)
    p.parse_args();main()
