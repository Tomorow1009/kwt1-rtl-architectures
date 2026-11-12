"""Private-runtime policy fixtures; Linux metadata is simulated on Windows.

No server directory, vendor library or actual EDA work is touched.
"""
import copy
import json
from pathlib import Path
import stat
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

import n1_paths as paths
import n1_server as runner


class RuntimePathTests(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory();self.addCleanup(self.temporary.cleanup)
        self.root=Path(self.temporary.name).resolve();self.shared=self.root/'shared';self.shared.mkdir()
        self.private=self.root/'s4_21usr_n1_20261113_0210';self.private.mkdir()
        self.cfg=dict(server_root=str(self.shared),tools={'dc_shell':'fixed_vendor_tool'},models={'fixture':True})
        self.ops=self.bundle('light-light126-n1-v4-OPS',True)
        self.base=self.bundle('light-light126-n1-v4-BASE',False)
        self.other=self.bundle('light-light126-n1-v4-UNREGISTERED',False)
        self.overrides={}
        def simulated_stat(path):
            path=Path(path).absolute();value=path.lstat()
            values=dict(st_mode=value.st_mode,st_uid=0,st_dev=value.st_dev,st_ino=value.st_ino)
            if path==self.private:values['st_mode']=stat.S_IFDIR|0o700
            values.update(self.overrides.get(path,{}))
            return types.SimpleNamespace(**values)
        for target,name,value in ((paths,'TMP_ROOT',self.root),(paths,'SERVER_ROOT',str(self.shared)),
                                  (paths,'_identity',lambda:0),(paths,'_stat',simulated_stat)):
            handle=patch.object(target,name,value);handle.start();self.addCleanup(handle.stop)

    def bundle(self,name,ops):
        root=self.private/name;root.mkdir()
        files={'handoff/team/server_config.json':json.dumps(self.cfg),
               'workspaces/arch03/scripts/n1_server.py':'# fixture operations entry\n'}
        files.update({'workspaces/arch03/rtl/arch03_n1_'+name+'.sv':'// fixture '+name+'\n'
            for name in ('systolic5x16','requantize','linear16x5','decoder','accel')})
        if ops:files['workspaces/arch03/scripts/n1_paths.py']='# fixture boundary identity\n'
        for relative,text in files.items():
            path=root/relative;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text)
        (root/'manifest.json').write_text(json.dumps(dict(fixture=True,files={name:paths.digest(root/name) for name in files})))
        (root/'runs/session/n1_synth').mkdir(parents=True)
        return root

    def configure(self,**changes):
        args=dict(cfg=self.cfg,bundle=self.ops,runtime_root=self.private,
                  manifest_sha=paths.digest(self.ops/'manifest.json'),
                  evidence=[(self.base,paths.digest(self.base/'manifest.json'))])
        args.update(changes)
        return paths.configure(**args)

    def test_explicit_siblings_pass_and_original_shared_lock_is_retained(self):
        cfg=self.configure()
        self.assertEqual(cfg['server_root'],self.cfg['server_root'])
        self.assertEqual(len(cfg['runtime_roots']),2)
        self.assertNotIn('runtime_roots',self.cfg)
        for bundle in (self.ops,self.base):
            run=bundle/'runs/session/n1_synth'
            self.assertEqual(paths.allowed_run(run,cfg),run)
        receipt=paths.receipt(cfg)
        self.assertEqual(receipt['shared_team_lock'],str(self.shared/'.arch02_team_lock'))
        self.assertTrue(receipt['durable_archive_required'])

    def test_default_shared_behavior_and_no_implicit_tmp_grant(self):
        self.assertEqual(paths.configure(self.cfg,self.shared/'bundle'),self.cfg)
        self.assertEqual(paths.allowed_run(self.shared/'original_run',self.cfg),self.shared/'original_run')
        with self.assertRaisesRegex(ValueError,'requires explicit'):paths.configure(self.cfg,self.ops)
        with self.assertRaisesRegex(ValueError,'outside original'):paths.allowed_run(self.base/'runs/session/n1_synth',self.cfg)
        with self.assertRaisesRegex(ValueError,'requires --runtime-root'):
            paths.configure(self.cfg,self.shared/'bundle',manifest_sha='1'*64)

    def test_arbitrary_tmp_other_bundles_and_nonstage_paths_rejected(self):
        cfg=self.configure()
        for path in (self.other/'runs/session/n1_synth',self.root/'unrelated',self.ops/'workspaces',
                     self.ops/'runs/session',self.ops/'runs/session/n1_synth/extra'):
            with self.subTest(path=str(path)):
                with self.assertRaises((ValueError,FileNotFoundError)):paths.allowed_run(path,cfg)
        wrong=self.root/'any_tmp_root';wrong.mkdir()
        with self.assertRaisesRegex(ValueError,'DATE_TIME'):self.configure(runtime_root=wrong)

    def test_runtime_mode_owner_and_root_directory_identity_enforced(self):
        for change in ({'st_mode':stat.S_IFDIR|0o755},{'st_uid':1001},{'st_mode':stat.S_IFLNK|0o777}):
            self.overrides[self.private]=change
            with self.subTest(change=change):
                with self.assertRaises(ValueError):self.configure()
        self.overrides.clear();cfg=self.configure()
        self.overrides[self.private]={'st_ino':paths._stat(self.private).st_ino+1}
        with self.assertRaisesRegex(ValueError,'replaced'):paths.recheck(cfg)

    def test_source_owner_symlink_and_digest_are_rechecked(self):
        source=self.base/'workspaces/arch03/rtl/arch03_n1_accel.sv'
        cfg=self.configure()
        for change in ({'st_uid':1001},{'st_mode':stat.S_IFLNK|0o777}):
            self.overrides[source]=change
            with self.subTest(change=change):
                with self.assertRaises(ValueError):paths.recheck(cfg)
        self.overrides.clear();source.write_text('// changed\n')
        with self.assertRaisesRegex(ValueError,'Changed runtime bundle source'):paths.recheck(cfg)

    def test_manifest_pin_required_and_config_cannot_inject_roots(self):
        for value in (None,'bad','0'*64):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):self.configure(manifest_sha=value)
        cfg=dict(self.cfg,runtime_roots=[])
        with self.assertRaisesRegex(ValueError,'inject'):self.configure(cfg=cfg)
        with self.assertRaisesRegex(ValueError,'Duplicate'):
            self.configure(evidence=[(self.ops,paths.digest(self.ops/'manifest.json'))])

    def test_config_library_and_lock_changes_are_not_authorized_by_tmp(self):
        cfg=copy.deepcopy(self.cfg);cfg['models']={'changed':True}
        with self.assertRaisesRegex(ValueError,'configuration, libraries or shared team lock'):self.configure(cfg=cfg)
        cfg['server_root']=str(self.private)
        with self.assertRaisesRegex(ValueError,'retain the existing shared'):self.configure(cfg=cfg)

    def test_manifest_cannot_escape_or_register_incomplete_ops(self):
        manifest=json.loads((self.ops/'manifest.json').read_text())
        manifest['files']['../escape']='a'*64
        (self.ops/'manifest.json').write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError,'Unsafe runtime manifest'):self.configure()
        with self.assertRaisesRegex(ValueError,'complete frozen N1'):
            self.configure(bundle=self.base,manifest_sha=paths.digest(self.base/'manifest.json'),evidence=[])

    def test_nested_bundle_and_altered_registration_rejected(self):
        nested=self.private/'nested';nested.mkdir()
        with self.assertRaisesRegex(ValueError,'direct child'):
            self.configure(bundle=nested)
        cfg=self.configure();cfg['runtime_roots'][0]['uid']=999
        with self.assertRaisesRegex(ValueError,'registration identity'):paths.recheck(cfg)

    def test_new_runtime_runner_uses_the_original_single_lock(self):
        process_relative='workspaces/arch03/scripts/n1_process.py'
        process_file=self.ops/process_relative
        process_file.write_bytes(Path(runner.n1_process.__file__).read_bytes())
        manifest=json.loads((self.ops/'manifest.json').read_text())
        manifest['files'][process_relative]=paths.digest(process_file)
        (self.ops/'manifest.json').write_text(json.dumps(manifest))
        evidence_digest=paths.digest(self.base/'manifest.json')
        argv=['n1_server.py','soc','--session','runtime_fixture','--runtime-root',str(self.private),
            '--runtime-manifest-sha256',paths.digest(self.ops/'manifest.json'),
            '--runtime-evidence',str(self.base),evidence_digest]
        def verify(cfg,run,*args,**kwargs):
            self.assertEqual(cfg['server_root'],str(self.shared))
            self.assertEqual(len(cfg['runtime_roots']),2)
            self.assertTrue((self.shared/'.arch02_team_lock/owner.json').is_file())
            owner=json.loads((self.shared/'.arch02_team_lock/owner.json').read_text())
            self.assertEqual(owner['child_ledger'],str(run.parent/'process_ledger'))
            self.assertFalse((self.private/'.arch02_team_lock').exists())
            self.assertTrue((run/'runtime_storage_receipt.json').is_file())
            return dict(status='fixture_only',cpu_executed=False)
        with patch.object(runner.common,'ROOT',self.ops),patch.object(runner.common,'ACTIVE_CHILD',None), \
             patch.object(runner.n1_process,'__file__',str(process_file)), \
             patch.object(sys,'argv',argv),patch.dict(sys.modules,{'n1_soc':types.SimpleNamespace(verify=verify)}), \
             patch.object(runner.shutil,'disk_usage',return_value=types.SimpleNamespace(free=40*1024**3)):
            runner.main()
        state=json.loads((self.ops/'runs/runtime_fixture/state.json').read_text())
        self.assertEqual(state['stages']['n1_soc']['status'],'passed')
        self.assertFalse((self.shared/'.arch02_team_lock').exists())

    def test_native_N1_reference_consumers_enforce_policy_before_evidence_read(self):
        import n1_gate,n1_saif,n1_power,n1_timing_audit,n1_drc_audit
        cfg=self.configure();outside=self.other/'runs/session/n1_synth'
        run=self.ops/'runs/session/n1_synth'
        checks=(lambda:n1_gate.verify_synthesis(outside,'0'*64,cfg),
                lambda:n1_saif.qualification(outside,'0'*64,cfg),
                lambda:n1_saif.verify(cfg,run,outside,'0'*64,run,'0'*64,n1_saif.LAYERS,None),
                lambda:n1_power.estimate(cfg,run,outside,'0'*64,'layer_01',None),
                lambda:n1_timing_audit.audit(cfg,run,outside,'0'*64,None),
                lambda:n1_drc_audit.audit(cfg,run,outside,'0'*64,None))
        for check in checks:
            with self.assertRaisesRegex(ValueError,'outside original'):check()


if __name__=='__main__':unittest.main()
