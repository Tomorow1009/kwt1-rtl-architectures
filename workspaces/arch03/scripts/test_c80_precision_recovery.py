"""Only a missing import may reuse this same C80 hardware chain for precision."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import c80_precision_recovery as p
import c80_archive_contract as archive
from test_c80_archive_contract import fixture,save


def failed(root):
    a=fixture(root,'initial');queue=Path(a['queue']);state=a['state']
    state.update(status='failed',stage='precision',error=p.ERROR)
    last=state['completed'].pop();run=Path(last['reference']['run'])
    (run/'summary.json').unlink()
    save(run.parent/'state.json',dict(stages={'c80_precision':dict(status='failed',error=p.ERROR,
        finished='time',run=str(run))}))
    source=root/'workspaces/arch03/scripts/c80_qualification.py';source.parent.mkdir(parents=True);source.write_text('# fixture')
    mf=save(root/'manifest.json',dict(files={}))
    request=dict(schema='c80-qualification-v1',bundle=str(root),bundle_manifest_sha256=mf,
        queue_sha256=p.digest(source))
    request_sha=save(queue/'request.json',request)
    save(queue/'process_ledger/child_000001.json',dict(driver_pid=123,pid=125,bundle=str(root),session=queue.name,
        status='exited',wait_completed=True,returncode=0,call_status='passed'))
    return dict(queue=str(queue),state_sha256=save(queue/'state.json',state),request_sha256=request_sha)


def recovered(root,previous):
    fresh=root/'runs/recovery';run=root/'runs/recovery_precision/c80_precision'
    proof=p.predecessor(previous,root,lambda pid:False)
    r=dict(run=str(run),sha256=save(run/'summary.json',dict(schema='arch03-c80-first20-precision-join-v1',
        fresh_float_reference_verified=True,batch={'batch_summary_sha256':proof['references']['batch20']['sha256']})))
    save(run.parent/'state.json',dict(stages={'c80_precision':dict(status='passed',finished='time',run=str(run),summary_sha256=r['sha256'])}))
    request=dict(schema=p.SCHEMA,bundle=str(root),recovery_sha256=p.digest(p.__file__),predecessor=previous)
    request_sha=save(fresh/'request.json',request)
    state=dict(schema=p.SCHEMA,status='precision_recovered_review_required',finished='time',pid=126,
        predecessor=previous,completed=[dict(stage='precision',reference=r)])
    save(fresh/'numeric_runtime.json',{'fixture':True});save(fresh/'predecessor_proof.json',proof)
    return dict(queue=str(fresh),state_sha256=save(fresh/'state.json',state),request_sha256=request_sha)


class Recovery(unittest.TestCase):
    def test_only_precise_failure_and_five_passes_are_reused(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);ref=failed(root);proof=p.predecessor(ref,root,lambda pid:False)
            self.assertEqual(list(proof['references']),list(p.qualification.ORDER[:-1]))
            self.assertEqual(proof['state']['status'],'failed');self.assertFalse(proof['stage_accepted'])
            with self.assertRaisesRegex(ValueError,'exited missing'):
                p.predecessor(ref,root,lambda pid:pid==123)
            with self.assertRaisesRegex(ValueError,'child still active'):
                p.predecessor(ref,root,lambda pid:pid==125)
            path=Path(ref['queue'])/'state.json';state=json.loads(path.read_text());state['error']='numerical mismatch'
            ref['state_sha256']=save(path,state)
            with self.assertRaisesRegex(ValueError,'missing-NumPy'):p.predecessor(ref,root,lambda pid:False)

    def test_changed_inputs_incomplete_stages_or_partial_precision_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);ref=failed(root);queue=Path(ref['queue']);path=queue/'state.json'
            state=json.loads(path.read_text());saved=dict(state);state['completed']=state['completed'][:-1]
            ref['state_sha256']=save(path,state)
            with self.assertRaisesRegex(ValueError,'all five'):p.predecessor(ref,root,lambda pid:False)
            ref['state_sha256']=save(path,saved)
            partial=root/'runs/initial_precision/c80_precision/float20';partial.mkdir()
            with self.assertRaisesRegex(ValueError,'confined'):p.predecessor(ref,root,lambda pid:False)

    def test_archive_binds_retry_and_preserves_failed_original(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);old=failed(root);fresh=recovered(root,old)
            a=archive.recovered_initial(old['queue'],old['state_sha256'],fresh,lambda pid:False)
            self.assertEqual(len(a['references']),6);self.assertEqual(a['state']['status'],'failed')
            self.assertTrue(a['original_failed_state_preserved'])
            with self.assertRaisesRegex(ValueError,'complete and exit'):
                archive.recovered_initial(old['queue'],old['state_sha256'],fresh,lambda pid:pid==126)
            path=Path(fresh['queue'])/'request.json';request=json.loads(path.read_text());request['recovery_sha256']='0'*64
            fresh['request_sha256']=save(path,request)
            with self.assertRaisesRegex(ValueError,'recovery source'):
                archive.recovered_initial(old['queue'],old['state_sha256'],fresh,lambda pid:False)

    def test_wrong_tool_hash_rejected_before_state_or_lock(self):
        with tempfile.TemporaryDirectory() as d:
            q=Path(d)/'runs/new'
            with self.assertRaisesRegex(ValueError,'recovery source'):
                p.execute(dict(schema=p.SCHEMA,recovery_sha256='0'*64),q)
            self.assertFalse(q.exists())


if __name__=='__main__':unittest.main()
