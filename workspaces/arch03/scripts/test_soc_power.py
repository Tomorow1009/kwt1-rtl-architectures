import tempfile
import unittest
from pathlib import Path
from soc_power import window_values,script,tcl_path


class PowerTests(unittest.TestCase):
    def test_window_is_ns_and_preserves_full_task_duration(self):
        window=dict(start_ns='18043.331529',end_ns='25951907.404809',period_ns='6.666666',cycles=3890080)
        self.assertEqual(window_values(window),('18043.331529','25951907.404809','25933864.073280'))
        for key,value in [('end_ns','18043.331529'),('end_ns','25951900'),('start_ns','NaN'),('cycles',0)]:
            bad=dict(window);bad[key]=value
            with self.assertRaises(ValueError):window_values(bad)

    def test_script_keeps_unannotated_objects_and_explicit_review_status(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'libs').mkdir()
            for name in ('standard','large','small'):(root/'libs'/(name+'.db')).touch()
            text=script({},root,root/'activity.vcd',dict(start_ns='10',end_ns='30',period_ns='5',cycles=4))
        self.assertIn('-time {10 30}',text)
        self.assertIn('-strip_path tb_top/u_e203_soc_top',text)
        self.assertIn('report_switching_activity -list_not_annotated -show_pin',text)
        self.assertIn('power_sram.rpt',text)
        self.assertIn('system_power_verified=false',text)
        self.assertIn('exit 1',text)
        self.assertNotIn('set_switching_activity',text)
        for bad in ('path}name','path\nname'):
            with self.assertRaises(ValueError):tcl_path(bad)


if __name__=='__main__':unittest.main()
