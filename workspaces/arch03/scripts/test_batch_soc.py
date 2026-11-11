"""Fail-closed dataset and resume checks; no EDA tools or server required."""
import hashlib,json,tempfile,unittest
from pathlib import Path
import batch_soc as batch

def write(path,value):path.write_text(json.dumps(value))

class BatchGuards(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.root=Path(cls.temp.name)
        cls.meta=dict(schema='kwt1-full-arch02-q12-v1',numeric_format={
            'input':'signed16 Q12','weight':'signed16 Q12','bias':'signed40 Q24','result':'signed16 Q12'},samples=[])
        for sample in range(1,101):
            entry=dict(sample=sample,wav='test/%d.wav'%sample,layers=[])
            for layer in range(1,13):
                folder=cls.root/('sample_%06d/layer_%02d'%(sample,layer));folder.mkdir(parents=True)
                hashes={}
                for name in batch.FILES:
                    (folder/name).write_bytes(b'00\n');hashes[name]=batch.sha(folder/name)
                layout=dict(schema='arch02-hex-v1',load_words=23488,outputs=25344,layer_number=layer,shift=12,sha256=hashes)
                write(folder/'layout.json',layout)
                entry['layers'].append(dict(layer_number=layer,outputs=25344,shift=12,
                                           sha256=hashes,layout_sha256=batch.sha(folder/'layout.json')))
            cls.meta['samples'].append(entry)

    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()

    def check(self,meta):
        write(self.root/'manifest.json',meta)
        return batch.dataset(self.root,batch.sha(self.root/'manifest.json'))

    def copy_meta(self):return json.loads(json.dumps(self.meta))

    def test_complete_manifest(self):
        tasks,files=self.check(self.meta)
        self.assertEqual((len(tasks),len(files)),(1200,7201))

    def test_duplicate_sample(self):
        m=self.copy_meta();m['samples'][-1]['sample']=1
        with self.assertRaisesRegex(ValueError,'unique samples'):self.check(m)

    def test_missing_layer(self):
        m=self.copy_meta();m['samples'][0]['layers'].pop()
        with self.assertRaisesRegex(ValueError,'unique layers'):self.check(m)

    def test_changed_quantization(self):
        m=self.copy_meta();m['numeric_format']['result']='signed16 Q10'
        with self.assertRaisesRegex(ValueError,'numeric format'):self.check(m)

    def test_changed_data(self):
        path=self.root/'sample_000001/layer_01/load.hex';raw=path.read_bytes()
        try:
            path.write_bytes(b'01\n')
            with self.assertRaisesRegex(ValueError,'Data file changed'):self.check(self.meta)
        finally:path.write_bytes(raw)

    def test_resume_requires_unchanged_capture(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);task=root/'task';run=root/'case';task.mkdir();run.mkdir()
            (task/'load.hex').write_bytes(b'01\n')
            values=[(i%101)-50 for i in range(25344)];sats=[0]*25344
            (run/'capture.csv').write_text(''.join('%d,%d\n'%(i,v) for i,v in enumerate(values)))
            (run/'cpu.log').write_text('ARCH03_SOC_PASS outputs=25344 cpu_executed=true cycles=123 saturated=0\n')
            (run/'firmware.verilog').write_bytes(b'01\r\n')
            record=dict(status='passed',outputs=25344,cpu_executed=True,cycles=123,saturated=0,
                        input_sha256=batch.sha(task/'load.hex'),artifacts={
                            name:batch.sha(run/name) for name in ('capture.csv','cpu.log','firmware.verilog')})
            write(run/'summary.json',record)
            batch.verified_case(run,task,(None,values,sats))
            with (run/'capture.csv').open('a') as f:f.write('0,-50\n')
            with self.assertRaisesRegex(ValueError,'artifact changed'):batch.verified_case(run,task,(None,values,sats))

if __name__=='__main__':unittest.main()
