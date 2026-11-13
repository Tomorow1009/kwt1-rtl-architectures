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
