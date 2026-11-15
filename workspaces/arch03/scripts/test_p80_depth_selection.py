import copy
import unittest
from p80_depth_selection import choose,LAYERS


def candidate(depth,cycles):
    rows=[dict(case=n,cycles=cycles,encoded_bytes=29756,codec_sha256='codec-'+n,
        layout_sha256='layout-'+n,capture_sha256='capture-'+n) for n in LAYERS]
    return dict(depth=depth,cycles_sum=cycles*12,cases=rows,hardware={'/bundle%d/rtl'%depth:'same'})


class P80DepthSelectionTests(unittest.TestCase):
    def test_throughput_one_percent_threshold_is_not_cycle_rounding(self):
        rows=[candidate(2,10000),candidate(4,9950),candidate(8,9900)]
        self.assertEqual(choose(rows,[2,4,8])['selected_depth'],2)
        rows[0]=candidate(2,10001)
        self.assertEqual(choose(rows,[2,4,8])['selected_depth'],4)
        self.assertEqual(choose(rows,[8])['selected_depth'],8)

    def test_rejects_incomplete_comparison_changed_inputs_and_no_area_candidate(self):
        rows=[candidate(2,10000),candidate(4,9950),candidate(8,9900)]
        for bad in (rows[:2],rows+[rows[0]]):
            with self.assertRaises(ValueError):choose(bad,[2,4,8])
        for key in ('codec_sha256','capture_sha256','encoded_bytes'):
            bad=copy.deepcopy(rows);bad[1]['cases'][0][key]='different'
            with self.assertRaises(ValueError):choose(bad,[2,4,8])
        with self.assertRaises(ValueError):choose(rows,[])


if __name__=='__main__':unittest.main()
