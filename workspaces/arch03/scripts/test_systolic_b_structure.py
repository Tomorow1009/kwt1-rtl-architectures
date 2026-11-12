"""Mapped named-port formatting must not become a false cell instance."""
import unittest
from systolic_b_structure import no_load_drivers


class StructureTests(unittest.TestCase):
    def test_named_pin_continuations_and_escaped_instance(self):
        logic=r'''
  leaf u0 (.out(n0),
      .clk(clk), .rst(rst));
  leaf \bank[1].u1  (.out(n1),
      .clk(clk), .rst(rst));
'''
        mapped={'top':{'logic':logic},'leaf':{'logic':''}}
        report="\n".join("Warning: In design 'top', net '%s' driven by pin '%s/out' has no loads. (LINT-2)"%
            pair for pair in [('n0','u0'),('n1','bank[1].u1')])
        report+='\n  Unloaded nets (LINT-2)                         2\n'
        ports=[dict(design='leaf',port='out',warning='LINT-8',disposition='declaration_only')]
        result=no_load_drivers(report,mapped,ports)
        self.assertTrue(result['matches_declaration_only_unloaded_ports'])
        self.assertEqual(result['count'],2)
        self.assertEqual(result['unique_driver_ports'],1)

    def test_actual_duplicate_instance_still_rejected(self):
        with self.assertRaisesRegex(ValueError,'Duplicate mapped instance u0'):
            no_load_drivers('',{'top':{'logic':'leaf u0 (.a(a));\nleaf u0 (.a(b));'}},[])


if __name__=='__main__':unittest.main()
