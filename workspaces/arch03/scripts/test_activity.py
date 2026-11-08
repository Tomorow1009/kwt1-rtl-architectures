import tempfile
import unittest
from pathlib import Path
from activity import audit_vcd,ROLES


def waveform():
    lines=['$timescale 1ps $end','$scope module tb_top $end','$scope module u_e203_soc_top $end']
    for i,instance in enumerate(ROLES.values()):
        lines+=['$scope module '+instance+' $end','$var wire 1 s%d clk $end'%i,'$upscope $end']
    lines+=['$upscope $end','$upscope $end','$enddefinitions $end','#0','$dumpoff',
            'xs0','$end','#100000','$dumpon']
    lines+=['0s%d'%i for i in range(len(ROLES))]
    lines+=['$end','#110000','1s0','xs1','#120000','$dumpoff','xs0','$end']
    return '\n'.join(lines)+'\n'


class ActivityTests(unittest.TestCase):
    def check(self,text):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'test.vcd';path.write_text(text)
            return audit_vcd(path,dict(start_ns='100',end_ns='120'))

    def test_interval_scope_and_unknowns_are_recorded(self):
        result=self.check(waveform())
        self.assertEqual(result['start_ns'],'100.000')
        self.assertEqual(result['unknown_value_records'],1)
        self.assertFalse(result['power_estimated'])
        self.assertFalse(result['mapped_netlist_annotation_verified'])

    def test_truncation_wrong_boundary_scope_and_duplicate_window_fail(self):
        text=waveform()
        for bad in (text.replace('#120000','#121000'),text[:text.rfind('#120000')],
                    text.replace('u_arch03_accel','missing_accelerator'),
                    text.replace('$scope module u_e203_soc_top','$scope module unrelated'),
                    text+'#130000\n$dumpon $end\n#140000\n$dumpoff $end\n',
                    text.replace('#110000','#90000'),text.replace('1s0','1undeclared'),
                    text.replace('$dumpon\n','$dumpon 0s0 $end\n'),text.replace('1s0','b10 s0')):
            with self.assertRaises(ValueError):self.check(bad)


if __name__=='__main__':unittest.main()
