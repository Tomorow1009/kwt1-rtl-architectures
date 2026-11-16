"""Only the exact recorded desktop helpers may have inaccessible descriptors."""
import importlib.util
from pathlib import Path
import tempfile
import types
import unittest

SOURCE=Path(__file__).resolve().parents[3]/'handoff/team/evidence/C32_R4_L03_XZ_MIGRATE_20261117.py'
spec=importlib.util.spec_from_file_location('r4_migrate',str(SOURCE))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def api(rows,uses=0):
    return types.SimpleNamespace(no_open_users=lambda *a,**k:dict(
        observed_open_runtime_uses=uses,inaccessible_owned_processes=rows,
        all_owned_processes_observed=False,idle_proven=False,source_deletion_authorized=False))


class Visibility(unittest.TestCase):
    def test_classification_never_claims_inaccessible_descriptors_observed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);pid=10519;name,cmd,start=m.SESSION_HELPERS[pid]
            p=root/str(pid);p.mkdir();(p/'comm').write_text(name+'\n')
            (p/'cmdline').write_bytes(cmd.encode()+b'\0')
            (p/'stat').write_text('%d (%s) '%(pid,name)+' '.join(['S']+['0']*18+[start]))
            result=m.usage_observation(api([dict(pid=pid,errno=13)]),root,p.stat().st_uid)
            self.assertFalse(result['idle_proven']);self.assertFalse(result['source_deletion_authorized'])
            self.assertFalse(result['observation_alone_authorizes_deletion'])
            self.assertFalse(result['classified_protected_session_helpers'][0]['descriptors_observed'])
            (p/'stat').write_text('%d (%s) '%(pid,name)+' '.join(['S']+['0']*18+['999']))
            with self.assertRaisesRegex(ValueError,'identity changed'):
                m.usage_observation(api([dict(pid=pid,errno=13)]),root,p.stat().st_uid)

    def test_unknown_protected_or_observed_source_users_reject(self):
        with self.assertRaisesRegex(ValueError,'Unclassified'):
            m.usage_observation(api([dict(pid=987654,errno=13)]),uid=0)
        with self.assertRaisesRegex(ValueError,'observed use'):
            m.usage_observation(api([],uses=1),uid=0)

    def test_wrong_permission_error_not_broadly_ignored(self):
        with self.assertRaisesRegex(ValueError,'Unclassified'):
            m.usage_observation(api([dict(pid=10519,errno=5)]),uid=0)


if __name__=='__main__':unittest.main()
