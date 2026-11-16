import copy
import unittest
from pathlib import Path
from c80_space_retry_contract import validate


class RetryContract(unittest.TestCase):
    def setUp(self):
        self.lock=Path('/shared/.arch02_team_lock')
        error="[Errno 28] No space left on device: '"+str(self.lock)+"'"
        self.f=dict(pid=314678,status='failed',error=error,finished='done',
            source_sha256='62c6114e559b0dac3686e3c9e7d039e200a052735b6fd43e8afa9f787e79181b')
        self.p=dict(pid=314678,status='failed',error=error,finished='done',completed=[],
            schema='c80-precision-only-recovery-v1')
        self.e=dict(pid=4047,status='failed_preserved',finished='done',
            source_sha256='01547cb992b2f8ca716a132baa09c2ac1f1eab52eeb4afb88a468f8e65491656')
    def check(self,alive=lambda pid:False):
        return validate(self.f,self.p,self.e,alive,self.lock)
    def test_exact_zero_work(self):
        self.assertFalse(self.check()['hardware_rerun'])
    def test_reject_other_errors(self):
        self.p['error']='invalid data'
        with self.assertRaises(ValueError):self.check()
    def test_reject_any_dispatched_work(self):
        for field,value in [('completed',[{'stage':'precision'}]),('stage','precision'),('current_run','/work')]:
            with self.subTest(field=field):
                old=copy.deepcopy(self.p);self.p[field]=value
                with self.assertRaises(ValueError):self.check()
                self.p=old
    def test_reject_live_old_owner(self):
        for pid in (279630,314678,4047):
            with self.subTest(pid=pid),self.assertRaises(ValueError):self.check(lambda p:p==pid)
    def test_reject_changed_export(self):
        self.e['source_sha256']='0'*64
        with self.assertRaises(ValueError):self.check()


if __name__=='__main__':unittest.main()
