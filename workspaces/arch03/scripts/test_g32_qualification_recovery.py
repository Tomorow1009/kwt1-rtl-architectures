import json
from pathlib import Path
import tempfile
import unittest
import g32_qualification_recovery as r


def save(p,value):
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(value));return r.digest(p)


def fixture(root):
    q=root/'runs/g32_initial01';q.mkdir(parents=True);rows=[]
    for name in r.PRIOR_ORDER:
        run=q.with_name(q.name+'_'+name)/('g32_'+name)
        h=save(run/'summary.json',dict(stage=name))
        save(run.parent/'state.json',dict(stages={'g32_'+name:dict(status='passed',run=str(run),
            finished='time',summary_sha256=h)}))
        rows.append(dict(stage=name,reference=dict(run=str(run),sha256=h)))
    run=q.with_name(q.name+'_icg')/'g32_icg';run.mkdir(parents=True);log=run/'clock_gating.log'
    log.write_text("Error: Unknown attribute 'name'. (FLT-005)\nError: while parsing filter expression:\nError: G32_CLOCK_GATING_ABORT ICG enable pin mismatch\n")
    save(run.parent/'state.json',dict(stages={'g32_icg':dict(status='failed',run=str(run),finished='time')}))
    for i in range(5):
        save(q/'process_ledger'/('child_%06d.json'%i),dict(driver_pid=123,bundle=str(root),session=q.name,
            status='exited',wait_completed=True,pid=1000+i,returncode=1 if i==4 else 0,
            call_status='failed' if i==4 else 'passed',log=str(log) if i==4 else 'prior'))
    save(q/'request.json',{})
    h=save(q/'state.json',dict(status='failed',stage='icg',finished='time',pid=123,completed=rows,
        error='Tool failed '+str(log)+' exit=1'))
    return dict(queue=str(q),state_sha256=h),q,log


class RecoveryIdentity(unittest.TestCase):
    def test_only_same_four_passed_stages_reused(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);ref,q,_=fixture(root);proof=r.predecessor(ref,root,lambda pid:False)
            self.assertEqual(list(proof['references']),list(r.PRIOR_ORDER))
            self.assertFalse(proof['stage_accepted']);self.assertTrue(proof['original_failure_preserved'])
            self.assertEqual(r.digest(q/'state.json'),ref['state_sha256'])

    def test_live_or_changed_evidence_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);ref,q,_=fixture(root)
            with self.assertRaisesRegex(ValueError,'exited predecessor'):
                r.predecessor(ref,root,lambda pid:pid==123)
            with self.assertRaisesRegex(ValueError,'Original child still active'):
                r.predecessor(ref,root,lambda pid:pid==1004)
            (q.with_name(q.name+'_synth')/'g32_synth/summary.json').write_text('{}')
            with self.assertRaisesRegex(ValueError,'successful stage changed'):
                r.predecessor(ref,root,lambda pid:False)

    def test_other_tool_failure_or_previous_batch_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);ref,q,log=fixture(root)
            log.write_text(log.read_text()+'Error: missing clock\n')
            with self.assertRaisesRegex(ValueError,'limited to the observed'):
                r.predecessor(ref,root,lambda pid:False)
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);ref,q,_=fixture(root);q.with_name(q.name+'_batch20').mkdir()
            with self.assertRaisesRegex(ValueError,'Old batch already started'):
                r.predecessor(ref,root,lambda pid:False)


if __name__=='__main__':unittest.main()
