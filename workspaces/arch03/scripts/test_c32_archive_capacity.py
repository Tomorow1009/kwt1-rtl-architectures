"""Copy-capacity boundaries, concurrent consumption and real tar readback."""
import hashlib
import io
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch
import c32_archive_capacity as c
import n1_archive_runtime as tar


class Capacity(unittest.TestCase):
    def test_default_and_explicit_profiles_keep_exact_twenty_percent(self):
        self.assertEqual(c.policy({})['reserve_bytes'], 2*1024**3)
        p = c.policy({'storage_profile': 'copy_only_512MiB'})
        self.assertEqual(p['reserve_bytes'], 512*1024**2)
        self.assertFalse(p['source_deletion_authorized'])
        for n in (0, 1, 4, 5, 1102799426):
            self.assertEqual(c.required_bytes(n, p), (6*n+4)//5+512*1024**2)
        self.assertEqual(tar.RESERVE, 2*1024**3)

    def test_unknown_and_forged_profiles_and_bad_sizes_rejected(self):
        for name in ('zero', None, 0, [], 'copy_only_512Mib'):
            with self.assertRaises(ValueError):c.policy({'storage_profile': name})
        p = c.policy({})
        for n in (-1, True, 1.5):
            with self.assertRaises(ValueError):c.required_bytes(n, p)
        p['reserve_bytes'] = 0
        with self.assertRaises(ValueError):c.Sink(io.BytesIO(), '.', p)

    def test_no_first_write_when_space_below_guard(self):
        p = c.policy({'storage_profile': 'copy_only_512MiB'})
        out = io.BytesIO();sink = c.Sink(out, '.', p)
        with patch.object(c.shutil, 'disk_usage', return_value=types.SimpleNamespace(
                free=p['reserve_bytes']+c.CHUNK+2)):
            with self.assertRaisesRegex(ValueError, 'retained'):sink.write(b'abc')
        self.assertEqual(out.getvalue(), b'');self.assertEqual(sink.tell(), 0)

    def test_another_writer_consumes_space_after_first_chunk(self):
        p = c.policy({});out = io.BytesIO();sink = c.Sink(out, '.', p)
        room = [types.SimpleNamespace(free=p['reserve_bytes']+2*c.CHUNK),
                types.SimpleNamespace(free=p['reserve_bytes'])]
        with patch.object(c.shutil, 'disk_usage', side_effect=room):
            sink.write(b'a'*c.CHUNK)
            with self.assertRaises(ValueError):sink.write(b'b')
        self.assertEqual(sink.tell(), c.CHUNK)
        self.assertEqual(out.getvalue(), b'a'*c.CHUNK)

    def test_short_write_rejected(self):
        p = c.policy({})
        stream = types.SimpleNamespace(write=lambda data: len(data)-1)
        sink = c.Sink(stream, '.', p)
        with patch.object(c.shutil, 'disk_usage', return_value=types.SimpleNamespace(free=10**12)):
            with self.assertRaises(OSError):sink.write(b'abc')
        self.assertEqual(sink.count, 0)

    def test_real_archive_matches_count_and_full_member_readback(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=root/'source.bin';data=bytes(range(256))*4097
            source.write_bytes(data);s=source.stat()
            rows=[dict(source=str(source),member='fixture/source.bin',kind='regular',
                stamp=tar.stamp(source),mode=0o600,uid=0,gid=0,mtime_ns=s.st_mtime_ns,
                bytes=len(data),sha256=hashlib.sha256(data).hexdigest())]
            predicted=tar.stream_archive(rows,tar.Sink());target=root/'copy.tar.gz'
            with patch.object(c.shutil,'disk_usage',return_value=types.SimpleNamespace(free=10**12)):
                with target.open('xb') as stream:
                    written=tar.stream_archive(rows,c.Sink(stream,root,c.policy({'storage_profile':'copy_only_512MiB'})))
            self.assertEqual(predicted,written);self.assertEqual(written,target.stat().st_size)
            self.assertEqual(tar.verify_archive(target,rows)['regular'],1)
            self.assertEqual(source.read_bytes(),data)


if __name__=='__main__':unittest.main()
