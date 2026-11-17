import base64
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import g32_prepare_bundle as s

def payload(depth=2):
    names=s.REQUIRED|{d+'/manifest.json' for d in s.FIRMWARE_DIRS}
    files={}
    for name in names:
        if name.endswith('/manifest.json'):
            value=2 if name.startswith('firmware_d2/') else 8 if name.startswith('firmware_d8/') else depth
            raw=json.dumps({'configuration':{'transaction_metadata_depth':value,'row_lanes':2},'peripheral_id':'0x4b57530f','numeric_format':'0x000e0c20'}).encode()
        else:raw=name.encode()
        files[name]=dict(base64=base64.b64encode(raw).decode(),sha256=hashlib.sha256(raw).hexdigest())
    return dict(schema='g32-source-firmware-overlay-v1',source_commit='a'*40,transaction_metadata_depth=depth,files=files)

class Bundle(unittest.TestCase):
    def test_selected_depth_binds_irq_sequence_and_contention_firmware(self):
        for depth in (2,):
            good=payload(depth);self.assertEqual(len(s.overlay(good)),len(good['files']))
            for directory in ('firmware','firmware_sequence','firmware_contention'):
                bad=payload(depth)
                bad['files'][directory+'/manifest.json']=payload(8 if depth!=8 else 2)['files'][directory+'/manifest.json']
                with self.assertRaisesRegex(ValueError,'Firmware identity/rows/depth'):s.overlay(bad)
        for depth in (1,3,4,8,16,True):
            with self.assertRaises(ValueError):s.overlay(payload(depth))
    def test_explicit_scope_and_bytes(self):
        d=payload();self.assertEqual(len(s.overlay(d)),len(d['files']))
        for path in ('../old8/a','workspaces/arch03/rtl/arch03_n1_decoder.sv','runs/old/log','firmware/secret.txt'):
            q=payload();q['files'][path]=next(iter(q['files'].values()))
            with self.assertRaises(ValueError):s.overlay(q)
        q=payload();next(iter(q['files'].values()))['base64']='Yg=='
        with self.assertRaises(ValueError):s.overlay(q)

    def test_copy_does_not_change_old_source_or_reuse_firmware(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);src=root/'s0';src.mkdir();files={}
            for name in ('data/input.hex','firmware/old.bin','workspaces/arch03/rtl/arch03_n1_decoder.sv'):
                p=src/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(name.encode());files[name]=s.sha(p)
            (src/'manifest.json').write_text(json.dumps(dict(source_commit='b'*40,files=files)))
            want=s.sha(src/'manifest.json')
            with patch.object(s,'BASE_SHA',want),patch.object(s,'BASE_COUNT',3):
                result=s.prepare(src,root/'g32',payload(2));self.assertTrue(result['source_preserved'])
                made=json.loads((root/'g32/manifest.json').read_text())
                self.assertEqual(made['transaction_metadata_depth'],2)
                self.assertEqual(made['production_hardware_commit'],'a'*40)
                self.assertEqual(made['runtime_layout'],'arch03-g32-lossless-layout6')
                self.assertFalse(made['cpu_execution_verified'])
                for role in ('sequence','contention'):
                    self.assertEqual(made['diagnostic_firmware'][role],s.sha(root/'g32'/('firmware_'+role)/'manifest.json'))
                self.assertFalse((root/'g32/firmware/old.bin').exists())
                self.assertTrue((src/'firmware/old.bin').exists())
                for name,h in files.items():self.assertEqual(s.sha(src/name),h)
                self.assertEqual(s.sha(src/'manifest.json'),want)
                with self.assertRaises(ValueError):s.prepare(src,root/'g32',payload())

if __name__=='__main__':unittest.main()
