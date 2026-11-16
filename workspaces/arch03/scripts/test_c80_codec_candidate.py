import random
import struct
import unittest

import c80_codec_candidate as codec


class CandidateTests(unittest.TestCase):
    def test_rice_boundaries_all_parameters(self):
        rng=random.Random(0x7834a9f1)
        for bits in (12,15):
            for k in range(12):
                values=[-(1<<(bits-1)),(1<<(bits-1))-1,-1,0,1]
                values += [rng.randrange(-(1<<(bits-1)),1<<(bits-1)) for _ in range(128)]
                payload=codec.pack(f for v in values for f in codec.rice_fields(v,k,bits))
                reader=codec.Reader(payload,0)
                self.assertEqual([codec.rice_read(reader,k,bits) for _ in values],values)
                self.assertEqual(reader.finish(),len(payload))
                self.assertEqual((codec.rice_cost(values,k,bits)+7)//8,len(payload))

    def test_predictor_ranges_and_resets(self):
        rng=random.Random(0x7834a9f1)
        samples=[[0]*64,[-8192]*64,[8191]*64,[-8192,8191]*32,list(range(-32,32))]
        samples += [[rng.randrange(-8192,8192) for _ in range(64)] for _ in range(128)]
        for row in samples:
            for previous in (None,[-8192]*64,[8191]*64):
                payload,_=codec.encode_row(row,previous)
                got,end=codec.decode_row(payload,0,previous)
                self.assertEqual(got,row);self.assertEqual(end,len(payload))
        p=codec.descriptor(4,0)
        with self.assertRaisesRegex(ValueError,'Missing previous'):
            codec.decode_row(p,0,None)
        # Overflow must be rejected, never clipped to signed14.
        p=codec.descriptor(4,2)+codec.pack((1,2) for _ in range(64))
        with self.assertRaisesRegex(ValueError,'reconstruction'):
            codec.decode_row(p,0,[8191]*64)

    def test_weight_modes_and_signed_extremes(self):
        values=tuple((i%4096)-2048 for i in range(1024))
        for mode in range(5):
            if mode==0:
                p=codec.descriptor(0,12)+codec.pack((v,12) for v in values)
            elif mode in (1,2):
                p=codec.descriptor(mode)+codec.pack((12,4) for _ in range(16))+codec.pack((v,12) for v in values)
            elif mode==3:
                p=codec.descriptor(3,4)+codec.pack(f for v in values for f in codec.rice_fields(v,4,12))
            else:
                p=codec.descriptor(4)+codec.pack((4,4) for _ in range(16))+codec.pack(f for v in values for f in codec.rice_fields(v,4,12))
            got,end=codec.decode_weight(p,0)
            self.assertEqual(got,list(values));self.assertEqual(end,len(p))
        for values in ((0,)*1024,(-2048,2047)*512):
            p,_=codec.encode_weight(values)
            self.assertEqual(codec.decode_weight(p,0)[0],list(values))

    def test_each_row_mode_with_unaligned_byte_start(self):
        values=list(range(64));previous=[v-1 for v in values]
        modes=[
            codec.descriptor(0,14)+codec.pack((v,14) for v in values),
            codec.descriptor(1,7)+codec.pack((v,7) for v in values),
            codec.descriptor(2,6)+struct.pack('<h',0)+codec.pack((v,6) for v in values),
            codec.descriptor(3,2)+struct.pack('<h',0)+codec.pack((1,2) for _ in range(63)),
            codec.descriptor(4,2)+codec.pack((1,2) for _ in range(64)),
            codec.descriptor(5,1)+struct.pack('<h',0)+codec.pack(f for _ in range(63) for f in codec.rice_fields(1,1,15)),
            codec.descriptor(6,1)+codec.pack(f for _ in range(64) for f in codec.rice_fields(1,1,15))]
        for payload in modes:
            got,end=codec.decode_row(b'X'+payload,1,previous)
            self.assertEqual(got,values);self.assertEqual(end,len(payload)+1)
        # The 63 two-bit residuals leave two unused high bits, which must be zero.
        bad=bytearray(modes[3]);bad[-1]|=0x80
        with self.assertRaisesRegex(ValueError,'padding'):codec.decode_row(bytes(bad),0)

    @staticmethod
    def fixture():
        x=[[((row*64+k)%16384)-8192 for k in range(64)] for row in range(99)]
        w=[[((k*256+col)%4096)-2048 for col in range(256)] for k in range(64)]
        b=[-(1<<31) if i%3==0 else (1<<31)-1 if i%3==1 else -1 for i in range(256)]
        words=[v&65535 for row in x for v in row]
        for tile in range(16):
            words.extend(w[k][tile*16+lane]&65535 for k in range(64) for lane in range(16))
            for lane in range(16):
                value=b[tile*16+lane]&((1<<40)-1)
                words.extend((value>>shift)&65535 for shift in (0,16,32))
        return struct.pack('<23488H',*words),(x,w,b)

    def test_full_coordinate_reconstruction_and_raw(self):
        raw,expected=self.fixture()
        for profile in ('compact_bias_v3','candidate'):
            for force in (False,True):
                payload,info=codec.encode(raw,profile,force)
                self.assertEqual(codec.decode(payload),expected)
                self.assertEqual(len(payload)%4,0)
                self.assertLessEqual(len(payload),46464+32)
                self.assertEqual(info['bias_bytes'],1024)
                if force:self.assertEqual(len(payload),46496)

    def test_malformed_stream(self):
        raw,_=self.fixture();payload,_=codec.encode(raw)
        for at in range(0,32,4):
            bad=bytearray(payload);bad[at]^=0x80
            with self.assertRaises(ValueError):codec.decode(bytes(bad))
        for cut in (4,8,64):
            with self.assertRaises(ValueError):codec.decode(payload[:-cut])
        with self.assertRaises(ValueError):codec.decode(payload+b'\0'*4)
        with self.assertRaises(ValueError):codec.decode_row(b'\x00\x01',0)
        with self.assertRaises(ValueError):codec.decode_weight(b'\x01\x00'+b'\xff'*8,0)


if __name__=='__main__':unittest.main()
