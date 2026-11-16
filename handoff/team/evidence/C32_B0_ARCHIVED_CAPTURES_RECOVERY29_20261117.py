"""Release only durably archived old B0 task.csv duplicates until query starts.

The retained full archive contains every output byte. No T80/old8 file, final
netlist, summary, simulation log, source, activity or backup is removed.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import sys
sys.dont_write_bytecode=True
ROOT=Path('/tmp/s4_21usr_c32_20261116_2010')
DEP=ROOT/'c32_recovery26.py'
DEP_SHA='0be4c3b63ee1507efaded7db45ff7d5c03c06f788f3b2efc97340b88054eb6ad'
PREFIX='bundles/light-light126-systolic-b-v3-20261112_114355-ced0e139a01e/runs/systolic_b_final02_final1200/systolic_b_batch/'


def main():
    if hashlib.sha256(DEP.read_bytes()).hexdigest()!=DEP_SHA:raise ValueError('Guard dependency changed')
    spec=importlib.util.spec_from_file_location('recovery29_guard',str(DEP))
    d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
    need,sha,read=d.need,d.sha,d.read;out=ROOT/'b0_archived_captures29'
    need(os.name=='posix' and ROOT.resolve()==ROOT and not out.exists(),'Wrong/repeated recovery29')
    need(sha(d.HELPER)==d.HELPER_SHA,'Idle helper changed');base=d.load('recovery29_idle',d.HELPER)
    need(sha(base.PREFLIGHT)==base.PREFLIGHT_SHA,'Archive helper changed')
    checked=d.load('recovery29_archive',base.PREFLIGHT)
    need(sha(base.BUNDLE/'manifest.json')==base.MANIFEST_SHA,'Frozen helper bundle changed')
    index=read(base.BUNDLE/'manifest.json')['files']
    for name in ('n1_archive_runtime.py','n1_paths.py','partition_synth_contract.py'):
        rel='workspaces/arch03/scripts/'+name;need(sha(base.BUNDLE/rel)==index[rel],'Inspection helper changed')
    sys.path.insert(0,str(base.BUNDLE/'workspaces/arch03/scripts'));import n1_archive_runtime as archive
    project=checked.PROJECT;lock=project.parent/'.arch02_team_lock'
    manifest=read(checked.BACKUP/'manifest.json');index={r['path']:r for r in manifest['files']}
    need(manifest['source_root']==str(project) and len(index)==len(manifest['files']),'Wrong archive source')
    summary=project/(PREFIX+'summary.json')
    terminal=summary.parent.parent/'state.json'
    fixed={checked.BACKUP/'manifest.json':checked.MANIFEST_SHA,checked.BACKUP/'receipt.json':checked.RECEIPT_SHA,
        checked.BACKUP/'completed-evidence.tar.gz':checked.ARCHIVE_SHA,checked.PRIOR:checked.PRIOR_SHA,
        DEP:DEP_SHA,summary:index[str(summary.relative_to(project))]['sha256'],
        terminal:index[str(terminal.relative_to(project))]['sha256']}
    stamps={str(p):checked.stamp(p) for p in fixed}
    need(all(sha(p)==h and checked.stamp(p)==stamps[str(p)] for p,h in fixed.items()),'Archive or final batch changed')
    prior=read(checked.PRIOR)
    need(prior['archive_sha256']==checked.ARCHIVE_SHA and prior['all_archive_members_readback_verified']==63653
         and prior['all_archive_bytes_readback_verified']==7006124866,'Missing complete archive readback')
    batch=read(summary);stage=read(terminal)['stages']['systolic_b_batch']
    need(batch['status']=='passed' and batch['tasks']==1200 and batch['checked_outputs']==30412800 and
         batch['failed']==0 and batch['asic_cpu_verified'] and batch['cpu_executed'] and
         stage['status']=='passed' and stage['summary_sha256']==sha(summary),'Not the completed real B0 batch')
    keys={r['key'] for r in batch['cases']};need(len(keys)==len(batch['cases'])==1200,'Repeated B0 task')
    selected={n:r for n,r in index.items() if n.startswith(PREFIX+'cases/') and n.endswith('/task.csv')}
    need(len(selected)==1200 and sum(r['bytes'] for r in selected.values())==385483006 and
         {n[len(PREFIX+'cases/'):].split('/')[0] for n in selected}==keys,'Wrong exact capture set')
    rows=[];files=[]
    for name,row in sorted(selected.items()):
        need(re.fullmatch(r'cases/sample_[0-9]{6}_layer_[0-9]{2}/task\.csv',name[len(PREFIX):]),'Unexpected capture path')
        p=project/name;st=checked.stamp(p)
        need(p.resolve()==p and project in p.parents and st['bytes']==row['bytes'] and
             sha(p)==row['sha256'] and checked.stamp(p)==st,'Capture differs from retained archive')
        rows.append(dict(path=name,bytes=row['bytes'],sha256=row['sha256'],stamp=st));files.append(p)
    proc=Path('/proc/57941');need(proc.exists() and b'/ops-c32-drc02-f14498f/inspect02.py\x00' in
        (proc/'cmdline').read_bytes(),'Expected waiting query changed')
    need(not (ROOT/'light-light126-c32-91135f6/runs/c32_drc_inspect02').exists(),'Query already started; no cleanup needed')
    obs=base.idle(archive,lock,files);out.mkdir(mode=0o700)
    state=dict(status='intent_verified',files=rows,removed_files=0,removed_bytes=0,source_sha256=sha(__file__),
        archive=str(checked.BACKUP/'completed-evidence.tar.gz'),archive_sha256=checked.ARCHIVE_SHA,
        readback_proof_sha256=checked.PRIOR_SHA,process_observation=obs,free_before=shutil.disk_usage(str(project)).free,
        protected_T80_modified=False,old8_modified=False,p80_modified=False,c80_modified=False,
        final_netlist_modified=False,summary_or_log_modified=False,backup_modified=False,queue_restarted=False,
        restore='Read the exact task.csv members listed in removal_journal.jsonl from the retained archive into fresh paths and verify SHA/size before restoring.')
    archive.save(out/'intent.json',state)
    try:
        with (out/'removal_journal.jsonl').open('x') as journal:
            for row,p in zip(rows,files):
                if lock.exists():break
                need(all(checked.stamp(q)==stamps[str(q)] for q in fixed) and checked.stamp(p)==row['stamp'] and
                     sha(p)==row['sha256'],'Capture or retained proof changed before removal')
                journal.write(json.dumps(dict(action='remove_intent',**row),sort_keys=True)+'\n');journal.flush();os.fsync(journal.fileno())
                if lock.exists():break
                p.unlink();archive.sync_dir(p.parent);state['removed_files']+=1;state['removed_bytes']+=row['bytes']
                journal.write(json.dumps(dict(action='removed',path=row['path']))+'\n');journal.flush();os.fsync(journal.fileno())
        need(all(checked.stamp(q)==stamps[str(q)] for q in fixed),'Retained evidence changed')
        state.update(status=('verified_duplicates_removed_archive_retained' if state['removed_files']==1200 else
            'query_started_remaining_captures_preserved'),finished=archive.now(),free_after=shutil.disk_usage(str(project)).free,
            journal_sha256=sha(out/'removal_journal.jsonl'))
    except BaseException as error:
        state.update(status='stopped_preserved',error=str(error),finished=archive.now());raise
    finally:archive.save(out/'state.json',state)
    print('RECOVERY29_COMPLETE',state['removed_files'],state['removed_bytes'],sha(out/'state.json'),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--execute-verified-archived-captures',action='store_true',required=True)
    p.parse_args();main()
