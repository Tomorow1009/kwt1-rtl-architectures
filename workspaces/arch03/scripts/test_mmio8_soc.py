"""Parser/source-contract tests; no fake simulator results are ASIC evidence."""
import ast
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
import mmio8_soc as soc


def fixture_log():
    return '\n'.join(soc.MARKERS)+('\nMMIO8_SOURCE_WINDOW start_cycle=100 end_cycle=3000100 cycles=3000000 '
        'start_ns=666.666600 end_ns=20000664.666600 start_edge_ns=666.666600 start_phase_ns=0.000000 source_read_acks=11744 input_write_acks=11744 '
        'input_read_acks=23488 output_write_acks=25344 command_wait=7 response_wait=3\n'
        'ARCH03_MMIO8_SOURCE_PASS outputs=25344 cpu_executed=true cycles=3000000 cpu_cycles=3001000 saturated=5\n')


class Mmio8SocTests(unittest.TestCase):
    def test_exact_full_window_and_bus_accounting(self):
        result = soc.read_window(fixture_log(), 5)
        self.assertEqual(result['cycles'], 3000000)
        self.assertEqual(result['data_region_transaction_count'], 72320)
        self.assertEqual(result['data_region_bus_slot_bytes'], 289280)
        self.assertEqual(result['useful_bytes_by_phase'], dict(source_read=46976,
            initial_shared_write=46976, shared_input_read=46976, output_write=50688))
        self.assertIsNone(result['total_system_transactions'])
        self.assertEqual(result['task_per_second'], 50)

    def test_dma_counts_cannot_replace_halfword_cpu_transactions(self):
        for old, new in [('input_read_acks=23488', 'input_read_acks=11744'),
                         ('output_write_acks=25344', 'output_write_acks=12672')]:
            with self.subTest(old=old), self.assertRaises(ValueError):
                soc.read_window(fixture_log().replace(old, new), 5)

    def test_start_end_cycle_difference_has_no_plus_one(self):
        with self.assertRaises(ValueError):
            soc.read_window(fixture_log().replace('end_cycle=3000100', 'end_cycle=3000101'), 5)

    def test_wrong_clock_and_nonfinite_time_rejected(self):
        for value in ('20001666.666600', 'NaN', 'Infinity', 'invalid'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                soc.read_window(fixture_log().replace('20000664.666600', value), 5)

    def test_actual_first_valid_clock_phase_preserved_without_hiding_wait(self):
        text = fixture_log().replace('start_ns=666.666600', 'start_ns=667.666600').replace(
            'start_phase_ns=0.000000', 'start_phase_ns=1.000000')
        result = soc.read_window(text, 5)
        self.assertEqual(result['cycles'], 3000000)
        self.assertEqual(result['start_ns'], '667.666600')
        self.assertEqual(result['elapsed_ns'], '19999997.000000')
        self.assertEqual(result['counted_duration_ns'], '19999998.000000')
        for old, new in [('start_phase_ns=1.000000', 'start_phase_ns=0'),
                         ('start_phase_ns=1.000000', 'start_phase_ns=NaN'),
                         ('start_phase_ns=1.000000', 'start_phase_ns=6.666666'),
                         ('start_edge_ns=666.666600', 'start_edge_ns=667.666600'),
                         ('start_edge_ns=666.666600', 'start_edge_ns=659.999934')]:
            with self.subTest(new=new), self.assertRaises(ValueError):
                soc.read_window(text.replace(old, new), 5)
        with self.assertRaises(ValueError):
            soc.read_window(text.replace('start_edge_ns=666.666600 ', ''), 5)

    def test_missing_duplicate_and_changed_mode_markers_rejected(self):
        for text in (fixture_log().replace(soc.MARKERS[0], ''),
                     soc.MARKERS[0]+'\n'+fixture_log(), fixture_log().replace('test_mode=0', 'test_mode=1')):
            with self.subTest(text=text[:60]), self.assertRaises(ValueError):
                soc.read_window(text, 5)

    def test_unique_window_and_completion_required(self):
        for prefix in ('MMIO8_SOURCE_WINDOW ', 'ARCH03_MMIO8_SOURCE_PASS '):
            line = [line for line in fixture_log().splitlines() if line.startswith(prefix)][0]
            with self.subTest(prefix=prefix), self.assertRaises(ValueError):
                soc.read_window(fixture_log()+line+'\n', 5)

    def test_cpu_and_capture_counters_must_match(self):
        for text, saturation in ((fixture_log().replace('cpu_executed=true', 'cpu_executed=false'), 5),
                                 (fixture_log().replace('cpu_cycles=3001000', 'cpu_cycles=2999999'), 5),
                                 (fixture_log().replace('outputs=25344', 'outputs=25343'), 5),
                                 (fixture_log(), 4)):
            with self.subTest(text=text[-120:], saturation=saturation), self.assertRaises(ValueError):
                soc.read_window(text, saturation)

    def test_error_markers_override_pass(self):
        for marker in ('Fatal: deliberate failure', 'Error-[SYNTAX] incomplete', 'FAIL assertion',
                       'FATAL assertion', 'MMIO8_SOURCE_FAIL incomplete'):
            with self.subTest(marker=marker), self.assertRaises(ValueError):
                soc.read_window(fixture_log()+marker+'\n', 5)

    def test_duplicate_fields_and_negative_counters_rejected(self):
        for text in (fixture_log().replace('command_wait=7', 'command_wait=7 command_wait=0'),
                     fixture_log().replace('command_wait=7', 'command_wait=-1'),
                     fixture_log().replace('response_wait=3', '')):
            with self.subTest(text=text[-200:]), self.assertRaises(ValueError):
                soc.read_window(text, 5)

    def test_reject_dma_firmware_and_missing_source_identity_before_io(self):
        with patch.object(soc.common, 'read', return_value=dict(run_mode='single_cpu_dma16_v1')):
            with self.assertRaises(ValueError):soc.verify_firmware(Path('unused'))
        manifest = dict(run_mode='single_cpu_mmio8_source_v1', physical_boot_policy='firmware_only_no_task_inputs',
            task_source_address='0xb0000000', shared_input_address='0xa0000000', shared_output_address='0xa000c000',
            peripheral_id='0x4b575403', layout_tag='0x00080001',
            configuration=dict(irq_enabled=False, original_mmio_driver_unchanged=True), source_sha256={})
        with patch.object(soc.common, 'read', return_value=manifest):
            with self.assertRaisesRegex(ValueError, 'source identity'):soc.verify_firmware(Path('unused'))

    def test_reference_compile_list_contains_no_dma_or_lane16_core(self):
        names = {path.name for path in soc.source_list()}
        self.assertTrue({'arch02_linear.sv', 'arch03_icb_accel.sv', 'arch03_shared_sram.sv', 'arch03_tcm_ram.sv'} <= names)
        self.assertFalse({'arch03_dma16_accel.sv', 'arch03_linear16.sv'} & names)

    def test_python36_grammar_and_stdlib_runtime(self):
        text = Path(soc.__file__).read_text(encoding='utf8')
        tree = ast.parse(text, feature_version=(3, 6)) if sys.version_info >= (3, 8) else ast.parse(text)
        names = {item.names[0].name for item in ast.walk(tree) if isinstance(item, ast.Import)}
        self.assertFalse(names & {'numpy', 'tensorflow', 'numeric'})


if __name__ == '__main__':
    unittest.main()
