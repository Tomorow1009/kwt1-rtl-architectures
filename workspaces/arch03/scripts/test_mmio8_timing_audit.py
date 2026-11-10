import ast
from pathlib import Path
import tempfile
import tkinter
import unittest
from unittest.mock import patch
import mmio8_timing_audit as a
from test_dma16_power import fake_databases
from test_mmio8_gate import fixture


class Mmio8TimingTests(unittest.TestCase):
    def test_query_targets_original_eight_lane_probe_and_is_read_only(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);fake_databases(root)
            text=a.script(root)
            self.assertEqual(tkinter.Tcl().call('info','complete',text),1)
            self.assertIn('all_high_fanout -nets -threshold 1000',text)
            self.assertIn('accel arch03_icb_accel u_arch03_accel',text)
            self.assertIn(a.gate.PROBE_MARKER,text)
            for bad in ('compile_ultra','write -format','set_false_path','core arch03_linear16'):
                self.assertNotIn(bad,text)
        with patch.object(a.gate,'probe_script',return_value='changed'):
            with self.assertRaises(ValueError):a.script(Path('.'))

    def test_actual_query_binds_files_and_rejects_changed_ddc(self):
        for mutate in (False,True):
            with tempfile.TemporaryDirectory() as directory:
                root=Path(directory);synth=root/'synthesis';synth.mkdir();run=root/'run';run.mkdir()
                fake_databases(synth)
                for name in ('mapped.ddc','mapped.v','mapped.sdc','summary.json'):(synth/name).write_text('fixture')
                def call(command,where,log):
                    self.assertEqual(command[:2],['dc_shell','-f']);self.assertEqual(where,run)
                    (run/'mapped_port_probe.tsv').write_text(fixture())
                    (run/'high_fanout.tsv').write_text('threshold\t1000\ncount\t1\nnet\ttop/hfclk\n')
                    if mutate:(synth/'mapped.ddc').write_text('changed')
                    return a.gate.PROBE_MARKER
                with patch.object(a.gate,'verify_synthesis') as verify:
                    if mutate:
                        with self.assertRaisesRegex(ValueError,'input changed'):
                            a.audit({'tools':{'dc_shell':'dc_shell'}},run,synth,'a'*64,call)
                    else:
                        result=a.audit({'tools':{'dc_shell':'dc_shell'}},run,synth,'a'*64,call)
                        self.assertEqual(verify.call_count,2)
                        self.assertEqual(result['high_fanout']['nets'],['top/hfclk'])
                        self.assertFalse(result['DMA_present']);self.assertFalse(result['strict_timing_verified'])
                        self.assertFalse(result['netlist_modified'])

    def test_python36_grammar(self):
        ast.parse(Path(a.__file__).read_text(),feature_version=(3,6))


if __name__=='__main__':unittest.main()
