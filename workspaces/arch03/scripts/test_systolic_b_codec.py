"""Independent bit/coordinate checks and malformed-input tests for B/v3."""
import random
import struct
import tempfile
import unittest
from pathlib import Path
import systolic_b_codec as c
from test_icb32_codec import make_raw


def independent_bits(data, widths, signed):
    bits = [(byte >> bit) & 1 for byte in data for bit in range(8)]
    cursor, out = 0, []
    for width in widths:
        v = sum(bits[cursor + bit] << bit for bit in range(width))
        if signed and width and bits[cursor + width - 1]:
            v -= 1 << width
        out.append(v)
        cursor += width
    return out


class CodecTests(unittest.TestCase):
    def test_row_modes_extremes_constants_crosswords(self):
        vectors = [[7] * 64, [-32768] * 64, [32767] * 64,
                   [-32768, 32767] * 32, list(range(-31, 33)),
                   [30000 + (k % 17) for k in range(64)]]
        for width in range(1, 17):
            vectors.append(([-(1 << (width - 1)), (1 << (width - 1)) - 1, 0, -1] * 16))
        seen = set()
        for values in vectors:
            data, info = c.encode_row(values)
            seen.add(info['mode'])
            self.assertEqual(len(data), min(info['candidates'].values()))
            self.assertEqual(c.decode_row(data, 0), (values, len(data)))
            header = int.from_bytes(data[:4], 'little')
            width, mode = (header >> 2) & 31, header & 3
            base = struct.unpack('<h', data[2:4])[0]
            actual = independent_bits(data[4:], [width] * 64, mode != c.X_DELTA)
            if mode == c.X_DELTA:
                actual = [v + base for v in actual]
            self.assertEqual(actual, values)
        self.assertEqual(seen, {'raw', 'signed', 'delta'})

    def test_weight_modes_column_order_and_complete_sizes(self):
        # Lane-dependent ranges choose column mode, k-block ranges choose block.
        cols = [(-(1 << lane) if k % 2 else (1 << lane) - 1)
                for k in range(64) for lane in range(16)]
        blocks = [(-(1 << (i // 64)) if i % 2 else (1 << (i // 64)) - 1)
                  for i in range(1024)]
        full = [-32768, 32767] * 512
        for values, expected in [(cols, 'column'), (blocks, 'block'), (full, 'raw')]:
            data, info = c.encode_weight(values)
            self.assertEqual(info['mode'], expected)
            self.assertEqual(len(data), min(info['candidates'].values()))
            self.assertEqual(c.decode_weight(data, 0), (values, len(data)))
            if expected == 'column':
                table = data[4:12]
                widths = [1 + ((table[lane // 2] >> (4 * (lane % 2))) & 15) for lane in range(16)]
                self.assertEqual(independent_bits(data[12:], widths * 64, True), values)

    def test_task_layout_coordinates_and_raw_fallback(self):
        for raw, force in [(make_raw(), False), (make_raw(True), False), (make_raw(), True)]:
            data = c.encode(raw, force)
            wire = c.decode_wire(data)
            self.assertEqual(c.verify_coordinates(raw, wire), 23488)
            self.assertEqual(c.decode(data), raw)
            self.assertLessEqual(len(data), 47008)
            self.assertEqual(c.read_header(data)['raw'], force or raw == make_raw(True))
            info = c.describe(data)
            self.assertLess(info['prefix_bytes'], info['all_x_bytes'])
            self.assertLess(info['all_x_bytes'], len(data))
            for at in (0, 2048, 2144, 14814, 14816, len(wire) - 2):
                corrupt = bytearray(wire)
                corrupt[at] ^= 1
                with self.assertRaisesRegex(ValueError, 'mismatch'):
                    c.verify_coordinates(raw, bytes(corrupt))

    def test_global_headers_truncation_trailing_v2_rejection(self):
        data = c.encode(make_raw())
        for word in range(8):
            bad = bytearray(data)
            bad[word * 4 + 3] ^= 128
            with self.assertRaises(ValueError):
                c.decode(bytes(bad))
        for n in (0, 4, 28, 32, len(data) - 4, len(data) - 1):
            with self.assertRaises(ValueError):
                c.decode(data[:n])
        with self.assertRaises(ValueError):
            c.decode(data + b'\0' * 4)
        with self.assertRaises(ValueError):
            c.decode(c.v2.encode(make_raw()))

    def test_row_bad_headers_overflow_and_truncation(self):
        for h in (3, 0, 1 << 7, 17 << 2, (1 << 16) | (8 << 2), 2 | (15 << 2)):
            with self.assertRaises(ValueError):
                c.decode_row(struct.pack('<I', h) + b'\0' * 128, 0)
        # Base 32767 + delta 1 would overflow; wrapping is forbidden.
        with self.assertRaisesRegex(ValueError, 'signed16'):
            c.decode_row(struct.pack('<I', 1 | (1 << 2) | (32767 << 16)) + b'\xff' * 8, 0)
        data, _ = c.encode_row(list(range(64)))
        with self.assertRaises(ValueError):
            c.decode_row(data[:-4], 0)

    def test_bad_weight_modes_tables_payloads_and_bias(self):
        for header in (3, 256, 0xffffffff):
            with self.assertRaises(ValueError):
                c.decode_weight(struct.pack('<I', header) + b'\0' * 2048, 0)
        for bad in (struct.pack('<I', 2), struct.pack('<IQ', 2, 0), struct.pack('<I', 1) + b'\0' * 8):
            with self.assertRaises(ValueError):
                c.decode_weight(bad, 0)
        for force in (False, True):
            data = bytearray(c.encode(make_raw(), force))
            if force:
                bias = 32 + 2048
            else:
                _, bias = c.decode_weight(bytes(data), 32)
            data[bias + 5] = 255
            with self.assertRaisesRegex(ValueError, 'bias'):
                c.decode(bytes(data))

    def test_random_losslessness_and_modes(self):
        rng = random.Random(20261111)
        for _ in range(20):
            lo = rng.randrange(-32768, 32768)
            hi = rng.randrange(lo, 32768)
            values = [rng.randint(lo, hi) for _ in range(64)]
            data, _ = c.encode_row(values)
            self.assertEqual(c.decode_row(data, 0)[0], values)

    def test_export_wire_words_and_refuse_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            raw, out = Path(tmp) / 'raw.bin', Path(tmp) / 'v3'
            raw.write_bytes(make_raw())
            info = c.export(raw, out)
            words = (out / 'load32.hex').read_text().split()
            self.assertEqual(b''.join(struct.pack('<I', int(v, 16)) for v in words), (out / 'load.bin').read_bytes())
            self.assertEqual(info['coordinate_halfwords_checked'], 23488)
            self.assertFalse(info['rtl_verified'])
            with self.assertRaises(FileExistsError):
                c.export(raw, out)


if __name__ == '__main__':
    unittest.main()
