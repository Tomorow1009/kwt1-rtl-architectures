import unittest
import copy
import os
from pathlib import Path
import tempfile
import tkinter
from c32_mapped_repair import equivalent_tokens, verify_cells, TARGETS, sizing_script


class RepairProof(unittest.TestCase):
    def fixture(self):
        cells='\n'.join('%s %s (.I(a),.Z(b));'%(v[0],p.rsplit('/',1)[1]) for p,v in sorted(TARGETS.items()))
        old='module core(input a,output b);\n'+cells+'\nendmodule'
        new=old
        for before,after in set(TARGETS.values()):new=new.replace(before,after)
        return old,new

    def test_exact_inspected_drivers(self):
        old,new=self.fixture();proof=equivalent_tokens(old,new)
        self.assertEqual(len(proof['changes']),4)

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
        new=old.replace('BUFV2RD','BUFV4RD').replace('NOR3V2','NOR3V4').replace('\t1\t','\t2\t')
        self.assertEqual(verify_cells(old,new)['area_delta_um2'],4)
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
            repair_identity=dict(schema='c32-equivalent-driver-token-proof-v2',all_other_verilog_tokens_identical=True,
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

    def test_tcl_empty_optional_flag_is_restored_absent(self):
        # Reproduce DC's UID-101 behavior: absent attribute returns empty,
        # without a Tcl exception. Restoring it as a Boolean is illegal.
        t=tkinter.Tcl()
        t.eval(r'''
array set refs {}
array set flags {u_e203_subsys_top true}
proc get_cells {path} {return $path}
proc sizeof_collection {x} {return [llength $x]}
proc get_object_name {x} {return $x}
proc get_lib_cells {x} {return [string map {* lib} $x]}
proc get_lib_pins {x} {
 if {[string match */* $x] && [string index $x end] eq "*"} {
  return [list [string range $x 0 end-1]I [string range $x 0 end-1]Z]
 }
 return $x
}
proc foreach_in_collection {var items body} {uplevel 1 [list foreach $var $items $body]}
proc get_attribute {x attr} {
 global refs flags
 switch $attr {
  ref_name {return $refs($x)}
  direction {if {[string match */I $x]} {return in} {return out}}
  function {return I}
  dont_touch {if {[info exists flags($x)]} {return $flags($x)} {return {}}}
  default {error "Unexpected mock attribute"}
 }
}
proc set_dont_touch {x value} {
 global flags
 if {$value ni {true false}} {error "UID-133 Boolean required"}
 set flags($x) $value
}
proc remove_attribute {x attr} {global flags;unset flags($x)}
proc size_cell {x lib} {global refs;set refs($x) [lindex [split $lib /] end]}
''')
        for path,(before,after) in TARGETS.items():t.call('set','refs('+path+')',before)
        cwd=os.getcwd()
        with tempfile.TemporaryDirectory() as directory:
            try:
                os.chdir(directory);t.eval(sizing_script())
                self.assertEqual(t.eval('array size flags'),'1')
                self.assertEqual(t.eval('set flags(u_e203_subsys_top)'),'true')
                self.assertEqual(sum(line.startswith('cell\t') for line in Path('equivalent_sizing.tsv').read_text().splitlines()),4)
            finally:os.chdir(cwd)
        for path,(before,after) in TARGETS.items():self.assertEqual(t.getvar('refs('+path+')'),after)


if __name__=='__main__':unittest.main()
