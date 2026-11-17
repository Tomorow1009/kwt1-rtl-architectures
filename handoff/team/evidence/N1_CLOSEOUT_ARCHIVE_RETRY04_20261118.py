"""Complete the N1 runtime archive after verified L06 capacity recovery.

Keep the already verified auxiliary archive. Use a separate 512MiB-reserve
copy-only profile with the same 20% compressed-size margin and all readbacks.
Never resume EDA, delete N1 sources, clear another lock or overwrite failures.
"""
import hashlib, json, os, sys
from pathlib import Path
sys.dont_write_bytecode=True
C=Path('/tmp/s4_21usr_n1_closeout_20261117_2355')
OLD=C/'tools-20261118_0015'
NEW=C/'tools-20261118_0110-reserve512'
PROJECT=Path('/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109')
MIGRATION=PROJECT/'backups/r4-l06-xz-20261118/receipt.json'
BASE_SHA='8a1162f15b3e7c561c11ecc403e5a0bca806078fb47ee080374ff678f7cfb5db'
PATHS_SHA='fe301e1e5f87852103c537b8191c7064f1b8c44a8979f1977901bf26ed16e39d'


def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(4*1024**2),b''):h.update(b)
    return h.hexdigest()


def read(p):return json.loads(Path(p).read_text())


def main():
    assert not NEW.exists() and not (C/'archive_state04.json').exists()
    previous=read(C/'archive_state03.json')
    assert previous['status']=='failed_preserved'
    assert previous['error']=='Insufficient shared archive space: need 1.2x exact gzip bytes plus 1.5GiB'
    assert not Path('/proc/%d'%previous['pid']).exists()
    m=read(MIGRATION)
    assert m['status']=='durable_xz_verified_staged_xz_retained' and m['full_durable_readback_verified']
    assert not Path('/proc/%d'%m['pid']).exists()
    assert not (PROJECT.parent/'.arch02_team_lock').exists()
    aux=Path(previous['auxiliary_destination'])
    assert read(aux/'receipt.json')==previous['auxiliary_receipt'] and previous['auxiliary_receipt']['status']=='verified'
    assert sha(OLD/'n1_archive_runtime.py')==BASE_SHA and sha(OLD/'n1_paths.py')==PATHS_SHA
    source=(OLD/'n1_archive_runtime.py').read_bytes()
    assert source.count(b'RESERVE=2*1024**3')==1 and source.count(b'plus 2GiB')==1
    modified=source.replace(b'RESERVE=2*1024**3',b'RESERVE=512*1024**2').replace(b'plus 2GiB',b'plus 512MiB')
    marker=b"        require(free>=required,'Insufficient shared archive space:"
    assert modified.count(marker)==1
    modified=modified.replace(marker,b"        print('N1_ARCHIVE_BUDGET',predicted,required,free,flush=True)\n"+marker)
    NEW.mkdir(mode=0o700)
    (NEW/'n1_archive_runtime.py').write_bytes(modified)
    (NEW/'n1_paths.py').write_bytes((OLD/'n1_paths.py').read_bytes())
    sys.path.insert(0,str(NEW));import n1_archive_runtime as base
    profile=dict(schema='n1-explicit-archive-capacity-profile-v1',base_sha256=BASE_SHA,
        derived_sha256=sha(NEW/'n1_archive_runtime.py'),paths_sha256=PATHS_SHA,
        reserve_bytes=512*1024**2,compressed_size_margin=1.2,copy_only=True,
        all_source_hash_checks_retained=True,full_member_readback_retained=True,source_deletion=False,
        changes=['RESERVE only','diagnostic text only','print exact capacity budget'])
    assert base.RESERVE==512*1024**2
    base.save(NEW/'capacity_profile.json',profile)
    assert sha(C/'runtime_request.json')=='6aa79be2948fa3a5468b7078eff6013ae7b8b47328cce6ddbbeac2b363b760da'
    request=read(C/'runtime_request.json')
    request['destination']=str(PROJECT/'backups/n1-runtime-20261118_0110')
    assert not Path(request['destination']).exists()
    base.save(C/'runtime_request04.json',request)
    state=dict(schema='n1-copy-only-closeout-v1',status='archiving_three_runtime_bundles',
        pid=os.getpid(),started=base.now(),script_sha256=sha(__file__),capacity_profile=profile,
        previous_attempt_sha256=sha(C/'archive_state03.json'),migration_receipt_sha256=sha(MIGRATION),
        auxiliary_receipt=previous['auxiliary_receipt'],auxiliary_destination=str(aux),
        original_report_identities=previous['original_report_identities'],auxiliary_not_rerun=True,
        hardware_commit='9305c6948c764fed01fe86b20bb3db94170299ab',source_modified=False,source_deleted=False,
        T80_modified=False,old8_modified=False,new_hardware_validation_started=False,original_results_reused=True)
    for name,digest in state['original_report_identities'].items():assert sha(Path(name))==digest
    base.save(C/'archive_state04.json',state)
    try:
        state['runtime_receipt']=base.archive(request)
        state['runtime_destination']=request['destination']
        assert sha(C/'archive_state03.json')==state['previous_attempt_sha256']
        for name,digest in state['original_report_identities'].items():assert sha(Path(name))==digest
        state.update(status='both_archives_verified_original_sources_retained',finished=base.now())
        base.save(C/'archive_state04.json',state)
        print('N1_BOTH_ARCHIVES_VERIFIED',flush=True);print(sha(C/'archive_state04.json'),flush=True)
    except BaseException as error:
        state.update(status='failed_preserved',error=str(error),finished=base.now())
        base.save(C/'archive_state04.json',state);raise


if __name__=='__main__':main()
