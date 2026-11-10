"""Diagnostic settings and report guards; no synthetic PPA acceptance."""
import ast
from decimal import Decimal
from pathlib import Path
import sys
import tempfile
import tkinter
import unittest
from unittest.mock import patch
import dma16_x_sensitivity as p
import server_run
from test_dma16_power import fake_databases, window
from test_dma16_power_numbers import UNITS, BASE_UNITS, power, hierarchy, sram
from test_dma16_power_activity_review import sources, unannotated


def reports(root, point):
    settings = p.point_settings(point)
    texts={'power_settings.rpt':'\n'.join(k+' '+v for k,v in settings.items())+'\n',
           'units.rpt':BASE_UNITS, 'power.rpt':power(), 'power_verbose.rpt':UNITS+power(),
           'power_with_boundary_nets.rpt':UNITS+'-include_boundary_nets\n'+power(),
           'power_hierarchy.rpt':hierarchy(), 'power_sram.rpt':sram(),
           'activity_sources.rpt':sources(), 'activity_unannotated_before.rpt':unannotated(),
           'activity_unannotated_after.rpt':unannotated(), 'power.log':p.power.MARKER+'\n'}
    for name,text in texts.items(): (root/name).write_text(text)


class SensitivityTests(unittest.TestCase):
    def test_each_point_sets_both_choices_before_vcd_and_preserves_original_script(self):
        expected={'zero':('0','false'),'frozen':('0.5','false'),'one':('1','false'),'initial':('0.5','true')}
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);fake_databases(root)
            baseline=p.power.script({},root,root/'task.vcd',window())
            for point,(factor,initial) in expected.items():
                text=p.script({},root,root/'task.vcd',window(),point)
                added=('\n    set_app_var power_x_transition_derate_factor '+factor+'\n'
                       '    set_app_var power_include_initial_x_transitions '+initial+'\n')
                self.assertEqual(text.replace(added,''),baseline)
                self.assertLess(text.index(added),text.index('read_vcd'))
                self.assertEqual(text.count('read_vcd -zero_delay'),1)
                self.assertEqual(tkinter.Tcl().call('info','complete',text),1)
                self.assertNotIn('set_switching_activity',text)

    def test_unknown_point_and_cli_scope_are_rejected_before_execution(self):
        for point in ('','0','0.5','frozen;quit','ONE'):
            with self.assertRaises(ValueError): p.point_settings(point)
        for argv in (['dma16_power','--x-point','zero'],['dma16_x_sensitivity']):
            with patch.object(sys,'argv',['server_run.py']+argv+['--session','scope_test']):
                with patch.object(server_run,'inputs') as inputs:
                    with self.assertRaisesRegex(ValueError,'X point'): server_run.main()
                    inputs.assert_not_called()

    def test_actual_settings_units_all_macros_and_window_energy_checked(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            for point in p.POINTS:
                reports(root,point);r=p.numeric_reports(root,'200',point)
                self.assertEqual(r['actual_settings'],p.point_settings(point))
                self.assertEqual(r['sram_breakdown']['cell_count'],162)
                self.assertEqual(Decimal(r['raw_reported_energy_j']),Decimal('6.6e-10'))
                self.assertFalse(r['system_power_verified']);self.assertFalse(r['physical_error_bound'])
                self.assertFalse(r['replaces_frozen_estimate'])

    def test_actual_setting_mismatch_and_tool_error_are_not_hidden(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);reports(root,'one')
            with self.assertRaisesRegex(ValueError,'settings differ'):p.numeric_reports(root,'200','frozen')
            (root/'power.log').write_text('Error: failure\n')
            with self.assertRaisesRegex(ValueError,'tool errors'):p.numeric_reports(root,'200','one')

    def test_unannotated_source_and_changed_normal_report_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            for filename,text in [('activity_unannotated_after.rpt',unannotated(tail='bad/net\n')),
                                  ('activity_sources.rpt',sources(probability=[152985]+[0]*5+[1,0,1,0])),
                                  ('power.rpt',power().replace('3.30000000e-03','3.40000000e-03'))]:
                reports(root,'zero');(root/filename).write_text(text)
                with self.subTest(filename=filename),self.assertRaises(ValueError):p.numeric_reports(root,'200','zero')

    def test_invalid_duration_cannot_produce_energy(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);reports(root,'initial')
            for duration in ('0','-1','NaN','Infinity'):
                with self.subTest(duration=duration),self.assertRaises(ValueError):p.numeric_reports(root,duration,'initial')

    def test_python36_grammar(self):
        ast.parse(Path(p.__file__).read_text(),feature_version=(3,6))


if __name__=='__main__':unittest.main()
