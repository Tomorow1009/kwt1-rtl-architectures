"""Deduplicate identical frozen T64 input copies, retaining every path and byte."""
import os, json, hashlib, datetime, shutil
from pathlib import Path, PurePosixPath

root=Path('/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109/bundles')
old=root/'light-light126-t64-v4-65d2507-delta01'
keep=root/'light-light126-t64-v4-65d2507-fix02'
receipt=Path('/tmp/s4_21usr_t64_20261115_1510/ops-b9155b4/duplicate_storage_receipt.json')
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not receipt.exists() and not (old/'runs').exists()
assert old.resolve()==old and keep.resolve()==keep and old.stat().st_dev==keep.stat().st_dev
assert h(keep/'manifest.json')=='6632a4f266d48f50fd8a9e542cb6e03f05653d7ade3153903b38c3282c3339c1'
a=json.loads((old/'manifest.json').read_text());b=json.loads((keep/'manifest.json').read_text())
assert all(h(old/n)==v==b['files'][n]==h(keep/n) for n,v in a['files'].items())
# Only this team's unused T64 received input copy; never an old8 or T80 run.
for process in Path('/proc').iterdir():
    if not process.name.isdigit() or int(process.name)==os.getpid():continue
    try:
        if process.stat().st_uid!=os.getuid():continue
        command=(process/'cmdline').read_bytes()
        assert str(old).encode() not in command, 'Process references old T64 inputs'
        cwd=(process/'cwd').resolve()
        assert cwd!=old and old not in cwd.parents, 'Process working in old T64 copy'
    except (FileNotFoundError,ProcessLookupError):pass
records=[]
for name,digest in a['files'].items():
    if not name.startswith('validated_data/'):continue
    rel=PurePosixPath(name);assert not rel.is_absolute() and '..' not in rel.parts
    p=old/name;q=keep/name
    assert p.resolve()==p and q.resolve()==q and not p.is_symlink() and not q.is_symlink()
    st=p.stat();assert st.st_uid==os.getuid() and q.stat().st_uid==os.getuid()
    if st.st_nlink!=1 or st.st_size<65536:continue
    assert h(p)==digest==h(q)
    records.append(dict(path=str(p),retained_identical_path=str(q),sha256=digest,
                        bytes=st.st_size,previous_inode=st.st_ino,allocated_bytes=st.st_blocks*512))
assert records
state=dict(status='prepared',time=datetime.datetime.now().isoformat(),records=records,
           old_manifest_sha256=h(old/'manifest.json'),kept_manifest_sha256=h(keep/'manifest.json'),
           no_content_removed=True,t80_untouched=True,old8_untouched=True)
receipt.write_text(json.dumps(state,indent=2)+'\n')
for row in records:
    p=Path(row['path']);q=Path(row['retained_identical_path']);temp=p.with_name(p.name+'.t64_dedup_link')
    assert not temp.exists() and h(p)==row['sha256']==h(q)
    os.link(str(q),str(temp));assert h(temp)==row['sha256']
    os.replace(str(temp),str(p))
    assert p.stat().st_ino==q.stat().st_ino and h(p)==row['sha256']
assert all(h(old/n)==v==h(keep/n) for n,v in a['files'].items())
state.update(status='complete_all_original_paths_and_bytes_retained',finished=datetime.datetime.now().isoformat(),
             duplicate_allocated_bytes_reclaimed=sum(x['allocated_bytes'] for x in records),free_bytes=shutil.disk_usage(str(root)).free)
receipt.write_text(json.dumps(state,indent=2)+'\n')
print('T64_DUPLICATE_STORAGE_COMPLETE',len(records),state['duplicate_allocated_bytes_reclaimed'],state['free_bytes'],h(receipt))
