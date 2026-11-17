"""Report joins use task identity and combined energy, not mean percentages."""
import copy
import math
import unittest
from g32_full100_report import build_rows


class ReportJoin(unittest.TestCase):
    def setUp(self):
        self.batch={'cases':[]};self.numeric={'cases':[]}
        for sample in range(1,101):
            for layer in range(1,13):
                key='sample_%03d_layer_%02d'%(sample,layer)
                energy=1.0 if sample<=50 else 100.0
                sse=.0001
                self.batch['cases'].append(dict(key=key,outputs=25344,total_outputs=25344,
                    cycles=60000+sample,encoded_bytes=24000,host_seconds=10,
                    capture_sha256='a'*64,receipt_sha256='b'*64))
                self.numeric['cases'].append(dict(sample=sample,layer=layer,outputs=25344,
                    nrmse_percent=100*math.sqrt(sse/energy),sse=sse,reference_energy=energy,
                    saturated=0,clipping=dict(x=0,w=0,b=0)))

    def test_weighted_error_and_cycle_scope(self):
        cases,layers=build_rows(self.batch,self.numeric)
        self.assertEqual(len(cases),1200)
        self.assertEqual(len(layers),12)
        for row in layers:
            self.assertEqual(row['tasks'],100)
            self.assertEqual(row['mean_complete_cycles'],60050.5)
            self.assertAlmostEqual(row['nrmse_percent'],100*math.sqrt(.01/5050.0))
            self.assertNotAlmostEqual(row['nrmse_percent'],.55)

    def test_reordered_case_rejected(self):
        self.batch['cases'][-2:]=self.batch['cases'][-2:][::-1]
        with self.assertRaises(ValueError):build_rows(self.batch,self.numeric)

    def test_truncated_total_proof_rejected(self):
        self.batch['cases'][-1]['total_outputs']=25343
        with self.assertRaises(ValueError):build_rows(self.batch,self.numeric)


if __name__=='__main__':unittest.main()
