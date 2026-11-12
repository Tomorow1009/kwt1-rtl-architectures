"""Offline mapped numeric-boundary and structural parser guard tests."""
import copy
import unittest
from n1_structure import numeric_width_inventory, no_load_drivers


def fixture():
    def module(ports,logic=''):
        return dict(ports={p:dict(direction='input',bounds=None if w==1 else [w-1,0]) for p,w in ports.items()},logic=logic)
    pe='arch03_n1_systolic_pe';array='arch03_n1_systolic5x16';quant='arch03_n1_requantize'
    return {'e203_soc_top':module({'clk':1},array+' array0 (.clk(clk));\n'+
            '\n'.join(quant+' q%d (.value(n));'%i for i in range(80))),
        array:module({'in_x':70,'in_w':192,'result_sum':2560},
            '\n'.join(pe+' p%d (.x_in(x));'%i for i in range(80))),
        pe:module({'x_in':26,'w_in':24,'result_sum':32}),
        quant:module({'value':33,'shift':5,'result':16,'saturated':1})}


class N1StructureTests(unittest.TestCase):
    def test_actual_boundary_widths_and_instance_count_are_required(self):
        mapped=fixture();result=numeric_width_inventory(mapped)
        self.assertEqual(result['counts'],{'pe':80,'array':1,'requantize':80})
        self.assertFalse(result['numeric_function_verified'])
        self.assertFalse(result['internal_total_capture_verified'])
        for module,port,width in [('arch03_n1_systolic_pe','result_sum',40),
                ('arch03_n1_requantize','value',41),('arch03_n1_systolic5x16','in_x',80)]:
            bad=copy.deepcopy(mapped);bad[module]['ports'][port]['bounds']=[width-1,0]
            with self.assertRaisesRegex(ValueError,'width mismatch'):numeric_width_inventory(bad)

    def test_missing_optimized_or_recursive_boundary_is_not_assumed_passed(self):
        mapped=fixture()
        bad=copy.deepcopy(mapped);del bad['arch03_n1_requantize']
        with self.assertRaisesRegex(ValueError,'Missing mapped'):numeric_width_inventory(bad)
        bad=copy.deepcopy(mapped);bad['e203_soc_top']['logic']=bad['e203_soc_top']['logic'].replace('arch03_n1_requantize q79 (.value(n));','')
        with self.assertRaisesRegex(ValueError,'instance count'):numeric_width_inventory(bad)
        bad=copy.deepcopy(mapped);bad['arch03_n1_systolic_pe']['logic']='e203_soc_top recur (.clk(clk));'
        with self.assertRaisesRegex(ValueError,'Recursive'):numeric_width_inventory(bad)

    def test_pin_continuations_are_not_fake_cell_instances(self):
        mapped={'top':{'logic':'leaf u0 (.out(n0),\n .clk(clk));\nleaf \\bank[1].u1  (.out(n1));'},'leaf':{'logic':''}}
        text="\n".join("Warning: In design 'top', net '%s' driven by pin '%s/out' has no loads. (LINT-2)" %
                       pair for pair in [('n0','u0'),('n1','bank[1].u1')])
        result=no_load_drivers(text,mapped,[dict(design='leaf',port='out',warning='LINT-8',disposition='declaration_only')])
        self.assertTrue(result['matches_declaration_only_unloaded_ports'])
        self.assertEqual(result['count'],2)


if __name__=='__main__':unittest.main()
