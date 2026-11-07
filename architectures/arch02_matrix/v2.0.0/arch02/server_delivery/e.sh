#!/bin/sh
set -eu
cd "$(dirname "$0")/arch02_server_r03"
python3 - <<'PY'
from pathlib import Path
import os,re,json
run=sorted(Path('dc_runs').glob('synth_*'))[-1].resolve()
print('REVIEW_RUN',run,flush=True)
for p in Path('/proc').iterdir():
 if not p.name.isdigit():continue
 try:
  status=(p/'status').read_text()
  if int(re.search(r'^Uid:\s+(\d+)',status,re.M).group(1))!=os.getuid():continue
  cwd=(p/'cwd').resolve();cmd=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')
  if str(run) in str(cwd) or 'dc_shell' in cmd or 'lc_shell' in cmd:print('PROCESS',p.name,cwd,cmd[:300])
 except (OSError,AttributeError,ValueError):pass
for name in ['dc.log','qor.rpt','area.rpt','references.rpt','check_design.rpt','check_timing.rpt','constraints.rpt','timing_max.rpt','timing_min.rpt']:
 p=run/name
 print('\nREPORT',name,'exists',p.exists(),flush=True)
 if p.exists():
  lines=p.read_text(errors='replace').splitlines()
  if name=='dc.log':
   for line in lines:
    if re.search(r'^(Error:|Warning:|DC_SYNTHESIS_FINISHED)',line):print(line)
   print('\n'.join(lines[-25:]))
  elif name in ('timing_max.rpt','timing_min.rpt'):print('\n'.join(lines[:110]))
  else:print('\n'.join(lines[-100:]))
for size in (128,4096):
 base=Path('/storage1/admin_public_dir/SRAM_Lib_2025/RAMSP%dX16'%size)
 print('PHYSICAL_SIZE',size)
 for p in base.rglob('*.lef'):
  text=p.read_text(errors='replace')
  for m in re.finditer(r'\bSIZE\s+([\d.]+)\s+BY\s+([\d.]+)\s*;',text):print(str(p),m.group(0),'product',float(m.group(1))*float(m.group(2)))
  break
PY
