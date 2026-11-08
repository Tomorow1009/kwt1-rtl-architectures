"""Verify and extract one team bundle without replacing an existing directory."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import stat
import sys
import zipfile

def unpack(archive,destination,expected):
    if hashlib.sha256(archive.read_bytes()).hexdigest()!=expected:
        raise ValueError('Archive SHA256 mismatch')
    destination=destination.resolve()
    with zipfile.ZipFile(str(archive)) as z:
        names=z.namelist()
        if not names or len(set(names))!=len(names):raise ValueError('Empty or duplicate archive entries')
        roots=set()
        for info in z.infolist():
            p=PurePosixPath(info.filename)
            if p.is_absolute() or '..' in p.parts or '\\' in info.filename or ':' in info.filename:
                raise ValueError('Unsafe archive path '+info.filename)
            if stat.S_ISLNK(info.external_attr>>16):raise ValueError('Symlink entry forbidden')
            roots.add(p.parts[0])
        if len(roots)!=1:raise ValueError('Expected one bundle directory')
        top=next(iter(roots));target=destination/top
        if target.exists():raise ValueError('Target already exists; do not overwrite '+str(target))
        manifest=json.loads(z.read(top+'/manifest.json').decode('utf-8'))
        expected_names={top+'/'+rel for rel in manifest['files']}|{top+'/manifest.json'}
        if set(names)!=expected_names:raise ValueError('Archive/manifest file set mismatch')
        for rel,digest in manifest['files'].items():
            if hashlib.sha256(z.read(top+'/'+rel)).hexdigest()!=digest:raise ValueError('Entry hash mismatch '+rel)
        destination.mkdir(parents=True,exist_ok=True)
        target.mkdir(exist_ok=False)
        for name in names:
            q=destination/name;q.parent.mkdir(parents=True,exist_ok=True)
            with q.open('xb') as f:f.write(z.read(name))
    print('UNPACK_HASH_PASS',target,flush=True)
    return target

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('archive',type=Path);p.add_argument('--destination',required=True,type=Path)
    p.add_argument('--sha256',required=True)
    a=p.parse_args();unpack(a.archive,a.destination,a.sha256)

if __name__=='__main__':
    try:main()
    except Exception as exc:print('FAIL:',exc,file=sys.stderr);sys.exit(1)
