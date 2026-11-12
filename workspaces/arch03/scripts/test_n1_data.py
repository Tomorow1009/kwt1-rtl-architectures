"""N1 ABI, reference, identity and coordinate tests; no RTL PASS is inferred."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import struct
import tempfile
import unittest
from unittest import mock

import dma16_batch as geometry
import n1_codec as codec
import n1_data as data
import systolic_b_codec as base


def fixture(folder):
    folder.mkdir()
    x = [[(row % 9)-4]*64 for row in range(99)]
    w = [[(col % 11)-5 for col in range(256)] for _ in range(64)]
    biases = [(-(1 << 31), (1 << 31)-1, 511, 512, 513, -511, -512, -513,
               32767*1024+511, 32767*1024+512, -32768*1024-511, -32768*1024-512)[c % 12]
              for c in range(256)]
    words = [v & 65535 for row in x for v in row]
    for group in range(32):
        for k in range(64):
            words.extend(w[k][group*8+lane] & 65535 for lane in range(8))
        for lane in range(8):
            value = biases[group*8+lane] & ((1 << 40)-1)
            words.extend((value >> shift) & 65535 for shift in (0, 16, 32))
    totals, results, sats = [], [], []
    for row in range(99):
        for col in range(256):
            # Closed-form 64 equal products, not the implementation's loop.
            value = 64*x[row][0]*w[0][col] + biases[col]
            rounded = (abs(value)+512)//1024
            rounded = -rounded if value < 0 else rounded
            result = max(-32768, min(32767, rounded))
            totals.append(value); results.append(result); sats.append(int(result != rounded))
    for name, values in [('load', words), ('total', totals), ('result', results), ('saturated', sats)]:
        data.write_hex(folder/(name+'.hex'), values, data.FILES[name+'.hex'][0])
    data.save(folder/'layout.json', dict(schema=data.SOURCE_SCHEMA, format=data.FORMAT,
        load_words=23488, outputs=25344, bias_storage_bits=40,
        files={name:dict(bytes=(folder/name).stat().st_size, sha256=data.sha(folder/name)) for name in data.FILES}))
    return words, totals, results, sats


class N1DataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix='n1_data_test_')
        cls.root = Path(cls.temporary.name)
        cls.source = cls.root/'source'
        cls.words, cls.totals, cls.results, cls.sats = fixture(cls.source)
        cls.raw = struct.pack('<23488H', *geometry.reorder_words(cls.words))
        cls.encoded = codec.encode(cls.raw)
        cls.prepared = cls.root/'prepared'
        data.prepare_case(cls.source, cls.prepared)

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def copy_source(self, label):
        target = self.root/label
        shutil.copytree(str(self.source), str(target))
        return target

    def rehash(self, source, name):
        meta = data.read(source/'layout.json')
        meta['files'][name] = dict(bytes=(source/name).stat().st_size, sha256=data.sha(source/name))
        data.save(source/'layout.json', meta)

    def test_frozen_converter_identity(self):
        self.assertEqual(data.sha(data.CONVERTER), data.CONVERTER_SHA)

    def test_group8_signed32_bias_and_integer_total33(self):
        _, _, bias = data.decode_group8(self.words)
        self.assertEqual(bias[:2], [-(1 << 31), (1 << 31)-1])
        self.assertLess(min(self.totals), -(1 << 31))
        self.assertGreater(max(self.totals), (1 << 31)-1)
        audit = data.inspect_case(self.source)
        self.assertEqual((audit['outputs'], audit['total_mismatches']), (25344, 0))

    def test_codec_payload_unchanged_and_independent_coordinates(self):
        for raw in (False, True):
            old = base.encode(self.raw, force_raw=raw)
            new = codec.encode(self.raw, force_raw=raw)
            self.assertEqual(new[32:], old[32:])
            self.assertEqual(codec.decode(new), self.raw)
            self.assertEqual(codec.verify_coordinates(self.raw, codec.decode_wire(new)), 23488)
            header = struct.unpack('<8I', new[:32])
            self.assertEqual(header[2], 0x00100004)
            self.assertEqual(header[5:], (23488, 46976, 0x000e0c20))
            with self.assertRaises(ValueError): base.read_header(new)
            with self.assertRaises(ValueError): codec.read_header(old)

    def test_bad_header_lengths_and_truncated_payload(self):
        for index in (0, 1, 2, 3, 4, 5, 6, 7):
            bad = bytearray(self.encoded)
            value = struct.unpack_from('<I', bad, 4*index)[0]
            struct.pack_into('<I', bad, 4*index, value ^ 0x80000000)
            with self.assertRaises(ValueError): codec.decode(bytes(bad))
        for length in (0, 31, len(self.encoded)-1, len(self.encoded)-4):
            bad = bytearray(self.encoded[:length])
            if length >= 32 and length % 4 == 0:
                struct.pack_into('<I', bad, 16, length)
            with self.assertRaises(ValueError): codec.decode(bytes(bad))

    def test_narrow_sign_extension_rejected_encode_and_decode(self):
        for word, replacement in ((0, 0x2000), (6336, 0x0800), (6336+1024+2, 0xffff),
                                  (6336+1024+5, 0x00ff)):
            bad = bytearray(self.raw)
            struct.pack_into('<H', bad, word*2, replacement)
            with self.assertRaises(ValueError): codec.encode(bytes(bad))
            # Legacy raw encoder accepts narrow-invalid values; N1 must reject
            # them after decompression as well as at source preparation.
            # Build the raw wire payload directly so even forbidden legacy
            # bias padding reaches the decoder's rejection path.
            legacy = bytearray(base.encode(self.raw, force_raw=True)[:32] +
                               bad[12672:14816] + bad[:12672] + bad[14816:])
            struct.pack_into('<I', legacy, 8, codec.LAYOUT)
            struct.pack_into('<I', legacy, 28, codec.NUMERIC_FORMAT)
            with self.assertRaises(ValueError): codec.decode(bytes(legacy))

    def test_group8_invalid_extensions_not_only_hashes(self):
        for index, value in ((0, 0x3fff), (6336, 0x0fff), (6336+514, 0x0000)):
            words = list(self.words); words[index] = value
            with self.assertRaises(ValueError): data.decode_group8(words)

    def test_total_exact_width_reserved_bits_and_sign(self):
        target = self.root/'total_single.hex'
        for encoded in ('1ffffffff\n', '100000000\n', '0ffffffff\n'):
            target.write_text(encoded, encoding='ascii')
            self.assertEqual(data.hex_values(target, 1, 33, True)[0],
                             {'1ffffffff\n': -1, '100000000\n': -(1 << 32), '0ffffffff\n': (1 << 32)-1}[encoded])
        for encoded in ('001ffffffff\n', '200000000\n', 'fffffffff\n', '1ffffffff 000000000\n'):
            target.write_text(encoded, encoding='ascii')
            with self.assertRaises(ValueError): data.hex_values(target, 1, 33, True)

    def test_bad_reference_even_with_consistent_metadata(self):
        source = self.copy_source('bad_reference')
        totals = list(self.totals); totals[-1] += 1
        data.write_hex(source/'total.hex', totals, 33)
        self.rehash(source, 'total.hex')
        with self.assertRaisesRegex(ValueError, 'row=98 column=255'):
            data.inspect_case(source)

    def test_prepared_identity_shift_and_npz(self):
        info = data.verify_prepared(self.source, self.prepared)
        self.assertEqual((info['shift'], info['layout'], info['numeric_format_id']), (10, 0x00100004, 0x000e0c20))
        import numpy as np
        with np.load(str(self.prepared/'expected.npz'), allow_pickle=False) as arrays:
            self.assertEqual(arrays['total'].shape, (99, 256))
            self.assertEqual(arrays['total'].ravel().tolist(), self.totals)
        with self.assertRaises(ValueError): data.prepare_case(self.source, self.root/'wrong_layout', layout_id=0x00100003)
        with self.assertRaises(ValueError): data.prepare_case(self.source, self.prepared)

    def test_source_identity_tamper_rejected(self):
        source = self.copy_source('tamper_source')
        changed = list(self.words); changed[0] = 0
        data.write_hex(source/'load.hex', changed, 16)
        with self.assertRaisesRegex(ValueError, 'identity'): data.source_case(source)

    def test_coordinate_capture_accepts_reordering_rejects_duplicates_and_wrong_total(self):
        capture = self.root/'capture.csv'
        rows = ['%d,%d,%d,%d,%d\n' % (i//256, i%256, self.results[i], self.sats[i], self.totals[i])
                for i in reversed(range(25344))]
        capture.write_text(''.join(rows), encoding='ascii')
        self.assertEqual(data.check_capture(capture, self.prepared)['outputs'], 25344)
        capture.write_text(rows[0]+''.join(rows), encoding='ascii')
        with self.assertRaisesRegex(ValueError, 'Duplicate'): data.check_capture(capture, self.prepared)
        capture.write_text(''.join(rows[:-1]), encoding='ascii')
        with self.assertRaisesRegex(ValueError, 'Missing'): data.check_capture(capture, self.prepared)
        fields = rows[0].strip().split(','); fields[4] = str(int(fields[4])+1)
        capture.write_text(','.join(fields)+'\n'+''.join(rows[1:]), encoding='ascii')
        with self.assertRaisesRegex(ValueError, 'total mismatch'): data.check_capture(capture, self.prepared)

    def test_capture_rejects_legacy_four_columns(self):
        capture = self.root/'legacy_capture.csv'
        capture.write_text('0,0,0,0\n', encoding='ascii')
        with self.assertRaisesRegex(ValueError, 'row,col,result,sat,total'):
            data.check_capture(capture, self.prepared)

    def test_dataset_inventory_identity_and_exact_file_set(self):
        root = self.root/'dataset'
        root.mkdir()
        inventory = {}
        for layer in range(1, 13):
            rel = 'sample_001/layer_%02d' % layer
            folder = root/rel
            shutil.copytree(str(self.source), str(folder))
            meta = data.read(folder/'layout.json'); meta['layer'] = layer
            data.save(folder/'layout.json', meta)
            for name in data.FILES:
                inventory[rel+'/'+name] = dict(bytes=(folder/name).stat().st_size, sha256=data.sha(folder/name))
        data.save(root/'manifest.json', dict(format=data.FORMAT))
        data.save(root/'SHA256_FILES.json', inventory)
        expected = data.sha(root/'SHA256_FILES.json')
        tasks = data.index_dataset(root, expected_sha=expected, expected_samples=1)
        self.assertEqual(len(tasks), 12)
        self.assertEqual(tasks[0]['dataset_inventory_sha256'], expected)
        self.assertEqual(tasks[-1]['shift'], 10)
        self.assertNotEqual(tasks[0]['dataset_manifest_sha256'], expected)
        with self.assertRaisesRegex(ValueError, 'inventory changed'):
            data.index_dataset(root, expected_sha='0'*64, expected_samples=1)
        (root/'extra.hex').write_text('0000\n', encoding='ascii')
        with self.assertRaisesRegex(ValueError, 'Extra or missing'):
            data.index_dataset(root, expected_sha=expected, expected_samples=1)
        (root/'extra.hex').unlink()
        (root/'sample_001/layer_01/load.hex').write_text('0000\n', encoding='ascii')
        with self.assertRaisesRegex(ValueError, 'HEX changed'):
            data.index_dataset(root, expected_sha=expected, expected_samples=1)

    def test_batch_storage_gate_precedes_compile(self):
        import n1_batch
        run = self.root/'space_guard'; run.mkdir()
        with mock.patch.object(n1_batch.data, 'index_dataset', return_value=[dict(shift=10)]*1200), \
             mock.patch.object(n1_batch.shutil, 'disk_usage', return_value=type('Disk', (), {'free': 0})()), \
             mock.patch.object(n1_batch.soc, 'compile_design') as compile_design:
            with self.assertRaisesRegex(ValueError, 'Insufficient space'):
                n1_batch.verify({}, run, self.root, self.source, None)
            compile_design.assert_not_called()
        receipt = data.read(run/'storage_budget.json')
        self.assertEqual(receipt['remaining_tasks'], 1200)
        self.assertEqual(receipt['margin'], 1.2)


if __name__ == '__main__':
    unittest.main()
