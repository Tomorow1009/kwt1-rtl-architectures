#!/bin/sh
set -eu
cd "$(dirname "$0")"
python3 - <<'PY'
from pathlib import Path
import json,hashlib,shutil,subprocess,sys
source=Path('arch02_server_r01').resolve();target=Path('arch02_server_r02').resolve()
if target.exists():raise SystemExit('Refusing existing revision '+str(target))
manifest=json.loads((source/'manifest.json').read_text())
for rel,digest in manifest['files'].items():
 p=(source/rel).resolve()
 if source not in p.parents or hashlib.sha256(p.read_bytes()).hexdigest()!=digest:raise SystemExit('Source manifest mismatch '+rel)
target.mkdir()
for rel in manifest['files']:
 dest=target/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(str(source/rel),str(dest))
tb='`timescale 1ns/1ps\nmodule adapter_case #(parameter AW=7,LAT=1)(output reg done=0);\n    reg clk=0;always #5 clk=~clk;\n    reg rst_n=0,cs=0,we=0;\n    reg [AW-1:0] addr=0;\n    reg [15:0] wdata=0;\n    wire [15:0] rdata;wire rvalid;\n    arch02_sram_port #(.AW(AW),.READ_LATENCY(LAT)) dut(.*);\n    reg [15:0] reference[0:(1<<AW)-1];\n    reg [15:0] expected[0:LAT-1];\n    reg [LAT-1:0] valid=0;\n    integer j,n;\n    always @(posedge clk) begin\n        if(!rst_n) valid=0;\n        else begin\n            for(j=LAT-1;j>0;j=j-1) begin\n                valid[j]=valid[j-1];expected[j]=expected[j-1];\n            end\n            valid[0]=cs && !we;\n            if(cs && we) reference[addr]=wdata;\n            if(cs && !we) expected[0]=reference[addr];\n        end\n        #1;\n        if(rvalid!==valid[LAT-1]) $fatal(1,"Adapter valid AW=%0d LAT=%0d",AW,LAT);\n        // Vendor Q updates at posedge + 1 ns; avoid comparing in that time slot.\n        // Check data at +4 ns, before the next falling edge (+5 ns).\n        // A reset in this interval cancels the return through rvalid.\n        #3;\n        if(rvalid && rdata!==expected[LAT-1])\n            $fatal(1,"Adapter data AW=%0d LAT=%0d expected=%h actual=%h",AW,LAT,expected[LAT-1],rdata);\n    end\n    task drive(input c,input w,input [AW-1:0] a,input [15:0] d);\n        begin @(negedge clk);cs=c;we=w;addr=a;wdata=d;end\n    endtask\n    initial begin\n        repeat(2) @(negedge clk);rst_n=1;\n        drive(1,1,0,16\'h1357);drive(1,1,(1<<AW)-1,16\'hface);\n        drive(1,1,(1<<(AW-1)),16\'h8001);\n        drive(1,0,0,0);drive(1,0,(1<<AW)-1,0);drive(1,0,(1<<(AW-1)),0);\n        drive(0,1,0,16\'hffff);drive(1,0,0,0);\n        for(n=0;n<120;n=n+1) begin\n            drive(n%7!=0,n%4==0,n%2 ? (1<<AW)-1 : 0,16\'h3100+n);\n        end\n        drive(1,0,0,0);\n        @(posedge clk);#2;rst_n=0;#1;\n        if(rvalid!==0) $fatal(1,"Reset failed to cancel return");\n        // cs remains asserted through reset; the macro must be disabled.\n        repeat(2) @(negedge clk);cs=0;rst_n=1;\n        drive(1,1,0,16\'h2468);drive(1,0,0,0);\n        drive(0,0,0,0);repeat(4) @(negedge clk);\n        $display("PASS adapter AW=%0d latency=%0d",AW,LAT);done=1;\n    end\nendmodule\nmodule tb_sram_adapter;\n    wire [3:0] done;\n    adapter_case #(7,1) a(done[0]);adapter_case #(7,2) b(done[1]);\n    adapter_case #(12,1) c(done[2]);adapter_case #(12,2) d(done[3]);\n    initial begin wait(&done);$display("PASS: SRAM adapter cases=4");$finish;end\n    initial begin #100000;$fatal(1,"Adapter watchdog");end\nendmodule\n\n// Verify the substitute\'s per-bit mask and Q-hold contract independently.\n`ifdef ARCH02_PIN_MOCK\nmodule tb_pin_mask;\n    reg CLK=0;always #5 CLK=~CLK;\n    reg CEN=1,GWEN=1;reg [15:0] WEN=16\'hffff,D=0;\n    reg [6:0] A=0;wire [15:0] Q;\n    RAMSP128X16 dut(.CLK(CLK),.CEN(CEN),.GWEN(GWEN),.WEN(WEN),\n        .D(D),.A(A),.Q(Q),.EMA(3\'b000),.EMAW(2\'b00),.RET1N(1\'b1));\n    integer b;\n    initial begin\n        @(negedge CLK);CEN=0;GWEN=0;WEN=0;D=16\'haaaa;\n        @(negedge CLK);GWEN=1;WEN=16\'hffff;\n        @(negedge CLK);if(Q!==16\'haaaa) $fatal(1,"Mock full write");\n        GWEN=0;WEN=16\'hff00;D=16\'h0055;\n        @(negedge CLK);if(Q!==16\'haaaa) $fatal(1,"Q changed on write");\n        GWEN=1;\n        @(negedge CLK);if(Q!==16\'haa55) $fatal(1,"Mock partial write");\n        CEN=1;GWEN=0;WEN=0;D=0;\n        @(negedge CLK);if(Q!==16\'haa55) $fatal(1,"Q changed disabled");\n        CEN=0;GWEN=1;\n        @(negedge CLK);if(Q!==16\'haa55) $fatal(1,"Disabled write modified memory");\n        for(b=0;b<16;b=b+1) begin\n            GWEN=0;WEN=~(16\'h1<<b);D=16\'hffff;\n            @(negedge CLK);GWEN=1;\n            @(negedge CLK);\n            if(Q!==(16\'haa55 | (16\'hffff>>(15-b)))) $fatal(1,"Bit mask mismatch bit=%0d",b);\n        end\n        $display("PASS: pin mock masks and hold");$finish;\n    end\nendmodule\n`endif\n'
changed=target/'arch02/tb/tb_sram_adapter.sv';changed.write_text(tb)
manifest['files']['arch02/tb/tb_sram_adapter.sv']=hashlib.sha256(changed.read_bytes()).hexdigest()
manifest['revision']='r02'
manifest['changes']=['Testbench valid compare remains posedge+1ns; data compare posedge+4ns avoids observed vendor Q update race at +1ns. Core RTL unchanged.']
manifest['status']='vendor_regression_pending'
(target/'manifest.json').write_text(json.dumps(manifest,indent=2))
for name in ['vendor_config.json','vendor.f']:shutil.copy2(str(source/name),str(target/name))
print('REVISION_READY '+str(target),flush=True)
cmd=[sys.executable,'vcs_run.py','--mode','all','--config','vendor_config.json','--filelist','vendor.f']
with (target/'full_run_console.log').open('w') as log:
 proc=subprocess.Popen(cmd,cwd=str(target),stdout=subprocess.PIPE,stderr=subprocess.STDOUT,universal_newlines=True)
 for line in proc.stdout:log.write(line);log.flush();print(line,end='',flush=True)
 rc=proc.wait()
if rc:
 runs=sorted((target/'server_runs').glob('*'));latest=runs[-1]
 print((latest/'summary.json').read_text(),flush=True)
 for p in sorted(latest.rglob('*.log')):
  text=p.read_text(errors='replace')
  if 'Fatal' in text or 'Error' in text or 'error' in text:print('FAILURE_LOG '+str(p)+'\n'+'\n'.join(text.splitlines()[-50:]),flush=True)
sys.exit(rc)
PY
