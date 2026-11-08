import unittest
from soc_synth import area_inventory,constraints


def inventory():
    rows=[]
    for path,kind,count in [('u_e203_itcm_gnrl_ram','RAMSP4096X16',32),
                            ('u_e203_dtcm_gnrl_ram','RAMSP4096X16',32),
                            ('u_arch03_shared','RAMSP4096X16',64),
                            ('u_arch03_accel','RAMSP4096X16',2),
                            ('u_arch03_accel','RAMSP128X16',8)]:
        rows.extend('top/%s/%s_%d\t%s\t100\tlib/%s'%(path,kind,i,kind,kind) for i in range(count))
    rows.append('top/cpu_reg\tDFF\t2\tlib/DFF')
    rows.append('top/u_arch03_accel/control_reg\tDFF\t2\tlib/DFF')
    return rows


class SocSynthTests(unittest.TestCase):
    def test_partition_counts_area_once_and_does_not_decide_scoring(self):
        result=area_inventory('\n'.join(inventory()),13804)
        self.assertEqual(result['whole_system_library_area'],13804)
        self.assertEqual(result['groups']['accelerator']['sram_count'],10)
        self.assertEqual(result['groups']['shared']['sram_area'],6400)
        self.assertEqual(result['groups']['accelerator']['standard_cell_area'],2)
        self.assertIsNone(result['official_scoring_area'])
        self.assertFalse(result['scoring_area_verified'])

    def test_missing_duplicate_reassigned_and_invalid_areas_fail(self):
        rows=inventory()
        for bad in (rows[:-3],rows+[rows[0]],
                    [r.replace('u_arch03_shared','unclassified') for r in rows],
                    [rows[0].replace('\t100\t','\tnan\t')]+rows[1:],
                    [rows[0].replace('\t100\t','\t0\t')]+rows[1:]):
            with self.assertRaises(ValueError):area_inventory('\n'.join(bad),13804)
        with self.assertRaises(ValueError):area_inventory('\n'.join(rows),12000)

    def test_constraints_keep_cross_clock_paths_and_strict_frequency(self):
        commands='\n'.join(s for s in constraints().splitlines() if not s.lstrip().startswith('#'))
        self.assertIn('-period 6.666666666',commands)
        self.assertIn('-period 66.0',commands)
        for forbidden in ('set_false_path','set_multicycle_path','set_clock_groups'):
            self.assertNotIn(forbidden,commands)
        self.assertIn('Missing/ambiguous clock mode pin',commands)


if __name__=='__main__':unittest.main()
