"""Reject inconsistent complete-task timing and unreviewed integration inputs."""
import ast
from pathlib import Path
import unittest
import dma16_soc as soc
import install_dma16 as installer


class IntegrationContractTests(unittest.TestCase):
    def setUp(self):
        self.result=dict(first_request_cycle=10,final_response_cycle=110,cycles=100)
        self.text=('DMA16_TASK_WINDOW finished=1 failed=0 failure_code=0 start_cycle=10 '
            'end_cycle=110 cycles=100 start_ns=66.666660 end_ns=733.333260 '
            'finished_cycle=116 finished_ns=773.333256 source_bytes=46976 '
            'input_write_bytes=46976 input_read_bytes=46976 output_bytes=50688\n')

    def test_final_ack_excludes_later_drain_proof(self):
        window=soc.read_window(self.text,self.result)
        self.assertEqual(window['cycles'],100)
        self.assertEqual(window['finished_cycle'],116)
        self.assertEqual(window['transfer_bytes'],191616)

    def test_mutations_rejected(self):
        for old,new in [('failed=0','failed=1'),('cycles=100','cycles=101'),
            ('733.333260','733.3332619'),('source_bytes=46976','source_bytes=0'),
            ('finished_cycle=116','finished_cycle=109')]:
            # Beyond the accepted 2 fs precision tolerance for time mutation.
            if old=='733.333260':new='733.333263'
            with self.subTest(old=old),self.assertRaises(ValueError):
                soc.read_window(self.text.replace(old,new),self.result)

    def test_duplicate_window_rejected(self):
        with self.assertRaises(ValueError):soc.read_window(self.text*2,self.result)

    def test_unimplemented_reference_rejected_before_copy(self):
        with self.assertRaises(ValueError):installer.install(Path('missing'),Path('unused'),'mmio8_reference')

    def test_top_sysmem_restore(self):
        original='module e203_soc_top(input hfextclk);\nwire sysmem_icb_cmd_valid;\nwire sysmem_icb_cmd_ready;\n'
        old=dict(cmd_valid='sysmem_icb_cmd_valid',cmd_ready='sysmem_icb_cmd_ready',cmd_addr='',cmd_read='',
                 cmd_wdata='',cmd_wmask='',rsp_valid='sysmem_icb_cmd_valid',rsp_ready='sysmem_icb_cmd_ready',
                 rsp_rdata="32'b0",rsp_err="1'b0")
        original+='thing u('+','.join('.sysmem_icb_%s(%s)'%item for item in old.items())+');\nendmodule'
        patched=installer.patch_soc(original)
        for name,width in installer.FIELDS:
            self.assertIn('.sysmem_icb_%s(sysmem_icb_%s)'%(name,name),patched)
        self.assertIn('input wire [31:0] sysmem_icb_rsp_rdata,',patched)
        self.assertIn('output wire [31:0] sysmem_icb_cmd_addr,',patched)
        with self.assertRaises(ValueError):installer.patch_soc(patched)

    def test_server_python36_syntax(self):
        for name in ('dma16_soc.py','install_dma16.py','server_run.py'):
            ast.parse(Path(__file__).with_name(name).read_text(),feature_version=(3,6))

    def test_passive_metrics_include_after_monitor_and_duplicate_rejected(self):
        original='module tb_top;\n`include "arch03_dma16_monitor.svh"\nendmodule\n'
        patched=soc.add_bus_metrics(original)
        self.assertLess(patched.index('arch03_dma16_monitor.svh'),patched.index('arch03_dma16_metrics.svh'))
        self.assertLess(patched.index('arch03_dma16_metrics.svh'),patched.index('endmodule'))
        for bad in (original+original,original.replace('dma16_monitor','unknown'),patched):
            with self.assertRaises(ValueError):soc.add_bus_metrics(bad)

    def test_metrics_never_enter_production_source_list(self):
        self.assertFalse(any('bus_metrics' in str(p) for p in soc.source_list()))
        code=soc.binding_include(soc.RTL_METRIC_BINDINGS)
        self.assertIn('.arb_rsp_ready('+soc.RTL_MEM+'.u_arch03_arb.rsp_ready)',code)


if __name__=='__main__':unittest.main()
