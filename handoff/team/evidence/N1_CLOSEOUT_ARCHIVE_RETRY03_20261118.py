"""N1 runtime-only archive retry with an explicit 1.5GiB reserve profile.

The default 2GiB plus 20% exact compressed-size budget stopped before writing.
Retain the verified auxiliary archive, every N1 source and the failed attempt.
Change only reserve and its diagnostic text in a new isolated helper copy.
"""
import hashlib, json, os, sys
from pathlib import Path
sys.dont_write_bytecode=True
C=Path('/tmp/s4_21usr_n1_closeout_20261117_2355')
OLD=C/'tools-20261118_0015'
NEW=C/'tools-20261118_0030-reserve1536'
BASE_SHA='8a1162f15b3e7c561c11ecc403e5a0bca806078fb47ee080374ff678f7cfb5db'
PATHS_SHA='fe301e1e5f87852103c537b8191c7064f1b8c44a8979f1977901bf26ed16e39d'


def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(4*1024**2),b''):h.update(b)
    return h.hexdigest()


def read(p):return json.loads(Path(p).read_text())


def main():
    previous=read(C/'archive_state.json')
    assert previous['status']=='failed_preserved' and previous['failed_phase']=='archiving_three_runtime_bundles'
    assert previous['error']=='Insufficient shared archive space: need 1.2x exact gzip bytes plus 2GiB'
    assert not Path('/proc/85162').exists() and not NEW.exists() and not (C/'archive_state03.json').exists()
    aux=Path(previous['auxiliary_destination'])
    assert read(aux/'receipt.json')==previous['auxiliary_receipt'] and previous['auxiliary_receipt']['status']=='verified'
    assert sha(OLD/'n1_archive_runtime.py')==BASE_SHA and sha(OLD/'n1_paths.py')==PATHS_SHA
    source=(OLD/'n1_archive_runtime.py').read_bytes()
    assert source.count(b'RESERVE=2*1024**3')==1 and source.count(b'plus 2GiB')==1
    modified=source.replace(b'RESERVE=2*1024**3',b'RESERVE=1536*1024**2').replace(b'plus 2GiB',b'plus 1.5GiB')
    NEW.mkdir(mode=0o700)
    (NEW/'n1_archive_runtime.py').write_bytes(modified)
    (NEW/'n1_paths.py').write_bytes((OLD/'n1_paths.py').read_bytes())
    sys.path.insert(0,str(NEW));import n1_archive_runtime as base
    profile=dict(schema='n1-explicit-archive-capacity-profile-v1',base_sha256=BASE_SHA,
        derived_sha256=sha(NEW/'n1_archive_runtime.py'),paths_sha256=PATHS_SHA,
        reserve_bytes=1536*1024**2,compressed_size_margin=1.2,copy_only=True,
        all_source_hash_checks_retained=True,full_member_readback_retained=True,
        source_deletion=False,changes=['RESERVE only','diagnostic text only'])
    assert base.RESERVE==1536*1024**2
    base.save(NEW/'capacity_profile.json',profile)
    request=read(C/'runtime_request.json')
    assert not Path(request['destination']).exists()
    request['destination']=str(Path(request['destination']).parent/'n1-runtime-20261118_0030')
    assert not Path(request['destination']).exists()
    base.save(C/'runtime_request03.json',request)
    state={k:v for k,v in previous.items() if k not in ('error','failed_phase','finished','status','pid','started','script_sha256')}
    state.update(status='archiving_three_runtime_bundles',pid=os.getpid(),started=base.now(),
        script_sha256=sha(__file__),previous_attempt_sha256=sha(C/'archive_state.json'),
        capacity_profile=profile,auxiliary_not_rerun=True)
    base.save(C/'archive_state03.json',state)
    try:
        state['runtime_receipt']=base.archive(request)
        state['runtime_destination']=request['destination']
        assert sha(C/'archive_state.json')==state['previous_attempt_sha256']
        for name,digest in state['original_report_identities'].items():assert sha(Path(name))==digest
        state.update(status='both_archives_verified_original_sources_retained',finished=base.now())
        base.save(C/'archive_state03.json',state)
        print('N1_BOTH_ARCHIVES_VERIFIED',sha(C/'archive_state03.json'),flush=True)
    except BaseException as error:
        state.update(status='failed_preserved',error=str(error),finished=base.now())
        base.save(C/'archive_state03.json',state);raise


if __name__=='__main__':main()
