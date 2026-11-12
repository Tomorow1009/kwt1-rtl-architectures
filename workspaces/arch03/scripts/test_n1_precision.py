"""Synthetic one-sample precision fixtures, never a production100 PASS."""
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import zipfile

import numpy as np
import n1_data as data
import n1_precision as precision


def npz_bytes(**values):
    stream = io.BytesIO()
    np.savez(stream, **values)
    return stream.getvalue()


class PrecisionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(dir=str(data.ROOT/'local_runs'), prefix='n1_precision_fixture_')
        cls.root = Path(cls.temporary.name)
        cls.dataset = cls.root/'dataset'
        cls.converter = data.converter_module()
        cls.x = np.zeros((12, 99, 64), dtype=np.float32)
        one_w = (np.arange(64*256, dtype=np.float32).reshape(64, 256) % 7)/8192.
        cls.w = np.repeat(one_w[np.newaxis], 12, axis=0)
        cls.bias = np.full((12, 256), .1, dtype=np.float32)
        cls.y = np.full((12, 99, 256), .1, dtype=np.float32)
        cls.weight_raw = npz_bytes(W=cls.w, b=cls.bias)
        cls.sample_raw = npz_bytes(X=cls.x, Y=cls.y)
        cls.source_raw = json.dumps(dict(wav='fixture.wav', split='fixture', wav_sha256='1'*64)).encode('ascii')
        cls.archive = cls.root/'fixture_float.zip'
        with zipfile.ZipFile(str(cls.archive), 'w', compression=zipfile.ZIP_DEFLATED) as zipped:
            zipped.writestr(precision.ARCHIVE_ROOT+'shared_weights.npz', cls.weight_raw)
            zipped.writestr(precision.ARCHIVE_ROOT+'sample_001/float_tensors.npz', cls.sample_raw)
            zipped.writestr(precision.ARCHIVE_ROOT+'sample_001/source.json', cls.source_raw)
        cls.converter.convert_sample(cls.sample_raw, cls.converter.arrays(cls.weight_raw, weights=True), cls.dataset/'sample_001')
        inventory = {p.relative_to(cls.dataset).as_posix():dict(bytes=p.stat().st_size, sha256=data.sha(p))
                     for p in cls.dataset.rglob('*.hex')}
        data.save(cls.dataset/'SHA256_FILES.json', inventory)
        cls.archive_sha = data.sha(cls.archive)
        cls.inventory_sha = data.sha(cls.dataset/'SHA256_FILES.json')
        data.save(cls.dataset/'manifest.json', dict(format=data.FORMAT, archive_sha256=cls.archive_sha,
            weights_sha256=precision.digest_bytes(cls.weight_raw), samples=[dict(sample=1, original_rank=1,
            sample_sha256=precision.digest_bytes(cls.sample_raw), wav='fixture.wav', split='fixture', wav_sha256='1'*64)]))
        cls.manifest_sha = data.sha(cls.dataset/'manifest.json')

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def test_full_fixture_audit_preserves_sources_and_cannot_claim100(self):
        hashes = {str(path): data.sha(path) for path in self.dataset.rglob('*') if path.is_file()}
        output = self.root/'audit_success'
        with mock.patch.object(precision, 'ARCHIVE_SHA', self.archive_sha), \
             mock.patch.object(data, 'DATA100_INVENTORY_SHA', self.inventory_sha):
            report = precision._audit(self.archive, self.dataset, output, self.manifest_sha, sample_count=1)
        self.assertEqual(report['status'], 'fixture_passed')
        self.assertEqual((report['samples'], report['tasks'], report['outputs']), (1, 12, 304128))
        self.assertFalse(report['internal_precision_verified'])
        self.assertFalse(report['cpu_executed'])
        self.assertFalse(report['official_precision_verified'])
        self.assertTrue(report['integer_reference_hex_verified'])
        self.assertLess(report['max_layer_nrmse_percent'], 3)
        self.assertEqual(hashes, {str(path): data.sha(path) for path in self.dataset.rglob('*') if path.is_file()})

    def test_wrong_archive_or_manifest_identity_fails_before_output(self):
        with self.assertRaisesRegex(ValueError, 'archive SHA'):
            precision._audit(self.archive, self.dataset, self.root/'bad_archive', self.manifest_sha, sample_count=1)
        with mock.patch.object(precision, 'ARCHIVE_SHA', self.archive_sha):
            with self.assertRaisesRegex(ValueError, 'manifest changed'):
                precision._audit(self.archive, self.dataset, self.root/'bad_manifest', '0'*64, sample_count=1)
        self.assertFalse((self.root/'bad_archive').exists())
        self.assertFalse((self.root/'bad_manifest').exists())

    def test_full100_cannot_accept_one_sample_inventory(self):
        with mock.patch.object(precision, 'ARCHIVE_SHA', self.archive_sha), \
             mock.patch.object(data, 'DATA100_INVENTORY_SHA', self.inventory_sha):
            with self.assertRaisesRegex(ValueError, 'exact frozen sample'):
                precision._audit(self.archive, self.dataset, self.root/'bad_count', self.manifest_sha)

    def test_quantized_weight_coordinates_checked_even_when_zero_x_hides_output(self):
        altered = self.w[0].astype(np.float64).copy();altered[1, 200] += .01
        with self.assertRaisesRegex(ValueError, 'original W coordinates'):
            precision.audit_layer(self.dataset/'sample_001/layer_01', self.x[0], altered,
                                  self.bias[0], self.y[0], self.converter)

    def test_float_error_is_fresh_not_reused_from_old_metadata(self):
        row = precision.audit_layer(self.dataset/'sample_001/layer_01', self.x[0], self.w[0],
                                    self.bias[0], np.ones((99, 256), dtype=np.float64), self.converter)
        self.assertGreater(row['nrmse_percent'], 80)
        self.assertEqual(row['integer_mismatches'], 0)

    def test_aggregation_combines_sse_and_energy_not_percentages(self):
        rows = []
        for layer in range(1, 13):
            for sse, energy in ((1., 1.), (1., 100.)):
                rows.append(dict(layer=layer, outputs=1, sse=sse, reference_energy=energy,
                                 clipping=dict(x=0, w=0, b=0), saturated=0))
        result = precision.aggregate(rows)
        self.assertAlmostEqual(result[0]['nrmse_percent'], 100*np.sqrt(2/101))
        self.assertNotAlmostEqual(result[0]['nrmse_percent'], (100+10)/2)

    def test_independent_signed33_prefix_and_rounding(self):
        x = np.full((99, 64), -8192, dtype=np.int64)
        w = np.full((64, 256), -2048, dtype=np.int64)
        bias = np.full(256, (1 << 31)-1, dtype=np.int64)
        ref, minimum, maximum = precision.independent_reference(x, w, bias)
        self.assertEqual(int(ref['total'][0, 0]), 3221225471)
        self.assertEqual(maximum, 1073741824)
        self.assertEqual(int(ref['result'][0, 0]), 32767)
        self.assertEqual(int(ref['saturated'].sum()), 25344)
        x.fill(0);w.fill(0)
        edges = [511, 512, 513, -511, -512, -513]
        bias[:6] = edges
        ref, _, _ = precision.independent_reference(x, w, bias)
        self.assertEqual(ref['result'][0, :6].tolist(), [0, 1, 1, 0, -1, -1])


if __name__ == '__main__':
    unittest.main()
