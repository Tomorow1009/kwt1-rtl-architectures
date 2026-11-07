#!/bin/sh
set -eu
cd "$(dirname "$0")/arch02_server_r01"
python3 - <<'PYCODE' > model_review.txt
from pathlib import Path
import re
for size in (128,4096):
 p=Path('/storage1/admin_public_dir/SRAM_Lib_2025/RAMSP%dX16/verilog/RAMSP%dX16.v'%(size,size))
 lines=p.read_text(errors='replace').splitlines()
 print('=== MODEL %s ==='%p)
 keep=set()
 for i,s in enumerate(lines):
  if re.search(r'^\s*(module|input|output|parameter|`ifdef|`ifndef|`else|`endif)\b|EMA|EMAW|RET1N|case.*(CEN|WEN|GWEN)|posedge|negedge|mem\[|mem_array|MEM\[|Memory\[',s):
   if s.lstrip().startswith('//'):continue
   for n in range(max(0,i-2),min(len(lines),i+5)):keep.add(n)
 for i in sorted(keep):
  if lines[i].strip() and not lines[i].lstrip().startswith('//'):print('%4d %s'%(i+1,lines[i]))
print('=== KWT DATA ===')
root=Path.home()/'Desktop/IC/KWT'
for pattern in ('manifest.json','integer_tensors.npz'):
 for n,p in enumerate(root.rglob(pattern)):
  if n>=20: print('MORE entries omitted');break
  print(p)
print('MODEL_REVIEW_COMPLETE')
PYCODE
head -60 model_review.txt
