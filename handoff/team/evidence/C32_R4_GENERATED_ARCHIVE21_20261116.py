"""Read-only staged archive of one completed R4 batch's generated inputs.

No removal, rename, persistent-backup replacement, EDA or queue restart.
Only HEX/BIN/Verilog task input images are selected; results and metadata stay.
"""
import hashlib
import importlib.util
import json
import os
from pathlib import Path,PurePosixPath
import re
import shutil
import stat
import sys
import tarfile
import time

sys.dont_write_bytecode=True
ROOT=Path('/tmp/s4_21usr_c32_20261116_2010')
OUT=ROOT/'r4_generated_archive21'
PROJECT=Path('/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109')
RUN=PROJECT/'bundles/light-light126-icb32-r4-20261111_043048-96443c284a1c/runs/icb32_r4_finish01_final1200/icb32_batch'
SUMMARY='3bb0290586f7b92e5a392cb8f7e735ec483b8b302cc285a39fff2e63ebc01bc2'
IDENTITY='27060dfcec0e8fcfadd925d2899ecabcad3c05d05d9048e631616811b540adc9'
OLD=Path('/tmp/s4_21usr_c80_20261116_1245')
BASE=OLD/'ops-b0-cleanup16-c8c730d/C80_B0_DUPLICATES_CLEANUP16_20261116.py'
BASE_SHA='0e98728332e0ba048142231f414322dc3aaf21e287b3bde0bc4121124c976441'


def need(ok,message):
    if not ok:raise ValueError(message)


def digest(stream):
    h=hashlib.sha256();size=0
    for block in iter(lambda:stream.read(4*1024**2),b''):h.update(block);size+=len(block)
    return h.hexdigest(),size


def sha(p):
    with Path(p).open('rb') as f:return digest(f)[0]


def read(p):return json.loads(Path(p).read_text())


def stamp(p):
    p=Path(p);s=p.lstat()
    need(p.resolve()==p.absolute() and stat.S_ISREG(s.st_mode) and s.st_uid==os.getuid(),'Not an owned ordinary file')
    return dict(device=s.st_dev,inode=s.st_ino,bytes=s.st_size,mtime_ns=s.st_mtime_ns,ctime_ns=s.st_ctime_ns)


def selected(name):
    p=PurePosixPath(name)
    return (not p.is_absolute() and '..' not in p.parts and '\\' not in name and p.as_posix()==name and
        len(p.parts)>=3 and p.parts[0]=='cases' and
        re.fullmatch(r'sample_\d{6}_layer_\d{2}',p.parts[1]) is not None and
        p.suffix in ('.hex','.bin','.verilog'))


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,str(path))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def main():
    need(os.name=='posix' and ROOT.resolve()==ROOT and ROOT.stat().st_mode&0o777==0o700 and
         not OUT.exists(),'Use a new private archive attempt')
    need(sha(BASE)==BASE_SHA,'Process helper changed')
    base=load('r4_archive_process_helpers21',BASE)
    need(sha(base.BUNDLE/'manifest.json')==base.MANIFEST_SHA,'Frozen helper bundle changed')
    mf=read(base.BUNDLE/'manifest.json')['files']
    for name in ('n1_archive_runtime.py','n1_paths.py','partition_synth_contract.py'):
        rel='workspaces/arch03/scripts/'+name;need(sha(base.BUNDLE/rel)==mf[rel],'Inspection helper changed')
    sys.path.insert(0,str(base.BUNDLE/'workspaces/arch03/scripts'))
    import n1_archive_runtime as archive
    lock=PROJECT.parent/'.arch02_team_lock'
    before_process=base.idle(archive,lock,[RUN])
    need(sha(RUN/'summary.json')==SUMMARY and sha(RUN/'batch_identity.json')==IDENTITY,'Wrong completed R4 batch')
    summary=read(RUN/'summary.json');stage=read(RUN.parent/'state.json')['stages']['icb32_batch']
    need(stage['status']=='passed' and stage['summary_sha256']==SUMMARY and summary['status']=='passed' and
         summary['tasks']==1200 and summary['checked_outputs']==30412800 and summary['failed']==0 and
         summary['asic_cpu_verified'] and summary['cpu_executed'],'R4 batch did not pass')
    keys={v['key'] for v in summary['cases']}
    need(len(keys)==1200 and len(summary['cases'])==1200,'Wrong R4 case set')
    protected={str(p):sha(p) for p in (RUN/'summary.json',RUN/'batch_identity.json',RUN.parent/'state.json')}
    rows={};metadata={}
    for key in sorted(keys):
        case=RUN/'cases'/key
        need(case.resolve()==case and case.is_dir(),'Missing canonical R4 case')
        receipt=case/'receipt.json';metadata[str(receipt)]=sha(receipt)
        for p in sorted(case.rglob('*')):
            name=p.relative_to(RUN).as_posix()
            if not selected(name):continue
            old=stamp(p);h=sha(p);need(stamp(p)==old,'Generated input changed while hashing')
            rows[name]=dict(bytes=old['bytes'],sha256=h,stamp=old)
    need(len(rows)>=1200 and {PurePosixPath(n).parts[1] for n in rows}==keys,'Missing generated case inputs')
    total=sum(v['bytes'] for v in rows.values())
    need(0<total<4*1024**3 and shutil.disk_usage(str(ROOT)).free>=int(total*1.2)+2*1024**3,'Staged archive space insufficient')
    base.idle(archive,lock,[RUN])
    OUT.mkdir(mode=0o700)
    manifest=dict(schema='r4-generated-inputs-staged-archive-v1',source_root=str(RUN),
        files=rows,source_bytes=total,protected_metadata=protected,case_receipts=metadata,
        source_sha256=sha(__file__),input_selection='Only per-task .hex/.bin/.verilog generated images',
        source_modified=False,source_deleted=False,protected_T80_modified=False,old8_modified=False)
    archive.save(OUT/'manifest.json',manifest)
    print('R4_ARCHIVE21_SELECTED',len(rows),total,flush=True)
    target=OUT/'generated-inputs.tar.gz';start=time.monotonic()
    with tarfile.open(str(target),'x:gz',compresslevel=1) as tar:
        for index,name in enumerate(sorted(rows)):
            p=RUN/name;need(stamp(p)==rows[name]['stamp'],'Source changed before copy')
            tar.add(str(p),arcname=name,recursive=False)
            if index%4096==0:print('R4_ARCHIVE21_COPIED',index,flush=True)
    with target.open('rb') as f:os.fsync(f.fileno())
    seen=set();verified_bytes=0
    with tarfile.open(str(target),'r:gz') as tar:
        for member in tar:
            need(member.isfile() and member.name in rows and member.name not in seen,'Unexpected archive member')
            v=rows[member.name];need(member.size==v['bytes'],'Archived size differs')
            with tar.extractfile(member) as f:h,n=digest(f)
            need(h==v['sha256'] and n==v['bytes'],'Archived member bytes differ')
            seen.add(member.name);verified_bytes+=n
    need(seen==set(rows) and verified_bytes==total,'Incomplete archive readback')
    for name,v in rows.items():need(stamp(RUN/name)==v['stamp'] and sha(RUN/name)==v['sha256'],'Source changed during archive')
    need(all(sha(p)==h for p,h in dict(protected,**metadata).items()),'R4 result metadata changed')
    after_process=base.idle(archive,lock,[RUN])
    result=dict(status='verified_staged_archive_source_preserved',archive=str(target),archive_sha256=sha(target),
        archive_bytes=target.stat().st_size,manifest_sha256=sha(OUT/'manifest.json'),
        members_verified=len(seen),source_bytes=total,elapsed_seconds=time.monotonic()-start,
        source_deleted=False,source_modified=False,persistent_shared_copy_completed=False,
        before_process=before_process,after_process=after_process)
    archive.save(OUT/'receipt.json',result);archive.sync_dir(OUT)
    print('R4_ARCHIVE21_VERIFIED',len(seen),total,target.stat().st_size,sha(OUT/'receipt.json'),flush=True)


if __name__=='__main__':main()
