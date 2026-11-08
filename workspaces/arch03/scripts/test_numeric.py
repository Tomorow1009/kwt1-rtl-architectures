import json
from pathlib import Path
import tempfile
import unittest
import numpy as np
from numeric import (decode, encode_arrays, error_metrics, export_task, integer_model,
                     numeric_format, pack_words, quantize, read_capture, unpack_words)


class NumericTests(unittest.TestCase):
    def setUp(self):
        self.x = np.zeros((99, 64), dtype=np.int64)
        self.w = np.zeros((64, 256), dtype=np.int64)
        self.b = np.zeros(256, dtype=np.int64)

    def test_exact_half_ties_and_adjacent_floats(self):
        values = np.array([.5, -.5, np.nextafter(.5, 0.), np.nextafter(-.5, 0.), 1.5, -1.5])/4096
        actual, clipped = quantize(values, 12, 16)
        np.testing.assert_array_equal(actual, [1, -1, 0, 0, 2, -2])
        self.assertFalse(clipped.any())

    def test_finite_extremes_clip_before_overflow(self):
        result, clipped = quantize(np.array([np.finfo(np.float64).max, -np.finfo(np.float64).max]), 24, 40)
        np.testing.assert_array_equal(result, [(1 << 39)-1, -(1 << 39)])
        self.assertTrue(clipped.all())

    def test_nonfinite_inputs_rejected(self):
        for value in (np.nan, np.inf, -np.inf):
            with self.assertRaisesRegex(ValueError, 'finite'):
                quantize(np.array([value]), 12, 16)

    def test_all_shift_edges_and_saturation(self):
        for shift in range(32):
            half = (1 << (shift-1)) if shift else 0
            values = [0, half, -half, half+1, -half-1, (1 << 39)-1, -(1 << 39)]
            self.b[:len(values)] = values
            result = integer_model(self.x, self.w, self.b, shift)
            for i, value in enumerate(values):
                mag = (abs(value)+half)//(1 << shift)
                rounded = -mag if value < 0 else mag
                expected = min(32767, max(-32768, rounded))
                self.assertEqual(result['result'][0, i], expected)
                self.assertEqual(bool(result['saturated'][0, i]), expected != rounded)
            self.assertTrue(np.isfinite(decode(result['result'], numeric_format(shift))).all())

    def test_full_dot_extremes_and_cancellation(self):
        self.x[:] = -32768; self.w[:] = -32768; self.b[:] = (1 << 39)-1
        result = integer_model(self.x, self.w, self.b, 31)
        self.assertEqual(result['total'][0, 0], 64*32768*32768+(1 << 39)-1)
        self.w[::2] = 32767; self.w[1::2] = -32767; self.b[:] = 0
        self.assertFalse(integer_model(self.x, self.w, self.b)['result'].any())

    def test_packet_roundtrip_and_little_endian(self):
        rng = np.random.RandomState(123)
        x = rng.randint(-32768, 32768, self.x.shape).astype(np.int64)
        w = rng.randint(-32768, 32768, self.w.shape).astype(np.int64)
        self.b[::2] = -(1 << 39); self.b[1::2] = (1 << 39)-1
        packet = pack_words(x, w, self.b)
        self.assertEqual(packet.nbytes, 46976)
        self.assertEqual(packet.tobytes()[:2], (int(x[0, 0]) & 65535).to_bytes(2, 'little'))
        decoded = unpack_words(np.frombuffer(packet.tobytes(), dtype='<u2'))
        for key, expected in [('X', x), ('W', w), ('b', self.b)]:
            np.testing.assert_array_equal(decoded[key], expected)
        packet[6336+512+2] = 256
        with self.assertRaisesRegex(ValueError, 'padding'):
            unpack_words(packet)

    def test_invalid_shape_width_shift_and_scale(self):
        with self.assertRaisesRegex(ValueError, 'shape'):
            encode_arrays(self.x[:1], self.w, self.b)
        self.x[0, 0] = 32768
        with self.assertRaisesRegex(ValueError, 'range'):
            integer_model(self.x, self.w, self.b)
        for shift in (-1, 32, True, 12.):
            with self.assertRaises(ValueError):
                numeric_format(shift)
        config = numeric_format(); config['output_fraction_bits'] = 11
        with self.assertRaisesRegex(ValueError, 'scale'):
            decode(np.array([1]), config)

    def test_zero_reference_floor(self):
        result = error_metrics(np.full((99, 256), 1e-9), np.zeros((99, 256)))
        self.assertAlmostEqual(result['nrmse'], .1)
        self.assertFalse(result['threshold_passed'])

    def test_export_compatible_with_existing_fixture_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); source = root/'source.npz'
            np.savez(str(source), X=self.x, W=self.w, b=self.b)
            config = export_task(source, root/'task', 12, 31)
            self.assertEqual(config['numeric_format']['output_fraction_bits'], -7)
            layout = json.loads((root/'task/layout.json').read_text())
            self.assertEqual(layout['load_words'], 23488)
            with self.assertRaisesRegex(ValueError, 'exists'):
                export_task(source, root/'task', 12)

    def test_fractional_capture_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'capture.csv'; path.write_text('0,1.5\n')
            with self.assertRaisesRegex(ValueError, 'integer capture'):
                read_capture(path)


if __name__ == '__main__':
    unittest.main()
