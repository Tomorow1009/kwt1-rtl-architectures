import copy
import unittest
import n1_float_recover100 as recovery


class SourceSelectionTests(unittest.TestCase):
    def setUp(self):
        self.rows = [dict(sample=i, original_rank=i, wav='word/%03d.wav'%i,
                         split='training', wav_sha256='a'*64) for i in range(1,101)]

    def test_exact_order(self):
        recovery.validate_samples(self.rows)

    def test_missing_sample(self):
        with self.assertRaisesRegex(ValueError, 'exactly100'):
            recovery.validate_samples(self.rows[:-1])

    def test_reordered_or_reranked(self):
        self.rows[20],self.rows[21] = self.rows[21],self.rows[20]
        with self.assertRaisesRegex(ValueError, 'rank/order'):
            recovery.validate_samples(self.rows)

    def test_duplicate_or_unsafe_path(self):
        for replacement in (self.rows[0]['wav'], '../other.wav', '/word/other.wav', 'word\\other.wav'):
            with self.subTest(replacement=replacement):
                rows=copy.deepcopy(self.rows)
                rows[10]['wav']=replacement
                with self.assertRaises(ValueError):
                    recovery.validate_samples(rows)

    def test_missing_original_hash(self):
        self.rows[99]['wav_sha256']='a'*63
        with self.assertRaisesRegex(ValueError, 'Invalid WAV hash'):
            recovery.validate_samples(self.rows)


if __name__ == '__main__':
    unittest.main()
