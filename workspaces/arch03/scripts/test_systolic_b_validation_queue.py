"""Regression for real queue CLI selection; mocked children are not RTL evidence."""
import contextlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import build_systolic_b_sequence
import systolic_b_gate
import systolic_b_validation_queue as queue


class ValidationQueueTests(unittest.TestCase):
    def exercise(self, cases, fail=None):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'handoff/team').mkdir(parents=True)
            (root/'handoff/team/server_config.json').write_text(json.dumps({'server_root':str(root)}))
            (root/'manifest.json').write_text('{}')
            calls=[]
            class Child:
                pid=123
                def __init__(self, command, **kwargs):
                    self.stage=command[2];calls.append(command)
                    session=command[command.index('--session')+1]
                    run=root/'runs'/session/self.stage;run.mkdir(parents=True)
                    self.code=int(self.stage==fail)
                    if self.stage=='systolic_b_sequence':
                        # Model the real runner's early firmware A/B-order guard.
                        selected=command[command.index('--cases')+1:] if '--cases' in command else None
                        self.code=int(selected!=list(cases))
                    (run/'summary.json').write_text('{}')
                    (run.parent/'state.json').write_text(json.dumps({'stages':{self.stage:{
                        'status':'failed' if self.code else 'passed',
                        'summary_sha256':queue.sha(run/'summary.json')}}}))
                def wait(self):return self.code
            manifest={'tasks':{key:{'case':case} for key,case in zip(('A','B'),cases)}}
            with contextlib.ExitStack() as stack:
                for name,value in [('ROOT',root),('inputs',lambda:None),('predecessor',lambda *args:'a'*64)]:
                    stack.enter_context(patch.object(queue,name,value))
                stack.enter_context(patch.object(systolic_b_gate,'verify_synthesis',return_value=(
                    {'setup_hold_nonnegative':True,'area_summary':{'conservative_budget_within_2mm2':True}},None)))
                stack.enter_context(patch.object(build_systolic_b_sequence,'verify_firmware',return_value=(manifest,None)))
                stack.enter_context(patch.object(queue.subprocess,'Popen',Child))
                stack.enter_context(patch.object(queue.shutil,'disk_usage',return_value=type('Usage',(),{'free':20*1024**3})()))
                stack.enter_context(patch.object(queue.sys,'argv',['queue','--synth-run',str(root/'synth'),
                    '--synth-pid','1','--synth-started','fixture','--bundle-manifest-sha256',queue.sha(root/'manifest.json'),
                    '--session','test']))
                if fail=='systolic_b_contention':
                    with self.assertRaises(ValueError):queue.main()
                else:queue.main()
            return calls,json.loads((root/'runs/test_queue/state.json').read_text())

    def test_sequence_uses_firmware_order_and_then_runs_remaining_stages(self):
        for cases in [('layer_01','rounding'),('extremes','layer_02')]:
            with self.subTest(cases=cases):
                calls,state=self.exercise(cases)
                self.assertEqual([c[2] for c in calls],['systolic_b_sequence','systolic_b_contention',
                    'systolic_b_saif_probe','systolic_b_timing_audit','systolic_b_gate'])
                self.assertEqual(state['status'],'validation_complete_review_required')
                self.assertFalse(state['final1200_started'])

    def test_required_failure_stops_successors(self):
        calls,state=self.exercise(('layer_01','rounding'),'systolic_b_contention')
        self.assertEqual(len(calls),2);self.assertEqual(state['status'],'failed')

    def test_optional_probe_failure_is_retained_without_skipping_gate(self):
        calls,state=self.exercise(('layer_01','rounding'),'systolic_b_saif_probe')
        self.assertEqual(calls[-1][2],'systolic_b_gate')
        self.assertEqual(state['status'],'validation_complete_review_required')
        self.assertEqual(len(state['optional_failures']),1)


if __name__=='__main__':unittest.main()
