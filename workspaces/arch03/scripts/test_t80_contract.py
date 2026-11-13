"""Independent route/traffic contracts for the new stage (no historical PASS)."""
import ast
from pathlib import Path
import unittest
import install_t80
from install_dma16 import FIELDS, connections, instance
from t80_window import read_window
import t80_soc
from t80_batch import select_first20


class T80Contract(unittest.TestCase):
    def test_fixed_first20_and_changed_inventory_rejection(self):
        tasks = [dict(sample=s, layer=l, shift=10) for s in range(1, 101) for l in range(1, 13)]
        selected = select_first20(tasks)
        self.assertEqual(len(selected), 240)
        self.assertEqual((selected[-1]['sample'], selected[-1]['layer']), (20, 12))
        for bad in (tasks[:240], tasks[::-1], tasks+[tasks[0]]):
            with self.assertRaises(ValueError):
                select_first20(bad)

    def baseline(self):
        # Same named boundaries as the immutable platform, with no RTL behavior.
        fields = ','.join('.i_icb_%s(mem_icb_%s)' % (k, k) for k, _ in FIELDS)
        fields += ",.i_icb_cmd_excl(1'b0),.i_icb_cmd_lock(1'b0),.i_icb_cmd_size(2'b0)"
        body = 'original_bus #(.SPLT_FIFO_OUTS_NUM(1),.SPLT_FIFO_CUT_READY(1)) mem_fab('+fields+');\n'
        body += instance('arch03_icb_arb2_turnover', 'u_arch03_arb',
            connections('a3_cpu_', 'cpu_')+connections('a3_dma_', 'dma_')+connections('a3_bus_'))
        body += instance('arch03_icb_memory_router_turnover', 'u_arch03_router',
            connections('a3_bus_')+connections('a3_mem_', 'mem_')+connections('sysmem_icb_', 'src_'))
        body += 'arch03_n1_accel u_arch03_accel();\n'
        return body

    def test_all_bus_signals_move_together_and_bus_parameters_survive(self):
        changed = install_t80.patch_mems(self.baseline())
        bus, arb, router = changed.split(');')[:3]
        for k, _ in FIELDS:
            self.assertIn('.i_icb_%s(a3_bus_%s)' % (k, k), bus)
            self.assertIn('.cpu_%s(mem_icb_%s)' % (k, k), arb)
            self.assertIn('.%s(a3_cpu_%s)' % (k, k), router)
            self.assertIn('.dma_%s(a3_dma_%s)' % (k, k), arb)
        self.assertIn('.SPLT_FIFO_OUTS_NUM(1),.SPLT_FIFO_CUT_READY(1)', bus)
        self.assertIn(".i_icb_cmd_excl(1'b0),.i_icb_cmd_lock(1'b0),.i_icb_cmd_size(2'b0)", bus)
        self.assertNotIn('arch03_n2', changed)
        with self.assertRaises(ValueError):
            install_t80.patch_mems(changed)

    def test_changed_original_and_duplicate_input_rejected(self):
        for bad in (self.baseline().replace('mem_icb_cmd_addr','unknown_addr'),
                    self.baseline()+'.i_icb_cmd_valid(mem_icb_cmd_valid)',
                    self.baseline().replace('u_arch03_router','unknown_router')):
            with self.subTest(text=bad), self.assertRaises(ValueError):
                install_t80.patch_mems(bad)

    def window(self):
        return ('ICB32_TASK_WINDOW finished=1 failed=0 failure_code=0 start_cycle=10 '
                'end_cycle=110 cycles=100 start_ns=66.666660 end_ns=733.333260 '
                'finished_cycle=112 finished_ns=746.666592 source_bytes=64 '
                'input_write_bytes=64 input_read_bytes=64 output_bytes=50688\n')

    def test_four_stage_counts_and_boundaries(self):
        result = dict(first_request_cycle=10, final_response_cycle=110, cycles=100)
        got = read_window(self.window(), result, 64)
        self.assertEqual(got['transfer_transactions'], 3*16+12672)
        self.assertEqual(got['transfer_bytes'], 3*64+50688)
        for old, new in [('input_read_bytes=64','input_read_bytes=0'),
                         ('finished_cycle=112','finished_cycle=109'),
                         ('end_ns=733.333260','end_ns=NaN'),
                         ('cycles=100','cycles=100 cycles=100')]:
            with self.subTest(old=old), self.assertRaises(ValueError):
                read_window(self.window().replace(old, new), result, 64)

    def test_sources_reuse_numeric_hardware_but_not_old_transport_or_gates(self):
        names = {p.name for p in t80_soc.source_list()}
        self.assertIn('arch03_n1_systolic5x16.sv', names)
        self.assertIn('arch03_n1_linear16x5.sv', names)
        self.assertIn('arch03_t80_transport.sv', names)
        self.assertIn('arch03_t80_accel.sv', names)
        self.assertFalse(any('n2' in p or 'icg' in p or 'systolic_b_transport' in p for p in names))
        for p in Path(__file__).parent.glob('*t80*.py'):
            ast.parse(p.read_text(), feature_version=(3, 6))


if __name__ == '__main__':
    unittest.main()
