"""Synthetic source-join checks; no TensorFlow, real audio or server access."""
import ast
import copy
from pathlib import Path
import sys
import tempfile
import unittest

import n1_audio_path_join as join


class AudioPathJoinTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.index = dict(schema='n1-audio-path-index-v2', source_csv_sha256=join.CSV_SHA,
            count=105829, index_base=0,
            paths=['fixture/%06d.wav' % n for n in range(105829)],
            splits=['training']*84843+['testing']*11005+['validation']*9981)
        cls.selected = list(range(83))+list(range(84843,84856))+list(range(95848,95852))
        cls.manifest = dict(weights_sha256=join.WEIGHTS_SHA, archive_sha256=join.ARCHIVE_SHA,
            samples=[dict(sample=n+1, original_rank=n+1, wav=cls.index['paths'][i],
                split=cls.index['splits'][i], wav_sha256='1'*64, sample_sha256='2'*64)
                for n, i in enumerate(cls.selected)])

    def changed(self, key, value):
        manifest = copy.deepcopy(self.manifest)
        manifest['samples'][0][key] = value
        return join.evaluate(self.index, manifest)

    def test_positive_100_indices_and_splits(self):
        result = join.evaluate(self.index, self.manifest)
        self.assertTrue(result['passed'])
        self.assertEqual(result['indices'], self.selected)
        self.assertFalse(result['wav_bytes_verified'])
        self.assertFalse(result['float_source_recovered'])

    def test_missing_path_rejected(self):
        result = self.changed('wav', 'missing/missing.wav')
        self.assertFalse(result['passed'])
        self.assertEqual(result['missing'], 1)

    def test_duplicate_wave_rejected(self):
        result = self.changed('wav', self.manifest['samples'][1]['wav'])
        self.assertFalse(result['passed'])
        self.assertEqual(result['duplicate_wavs'], 1)

    def test_split_mismatch_rejected(self):
        result = self.changed('split', 'testing')
        self.assertFalse(result['passed'])
        self.assertEqual(result['split_mismatches'], 1)

    def test_duplicate_sample_rejected(self):
        result = self.changed('sample', 2)
        self.assertFalse(result['passed'])
        self.assertEqual(result['duplicate_sample_ids'], 1)

    def test_rank_mismatch_rejected(self):
        result = self.changed('original_rank', 2)
        self.assertFalse(result['passed'])
        self.assertFalse(result['ranks_match'])

    def test_short_source_hash_rejected(self):
        result = self.changed('wav_sha256', '0'*63)
        self.assertFalse(result['passed'])
        self.assertEqual(result['malformed_source_hashes'], 1)

    def test_input_wrong_sha_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/'fixture'
            path.write_bytes(b'fixture')
            with self.assertRaisesRegex(ValueError, 'SHA-256'):
                join.checked_read(path, '0'*64, 1000000)
            self.assertEqual(path.read_bytes(), b'fixture')

    def test_ascii_python36_parse(self):
        source = Path(join.__file__).read_bytes().decode('ascii')
        if sys.version_info >= (3, 8):
            ast.parse(source, feature_version=6)
        else:
            ast.parse(source)


if __name__ == '__main__':
    unittest.main()
