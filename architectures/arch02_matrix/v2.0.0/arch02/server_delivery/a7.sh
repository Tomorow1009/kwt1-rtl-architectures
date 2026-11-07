#!/bin/sh
set -eu
cd "$(dirname "$0")/arch02_server_r01"
python3 - <<'PY'
from pathlib import Path
import subprocess,re,datetime,shutil
root=Path.cwd();run=root/'server_runs'/('diagnostic_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'));run.mkdir()
model=Path('/storage1/admin_public_dir/SRAM_Lib_2025/RAMSP128X16/verilog/RAMSP128X16.v')
lines=model.read_text().splitlines();keep=set()
for i,s in enumerate(lines):
 if re.search(r'task\s+readwrite',s,re.I):
  end=next(j+1 for j in range(i+1,len(lines)) if 'endtask' in lines[j]);keep.update(range(i,end))
 if re.search(r'^\s*(initial|specparam|`define|`ifdef|`ifndef)|\$setuphold|\(CLK.*Q|buf.*(?:CLK_|CEN_|GWEN_)|assign.*(?:CLK_|CEN_|GWEN_)',s):keep.update(range(max(0,i-1),min(len(lines),i+12)))
(run/'model_details.txt').write_text('\n'.join('%d %s'%(i+1,lines[i]) for i in sorted(keep)))
tb=r'''`timescale 1ns/1ps
module diag;
reg CLK=0;always #50 CLK=~CLK;
reg CEN=1,GWEN=1;reg [15:0] WEN=16'hffff,D=0;reg [6:0] A=0;wire [15:0] Q;
RAMSP128X16 dut(.Q(Q),.CLK(CLK),.CEN(CEN),.GWEN(GWEN),.WEN(WEN),.A(A),.D(D),.EMA(3'd2),.EMAW(2'd0),.RET1N(1'b1));
always @(posedge CLK) begin
 #1;$display("DIAG +1 t=%0t cen=%b gwen=%b wen=%h q=%h delayed_clk=%b delayed_cen=%b delayed_gwen=%b ret=%b",$time,CEN,GWEN,WEN,Q,dut.CLK_,dut.CEN_,dut.GWEN_,dut.RET1N_);
 #39;$display("DIAG +40 t=%0t q=%h qint=%h mem0=%h",$time,Q,dut.Q_int,dut.mem[0]);
end
initial begin
 @(negedge CLK);CEN=0;GWEN=0;WEN=0;D=16'h1357;
 @(negedge CLK);GWEN=1;WEN=16'hffff;
 @(negedge CLK);$display("DIAG read=%h expected=1357",Q);CEN=1;
 @(negedge CLK);$finish;
end
endmodule
'''
(run/'diag.sv').write_text(tb)
for tag,flags in [('default',[]),('neg_tchk',['+neg_tchk']),('ud_model',['+define+ARM_UD_MODEL'])]:
 b=run/tag;b.mkdir()
 with (b/'compile.log').open('w') as f:r=subprocess.call([shutil.which('vcs'),'-full64','-sverilog','-top','diag','-o',str(b/'simv')]+flags+[str(run/'diag.sv'),str(model)],cwd=str(b),stdout=f,stderr=subprocess.STDOUT)
 print('COMPILE',tag,r,flush=True)
 if r:print('\n'.join((b/'compile.log').read_text().splitlines()[-20:]),flush=True);continue
 with (b/'sim.log').open('w') as f:r=subprocess.call([str(b/'simv')],cwd=str(b),stdout=f,stderr=subprocess.STDOUT)
 print('SIM',tag,r,flush=True)
 for line in (b/'sim.log').read_text().splitlines():
  if re.search(r'DIAG|Warning|Error|Fatal',line,re.I):print(line,flush=True)
print('DIAGNOSTIC_ONLY',run,flush=True)
PY
