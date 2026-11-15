import copy,json,tempfile,unittest
from pathlib import Path
import partition_synth_contract as c

class PartitionTests(unittest.TestCase):
    def args(self):
        return dict(partition='accelerator',sources={'rtl':'1'*64},
            parameters=dict(period_ns=c.PERIOD,corner=c.CORNER,row_lanes=5),
            libraries={'ss':'2'*64},constraints={'boundary':'3'*64},
            tool=dict(version='Q-2020.03-SP2',executable_sha256='4'*64),dependencies={'boundary_ddc':'5'*64})

    def test_cache_invalidates_each_real_dependency(self):
        a=self.args();old=c.fingerprint(**a)
        for group,key,value in [('sources','rtl','6'*64),('libraries','ss','6'*64),
                ('constraints','boundary','6'*64),('tool','version','Q-2020.03-SP3'),
                ('dependencies','boundary_ddc','6'*64),('parameters','row_lanes',2)]:
            changed=copy.deepcopy(a);changed[group][key]=value
            self.assertNotEqual(c.fingerprint(**changed),old)
        b=copy.deepcopy(a);b['parameters']['period_ns']='6.667'
        with self.assertRaises(ValueError):c.fingerprint(**b)
        a['parameters']['row_lanes']=2
        self.assertEqual(old['identity']['parameters']['row_lanes'],5)

    def test_cached_artifact_corruption_and_incomplete_stage_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);artifacts={}
            for name in ('mapped.ddc','mapped.v','constraints.tcl','tool_version.txt'):
                (root/name).write_bytes(name.encode());artifacts[name]=c.digest(root/name)
            expected=c.fingerprint(**self.args());row=dict(schema=c.SCHEMA,status='mapped',fingerprint=expected,artifacts=artifacts)
            self.assertTrue(c.reusable(row,expected,root))
            corrupt=copy.deepcopy(expected);corrupt['identity']['parameters']['row_lanes']=2
            with self.assertRaises(ValueError):c.reusable(row,corrupt,root)
            row['status']='running'
            with self.assertRaises(ValueError):c.reusable(row,expected,root)
            row['status']='mapped';(root/'mapped.ddc').write_bytes(b'changed')
            with self.assertRaises(ValueError):c.reusable(row,expected,root)

    def inventory(self):
        rows=[]
        for name,owner,kind,area in [('cpu/core','platform_other','standard_cell',30),
            ('cpu/u_arch03_arb/g','dma_arbiter','standard_cell',10),
            ('cpu/irq_glue','platform_other','standard_cell',5),
            ('cpu/u_arch03_accel/mac','accelerator','standard_cell',20),
            ('cpu/u_arch03_accel/ram','accelerator','sram',40),
            ('cpu/u_arch03_shared/ctl','shared','standard_cell',7),
            ('cpu/u_arch03_shared/ram','shared','sram',100),
            ('cpu/itcm/ram','itcm','sram',100)]:
            rows.append(dict(instance=name,owner=owner,kind=kind,area=area,reference='fixture'))
        return dict(rows=rows,whole_system_library_area=312,conservative_budget_library_area=112)

    def test_cpu_partition_does_not_exempt_team_arbiter_or_unknown_glue(self):
        a=c.area_attribution(self.inventory(),{'cpu/core':'a'*64})
        self.assertEqual(a['project_charged_mm2'],82/1e6)
        self.assertEqual(a['decision_area_mm2'],112/1e6)
        self.assertIsNone(a['audited_project_mm2'])
        arb=next(r for r in a['rows'] if r['original_owner']=='dma_arbiter')
        self.assertEqual((arb['physical_partition'],arb['decision']),('cpu_soc','project_added'))
        self.assertEqual(sum(x['area_um2'] for x in a['physical_partitions'].values()),312)

    def test_new_logic_cannot_be_exempted_and_duplicate_leaves_rejected(self):
        with self.assertRaises(ValueError):c.area_attribution(self.inventory(),{'cpu/u_arch03_arb/g':'a'*64})
        v=self.inventory();v['rows'].append(v['rows'][0])
        with self.assertRaises(ValueError):c.area_attribution(v)

    def test_characterization_uses_single_top_clock_and_real_boundary_context(self):
        text=c.characterize_script('/run/frozen.ddc','/run/task_mode.sdc','/run/libs.tcl')
        self.assertIn('characterize -constraint $target',text)
        self.assertIn('6.666666',text)
        self.assertNotIn('create_clock',text)
        self.assertNotIn('set_false_path',text)
        self.assertNotIn('compile',text)
        with self.assertRaises(ValueError):c.characterize_script('/run/evil}.ddc','/run/sdc','/run/libs.tcl')

if __name__=='__main__':unittest.main()
