#!/bin/sh
set -eu
cd "$(dirname "$0")/arch02_server_r01"
python3 - <<'PY'
from pathlib import Path
import re
for size in (128,4096):
 p=Path('/storage1/admin_public_dir/SRAM_Lib_2025/RAMSP%dX16/verilog/RAMSP%dX16.v'%(size,size))
 lines=p.read_text().splitlines()
 keep=set()
 for i,s in enumerate(lines):
  if re.search(r'task readwrite|always @.*(?:CLK_|EMA_|EMAW_)',s):
   end=next((j+1 for j in range(i+1,len(lines)) if 'endtask' in lines[j]),i+65) if 'task readwrite' in s else min(i+65,len(lines))
   keep.update(range(i,end))
 out=['MODEL '+str(p)]
 for i in sorted(keep):
  s=lines[i].strip()
  if s and not s.startswith('//'): out.append('%d %s'%(i+1,s))
 Path('logic%d.txt'%size).write_text('\n'.join(out)+'\n')
 print('WROTE logic%d.txt lines=%d'%(size,len(out)))
print('LOGIC_REPORT_READY')
PY
