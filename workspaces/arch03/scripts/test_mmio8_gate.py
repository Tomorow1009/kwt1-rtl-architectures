"""Mapped-reference tool contracts; these fixtures are not EDA evidence."""
import ast
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import tkinter
import mmio8_gate as g
from test_dma16_gate import top


def fixture():
    lines = []
    for role, spec in g.interfaces().items():
        path = 'actual_chip/actual_memory/'+g.SUFFIXES[role]
        lines.append('cell\t%s\t%s\t%s' % (role, path, g.REFERENCES[role]))
        lines += ['pin\t%s\t%s/%s\t%s' % (role, path, name, direction)
                  for name, direction in g.shared.port_bits(spec).items()]
    for name in ('test_mode', 'pllbypass', 'plloutdivby1'):
        lines.append('guard\t%s\tactual_chip/u_e203_subsys_hclkgen/%s\tin' % (name, name))
    lines.append('guard\tbootrom_selected\tactual_aon/u_sirv_aon_wrapper/bootrom_deglitch/io_q\tout')
    return '\n'.join(lines)+'\n'


class Mmio8GateTests(unittest.TestCase):
    def test_actual_modules_bind_original_monitor_without_internal_aliases(self):
        probe = g.parse_probe(fixture())
        self.assertFalse(probe['DMA_present'])
        self.assertFalse(probe['alias_binding_used'])
        original = (g.A3/'tb/arch03_mmio8_source_monitor.svh').read_text()
        generated = g.generate_monitor(original, probe['bindings'])
        self.assertIn('u_e203_soc_top.actual_chip.actual_memory.u_arch03_arb.cpu_cmd_valid', generated)
        self.assertIn('u_e203_soc_top.actual_chip.actual_memory.u_arch03_router.transaction_pending', generated)
        self.assertIn('u_e203_soc_top.actual_chip.actual_memory.u_arch03_accel.rsp_rdata[31]', generated)
        self.assertIn('if(!m8_armed || !m8_cleared)', generated)
        self.assertIn('m8_copies>=m8_sources', generated)
        self.assertIn('m8_end_ns=$realtime', generated)
        self.assertNotIn('`M8MEM', generated)
        self.assertNotIn('a3_cpu_', generated)
        self.assertNotIn('a3_arb_pending', generated)

    def test_bad_probe_port_shape_identity_and_hierarchy_fail(self):
        text = fixture()
        pin = next(x for x in text.splitlines() if '/cpu_cmd_addr[17]\t' in x)
        for changed in (text.replace(pin+'\n', ''), text+pin+'\n',
                        text.replace(pin, pin.rsplit('\t', 1)[0]+'\tout'),
                        text.replace('arch03_icb_accel', 'arch03_dma16_accel'),
                        text.replace('actual_memory/u_arch03_router', 'elsewhere/u_arch03_router'),
                        text.replace('/cpu_cmd_addr[17]', '/cpu_cmd_addr[35]'),
                        text.replace('/bootrom_deglitch/io_q', '/bootrom_deglitch/wrong')):
            with self.subTest(changed=changed[-80:]), self.assertRaises(ValueError):
                g.parse_probe(changed)

    def test_monitor_requires_all_observed_pins_and_no_unresolved_alias(self):
        probe = g.parse_probe(fixture()); original = (g.A3/'tb/arch03_mmio8_source_monitor.svh').read_text()
        with self.assertRaises(ValueError):
            g.generate_monitor(original, {'accel': 'wrong'})
        with self.assertRaises(ValueError):
            g.generate_monitor(original+'\nwire new_alias=`M8MEM.private_state;\n', probe['bindings'])

    def test_gate_tb_uses_original_source_monitor_and_complete_top_ports(self):
        tb = g.testbench(top(), g.parse_probe(fixture()))
        self.assertIn('arch03_mmio8_gate_monitor.svh', tb)
        self.assertNotIn('arch03_dma16_metrics.svh', tb)
        self.assertNotIn('arch03_dma16_gate_monitor.svh', tb)
        self.assertIn('always #3.333333 clk', tb)
        self.assertIn('.sysmem_icb_rsp_rdata(a3_source_rsp_rdata)', tb)
        with self.assertRaises(ValueError):
            g.testbench(top().replace('[31:0] sysmem_icb_rsp_rdata', '[30:0] sysmem_icb_rsp_rdata'), g.parse_probe(fixture()))

    def test_probe_is_read_only_and_targets_original_accelerator(self):
        with tempfile.TemporaryDirectory() as directory:
            run = Path(directory); (run/'libs').mkdir(); dbs = []
            for name in ('std', 'small', 'large'):
                p = run/'libs'/(name+'.db'); p.write_text(name); dbs.append(p)
            (run/'source_inputs.json').write_text(json.dumps({str(p): g.sha(p) for p in dbs}))
            script = g.probe_script(run)
        self.assertEqual(tkinter.Tcl().call('info', 'complete', script), 1)
        self.assertIn('accel arch03_icb_accel u_arch03_accel', script)
        self.assertNotIn('core arch03_linear16', script)
        self.assertIn(g.PROBE_MARKER, script)
        for bad in ('compile ', 'write -format', 'set_dont_touch', 'set_false_path'):
            self.assertNotIn(bad, script)

    def test_synthesis_rejects_old_scope_or_DMA16_even_with_matching_digest(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); run = root/'session/mmio8_synth'; run.mkdir(parents=True)
            summary = dict(scope='dma16_whole_soc_task_mode_preliminary_synthesis',
                           DMA_present=True, synthesis_completed=True)
            (run/'summary.json').write_text(json.dumps(summary)); digest = g.sha(run/'summary.json')
            (run.parent/'state.json').write_text(json.dumps({'stages': {'mmio8_synth': {
                'status': 'passed', 'summary_sha256': digest}}}))
            with self.assertRaisesRegex(ValueError, 'Fresh original-MMIO8'):
                g.verify_synthesis(run, digest, {'server_root': str(root)})
            with self.assertRaisesRegex(ValueError, 'digest'):
                g.verify_synthesis(run, '0'*64, {'server_root': str(root)})

    def test_activity_adapter_preserves_exact_scan_and_unknown_records(self):
        mocked = dict(status='scope_and_window_verified', unknown_value_records=19,
            sha256='a'*64, dma16_header={'status': 'dma16_declarations_verified', 'source_port_bits': 106},
            auditor={'kind': 'complete_native_stream_scan_and_SHA256_plus_dma16_header'})
        with patch.object(g.fabric_activity, 'audit_activity', return_value=mocked) as scan:
            result = g.audit_activity(Path('case.vcd'), {'start_ns': '1'}, Path('run'), 'callback')
        scan.assert_called_once()
        self.assertEqual(result['unknown_value_records'], 19)
        self.assertEqual(result['mmio8_source_header']['source_port_bits'], 106)
        self.assertEqual(result['sha256'], 'a'*64)
        self.assertNotIn('dma16_header', result)

    def test_python36_and_reject_invalid_case_before_tools(self):
        ast.parse(Path(g.__file__).read_text(), feature_version=(3, 6))
        for cases in ([], ['layer_01', 'layer_01'], ['layer_99']):
            with self.assertRaises(ValueError):
                g.verify({}, Path('.'), Path('.'), '0'*64, cases, None)


if __name__ == '__main__':
    unittest.main()
