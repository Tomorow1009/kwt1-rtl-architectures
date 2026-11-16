"""Fresh bounded cleanup of the 663 captures explicitly retained by recovery29.

Reuse its unchanged archive, path, byte/hash and idle guards, never its main
against the old scope. Stop at the existing shared lock. No summary/log/source,
final netlist, activity, archive, old8, T80 or frozen S0/P80/C80 is removed.
"""
import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path('/tmp/s4_21usr_c32_20261116_2010')
SOURCE=ROOT/'c32_recovery29.py'
SOURCE_SHA='6710fc05d79ccd019c3fc1e0aaff55329e194c345b0ff93ca26749f985dd1627'
STATE_SHA='a1170088c32ca7f91ac01916c351e96215dcdc1510b8f97ebd7fb7ebe35b8663'


def main():
    def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
    assert sha(SOURCE)==SOURCE_SHA
    state=ROOT/'b0_archived_captures29/state.json'
    assert sha(state)==STATE_SHA
    prior=json.loads(state.read_text())
    assert prior['status']=='query_started_remaining_captures_preserved' and prior['removed_files']==537 and prior['removed_bytes']==172434752
    journal=state.with_name('removal_journal.jsonl')
    assert sha(journal)==prior['journal_sha256']
    removed=[r['path'] for r in map(json.loads,journal.read_text().splitlines()) if r['action']=='removed']
    assert len(removed)==len(set(removed))==537
    launch=json.loads((ROOT/'c32_repair01_launch.json').read_text())
    expected=ROOT/'light-light126-c32-repair-c7c7f6c'
    assert launch['bundle']==str(expected) and launch['source_commit']=='c7c7f6c3505ca54b90d1fa54893b925866d3c3ee'
    assert sha(expected/'manifest.json')==launch['manifest_sha256']
    request=json.loads((ROOT/'c32_repair01_request.json').read_text())
    assert sha(ROOT/'c32_repair01_request.json')==launch['request_sha256']
    assert sha(expected/'workspaces/arch03/scripts/c32_mapped_repair.py')==request['tool_sha256']
    proc=Path('/proc/%d'%launch['pid'])
    assert proc.exists() and str(expected/'workspaces/arch03/scripts/c32_mapped_repair.py').encode()+b'\0' in (proc/'cmdline').read_bytes()
    assert not (expected/'runs/c32_repair01').exists(), 'Repair started; no cleanup needed'
    text=SOURCE.read_text()
    def once(old,new):
        nonlocal text
        assert text.count(old)==1, 'Changed cleanup guard template'
        text=text.replace(old,new)
    once("out=ROOT/'b0_archived_captures29'", "out=ROOT/'b0_archived_captures30'")
    once("'Wrong/repeated recovery29'", "'Wrong/repeated recovery30'")
    once('    rows=[];files=[]', '''    done=set(REMOVED)
    need(done<=set(selected),'Removed captures outside original archive')
    need(all(not (project/n).exists() for n in done),'Previously removed capture reappeared; preserve it')
    selected={n:r for n,r in selected.items() if n not in done}
    need(len(selected)==663 and sum(r['bytes'] for r in selected.values())==213048254,'Wrong remaining capture set')
    rows=[];files=[]''')
    old="""    proc=Path('/proc/57941');need(proc.exists() and b'/ops-c32-drc02-f14498f/inspect02.py\\x00' in
        (proc/'cmdline').read_bytes(),'Expected waiting query changed')
    need(not (ROOT/'light-light126-c32-91135f6/runs/c32_drc_inspect02').exists(),'Query already started; no cleanup needed')"""
    new="""    proc=Path('/proc/%d'%WAITING_PID)
    need(proc.exists() and WAITING_TOOL.encode()+b'\\x00' in (proc/'cmdline').read_bytes(),'Expected waiting repair changed')
    need(not (Path(WAITING_BUNDLE)/'runs/c32_repair01').exists(),'Repair started; no cleanup needed')"""
    once(old,new)
    once("state['removed_files']==1200", "state['removed_files']==663")
    once("'RECOVERY29_COMPLETE'", "'RECOVERY30_COMPLETE'")
    namespace=dict(__name__='recovery30_checked_logic',__file__=str(Path(__file__).resolve()),
        REMOVED=removed,WAITING_PID=launch['pid'],WAITING_TOOL=str(expected/'workspaces/arch03/scripts/c32_mapped_repair.py'),
        WAITING_BUNDLE=str(expected))
    exec(compile(text,'recovery30_from_pinned29','exec'),namespace)
    namespace['main']()


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--execute-verified-remaining-captures',action='store_true',required=True)
    p.parse_args();main()
