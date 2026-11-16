"""Read-only recheck of old B0 generated inputs already in its durable backup.

Never deletes, moves, compresses or modifies any source/backup. It can run
alongside the unrelated P80 mapping because it only reads the completed B0
batch and archive; writes are restricted to one fresh private audit directory.
This is not a cleanup authorization or a proof that files are unused.
"""
import datetime
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import tarfile

ROOT = Path('/tmp/s4_21usr_p80_20261116_0315')
OUT = ROOT/'b0_archived_batch_preflight12'
PROJECT = Path('/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109')
BACKUP = PROJECT/'backups/systolic-b-20261112_2320'
BUNDLE = 'light-light126-systolic-b-v3-20261112_114355-ced0e139a01e'
RUN_REL = 'bundles/'+BUNDLE+'/runs/systolic_b_final02_final1200/systolic_b_batch'
MANIFEST_SHA = '443a49be5abd11b5ab8d5c5bef744ae1c6cef5908ffd933041d06e086193aea9'
RECEIPT_SHA = 'b798a588f09cc18edc1239df988f6e2779a16e86989e2e88aca8a30acb29f5ee'
ARCHIVE_SHA = 'dbfd6e93ea6257995e61e6fce8bff0aaf0d0f9d47c0d33cc38d6ce08ea536a50'
SUFFIXES = ('.hex', '.verilog', '.bin')


def need(ok, message):
    if not ok: raise ValueError(message)


def now(): return datetime.datetime.now().isoformat()


def digest(stream):
    value=hashlib.sha256(); size=0
    for data in iter(lambda: stream.read(1024*1024), b''):
        value.update(data); size+=len(data)
    return value.hexdigest(), size


def sha(path):
    with Path(path).open('rb') as stream: return digest(stream)[0]


def stamp(path):
    path=Path(path); value=path.lstat()
    need(path.resolve()==path.absolute() and stat.S_ISREG(value.st_mode) and
         value.st_uid==os.getuid(), 'Source is not a plain owned file: '+str(path))
    return [value.st_dev,value.st_ino,value.st_size,value.st_mtime_ns,value.st_ctime_ns]


def save(name, value):
    path=OUT/name
    with path.open('x') as stream:
        json.dump(value,stream,indent=2,sort_keys=True);stream.write('\n')
        stream.flush();os.fsync(stream.fileno())


def main():
    need(os.name=='posix' and ROOT.resolve()==ROOT and ROOT.stat().st_uid==os.getuid() and
         ROOT.stat().st_mode & 0o777==0o700, 'Wrong private audit root')
    need(not OUT.exists(), 'Preserve previous audit')
    metadata=[BACKUP/'manifest.json',BACKUP/'receipt.json']
    need(sha(metadata[0])==MANIFEST_SHA and sha(metadata[1])==RECEIPT_SHA, 'Backup metadata differs')
    manifest=json.loads(metadata[0].read_text()); receipt=json.loads(metadata[1].read_text())
    need(manifest['schema']=='arch03-b-server-backup-v1' and manifest['source_root']==str(PROJECT),
         'Wrong B0 archive source root')
    need(receipt['status']=='verified' and receipt['archive_sha256']==ARCHIVE_SHA and
         receipt['verified_files']==63653 and receipt['source_bytes']==7006124866,
         'Wrong B0 backup receipt')
    inventory={}
    for row in manifest['files']:
        name=row['path']; parts=PurePosixPath(name).parts
        need(name not in inventory and not PurePosixPath(name).is_absolute() and
             name==PurePosixPath(name).as_posix() and not any(x in ('','..','.') for x in parts),
             'Unsafe or duplicate archive name')
        inventory[name]=row
    need(len(inventory)==63653, 'Incomplete original archive manifest')
    archive=BACKUP/'completed-evidence.tar.gz'
    before={str(p):stamp(p) for p in metadata+[archive]}
    need(archive.stat().st_size==1261445859, 'Archive length differs')
    summary_name=RUN_REL+'/summary.json'; state_name=str(PurePosixPath(RUN_REL).parent/'state.json')
    for name in (summary_name,state_name):
        need(name in inventory and sha(PROJECT/name)==inventory[name]['sha256'], 'B0 terminal receipt changed')
    report=json.loads((PROJECT/summary_name).read_text())
    state=json.loads((PROJECT/state_name).read_text())['stages']['systolic_b_batch']
    need(state['status']=='passed' and state['summary_sha256']==inventory[summary_name]['sha256'] and
         report['status']=='passed' and report['tasks']==1200 and report['checked_outputs']==30412800 and
         report['failed']==0 and report['asic_cpu_verified'] and report['cpu_executed'],
         'B0 batch is not the completed real CPU batch')
    keys={row['key'] for row in report['cases']}
    need(len(keys)==1200 and len(report['cases'])==1200, 'Incomplete or duplicate B0 cases')
    prefix=RUN_REL+'/cases/'
    selected={name:row for name,row in inventory.items() if name.startswith(prefix) and
              PurePosixPath(name).suffix in SUFFIXES}
    need(selected and len(selected)<60000 and sum(row['bytes'] for row in selected.values())<3*1024**3,
         'Unexpected generated-input candidate scope')
    need({name[len(prefix):].split('/')[0] for name in selected}==keys, 'Candidate case set differs')
    OUT.mkdir(mode=0o700)
    save('intent.json',dict(started=now(),pid=os.getpid(),script_sha256=sha(__file__),
        candidate_files=len(selected),candidate_bytes=sum(row['bytes'] for row in selected.values()),
        suffixes=SUFFIXES,source_batch=str(PROJECT/RUN_REL),source_deleted=False,source_modified=False,
        backup_modified=False,cleanup_authorized_by_this_audit=False))
    need(sha(archive)==ARCHIVE_SHA, 'Original durable archive digest differs')
    seen=set(); total=0
    with tarfile.open(str(archive),'r|gz') as tar:
        for member in tar:
            need(member.isfile() and member.name in inventory and member.name not in seen,
                 'Unexpected archive member or type')
            row=inventory[member.name]
            need(member.size==row['bytes'], 'Archive member size differs')
            with tar.extractfile(member) as stream: actual,size=digest(stream)
            need(actual==row['sha256'] and size==row['bytes'], 'Archive member content differs')
            seen.add(member.name);total+=size
    need(seen==set(inventory) and total==7006124866, 'Incomplete full archive readback')
    candidates=[]
    for name,row in sorted(selected.items()):
        path=PROJECT/name; identity=stamp(path)
        need(identity[2]==row['bytes'] and sha(path)==row['sha256'] and stamp(path)==identity,
             'Current duplicate differs from its verified archive member')
        candidates.append(dict(path=name,bytes=row['bytes'],sha256=row['sha256'],stamp=identity))
    need(all(stamp(p)==old for p,old in before.items()), 'Backup changed during audit')
    need(sha(metadata[0])==MANIFEST_SHA and sha(metadata[1])==RECEIPT_SHA, 'Metadata changed during audit')
    save('verified_candidates.json',dict(schema='p80-b0-archived-input-duplicates-readonly-v1',
        finished=now(),archive=str(archive),archive_sha256=ARCHIVE_SHA,manifest_sha256=MANIFEST_SHA,
        original_receipt_sha256=RECEIPT_SHA,all_archive_members_readback_verified=63653,
        all_archive_bytes_readback_verified=total,source_root=str(PROJECT),source_batch=RUN_REL,
        files=candidates,total_candidate_bytes=sum(x['bytes'] for x in candidates),
        source_modified=False,source_deleted=False,backup_modified=False,
        unused_proven=False,cleanup_authorized_by_this_audit=False,
        protected_T80_modified=False,old8_modified=False))
    print('B0_ARCHIVED_INPUT_DUPLICATES_VERIFIED',len(candidates),sum(x['bytes'] for x in candidates),
          sha(OUT/'verified_candidates.json'),'source_deleted=false',flush=True)


if __name__=='__main__': main()
