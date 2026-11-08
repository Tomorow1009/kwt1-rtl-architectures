"""Focused non-destructive failure checks using temporary copies only."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile
import local
from unpack import unpack

class PortabilityTests(unittest.TestCase):
    def test_missing_tool(self):
        with self.assertRaises(FileNotFoundError):local.executable('iverilog','__absent_bin__')

    def test_bad_data_path(self):
        with self.assertRaises(FileNotFoundError):local.verify_data({'data_root':'__absent_data__'})

    def test_unknown_config(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'config.json';p.write_text('{"password":"not-a-real-secret"}')
            with self.assertRaises(ValueError):local.config(p)

    def test_bundle_hash_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);z=p/'bundle.zip';payload=b'example'
            m={'files':{'input.hex':hashlib.sha256(payload).hexdigest()}}
            with zipfile.ZipFile(str(z),'w') as out:
                out.writestr('bundle/input.hex',payload);out.writestr('bundle/manifest.json',json.dumps(m))
            with self.assertRaises(ValueError):unpack(z,p/'out','0'*64)
            digest=hashlib.sha256(z.read_bytes()).hexdigest()
            result=unpack(z,p/'out',digest)
            self.assertEqual((result/'input.hex').read_bytes(),payload)
            with self.assertRaises(ValueError):unpack(z,p/'out',digest)

    def test_path_traversal(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);z=p/'bad.zip'
            with zipfile.ZipFile(str(z),'w') as out:out.writestr('../escape','bad')
            with self.assertRaises(ValueError):unpack(z,p/'out',hashlib.sha256(z.read_bytes()).hexdigest())
            self.assertFalse((p/'out').exists())

    def test_modified_bundle_input(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);z=p/'bad.zip'
            with zipfile.ZipFile(str(z),'w') as out:
                out.writestr('bundle/input','changed');out.writestr('bundle/manifest.json',json.dumps({'files':{'input':'0'*64}}))
            with self.assertRaises(ValueError):unpack(z,p/'out',hashlib.sha256(z.read_bytes()).hexdigest())
            self.assertFalse((p/'out').exists())

    def test_recorded_stage_not_restarted(self):
        import server
        with self.assertRaises(ValueError):server.run_stage('preflight',Path('.'),{'stages':{'preflight':{'status':'running'}}},{})

    def test_missing_prior_stage(self):
        import server
        with self.assertRaises(ValueError):server.run_stage('hold',Path('.'),{'stages':{}},{})

if __name__=='__main__':unittest.main(verbosity=2)
