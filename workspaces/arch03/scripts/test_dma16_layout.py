"""Adversarial layout/coordinate tests; no simulator or TensorFlow required."""
import json
from pathlib import Path
import struct
import tempfile
import unittest

import numpy as np
import dma16_layout as layout
import numeric


def matrices():
    # Values depend on original coordinates and expose row/lane/tile swaps.
    x = (np.arange(6336, dtype=np.int64).reshape(99, 64)*13 % 65536)-32768
    w = (np.arange(16384, dtype=np.int64).reshape(64, 256)*7 % 65536)-32768
    b = np.array([(-1 if j % 2 else 1)*(j*1234567+77) for j in range(256)], dtype=np.int64)
    b[:4] = [-(1 << 39), (1 << 39)-1, -1, 0]
    return x, w, b


def fixture(root, shift=12):
    root.mkdir()
    x, w, b = matrices()
    expected = numeric.integer_model(x, w, b, shift)
    (root/'load.hex').write_text(''.join('%04x\n' % int(v) for v in numeric.pack_words(x, w, b)), encoding='ascii')
    for key, bits in [('total', 41), ('result', 16), ('saturated', 1)]:
        (root/(key+'.hex')).write_text(''.join(('%0*x\n' % ((bits+3)//4, int(v) & ((1 << bits)-1)))
                                             for v in expected[key].flat), encoding='ascii')
    np.savez_compressed(str(root/'expected.npz'), **expected)
    layout.save_json(root/'layout.json', dict(shift=shift, load_words=23488, outputs=25344,
                        sha256={p.name: layout.sha(p) for p in root.iterdir()}))
    return x, w, b


class Tile16Tests(unittest.TestCase):
    def setUp(self):
        self.x, self.w, self.b = matrices()
        self.payload = layout.pack_tile16(self.x, self.w, self.b)

    def test_all_coordinates_signed_extremes_and_tile_boundaries(self):
        actual = layout.verify_coordinates(self.payload, self.x, self.w, self.b)
        for key, expected in [('X', self.x), ('W', self.w), ('b', self.b)]:
            np.testing.assert_array_equal(actual[key], expected)
        self.assertEqual(len(self.payload), 46976)
        for column in (0, 15, 16, 31, 240, 255):
            offset = 12672+(column//16)*2144+(column % 16)*2
            self.assertEqual(struct.unpack_from('<h', self.payload, offset)[0], self.w[0, column])

    def test_packed32_is_low_half_first_little_endian(self):
        x = self.x.copy()
        x[0, :2] = [0x1234, -21555]  # 0xabcd
        raw = layout.pack_tile16(x, self.w, self.b)
        self.assertEqual(raw[:4], b'\x34\x12\xcd\xab')
        self.assertEqual(struct.unpack_from('<I', raw)[0], 0xabcd1234)

    def test_legacy_8lane_layout_is_not_accepted_as_tile16(self):
        legacy = numeric.pack_words(self.x, self.w, self.b).tobytes()
        with self.assertRaisesRegex(ValueError, 'W coordinate mismatch'):
            layout.verify_coordinates(legacy, self.x, self.w, self.b)

    def test_weight_lane_permutation_is_detected(self):
        raw = bytearray(self.payload)
        raw[12672:12676] = raw[12674:12676]+raw[12672:12674]
        with self.assertRaisesRegex(ValueError, 'W coordinate mismatch'):
            layout.verify_coordinates(bytes(raw), self.x, self.w, self.b)

    def test_tile_permutation_is_detected(self):
        raw = self.payload[:12672]+self.payload[14816:16960]+self.payload[12672:14816]+self.payload[16960:]
        with self.assertRaisesRegex(ValueError, 'W coordinate mismatch'):
            layout.verify_coordinates(raw, self.x, self.w, self.b)

    def test_x_coordinate_and_endianness_errors_are_detected(self):
        raw = bytearray(self.payload)
        raw[2:4] = raw[2:4][::-1]
        with self.assertRaisesRegex(ValueError, 'X coordinate mismatch'):
            layout.verify_coordinates(bytes(raw), self.x, self.w, self.b)

    def test_bias_high_padding_is_not_sign_extension(self):
        raw = bytearray(self.payload)
        raw[14725] = 255
        with self.assertRaisesRegex(ValueError, 'Bias high padding'):
            layout.verify_coordinates(bytes(raw), self.x, self.w, self.b)

    def test_bias_value_corruption_is_detected(self):
        raw = bytearray(self.payload)
        raw[14720] ^= 1
        with self.assertRaisesRegex(ValueError, 'Bias coordinate mismatch'):
            layout.verify_coordinates(bytes(raw), self.x, self.w, self.b)

    def test_truncated_or_extra_bytes_are_rejected(self):
        for raw in (self.payload[:-1], self.payload+b'\0'):
            with self.assertRaisesRegex(ValueError, '46976'):
                layout.verify_coordinates(raw, self.x, self.w, self.b)

    def test_out_of_range_and_wrong_shape_are_rejected(self):
        with self.assertRaises(ValueError):
            layout.pack_tile16(self.x[:, :-1], self.w, self.b)
        b = self.b.copy(); b[0] = 1 << 39
        with self.assertRaisesRegex(ValueError, 'out of range'):
            layout.pack_tile16(self.x, self.w, b)
        with self.assertRaises(ValueError):
            layout.pack_tile16(self.x.astype(float), self.w, self.b)

    def test_export_preserves_reference_and_checks_every_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, output = Path(tmp)/'old', Path(tmp)/'new'
            fixture(source, 11)
            original = {p.name: layout.sha(p) for p in source.iterdir()}
            manifest = layout.export_case(source, output)
            self.assertEqual(manifest['numeric_format']['shift'], 11)
            self.assertEqual((output/'result.bin').stat().st_size, 50688)
            self.assertEqual(layout.sha(source/'expected.npz'), layout.sha(output/'expected.npz'))
            self.assertEqual(original, {p.name: layout.sha(p) for p in source.iterdir()})
            self.assertEqual(layout.verify_export(source, output)['outputs'], 25344)
            self.assertFalse(manifest['verification']['rtl_verified'])
            self.assertEqual(manifest['runtime_inputs'], ['load.bin', 'load.hex', 'load32.hex'])
            with self.assertRaisesRegex(ValueError, 'already exists'):
                layout.export_case(source, output)

    def test_source_hash_tampering_stops_before_output_creation(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, output = Path(tmp)/'old', Path(tmp)/'new'
            fixture(source)
            with (source/'load.hex').open('a', encoding='ascii') as stream:
                stream.write('0000\n')
            with self.assertRaisesRegex(ValueError, 'Source hash mismatch'):
                layout.export_case(source, output)
            self.assertFalse(output.exists())

    def test_corrupt_result_with_updated_hash_still_fails_coordinate_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, output = Path(tmp)/'old', Path(tmp)/'new'
            fixture(source)
            manifest = layout.export_case(source, output)
            raw = bytearray((output/'result.bin').read_bytes()); raw[37] ^= 1
            (output/'result.bin').write_bytes(raw)
            manifest['sha256']['result.bin'] = layout.sha(output/'result.bin')
            layout.save_json(output/'layout_manifest.json', manifest)
            with self.assertRaisesRegex(ValueError, 'row-major coordinate mismatch'):
                layout.verify_export(source, output)

    def test_corrupt_hex_with_updated_hash_still_fails_binary_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, output = Path(tmp)/'old', Path(tmp)/'new'
            fixture(source)
            manifest = layout.export_case(source, output)
            lines = (output/'load32.hex').read_text().splitlines()
            lines[0] = '00000000'
            (output/'load32.hex').write_text('\n'.join(lines)+'\n', encoding='ascii')
            manifest['sha256']['load32.hex'] = layout.sha(output/'load32.hex')
            layout.save_json(output/'layout_manifest.json', manifest)
            with self.assertRaisesRegex(ValueError, 'packing mismatch'):
                layout.verify_export(source, output)


if __name__ == '__main__':
    unittest.main()
