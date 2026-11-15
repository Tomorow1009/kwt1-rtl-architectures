import base64
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import p80_prepare_bundle as s

def payload(depth=4):
    names=s.REQUIRED|{d+'/manifest.json' for d in s.FIRMWARE_DIRS}
    files={}
    for name in names:
        if name.endswith('/manifest.json'):
            value=2 if name.startswith('firmware_d2/') else 8 if name.startswith('firmware_d8/') else depth
            raw=json.dumps({'configuration':{'transaction_metadata_depth':value}}).encode()
        else:raw=name.encode()
        files[name]=dict(base64=base64.b64encode(raw).decode(),sha256=hashlib.sha256(raw).hexdigest())
    return dict(schema='p80-source-firmware-overlay-v1',source_commit='a'*40,transaction_metadata_depth=depth,files=files)

class Bundle(unittest.TestCase):
    def test_selected_depth_binds_irq_sequence_and_contention_firmware(self):
        for depth in (2,4,8):
            good=payload(depth);self.assertEqual(len(s.overlay(good)),len(good['files']))
            for directory in ('firmware','firmware_sequence','firmware_contention'):
                bad=payload(depth)
                bad['files'][directory+'/manifest.json']=payload(8 if depth!=8 else 2)['files'][directory+'/manifest.json']
                with self.assertRaisesRegex(ValueError,'Firmware queue depth'):s.overlay(bad)
        for depth in (1,3,16,True):
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
                result=s.prepare(src,root/'p80',payload(2));self.assertTrue(result['source_preserved'])
                self.assertEqual(json.loads((root/'p80/manifest.json').read_text())['transaction_metadata_depth'],2)
                self.assertFalse((root/'p80/firmware/old.bin').exists())
                self.assertTrue((src/'firmware/old.bin').exists())
                for name,h in files.items():self.assertEqual(s.sha(src/name),h)
                self.assertEqual(s.sha(src/'manifest.json'),want)
                with self.assertRaises(ValueError):s.prepare(src,root/'p80',payload())

if __name__=='__main__':unittest.main()
