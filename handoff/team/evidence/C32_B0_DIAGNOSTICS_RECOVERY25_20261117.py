"""Remove twelve fully archived B0 duplicate timing diagnostics, then start C32 finish03.

No source/netlist/simulation log/summary/activity/backup is removed. The original failed
finish02 must have exited before any child. Exact paths and byte totals only.
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
BUNDLE=ROOT/'light-light126-c32-91135f6'
OUT=ROOT/'b0_archived_diagnostics25'
INITIAL_SHA='37e1279f0c165b6fb50493c4d87edb2a994e159a90e22e48b92c41ef8ab500c0'
FAILED_SHA='c502d28a5d4aee1689abe597b40465f42a2d98c17fb9468b28b3ecd7423eccec'
MANIFEST='d877234086f471acb3c7f4ea0c69bb280606d6bbb45fdd212e8bf30366b316c7'
DEPENDENCY=Path('/tmp/s4_21usr_c80_20261116_1245/ops-b0-cleanup16-c8c730d/C80_B0_DUPLICATES_CLEANUP16_20261116.py')
DEPENDENCY_SHA='0e98728332e0ba048142231f414322dc3aaf21e287b3bde0bc4121124c976441'
LAUNCH=ROOT/'c32_finish03_from_initial03.py'
LAUNCH_SHA='291bcfe3ea26d23fe58f8baea34511c67b2c353cb9807f8cd3135f30fac13e27'
PREFIX='bundles/light-light126-systolic-b-v3-20261112_114355-ced0e139a01e/runs/'
SELECTED={PREFIX+'systolic_b_power_final01_power_l%02d/systolic_b_power/disabled_timing.rpt'%i:13773448 for i in range(1,13)}


def need(ok,message):
    if not ok:raise ValueError(message)


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for b in iter(lambda:stream.read(4*1024**2),b''):h.update(b)
    return h.hexdigest()


def read(path):return json.loads(Path(path).read_text())


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,str(path))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def selected(path,size):return path in SELECTED and type(size) is int and SELECTED[path]==size


def queues_stopped():
    initial=BUNDLE/'runs/c32_initial03/state.json'
    failed=BUNDLE/'runs/c32_finish02/state.json'
    need(sha(initial)==INITIAL_SHA and sha(failed)==FAILED_SHA,'C32 terminal identity changed')
    a=read(initial);b=read(failed)
    need(a['status']=='qualification_ready_gate_power_pending' and a.get('finished') and
         a['pid']==238916 and not Path('/proc/238916').exists(),'Initial03 still active')
    need(b['status']=='failed' and b.get('finished') and b['completed']==[] and b.get('stage') is None and
         b['pid']==304144 and not Path('/proc/304144').exists() and
         'No space left on device' in b['error'] and '.arch02_team_lock' in b['error'],
         'Finish02 did not exit before child work on ENOSPC')
    need(not list((failed.parent/'process_ledger').glob('child_*.json')),'Finish02 had child work')
    need(not (BUNDLE/'runs/c32_finish03').exists(),'Finish02 already exists; do not clean or repeat')


def main():
    need(os.name=='posix' and ROOT.resolve()==ROOT and not OUT.exists(),'Wrong or repeated recovery25')
    need(sha(DEPENDENCY)==DEPENDENCY_SHA and sha(LAUNCH)==LAUNCH_SHA,'Helper changed')
    base=load('c32_recovery25_idle_helpers',DEPENDENCY)  # Never call old cleanup main.
    need(sha(base.PREFLIGHT)==base.PREFLIGHT_SHA,'Archive preflight changed')
    checked=load('c32_recovery25_archive_helpers',base.PREFLIGHT)
    need(sha(base.BUNDLE/'manifest.json')==base.MANIFEST_SHA,'Frozen helper bundle changed')
    index=read(base.BUNDLE/'manifest.json')['files']
    for n in ('n1_archive_runtime.py','n1_paths.py','partition_synth_contract.py'):
        rel='workspaces/arch03/scripts/'+n;need(sha(base.BUNDLE/rel)==index[rel],'Inspection helper changed')
    sys.path.insert(0,str(base.BUNDLE/'workspaces/arch03/scripts'))
    import n1_archive_runtime as archive
    project=checked.PROJECT;lock=project.parent/'.arch02_team_lock'
    queues_stopped()
    fixed={checked.BACKUP/'manifest.json':checked.MANIFEST_SHA,
           checked.BACKUP/'receipt.json':checked.RECEIPT_SHA,
           checked.BACKUP/'completed-evidence.tar.gz':checked.ARCHIVE_SHA,
           checked.PRIOR:checked.PRIOR_SHA,DEPENDENCY:DEPENDENCY_SHA,LAUNCH:LAUNCH_SHA,
           BUNDLE/'manifest.json':MANIFEST,
           BUNDLE/'runs/c32_initial03/state.json':INITIAL_SHA,
           BUNDLE/'runs/c32_finish02/state.json':FAILED_SHA}
    stamps={str(p):checked.stamp(p) for p in fixed}
    need(all(sha(p)==h and checked.stamp(p)==stamps[str(p)] for p,h in fixed.items()),'Archive or proof changed')
    prior=read(checked.PRIOR)
    need(prior['archive_sha256']==checked.ARCHIVE_SHA and prior['all_archive_members_readback_verified']==63653 and
         prior['all_archive_bytes_readback_verified']==7006124866,'Missing complete archive readback proof')
    manifest=read(checked.BACKUP/'manifest.json')
    need(manifest['source_root']==str(project),'Wrong archive root')
    index={r['path']:r for r in manifest['files']};need(len(index)==len(manifest['files']),'Duplicate paths')
    rows=[];files=[]
    for name,size in sorted(SELECTED.items()):
        need(selected(name,size) and index[name]['bytes']==size,'Exact selected seed changed')
        p=project/name;st=checked.stamp(p)
        need(p.resolve()==p and project in p.parents and st['bytes']==size and
             sha(p)==index[name]['sha256'] and checked.stamp(p)==st,'Seed differs from retained archive')
        rows.append(dict(path=name,bytes=size,sha256=index[name]['sha256'],stamp=st));files.append(p)
    need(len(rows)==12 and sum(v['bytes'] for v in rows)==165281376,'Wrong scope')
    obs=base.idle(archive,lock,files);queues_stopped()
    need(all(checked.stamp(p)==stamps[str(p)] for p in fixed),'Inputs changed')
    OUT.mkdir(mode=0o700)
    state=dict(status='intent_verified',files=rows,removed_files=0,removed_bytes=0,
        source_sha256=sha(__file__),archive=str(checked.BACKUP/'completed-evidence.tar.gz'),
        archive_sha256=checked.ARCHIVE_SHA,readback_proof_sha256=checked.PRIOR_SHA,
        terminal_failed_finish02_sha256=FAILED_SHA,process_observation=obs,
        free_before=shutil.disk_usage(str(project)).free,
        protected_T80_modified=False,old8_modified=False,p80_modified=False,c80_modified=False,
        backup_modified=False,final_netlist_modified=False,
        restore='Read the exact twelve disabled_timing.rpt members from the retained verified archive into fresh paths and verify hashes.')
    archive.save(OUT/'intent.json',state)
    with (OUT/'removal_journal.jsonl').open('x') as journal:
        for row,p in zip(rows,files):
            base.idle(archive,lock,files);queues_stopped()
            need(all(checked.stamp(q)==stamps[str(q)] for q in fixed),'Retained evidence changed')
            need(checked.stamp(p)==row['stamp'] and sha(p)==row['sha256'],'Seed changed before remove')
            journal.write(json.dumps(dict(action='remove_intent',**row),sort_keys=True)+'\n')
            journal.flush();os.fsync(journal.fileno());need(not lock.exists(),'Team lock appeared')
            p.unlink();archive.sync_dir(p.parent)
            state['removed_files']+=1;state['removed_bytes']+=row['bytes']
            journal.write(json.dumps(dict(action='removed',path=row['path']))+'\n')
            journal.flush();os.fsync(journal.fileno());archive.save(OUT/'state.json',state)
    need(all(not p.exists() for p in files) and all(checked.stamp(p)==stamps[str(p)] for p in fixed),'Post-check failed')
    state.update(status='verified_duplicates_removed_archive_retained',finished=archive.now(),
        free_after=shutil.disk_usage(str(project)).free,journal_sha256=sha(OUT/'removal_journal.jsonl'))
    archive.save(OUT/'state.json',state)
    print('RECOVERY25_COMPLETE',state['removed_bytes'],sha(OUT/'state.json'),flush=True)
    need(sha(LAUNCH)==LAUNCH_SHA,'Finish02 launcher changed')
    command=[sys.executable,'-B',str(LAUNCH),'--manifest-sha256',MANIFEST,
             '--initial-state-sha256',INITIAL_SHA,'--failed-state-sha256',FAILED_SHA]
    with (OUT/'finish03_launcher.log').open('xb') as stream:
        code=subprocess.call(command,stdout=stream,stderr=subprocess.STDOUT)
    result=dict(returncode=code,command=command,cleanup_state_sha256=sha(OUT/'state.json'))
    p=ROOT/'c32_finish03_launch.json'
    if p.exists():result['launch_receipt_sha256']=sha(p);result['pid']=read(p)['pid']
    archive.save(OUT/'followup.json',result)
    print('RECOVERY25_FOLLOWUP',result,flush=True)
    need(code==0,'Cleanup completed; inspect new finish launch, never repeat deletion')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--execute-twelve-archived-diagnostics',action='store_true',required=True)
    p.parse_args();main()
