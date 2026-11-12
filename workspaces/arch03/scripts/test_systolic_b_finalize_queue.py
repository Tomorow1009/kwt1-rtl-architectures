"""Queue failure routing only; fake subprocesses are never hardware evidence."""
import contextlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import systolic_b_finalize_queue as queue


class QueueTests(unittest.TestCase):
    def exercise(self,failed=None,existing=False,qualified=False):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'handoff/team').mkdir(parents=True)
            (root/'handoff/team/server_config.json').write_text(json.dumps({'server_root':str(root)}))
            gate=root/'gate';gate.mkdir();(gate/'summary.json').write_text(json.dumps({'firmware_sha256':'a'*64}))
            request=dict(schema='systolic-b-finalize-request-v1',dataset=str(root/'data'),
                bundle_manifest_sha256='0'*64,
                asic={'run':'old_asic','sha256':'b'*64},synthesis={'run':'synth','sha256':'c'*64},
                gate={'run':str(gate),'sha256':queue.sha(gate/'summary.json')},
                R4_gate={'run':'R4_gate','sha256':'d'*64},R4_power={'run':'R4_power','sha256':'e'*64},
                native_probe={'run':'tiny','sha256':'f'*64})
            operations=root/'ops';operations.mkdir();(operations/'systolic_b_ops.py').write_text('fixture only')
            (operations/'manifest.json').write_text(json.dumps({'files':{'systolic_b_ops.py':queue.sha(operations/'systolic_b_ops.py')}}))
            request['operations']={'path':str(operations),'sha256':queue.sha(operations/'manifest.json')}
            if qualified:request['saif_qualification']={'run':'qualified','sha256':'1'*64}
            req=root/'request.json';req.write_text(json.dumps(request));calls=[]
            if existing:(root/'runs/test_clean14').mkdir(parents=True)
            class Child:
                pid=101
                def __init__(self,argv,**kwargs):
                    name=argv[argv.index('--stage')+1] if '--stage' in argv else argv[2]
                    session=argv[argv.index('--session')+1];calls.append(name)
                    run=root/'runs'/session/name;run.mkdir(parents=True)
                    (run/'summary.json').write_text(json.dumps({'compile_receipt':{'firmware_manifest_sha256':'a'*64}}))
                    self.code=1 if name==failed else 0
                def wait(self):return self.code
            with contextlib.ExitStack() as stack:
                for target,value in [('ROOT',root),('inputs',lambda:None),('preflight',lambda *args:None),
                        ('configuration_identity',lambda run:{'same':'fixture'}),('stage',lambda *args:None)]:
                    stack.enter_context(patch.object(queue,target,value))
                stack.enter_context(patch.object(queue.subprocess,'Popen',Child))
                stack.enter_context(patch.object(queue.sys,'argv',['queue','--request',str(req),
                    '--request-sha256',queue.sha(req),'--session','test']))
                if failed=='systolic_b_batch' or existing:
                    with self.assertRaises(ValueError):queue.main()
                else:queue.main()
            state=json.loads((root/'runs/test_queue/state.json').read_text())
            report=root/'runs/test_queue/report_request.json'
            return calls,state,json.loads(report.read_text()) if report.exists() else None

    def test_optional_saif_failure_retains_completed_own_batch(self):
        calls,state,report=self.exercise('native_saif_r4_replay')
        self.assertEqual(calls,['systolic_b_soc','systolic_b_batch','native_saif_r4_replay'])
        self.assertEqual(state['status'],'reports_ready_review_required')
        self.assertEqual(len(state['optional_failures']),1)
        self.assertIn('batch',report);self.assertEqual(report['power'],[])
        self.assertNotIn('activity',report);self.assertFalse(state['system_power_verified'])

    def test_actual_batch_failure_stops_successors(self):
        calls,state,report=self.exercise('systolic_b_batch')
        self.assertEqual(calls,['systolic_b_soc','systolic_b_batch'])
        self.assertEqual(state['status'],'failed');self.assertIsNone(report)

    def test_existing_session_is_not_restarted(self):
        calls,state,report=self.exercise(existing=True)
        self.assertEqual(calls,[]);self.assertEqual(state['status'],'failed');self.assertIsNone(report)

    def test_existing_method_qualification_does_not_repeat_R4_replay(self):
        calls,state,report=self.exercise('systolic_b_saif',qualified=True)
        self.assertEqual(calls,['systolic_b_soc','systolic_b_batch','systolic_b_saif'])
        self.assertEqual(state['status'],'reports_ready_review_required')
        self.assertIn('batch',report);self.assertEqual(report['power'],[])


if __name__=='__main__':unittest.main()
