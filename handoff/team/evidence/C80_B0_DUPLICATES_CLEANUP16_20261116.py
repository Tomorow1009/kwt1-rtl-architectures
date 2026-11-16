"""Explicitly remove 18 byte-identical, durably archived B0 duplicates.

Run only after current C80 validation AND exporter exit. No running package,
backup, summary, source, netlist, log, T80, old8 or P80 file is removed.
Deletion requires the separate --execute-verified-duplicates option.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

sys.dont_write_bytecode=True
ROOT=Path('/tmp/s4_21usr_c80_20261116_1245')
BUNDLE=ROOT/'light-light126-c80-74f3ae7'
PREFLIGHT=ROOT/'ops-b0-preflight15-964373c/C80_B0_REPORTS_SAIF_PREFLIGHT15_20261116.py'
PREFLIGHT_SHA='66442ee9177fe61175dca7cad488c39d9a4d322c9acf1db5aceee21c3b476b61'
PROOF=ROOT/'b0_archived_reports_saif_preflight15/verified_candidates.json'
PROOF_SHA='3d9ffdba6e36bca8487da1355ccdb8b397439d9332c2e026bcb1a4399bd9097c'
MANIFEST_SHA='d0f18e4a6aa8a928df37d4347f1a8853c448e823f0685a83c5b710732e5e7a59'
OUT=ROOT/'b0_archived_duplicates_cleanup16'


def need(ok,message):
    if not ok:raise ValueError(message)


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(4*1024**2),b''):h.update(chunk)
    return h.hexdigest()


def terminal_state(row,kind,alive):
    expected={'followup':'d5f012fefa01db49de5cb093774d7afee2547692a3f4611c7a2e25e73221cdc5',
              'export':'4c001bb4603a52b3c6f24d95566442bc59c48ee9709e37cbd224b0982331048a'}
    need(row.get('source_sha256')==expected[kind] and type(row.get('pid')) is int and
         row.get('finished') and not alive(row['pid']),'C80 owner is live, changed or nonterminal')
    if kind=='followup':
        need(row['status']=='reports_ready_independent_review_pending','C80 validation is not complete')
    else:
        good=row['status']=='facts_joined_manual_conclusion_required'
        space_failure=row['status']=='failed_preserved' and any(
            s in str(row.get('error','')) for s in ('No space left on device','Errno 28','ENOSPC'))
        need(good or space_failure,'Unexpected exporter failure; do not clean up')


def stopped():
    states={}
    for name,kind in (('c80_followup02.json','followup'),('c80_export_review02/state.json','export')):
        p=ROOT/name;row=json.loads(p.read_text())
        terminal_state(row,kind,lambda pid:Path('/proc/%d'%pid).exists())
        states[str(p)]=sha(p)
    return states


def idle(archive,lock,files):
    need(not lock.exists(),'Existing team lock; no cleanup')
    names=subprocess.check_output(['ps','-u',str(os.getuid()),'-o','comm=']).decode().splitlines()
    need(not any(n.strip() in ('dc_shell','dc_shell-xg-t','common_shell_ex','pt_shell',
                              'vcs','vcs1','vcs2','simv') for n in names),'Own EDA still active')
    obs=archive.no_open_users(files,copy_only=True);exceptions=[]
    for row in obs['inaccessible_owned_processes']:
        proc=Path('/proc')/str(row['pid'])
        try:
            comm=(proc/'comm').read_text().strip();cmd=(proc/'cmdline').read_bytes()
            need((comm=='gnome-keyring-d' and cmd==b'gnome-keyring-daemon\x00--start\x00') or
                 (comm=='gnome-pty-helpe' and cmd==b'gnome-pty-helper\x00'),
                 'Unknown protected process; no cleanup')
            exceptions.append(dict(pid=row['pid'],comm=comm,command=cmd.decode().replace('\x00',' ')))
        except FileNotFoundError:continue
    obs.update(protected_desktop_service_exceptions=exceptions,all_process_fds_verified=not exceptions)
    need(not lock.exists(),'Team lock appeared during process check')
    return obs


def main():
    need(os.name=='posix' and not OUT.exists(),'Server-only, new cleanup attempt required')
    need(sha(PREFLIGHT)==PREFLIGHT_SHA and sha(PROOF)==PROOF_SHA,'Read-only proof changed')
    spec=importlib.util.spec_from_file_location('b0_scope15',str(PREFLIGHT))
    checked=importlib.util.module_from_spec(spec);spec.loader.exec_module(checked)
    need(sha(BUNDLE/'manifest.json')==MANIFEST_SHA,'Operations bundle changed')
    manifest=json.loads((BUNDLE/'manifest.json').read_text())['files']
    for name in ('n1_archive_runtime.py','n1_paths.py','partition_synth_contract.py'):
        rel='workspaces/arch03/scripts/'+name
        need(sha(BUNDLE/rel)==manifest[rel],'Changed process-inspection dependency')
    sys.path.insert(0,str(BUNDLE/'workspaces/arch03/scripts'));import n1_archive_runtime as archive
    proof=json.loads(PROOF.read_text());rows=proof['files']
    need(proof['schema']=='c80-b0-reports-saif-duplicates-readonly-v1' and
         proof['archive_sha256']==checked.ARCHIVE_SHA and
         len(rows)==18 and {checked.candidate_name(r['path']) for r in rows}==set(checked.candidates()) and
         sum(r['bytes'] for r in rows)==2339541372,'Wrong duplicate scope')
    fixed={checked.BACKUP/'manifest.json':checked.MANIFEST_SHA,
           checked.BACKUP/'receipt.json':checked.RECEIPT_SHA,
           checked.BACKUP/'completed-evidence.tar.gz':checked.ARCHIVE_SHA,
           PROOF:PROOF_SHA,PREFLIGHT:PREFLIGHT_SHA}
    fixed.update({Path(p):h for p,h in stopped().items()})
    lock=checked.PROJECT.parent/'.arch02_team_lock';files=[checked.PROJECT/r['path'] for r in rows]
    processes=idle(archive,lock,files)
    before={str(p):checked.stamp(p) for p in fixed}
    need(all(sha(p)==h and checked.stamp(p)==before[str(p)] for p,h in fixed.items()),'Changed backup or terminal evidence')
    for row,p in zip(rows,files):
        need(checked.stamp(p)==row['stamp'] and sha(p)==row['sha256'] and checked.stamp(p)==row['stamp'],
             'Current duplicate changed')
    need(all(sha(p)==h for p,h in fixed.items()),'Changed frozen input')
    idle(archive,lock,files);stopped();OUT.mkdir(mode=0o700)
    state=dict(status='removing_verified_duplicates',script_sha256=sha(__file__),proof_sha256=PROOF_SHA,
        removed_files=0,removed_bytes=0,free_before=shutil.disk_usage(str(checked.PROJECT)).free,
        process_observation=processes,terminal_evidence={str(p):h for p,h in fixed.items()},
        archive=str(checked.BACKUP/'completed-evidence.tar.gz'),archive_sha256=checked.ARCHIVE_SHA,
        backup_modified=False,protected_T80_modified=False,old8_modified=False,p80_modified=False,
        coordination='No existing team lock and no own EDA; stop if a new lock appears',
        restore='Read the exact named members from the retained archive into a new empty directory, verify each SHA/byte count, then restore reviewed original paths.')
    archive.save(OUT/'state.json',state)
    try:
        with (OUT/'removal_journal.jsonl').open('x') as journal:
            for row,p in zip(rows,files):
                idle(archive,lock,files);stopped()
                need(all(checked.stamp(q)==before[str(q)] for q in fixed),'Backup or terminal evidence changed')
                need(checked.stamp(p)==row['stamp'] and sha(p)==row['sha256'],'Duplicate changed before removal')
                journal.write(json.dumps(dict(action='remove_intent',**row),sort_keys=True)+'\n')
                journal.flush();os.fsync(journal.fileno())
                need(not lock.exists(),'New team lock; preserve remaining duplicates')
                p.unlink();archive.sync_dir(p.parent)
                state['removed_files']+=1;state['removed_bytes']+=row['bytes']
                journal.write(json.dumps(dict(action='removed',path=row['path']))+'\n')
                journal.flush();os.fsync(journal.fileno());archive.save(OUT/'state.json',state)
        need(all(not p.exists() for p in files) and all(sha(p)==h for p,h in fixed.items()),'Post-cleanup identity mismatch')
        state.update(status='verified_duplicates_removed_backup_retained',finished=archive.now(),
            free_after=shutil.disk_usage(str(checked.PROJECT)).free,journal_sha256=sha(OUT/'removal_journal.jsonl'))
        archive.save(OUT/'state.json',state)
        print('B0_DUPLICATES16_COMPLETE',state['removed_files'],state['removed_bytes'],sha(OUT/'state.json'),flush=True)
    except BaseException as error:
        state.update(status='stopped_preserved',error=str(error),finished=archive.now())
        archive.save(OUT/'state.json',state);raise


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--execute-verified-duplicates',action='store_true',required=True)
    p.parse_args();main()
