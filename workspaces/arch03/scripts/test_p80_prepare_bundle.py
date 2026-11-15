import base64
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import p80_prepare_bundle as s

def payload():
    names=s.REQUIRED|{d+'/manifest.json' for d in s.FIRMWARE_DIRS}
    files={}
    for name in names:
        raw=name.encode();files[name]=dict(base64=base64.b64encode(raw).decode(),sha256=hashlib.sha256(raw).hexdigest())
    return dict(schema='p80-source-firmware-overlay-v1',source_commit='a'*40,transaction_metadata_depth=4,files=files)

class Bundle(unittest.TestCase):
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
                result=s.prepare(src,root/'p80',payload());self.assertTrue(result['source_preserved'])
                self.assertFalse((root/'p80/firmware/old.bin').exists())
                self.assertTrue((src/'firmware/old.bin').exists())
                for name,h in files.items():self.assertEqual(s.sha(src/name),h)
                self.assertEqual(s.sha(src/'manifest.json'),want)
                with self.assertRaises(ValueError):s.prepare(src,root/'p80',payload())

if __name__=='__main__':unittest.main()
