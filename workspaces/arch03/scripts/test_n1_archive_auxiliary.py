"""Small real-file archive tests; Linux account/proc/device facts are fixtures."""
import copy
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import tarfile
import types
import unittest
from unittest.mock import patch

import n1_archive_auxiliary as aux
import test_n1_paths as fixtures


class AuxiliaryArchiveTests(unittest.TestCase):
    def setUp(self):
        self.f = fixtures.RuntimePathTests(); self.f.setUp(); self.addCleanup(self.f.doCleanups)
        self.operations = self.f.shared/'operations'; self.operations.mkdir()
        self.f.overrides[self.operations] = {'st_dev': self.f.private.stat().st_dev+1}
        self.source = self.f.private/'b0_control_l01_20261113_0403'; self.source.mkdir()
        (self.source/'summary.json').write_text('{"fixture":"completed review only"}\n')
        (self.source/'selected.bin').write_bytes(bytes(range(256))*30)
        (self.source/'empty').mkdir()
        self.target = self.operations/'n1-aux-archive-20261113_0620-test'
        self.request = dict(schema=aux.REQUEST_SCHEMA,runtime_root=str(self.f.private),destination=str(self.target),
                            entries=[dict(name=self.source.name,tree_sha256=None)])
        for obj,name,value in ((aux,'RUNTIME',self.f.private),(aux,'OPERATIONS',self.operations),
            (aux.base,'sync_dir',lambda p:None),
            (aux.base,'no_open_users',lambda p,**kw:dict(fixture=True,open_runtime_uses=0)),
            (aux.shutil,'disk_usage',lambda p:types.SimpleNamespace(free=100*1024**3))):
            h=patch.object(obj,name,value);h.start();self.addCleanup(h.stop)

    def pinned(self):
        result=aux.process(self.request,'identities')
        value=copy.deepcopy(self.request)
        value['entries'][0]['tree_sha256']=result['tree_sha256'][self.source.name]
        return value

    def snapshot(self):
        return {str(p):p.read_bytes() for p in self.source.rglob('*') if p.is_file()}

    def test_metadata_plan_does_not_hash_source_or_create_files(self):
        before=self.snapshot()
        with patch.object(aux.os,'open',side_effect=AssertionError('plan opened a content descriptor')):
            result=aux.process(self.request,'plan')
        self.assertEqual(result['status'],'bounded_read_only_plan')
        self.assertIsNone(result['tree_sha256']);self.assertIsNone(result['required_bytes'])
        self.assertFalse(self.target.exists());self.assertFalse(aux.lock_path().exists())
        self.assertEqual(before,self.snapshot())

    def test_full_roundtrip_all_members_and_empty_directory_source_retained(self):
        request=self.pinned();before=self.snapshot()
        result=aux.process(request,'archive')
        self.assertEqual(result['status'],'verified');self.assertFalse(result['source_deleted'])
        self.assertFalse(result['hardware_acceptance']);self.assertFalse(result['relocated_verifier_verified'])
        self.assertEqual(before,self.snapshot());self.assertFalse(aux.lock_path().exists())
        with tarfile.open(str(self.target/'auxiliary-evidence.tar.gz'),'r:gz') as archive:
            names=archive.getnames();self.assertIn(self.source.name+'/empty',names)
            for name,content in before.items():
                member=self.source.name+'/'+Path(name).relative_to(self.source).as_posix()
                self.assertEqual(archive.extractfile(member).read(),content)

    def test_plan_and_identity_modes_refuse_existing_shared_lock(self):
        lock=aux.lock_path();lock.mkdir();owner=lock/'owner.json';owner.write_bytes(b'other-owner')
        for mode in ('plan','identities','archive'):
            request=copy.deepcopy(self.request);request['entries'][0]['tree_sha256']='a'*64
            with self.subTest(mode=mode),self.assertRaisesRegex(ValueError,'occupied'):
                aux.process(request,mode)
        self.assertEqual(owner.read_bytes(),b'other-owner');self.assertFalse(self.target.exists())

    def test_unlisted_duplicate_traversal_and_runtime_rejected(self):
        for name in ('../b0_control_l01_20261113_0403','another_user','/tmp/other','b0_control_l01_20261113_0403/child'):
            request=copy.deepcopy(self.request);request['entries'][0]['name']=name
            with self.subTest(name=name),self.assertRaisesRegex(ValueError,'unlisted'):
                aux.process(request,'plan')
        request=copy.deepcopy(self.request);request['entries']*=2
        with self.assertRaisesRegex(ValueError,'duplicate'):aux.process(request,'plan')
        request=copy.deepcopy(self.request);request['runtime_root']=str(self.f.root)
        with self.assertRaisesRegex(ValueError,'exact existing'):aux.process(request,'plan')

    def test_destination_boundary_existing_and_same_filesystem_rejected(self):
        request=copy.deepcopy(self.request);request['destination']=str(self.f.private/'n1-aux-archive-20261113_0620')
        with self.assertRaisesRegex(ValueError,'fixed project'):aux.process(request,'plan')
        self.target.mkdir()
        with self.assertRaisesRegex(ValueError,'already exists'):aux.process(self.request,'plan')
        self.target.rmdir();self.f.overrides[self.operations]={'st_dev':self.f.private.stat().st_dev}
        with self.assertRaisesRegex(ValueError,'durable shared'):aux.process(self.request,'plan')

    def test_other_owner_and_root_mode_refused(self):
        self.f.overrides[self.source/'selected.bin']={'st_uid':99}
        with self.assertRaisesRegex(ValueError,'another owner'):aux.process(self.request,'identities')
        self.f.overrides.pop(self.source/'selected.bin')
        self.f.overrides[self.f.private]={'st_mode':stat.S_IFDIR|0o755}
        with self.assertRaisesRegex(ValueError,'0700'):aux.process(self.request,'plan')

    def test_actual_live_and_dangling_symlink_rejected_without_following(self):
        external=self.f.root/'outside';external.write_bytes(b'private-external-fixture')
        link=self.source/'pointer';os.symlink(str(external),str(link))
        for dangling in (False,True):
            if dangling:external.unlink()
            with self.subTest(dangling=dangling),self.assertRaisesRegex(ValueError,'symlink'):
                aux.process(self.request,'identities')
        self.assertFalse(self.target.exists());self.assertTrue(link.is_symlink())

    def test_bounded_entries_bytes_depth_and_time(self):
        for name,value,pattern in (('MAX_ENTRIES',1,'entry limit'),('MAX_BYTES',1,'total byte'),
                                   ('MAX_FILE',1,'large auxiliary'),('MAX_DEPTH',1,'depth'),('PLAN_SECONDS',0,'time')):
            with self.subTest(name=name),patch.object(aux,name,value),self.assertRaisesRegex(ValueError,pattern):
                aux.process(self.request,'plan')
        self.assertFalse(self.target.exists())

    def test_two_explicit_new_names_are_directories_and_no_nearby_name_allowed(self):
        for name in ('light-light126-n1-evidenceops-20261113_0640','b0_control_l02_l12_20261113_0640'):
            request=copy.deepcopy(self.request);request['entries']=[dict(name=name,tree_sha256=None)]
            path=self.f.private/name;path.mkdir()
            self.assertEqual(aux.process(request,'plan')['selected_names'],[name])
            path.rmdir();path.write_bytes(b'wrong type')
            with self.assertRaisesRegex(ValueError,'type changed'):aux.process(request,'plan')
            request['entries'][0]['name']=name+'_other'
            with self.assertRaisesRegex(ValueError,'unlisted'):aux.process(request,'plan')

    def test_missing_wrong_identity_and_changed_tree_refused(self):
        with self.assertRaisesRegex(ValueError,'reviewed tree|Reviewed per-entry'):aux.process(self.request,'archive')
        request=self.pinned();request['entries'][0]['tree_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'identity differs'):aux.process(request,'archive')
        request=self.pinned();(self.source/'new-evidence').write_bytes(b'new')
        with self.assertRaisesRegex(ValueError,'identity differs'):aux.process(request,'archive')
        self.assertFalse(self.target.exists());self.assertFalse(aux.lock_path().exists())

    def test_low_space_preserves_source_and_never_creates_destination(self):
        request=self.pinned();before=self.snapshot()
        with patch.object(aux.shutil,'disk_usage',return_value=types.SimpleNamespace(free=aux.base.RESERVE)):
            with self.assertRaisesRegex(ValueError,'20% margin'):aux.process(request,'archive')
        self.assertEqual(before,self.snapshot());self.assertFalse(self.target.exists());self.assertFalse(aux.lock_path().exists())

    def test_mid_write_space_failure_preserves_partial_and_failed_receipt(self):
        request=self.pinned();before=self.snapshot();calls=[]
        def disk(path):
            calls.append(path);return types.SimpleNamespace(free=100*1024**3 if len(calls)==1 else 0)
        with patch.object(aux.shutil,'disk_usage',side_effect=disk),self.assertRaisesRegex(ValueError,'reserve'):
            aux.process(request,'archive')
        self.assertEqual(before,self.snapshot());self.assertTrue((self.target/'auxiliary-evidence.tar.gz.partial').exists())
        self.assertEqual(json.loads((self.target/'state.json').read_text())['status'],'failed')
        self.assertFalse((self.target/'receipt.json').exists());self.assertFalse(aux.lock_path().exists())

    def test_archive_corruption_and_source_mutation_prevent_publish(self):
        request=self.pinned();original=aux.base.verify_archive
        def corrupt(path,rows):
            with path.open('r+b') as stream:stream.seek(-1,2);value=stream.read(1);stream.seek(-1,2);stream.write(bytes([value[0]^1]))
            return original(path,rows)
        with patch.object(aux.base,'verify_archive',side_effect=corrupt),self.assertRaises(Exception):
            aux.process(request,'archive')
        self.assertFalse((self.target/'auxiliary-evidence.tar.gz').exists());self.assertFalse(aux.lock_path().exists())
        self.target=self.operations/'n1-aux-archive-20261113_0621-mutated'
        self.request['destination']=str(self.target);request=self.pinned()
        def mutate(path,rows):
            value=original(path,rows);(self.source/'selected.bin').write_bytes(b'changed by fixture');return value
        with patch.object(aux.base,'verify_archive',side_effect=mutate),self.assertRaisesRegex(ValueError,'changed during'):
            aux.process(request,'archive')
        self.assertEqual((self.source/'selected.bin').read_bytes(),b'changed by fixture')
        self.assertFalse((self.target/'auxiliary-evidence.tar.gz').exists());self.assertFalse(aux.lock_path().exists())

    def test_owner_replaced_after_copy_is_not_released_or_marked_verified(self):
        request=self.pinned();original=aux.base.verify_archive
        def replace(path,rows):
            result=original(path,rows);(aux.lock_path()/'owner.json').write_bytes(b'replacement-owner');return result
        with patch.object(aux.base,'verify_archive',side_effect=replace),self.assertRaisesRegex(ValueError,'ownership changed'):
            aux.process(request,'archive')
        self.assertEqual((aux.lock_path()/'owner.json').read_bytes(),b'replacement-owner')
        self.assertFalse((self.target/'receipt.json').exists());self.assertFalse((self.target/'auxiliary-evidence.tar.gz').exists())

    def test_open_users_reject_before_archive(self):
        request=self.pinned()
        with patch.object(aux.base,'no_open_users',side_effect=ValueError('still in use')),self.assertRaisesRegex(ValueError,'still in use'):
            aux.process(request,'archive')
        self.assertFalse(self.target.exists());self.assertFalse(aux.lock_path().exists())

    def test_initial_owner_sync_failure_keeps_partial_lock_for_review(self):
        request=self.pinned();before=self.snapshot()
        with patch.object(aux.os,'fsync',side_effect=OSError('fixture ENOSPC')):
            with self.assertRaisesRegex(OSError,'ENOSPC'):aux.process(request,'archive')
        self.assertTrue((aux.lock_path()/'owner.json').is_file())
        self.assertEqual(before,self.snapshot());self.assertFalse(self.target.exists())

    def test_dependency_hash_and_request_hash_are_mandatory(self):
        with patch.object(aux,'HELPER_SHA','0'*64),self.assertRaisesRegex(ValueError,'helper SHA'):
            aux.process(self.request,'plan')
        path=self.f.root/'request.json';path.write_text(json.dumps(self.request))
        args=['tool','--mode','plan','--request',str(path),'--request-sha256','0'*64]
        with patch.object(sys,'argv',args),self.assertRaisesRegex(ValueError,'request SHA'):aux.main()
        self.assertFalse(self.target.exists())


if __name__=='__main__':unittest.main()
