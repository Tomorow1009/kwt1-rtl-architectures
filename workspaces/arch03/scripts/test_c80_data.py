"""C80 source identity, full reference and coordinate preparation checks."""
import copy
from pathlib import Path
import tempfile
import unittest

import c80_data as data
import n1_data
from test_n1_data import fixture


class C80DataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix='c80_data_')
        cls.root = Path(cls.temporary.name); cls.source = cls.root/'source'
        cls.words, cls.totals, cls.results, cls.sats = fixture(cls.source)
        cls.target = cls.root/'compressed'
        cls.before = {p.name: data.sha(p) for p in cls.source.iterdir()}
        data.prepare_case(cls.source, cls.target)

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def test_prepared_references_and_distinct_identity(self):
        record = data.verify_prepared(self.source, self.target)
        self.assertEqual(record['layout'], 0x00100006)
        self.assertEqual(record['internal_halfwords'], 23488)
        self.assertEqual(record['external_raw_halfwords'], 23232)
        self.assertFalse(record['rtl_verified'])
        self.assertFalse(record['stage_accepted'])
        for name, expected in [('total', self.totals), ('result', self.results), ('saturated', self.sats)]:
            actual = n1_data.hex_values(self.target/(name+'.hex'), 25344,
                                       n1_data.FILES[name+'.hex'][0], name != 'saturated')
            self.assertEqual(actual, expected)
        with self.assertRaises(ValueError): n1_data.verify_prepared(self.source, self.target)
        with self.assertRaises(ValueError): data.prepare_case(self.source, self.target)
        with self.assertRaises(ValueError): data.prepare_case(self.source, self.root/'old', layout_id=0x00100004)
        self.assertEqual({p.name: data.sha(p) for p in self.source.iterdir()}, self.before)

    def test_raw_stream_bias_recovery(self):
        target = self.root/'raw'
        data.prepare_case(self.source, target, force_raw=True)
        record = data.verify_prepared(self.source, target)
        self.assertTrue(record['raw'])
        self.assertEqual(record['encoded_bytes'], 46496)
        self.assertEqual((target/'load.bin').read_bytes(), (self.target/'load.bin').read_bytes())

    def test_changed_layout_and_source_reference_rejected(self):
        path = self.target/'layout_manifest.json'; original = path.read_bytes()
        try:
            meta = data.read(path); meta['layout'] = 0x00100004; data.save(path, meta)
            with self.assertRaises(ValueError): data.verify_prepared(self.source, self.target)
        finally: path.write_bytes(original)
        path = self.source/'total.hex'; original = path.read_bytes()
        layout = self.source/'layout.json'; original_layout = layout.read_bytes()
        try:
            changed = copy.copy(self.totals); changed[-1] += 1
            n1_data.write_hex(path, changed, 33)
            meta = data.read(layout); meta['files']['total.hex'] = dict(bytes=path.stat().st_size, sha256=data.sha(path))
            data.save(layout, meta)
            with self.assertRaisesRegex(ValueError, 'row=98 column=255'):
                data.prepare_case(self.source, self.root/'bad_reference')
        finally:
            path.write_bytes(original); layout.write_bytes(original_layout)


if __name__ == '__main__': unittest.main()
