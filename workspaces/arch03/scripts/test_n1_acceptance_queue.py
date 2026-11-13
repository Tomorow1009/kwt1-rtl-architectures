import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import n1_acceptance_queue as q


class QueueTests(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory(); self.root = Path(self.t.name)
        self.run = self.root/'activity/n1_saif'; self.run.mkdir(parents=True)
        self.request = dict(activity_run=str(self.run), activity_pid=123, activity_started='fixed',
                            gate_summary_sha256='gate', synthesis_summary_sha256='synth')
        self.record = dict(status='running', pid=123, started='fixed', run=str(self.run))
        self.write_state()

    def tearDown(self):self.t.cleanup()
    def write_state(self):
        (self.run.parent/'state.json').write_text(json.dumps({'stages':{'n1_saif':self.record}}))

    def test_observe_running_without_claiming_completion(self):
        self.assertIsNone(q.observed_activity(self.request))

    def test_replaced_and_failed_original_do_not_continue(self):
        self.record['pid'] = 124; self.write_state()
        with self.assertRaisesRegex(ValueError, 'identity changed'):q.observed_activity(self.request)
        self.record.update(pid=123, status='failed'); self.write_state()
        with self.assertRaisesRegex(ValueError, 'failed'):q.observed_activity(self.request)

    def complete(self):
        result = dict(schema='arch03-n1-native-saif-v1', status='N1_native_saif_function_and_complete_windows_passed',
                      gate_summary_sha256='gate', synthesis_summary_sha256='synth',
                      cases=[{'case':'layer_%02d'%i} for i in range(1,13)])
        (self.run/'summary.json').write_text(json.dumps(result))
        self.record.update(status='passed', summary_sha256=q.common.sha(self.run/'summary.json'));self.write_state()
        return result

    def test_completed_exact_twelve_and_hash_required(self):
        result = self.complete(); self.assertEqual(q.observed_activity(self.request)['run'], str(self.run))
        result['cases'][-1]['case'] = 'layer_01'
        (self.run/'summary.json').write_text(json.dumps(result))
        with self.assertRaisesRegex(ValueError, 'matching completed'):q.observed_activity(self.request)
        self.record['summary_sha256'] = q.common.sha(self.run/'summary.json');self.write_state()
        with self.assertRaisesRegex(ValueError, 'fixed N1'):q.observed_activity(self.request)

    def test_failed_child_is_waited_and_not_recorded_as_done(self):
        output = self.root/'queue';output.mkdir()
        state = {'completed':[]}; target=self.root/'new/n1_precision'
        class Child:
            pid = 987
            waited = False
            def wait(self):self.waited=True;return 1
        child=Child()
        with patch.object(q.subprocess,'Popen',return_value=child):
            with self.assertRaisesRegex(ValueError,'child failed'):
                q.run_child(['test'],output,state,'precision',target,'n1_precision',self.root/'lock')
        self.assertTrue(child.waited);self.assertIsNone(state['child_pid']);self.assertEqual(state['completed'],[])

    def test_existing_child_not_started(self):
        output=self.root/'queue';output.mkdir();target=self.root/'old/n1_precision';target.parent.mkdir()
        with patch.object(q.subprocess,'Popen') as spawn:
            with self.assertRaisesRegex(ValueError,'Preserve existing'):
                q.run_child(['test'],output,{'completed':[]},'precision',target,'n1_precision',self.root/'lock')
            spawn.assert_not_called()


if __name__=='__main__':unittest.main()
