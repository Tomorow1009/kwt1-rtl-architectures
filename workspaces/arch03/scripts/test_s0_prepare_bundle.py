import base64
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import s0_prepare_bundle as s


def payload():
    files={}
    for name in s.ALLOWED:
        raw=('fixture '+name).encode('ascii')
        files[name]=dict(base64=base64.b64encode(raw).decode('ascii'),sha256=hashlib.sha256(raw).hexdigest())
    return dict(schema='s0-tools-overlay-v1',operations_source_commit='a'*40,files=files)


class S0PrepareTests(unittest.TestCase):
    def test_overlay_rejects_extra_paths_and_tampered_bytes(self):
        p=payload();self.assertEqual(set(s.overlay(p)),s.ALLOWED)
        p['files']['../old8/delete']=next(iter(p['files'].values()))
        with self.assertRaises(ValueError):s.overlay(p)
        p=payload();next(iter(p['files'].values()))['base64']='Yg=='
        with self.assertRaises(ValueError):s.overlay(p)

    def test_clone_preserves_source_and_never_overwrites_destination(self):
        with tempfile.TemporaryDirectory() as d:
            src=Path(d)/'source';src.mkdir();files={}
            old='workspaces/arch03/scripts/n1_process.py'
            names=[old]+['inputs/%04d.txt'%i for i in range(832)]
            for n in names:
                path=src/n;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(n.encode())
                files[n]=s.sha(path)
            (src/'manifest.json').write_text(json.dumps(dict(files=files,source_commit='b'*40)))
            want=s.sha(src/'manifest.json');target=Path(d)/'new'
            with patch.object(s,'BASE_SHA',want):
                report=s.prepare(src,target,payload())
                self.assertTrue(report['source_preserved'])
                self.assertEqual(s.sha(src/old),files[old])
                self.assertNotEqual(s.sha(src/old),s.sha(target/old))
                self.assertNotEqual((src/'inputs/0001.txt').stat().st_ino,(target/'inputs/0001.txt').stat().st_ino)
                with self.assertRaises(ValueError):s.prepare(src,target,payload())
                self.assertFalse((target/'runs').exists())


if __name__=='__main__':unittest.main()
