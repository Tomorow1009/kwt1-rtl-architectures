"""Exercise actual original-member/source guards and fresh numerical audit."""
import contextlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import zipfile

import n1_data as data
import n1_precision as old
import n1_recovered_precision as recovered
from test_n1_precision import PrecisionTests


class RecoveredPrecisionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        PrecisionTests.setUpClass()
        cls.base=PrecisionTests
        cls.archive=cls.base.root/'recovered.zip'
        with zipfile.ZipFile(str(cls.archive),'w') as zipped:
            zipped.writestr(recovered.ROOT+'shared_weights.npz',cls.base.weight_raw)
            zipped.writestr(recovered.ROOT+'sample_001/float_tensors.npz',cls.base.sample_raw)
        cls.digest=data.sha(cls.archive)

    @classmethod
    def tearDownClass(cls):
        PrecisionTests.tearDownClass()

    def patches(self):
        stack=contextlib.ExitStack()
        stack.enter_context(mock.patch.object(recovered,'MANIFEST_SHA',self.base.manifest_sha))
        stack.enter_context(mock.patch.object(recovered,'WEIGHTS_SHA',old.digest_bytes(self.base.weight_raw)))
        stack.enter_context(mock.patch.object(recovered,'ORIGINAL_ARCHIVE_SHA',self.base.archive_sha))
        stack.enter_context(mock.patch.object(data,'DATA100_INVENTORY_SHA',self.base.inventory_sha))
        return stack

    def test_fresh_fixture_pass_does_not_approve_production(self):
        with self.patches():
            result=recovered._audit(self.archive,self.digest,self.base.dataset,self.base.root/'recovered_audit',1)
        self.assertEqual(result['status'],'fixture_passed')
        self.assertTrue(result['recovered_original_members_verified'])
        self.assertFalse(result['original_float_archive_verified'])
        self.assertFalse(result['internal_precision_verified'])
        self.assertFalse(result['cpu_executed'])
        self.assertEqual(result['outputs'],304128)
        self.assertEqual(result['integer_mismatches'],0)

    def test_changed_member_cannot_pass_with_new_container_digest(self):
        path=self.base.root/'changed_recovered.zip'
        with zipfile.ZipFile(str(path),'w') as zipped:
            zipped.writestr(recovered.ROOT+'shared_weights.npz',self.base.weight_raw)
            zipped.writestr(recovered.ROOT+'sample_001/float_tensors.npz',self.base.sample_raw+b'changed')
        with self.patches():
            manifest=recovered.verified_manifest(self.base.dataset,1)
            with self.assertRaisesRegex(ValueError,'Original float NPZ differs'):
                recovered.verify_members(path,data.sha(path),manifest)

    def test_missing_and_extra_members_rejected(self):
        for extra in (False,True):
            path=self.base.root/('wrong_set_%d.zip'%extra)
            with zipfile.ZipFile(str(path),'w') as zipped:
                zipped.writestr(recovered.ROOT+'shared_weights.npz',self.base.weight_raw)
                if extra:
                    zipped.writestr(recovered.ROOT+'sample_001/float_tensors.npz',self.base.sample_raw)
                    zipped.writestr('unexpected.json','{}')
            with self.patches():
                manifest=recovered.verified_manifest(self.base.dataset,1)
                with self.assertRaisesRegex(ValueError,'member set'):
                    recovered.verify_members(path,data.sha(path),manifest)

    def test_original_zip_entry_remains_strict(self):
        with self.assertRaisesRegex(ValueError,'archive SHA'):
            old._audit(self.archive,self.base.dataset,self.base.root/'cannot_use_as_original',self.base.manifest_sha,1)


if __name__=='__main__':
    unittest.main()
