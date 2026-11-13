import copy
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import t80_resume_evidence as resume


class ResumeGuard(unittest.TestCase):
    def test_new_clone_accepts_only_pinned_activity_tool_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            source=Path(directory)/'source';target=Path(directory)/'target'
            name='workspaces/arch03/scripts/t80_window.py'
            for root,body in ((source,'old'),(target,'fixed')):
                (root/name).parent.mkdir(parents=True);(root/name).write_text(body)
                (root/'hardware.sv').write_text('same hardware')
                files={n:resume.common.sha(root/n) for n in (name,'hardware.sv')}
                (root/'manifest.json').write_text(json.dumps(dict(files=files)))
            old=dict(bundle=str(source),bundle_manifest_sha256=resume.common.sha(source/'manifest.json'))
            req=dict(bundle=str(target),bundle_manifest_sha256=resume.common.sha(target/'manifest.json'))
            resume.verify_tool_only_clone(old,req)
            (target/'hardware.sv').write_text('changed hardware')
            manifest=json.loads((target/'manifest.json').read_text())
            manifest['files']['hardware.sv']=resume.common.sha(target/'hardware.sv')
            (target/'manifest.json').write_text(json.dumps(manifest))
            req['bundle_manifest_sha256']=resume.common.sha(target/'manifest.json')
            with self.assertRaisesRegex(ValueError,'non-activity source'):
                resume.verify_tool_only_clone(old,req)

    def test_only_terminal_queue_with_exact_completed_gate_prefix(self):
        with tempfile.TemporaryDirectory() as directory:
            q=Path(directory)
            names=('contention','sequence','synth','timing_audit','drc_audit','structure','gate')
            ref=lambda name:dict(run='/'+name,sha256='a'*64)
            state=dict(status='failed',pid=2147483647,child_pid=None,
                completed=[dict(stage='t80_'+n,reference=ref(n)) for n in names],batch_reference=ref('batch'))
            (q/'request.json').write_text(json.dumps(dict(bundle_manifest_sha256='b'*64)))
            request=dict(original_queue=str(q),bundle_manifest_sha256='b'*64)
            def write(value):
                (q/'state.json').write_text(json.dumps(value))
                request['original_queue_sha256']=hashlib.sha256((q/'state.json').read_bytes()).hexdigest()
            with patch.object(resume,'reference',side_effect=lambda path,stage:ref(path.lstrip('/'))), \
                 patch.object(resume,'pid_present',side_effect=lambda pid:pid==os.getpid()):
                write(state);self.assertEqual(resume.original(request)[0],state)
                for field,value in [('status','running'),('child_pid',44),('pid',os.getpid())]:
                    bad=dict(state);bad[field]=value;write(bad)
                    with self.assertRaises(ValueError):resume.original(request)
                for count in (6,8):
                    bad=copy.deepcopy(state);bad['completed']=(bad['completed']+[bad['completed'][-1]])[:count];write(bad)
                    with self.assertRaises(ValueError):resume.original(request)
                write(state);request['original_queue_sha256']='c'*64
                with self.assertRaises(ValueError):resume.original(request)


if __name__=='__main__':unittest.main()
