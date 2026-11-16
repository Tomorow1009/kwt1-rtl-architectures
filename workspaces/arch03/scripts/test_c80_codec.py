import unittest

import c80_codec as codec
import c80_codec_candidate as candidate
import n1_codec
import test_c80_codec_candidate as fixtures


class C80HostIdentity(unittest.TestCase):
    def test_selected_payload_and_internal_bias_recovery(self):
        raw,coordinates=fixtures.CandidateTests.fixture()
        for fallback in (False,True):
            old,_=candidate.encode(raw,force_raw=fallback)
            new=codec.from_candidate(old)
            self.assertEqual(old[32:],new[32:])
            self.assertEqual(len(old),len(new))
            self.assertEqual(codec.decode_coordinates(new),coordinates)
            self.assertEqual(codec.decode(new),raw)
            wire=codec.decode_wire(new)
            self.assertEqual(wire,raw[12672:14816]+raw[:12672]+raw[14816:])
            self.assertEqual(len(wire),46976)
            h=codec.read_header(new)
            self.assertEqual(h['external_raw_halfwords'],23232)
            self.assertEqual(h['internal_halfwords'],23488)
            self.assertFalse(codec.describe(new)['rtl_verified'])
            with self.assertRaises(ValueError):n1_codec.decode(new)
        with self.assertRaises(ValueError):codec.read_header(candidate.encode(raw)[0])
        with self.assertRaises(ValueError):codec.from_candidate(candidate.encode(raw,'compact_bias_v3')[0])

    def test_header_fields_and_truncation_rejected(self):
        raw,_=fixtures.CandidateTests.fixture();data=codec.encode(raw)
        for at in range(0,32,4):
            altered=bytearray(data);altered[at]^=0x80
            with self.assertRaises(ValueError):codec.decode(bytes(altered))
        for cut in (1,4,64):
            with self.assertRaises(ValueError):codec.decode(data[:-cut])
        with self.assertRaises(ValueError):codec.decode(data+b'\0'*4)
        old=n1_codec.encode(raw)
        with self.assertRaises(ValueError):codec.decode(old)


if __name__ == '__main__':unittest.main()
