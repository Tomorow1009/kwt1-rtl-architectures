#!/bin/sh
set -eu
cd "$(dirname "$0")/arch02_server_r03"
python3 - <<'PY'
from pathlib import Path
import json,re
runs=sorted(Path('dc_runs').glob('inventory_*'))
run=runs[-1]
data=json.loads((run/'inventory.json').read_text())
print('INVENTORY',run)
for archive,entries in data['archives'].items():
 print('ARCHIVE',archive)
 for e in entries:
  n=e['name']
  if n.endswith('_basic.db') and ('_ss_' in n and '125c' in n or '_tt_' in n and '25c' in n):print(n,e['bytes'])
for size in (128,4096):
 p=Path('/storage1/admin_public_dir/SRAM_Lib_2025/RAMSP%dX16/lib/RAMSP%dX16_ss_0p99v_0p99v_125c.lib'%(size,size))
 print('MACRO_HEADER',p)
 text=p.read_text()
 for line in text.splitlines():
  if re.search(r'^\s*(library\s*\(|time_unit|voltage_unit|capacitive_load_unit|area\s*:|nom_voltage|nom_temperature|operating_conditions\s*\(|voltage\s*:|temperature\s*:|cell\s*\()',line):print(line.strip())
print('DC_ENVIRONMENT')
print((run/'dc_environment.log').read_text(errors='replace')[-6000:])
PY
