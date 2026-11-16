import unittest
from c32_mapped_repair import equivalent_tokens, verify_cells, TARGETS, sizing_script


class RepairProof(unittest.TestCase):
    def fixture(self):
        cells='\n'.join('%s %s (.I(a),.Z(b));'%(v[0],p.rsplit('/',1)[1]) for p,v in sorted(TARGETS.items()))
        old='module core(input a,output b);\n'+cells+'\nendmodule'
        return old,old.replace('BUFV2RD_12TR40','BUFV4RD_12TR40')

    def test_exact_three(self):
        old,new=self.fixture();proof=equivalent_tokens(old,new)
        self.assertEqual(len(proof['changes']),3)

    def test_changed_wire_rejected(self):
        old,new=self.fixture()
        with self.assertRaises(ValueError):equivalent_tokens(old,new.replace('.I(a)','.I(b)',1))

    def test_partial_replacement_rejected(self):
        old,new=self.fixture()
        with self.assertRaises(ValueError):equivalent_tokens(old,new.replace('BUFV4RD','BUFV2RD',1))

    def test_extra_cell_rejected(self):
        old,new=self.fixture()
        with self.assertRaises(ValueError):equivalent_tokens(old,new.replace('endmodule','BUFV4RD_12TR40 U0(.I(a),.Z(b)); endmodule'))

    def test_leaf_proof(self):
        old='\n'.join('%s\t%s\t1\tlib/%s'%(p,v[0],v[0]) for p,v in sorted(TARGETS.items()))+'\nother\tINV\t2\tlib/INV'
        new=old.replace('BUFV2RD','BUFV4RD').replace('\t1\t','\t2\t')
        self.assertEqual(verify_cells(old,new)['area_delta_um2'],3)
        with self.assertRaises(ValueError):verify_cells(old,new.replace('other\tINV\t2','other\tINV\t3'))

    def test_no_compile_and_equivalence(self):
        script=sizing_script()
        self.assertNotIn('\ncompile ',script)
        self.assertIn('function differs',script)
        self.assertIn('remove_attribute $object dont_touch',script)


if __name__=='__main__':unittest.main()
