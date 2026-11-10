"""Check queue refusal of partial/changed predecessors and duplicate scope."""
import json
from pathlib import Path
import tempfile
import unittest
import icb32_finalize_queue as queue


class FinalizeQueueTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.run=Path(self.tmp.name)/'gate_session'/'icb32_gate'
        self.run.mkdir(parents=True)
        self.synth='a'*64
        self.report=dict(synthesis_summary_sha256=self.synth,gate_simulation_verified=True,
            cpu_executed=True,cases=[dict(case='layer_%02d'%n,
            activity=dict(status='scope_and_window_verified')) for n in range(1,13)]+
            [dict(case='extremes'),dict(case='rounding')])
        self.publish('running')

    def publish(self,status):
        queue.save(self.run/'summary.json',self.report)
        queue.save(self.run.parent/'state.json',dict(stages=dict(icb32_gate=dict(
            status=status,pid=123,started='fixed_start',summary_sha256=queue.sha(self.run/'summary.json')))))

    def result(self):
        return queue.gate_result(self.run,123,'fixed_start',self.synth)

    def test_wait_then_full_receipt(self):
        self.assertIsNone(self.result())
        self.publish('passed')
        self.assertEqual(self.result()['sha256'],queue.sha(self.run/'summary.json'))

    def test_refuses_failed_partial_or_missing_activity(self):
        self.publish('failed')
        with self.assertRaisesRegex(ValueError,'failed or stopped'):self.result()
        self.report['cases'].pop();self.publish('passed')
        with self.assertRaisesRegex(ValueError,'all 14'):self.result()
        self.report['cases'].append(dict(case='rounding'))
        self.report['cases'][0]['activity']['status']='partial';self.publish('passed')
        with self.assertRaisesRegex(ValueError,'activity'):self.result()

    def test_refuses_changed_identity_or_summary(self):
        self.publish('passed')
        with self.assertRaisesRegex(ValueError,'identity'):
            queue.gate_result(self.run,456,'fixed_start',self.synth)
        with self.assertRaisesRegex(ValueError,'identity'):
            queue.gate_result(self.run,123,'other_start',self.synth)
        with self.assertRaisesRegex(ValueError,'synthesis'):
            queue.gate_result(self.run,123,'fixed_start','b'*64)
        self.report['cpu_executed']=False
        queue.save(self.run/'summary.json',self.report)
        with self.assertRaisesRegex(ValueError,'digest'):self.result()

    def test_serial_scope_is_twelve_power_then_metrics_then_batch(self):
        steps=queue.commands(Path('/bundle'),'final01',dict(run='/gate',sha256='c'*64),Path('/data'))
        self.assertEqual(len(steps),14)
        self.assertEqual(len({x['session'] for x in steps}),14)
        self.assertEqual([x['stage'] for x in steps],['icb32_power']*12+['icb32_soc','icb32_batch'])
        self.assertEqual([x['case'] for x in steps[:12]],['layer_%02d'%n for n in range(1,13)])
        self.assertEqual(steps[-1]['argv'][-2:],['--dataset',str(Path('/data'))])
        self.assertTrue(all('--gate-summary-sha256' in x['argv'] for x in steps[:12]))


if __name__=='__main__':unittest.main()
