import os,tempfile,unittest
from pathlib import Path
from activity import audit_vcd
from activity_fast import audit_vcd_fast
from test_activity import waveform


@unittest.skipUnless(os.environ.get('ARCH03_ACTIVITY_SCANNER'),'Explicit compiled scanner path required')
class NativeActivityTests(unittest.TestCase):
    def compare(self,text,valid=True):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'test.vcd';path.write_text(text,encoding='ascii')
            window=dict(start_ns='100',end_ns='120')
            if valid:
                self.assertEqual(audit_vcd(path,window),audit_vcd_fast(path,window,os.environ['ARCH03_ACTIVITY_SCANNER']))
            else:
                with self.assertRaises((ValueError,IndexError)):audit_vcd(path,window)
                with self.assertRaises(ValueError):audit_vcd_fast(path,window,os.environ['ARCH03_ACTIVITY_SCANNER'])

    def test_exact_native_reference_parity_including_aliases_unknowns_and_many_records(self):
        base=waveform();self.compare(base)
        self.compare(base.replace('$var wire 1 s0 clk $end','$var wire 1 s0 clk $end\n$var wire 1 s0 alias $end'))
        self.compare(base.replace('$var wire 1 s0 clk $end','$var wire 128 s0 data $end').replace('1s0','b'+('1'*128)+' s0'))
        self.compare(base.replace('1s0','rNaN s0'))
        self.compare(base.replace('1s0','r1.25 s0'))
        self.compare(base.replace('1s0','\n'.join(('1s0','0s0','xs0','zs0')*25000)))

    def test_native_rejects_same_structural_and_interval_errors(self):
        text=waveform()
        for bad in (text.replace('#120000','#121000'),text[:text.rfind('#120000')],
                    text.replace('u_arch03_accel','missing_accelerator'),
                    text.replace('$scope module u_e203_soc_top','$scope module unrelated'),
                    text+'#130000\n$dumpon $end\n#140000\n$dumpoff $end\n',
                    text.replace('#110000','#90000'),text.replace('1s0','1undeclared'),
                    text.replace('$dumpon\n','$dumpon 0s0 $end\n'),text.replace('1s0','b10 s0'),
                    text.replace('1s0','b2 s0'),text.replace('$timescale 1ps $end','$timescale 2ps $end'),
                    text.replace('1s0','rINVALID s0'),text.replace('$dumpon\n','$dumpon\n$dumpon\n'),
                    text.replace('$var wire 1 s0 clk $end','$var wire 1 s0 clk $end\n$var wire 2 s0 alias $end')):
            self.compare(bad,False)


if __name__=='__main__':unittest.main()
