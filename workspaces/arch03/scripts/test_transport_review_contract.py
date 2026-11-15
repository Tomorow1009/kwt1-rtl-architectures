import unittest
import transport_review_contract as c


class ReviewIdentity(unittest.TestCase):
    def test_partitioned_s0_cannot_borrow_monolithic_identity(self):
        request = dict(transport_stage='S0',jobs=[dict(name='S0')])
        manifest = dict(architecture='arch03_t80_s0_partition',row_lanes=5,
                        fixed_shift=10,numeric_format_id='0x000e0c20')
        self.assertEqual(c.profile(request,manifest),'S0')
        with self.assertRaises(ValueError):c.profile(request,dict(manifest,architecture='arch03_t80'))
        report = dict(schema='arch03-s0-evidence-export-v1',stage='S0',row_lanes=5,
                      numeric_format='0x000e0c20',layout_id=0x00100004,shift=10,
                      synthesis_route=dict(scope=c.S0_SCOPE))
        c.report_identity(report,'S0')
        with self.assertRaises(ValueError):c.report_identity(dict(report,synthesis_route={}), 'S0')
        synthesis = dict(scope=c.S0_SCOPE,synthesis_completed=True,project_limit_mm2=1.0,
                         link_report=dict(scope='s0_three_ddc_link',row_lanes=5))
        c.synthesis_identity(synthesis,'S0')
        for change in (dict(scope='t80_whole_soc_task_mode_preliminary_synthesis'),
                       dict(project_limit_mm2=1.2),dict(link_report={})):
            with self.assertRaises(ValueError):c.synthesis_identity(dict(synthesis,**change),'S0')

    def test_only_matching_transport_bundle_and_own_job(self):
        for stage, rows in (('T80',5),('T64',4)):
            request = dict(transport_stage=stage,jobs=[dict(name=stage)])
            manifest = dict(architecture='arch03_'+stage.lower(), row_lanes=rows,
                            fixed_shift=10,numeric_format_id='0x000e0c20')
            self.assertEqual(c.profile(request,manifest),stage)
            for key,value in (('row_lanes',9-rows),('fixed_shift',16),('architecture','arch03_n1')):
                changed = dict(manifest);changed[key]=value
                with self.assertRaises(ValueError):c.profile(request,changed)
            for jobs in ([],[dict(name='N1')],[dict(name=stage),dict(name='B0')]):
                with self.assertRaises(ValueError):c.profile(dict(request,jobs=jobs),manifest)

    def test_report_and_synthesis_from_predecessor_rejected(self):
        for stage,rows in (('T80',5),('T64',4)):
            report=dict(schema='arch03-'+stage.lower()+'-evidence-export-v1',stage=stage,
                        row_lanes=rows,numeric_format='0x000e0c20',layout_id=0x00100004,shift=10)
            c.report_identity(report,stage)
            c.synthesis_identity(dict(scope=stage.lower()+'_whole_soc_task_mode_preliminary_synthesis',
                                      synthesis_completed=True),stage)
            with self.assertRaises(ValueError):c.report_identity(dict(report,stage='N1'),stage)
            with self.assertRaises(ValueError):c.synthesis_identity(dict(scope='n1_whole_soc_task_mode_preliminary_synthesis',
                                                                        synthesis_completed=True),stage)


if __name__ == '__main__':unittest.main()
