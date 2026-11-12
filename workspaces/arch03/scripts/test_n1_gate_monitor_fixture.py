"""Execute generated mapped-observer checks with public-pin procedural stubs.

This tests monitor behavior only. No E203, arithmetic or mapped standard cells
are executed; it must never be counted as the N1 fourteen-case gate acceptance.
"""
from datetime import datetime
from pathlib import Path
import json
import subprocess
import unittest

import n1_gate as gate
from test_n1_gate import probe

VIVADO=Path('D:/Xilinx/Vivado/2018.3/bin')
DATA=gate.A3/'local_runs/n1_data14_20261113_02/prepared/extremes'


def fixture():
    modules=[]
    for role in ('core','decoder','accel','shared','arb','router'):
        text=['module fixture_'+role+'(input wire clk,rst_n);']
        for name,(_,width) in gate.interfaces()[role].items():
            if name in ('clk','rst_n'):continue
            initial=1 if name.endswith('ready') else 0
            text.append('reg %s%s=%d;' % ('' if width==1 else '[%d:0] '%(width-1),name,initial))
        if role=='accel':
            text+=['fixture_core core(clk,rst_n);','fixture_decoder decoder(clk,rst_n);']
        modules.append('\n'.join(text+['endmodule']))
    return '\n'.join(modules)+r'''
module fixture_mems(input clk,rst_n);
 fixture_accel u_arch03_accel(clk,rst_n);
 fixture_shared u_arch03_shared(clk,rst_n);
 fixture_arb u_arch03_arb(clk,rst_n);
 fixture_router u_arch03_router(clk,rst_n);
endmodule
module fixture_soc(input clk,rst_n);fixture_mems actual_mems(clk,rst_n);endmodule
module tb_n1_gate_monitor_fixture;
 reg clk=0,rst_n=0;always #3.333333 clk=~clk;
 fixture_soc u_e203_soc_top(clk,rst_n);
 reg a3_source_cmd_valid=0,a3_source_cmd_read=1,a3_source_rsp_ready=1;
 reg [31:0] a3_source_cmd_addr=32'hb0000000,a3_source_cmd_wdata=0;
 reg [3:0] a3_source_cmd_wmask=15;
 wire a3_source_cmd_ready,a3_source_rsp_valid,a3_source_rsp_err;
 wire [31:0] a3_source_rsp_rdata;
 `include "arch03_n1_gate_monitor.svh"
 `define C u_e203_soc_top.actual_mems.u_arch03_accel.core
 `define S u_e203_soc_top.actual_mems.u_arch03_shared
 integer scenario=0;
 task write_pair;
 begin
  @(negedge clk);`S.cmd_valid=1;`S.cmd_read=0;
  `S.cmd_addr=32'ha000c200;`S.cmd_wdata=scenario==5 ? 32'h7fff8001 : 32'h7fff8000;`S.cmd_wmask=15;
  @(negedge clk);`S.cmd_valid=0;`S.rsp_valid=1;
  @(negedge clk);`S.rsp_valid=0;
 end
 endtask
 initial begin
  if(!$value$plusargs("SCENARIO=%d",scenario))scenario=0;
  repeat(3)@(negedge clk);rst_n=1;
  @(negedge clk);
  if(scenario!=4)begin
   `C.out_valid=1;`C.out_row=1;`C.out_column=0;
   `C.result=scenario==1 ? 32'h7fff8001 : 32'h7fff8000;
   `C.saturated=scenario==2 ? 0 : 3;
   @(negedge clk);
   if(scenario==3)@(negedge clk);
   `C.out_valid=0;
  end
  write_pair;
  if(scenario==6)write_pair;
  if(a3_outputs!=2 || a3_core_outputs!=2 || a3_actual_sat[256]!==1 || a3_actual_sat[257]!==1)
   $fatal(1,"Mapped-observer fixture did not retain actual outputs/saturation");
  $fclose(a3_file);
  $display("N1_GATE_MONITOR_FIXTURE_PASS outputs=2 cpu_executed=false mapped_design=false total_checked=false");
  $finish;
 end
 `undef S
 `undef C
endmodule
'''


@unittest.skipUnless((VIVADO/'xvlog.bat').is_file() and DATA.is_dir(), 'Vivado/fixed N1 extremes unavailable')
class N1GateMonitorFixtureTests(unittest.TestCase):
    @classmethod
    def command(cls,argv,log):
        result=subprocess.run([str(x) for x in argv],cwd=str(cls.folder),stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        text=result.stdout.decode('utf8',errors='replace')
        (cls.folder/log).write_text(text,encoding='utf8')
        return result.returncode,text

    @classmethod
    def setUpClass(cls):
        cls.folder=gate.ROOT/'local_runs'/('n1_gate_monitor_fixture_'+datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
        cls.folder.mkdir()
        text,frozen=probe();receipt=gate.parse_probe(text,frozen)
        generated=gate.generate((gate.A3/'tb/arch03_n1_monitor.svh').read_text(),receipt['bindings'])
        (cls.folder/'arch03_n1_gate_monitor.svh').write_text(generated)
        tb=cls.folder/'fixture.sv';tb.write_text(fixture())
        files=[gate.A3/'tb'/n for n in ('arch03_icb32_source.sv','arch03_task_window_icb32.sv','arch03_icb32_gate_proof.sv')]+[tb]
        code,text=cls.command([VIVADO/'xvlog.bat','--sv','-i',cls.folder]+files,'compile.log')
        if code:raise AssertionError(text)
        code,text=cls.command([VIVADO/'xelab.bat','tb_n1_gate_monitor_fixture','-s','fixture'],'elaborate.log')
        if code:raise AssertionError(text)
        (cls.folder/'run.tcl').write_text('run all\nquit\n')
        cls.byte_count=json.loads((DATA/'codec.json').read_text())['encoded_bytes']

    def scenario(self,number):
        capture=self.folder/('case_%d.csv'%number)
        options=self.folder/('case_%d.options'%number)
        arguments=['DATA_DIR='+DATA.resolve().as_posix(),'CAPTURE='+capture.resolve().as_posix(),
            'LOAD32='+(DATA/'codec32.hex').resolve().as_posix(),'CODEC_BYTES='+str(self.byte_count),
            'LAYOUT=1048580','SCENARIO='+str(number)]
        options.write_text('fixture\n-tclbatch run.tcl\n'+''.join('-testplusarg '+x+'\n' for x in arguments))
        code,text=self.command([VIVADO/'xsim.bat','-f',options],'case_%d.log'%number)
        return code,text,capture

    def test_capture_uses_actual_results_and_saturation_at_write_ack(self):
        code,text,capture=self.scenario(0)
        self.assertEqual(code,0,text)
        self.assertIn('N1_GATE_MONITOR_FIXTURE_PASS',text)
        self.assertNotIn(gate.PROOF,text)
        self.assertEqual(capture.read_text().splitlines(),['1,0,-32768,1','1,1,32767,1'])

    def test_wrong_core_result_sat_duplicate_missing_core_and_write_are_rejected(self):
        expected={1:'B core value/saturation mismatch',2:'B core value/saturation mismatch',
                  3:'Invalid/duplicate B core coordinate',4:'DMA actual writeback mismatch',
                  5:'DMA actual writeback mismatch',6:'DMA actual writeback mismatch'}
        for number,marker in expected.items():
            with self.subTest(scenario=number):
                _,text,_=self.scenario(number)
                self.assertIn(marker,text)
                self.assertNotIn('N1_GATE_MONITOR_FIXTURE_PASS',text)


if __name__=='__main__':unittest.main()
