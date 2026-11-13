import os
from pathlib import Path
import tempfile
import unittest
import t80_archive_runtime as copy


class CopyOnlyArchive(unittest.TestCase):
    def test_full_readback_and_changed_source_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            parent=Path(temp).resolve();root=parent/'runtime';root.mkdir()
            (root/'empty').mkdir();data=root/'result.bin';data.write_bytes(bytes(range(256))*20)
            rows=copy.inventory(root,root.stat().st_uid)
            out=parent/'backup.tar.gz'
            with out.open('wb') as stream:
                copy.tar.stream_archive(rows,copy.tar.Sink(stream,parent))
            counts=copy.tar.verify_archive(out,rows)
            self.assertEqual(counts,dict(regular=1,directory=2,symlink=0))
            self.assertEqual(copy.inventory(root,root.stat().st_uid),rows)
            data.write_bytes(b'changed')
            with self.assertRaises(ValueError):copy.tar.stream_archive(rows,copy.tar.Sink())
            self.assertEqual(data.read_bytes(),b'changed')


if __name__=='__main__':unittest.main()
