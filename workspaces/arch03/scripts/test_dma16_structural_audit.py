import ast
import json
from pathlib import Path
import tempfile
import unittest
import dma16_structural_audit as p

NETLIST = '''module example (mask, a, y);
  input [3:0] mask;
  input [39:0] a;
  output y;
  wire [3:0] mask;
  wire spare;
  gate g (.mask(1'b0), .A(a[38:0]), .Z(y));
endmodule
'''
REPORT = ("Warning: In design 'example', port 'mask[3]' is not connected to any nets. (LINT-28)\n"
          "Warning: In design 'example', input port 'a[39]' is unloaded. (LINT-8)\n")


class StructuralTests(unittest.TestCase):
    def test_declared_unused_bits_and_named_instance_ports_are_not_logic_uses(self):
        result = p.classify(REPORT, NETLIST)
        self.assertEqual(result['disposition_counts'], {'declaration_only': 2})
        self.assertEqual(result['direction_counts'], {'input': 2})
        self.assertFalse(p.uses(p.modules(NETLIST)['example'], 'a[39]')['expression_occurrences'])

    def test_used_bit_slice_whole_vector_and_output_remain_for_review(self):
        module = p.modules(NETLIST)['example']
        self.assertEqual(p.uses(module, 'a[38]')['disposition'], 'expression_present_requires_review')
        self.assertEqual(p.uses(module, 'y')['direction'], 'output')
        whole = p.modules(NETLIST.replace('a[38:0]', 'a'))['example']
        self.assertEqual(p.uses(whole, 'a[39]')['expression_occurrences'], 1)
        variable = p.modules(NETLIST.replace('a[38:0]', 'a[mask]'))['example']
        self.assertEqual(p.uses(variable, 'a[39]')['expression_occurrences'], 1)
        self.assertEqual(p.uses(variable, 'mask[3]')['expression_occurrences'], 1)

    def test_comments_do_not_add_logic_references(self):
        text = NETLIST.replace('gate g', '// mask[3] a[39]\n /* mask a */\n gate g')
        self.assertEqual(p.classify(REPORT, text)['disposition_counts'], {'declaration_only': 2})

    def test_missing_duplicate_ansi_and_initialized_declarations_are_rejected(self):
        for bad in (NETLIST+NETLIST, NETLIST.replace('module example', 'module example # (parameter X=1)'),
                    NETLIST.replace('(mask, a, y)', '(input mask, a, y)'),
                    NETLIST.replace('wire spare;', "wire spare=1'b0;"),
                    NETLIST.replace('output y;', ''), NETLIST.replace('module example', 'modul example')):
            with self.assertRaises(ValueError): p.modules(bad)

    def test_every_port_warning_must_parse_and_match_a_real_declared_bit(self):
        for bad in (REPORT+REPORT, REPORT.replace('example', 'absent'), REPORT.replace('mask[3]', 'mask[8]'),
                    REPORT.replace('a[39]', 'other'), REPORT.replace('is unloaded', 'changed wording'),
                    REPORT+"Warning: unexpected unclassified detail\n"):
            with self.assertRaises(ValueError): p.classify(bad, NETLIST)

    def test_all_warning_classes_remain_in_inventory_without_automatic_waiver(self):
        text = REPORT+"Warning: fixed cell has no loads. (LINT-1)\n"
        result = p.classify(text, NETLIST)
        self.assertEqual(result['warning_counts']['LINT-1'], 1)
        self.assertEqual(result['port_warning_count'], 2)

    def test_artifact_identity_and_original_receipt_are_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); run = root/'dma16_synth'; run.mkdir()
            (run/'mapped.v').write_text(NETLIST); (run/'check_design_mapped.rpt').write_text(REPORT)
            summary = dict(scope='dma16_whole_soc_task_mode_preliminary_synthesis',
                           artifacts={n: p.sha(run/n) for n in ('mapped.v', 'check_design_mapped.rpt')})
            (run/'summary.json').write_text(json.dumps(summary)); digest = p.sha(run/'summary.json')
            (root/'state.json').write_text(json.dumps({'stages': {'dma16_synth': {'status': 'passed', 'summary_sha256': digest}}}))
            result = p.audit(run, digest)
            self.assertFalse(result['timing_verified']); self.assertFalse(result['netlist_modified'])
            with self.assertRaisesRegex(ValueError, 'digest'): p.audit(run, '0'*64)
            (run/'mapped.v').write_text(NETLIST+'//changed')
            with self.assertRaisesRegex(ValueError, 'changed'): p.audit(run, digest)

    def test_python36_grammar(self):
        ast.parse(Path(p.__file__).read_text(), feature_version=(3, 6))


if __name__ == '__main__': unittest.main()
