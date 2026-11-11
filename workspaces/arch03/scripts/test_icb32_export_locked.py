"""Ownership and still-running-child checks for the report-only operation."""
import tempfile
from pathlib import Path
import unittest
from unittest.mock import Mock
from icb32_export_locked import release_own_lock, save


class LockTests(unittest.TestCase):
    def test_foreign_owner_and_live_child_are_never_released(self):
        with tempfile.TemporaryDirectory() as directory:
            lock=Path(directory)/'lock';lock.mkdir()
            owner=dict(pid=1,host='host',bundle='bundle',session='report')
            foreign=dict(owner,pid=2);save(lock/'owner.json',foreign)
            self.assertFalse(release_own_lock(lock,owner,None))
            self.assertTrue((lock/'owner.json').exists())
            save(lock/'owner.json',owner)
            self.assertFalse(release_own_lock(lock,owner,Mock(poll=lambda:None)))
            self.assertTrue(lock.is_dir())
            self.assertTrue(release_own_lock(lock,owner,Mock(poll=lambda:0)))
            self.assertFalse(lock.exists())

    def test_unexpected_lock_content_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            lock=Path(directory)/'lock';lock.mkdir()
            owner=dict(pid=1,host='host',bundle='bundle',session='report')
            save(lock/'owner.json',owner);(lock/'unexpected').write_text('keep')
            self.assertFalse(release_own_lock(lock,owner,None))
            self.assertTrue((lock/'unexpected').exists())
            self.assertTrue((lock/'owner.json').exists())


if __name__=='__main__':
    unittest.main()
