import copy
from pathlib import Path
import tkinter
import unittest
from unittest.mock import patch
import g32_icg_mapping as m
import g32_icg_timing as t
import g32_review_contract as contract

NAME='soc/u_arch03_accel/core/array/pe0/gate_sum/icg'

def fixture():
    lines=['schema\tg32-mapped-icg-v1','cell\t'+NAME+'\t'+m.CELL]
    for p in ('CK','E','TE','Q'):
        lines.append('\t'.join(('pin',NAME,p,NAME+'/'+p,'out' if p=='Q' else 'in')))
    lines+=['endpoint\t'+NAME+'\tsoc/u_arch03_accel/core/array/pe0/accumulator_reg[0]/CK\tregister_clock','total\t1']
    return '\n'.join(lines)

def timing():
    return '\n'.join(['schema\tg32-clock-gating-paths-v1','test_enable\t'+NAME+'\t0',
        'path\t'+NAME+'\tmax\t0.01\t'+NAME+'/E',
        'path\t'+NAME+'\tmin\t0.02\t'+NAME+'/E','count\t1'])

class G32ClockGate(unittest.TestCase):
    def test_actual_mapping_does_not_grant_power(self):
        result=m.inventory(fixture())
        self.assertEqual(result['actual_g32_cells'],1)
        self.assertEqual(result['gated_register_clock_pins'],1)
        self.assertFalse(result['energy_verified'])
        self.assertFalse(result['clock_gating_timing_verified'])

    def test_reject_nonclock_control_and_unobserved_pins(self):
        for text in (fixture().replace('register_clock','other'),
                     fixture().replace('accumulator_reg','result_valid_reg'),
                     fixture().replace('total\t1','total\t2'),
                     fixture().replace('soc/u_arch03_accel/core/array/pe0/accumulator','soc/CPU/accumulator')):
            with self.assertRaises(ValueError):m.inventory(text)

    def test_every_actual_gate_needs_both_paths_and_static_TE(self):
        actual=m.inventory(fixture());r=t.parse(timing(),actual)
        self.assertTrue(r['enable_path_setup_hold_nonnegative'])
        for text in (timing().replace('test_enable\t'+NAME+'\t0','test_enable\t'+NAME+'\t1'),
                     timing().replace('path\t'+NAME+'\tmin\t0.02\t'+NAME+'/E\n',''),
                     timing().replace('\t0.01\t','\tNaN\t'),timing().replace('/E','/D')):
            with self.assertRaises(ValueError):t.parse(text,actual)
        self.assertFalse(t.parse(timing().replace('\t0.01\t','\t-0.00001\t'),actual)['enable_path_setup_hold_nonnegative'])

    def test_queries_keep_own_clock_and_no_disabled_gating_checks(self):
        with patch.object(t,'power_databases',return_value=[Path('/new/std.db')]):
            text=t.script(Path('/new/map'),Path('/new/exact.sdc'))
        self.assertEqual(tkinter.Tcl().call('info','complete',text),1)
        self.assertEqual(tkinter.Tcl().call('info','complete',m.TCL),1)
        self.assertIn('report_clock_gating_check -nosplit',text)
        self.assertIn('get_timing_paths -to $e -delay_type $delay',text)
        for forbidden in ('set_disable_clock_gating_check','set_false_path','compile -','read_saif','read_vcd'):
            self.assertNotIn(forbidden,text)

    def test_old_repaired_mapping_cannot_become_G32(self):
        self.assertFalse(contract.route_identity(dict(scope='c32_equivalent_cell_repaired_whole_soc_task_mode',
            old_linked_ddc_reused=True,block_cache_reused=True)))
        self.assertFalse(contract.route_identity(dict(scope=contract.SCOPE,old_linked_ddc_reused=True,block_cache_reused=True)))
        self.assertTrue(contract.route_identity(dict(scope=contract.SCOPE,old_linked_ddc_reused=False,block_cache_reused=False)))

if __name__=='__main__':unittest.main()
