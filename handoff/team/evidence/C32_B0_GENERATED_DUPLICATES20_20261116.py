"""Remove only archived generated/compiled duplicates from five exact old B0 runs.

Uses prior readback proof plus fresh full archive, manifest and source hashes.
The C32 initial queue must have exited before doing any child work. Original
T80, old8, P80/C80, all backups, source, netlists and summaries are excluded.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path,PurePosixPath
import shutil
import subprocess
import sys

sys.dont_write_bytecode=True
ROOT=Path('/tmp/s4_21usr_c32_20261116_2010')
INITIAL=ROOT/'light-light126-c32-61246bb/runs/c32_initial01'
INITIAL_SHA='42ffa16c397ab474753eb1cc9ef5617c2bf226bbee1c318f8e752fd5416aa674'
OLD=Path('/tmp/s4_21usr_c80_20261116_1245')
DEPENDENCY=OLD/'ops-b0-cleanup16-c8c730d/C80_B0_DUPLICATES_CLEANUP16_20261116.py'
DEPENDENCY_SHA='0e98728332e0ba048142231f414322dc3aaf21e287b3bde0bc4121124c976441'
OUT=ROOT/'b0_archived_generated_duplicates20'
PREFIX='bundles/light-light126-systolic-b-v3-20261112_114355-ced0e139a01e/runs/'
GROUPS={'systolic_b_final02_clean14':(574,30590599),
        'systolic_b_v3_drc06_gate02':(574,30590599),
        'systolic_b_v3_validation03_gate14':(574,30590599),
        'systolic_b_v3_validation03_contention':(82,4417569),
        'systolic_b_v3_validation03_sequence':(48,2264344)}


def selected(name):
    p=PurePosixPath(name)
    if p.is_absolute() or '..' in p.parts or '\\' in name or p.as_posix()!=name:return False
    if not name.startswith(PREFIX):return False
    parts=name[len(PREFIX):].split('/')
    return len(parts)>1 and parts[0] in GROUPS and (parts[-1]=='simv' or
        Path(name).suffix in ('.o','.so','.a','.hex','.bin','.verilog'))


def need(ok,message):
    if not ok:raise ValueError(message)


def read(path):return json.loads(Path(path).read_text())


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,str(path))
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value


def initial_guard(sha):
    need(sha(INITIAL/'state.json')==INITIAL_SHA,'Original failed C32 queue changed')
    row=read(INITIAL/'state.json')
    need(row.get('status')=='failed' and row.get('pid')==177134 and row.get('finished') and
         row.get('completed')==[] and row.get('stage') is None and
         'No space left on device' in row.get('error','') and '.arch02_team_lock' in row['error'] and
         not Path('/proc/177134').exists(),'C32 did not exit before all child work')
    need(not list((INITIAL/'process_ledger').glob('child_*.json')),'C32 had accepted child work')


def main():
    import hashlib
    def sha(path):
        h=hashlib.sha256()
        with Path(path).open('rb') as f:
            for b in iter(lambda:f.read(4*1024**2),b''):h.update(b)
        return h.hexdigest()
    need(os.name=='posix' and ROOT.resolve()==ROOT and not OUT.exists(),'Wrong or repeated operation')
    need(sha(DEPENDENCY)==DEPENDENCY_SHA,'Process-inspection helper changed')
    base=load('b0_process_helpers19',DEPENDENCY)  # Its cleanup main is never called.
    need(sha(base.PREFLIGHT)==base.PREFLIGHT_SHA,'Read-only archive helper changed')
    checked=load('b0_archive_helpers19',base.PREFLIGHT)
    need(sha(base.BUNDLE/'manifest.json')==base.MANIFEST_SHA,'Frozen helper bundle changed')
    mf=read(base.BUNDLE/'manifest.json')['files']
    for name in ('n1_archive_runtime.py','n1_paths.py','partition_synth_contract.py'):
        rel='workspaces/arch03/scripts/'+name
        need(sha(base.BUNDLE/rel)==mf[rel],'Changed process-inspection dependency')
    sys.path.insert(0,str(base.BUNDLE/'workspaces/arch03/scripts'))
    import n1_archive_runtime as archive
    project=checked.PROJECT;lock=project.parent/'.arch02_team_lock'
    initial_guard(sha);terminal=base.stopped()
    need(not (ROOT/'light-light126-c32-61246bb/runs/c32_initial02').exists(), 'C32 initial02 already exists')
    fixed={checked.BACKUP/'manifest.json':checked.MANIFEST_SHA,
           checked.BACKUP/'receipt.json':checked.RECEIPT_SHA,
           checked.BACKUP/'completed-evidence.tar.gz':checked.ARCHIVE_SHA,
           checked.PRIOR:checked.PRIOR_SHA,INITIAL/'state.json':INITIAL_SHA,
           DEPENDENCY:DEPENDENCY_SHA,base.PREFLIGHT:base.PREFLIGHT_SHA}
    fixed.update({Path(p):h for p,h in terminal.items()})
    stamps={str(p):checked.stamp(p) for p in fixed}
    need(all(sha(p)==h and checked.stamp(p)==stamps[str(p)] for p,h in fixed.items()),'Retained archive/proof changed')
    prior=read(checked.PRIOR)
    need(prior['archive_sha256']==checked.ARCHIVE_SHA and
         prior['all_archive_members_readback_verified']==63653 and
         prior['all_archive_bytes_readback_verified']==7006124866,'Missing complete readback proof')
    manifest=read(checked.BACKUP/'manifest.json')
    need(manifest['source_root']==str(project),'Wrong archived project')
    index={v['path']:v for v in manifest['files']}
    need(len(index)==len(manifest['files']),'Duplicate archive path')
    rows=[];files=[];groups={k:[0,0] for k in GROUPS}
    for rel,v in sorted(index.items()):
        if not selected(rel):continue
        p=project/rel
        if not p.exists():continue
        need(p.resolve()==p and project in p.parents,'Wrong exact generated-file path')
        stamp=checked.stamp(p)
        need(stamp['bytes']==v['bytes'] and sha(p)==v['sha256'] and checked.stamp(p)==stamp,'Archived duplicate differs')
        rows.append(dict(path=rel,bytes=v['bytes'],sha256=v['sha256'],stamp=stamp));files.append(p)
        g=groups[rel[len(PREFIX):].split('/')[0]];g[0]+=1;g[1]+=v['bytes']
    need(all(tuple(groups[k])==v for k,v in GROUPS.items()) and len(rows)==1852 and
         sum(v['bytes'] for v in rows)==98453710,'Exact five-run candidate count or bytes changed')
    watch_roots=[project/PREFIX/group for group in GROUPS]
    process=base.idle(archive,lock,watch_roots);initial_guard(sha)
    need(base.stopped()==terminal and all(checked.stamp(p)==stamps[str(p)] for p in fixed),'Evidence changed')
    OUT.mkdir(mode=0o700)
    state=dict(status='intent_verified',files=rows,removed_files=0,removed_bytes=0,
        source_sha256=sha(__file__),original_c32_failed_state_sha256=INITIAL_SHA,
        retained_archive=str(checked.BACKUP/'completed-evidence.tar.gz'),archive_sha256=checked.ARCHIVE_SHA,
        full_readback_proof_sha256=checked.PRIOR_SHA,process_observation=process,
        free_before=shutil.disk_usage(str(project)).free,protected_T80_modified=False,old8_modified=False,
        p80_modified=False,c80_modified=False,backup_modified=False,
        restore='Extract these exact generated/compiled members from the retained archive into a fresh directory, verify hashes, then restore reviewed original paths.')
    archive.save(OUT/'intent.json',state)
    try:
        with (OUT/'removal_journal.jsonl').open('x') as journal:
            for number,(v,p) in enumerate(zip(rows,files)):
                if number%64==0:
                    base.idle(archive,lock,watch_roots);initial_guard(sha)
                    need(base.stopped()==terminal and all(checked.stamp(q)==stamps[str(q)] for q in fixed),'Evidence changed')
                need(checked.stamp(p)==v['stamp'] and sha(p)==v['sha256'],'Duplicate changed before removal')
                journal.write(json.dumps(dict(action='remove_intent',**v),sort_keys=True)+'\n')
                journal.flush();os.fsync(journal.fileno())
                need(not lock.exists(),'Team lock appeared; preserve remaining files')
                p.unlink();archive.sync_dir(p.parent)
                state['removed_files']+=1;state['removed_bytes']+=v['bytes']
                journal.write(json.dumps(dict(action='removed',path=v['path']))+'\n')
                journal.flush();os.fsync(journal.fileno())
                if (number+1)%64==0:archive.save(OUT/'state.json',state)
        need(all(not p.exists() for p in files) and all(checked.stamp(p)==stamps[str(p)] for p in fixed),'Post-cleanup mismatch')
        state.update(status='verified_duplicates_removed_backup_retained',finished=archive.now(),
            free_after=shutil.disk_usage(str(project)).free,journal_sha256=sha(OUT/'removal_journal.jsonl'))
        archive.save(OUT/'state.json',state)
        print('B0_DUPLICATES20_COMPLETE',state['removed_bytes'],sha(OUT/'state.json'),flush=True)
        # Release completed duplicates and immediately attempt the already-pinned
        # fresh qualification. No second cleanup pass or old queue restart.
        tool=ROOT/'ops-recovery02/C32_QUALIFICATION02_LAUNCH_20261116.py'
        need(sha(tool)=='5a74620bc3a76bf3285f49274a224af0f3767f0287be0d5a9871af29413c917d','Changed initial02 launcher')
        manifest=read(ROOT/'light-light126-c32-61246bb.prepared.json')['manifest_sha256']
        recovery=sha(ROOT/'b0_archived_duplicate_reports19/state.json')
        command=[sys.executable,'-B',str(tool),'--manifest-sha256',manifest,'--cleanup-receipt-sha256',recovery]
        result=subprocess.call(command)
        followup=dict(command=command,returncode=result,cleanup_state_sha256=sha(OUT/'state.json'))
        receipt=ROOT/'c32_initial02_launch.json'
        if receipt.exists():followup['launch_receipt_sha256']=sha(receipt)
        archive.save(OUT/'followup.json',followup)
        need(result==0,'Fresh queue preflight failed; cleanup complete, do not repeat deletion')
    except BaseException as exc:
        if state.get('status')!='verified_duplicates_removed_backup_retained':state['status']='failed_preserved'
        state.update(followup_or_cleanup_error=str(exc),finished=archive.now())
        archive.save(OUT/'state.json',state);raise


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--execute-five-run-archived-duplicates',action='store_true',required=True)
    p.parse_args();main()
