import json
from pathlib import Path
import tempfile
import unittest
from test_g32_qualification_recovery import fixture,save
import g32_recovery_contract as c


def completed(root):
    ref,old,_=fixture(root);runtime=root.parent;ops=runtime/'ops';ops.mkdir()
    scripts=root/'workspaces/arch03/scripts';scripts.mkdir(parents=True)
    (scripts/'g32_qualification.py').write_text('original coordinator')
    text='name == E\nname == TE\nname == E\n';(scripts/'g32_icg_timing.py').write_text(text)
    (ops/'g32_icg_timing_pt2022.py').write_text(text.replace('name == E','full_name =~ */E').replace('name == TE','full_name =~ */TE'))
    (ops/'g32_qualification_recovery.py').write_text('new coordinator')
    manifest=save(ops/'manifest.json',dict(files={p.name:c.digest(p) for p in ops.iterdir()}))
    bundle_sha=save(root/'manifest.json',{})
    original=dict(schema='g32-qualification-v1',bundle=str(root),bundle_manifest_sha256=bundle_sha,
        queue_sha256=c.digest(scripts/'g32_qualification.py'),runtime_root=str(runtime),platform='p',dataset='d',
        float_archive='f',float_archive_sha256='f'*64,baseline={})
    save(old/'request.json',original)
    prior=c.predecessor(ref,root,lambda pid:False)
    queue=root/'runs/g32_recovery01';queue.mkdir()
    save(queue/'predecessor_proof.json',prior)
    request=dict(original,schema=c.SCHEMA,queue_sha256=c.digest(ops/'g32_qualification_recovery.py'),
        operations_root=str(ops),operations_manifest_sha256=manifest,predecessor=ref)
    request_sha=save(queue/'request.json',request);save(runtime/'g32_recovery01_request.json',request)
    rows=[]
    for name in c.ORDER:
        run=queue.with_name(queue.name+'_'+name)/('g32_'+name);h=save(run/'summary.json',dict(stage=name))
        save(run.parent/'state.json',dict(stages={'g32_'+name:dict(status='passed',finished='time',
            run=str(run),summary_sha256=h)}));rows.append(dict(stage=name,reference=dict(run=str(run),sha256=h)))
    save(queue/'process_ledger/child_000001.json',dict(driver_pid=200,bundle=str(root),session=queue.name,
        status='exited',wait_completed=True,returncode=0,call_status='passed',pid=201))
    h=save(queue/'state.json',dict(schema=c.SCHEMA,status='qualification_recovered_gate_power_pending',
        finished='time',pid=200,completed=rows,predecessor=ref))
    save(runtime/'g32_recovery01_launch.json',dict(pid=200,request_sha256=request_sha,
        initial_state_sha256=ref['state_sha256'],operations_manifest_sha256=manifest,bundle_manifest_sha256=bundle_sha))
    return old,ref['state_sha256'],queue,h


class RecoveryChain(unittest.TestCase):
    def test_preserves_failed_state_and_joins_only_own_three_stages(self):
        with tempfile.TemporaryDirectory() as d:
            args=completed(Path(d)/'bundle');p=c.recovered_initial(*args,alive=lambda pid:False)
            self.assertEqual(p['state']['status'],'failed')
            self.assertEqual(list(p['references']),list(c.PRIOR_ORDER)+list(c.ORDER))
            self.assertFalse(p['stage_accepted']);self.assertFalse(p['archive_implies_acceptance'])
            self.assertEqual(c.digest(args[0]/'state.json'),args[1])

    def test_rejects_live_recovery_or_child_and_changed_result(self):
        for pid in (200,201):
            with tempfile.TemporaryDirectory() as d:
                args=completed(Path(d)/'bundle')
                with self.assertRaises(ValueError):c.recovered_initial(*args,alive=lambda x:x==pid)
        with tempfile.TemporaryDirectory() as d:
            args=completed(Path(d)/'bundle');q=args[2]
            (q.with_name(q.name+'_icg')/'g32_icg/summary.json').write_text('{}')
            with self.assertRaisesRegex(ValueError,'summary changed'):c.recovered_initial(*args,alive=lambda pid:False)

    def test_rejects_changed_pin_patch_even_when_manifest_recomputed(self):
        with tempfile.TemporaryDirectory() as d:
            args=list(completed(Path(d)/'bundle'));q=args[2];r=c.read(q/'request.json');ops=Path(r['operations_root'])
            (ops/'g32_icg_timing_pt2022.py').write_text('disable all checks')
            m=c.read(ops/'manifest.json');m['files']['g32_icg_timing_pt2022.py']=c.digest(ops/'g32_icg_timing_pt2022.py')
            r['operations_manifest_sha256']=save(ops/'manifest.json',m);save(q/'request.json',r)
            with self.assertRaisesRegex(ValueError,'three pin-query corrections'):c.recovered_initial(*args,alive=lambda pid:False)


if __name__=='__main__':unittest.main()
