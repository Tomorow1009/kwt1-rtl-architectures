#!/bin/sh
set -eu
cd "$(dirname "$0")/arch02_server_r01"
python3 - <<'PY'
from pathlib import Path
import json,hashlib,subprocess,sys
models=[Path('/storage1/admin_public_dir/SRAM_Lib_2025/RAMSP%dX16/verilog/RAMSP%dX16.v'%(n,n)) for n in (128,4096)]
for p in models:
 if not p.is_file():raise SystemExit('Missing vendor model '+str(p))
cfg={'kind':'vendor_confirmed','evidence':'VNC source review: RAMSP128X16.v EMA/EMAW lines226-233, CEN/writeEnable271-284, posedge427 and readWrite450; RAMSP4096X16.v EMA/EMAW231-238, RET1N263-268, CEN276, writeEnable287-290, posedge434. Native read contract to be checked by unit simulation; no PPA claim.','macros':{},'models':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in models}}
for n in (128,4096):cfg['macros'][str(n)]={'cen_low':1,'gwen_low':1,'wen_low':1,'ema':2,'emaw':0,'ret1n':1,'read_latency':1,'clock_edge':'posedge'}
Path('vendor_config.json').write_text(json.dumps(cfg,indent=2))
Path('vendor.f').write_text('\n'.join(str(p) for p in models)+'\n')
ret=subprocess.call([sys.executable,'vcs_run.py','--mode','unit','--config','vendor_config.json','--filelist','vendor.f'])
if ret:
 runs=sorted(Path('server_runs').glob('*'))
 if runs:
  for p in sorted(runs[-1].rglob('*.log')):
   print('LOG '+str(p),flush=True)
   print('\n'.join(p.read_text(errors='replace').splitlines()[-60:]),flush=True)
sys.exit(ret)
PY
