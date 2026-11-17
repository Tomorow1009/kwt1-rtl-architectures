"""If necessary, reclaim one archived B0 hierarchy report, then migrate L06.

At >=16MiB free, remove nothing. Otherwise only the exact byte-identical B0
hierarchy.rpt duplicate is removed; its unchanged durable archive is retained.
Do not delete any RTL, netlist, old8, T80 or N1 file. Migration acquires the
original shared lock immediately, before its lengthy source verification.
"""
import argparse, hashlib, importlib.util, json, os, shutil, sys
from pathlib import Path
sys.dont_write_bytecode=True
C=Path('/tmp/s4_21usr_n1_closeout_20261117_2355')
STAGE=Path('/tmp/s4_21usr_n1_r4_l06_stage03_20261118')
OUT=C/'lock_space43'
HELPER=Path('/tmp/s4_21usr_c80_20261116_1245/ops-b0-cleanup16-c8c730d/C80_B0_DUPLICATES_CLEANUP16_20261116.py')
REL='bundles/light-light126-systolic-b-v3-20261112_114355-ced0e139a01e/runs/systolic_b_v3_drc06/systolic_b_synth/hierarchy.rpt'


def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(4*1024**2),b''):h.update(b)
    return h.hexdigest()


def read(p):return json.loads(Path(p).read_text())
def load(name,p):
    spec=importlib.util.spec_from_file_location(name,str(p));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def main(stage_sha,migration_sha):
    assert not OUT.exists() and sha(STAGE/'state.json')==stage_sha
    stage=read(STAGE/'state.json')
    assert stage['status']=='fully_verified_staging_original_retained' and stage['full_xz_readback_verified']
    assert not Path('/proc/%d'%stage['pid']).exists()
    migration_path=C/'l06_migrate02.py';assert sha(migration_path)==migration_sha
    migrate=load('n1_l06_verified_migration',migration_path)
    assert migrate.STAGE==STAGE and migrate.STAGE_SCRIPT_SHA==stage['source_script_sha256']
    assert sha(HELPER)=='0e98728332e0ba048142231f414322dc3aaf21e287b3bde0bc4121124c976441'
    base=load('n1_lock43_idle',HELPER);assert sha(base.PREFLIGHT)==base.PREFLIGHT_SHA
    checked=load('n1_lock43_archive',base.PREFLIGHT)
    assert sha(base.BUNDLE/'manifest.json')==base.MANIFEST_SHA
    deps=read(base.BUNDLE/'manifest.json')['files']
    for name in ('n1_archive_runtime.py','n1_paths.py','partition_synth_contract.py'):
        rel='workspaces/arch03/scripts/'+name;assert sha(base.BUNDLE/rel)==deps[rel]
    sys.path.insert(0,str(base.BUNDLE/'workspaces/arch03/scripts'));import n1_archive_runtime as archive
    project=checked.PROJECT;lock=project.parent/'.arch02_team_lock'
    assert project==migrate.PROJECT
    state=dict(schema='n1-l06-lock-space-v1',status='preflight',script_sha256=sha(__file__),
        stage_sha256=stage_sha,migration_sha256=migration_sha,removed_files=0,
        T80_modified=False,old8_modified=False,N1_modified=False,source_code_modified=False,
        durable_archive_modified=False,free_before=shutil.disk_usage(str(project)).free)
    if state['free_before']<16*1024**2:
        fixed={checked.BACKUP/'manifest.json':checked.MANIFEST_SHA,
            checked.BACKUP/'receipt.json':checked.RECEIPT_SHA,
            checked.BACKUP/'completed-evidence.tar.gz':checked.ARCHIVE_SHA,
            checked.PRIOR:checked.PRIOR_SHA}
        stamps={str(p):checked.stamp(p) for p in fixed}
        assert all(sha(p)==h and checked.stamp(p)==stamps[str(p)] for p,h in fixed.items())
        prior=read(checked.PRIOR)
        assert prior['archive_sha256']==checked.ARCHIVE_SHA and prior['all_archive_members_readback_verified']==63653
        assert prior['all_archive_bytes_readback_verified']==7006124866
        index={r['path']:r for r in read(checked.BACKUP/'manifest.json')['files']}
        row=index[REL];source=project/REL;before=checked.stamp(source)
        assert 0<row['bytes']<16*1024**2 and before['bytes']==row['bytes']
        assert sha(source)==row['sha256'] and checked.stamp(source)==before
        state.update(process_observation=base.idle(archive,lock,[source]),
            duplicate=dict(path=REL,sha256=row['sha256'],bytes=row['bytes'],stamp=before),
            archive=str(checked.BACKUP/'completed-evidence.tar.gz'),archive_sha256=checked.ARCHIVE_SHA,
            prior_full_readback_sha256=checked.PRIOR_SHA,
            restore='Extract the exact hierarchy.rpt member from the retained B0 complete archive to a new path; verify SHA and bytes before restoring.')
        OUT.mkdir(mode=0o700);archive.save(OUT/'intent.json',state)
        assert all(checked.stamp(p)==stamps[str(p)] for p in fixed)
        base.idle(archive,lock,[source]);assert checked.stamp(source)==before and sha(source)==row['sha256']
        assert not lock.exists()
        source.unlink();archive.sync_dir(source.parent)
        state.update(removed_files=1,removed_bytes=row['bytes'],status='verified_duplicate_removed_archive_retained')
        archive.save(OUT/'state.json',state)
    else:
        base.idle(archive,lock,[]);OUT.mkdir(mode=0o700)
        state['status']='enough_lock_space_no_cleanup';archive.save(OUT/'state.json',state)
    try:
        migrate.main(stage_sha)
        state.update(status='migration_completed',finished=archive.now(),
            migration_receipt_sha256=sha(migrate.DEST/'receipt.json'))
    except BaseException as error:
        state.update(status='migration_stopped_preserved',error=str(error),finished=archive.now());raise
    finally:archive.save(OUT/'state.json',state)
    print('N1_LOCK_SPACE_AND_L06_MIGRATION_COMPLETE',sha(OUT/'state.json'),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--stage-sha256',required=True);p.add_argument('--migration-sha256',required=True)
    a=p.parse_args();main(a.stage_sha256,a.migration_sha256)
