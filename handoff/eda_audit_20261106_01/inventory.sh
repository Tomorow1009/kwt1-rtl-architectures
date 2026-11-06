#!/bin/sh
# Read-only environment/resource inspection. Writes only its own unique run folder.
set -eu
base=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
run="$base/run_$(date +%Y%m%d_%H%M%S)_$$"
umask 077
mkdir "$run"
cd "$run"
printf '%s\n' "$run" > "$base/latest_run.txt"
if command -v python3 >/dev/null 2>&1; then py=python3
elif command -v python >/dev/null 2>&1; then py=python
else printf 'AUDIT_FAILED: Python unavailable\n' > summary.txt; exit 2
fi
set +e
"$py" - "$run" <<'PY' > inventory.log 2>&1
from __future__ import print_function
import os, sys, time, collections, subprocess
run = sys.argv[1]
home = os.path.expanduser('~')
summary = []
def emit(s):
    print(s)
    summary.append(s)
def executable(name):
    for folder in os.environ.get('PATH', '').split(os.pathsep):
        p = os.path.join(folder, name)
        if os.path.isfile(p) and os.access(p, os.X_OK): return os.path.realpath(p)
    return 'NOT_ON_PATH'
emit('EDA AUDIT - ENVIRONMENT AND RESOURCE INVENTORY')
emit('HOME=' + home)
emit('SHELL=' + os.environ.get('SHELL', 'UNKNOWN'))
emit('PYTHON=' + sys.version.split()[0])
emit('RUN=' + run)
for p in [os.path.join(home, 'Desktop'), os.path.join(home, 'Desktop', 'iccompetition'), '/iccompetition']:
    emit('PATH %s exists=%s writable=%s real=%s' % (p, os.path.exists(p), os.access(p, os.W_OK), os.path.realpath(p)))
emit('TOOLS (entrypoint only; licenses not yet tested):')
tools = ['dc_shell','pt_shell','fm_shell','lc_shell','vcs','verdi','icc2_shell','innovus','genus','xrun','virtuoso','spectre','calibre','timeout','tcsh','bash']
for name in tools: emit(name + '=' + executable(name))
config_paths = []
import re
for name in ['.cshrc','.tcshrc','.synopsys_dc.setup']:
    p = os.path.join(home,name)
    emit('CONFIG %s readable=%s' % (p,os.access(p,os.R_OK)))
    if os.path.isfile(p):
        with open(p,'r') as f:
            for line in f:
                if re.search(r'(?i)password|token|secret|license',line): continue
                if re.search(r'(?i)source|alias|target_library|link_library|search_path|pdk|sram',line):
                    config_paths.append('%s: %s' % (name,line.rstrip()))
with open('config_references.txt','w') as f: f.write('\n'.join(config_paths)+'\n')
roots = ['/storage1/admin_public_dir/SMIC40_2025','/storage1/admin_public_dir/SRAM_Lib_2025','/storage1/admin_public_dir/Document','/storage1/admin_public_dir/2025_Lab','/storage1/admin_public_dir/SOC_RTL_2025']
extensions = set(['.db','.lib','.lef','.gds','.gdsii','.v','.sv','.tf','.tluplus','.itf','.ndm','.pdf','.sp','.spi','.cdl','.tcl','.sh','.csh','.cfg','.txt','.md','.zip','.tar','.gz','.tgz','.lib.gz','.lef.gz','.gds.gz'])
manifest = open('resource_manifest.txt','w')
for root in roots:
    emit('RESOURCE ' + root + ' readable=' + str(os.access(root,os.R_OK)))
    counts=collections.Counter(); examples={}; top=[]; visited=0; limited=False
    errors=[]; start=time.time()
    if os.path.isdir(root):
        for folder, dirs, files in os.walk(root,followlinks=False,onerror=lambda e: errors.append(str(e))):
            dirs.sort(); files.sort()
            rel=os.path.relpath(folder,root)
            depth=0 if rel=='.' else rel.count(os.sep)+1
            if depth<=1: top.append(rel)
            if depth>=6: dirs[:]=[]; limited=True
            for name in files:
                visited+=1
                p=os.path.join(folder,name)
                ext=os.path.splitext(name.lower())[1]
                if ext=='.gz' and os.path.splitext(name[:-3].lower())[1] in ['.lib','.lef','.gds']:
                    ext=os.path.splitext(name[:-3].lower())[1]+'.gz'
                if ext in extensions or 'readme' in name.lower() or 'compiler' in name.lower():
                    readable=os.access(p,os.R_OK)
                    manifest.write('%s | readable=%s\n' % (p,readable))
                    counts[ext or '(none)']+=1
                    if len(examples.setdefault(ext,[]))<3: examples[ext].append(p)
                if visited>=15000: break
            if visited>=15000 or time.time()-start>25:
                limited=True; break
    emit('  TOP: ' + ', '.join(top[:14]))
    emit('  FILES_VISITED=%d LIMITED=%s ERRORS=%d' % (visited,limited,len(errors)))
    emit('  TYPES: ' + ' '.join('%s=%d'%(k,v) for k,v in sorted(counts.items())))
    with open(os.path.basename(root)+'_examples.txt','w') as f:
        for ext,paths in sorted(examples.items()):
            f.write(ext+'\n'+'\n'.join(paths)+'\n')
        for error in errors: f.write('ERROR '+error+'\n')
manifest.close()
emit('AUDIT_INVENTORY_COMPLETE')
with open('summary.txt','w') as f: f.write('\n'.join(summary)+'\n')
PY
result=$?
set -e
if [ "$result" -ne 0 ]; then
    printf 'AUDIT_INVENTORY_FAILED: inspect inventory.log\n' >> summary.txt
fi
printf 'INVENTORY_EXIT=%s\n' "$result" >> summary.txt
if command -v pluma >/dev/null 2>&1; then pluma "$run/summary.txt" >/dev/null 2>&1 &
else cat summary.txt
fi
exit "$result"
