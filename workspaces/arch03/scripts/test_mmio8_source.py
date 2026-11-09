"""Software contract tests only. No simulator or ASIC execution is claimed."""
import ast
from pathlib import Path
import struct
import unittest
import build_mmio8_source as firmware
import mmio8_source_layout as layout


class Mmio8SourceTests(unittest.TestCase):
    def setUp(self):
        self.words = [(i*319+7) & 65535 for i in range(23488)]
        for col in range(256):
            self.words[6336+(col//8)*536+512+(col % 8)*3+2] = col
        self.payload = struct.pack('<23488H', *self.words)
        self.packed = list(struct.unpack('<11744I', self.payload))

    def test_original_halfword_and_byte_order(self):
        layout.verify_words(self.words, self.packed, self.payload)
        self.assertEqual(self.packed[0], self.words[0] | (self.words[1] << 16))

    def test_reversed_halfword_order_rejected(self):
        changed = self.packed[:]
        changed[0] = (changed[0] >> 16) | ((changed[0] & 65535) << 16)
        with self.assertRaises(ValueError):
            layout.verify_words(self.words, changed, self.payload)

    def test_tile16_instead_of_original_tile8_rejected(self):
        from dma16_batch import reorder_words
        wrong = struct.pack('<23488H', *reorder_words(self.words))
        with self.assertRaises(ValueError):
            layout.verify_words(self.words, list(struct.unpack('<11744I', wrong)), wrong)

    def test_byte_endianness_error_rejected(self):
        changed = bytearray(self.payload)
        changed[0], changed[1] = changed[1], changed[0]
        with self.assertRaises(ValueError):
            layout.verify_words(self.words, self.packed, changed)

    def test_bias40_padding_rejected_even_if_all_encodings_match(self):
        changed = self.words[:]
        changed[6336+512+2] = 256
        raw = struct.pack('<23488H', *changed)
        with self.assertRaises(ValueError):
            layout.verify_words(changed, list(struct.unpack('<11744I', raw)), raw)

    def test_short_source_rejected(self):
        with self.assertRaises(ValueError):
            layout.verify_words(self.words, self.packed[:-1], self.payload)

    def test_program_only_elf_boundary(self):
        result = firmware.self_test()
        self.assertEqual(result['checks'], 8)
        self.assertIs(result['cpu_executed'], False)

    def test_python36_syntax(self):
        for name in ('build_mmio8_source.py', 'mmio8_source_layout.py'):
            ast.parse(Path(__file__).with_name(name).read_text(encoding='utf8'), feature_version=(3, 6))


if __name__ == '__main__':
    unittest.main()
