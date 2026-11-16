import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, MagicMock
import c32_finish as finish


class FinishOrderTests(unittest.TestCase):
    def test_execute_checks_real_hashes_and_writes_all_stage_receipts(self):
        # Exercise the real queue entry point and disk receipts, mocking only
        # external source verification, EDA and the shared-server lock owner.
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'handoff/team').mkdir(parents=True)
            (root/'manifest.json').write_text('{}')
            (root/'handoff/team/server_config.json').write_text('{}')
            (root/'synth').mkdir()
            constraint=root/'synth/constraints.rpt'
            clean='This design has no violated constraints.\n'
            constraint.write_text(clean)
            synthesis_report={'scope':'c32_partitioned_whole_soc_task_mode','setup_hold_nonnegative':True,
                'area_summary':{'conservative_budget_mm2':0.95},'artifacts':{'constraints.rpt':finish.common.sha(constraint)}}
            request=dict(schema='c32-final-netlist-finish-v1',bundle=str(root),
                bundle_manifest_sha256=finish.common.sha(root/'manifest.json'),
                queue_sha256=finish.common.sha(Path(finish.__file__)),runtime_root=str(root),
                runtime_evidence=[],synthesis=dict(run=str(root/'synth'),sha256='a'*64),
                qualification=dict(run=str(root/'qualification'),sha256='b'*64))
            queue=root/'runs/finish';queue.parent.mkdir()
            ledger=MagicMock();ledger.acquired=True
            with contextlib.ExitStack() as stack:
                stack.enter_context(patch.object(finish.common,'ROOT',root))
                stack.enter_context(patch.object(finish.paths,'configure',return_value={'server_root':str(root)}))
                stack.enter_context(patch.object(finish.common,'inputs'))
                stack.enter_context(patch.object(finish.paths,'recheck'))
                stack.enter_context(patch.object(finish.paths,'allowed_run'))
                stack.enter_context(patch.object(finish.paths,'receipt',return_value={}))
                stack.enter_context(patch.object(finish,'verify_synthesis',return_value=(synthesis_report,{})))
                stack.enter_context(patch('c32_saif.qualification'))
                stack.enter_context(patch.object(finish,'ProcessLedger',return_value=ledger))
                stack.enter_context(patch.object(finish.shutil,'disk_usage',return_value=MagicMock(free=100*1024**3)))
                dispatch=stack.enter_context(patch.object(finish,'dispatch',side_effect=lambda name,*a:dict(test_stage=name)))
                stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
                bad=dict(request,queue_sha256='0'*64)
                with self.assertRaisesRegex(ValueError,'source changed'):finish.execute(bad,queue)
                self.assertFalse(queue.exists());dispatch.assert_not_called()
                for invalid in ('max_transition\ncore/n9916 (dont_touch)\n 1.35 1.37 -0.02 (VIOLATED)\n',
                                'Report did not complete\n'):
                    constraint.write_text(invalid)
                    synthesis_report['artifacts']['constraints.rpt']=finish.common.sha(constraint)
                    with self.assertRaisesRegex(ValueError,'design-rule violations'):finish.execute(request,queue)
                    self.assertFalse(queue.exists());dispatch.assert_not_called();ledger.acquire.assert_not_called()
                constraint.write_text(clean)
                synthesis_report['artifacts']['constraints.rpt']=finish.common.sha(constraint)
                finish.execute(request,queue)
            state=json.loads((queue/'state.json').read_text())
            self.assertEqual(state['status'],'reports_ready_review_required')
            self.assertFalse(state['stage_accepted'])
            self.assertEqual([r['stage'] for r in state['completed']],list(finish.ORDER))
            for row in state['completed']:
                ref=row['reference'];run=Path(ref['run'])
                self.assertEqual(finish.common.sha(run/'summary.json'),ref['sha256'])
                receipt=json.loads((run.parent/'state.json').read_text())
                self.assertEqual(next(iter(receipt['stages'].values()))['status'],'passed')
            ledger.acquire.assert_called_once();ledger.release.assert_called_once()

    def test_failure_stops_successors_and_does_not_schedule_synthesis(self):
        seen=[]
        def stage(name,*args):
            seen.append(name)
            if name=='saif':raise RuntimeError('Actual activity failed')
            return {'run':name,'sha256':'a'*64}
        with patch.object(finish,'run_stage',side_effect=stage):
            with self.assertRaisesRegex(RuntimeError,'activity failed'):
                finish.sequence({},None,{},None,{})
        self.assertEqual(seen,['structure','gate','saif'])

    def test_twelve_power_stages_follow_the_same_new_activity(self):
        seen=[]
        def stage(name,cfg,queue,state,ledger,request,refs):
            seen.append(name)
            if name=='saif':self.assertEqual(refs['gate']['run'],'gate')
            if name.startswith('power_'):self.assertEqual(refs['saif']['run'],'saif')
            return {'run':name,'sha256':'a'*64}
        with patch.object(finish,'run_stage',side_effect=stage):
            result=finish.sequence({},None,{},None,{})
        self.assertEqual(len(result),17)
        self.assertEqual(seen[-12:],['power_layer_%02d'%i for i in range(1,13)])
        self.assertNotIn('synth',seen)
        self.assertNotIn('batch100',seen)


if __name__=='__main__':unittest.main()
