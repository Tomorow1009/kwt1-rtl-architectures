"""Tool-only fixtures; never call execute/build_runtime or import TensorFlow."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

import numpy as np

import n1_float_single_probe as probe


class SingleFloatProbeTest(unittest.TestCase):
    def proof(self):
        return dict(schema='n1-wav-source-join-receipt-v1', passed=True, checked=100,
            mismatches=0, inputs_stable=True, wav_hashlist_sha256=probe.WAV_LIST_SHA,
            server_manifest_sha256=probe.SERVER_MANIFEST_SHA,
            sample_001_float_npz_sha256='3'*64, observed_server_time='fixture', evidence_sha256='4'*64)

    def arrays(self):
        return {name:np.zeros(shape,dtype=np.float32) for name,shape in probe.SHAPES}

    def test_import_does_not_import_tensorflow(self):
        self.assertNotIn('tensorflow',sys.modules)

    def test_source_proof_positive(self):
        probe.proof_identity(self.proof(),'3'*64)

    def test_source_proof_unpassed(self):
        proof=self.proof(); proof['passed']=False
        with self.assertRaisesRegex(ValueError,'not passed'):
            probe.proof_identity(proof,'3'*64)

    def test_source_proof_changed_input(self):
        proof=self.proof(); proof['server_manifest_sha256']='5'*64
        with self.assertRaisesRegex(ValueError,'input identity'):
            probe.proof_identity(proof,'3'*64)

    def test_source_proof_missing_original_hash(self):
        with self.assertRaisesRegex(ValueError,'Original sample NPZ SHA'):
            probe.proof_identity(self.proof(),None)

    def test_source_proof_different_original_hash(self):
        with self.assertRaisesRegex(ValueError,'identity disagreement'):
            probe.proof_identity(self.proof(),'5'*64)

    def test_synthetic_serialization_and_preserve_existing(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'candidate.npz'
            meta=probe.write_candidate(path,self.arrays())
            self.assertEqual([v['name'] for v in meta['members']],['X.npy','Y.npy','logits.npy'])
            self.assertEqual(meta['arrays']['logits']['shape'],[1,12])
            before=path.read_bytes()
            with self.assertRaisesRegex(ValueError,'already exists'):
                probe.write_candidate(path,self.arrays())
            self.assertEqual(before,path.read_bytes())

    def test_reject_float64_before_write(self):
        arrays=self.arrays(); arrays['X']=arrays['X'].astype(np.float64)
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'candidate.npz'
            with self.assertRaisesRegex(ValueError,'float32 shape'):
                probe.write_candidate(path,arrays)
            self.assertFalse(path.exists())

    def test_reject_flat_logits_before_write(self):
        arrays=self.arrays(); arrays['logits']=arrays['logits'][0]
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'candidate.npz'
            with self.assertRaisesRegex(ValueError,'float32 shape'):
                probe.write_candidate(path,arrays)
            self.assertFalse(path.exists())


if __name__ == '__main__':
    unittest.main()
