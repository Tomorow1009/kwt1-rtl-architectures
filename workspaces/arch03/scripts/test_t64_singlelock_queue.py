"""Coordinator stage isolation, lock persistence and failure with real child."""
from contextlib import ExitStack
import errno
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

import n1_process as process
import t64_singlelock_queue as queue


class SingleLockTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve();self.bundle=self.root/'bundle'
        self.owner=self.bundle/'runs/queue';self.owner.mkdir(parents=True)
        self.lock=self.root/'lock'
        self.common=types.SimpleNamespace(ROOT=self.bundle,LOCK=None,ACTIVE_CHILD=None)
        self.ledger=process.ProcessLedger(self.common,self.lock,self.owner)
        self.ledger.acquire();self.ledger.initialize()
        self.owner_bytes=(self.lock/'owner.json').read_bytes()
        self.state=dict(completed=[],status='running',child_pid=None)
        self.stack=ExitStack();self.addCleanup(self.stack.close)
        for target,name,value in ((queue.common,'ROOT',self.bundle),(queue.common,'inputs',lambda:{}),
            (queue.paths,'allowed_run',lambda *a:None),(queue.paths,'receipt',lambda c:{}),
            (queue.paths,'recheck',lambda c:None),
            (queue.shutil,'disk_usage',lambda p:types.SimpleNamespace(free=100*1024**3))):
            self.stack.enter_context(patch.object(target,name,value))

    def fake_dispatch(self,name,cfg,run,request,refs,call):
        text=call([sys.executable,'-B','-c',"print('fixture result')"],run,'fixture.log')
        return dict(fixture_only=True,text=text)

    def test_two_stages_share_original_lock_and_retain_separate_receipts(self):
        with patch.object(queue,'dispatch',self.fake_dispatch),patch.object(process,'write_initial_owner',
                side_effect=OSError(errno.ENOSPC,'shared full')):
            for name in ('batch20','contention'):
                ref=queue.run_stage(name,name,{},self.owner,self.state,self.ledger,{}, {})
                self.assertEqual(ref,queue.completed(ref['run'],'t64_'+name))
                self.assertEqual((self.lock/'owner.json').read_bytes(),self.owner_bytes)
        self.assertEqual(len(self.state['completed']),1)
        self.assertIn('batch_reference',self.state)
        self.assertEqual(len(list(self.ledger.ledger.glob('child_*.json'))),2)
        self.ledger.release();self.assertFalse(self.lock.exists())

    def test_failed_stage_has_no_success_receipt_and_child_is_reaped(self):
        def fail(*args):
            self.fake_dispatch(*args);raise ValueError('fixture verification failure')
        with patch.object(queue,'dispatch',fail):
            with self.assertRaisesRegex(ValueError,'verification failure'):
                queue.run_stage('batch20','batch20',{},self.owner,self.state,self.ledger,{}, {})
        stage=self.bundle/'runs/queue_batch20'
        record=json.loads((stage/'state.json').read_text())['stages']['t64_batch20']
        self.assertEqual(record['status'],'failed');self.assertNotIn('summary_sha256',record)
        self.assertFalse((stage/'t64_batch20/summary.json').exists())
        self.assertFalse(self.state['completed']);self.assertNotIn('batch_reference',self.state)
        self.assertIsNone(self.common.ACTIVE_CHILD);self.ledger.release()

    def test_preexisting_stage_is_preserved_without_dispatch(self):
        stage=self.bundle/'runs/queue_synth';stage.mkdir();(stage/'evidence').write_text('keep')
        with patch.object(queue,'dispatch') as dispatch:
            with self.assertRaisesRegex(ValueError,'Preserve existing'):
                queue.run_stage('synth','synth',{},self.owner,self.state,self.ledger,{}, {})
            dispatch.assert_not_called()
        self.assertEqual((stage/'evidence').read_text(),'keep');self.ledger.release()

    def test_low_space_prevents_child_and_preserves_lock(self):
        with patch.object(queue.shutil,'disk_usage',lambda p:types.SimpleNamespace(free=1)),\
             patch.object(queue,'dispatch') as dispatch:
            with self.assertRaisesRegex(ValueError,'Insufficient stage space'):
                queue.run_stage('synth','synth',{},self.owner,self.state,self.ledger,{}, {})
            dispatch.assert_not_called()
        self.assertEqual((self.lock/'owner.json').read_bytes(),self.owner_bytes)
        self.ledger.release()


if __name__=='__main__':unittest.main()
