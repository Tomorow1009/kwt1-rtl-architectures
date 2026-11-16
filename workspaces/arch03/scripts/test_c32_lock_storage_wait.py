"""Only transient untouched original-lock storage failure may be retried."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest

p=Path(__file__).resolve().parents[3]/'handoff/team/evidence/C32_FINISH_LOCK_RECOVERY04_20261117.py'
s=importlib.util.spec_from_file_location('c32_lock_recovery',str(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)


class LockWait(unittest.TestCase):
    def test_enospc_then_acquire_without_restarting_work(self):
        calls=[];sleeps=[];ledger=SimpleNamespace(lock=SimpleNamespace(exists=lambda:False))
        def acquire():
            calls.append(1)
            if len(calls)==1:raise OSError(28,'full')
            return 'owned'
        self.assertEqual(m.acquire_wait(ledger,acquire,sleeps.append),'owned')
        self.assertEqual((len(calls),sleeps),(2,[5]))

    def test_partial_created_lock_and_other_errors_are_not_retried(self):
        for code,partial in [(28,True),(13,False)]:
            state={'present':False};calls=[]
            ledger=SimpleNamespace(lock=SimpleNamespace(exists=lambda:state['present']))
            def acquire():
                state['present']=partial;calls.append(1);raise OSError(code,'stop')
            with self.assertRaises(OSError):m.acquire_wait(ledger,acquire,lambda n:self.fail('must not retry'))
            self.assertEqual(len(calls),1)

    def test_existing_team_lock_waits_without_mutating_it(self):
        state={'present':True};calls=[]
        ledger=SimpleNamespace(lock=SimpleNamespace(exists=lambda:state['present']))
        def sleep(n):self.assertEqual(calls,[]);state['present']=False
        self.assertEqual(m.acquire_wait(ledger,lambda:calls.append('acquired'),sleep),None)
        self.assertEqual(calls,['acquired'])


if __name__=='__main__':unittest.main()
