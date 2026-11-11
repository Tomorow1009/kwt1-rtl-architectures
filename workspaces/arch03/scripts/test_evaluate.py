import hashlib,json,math,tempfile,unittest
from pathlib import Path
import numpy as np
from evaluate import evaluate

class EvaluationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.tasks=[]
        for sample,ref,value in [('a',1.,2),('b',10.,10)]:
            r=self.root/(sample+'_float.npz');e=self.root/(sample+'_int.npz');c=self.root/(sample+'.csv')
            np.savez(str(r),Y_float=np.full((99,256),ref,dtype=np.float32))
            np.savez(str(e),result_int=np.full((99,256),value,dtype=np.int16))
            np.savetxt(str(c),np.column_stack((np.arange(25344),np.full(25344,value))),fmt='%d',delimiter=',')
            for layer in range(1,13):
                t=dict(sample_id=sample,layer=layer,fraction_bits=0)
                for key,path in [('reference_npz',r),('integer_npz',e),('actual_csv',c)]:
                    t[key]=path.name;t[key+'_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
                self.tasks.append(t)
        self.manifest=self.root/'tasks.json'
    def tearDown(self):self.tmp.cleanup()
    def write(self,tasks=None,kind='development'):
        self.manifest.write_text(json.dumps(dict(dataset_kind=kind,provenance='Synthetic evaluator test only',
                                               tasks=self.tasks if tasks is None else tasks)))
    def test_energy_aggregation_not_average_of_ratios(self):
        self.write();r=evaluate(self.manifest)
        self.assertAlmostEqual(r['max_layer_nrmse'],1/math.sqrt(101),places=12)
        self.assertFalse(r['threshold_passed']);self.assertFalse(r['official_precision_verified'])
    def test_official_requires_600_samples(self):
        self.write(kind='official')
        with self.assertRaisesRegex(ValueError,'600'):evaluate(self.manifest)
    def test_duplicate_layer_rejected(self):
        self.write(self.tasks+[self.tasks[0]])
        with self.assertRaisesRegex(ValueError,'Duplicate'):evaluate(self.manifest)
    def test_incomplete_layers_rejected(self):
        self.write(self.tasks[:-1])
        with self.assertRaisesRegex(ValueError,'12 layers'):evaluate(self.manifest)
    def test_tampered_capture_rejected(self):
        self.write();(self.root/'a.csv').write_text('0,2\n')
        with self.assertRaisesRegex(ValueError,'hash mismatch'):evaluate(self.manifest)
    def test_duplicate_output_coordinate_rejected(self):
        p=self.root/'a.csv';lines=p.read_text().splitlines();lines[-1]=lines[0];p.write_text('\n'.join(lines)+'\n')
        for t in self.tasks:
            if t['sample_id']=='a':t['actual_csv_sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
        self.write()
        with self.assertRaisesRegex(ValueError,'capture'):evaluate(self.manifest)
    def test_nonfinite_float_rejected(self):
        p=self.root/'a_float.npz';np.savez(str(p),Y_float=np.full((99,256),np.nan))
        for t in self.tasks:
            if t['sample_id']=='a':t['reference_npz_sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
        self.write()
        with self.assertRaisesRegex(ValueError,'reference'):evaluate(self.manifest)
if __name__=='__main__':unittest.main()
