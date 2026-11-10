"""Area/mode contract checks only; these are not synthesized hardware results."""
import json
import tempfile
import unittest
from pathlib import Path
import icb32_synth as new
from test_dma16_synth import constraint_interpreter,write_library_receipts,top


def inventory():
    sizes=json.loads(new.METADATA.read_text())['cells'];rows=[]
    # Independent architectural count: 64 TCM + 64 shared large, 64 X + 32 W small.
    for root,ref,n in [('u_e203_itcm_gnrl_ram','RAMSP4096X16',32),
        ('u_e203_dtcm_gnrl_ram','RAMSP4096X16',32),('u_arch03_shared','RAMSP4096X16',64),
        ('u_arch03_accel','RAMSP128X16',96)]:
        rows+=['top/%s/m%d\t%s\t%.8f\tlib/%s'%(root,i,ref,sizes[ref]['area'],ref) for i in range(n)]
    for root in ['u_arch03_accel','u_arch03_arb','u_arch03_router','u_arch03_shared','cpu']:
        rows.append('top/%s/cell\tDFF\t10\tlib/DFF'%root)
    return rows


class Icb32SynthesisTests(unittest.TestCase):
    def test_correct_banks_and_conservative_glue(self):
        rows=inventory();r=new.area_inventory('\n'.join(rows),sum(float(v.split('\t')[2]) for v in rows))
        self.assertEqual(r['macro_count'],224)
        self.assertEqual(r['groups']['accelerator']['sram_count'],96)
        self.assertEqual(r['physical_sram_bytes'],1048*1024)
        self.assertEqual(r['conservative_budget_library_area']-r['known_added_library_area'],10)
        self.assertFalse(r['scoring_area_verified'])
        for invalid in (rows[1:],rows+[rows[0]],[v.replace('/u_arch03_arb/','/fixed/') for v in rows]):
            with self.assertRaises(ValueError):new.area_inventory('\n'.join(invalid),r['whole_system_library_area'])

    def test_original_io_budgets_and_templates(self):
        interpreter,_,_=constraint_interpreter();interpreter.eval(new.constraints())
        new.verify_top_sysmem(top(True));new.verify_top_sysmem(top(False))
        with tempfile.TemporaryDirectory() as folder:
            libs=Path(folder)/'libs';libs.mkdir()
            for name in ('standard.db','m128.db','m4096.db'):(libs/name).write_text('fixture only')
            script=new.script(Path(folder),{'standard_library_member':'standard.db'})
            self.assertIn('!= 224',script)
            self.assertIn('!= 96',script);self.assertIn('!= 128',script)
            self.assertNotIn('!= 162',script)
            write_library_receipts(Path(folder));self.assertEqual(new.area_basis(Path(folder))['units'],'um^2')

    def test_old_or_loop_broken_result_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            run=Path(folder);(run/'linked.ddc').write_text('old')
            with self.assertRaisesRegex(ValueError,'fresh run'):
                new.synth({},run,Path('unused'),lambda *args:self.fail('must reject before tools'))
        with self.assertRaises(ValueError):new.require_loop_free_timing('Checking loops TIM-209 timing loops detected')
        self.assertFalse(new.require_loop_free_timing('Checking loops')['strict_timing_verified'])


if __name__=='__main__':unittest.main()
