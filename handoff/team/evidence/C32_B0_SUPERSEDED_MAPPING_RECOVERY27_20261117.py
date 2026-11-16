"""Release five exact archived intermediate B0 mapping duplicates.

Final B0 DRC06, all summaries, R4 SAIF method data, T80, old8 and backups stay.
No queue restart: the existing C32 query acquires the original lock itself.
"""
import argparse
import os
from pathlib import Path
import shutil
import sys
import importlib.util

sys.dont_write_bytecode=True
ROOT=Path('/tmp/s4_21usr_c32_20261116_2010')
DEP=ROOT/'c32_recovery26.py'
DEP_SHA='0be4c3b63ee1507efaded7db45ff7d5c03c06f788f3b2efc97340b88054eb6ad'
PREFIX='bundles/light-light126-systolic-b-v3-20261112_114355-ced0e139a01e/runs/'
SELECTED={PREFIX+'systolic_b_v3_drc04/systolic_b_synth/mapped.v':37745009,
          PREFIX+'systolic_b_v3_drc04/systolic_b_synth/mapped.ddc':33112064,
          PREFIX+'systolic_b_v3_drc05/systolic_b_synth/mapped.v':37781586,
          PREFIX+'systolic_b_v3_drc05/systolic_b_synth/mapped.ddc':33144832,
          PREFIX+'systolic_b_v3_drc03/systolic_b_synth/repair_seed.ddc':32940032}


def main():
    import hashlib
    assert hashlib.sha256(DEP.read_bytes()).hexdigest()==DEP_SHA
    spec=importlib.util.spec_from_file_location('recovery27_base',str(DEP))
    d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
    need,sha,read=d.need,d.sha,d.read
    out=ROOT/'b0_archived_intermediates27'
    need(os.name=='posix' and ROOT.resolve()==ROOT and not out.exists(),'Wrong/repeated recovery27')
    need(sha(d.HELPER)==d.HELPER_SHA,'Idle helper changed');base=d.load('recovery27_idle',d.HELPER)
    need(sha(base.PREFLIGHT)==base.PREFLIGHT_SHA,'Archive helper changed')
    checked=d.load('recovery27_archive',base.PREFLIGHT)
    need(sha(base.BUNDLE/'manifest.json')==base.MANIFEST_SHA,'Frozen helper bundle changed')
    index=read(base.BUNDLE/'manifest.json')['files']
    for name in ('n1_archive_runtime.py','n1_paths.py','partition_synth_contract.py'):
        rel='workspaces/arch03/scripts/'+name;need(sha(base.BUNDLE/rel)==index[rel],'Inspection helper changed')
    sys.path.insert(0,str(base.BUNDLE/'workspaces/arch03/scripts'));import n1_archive_runtime as archive
    project=checked.PROJECT;lock=project.parent/'.arch02_team_lock'
    manifest=read(checked.BACKUP/'manifest.json');index={r['path']:r for r in manifest['files']}
    need(manifest['source_root']==str(project) and len(index)==len(manifest['files']),'Wrong archive source')
    power=project/(PREFIX+'systolic_b_power_final01_power_l01/systolic_b_power/summary.json')
    final=project/(PREFIX+'systolic_b_v3_drc06/systolic_b_synth/summary.json')
    fixed={checked.BACKUP/'manifest.json':checked.MANIFEST_SHA,checked.BACKUP/'receipt.json':checked.RECEIPT_SHA,
        checked.BACKUP/'completed-evidence.tar.gz':checked.ARCHIVE_SHA,checked.PRIOR:checked.PRIOR_SHA,
        DEP:DEP_SHA,power:index[str(power.relative_to(project))]['sha256'],final:index[str(final.relative_to(project))]['sha256']}
    stamps={str(p):checked.stamp(p) for p in fixed}
    need(all(sha(p)==h and checked.stamp(p)==stamps[str(p)] for p,h in fixed.items()),'Archive or final evidence changed')
    need(read(power)['synthesis_run']==str(final.parent) and read(power)['synthesis_summary_sha256']==sha(final),
         'B0 final synthesis is not DRC06; stop')
    prior=read(checked.PRIOR)
    need(prior['archive_sha256']==checked.ARCHIVE_SHA and prior['all_archive_members_readback_verified']==63653
         and prior['all_archive_bytes_readback_verified']==7006124866,'Missing complete archive readback')
    rows=[];files=[]
    for name,size in sorted(SELECTED.items()):
        p=project/name;st=checked.stamp(p)
        need(p.resolve()==p and project in p.parents and index[name]['bytes']==size==st['bytes']
             and sha(p)==index[name]['sha256'] and checked.stamp(p)==st,'Intermediate differs from archive')
        files.append(p);rows.append(dict(path=name,bytes=size,sha256=index[name]['sha256'],stamp=st))
    need(len(files)==5 and sum(r['bytes'] for r in rows)==174723523,'Wrong exact cleanup scope')
    d.waiting();obs=base.idle(archive,lock,files);d.waiting()
    out.mkdir(mode=0o700)
    state=dict(status='intent_verified',files=rows,removed_files=0,removed_bytes=0,source_sha256=sha(__file__),
        archive=str(checked.BACKUP/'completed-evidence.tar.gz'),archive_sha256=checked.ARCHIVE_SHA,
        readback_proof_sha256=checked.PRIOR_SHA,process_observation=obs,free_before=shutil.disk_usage(str(project)).free,
        protected_T80_modified=False,old8_modified=False,p80_modified=False,c80_modified=False,
        final_B0_netlist_modified=False,R4_method_activity_modified=False,backup_modified=False,queue_restarted=False,
        restore='Restore only the five named intermediate members from the verified archive into fresh paths and verify all hashes.')
    archive.save(out/'intent.json',state)
    for row,p in zip(rows,files):
        if lock.exists():break
        base.idle(archive,lock,files)
        need(all(checked.stamp(q)==stamps[str(q)] for q in fixed) and checked.stamp(p)==row['stamp'] and
             sha(p)==row['sha256'] and not lock.exists(),'Source, backup or lock changed before remove')
        archive.save(out/('remove_intent_%d.json'%state['removed_files']),row)
        p.unlink();archive.sync_dir(p.parent);state['removed_files']+=1;state['removed_bytes']+=row['bytes']
        archive.save(out/'state.json',state)
    need(all(checked.stamp(q)==stamps[str(q)] for q in fixed),'Retained evidence changed')
    state.update(status=('verified_duplicates_removed_archive_retained' if state['removed_files']==5 else
        'query_started_remaining_duplicates_preserved'),finished=archive.now(),free_after=shutil.disk_usage(str(project)).free)
    archive.save(out/'state.json',state);print('RECOVERY27_COMPLETE',state['removed_files'],state['removed_bytes'],sha(out/'state.json'),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--execute-five-archived-intermediates',action='store_true',required=True)
    p.parse_args();main()
