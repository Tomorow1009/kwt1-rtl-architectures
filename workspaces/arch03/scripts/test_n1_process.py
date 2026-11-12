"""Small real subprocesses plus injected storage faults; no EDA or shared server."""
import errno
from contextlib import ExitStack
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

import n1_process as process
import n1_server as server


class N1ProcessTests(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory();self.addCleanup(self.temporary.cleanup)
        self.root=Path(self.temporary.name).resolve();self.bundle=self.root/'bundle';self.bundle.mkdir()
        self.shared=self.root/'shared';self.shared.mkdir();self.lock=self.shared/'.arch02_team_lock'
        self.session=self.bundle/'runs/session';self.run=self.session/'n1_batch'
        self.common=types.SimpleNamespace(ROOT=self.bundle,LOCK=None,ACTIVE_CHILD=None)
        self.manager=process.ProcessLedger(self.common,self.lock,self.session)
        self.children=[];self.real_popen=subprocess.Popen

    def ready(self):
        self.manager.acquire();self.run.mkdir(parents=True);self.manager.initialize()
        self.owner_before=(self.lock/'owner.json').read_bytes()

    def command(self,code=None):
        return [sys.executable,'-B','-c',code or
            "import pathlib,time; time.sleep(0.07); pathlib.Path('child_done').write_text('done'); print('child complete')"]

    def launch(self,*args,**kwargs):
        child=self.real_popen(*args,**kwargs);self.children.append(child);return child

    def no_child_left(self):
        self.assertIsNone(self.common.ACTIVE_CHILD);self.assertIsNone(self.manager.active)
        self.assertTrue(all(child.poll() is not None for child in self.children))

    def first_record(self):return json.loads((self.manager.ledger/'child_000001.json').read_text())

    def test_normal_sequence_uses_private_records_and_never_rewrites_shared_owner(self):
        self.ready()
        with patch.object(process,'write_initial_owner',side_effect=OSError(errno.ENOSPC,'shared full')):
            with patch.object(process.subprocess,'Popen',side_effect=self.launch):
                for index in range(3):
                    text=self.manager.call(self.command("print('case %d')"%index),self.run,'case%d.log'%index)
                    self.assertIn('case %d'%index,text)
                    self.assertEqual((self.lock/'owner.json').read_bytes(),self.owner_before)
        self.assertEqual(sorted(p.name for p in self.lock.iterdir()),['owner.json'])
        owner=json.loads(self.owner_before);self.assertEqual(owner['child_ledger'],str(self.manager.ledger))
        records=[json.loads(p.read_text()) for p in sorted(self.manager.ledger.glob('child_*.json'))]
        self.assertEqual([v['sequence'] for v in records],[1,2,3])
        self.assertEqual([v['pid'] for v in records],[child.pid for child in self.children])
        self.assertTrue(all(v['call_status']=='passed' and v['wait_completed'] for v in records))
        self.no_child_left();self.manager.release();self.assertFalse(self.lock.exists())

    def test_initial_owner_enospc_before_file_only_cleans_proven_empty_new_lock(self):
        with patch.object(process,'write_initial_owner',side_effect=OSError(errno.ENOSPC,'initial owner full')):
            with self.assertRaises(OSError):self.manager.acquire()
        self.assertFalse(self.lock.exists());self.no_child_left();self.assertIsNone(self.common.LOCK)

    def test_initial_partial_owner_enospc_preserves_lock_for_manual_recovery(self):
        def partial(path,raw):
            Path(path).write_bytes(raw[:12]);raise OSError(errno.ENOSPC,'partial owner')
        with patch.object(process,'write_initial_owner',side_effect=partial):
            with self.assertRaises(OSError):self.manager.acquire()
        self.assertTrue(self.lock.is_dir());self.assertEqual((self.lock/'owner.json').read_bytes(),self.manager.owner_raw[:12])
        self.assertFalse(self.manager.acquired);self.no_child_left()

    def test_existing_lock_and_unknown_content_are_never_cleaned(self):
        self.lock.mkdir();(self.lock/'owner.json').write_text('other owner')
        with self.assertRaises(FileExistsError):self.manager.acquire()
        self.assertEqual((self.lock/'owner.json').read_text(),'other owner')

    def test_initial_failure_with_new_unknown_member_is_preserved(self):
        def foreign(path,raw):
            (Path(path).parent/'unexpected').write_text('preserve');raise OSError(errno.ENOSPC,'full')
        with patch.object(process,'write_initial_owner',side_effect=foreign):
            with self.assertRaises(OSError):self.manager.acquire()
        self.assertEqual((self.lock/'unexpected').read_text(),'preserve')

    def test_private_intent_enospc_prevents_popen(self):
        self.ready()
        with patch.object(process,'atomic_save',side_effect=OSError(errno.ENOSPC,'private full')):
            with patch.object(process.subprocess,'Popen') as spawn:
                with self.assertRaises(OSError):self.manager.call(self.command(),self.run,'run.log')
                spawn.assert_not_called()
        self.no_child_left();self.manager.release()

    def test_private_pid_record_enospc_waits_for_real_child_before_raising(self):
        self.ready();save=process.atomic_save;observed=[]
        def fail_running(path,value):
            if value.get('status')=='running':
                observed.append((self.common.ACTIVE_CHILD is self.children[-1],self.lock.exists()))
                raise OSError(errno.ENOSPC,'private pid record full')
            return save(path,value)
        with patch.object(process.subprocess,'Popen',side_effect=self.launch),patch.object(process,'atomic_save',side_effect=fail_running):
            with self.assertRaisesRegex(OSError,'private pid record full'):
                self.manager.call(self.command(),self.run,'run.log')
        self.assertEqual(observed,[(True,True)]);self.assertEqual((self.run/'child_done').read_text(),'done')
        self.assertTrue(self.first_record()['wait_completed']);self.assertEqual(self.first_record()['call_status'],'failed')
        self.no_child_left();self.assertTrue(self.lock.exists());self.manager.release()

    def test_persistent_private_failure_after_spawn_still_drains_child(self):
        self.ready();save=process.atomic_save
        def fail_after_prepared(path,value):
            if value.get('status') in ('running','exited'):raise OSError(errno.ENOSPC,'private permanently full')
            return save(path,value)
        with patch.object(process.subprocess,'Popen',side_effect=self.launch),patch.object(process,'atomic_save',side_effect=fail_after_prepared):
            with self.assertRaisesRegex(RuntimeError,'private permanently full'):
                self.manager.call(self.command(),self.run,'run.log')
        self.assertTrue((self.run/'child_done').exists());self.assertEqual(self.first_record()['status'],'prepared')
        self.no_child_left();self.manager.release()

    def test_popen_failure_records_no_child_and_keeps_original_lock(self):
        self.ready()
        with patch.object(process.subprocess,'Popen',side_effect=OSError(errno.ENOENT,'missing executable')):
            with self.assertRaises(OSError):self.manager.call(['missing-fixture'],self.run,'run.log')
        row=self.first_record();self.assertEqual(row['status'],'spawn_failed');self.assertIsNone(row['pid'])
        self.no_child_left();self.assertEqual((self.lock/'owner.json').read_bytes(),self.owner_before);self.manager.release()

    def test_failed_child_and_fatal_log_are_not_success(self):
        self.ready()
        with patch.object(process.subprocess,'Popen',side_effect=self.launch):
            with self.assertRaisesRegex(RuntimeError,'exit=7'):
                self.manager.call(self.command('import sys; sys.exit(7)'),self.run,'bad_exit.log')
            with self.assertRaisesRegex(RuntimeError,'exit=0'):
                self.manager.call(self.command("print('Error: fixture tool failure')"),self.run,'bad_text.log')
        self.no_child_left();self.assertEqual(self.first_record()['returncode'],7);self.manager.release()

    def test_owner_changed_before_spawn_prevents_launch_and_cleanup(self):
        self.ready();changed=json.loads(self.owner_before);changed['token']='another-owner'
        (self.lock/'owner.json').write_text(json.dumps(changed))
        with patch.object(process.subprocess,'Popen') as spawn:
            with self.assertRaisesRegex(ValueError,'owner identity changed'):self.manager.call(self.command(),self.run,'run.log')
            spawn.assert_not_called()
        with self.assertRaisesRegex(ValueError,'owner identity changed'):self.manager.release()
        self.assertEqual(json.loads((self.lock/'owner.json').read_text()),changed)

    def test_owner_changed_after_popen_is_waited_and_foreign_lock_preserved(self):
        self.ready();save=process.atomic_save
        def change_owner(path,value):
            answer=save(path,value)
            if value.get('status')=='running':(self.lock/'owner.json').write_text('{}')
            return answer
        with patch.object(process.subprocess,'Popen',side_effect=self.launch),patch.object(process,'atomic_save',side_effect=change_owner):
            with self.assertRaisesRegex(ValueError,'owner identity changed'):
                self.manager.call(self.command(),self.run,'run.log')
        self.assertTrue((self.run/'child_done').exists());self.no_child_left()
        with self.assertRaisesRegex(ValueError,'owner identity changed'):self.manager.release()
        self.assertEqual((self.lock/'owner.json').read_text(),'{}')

    def test_same_owner_bytes_in_replaced_lock_do_not_prove_ownership(self):
        self.ready();old=self.shared/'original_fixture_lock';self.lock.rename(old);self.lock.mkdir()
        (self.lock/'owner.json').write_bytes(self.owner_before)
        with self.assertRaisesRegex(ValueError,'directory identity changed'):self.manager.release()
        self.assertTrue((old/'owner.json').exists());self.assertEqual((self.lock/'owner.json').read_bytes(),self.owner_before)

    def test_wait_interruption_keeps_active_child_and_waits_again(self):
        self.ready();seen=[]
        def launch(*args,**kwargs):
            child=self.launch(*args,**kwargs);wait=child.wait;first=[True]
            def interrupted(*a,**k):
                seen.append((self.common.ACTIVE_CHILD is child,self.lock.exists()))
                if first[0]:first[0]=False;raise KeyboardInterrupt('fixture cancel while waiting')
                return wait(*a,**k)
            child.wait=interrupted;return child
        with patch.object(process.subprocess,'Popen',side_effect=launch):
            with self.assertRaises(KeyboardInterrupt):self.manager.call(self.command(),self.run,'run.log')
        self.assertTrue(all(active and locked for active,locked in seen))
        self.assertTrue((self.run/'child_done').exists());self.no_child_left();self.manager.release()

    def test_system_exit_after_spawn_is_delayed_until_child_done(self):
        self.ready();save=process.atomic_save
        def stop(path,value):
            if value.get('status')=='running':raise SystemExit('fixture stop')
            return save(path,value)
        with patch.object(process.subprocess,'Popen',side_effect=self.launch),patch.object(process,'atomic_save',side_effect=stop):
            with self.assertRaises(SystemExit):self.manager.call(self.command(),self.run,'run.log')
        self.assertTrue((self.run/'child_done').exists());self.no_child_left();self.manager.release()

    def test_log_close_failure_is_recorded_after_child_is_reaped(self):
        self.ready();original_open=Path.open
        class FailingClose:
            def __init__(self,stream):self.stream=stream
            def fileno(self):return self.stream.fileno()
            def close(self):
                self.stream.close();raise OSError(errno.ENOSPC,'fixture log close failed')
        def opening(path,*args,**kwargs):
            stream=original_open(path,*args,**kwargs)
            return FailingClose(stream) if path==self.run/'run.log' and args==('x',) else stream
        with patch.object(Path,'open',opening),patch.object(process.subprocess,'Popen',side_effect=self.launch):
            with self.assertRaisesRegex(OSError,'log close failed'):self.manager.call(self.command(),self.run,'run.log')
        self.assertTrue((self.run/'child_done').exists());self.no_child_left()
        row=self.first_record();self.assertTrue(row['wait_completed']);self.assertEqual(row['call_status'],'failed')
        self.assertIn('log close failed',row['errors'][0]['message']);self.manager.release()

    def test_unknown_lock_member_blocks_release(self):
        self.ready();(self.lock/'unexpected').write_text('preserve')
        with self.assertRaisesRegex(ValueError,'Unexpected shared lock members'):self.manager.release()
        self.assertTrue((self.lock/'owner.json').exists())

    def test_n1_server_uses_only_new_process_calls_and_pins_dependency(self):
        source=Path(__file__).with_name('n1_server.py').read_text()
        self.assertNotIn('common.call',source)
        self.assertIn("packaged['files'].get(process_relative)",source)
        self.assertIn('processes.initialize()',source);self.assertIn('processes.release()',source)

    def main_fixture(self,verify,include_dependency=True):
        import n1_batch
        path=self.bundle/'workspaces/arch03/scripts/n1_process.py';path.parent.mkdir(parents=True)
        path.write_bytes(Path(process.__file__).read_bytes())
        manifest={'files':{'workspaces/arch03/scripts/n1_process.py':server.common.sha(path)} if include_dependency else {}}
        config=self.bundle/'handoff/team/server_config.json';config.parent.mkdir(parents=True)
        cfg={'server_root':str(self.shared)};config.write_text(json.dumps(cfg))
        stack=ExitStack()
        for target,name,value in ((server.common,'ROOT',self.bundle),(server.common,'LOCK',None),
            (server.common,'ACTIVE_CHILD',None),(server.common,'inputs',lambda:manifest),
            (process,'__file__',str(path)),(server.n1_paths,'configure',lambda *a:cfg),
            (server.n1_paths,'recheck',lambda cfg:None),(n1_batch,'verify',verify),
            (server.shutil,'disk_usage',lambda path:types.SimpleNamespace(free=100*1024**3)),
            (sys,'argv',['n1_server.py','batch','--session','session','--dataset',str(self.root/'fixture_data')])):
            stack.enter_context(patch.object(target,name,value))
        return stack

    def test_server_main_normal_stage_has_real_child_ledger_and_releases_lock(self):
        seen=[]
        def verify(cfg,run,platform,dataset,call):
            seen.append(json.loads((self.lock/'owner.json').read_text()))
            return {'status':'fixture_passed','text':call(self.command(),run,'run.log')}
        with self.main_fixture(verify),patch.object(process.subprocess,'Popen',side_effect=self.launch):
            server.main();self.assertIsNone(server.common.ACTIVE_CHILD)
        state=json.loads((self.session/'state.json').read_text())
        self.assertEqual(state['stages']['n1_batch']['status'],'passed');self.assertFalse(self.lock.exists())
        self.assertEqual(seen[0]['child_ledger'],str(self.session/'process_ledger'))
        row=json.loads((self.session/'process_ledger/child_000001.json').read_text())
        self.assertTrue(row['wait_completed']);self.assertEqual(row['call_status'],'passed')
        self.assertTrue(all(child.poll() is not None for child in self.children))

    def test_server_main_record_failure_marks_failed_after_wait_not_false_pass(self):
        def verify(cfg,run,platform,dataset,call):
            call(self.command(),run,'run.log');raise AssertionError('must not continue after ledger failure')
        save=process.atomic_save
        def failing(path,value):
            if value.get('status')=='running':raise OSError(errno.ENOSPC,'integration private full')
            return save(path,value)
        with self.main_fixture(verify),patch.object(process.subprocess,'Popen',side_effect=self.launch),patch.object(process,'atomic_save',side_effect=failing):
            with self.assertRaisesRegex(OSError,'integration private full'):server.main()
            self.assertIsNone(server.common.ACTIVE_CHILD)
        state=json.loads((self.session/'state.json').read_text())
        self.assertEqual(state['stages']['n1_batch']['status'],'failed');self.assertNotIn('summary_sha256',state['stages']['n1_batch'])
        self.assertTrue((self.run/'child_done').exists());self.assertFalse(self.lock.exists())
        self.assertTrue(all(child.poll() is not None for child in self.children))

    def test_server_main_missing_process_manifest_entry_stops_before_lock(self):
        with self.main_fixture(lambda *a:None,include_dependency=False):
            with self.assertRaisesRegex(ValueError,'ledger dependency is absent'):server.main()
        self.assertFalse(self.lock.exists());self.assertFalse(self.session.exists())


if __name__=='__main__':unittest.main()
