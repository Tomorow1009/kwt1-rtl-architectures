#!/bin/sh
set -eu
cd "$(dirname "$0")/arch02_server_r03"
python3 - <<'PY'
from pathlib import Path
import re,collections
run=Path('dc_runs/hold_20261108_005224')
for name in ['check_design.rpt','check_timing.rpt','dc.log']:
 lines=(run/name).read_text(errors='replace').splitlines();seen=collections.Counter()
 print('WARNING_REVIEW',name,flush=True)
 for i,line in enumerate(lines):
  if not line.startswith(('Warning:','Error:')):continue
  m=re.search(r'\(([A-Z]+-\d+)\)',line);code=m.group(1) if m else 'OTHER'
  seen[code]+=1
  if seen[code]<=1:print('\n'.join(lines[i:i+4]),flush=True)
 print('COUNTS',dict(seen),flush=True)
PY
