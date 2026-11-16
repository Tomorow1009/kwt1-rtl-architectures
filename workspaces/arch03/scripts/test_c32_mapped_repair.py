import unittest
import copy
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

    def test_repaired_route_cannot_claim_fresh_or_skip_proof(self):
        import c32_mapped_repair as repair
        from c32_review_contract import route_identity
        route=dict(scope=repair.SCOPE,old_linked_ddc_reused=True,block_cache_reused=True,
            mapped_repair=dict(schema='c32-equivalent-cell-repair-v1',
                original_summary_sha256=repair.ORIGIN_SHA,original_netlist_sha256=repair.ORIGIN_NETLIST,
                original_scope='c32_partitioned_whole_soc_task_mode',targets={k:list(v) for k,v in TARGETS.items()},
                rtl_modified=False,topology_changed=False,task_constraints_unchanged=True,
                inherited_gate_pass=False,requires_new_gate_and_ppa=True,only_size_cell_no_compile=True),
            repair_identity=dict(schema='c32-three-buffer-token-proof-v1',all_other_verilog_tokens_identical=True,
                leaf_identity=dict(all_other_leaves_identical=True)))
        self.assertTrue(route_identity(route))
        for key in ('old_linked_ddc_reused','block_cache_reused'):
            changed=copy.deepcopy(route);changed[key]=False
            self.assertFalse(route_identity(changed))
        for key,value in [('original_summary_sha256','0'*64),('inherited_gate_pass',True),
                          ('task_constraints_unchanged',False),('targets',{})]:
            changed=copy.deepcopy(route);changed['mapped_repair'][key]=value
            self.assertFalse(route_identity(changed))
        changed=copy.deepcopy(route);changed['repair_identity']={}
        self.assertFalse(route_identity(changed))


if __name__=='__main__':unittest.main()
