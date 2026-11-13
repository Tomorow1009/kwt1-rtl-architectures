"""Small archive fixtures only; no production source, Linux process or EDA run."""
import copy
import errno
import json
import os
from pathlib import Path
import stat
import tarfile
import types
import unittest
from unittest.mock import patch

import n1_archive_runtime as archive
import test_n1_paths as runtime_fixture


class N1ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.f=runtime_fixture.RuntimePathTests();self.f.setUp();self.addCleanup(self.f.doCleanups)
        self.backups=self.f.shared/'backups';self.backups.mkdir()
        self.target=self.backups/'n1-runtime-20261113_0300'
        for bundle in (self.f.ops,self.f.base):
            run=bundle/'runs/session/n1_synth'
            (run/'summary.json').write_text(json.dumps({'fixture':True}))
            (run.parent/'state.json').write_text(json.dumps(dict(schema='arch03-n1-server-state-v1',
                stages={'n1_synth':dict(status='passed',finished='fixture_finished',
                    summary_sha256=archive.paths.digest(run/'summary.json'))})))
            (run/'mapped.v').write_bytes(b'fixture mapped data\0'*100)
            (run/'derived.db').write_bytes(b'fixture generated library\0'*100)
            (run/'empty_dir').mkdir()
        helper=self.f.ops/'workspaces/arch03/scripts/n1_paths.py'
        helper.write_bytes(Path(archive.paths.__file__).read_bytes())
        manifest=json.loads((self.f.ops/'manifest.json').read_text())
        manifest['files']['workspaces/arch03/scripts/n1_paths.py']=archive.paths.digest(helper)
        (self.f.ops/'manifest.json').write_text(json.dumps(manifest))
        self.request=dict(ops_bundle=str(self.f.ops),ops_manifest_sha256=archive.paths.digest(self.f.ops/'manifest.json'),
            runtime_root=str(self.f.private),evidence=[[str(self.f.base),archive.paths.digest(self.f.base/'manifest.json')]],
            destination=str(self.target))
        self.real_no_open=archive.no_open_users
        for name,value in (('BACKUPS',self.backups),('sync_dir',lambda path:None),
            ('no_open_users',lambda roots:dict(owned_processes_inspected=0,open_runtime_uses=0,fixture=True))):
            p=patch.object(archive,name,value);p.start();self.addCleanup(p.stop)
        p=patch.object(archive,'destination',return_value=self.target);p.start();self.addCleanup(p.stop)
        self.destination_patch=p
        p=patch.object(archive.shutil,'disk_usage',return_value=types.SimpleNamespace(free=100*1024**3))
        p.start();self.addCleanup(p.stop)

    def snapshot(self):
        return {str(path):archive.paths.digest(path) for bundle in (self.f.ops,self.f.base)
                for path in bundle.rglob('*') if path.is_file()}

    def assert_lock_released(self):self.assertFalse((self.f.shared/'.arch02_team_lock').exists())

    def auxiliary(self,name='b0_inventory01',status='inventory_rejected'):
        run=self.f.ops/'runs'/name;run.mkdir()
        value=dict(schema='b0-read-only-power-review-inventory-v1',status=status,system_power_verified=False)
        if status=='inventory_rejected':value['error']='fixture input budget rejection'
        else:value.update(no_eda_or_simulation_started=True,no_files_written=True,no_large_wave_read=True)
        receipt=run/'inventory.json';receipt.write_text(json.dumps(value))
        return dict(run=str(run),receipt_sha256=archive.paths.digest(receipt))

    def test_explicit_readonly_auxiliary_receipts_roundtrip_without_stage_acceptance(self):
        bindings=[self.auxiliary(),self.auxiliary('b0_inventory02','read_only_inventory_collected_review_required')]
        self.request['auxiliary_runs']=bindings;before=self.snapshot()
        archive.archive(self.request)
        self.assertEqual(before,self.snapshot())
        manifest=json.loads((self.target/'manifest.json').read_text())
        auxiliary=[row for row in manifest['terminal_states'] if row.get('kind')=='auxiliary_read_only_inventory']
        self.assertEqual(len(auxiliary),2)
        self.assertEqual({row['receipt_sha256'] for row in auxiliary},{row['receipt_sha256'] for row in bindings})
        self.assertTrue(all(row['acceptance_not_inferred_from_archive'] and not row['system_power_verified'] for row in auxiliary))
        names={row['member'] for row in manifest['files']}
        for binding in bindings:
            self.assertIn(self.f.ops.name+'/runs/'+Path(binding['run']).name+'/inventory.json',names)
        self.assertFalse(manifest['archive_implies_acceptance']);self.assert_lock_released()

    def test_auxiliary_missing_binding_wrong_hash_and_unregistered_path_stop(self):
        binding=self.auxiliary()
        with self.assertRaisesRegex(ValueError,'lacks terminal state'):archive.archive(self.request)
        self.request['auxiliary_runs']=[dict(binding,receipt_sha256='0'*64)]
        with self.assertRaisesRegex(ValueError,'receipt SHA256 differs'):archive.archive(self.request)
        self.request['auxiliary_runs']=[dict(binding,run=str(self.f.root/'runs/b0_inventory01'))]
        with self.assertRaisesRegex(ValueError,'registered bundle'):archive.archive(self.request)
        self.assertFalse(self.target.exists());self.assert_lock_released()

    def test_auxiliary_schema_status_and_readonly_flags_are_strict(self):
        binding=self.auxiliary('b0_inventory02','read_only_inventory_collected_review_required')
        receipt=Path(binding['run'])/'inventory.json';valid=json.loads(receipt.read_text())
        for change,expected in (({'schema':'unknown'},'schema or terminal status'),
            ({'status':'running'},'schema or terminal status'),({'status':'passed'},'schema or terminal status'),
            ({'system_power_verified':True},'schema or terminal status'),
            ({'no_files_written':False},'read-only evidence'),({'no_eda_or_simulation_started':1},'read-only evidence')):
            with self.subTest(change=change):
                receipt.write_text(json.dumps(dict(valid,**change)))
                bindings=[dict(binding,receipt_sha256=archive.paths.digest(receipt))]
                with self.assertRaisesRegex(ValueError,expected):archive.terminal_states([self.f.ops,self.f.base],bindings)
        receipt.write_text(json.dumps(dict(schema=valid['schema'],status='inventory_rejected',system_power_verified=False)))
        with self.assertRaisesRegex(ValueError,'lacks its error'):
            archive.terminal_states([self.f.ops],[dict(binding,receipt_sha256=archive.paths.digest(receipt))])

    def test_auxiliary_duplicate_extra_fields_and_n1_state_override_rejected(self):
        binding=self.auxiliary();bundles=[self.f.ops,self.f.base]
        with self.assertRaisesRegex(ValueError,'Duplicate'):archive.terminal_states(bundles,[binding,binding])
        with self.assertRaisesRegex(ValueError,'only run and receipt_sha256'):
            archive.terminal_states(bundles,[dict(binding,allow_unknown=True)])
        override=dict(binding,run=str(self.f.base/'runs/session'))
        with self.assertRaisesRegex(ValueError,'cannot override an N1 state'):archive.terminal_states(bundles,[override])
        with self.assertRaisesRegex(ValueError,'must be a list'):archive.terminal_states(bundles,{'run':binding})

    def test_auxiliary_receipt_mutation_during_preflight_retains_source(self):
        binding=self.auxiliary();self.request['auxiliary_runs']=[binding]
        original=archive.stream_archive;receipt=Path(binding['run'])/'inventory.json'
        def change(rows,sink):
            result=original(rows,sink)
            value=json.loads(receipt.read_text());value['error']='changed fixture reason'
            receipt.write_text(json.dumps(value));return result
        with patch.object(archive,'stream_archive',side_effect=change):
            with self.assertRaisesRegex(ValueError,'changed during archive size preflight'):archive.archive(self.request)
        self.assertTrue(receipt.is_file());self.assertFalse(self.target.exists());self.assert_lock_released()

    def test_complete_roundtrip_preserves_all_files_directories_and_source(self):
        before=self.snapshot();result=archive.archive(self.request)
        self.assertEqual(result['status'],'verified');self.assertEqual(before,self.snapshot())
        self.assertFalse(result['source_deleted']);self.assertFalse(result['source_temp_cleanup_authorized'])
        self.assertFalse(result['relocated_verifier_verified']);self.assertFalse(result['clean_directory_reproduction_verified'])
        manifest=json.loads((self.target/'manifest.json').read_text())
        names={row['member'] for row in manifest['files']}
        self.assertIn(self.f.ops.name+'/runs/session/n1_synth/derived.db',names)
        self.assertIn(self.f.ops.name+'/runs/session/n1_synth/empty_dir',names)
        self.assertEqual(result['archive_sha256'],archive.paths.digest(self.target/'runtime-evidence.tar.gz'))
        mapping=json.loads((self.target/'recovery_index.json').read_text())
        self.assertFalse(mapping['relocated_verifier_verified']);self.assertTrue(mapping['source_receipts_unchanged'])
        self.assertEqual(result['member_counts']['regular'],len(before))
        self.assert_lock_released()

    def queue_fixture(self,completed=13,status='numbers_ready_independent_review_required'):
        session=self.f.ops/'runs/n1_acceptance01';session.mkdir()
        request=dict(schema='arch03-n1-acceptance-continuation-v1',bundle=str(self.f.ops))
        (session/'request.json').write_text(json.dumps(request))
        state=dict(schema='arch03-n1-acceptance-queue-state-v1',status=status,finished='fixture',
            child_pid=None,n2_allowed=False,system_power_verified=False,completed=[],
            request_sha256=archive.paths.digest(session/'request.json'))
        if status=='failed':state['error']='fixture child failure preserved'
        for i in range(completed):
            label,kind,suffix=('precision','n1_precision','_precision') if i==0 else (
                'power%02d'%i,'n1_power','_p%02d'%i)
            run=session.parent/(session.name+suffix)/kind;run.mkdir(parents=True)
            (run/'summary.json').write_text(json.dumps(dict(fixture=label)))
            digest=archive.paths.digest(run/'summary.json')
            (run.parent/'state.json').write_text(json.dumps(dict(schema='arch03-n1-server-state-v1',
                stages={kind:dict(status='passed',finished='fixture',summary_sha256=digest)})))
            state['completed'].append(dict(label=label,stage=kind,reference=dict(run=str(run),sha256=digest)))
        (session/'state.json').write_text(json.dumps(state))
        return session,state

    def test_terminal_observer_queue_roundtrip_does_not_grant_acceptance(self):
        session,state=self.queue_fixture();before=self.snapshot()
        archive.archive(self.request)
        self.assertEqual(before,self.snapshot())
        records=json.loads((self.target/'manifest.json').read_text())['terminal_states']
        queue=[r for r in records if r.get('kind')=='serial_observer_queue'][0]
        self.assertEqual(queue['completed_children'],13)
        self.assertFalse(queue['system_power_verified']);self.assertTrue(queue['acceptance_not_inferred_from_archive'])

    def test_queue_running_incomplete_or_changed_child_cannot_archive(self):
        session,state=self.queue_fixture()
        for changed in (dict(state,status='running'),dict(state,child_pid=123),
                        dict(state,n2_allowed=True),dict(state,completed=state['completed'][:-1]),
                        dict(state,request_sha256='0'*64)):
            with self.subTest(changed=changed['status']),self.assertRaises(ValueError):
                archive.completed_queue(session,changed)
        child=Path(state['completed'][0]['reference']['run'])/'summary.json'
        child.write_text('changed')
        with self.assertRaisesRegex(ValueError,'child identity'):archive.completed_queue(session,state)

    def test_failed_queue_preserves_completed_prefix_and_failure(self):
        session,state=self.queue_fixture(2,'failed')
        result=archive.completed_queue(session,state)
        self.assertEqual(result['status'],'failed');self.assertEqual(result['completed_children'],2)
        self.assertFalse(result['system_power_verified'])

    def test_running_or_unknown_stage_stops_before_destination(self):
        state_path=self.f.base/'runs/session/state.json';state=json.loads(state_path.read_text())
        state['stages']['n1_synth']['status']='running';state_path.write_text(json.dumps(state))
        with self.assertRaisesRegex(ValueError,'has not ended'):archive.archive(self.request)
        self.assertFalse(self.target.exists());self.assert_lock_released()
        state['schema']='unknown';state_path.write_text(json.dumps(state))
        with self.assertRaisesRegex(ValueError,'Unknown runtime session'):archive.archive(self.request)
        self.assertFalse(self.target.exists());self.assert_lock_released()

    def test_failed_terminal_evidence_is_preserved_without_acceptance(self):
        state_path=self.f.base/'runs/session/state.json';state=json.loads(state_path.read_text())
        state['stages']['n1_synth']['status']='failed';state['stages']['n1_synth']['error']='fixture failure'
        state_path.write_text(json.dumps(state));before=state_path.read_bytes()
        archive.archive(self.request)
        manifest=json.loads((self.target/'manifest.json').read_text())
        self.assertIn('failed',{row['status'] for row in manifest['terminal_states']})
        self.assertFalse(manifest['archive_implies_acceptance']);self.assertEqual(state_path.read_bytes(),before)

    def test_existing_lock_and_existing_destination_are_never_replaced(self):
        lock=self.f.shared/'.arch02_team_lock';lock.mkdir();owner=lock/'owner.json';owner.write_text('existing operator')
        with self.assertRaises(FileExistsError):archive.archive(self.request)
        self.assertEqual(owner.read_text(),'existing operator');self.assertFalse(self.target.exists())
        # Explicitly dispose only this synthetic test fixture lock, not tool work.
        owner.unlink();lock.rmdir();self.target.mkdir();(self.target/'original').write_text('keep')
        self.destination_patch.stop()
        with self.assertRaisesRegex(ValueError,'destination exists'):archive.archive(self.request)
        self.assertEqual((self.target/'original').read_text(),'keep')

    def test_active_user_and_missing_terminal_state_are_not_archived(self):
        with patch.object(archive,'no_open_users',side_effect=ValueError('Runtime files are still in use')):
            with self.assertRaisesRegex(ValueError,'still in use'):archive.archive(self.request)
        self.assertFalse(self.target.exists());self.assert_lock_released()
        (self.f.base/'runs/unclassified').mkdir()
        with self.assertRaisesRegex(ValueError,'lacks terminal state'):archive.archive(self.request)
        self.assertFalse(self.target.exists());self.assert_lock_released()

    def test_actual_runs_root_symlink_and_dangling_link_reject_before_iteration(self):
        bundle=self.f.root/'symlink_fixture_bundle';bundle.mkdir()
        target=self.f.root/'external_runs_fixture';target.mkdir()
        runs=bundle/'runs';runs.symlink_to(target,target_is_directory=True)
        self.addCleanup(lambda:runs.unlink() if runs.is_symlink() else None)
        self.assertTrue(runs.is_symlink())
        # The real filesystem symlink is used; no mocked lstat or link metadata.
        for dangling in (False,True):
            with self.subTest(dangling=dangling):
                if dangling:target.rmdir()  # only this newly created empty fixture target
                self.assertEqual(runs.exists(),not dangling)
                with patch.object(Path,'iterdir',side_effect=AssertionError('Must not iterate a linked runs root')):
                    with self.assertRaisesRegex(ValueError,'runs root must be a real directory'):
                        archive.terminal_states([bundle])
        self.assertTrue(runs.is_symlink())

    def test_regular_file_runs_root_rejects_instead_of_being_skipped(self):
        bundle=self.f.root/'file_runs_fixture_bundle';bundle.mkdir()
        runs=bundle/'runs';runs.write_text('preserve fixture file')
        with patch.object(Path,'iterdir',side_effect=AssertionError('Must not iterate a file runs root')):
            with self.assertRaisesRegex(ValueError,'runs root must be a real directory'):
                archive.terminal_states([bundle])
        self.assertEqual(runs.read_text(),'preserve fixture file')

    def test_insufficient_budget_keeps_sources_and_creates_no_archive(self):
        before=self.snapshot()
        with patch.object(archive.shutil,'disk_usage',return_value=types.SimpleNamespace(free=archive.RESERVE)):
            with self.assertRaisesRegex(ValueError,'Insufficient shared archive space'):archive.archive(self.request)
        self.assertEqual(before,self.snapshot());self.assertFalse(self.target.exists());self.assert_lock_released()

    def test_late_space_failure_preserves_partial_and_all_sources(self):
        before=self.snapshot()
        with patch.object(archive.shutil,'disk_usage',side_effect=[types.SimpleNamespace(free=100*1024**3),
                                                               types.SimpleNamespace(free=archive.RESERVE-1)]):
            with self.assertRaisesRegex(ValueError,'reserve reached'):archive.archive(self.request)
        self.assertEqual(before,self.snapshot());self.assertTrue((self.target/'runtime-evidence.tar.gz.partial').exists())
        self.assertFalse((self.target/'runtime-evidence.tar.gz').exists())
        self.assertEqual(json.loads((self.target/'state.json').read_text())['status'],'failed');self.assert_lock_released()

    def test_source_mutation_between_passes_stops_without_false_verified(self):
        original=archive.stream_archive;calls=[];source=self.f.base/'runs/session/n1_synth/mapped.v'
        def change(rows,sink):
            result=original(rows,sink);calls.append(1)
            if len(calls)==1:source.write_bytes(b'changed by test fixture')
            return result
        with patch.object(archive,'stream_archive',side_effect=change):
            with self.assertRaisesRegex(ValueError,'changed during archive size preflight'):archive.archive(self.request)
        self.assertTrue(source.exists());self.assertFalse(self.target.exists());self.assert_lock_released()

    def test_archive_hash_or_member_failure_retains_source_and_partial(self):
        before=self.snapshot()
        with patch.object(archive,'verify_archive',side_effect=ValueError('fixture archive mismatch')):
            with self.assertRaisesRegex(ValueError,'archive mismatch'):archive.archive(self.request)
        self.assertEqual(before,self.snapshot());self.assertTrue((self.target/'runtime-evidence.tar.gz.partial').exists())
        self.assertFalse((self.target/'receipt.json').exists());self.assert_lock_released()
        manifest=json.loads((self.target/'manifest.json').read_text())
        bad=copy.deepcopy(manifest['files']);next(row for row in bad if row['kind']=='regular')['sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'restored SHA'):archive.verify_archive(self.target/'runtime-evidence.tar.gz.partial',bad)

    def test_full_gzip_footer_is_checked_after_tar_end_marker(self):
        archive.archive(self.request)
        manifest=json.loads((self.target/'manifest.json').read_text())
        raw=bytearray((self.target/'runtime-evidence.tar.gz').read_bytes());raw[-1]^=1
        corrupt=self.f.root/'corrupt_footer.gz';corrupt.write_bytes(raw)
        with self.assertRaises((OSError,EOFError,ValueError)):
            archive.verify_archive(corrupt,manifest['files'])

    def test_symlink_is_preserved_without_reading_external_target(self):
        link=self.f.base/'runs/session/n1_synth/vendor_link';link.write_bytes(b'fixture link backing')
        target='/storage1/admin_public_dir/fixture_private_library.db'
        real_lstat=Path.lstat;real_readlink=archive.os.readlink
        def synthetic_lstat(path):
            actual=real_lstat(path)
            if path!=link:return actual
            return types.SimpleNamespace(st_dev=actual.st_dev,st_ino=actual.st_ino,st_size=len(target),
                st_mtime_ns=actual.st_mtime_ns,st_ctime_ns=actual.st_ctime_ns,st_uid=0,st_gid=actual.st_gid,
                st_mode=stat.S_IFLNK|0o777,st_nlink=1)
        def synthetic_readlink(path):return target if Path(path)==link else real_readlink(path)
        with patch.object(Path,'lstat',synthetic_lstat),patch.object(archive.os,'readlink',side_effect=synthetic_readlink):
            result=archive.archive(self.request)
        self.assertEqual(result['member_counts']['symlink'],1)
        manifest=json.loads((self.target/'manifest.json').read_text())
        entry=next(row for row in manifest['files'] if row['kind']=='symlink')
        self.assertEqual(entry['target'],target);self.assertFalse(entry['target_content_archived'])
        self.assertEqual(entry['link_class'],'external_vendor_reference_not_copied')
        with tarfile.open(str(self.target/'runtime-evidence.tar.gz'),'r:gz') as packed:
            self.assertTrue(packed.getmember(entry['member']).issym())
        self.assertEqual(link.read_bytes(),b'fixture link backing')

    def test_shared_destination_boundary_and_separate_device_required(self):
        self.destination_patch.stop()
        same_device=types.SimpleNamespace(stat=lambda:self.backups.stat())
        with self.assertRaisesRegex(ValueError,'not the runtime filesystem'):
            archive.destination(self.target,same_device,0)
        other_device=types.SimpleNamespace(stat=lambda:types.SimpleNamespace(st_dev=self.backups.stat().st_dev+1))
        self.assertEqual(archive.destination(self.target,other_device,0),self.target)
        with self.assertRaisesRegex(ValueError,'fixed shared backups'):
            archive.destination(self.f.root/'arbitrary',other_device,0)

    def test_special_files_fail_instead_of_disappearing(self):
        special=self.f.base/'runs/session/n1_synth/special';special.write_bytes(b'fixture backing')
        original=Path.lstat
        def fake(path):
            value=original(path)
            if path!=special:return value
            return types.SimpleNamespace(st_dev=value.st_dev,st_ino=value.st_ino,st_size=value.st_size,
                st_mtime_ns=value.st_mtime_ns,st_ctime_ns=value.st_ctime_ns,st_uid=0,st_gid=value.st_gid,
                st_mode=stat.S_IFIFO|0o600,st_nlink=1)
        with patch.object(Path,'lstat',fake):
            with self.assertRaisesRegex(ValueError,'Special runtime artifact'):archive.archive(self.request)
        self.assertTrue(special.exists());self.assertFalse(self.target.exists());self.assert_lock_released()

    def test_proc_scan_includes_own_logs_mmaps_and_permission_failures(self):
        # Call the real function despite the full-workflow fixture's mock.
        scan=self.real_no_open
        proc=self.f.root/'proc';process=proc/str(os.getpid());fd=process/'fd';fd.mkdir(parents=True)
        (fd/'1').write_bytes(b'');(process/'maps').write_text('')
        roots=[Path('/tmp/mock_n1')]
        targets={str(process/'cwd'):'/unrelated',str(process/'exe'):'/usr/bin/python3',str(fd/'1'):'/unrelated/log'}
        with patch.object(archive,'PROC_ROOT',proc),patch.object(archive.os,'readlink',side_effect=lambda name:targets[name]):
            self.assertEqual(scan(roots)['open_runtime_uses'],0)
            targets[str(fd/'1')]='/tmp/mock_n1/driver.log'
            with self.assertRaisesRegex(ValueError,'still in use'):scan(roots)
            targets[str(fd/'1')]='/unrelated/log'
            (process/'maps').write_text('7f00-7f01 r-xp 0000 08:01 1 /tmp/mock_n1/simv\n')
            with self.assertRaisesRegex(ValueError,'still in use'):scan(roots)
        with patch.object(archive,'PROC_ROOT',proc),patch.object(archive.os,'readlink',side_effect=PermissionError(errno.EACCES,'denied')):
            with self.assertRaisesRegex(ValueError,'Cannot prove runtime idle'):scan(roots)


if __name__=='__main__':unittest.main()
