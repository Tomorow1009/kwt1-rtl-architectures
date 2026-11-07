#!/bin/sh
set -eu
cd "$(dirname "$0")/arch02_server_r01"
python3 - <<'PY'
from pathlib import Path
import subprocess,re,datetime,shutil,hashlib,json
root=Path.cwd();run=root/'server_runs'/('sample_timing_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'));run.mkdir()
old=root/'server_runs/diagnostic_20261107_235529/diag.sv'
src=old.read_text().replace('always #50','always #5').replace('#39;','#3;')
src=src.replace('initial begin','always @(Q) $display("Q_CHANGE t=%0t q=%h",$time,Q);\ninitial begin')
(run/'diag.sv').write_text(src)
models=[Path(x) for x in (root/'vendor.f').read_text().splitlines() if x.strip()]
for p in models:
 print('MODEL_DELAYS',p.name,flush=True)
 for i,s in enumerate(p.read_text().splitlines()):
  if re.search(r'\(CLK.*Q|specparam.*(?:t|T)|Q_int.*<=|Q_int.*#',s):print(str(i+1)+' '+s.strip(),flush=True)
vcs=shutil.which('vcs')
b=run/'diag';b.mkdir()
with (b/'compile.log').open('w') as f:rc=subprocess.call([vcs,'-full64','-sverilog','-top','diag','-o',str(b/'simv'),str(run/'diag.sv'),str(models[0])],cwd=str(b),stdout=f,stderr=subprocess.STDOUT)
if rc:raise SystemExit('Diagnostic compile failed '+str(b))
with (b/'sim.log').open('w') as f:rc=subprocess.call([str(b/'simv')],cwd=str(b),stdout=f,stderr=subprocess.STDOUT)
for line in (b/'sim.log').read_text().splitlines():
 if 'DIAG' in line or 'Q_CHANGE' in line:print(line,flush=True)
original=root/'arch02/tb/tb_sram_adapter.sv'
text=original.read_text();assert text.count('        if(rvalid && rdata')==1
modified=text.replace('        if(rvalid && rdata','        #3; // Diagnostic data sample at posedge + 4 ns.\n        if(rvalid && rdata')
test=run/'tb_sram_adapter_sample4.sv';test.write_text(modified)
(run/'changes.json').write_text(json.dumps({'original_sha256':hashlib.sha256(original.read_bytes()).hexdigest(),'diagnostic_sha256':hashlib.sha256(test.read_bytes()).hexdigest(),'only_change':'post-posedge data compare delay 1 ns to 4 ns; valid check remains 1 ns; clock still 10 ns'},indent=2))
b=run/'adapter';b.mkdir()
sources=[root/'arch02/rtl/sram_port.sv',root/'arch02/rtl/sram_macro_adapter.sv',test]+models
with (b/'compile.log').open('w') as f:rc=subprocess.call([vcs,'-full64','-sverilog','-top','tb_sram_adapter','+incdir+'+str(root/'server_runs/20261107_234747_152837'),'-o',str(b/'simv')]+[str(p) for p in sources],cwd=str(b),stdout=f,stderr=subprocess.STDOUT)
if rc:raise SystemExit('Adapter compile failed '+str(b))
with (b/'sim.log').open('w') as f:rc=subprocess.call([str(b/'simv')],cwd=str(b),stdout=f,stderr=subprocess.STDOUT)
print((b/'sim.log').read_text(),flush=True)
print('SAMPLE_TIMING_DIAGNOSTIC',run,'exit',rc,flush=True)
PY
