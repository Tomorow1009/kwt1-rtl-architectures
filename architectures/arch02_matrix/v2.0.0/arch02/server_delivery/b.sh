#!/bin/sh
set -eu
cd "$(dirname "$0")/arch02_server_r02"
python3 - <<'PY'
from pathlib import Path
import datetime,json,tarfile,re,subprocess,shutil
run=Path('dc_runs')/('inventory_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'));run.mkdir(parents=True)
report={'standard_root':'/storage1/admin_public_dir/SMIC40_2025','macros':{},'archives':{},'files':[]}
for n in (128,4096):
 root=Path('/storage1/admin_public_dir/SRAM_Lib_2025/RAMSP%dX16'%n)
 files=sorted(p for p in root.rglob('*') if p.is_file() and p.suffix in ('.lib','.db','.pdf','.txt'))
 report['macros'][str(n)]=[str(p) for p in files]
 print('MACRO',n,'libraries',len([p for p in files if p.suffix in ('.lib','.db')]),flush=True)
 for p in files:
  if p.suffix in ('.lib','.db'):print(str(p),flush=True)
root=Path(report['standard_root'])
for p in root.rglob('*'):
 if not p.is_file():continue
 report['files'].append({'path':str(p),'bytes':p.stat().st_size})
 if p.name.endswith('.tar.gz'):
  found=[]
  with tarfile.open(str(p),'r|gz') as archive:
   for i,m in enumerate(archive):
    if i>=30000:raise RuntimeError('Archive inventory limit '+str(p))
    if m.isfile() and (m.name.endswith(('.db','.lib','.tcl','.txt','.pdf')) or 'README' in m.name.upper()):found.append({'name':m.name,'bytes':m.size})
  report['archives'][str(p)]=found
  print('ARCHIVE',str(p),'selected_entries',len(found),flush=True)
  for m in found[:100]:print(m['name'],m['bytes'],flush=True)
(run/'inventory.json').write_text(json.dumps(report,indent=2))
dc=shutil.which('dc_shell')
if dc:
 log=run/'dc_environment.log'
 with log.open('w') as f:
  rc=subprocess.call([dc,'-x','puts "DC_LIBRARY_DISCOVERY"; printvar target_library; printvar link_library; printvar search_path; list_libs; quit'],cwd=str(run.resolve()),stdout=f,stderr=subprocess.STDOUT)
 print('DC_DISCOVERY_EXIT',rc,flush=True)
 print('\n'.join(log.read_text(errors='replace').splitlines()[-60:]),flush=True)
print('DC_INVENTORY_COMPLETE',run,flush=True)
PY
