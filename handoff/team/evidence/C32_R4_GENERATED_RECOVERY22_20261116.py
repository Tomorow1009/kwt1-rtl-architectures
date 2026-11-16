"""Recover only archive21's verified generated R4 input duplicates.

Preserves all task outputs, results, source, logs, netlists and activities.
Never touches T80, old8, P80/C80 or an existing backup. Staged archive stays
in private /tmp; a separately verified persistent copy follows recovery.
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
ROOT=Path('/tmp/s4_21usr_c32_20261116_2010')
HELPER=ROOT/'r4_archive21_fixed.py'
HELPER_SHA='2a28e61f85792f4f0d2fc2655950feaeb34a3a9e728ca108042f982dace233c4'
OUT=ROOT/'r4_generated_recovery22'
INITIAL_SHA='42ffa16c397ab474753eb1cc9ef5617c2bf226bbee1c318f8e752fd5416aa674'


def need(ok,message):
    if not ok:raise ValueError(message)


def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(4*1024**2),b''):h.update(b)
    return h.hexdigest()


def read(p):return json.loads(Path(p).read_text())


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive-receipt-sha256',required=True)
    parser.add_argument('--execute-verified-generated-duplicates',action='store_true',required=True)
    args=parser.parse_args()
    need(os.name=='posix' and ROOT.resolve()==ROOT and ROOT.stat().st_mode&0o777==0o700 and
         not OUT.exists(),'Use a fresh server recovery operation')
    need(sha(HELPER)==HELPER_SHA,'Staged-archive helper changed')
    spec=importlib.util.spec_from_file_location('r4_archive_scope21',str(HELPER))
    h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
    need(sha(h.BASE)==h.BASE_SHA,'Process helper changed')
    base=h.load('r4_recovery_process22',h.BASE)
    need(sha(base.BUNDLE/'manifest.json')==base.MANIFEST_SHA,'Helper bundle changed')
    mf=read(base.BUNDLE/'manifest.json')['files']
    for name in ('n1_archive_runtime.py','n1_paths.py','partition_synth_contract.py'):
        rel='workspaces/arch03/scripts/'+name
        need(sha(base.BUNDLE/rel)==mf[rel],'Inspection dependency changed')
    sys.path.insert(0,str(base.BUNDLE/'workspaces/arch03/scripts'))
    import n1_archive_runtime as archive
    launch=read(ROOT/'r4_archive21_fixed_launch.json')
    need(type(launch['pid']) is int and not Path('/proc/%d'%launch['pid']).exists(),'Archive worker not exited')
    receipt=h.OUT/'receipt.json'
    need(len(args.archive_receipt_sha256)==64 and sha(receipt)==args.archive_receipt_sha256,'Wrong readback receipt')
    proof=read(receipt);manifest=h.OUT/'manifest.json';packed=h.OUT/'generated-inputs.tar.gz'
    need(proof['status']=='verified_staged_archive_source_preserved' and
         proof['source_deleted'] is False and proof['source_modified'] is False and
         proof['archive']==str(packed) and sha(manifest)==proof['manifest_sha256'] and
         packed.stat().st_size==proof['archive_bytes'] and sha(packed)==proof['archive_sha256'],
         'Staged full-readback proof or archive changed')
    data=read(manifest);rows=data['files']
    need(data['source_root']==str(h.RUN) and data['source_sha256']==HELPER_SHA and
         len(rows)==proof['members_verified'] and sum(v['bytes'] for v in rows.values())==proof['source_bytes'] and
         0<proof['source_bytes']<4*1024**3 and all(h.selected(n) for n in rows),'Wrong generated-input scope')
    need(len({n.split('/')[1] for n in rows})==1200,'Incomplete case set')
    initial=ROOT/'light-light126-c32-61246bb/runs/c32_initial01/state.json'
    need(sha(initial)==INITIAL_SHA and not Path('/proc/177134').exists() and
         not (initial.parent.parent/'c32_initial02').exists(),'C32 is not a zero-work stopped queue')
    fixed=dict(data['protected_metadata'],**data['case_receipts'])
    fixed.update({str(manifest):proof['manifest_sha256'],str(receipt):args.archive_receipt_sha256,
                  str(packed):proof['archive_sha256'],str(HELPER):HELPER_SHA,str(initial):INITIAL_SHA})
    stamps={p:h.stamp(p) for p in fixed}
    need(all(sha(p)==v for p,v in fixed.items()),'Retained metadata changed')
    lock=h.PROJECT.parent/'.arch02_team_lock'
    obs=base.idle(archive,lock,[h.RUN])
    for name,v in rows.items():
        p=h.RUN/name
        need(p.resolve()==p and h.RUN in p.parents and h.stamp(p)==v['stamp'] and
             sha(p)==v['sha256'] and h.stamp(p)==v['stamp'],'Generated input differs from verified archive')
    base.idle(archive,lock,[h.RUN]);OUT.mkdir(mode=0o700)
    state=dict(status='verified_staged_duplicates_removing',source_sha256=sha(__file__),
        archive_receipt_sha256=args.archive_receipt_sha256,archive=str(packed),
        archive_sha256=proof['archive_sha256'],files=len(rows),source_bytes=proof['source_bytes'],
        removed_files=0,removed_bytes=0,free_before=shutil.disk_usage(str(h.PROJECT)).free,
        process_observation=obs,protected_T80_modified=False,old8_modified=False,
        p80_modified=False,c80_modified=False,results_modified=False,
        restore='Read exact members from retained gzip tar, verify manifest SHA/bytes, restore named inputs only.')
    archive.save(OUT/'state.json',state)
    try:
        names=sorted(rows)
        with (OUT/'removal_journal.jsonl').open('x') as journal:
            for start in range(0,len(names),128):
                group=names[start:start+128]
                base.idle(archive,lock,[h.RUN])
                need(all(h.stamp(p)==v for p,v in stamps.items()),'Retained evidence changed')
                for name in group:
                    p=h.RUN/name;v=rows[name]
                    need(h.stamp(p)==v['stamp'] and sha(p)==v['sha256'],'Duplicate changed before removal')
                journal.write(json.dumps(dict(action='batch_remove_intent',paths=group))+'\n')
                journal.flush();os.fsync(journal.fileno())
                for name in group:
                    need(not lock.exists(),'New team lock; stop before more deletion')
                    p=h.RUN/name;need(h.stamp(p)==rows[name]['stamp'],'Source changed after intent')
                    p.unlink();state['removed_files']+=1;state['removed_bytes']+=rows[name]['bytes']
                for parent in {str((h.RUN/n).parent) for n in group}:archive.sync_dir(parent)
                journal.write(json.dumps(dict(action='batch_removed',paths=group))+'\n')
                journal.flush();os.fsync(journal.fileno());archive.save(OUT/'state.json',state)
                if start%4096==0:print('R4_RECOVERY22_REMOVED',state['removed_files'],state['removed_bytes'],flush=True)
        need(all(not (h.RUN/n).exists() for n in rows),'Not all selected duplicates removed')
        need(all(sha(p)==v for p,v in fixed.items()),'Retained archive/metadata changed after removal')
        state.update(status='verified_duplicates_removed_staged_archive_retained',finished=archive.now(),
            free_after=shutil.disk_usage(str(h.PROJECT)).free,journal_sha256=sha(OUT/'removal_journal.jsonl'))
        archive.save(OUT/'state.json',state)
        # Only the generated duplicate inputs were removed. Persist a second
        # complete archive copy before attempting any C32 EDA work.
        target=h.PROJECT/'backups/r4-generated-inputs-20261116_2135'
        need(not target.exists() and shutil.disk_usage(str(h.PROJECT)).free>=
             proof['archive_bytes']+manifest.stat().st_size+64*1024**2,'No room for persistent copy; staged archive retained')
        target.mkdir(mode=0o700)
        for p in (packed,manifest,receipt):
            dest=target/p.name
            with p.open('rb') as src,dest.open('xb') as dst:
                shutil.copyfileobj(src,dst,4*1024**2);dst.flush();os.fsync(dst.fileno())
            need(dest.stat().st_size==p.stat().st_size and sha(dest)==sha(p),'Persistent copy differs')
        archive.sync_dir(target)
        archive.save(OUT/'persistent_copy.json',dict(status='verified',directory=str(target),
            archive_sha256=proof['archive_sha256'],manifest_sha256=proof['manifest_sha256'],
            staged_archive_preserved=True,cleanup_state_sha256=sha(OUT/'state.json')))
        print('R4_RECOVERY22_PERSISTED',sha(OUT/'state.json'),str(target),flush=True)
        tool=ROOT/'ops-recovery02/C32_QUALIFICATION02_LAUNCH_20261116.py'
        need(sha(tool)=='5a74620bc3a76bf3285f49274a224af0f3767f0287be0d5a9871af29413c917d','Changed C32 launcher')
        command=[sys.executable,'-B',str(tool),'--manifest-sha256',
            read(ROOT/'light-light126-c32-61246bb.prepared.json')['manifest_sha256'],
            '--cleanup-receipt-sha256',sha(ROOT/'b0_archived_duplicate_reports19/state.json')]
        result=subprocess.call(command)
        archive.save(OUT/'followup.json',dict(command=command,returncode=result))
        need(result==0,'C32 preflight failed after cleanup; do not repeat removal')
    except BaseException as exc:
        state.update(error=str(exc),stopped=archive.now());archive.save(OUT/'state.json',state);raise


if __name__=='__main__':main()
