import ast
import copy
from pathlib import Path
import unittest
import dma16_unknown_netlist as p

NETLIST = r'''module child (a, y);
 input [3:0] a;
 output y;
 wire [3:0] a;
 wire [31:0] error_q;
 wire [31:0] output_q;
 wire \fifo[0] ;
 wire spare;
 CELL g (.A(a[2:0]), .Y(y));
 CELL g2 (.A(output_q[1:0]), .Y(\fifo[0] ));
endmodule
module e203_soc_top (a, y);
 input [3:0] a;
 output y;
 child \gen[0].core (.a(a), .y(y));
endmodule
'''


def signal(identifier, aliases):
    return dict(identifier=identifier, aliases=aliases, unknown_records=1,
                unknown_records_after_begin=0, unknown_at_end=True,
                any_unknown_ticks=100, unobserved_prefix_ticks=0)


class UnknownNetlistTests(unittest.TestCase):
    def setUp(self):
        self.index = p.index_netlist(NETLIST)
        self.prefix = p.ROOT+'.gen[0].core.'

    def test_dotted_escaped_instance_resolves_exact_vector_bits(self):
        row = p.resolve_alias(self.prefix+'a [3]', self.index)
        self.assertEqual(row['disposition'], 'mapped_declaration_only')
        self.assertEqual(p.resolve_alias(self.prefix+'a [2]', self.index)['expression_occurrences'], 1)
        self.assertEqual(p.resolve_alias(self.prefix+'a [3:0]', self.index)['expression_occurrences'], 1)

    def test_declaration_only_internal_bit_and_used_scalar_remain_distinct(self):
        for name in ['error_q [31]', 'output_q [31]', 'spare']:
            self.assertEqual(p.resolve_alias(self.prefix+name, self.index)['disposition'], 'mapped_declaration_only')
        self.assertEqual(p.resolve_alias(self.prefix+'fifo[0]', self.index)['expression_occurrences'], 1)

    def test_whole_vector_and_variable_select_prevent_false_waiver(self):
        for expr in ['a', 'a[output_q]']:
            index = p.index_netlist(NETLIST.replace('a[2:0]', expr))
            self.assertEqual(p.resolve_alias(self.prefix+'a [3]', index)['disposition'], 'mapped_expression_requires_time_review')

    def test_named_pin_label_is_not_a_signal_use(self):
        index = p.index_netlist(NETLIST.replace('.A(a[2:0])', '.spare(a[2:0])'))
        self.assertEqual(p.resolve_alias(self.prefix+'spare', index)['expression_occurrences'], 0)

    def test_variable_index_net_itself_is_a_use(self):
        index = p.index_netlist(NETLIST.replace('a[2:0]', 'a[error_q]'))
        self.assertEqual(p.resolve_alias(self.prefix+'error_q [31]', index)['expression_occurrences'], 1)

    def test_external_model_and_missing_names_are_never_waived(self):
        row = p.resolve_alias(self.prefix+'g.internal', self.index)
        self.assertEqual(row['disposition'], 'external_model_internal_requires_review')
        self.assertEqual(row['reference'], 'CELL')
        self.assertEqual(p.resolve_alias(self.prefix+'absent', self.index)['disposition'], 'unresolved_mapped_signal_requires_review')
        with self.assertRaises(ValueError): p.resolve_alias('other.y', self.index)

    def test_all_aliases_must_be_declaration_only(self):
        rows = [signal('a', [self.prefix+'spare']),
                signal('b', [self.prefix+'spare', self.prefix+'a [2]']),
                signal('c', [self.prefix+'spare', self.prefix+'g.internal'])]
        out = p.classify(dict(signals=rows), self.index)
        self.assertEqual(out['disposition_counts'], {'all_aliases_mapped_declaration_only': 1,
            'mapped_expression_requires_time_review': 1, 'model_or_unresolved_alias_requires_review': 1})
        self.assertFalse(out['system_power_verified'])
        self.assertEqual(sum(x['identifiers'] for x in out['canonical_scope_counts'].values()), 3)
        self.assertEqual(sum(out['alias_disposition_counts'].values()), 5)

    def test_no_alias_missing_duplicate_or_out_of_bounds_can_pass(self):
        with self.assertRaises(ValueError): p.resolve_alias(self.prefix+'a [4]', self.index)
        for rows in [[signal('a', [])], [signal('a', [self.prefix+'spare'])]*2]:
            with self.assertRaises(ValueError): p.classify(dict(signals=rows), self.index)

    def test_unknown_and_unobserved_durations_are_preserved_without_power_bound(self):
        row = signal('a', [self.prefix+'a [2]']); row['unobserved_prefix_ticks'] = 50
        before = copy.deepcopy(row); result = p.classify(dict(signals=[row]), self.index)
        self.assertEqual(row, before)
        self.assertEqual(result['identifiers'][0]['unobserved_prefix_ticks'], 50)
        self.assertEqual(result['identifiers'][0]['any_unknown_ticks'], 100)

    def test_comments_do_not_create_references_and_malformed_structure_is_rejected(self):
        index = p.index_netlist(NETLIST.replace('CELL g ', '// error_q[31]\nCELL g '))
        self.assertEqual(p.resolve_alias(self.prefix+'error_q [31]', index)['expression_occurrences'], 0)
        for bad in [NETLIST.replace('wire spare;', "wire spare=1'b0;"),
                    NETLIST.replace('child \\gen[0].core', 'e203_soc_top \\gen[0].core'),
                    NETLIST.replace('wire spare;', 'wire [1:0] a;'),
                    NETLIST.replace('CELL g ', 'always @(a) y=a;\nCELL g ')]:
            with self.assertRaises(ValueError): p.index_netlist(bad)

    def test_python36_grammar(self):
        ast.parse(Path(p.__file__).read_text(), feature_version=(3, 6))


if __name__ == '__main__': unittest.main()
