"""Wire-level/adversarial codec checks, including independent bit decoding."""
import random
import struct
import tempfile
import unittest
from pathlib import Path

import icb32_codec as c


def independent_block(data):
    # Deliberately use individual byte bits, not the codec's packed integer.
    h = struct.unpack_from('<I', data)[0]
    width, count = h & 31, ((h >> 5) & 63) + 1
    bits = [(byte >> bit) & 1 for byte in data[4:] for bit in range(8)]
    return [sum(bits[i * width + bit] << bit for bit in range(width - 1))
            - (bits[(i + 1) * width - 1] << (width - 1)) for i in range(count)]


def make_raw(full=False):
    rng = random.Random(20261110)
    values = [rng.randrange(-32768, 32768) if full else rng.randrange(-127, 128) for _ in range(c.HALVES)]
    for tile in range(16):
        for lane in range(16):
            i = 6336 + tile * 1072 + 1024 + lane * 3
            values[i:i + 3] = [-32768, -1, 255]  # signed40 bias, zero upper padding
    return b''.join(struct.pack('<H', v & 65535) for v in values)


class CodecTests(unittest.TestCase):
    def test_all_widths_extremes_tails_and_independent_decoder(self):
        for width in range(1, 17):
            lo, hi = -(1 << (width - 1)), (1 << (width - 1)) - 1
            for count in (1, 3, 31, 63, 64):
                values = ([lo, hi, 0, -1] * 16)[:count]
                encoded = c.encode_block(values)
                self.assertEqual(c.signed_width(values), width)
                self.assertEqual(independent_block(encoded), values)
                self.assertEqual(c.decode_block(encoded), (values, len(encoded)))

    def test_full_task_stream_and_bias_coordinates(self):
        raw = make_raw()
        encoded = c.encode(raw)
        self.assertFalse(c.read_header(encoded)['raw'])
        self.assertEqual(c.decode(encoded), raw)
        info = c.describe(encoded)
        self.assertEqual(info['transfer_transactions'], len(encoded) // 2 + 12672)
        self.assertLess(info['prefix_bytes'], len(encoded))

    def test_full_width_automatic_and_forced_raw_fallback(self):
        for raw, force in [(make_raw(True), False), (make_raw(), True)]:
            encoded = c.encode(raw, force_raw=force)
            self.assertTrue(c.read_header(encoded)['raw'])
            self.assertEqual(len(encoded), 47008)
            self.assertEqual(c.decode(encoded), raw)
            self.assertLessEqual(len(encoded), 49152)

    def test_header_corruption_and_length_rejected(self):
        encoded = c.encode(make_raw())
        for index in range(8):
            data = bytearray(encoded)
            word = struct.unpack_from('<I', data, index * 4)[0]
            struct.pack_into('<I', data, index * 4, word ^ 0x80000000)
            with self.assertRaises(ValueError):
                c.decode(bytes(data))
        for n in (0, 4, 28, 32, len(encoded) - 4, len(encoded) - 1):
            with self.assertRaises(ValueError):
                c.decode(encoded[:n])
        with self.assertRaises(ValueError):
            c.decode(encoded + b'\0' * 4)

    def test_bad_block_count_width_reserved_and_padding(self):
        for word in (0, 17, 31, 1 << 11, 0xffffffff):
            with self.assertRaises(ValueError):
                c.decode_block(struct.pack('<I', word) + b'\0' * 128)
        with self.assertRaisesRegex(ValueError, 'count'):
            c.decode_block(c.encode_block([1, 2, 3]), expected_count=64)
        encoded = bytearray(c.encode_block([0]))
        encoded[-1] = 0x80
        with self.assertRaisesRegex(ValueError, 'padding'):
            c.decode_block(bytes(encoded))
        block = c.encode_block([-32768] * 64)
        with self.assertRaisesRegex(ValueError, 'Truncated'):
            c.decode_block(block[:-4])

    def test_nonzero_bias_padding_never_accepted(self):
        raw = bytearray(make_raw())
        raw[12672 + 2048 + 5] = 255
        with self.assertRaisesRegex(ValueError, 'bias'):
            c.encode(bytes(raw))
        encoded = bytearray(c.encode(make_raw(), force_raw=True))
        encoded[32 + 12672 + 2048 + 5] = 255
        with self.assertRaisesRegex(ValueError, 'bias'):
            c.decode(bytes(encoded))

    def test_block_input_validation(self):
        for v in ([], [0] * 65, [32768], [-32769], [1.2]):
            with self.assertRaises(ValueError):
                c.encode_block(v)

    def test_export_words_reconstruct_actual_runtime_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            src, out = Path(tmp) / 'raw.bin', Path(tmp) / 'v2'
            src.write_bytes(make_raw())
            info = c.export(src, out)
            actual = b''.join(struct.pack('<I', int(v, 16)) for v in (out / 'load32.hex').read_text().split())
            self.assertEqual(actual, (out / 'load.bin').read_bytes())
            self.assertEqual(c.decode(actual), src.read_bytes())
            self.assertFalse(info['rtl_verified'])
            with self.assertRaises(FileExistsError):
                c.export(src, out)


if __name__ == '__main__':
    unittest.main()
