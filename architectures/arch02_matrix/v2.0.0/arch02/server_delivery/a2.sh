#!/bin/sh
set -eu
cd "$(dirname "$0")"
python3 - <<'PYCODE'
from pathlib import Path
import zipfile, hashlib, json
root=Path.cwd()
dest=root/'arch02_server_r01'
if dest.exists():
    raise SystemExit('Destination already exists; inspect previous run, do not overwrite')
with zipfile.ZipFile(str(root/'arch02_server_r01.zip')) as z:
    for name in z.namelist():
        p=(root/name).resolve()
        p.relative_to(dest.resolve())
    z.extractall(str(root))
m=json.loads((dest/'manifest.json').read_text())
for rel,digest in m['files'].items():
    p=(dest/rel).resolve();p.relative_to(dest.resolve())
    if hashlib.sha256(p.read_bytes()).hexdigest()!=digest:
        raise SystemExit('HASH MISMATCH '+rel)
print('BUNDLE_HASH_PASS files='+str(len(m['files'])))
PYCODE
python3 arch02_server_r01/probe.py > arch02_server_r01/discovery.txt 2>&1
cat arch02_server_r01/discovery.txt
