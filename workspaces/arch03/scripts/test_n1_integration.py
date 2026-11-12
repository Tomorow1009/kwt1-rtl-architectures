"""Independent N1 integration boundaries and monitor-fixture tests.

The RTL fixture drives two known outputs through the passive observer. It does
not execute E203 or DUT arithmetic and must never be reported as a SoC PASS.
"""
import copy
import datetime
import json
import os
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest
from unittest import mock

import build_n1_firmware as firmware
import n1_batch
import n1_codec
import n1_data
import n1_soc
import n1_synth
import n1_bus_metrics

ROOT = Path(__file__).resolve().parents[3]
A3 = ROOT/'workspaces/arch03'
ZIG = ROOT.parent/'takeover_local/tools/zig-windows-x86_64-0.13.0/zig.exe'
VIVADO = Path('D:/Xilinx/Vivado/2018.3/bin')
DATA = A3/'local_runs/n1_data14_20261113_02/prepared/extremes'


def execute(command, cwd, log):
    environment = os.environ.copy()
    environment['ZIG_LOCAL_CACHE_DIR'] = str(cwd/'zig-local-cache')
    environment['ZIG_GLOBAL_CACHE_DIR'] = str(ROOT/'local_runs/zig-n1-integration-cache')
    process = subprocess.run([str(part) for part in command], cwd=str(cwd),
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=environment)
    text = process.stdout.decode('utf8', errors='replace')
    (cwd/log).write_text(text, encoding='utf8')
    return process.returncode, text


class BoundaryTests(unittest.TestCase):
    def test_boot_rejects_old_shift_layout_task_preload_and_bad_lengths(self):
        base = bytearray(262144)
        boot = firmware.metadata_image(base, 10, 32, 5, n1_codec.LAYOUT)
        self.assertEqual(struct.unpack_from('<4I', boot, 0xfff0), (10, 32, 0x00100004, 5))
        for shift in (0, 9, 11, 12, 31, True):
            with self.assertRaises(ValueError): firmware.metadata_image(base, shift)
        for layout in (0x00100002, 0x00100003, 0x00100005):
            with self.assertRaises(ValueError): firmware.metadata_image(base, 10, layout=layout)
        for size in (0, 28, 33, 47012, 2**32):
            with self.assertRaises(ValueError): firmware.metadata_image(base, 10, encoded_bytes=size)
        for at in (0xfff0, 0x10000, 262143):
            damaged = bytearray(base); damaged[at] = 1
            with self.assertRaises(ValueError): firmware.metadata_image(damaged, 10)

    def test_actual_compiled_firmware_identity(self):
        folder = ROOT/'local_runs/n1_firmware_irq_20261113_0105'
        if not (folder/'manifest.json').is_file(): self.skipTest('Local compiled firmware is unavailable')
        meta, base = n1_soc.verify_firmware(folder)
        self.assertEqual(meta['peripheral_id'], '0x4b575306')
        self.assertEqual(meta['numeric_format'], '0x000e0c20')
        self.assertEqual(set(meta['images']), {'shift_10'})
        self.assertFalse(any(base[0xfff0:]))
        self.assertTrue(meta['configuration']['irq_enabled'])

    def test_port_contract_rejects_missing_reversed_and_duplicate_bits(self):
        rows = ['%s\t%s' % pair for pair in sorted(n1_synth.sysmem_bits().items())]
        self.assertEqual(n1_synth.verify_ports('\n'.join(rows))['bits'], 106)
        for text in ('\n'.join(rows[:-1]), '\n'.join(rows+[rows[0]]),
                     '\n'.join([rows[0].replace('\tin', '\tout')]+rows[1:])):
            # The first lexicographic signal is an output; force its opposite.
            if text == '\n'.join(rows):
                text = '\n'.join([rows[0].replace('\tout', '\tin')]+rows[1:])
            with self.assertRaises(ValueError): n1_synth.verify_ports(text)

    def test_top_contract_requires_all_original_sysmem_signals(self):
        declarations = []
        for name, (direction, width) in n1_synth.SYSMEM.items():
            declarations.append('%s wire %ssysmem_icb_%s' %
                                ('input' if direction == 'in' else 'output',
                                 '' if width == 1 else '[%d:0] ' % (width-1), name))
        top = 'module e203_soc_top('+','.join(declarations)+'); endmodule'
        n1_synth.verify_top_sysmem(top)
        with self.assertRaises(ValueError): n1_synth.verify_top_sysmem(top.replace('[31:0]', '[63:0]', 1))
        with self.assertRaises(ValueError): n1_synth.verify_top_sysmem(top.replace('sysmem_icb_cmd_addr', 'other_addr'))
        for report in ('', 'Checking loops\nWarning: TIM-209 loop breakpoint'):
            with self.assertRaises(ValueError): n1_synth.require_loop_free_timing(report)

    def test_batch_real_identity_path_precedes_first_run(self):
        # Execute all real identity-building code, stopping immediately before
        # the first simulator run; catches wrong Path/string and stale keys.
        with tempfile.TemporaryDirectory(dir=str(ROOT/'local_runs'), prefix='n1_batch_boundary_') as temp:
            run = Path(temp); fwdir = run/'fw'; fwdir.mkdir()
            n1_data.save(fwdir/'manifest.json', {})
            n1_data.save(run/'manifest.json', dict(format=n1_data.FORMAT))
            n1_data.save(run/'n1_build_contract.json', {})
            source = run/'source'; source.mkdir(); n1_data.save(source/'layout.json', {})
            tasks = [dict(shift=10, key='task_%04d'%i, source=str(source),
                          source_layout_sha256=n1_data.sha(source/'layout.json'), sample=i//12+1, layer=i%12+1)
                     for i in range(1200)]
            contract = dict(diagnostic=None, row_lanes=5, layout_id=0x00100004, firmware=str(fwdir))
            fw = dict(configuration=dict(irq_enabled=True), numeric_format='0x000e0c20')
            with mock.patch.object(n1_batch.data, 'index_dataset', return_value=tasks), \
                 mock.patch.object(n1_batch, 'storage_guard'), \
                 mock.patch.object(n1_batch.soc, 'compile_design', return_value=(contract, {}, fw, b'')), \
                 mock.patch.object(n1_batch.soc, 'verify_frozen'), \
                 mock.patch.object(n1_batch.soc, 'run_case', side_effect=RuntimeError('STOP_BEFORE_SIMULATION')) as sim:
                with self.assertRaisesRegex(RuntimeError, 'STOP_BEFORE_SIMULATION'):
                    n1_batch.verify({}, run, run, run, None)
                self.assertEqual(sim.call_count, 1)
            identity = n1_data.read(run/'batch_identity.json')
            self.assertEqual(identity['schema'], 'arch03-n1-batch-v4')
            self.assertEqual(identity['runner_sha256'], n1_data.sha(n1_batch.__file__))
            self.assertEqual(identity['capture_columns'], ['row', 'column', 'result', 'saturated', 'total'])

    def test_compile_contract_binds_transitive_data_and_monitor_tools(self):
        source = Path(n1_soc.__file__).read_text()
        # These are execution dependencies, beyond RTL/model hashes. A source
        # change after compilation must invalidate the frozen run contract.
        for filename in ('n1_data.py', 'n1_codec.py', 'systolic_b_data.py', 'systolic_b_codec.py',
                         'icb32_codec.py', 'dma16_batch.py', 'n1_batch.py',
                         'n1_bus_metrics.py', 'build_n1_firmware.py'):
            self.assertTrue(filename in source, 'Missing frozen execution dependency '+filename)

    def test_n1_metrics_numeric_valid_bits_and_old_schema_rejection(self):
        template = (A3/'tb/arch03_n1_metrics.svh').read_text()
        self.assertIn('pe.x_in[25]', template)
        self.assertIn('pe.w_in[23]', template)
        self.assertNotIn('pe.x_in[27]', template)
        self.assertNotIn('pe.w_in[27]', template)
        source = n1_bus_metrics.instrument((A3/'tb/arch03_n1_monitor.svh').read_text(), 5)
        self.assertNotIn('@ROWS@', source)
        self.assertEqual(source.count('a3_report_metrics;'), 2)  # task declaration and one call
        values = dict(rows=5, cycles=30000, encoded_bytes=30000,
                      x_reads=101376, x_writes=6336, w_reads=327680, w_writes=16384,
                      mac_updates=1622016, command_ready_wait=0, response_backpressure=0,
                      pending_response_wait=0, turnovers=100, result_stalls=0)
        lines = ['ICB32_METRICS schema=n1_passive_v1 '+' '.join('%s=%d'%pair for pair in values.items())]
        lines += ['ICB32_METRIC_PHASE phase=%d acks=%d latency_sum=%d latency_max=1'%(i, n, n)
                  for i, n in enumerate((7500, 7500, 12672))]
        text = '\n'.join(lines)
        window = dict(cycles=30000, encoded_bytes=30000, transfer_transactions=27672)
        parsed = n1_bus_metrics.parse_metrics(text, window)
        self.assertEqual(parsed['measured']['mac_updates'], 1622016)
        with self.assertRaises(ValueError):
            n1_bus_metrics.parse_metrics(text.replace('schema=n1_passive_v1', 'schema=systolic_b_passive_v1'), window)

    @unittest.skipUnless(ZIG.is_file(), 'Zig unavailable')
    def test_actual_driver_config_validator_on_host(self):
        source = (A3/'sw/kwt_n1.c').read_text()
        begin = source.index('static int valid_config(')
        end = source.index('\nint kwt_icb32_run', begin)
        validator = source[begin:end]
        harness = '#include "kwt_n1.h"\n'+validator+r'''
int main(void) {
 struct kwt_icb32_config c={0xb0000000u,0xa0000000u,0xa000c000u,10,47008,1,1,0x00100004u}, t;
 if(!valid_config(&c) || valid_config(0))return 1;
 for(unsigned s=0;s<32;s++){t=c;t.shift=s;if(valid_config(&t)!=(s==10))return 2;}
 t=c;t.layout=0x00100003u;if(valid_config(&t))return 3;
 t=c;t.encoded_bytes=47012;if(valid_config(&t))return 4;
 t=c;t.encoded_bytes=33;if(valid_config(&t))return 5;
 t=c;t.output=c.input+4;if(valid_config(&t))return 6;
 t=c;t.input=0xfffffffcu;if(valid_config(&t))return 7;
 t=c;t.output=0xa007ff00u;if(valid_config(&t))return 8;
 t=c;t.source=0xb000bffcu;if(valid_config(&t))return 9;
 t=c;t.input++;if(valid_config(&t))return 10;
 t=c;t.prefetch=2;if(valid_config(&t))return 11;
 t=c;t.dma_mode=0;if(valid_config(&t))return 12;
 return 0;
}
'''
        with tempfile.TemporaryDirectory(dir=str(ROOT/'local_runs'), prefix='n1_driver_boundary_') as temp:
            folder = Path(temp); path = folder/'validator.c'; path.write_text(harness)
            executable = folder/'validator.exe'
            code, text = execute([ZIG, 'cc', '-Wall', '-Wextra', '-Werror', '-I', A3/'sw', path, '-o', executable], folder, 'compile.log')
            self.assertEqual(code, 0, text)
            code, text = execute([executable], folder, 'run.log')
            self.assertEqual(code, 0, text)


FIXTURE = r'''
`timescale 1ns/1fs
module n1_fixture_core;
 reg enabled=0; reg [79:0] pe_valid=0; reg [719:0] pe_block=0;
 reg [8:0] slot_block[0:1]; reg [6:0] slot_row[0:1]; reg [3:0] slot_tile[0:1];
 reg [1:0] occupied=0; reg signed [32:0] converted_total[0:79]; integer i;
 initial begin for(i=0;i<2;i=i+1)begin slot_block[i]=0;slot_row[i]=0;slot_tile[i]=0;end
 for(i=0;i<80;i=i+1)converted_total[i]=0;end
endmodule
module n1_fixture_transport; reg empty=1; endmodule
module n1_fixture_dma;
 reg [31:0] error_q=0,input_bytes_q=32,decoded_words=0,load_count_q=0;
 reg half_q=0,core_done_q=0,committed_valid=0,committed_ready=0,load_fire=0;
 reg [31:0] committed_data=0; reg [2:0] core_load_count=0; reg [63:0] core_load_data=0;
 reg core_out_valid=0,core_out_ready=1;reg [6:0] core_row=0;reg [7:0] core_col=0;
 reg [31:0] core_result=0;reg [1:0] core_sat=0;
 n1_fixture_core core();n1_fixture_transport transport();
endmodule
module n1_fixture_mems(input clk,rst_n);
 reg expl_axi_icb_cmd_valid=0,expl_axi_icb_cmd_ready=1,expl_axi_icb_cmd_read=1;
 reg [31:0] expl_axi_icb_cmd_addr=0,expl_axi_icb_cmd_wdata=0;reg [3:0] expl_axi_icb_cmd_wmask=15;
 reg a3_dma_cmd_valid=0,a3_dma_cmd_ready=1,a3_dma_cmd_read=1,a3_dma_rsp_valid=0,a3_dma_rsp_ready=1,a3_dma_rsp_err=0;
 reg [31:0] a3_dma_cmd_addr=0;reg [3:0] a3_dma_cmd_wmask=15;
 reg a3_arb_pending=0,a3_router_pending=0;
 reg a3_mem_rsp_valid=0,a3_mem_rsp_ready=1,a3_mem_rsp_err=0;
 reg a3_mem_cmd_valid=0,a3_mem_cmd_ready=1,a3_mem_cmd_read=1;
 reg [31:0] a3_mem_cmd_addr=0,a3_mem_cmd_wdata=0;reg [3:0] a3_mem_cmd_wmask=15;
 n1_fixture_dma u_arch03_accel();
endmodule
module n1_fixture_main(input clk,rst_n);n1_fixture_mems u_e203_subsys_mems(clk,rst_n);endmodule
module n1_fixture_subsys(input clk,rst_n);n1_fixture_main u_e203_subsys_main(clk,rst_n);endmodule
module n1_fixture_soc(input clk,rst_n);n1_fixture_subsys u_e203_subsys_top(clk,rst_n);endmodule
module tb_n1_monitor_fixture;
 reg clk=0,rst_n=0;always #3.333333 clk=~clk;
 n1_fixture_soc u_e203_soc_top(clk,rst_n);
 reg a3_source_cmd_valid=0,a3_source_cmd_read=1,a3_source_rsp_ready=1;
 reg [31:0] a3_source_cmd_addr=32'hb0000000,a3_source_cmd_wdata=0;reg [3:0] a3_source_cmd_wmask=15;
 wire a3_source_cmd_ready,a3_source_rsp_valid,a3_source_rsp_err;wire [31:0] a3_source_rsp_rdata;
 `include "arch03_n1_monitor.svh"
 `define M u_e203_soc_top.u_e203_subsys_top.u_e203_subsys_main.u_e203_subsys_mems
 `define D `M.u_arch03_accel
 integer scenario=0;
 task write_pair;
 begin
  @(negedge clk);`M.a3_mem_cmd_valid=1;`M.a3_mem_cmd_read=0;
  `M.a3_mem_cmd_addr=32'ha000c200;`M.a3_mem_cmd_wdata=32'h7fff8000;
  @(negedge clk);`M.a3_mem_cmd_valid=0;`M.a3_mem_rsp_valid=1;
  @(negedge clk);`M.a3_mem_rsp_valid=0;
 end
 endtask
 initial begin
  if(!$value$plusargs("SCENARIO=%d",scenario))scenario=0;
  repeat(3)@(negedge clk);rst_n=1;
  @(negedge clk);`D.core.enabled=1;`D.core.occupied=1;
  `D.core.converted_total[16]=-33'sd3221094400;
  `D.core.converted_total[17]=33'sd3220570175;
  if(scenario==1)`D.core.converted_total[16]=-33'sd3221094399;
  if(scenario==3)`D.core.slot_block[0]=2;
  if(scenario==4)begin `D.core.slot_row[0]=95;`D.core.pe_valid[64]=1;end
  else if(scenario!=5)begin `D.core.pe_valid[16]=1;`D.core.pe_valid[17]=1;end
  @(negedge clk);
  if(scenario==2)begin @(negedge clk);end
  `D.core.pe_valid=0;
  `D.core_out_valid=1;`D.core_row=1;`D.core_col=0;
  `D.core_result=32'h7fff8000;`D.core_sat=3;
  @(negedge clk);`D.core_out_valid=0;
  write_pair;
  if(scenario==6)write_pair;
  if(n1_total_count!=2 || a3_outputs!=2 || n1_actual_total[256]!==-33'sd3221094400 ||
     n1_actual_total[257]!==33'sd3220570175)$fatal(1,"Fixture did not capture native signed33 values");
  $fclose(a3_file);
  $display("N1_MONITOR_FIXTURE_PASS outputs=2 cpu_executed=false arithmetic_executed=false");$finish;
 end
 `undef D
 `undef M
endmodule
'''


@unittest.skipUnless((VIVADO/'xvlog.bat').is_file() and DATA.is_dir(), 'Vivado/fixed N1 extremes unavailable')
class MonitorFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.run_dir = ROOT/'local_runs'/('n1_monitor_fixture_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
        cls.run_dir.mkdir()
        tb = cls.run_dir/'fixture.sv';tb.write_text(FIXTURE)
        files = [A3/'tb/arch03_icb32_source.sv', A3/'tb/arch03_task_window_icb32.sv', tb]
        code, text = execute([VIVADO/'xvlog.bat', '--sv', '-i', A3/'tb']+files, cls.run_dir, 'compile.log')
        if code: raise AssertionError(text)
        code, text = execute([VIVADO/'xelab.bat', 'tb_n1_monitor_fixture', '-s', 'n1_observer_fixture'], cls.run_dir, 'elaborate.log')
        if code: raise AssertionError(text)
        (cls.run_dir/'run.tcl').write_text('run all\nquit\n')
        cls.bytes = n1_data.read(DATA/'codec.json')['encoded_bytes']

    def scenario(self, number):
        capture = self.run_dir/('scenario_%d.csv' % number)
        arguments = ['DATA_DIR='+DATA.resolve().as_posix(), 'CAPTURE='+capture.resolve().as_posix(),
                     'LOAD32='+(DATA/'codec32.hex').resolve().as_posix(), 'CODEC_BYTES='+str(self.bytes),
                     'LAYOUT='+str(n1_codec.LAYOUT), 'SCENARIO='+str(number)]
        options = self.run_dir/('scenario_%d.options' % number)
        options.write_text('n1_observer_fixture\n-tclbatch run.tcl\n'+
                           ''.join('-testplusarg '+argument+'\n' for argument in arguments))
        command = [VIVADO/'xsim.bat', '-f', options]
        code, text = execute(command, self.run_dir, 'scenario_%d.log' % number)
        return code, text, capture

    def test_native_total_is_retained_until_actual_write_response(self):
        code, text, capture = self.scenario(0)
        self.assertEqual(code, 0, text)
        self.assertIn('N1_MONITOR_FIXTURE_PASS outputs=2 cpu_executed=false', text)
        self.assertEqual(capture.read_text().splitlines(), ['1,0,-32768,1,-3221094400', '1,1,32767,1,3220570175'])

    def test_monitor_rejects_bad_total_duplicate_stale_tail_and_missing_proof(self):
        expected = {1:'N1 total mismatch',2:'N1 total duplicate/invalid',3:'N1 total stale result ownership',
                    4:'N1 total duplicate/invalid',5:'DMA actual writeback mismatch',6:'DMA actual writeback mismatch'}
        for scenario, marker in expected.items():
            with self.subTest(scenario=scenario):
                _, text, _ = self.scenario(scenario)
                self.assertIn(marker, text)
                self.assertNotIn('N1_MONITOR_FIXTURE_PASS', text)


if __name__ == '__main__':
    unittest.main()
