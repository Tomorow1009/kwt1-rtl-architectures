import copy
import hashlib
import re
import unittest
from technology_binding import load_bindings,patch_generic_cells,verify_liberty


class BindingTests(unittest.TestCase):
    def setUp(self):
        self.bindings=load_bindings()
        self.source='// BUFV4_8TR40 is documented here, not instantiated.\n'
        for kind,spec in self.bindings['cells'].items():
            for index in range(spec['count']):
                ports=','.join('.%s(signal_%s)'%(p,p) for p in spec['ports'])
                self.source+='%s u_donttouch_%s_%d(%s);\n'%(kind,kind,index,ports)

    def test_exact_cell_inventory_and_unchanged_wiring(self):
        mapped,counts=patch_generic_cells(self.source)
        self.assertEqual(sum(counts.values()),23)
        self.assertTrue(mapped.startswith('// BUFV4_8TR40'))
        for kind,spec in self.bindings['cells'].items():
            self.assertEqual(len(re.findall(r'(?m)^'+re.escape(spec['target'])+r' u_donttouch_',mapped)),spec['count'])
        original_connections=[line[line.find('('):] for line in self.source.splitlines()[1:]]
        mapped_connections=[line[line.find('('):] for line in mapped.splitlines()[1:]]
        self.assertEqual(original_connections,mapped_connections)

    def test_missing_cell_wrong_pin_and_unknown_cell_fail(self):
        for text in (self.source.replace('BUFV4_8TR40 u_donttouch_','UNKNOWN u_donttouch_',1),
                     self.source.replace('.I(signal_I)','.BAD(signal_I)',1),
                     self.source[:self.source.rfind('\n',0,-1)+1]):
            with self.assertRaises(ValueError):patch_generic_cells(text)

    def test_library_identity_function_and_gate_type_fail_closed(self):
        # Tiny independently generated schema fixture, never a vendor library.
        data=copy.deepcopy(self.bindings)
        text=''
        for spec in data['cells'].values():
            text+='cell(%s) {\n'%spec['target']
            for pin in spec['pins']:text+='pin(%s) { }\n'%pin
            text+='%s : "%s";\n'%(spec.get('function_attribute','function'),spec['function'])
            if 'clock_gating_integrated_cell' in spec:
                text+='clock_gating_integrated_cell : "%s";\n'%spec['clock_gating_integrated_cell']
            text+='}\n'
        raw=text.encode();data['library_sha256']=hashlib.sha256(raw).hexdigest()
        self.assertEqual(verify_liberty(raw,data)['bound_cell_types'],11)
        with self.assertRaises(ValueError):verify_liberty(raw+b' ',data)
        for modified in (text.replace('function : "I"','function : "!I"',1),
                         text.replace('latch_posedge_postcontrol','latch_negedge'),
                         text.replace('pin(Z)','pin(WRONG)',1)):
            raw=modified.encode();data['library_sha256']=hashlib.sha256(raw).hexdigest()
            with self.assertRaises(ValueError):verify_liberty(raw,data)


if __name__=='__main__':unittest.main()
