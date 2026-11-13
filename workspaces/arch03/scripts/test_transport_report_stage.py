import copy
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
import transport_report_stage as report


class CompletedQueueContract(unittest.TestCase):
    def test_unknown_inventory_accepts_files_only_inside_registered_stages(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory).resolve();stage=root/'runs'/'session'/'t80_saif'
            stage.mkdir(parents=True);wave=stage/'layer_01.saif';wave.write_bytes(b'fixture')
            outside=root/'other.saif';outside.write_bytes(b'not registered')
            def allowed(path,cfg,label):
                if path!=stage:raise ValueError('Unregistered stage')
                return path
            paths=SimpleNamespace(allowed_run=allowed)
            self.assertEqual(report.evidence_path(stage,paths,{}),stage)
            self.assertEqual(report.evidence_path(wave,paths,{}),wave)
            with self.assertRaises(ValueError):report.evidence_path(outside,paths,{})

    def test_queue_is_session_not_stage_and_cannot_escape_bundle(self):
        with tempfile.TemporaryDirectory() as directory:
            bundle=Path(directory).resolve()/'bundle'
            queue=bundle/'runs'/'t80_finish03'
            queue.mkdir(parents=True)
            self.assertEqual(report.verify_queue_path(queue,bundle),queue)
            stage=queue/'t80_saif';stage.mkdir()
            foreign=Path(directory).resolve()/'foreign'/'runs'/'t80_finish03'
            foreign.mkdir(parents=True)
            for rejected in (stage,foreign,queue.parent,queue.parent/'missing'):
                with self.assertRaises(ValueError):report.verify_queue_path(rejected,bundle)

    def queue(self, stage):
        names=('contention','sequence','synth','timing_audit','drc_audit','structure','gate','saif','precision')
        records=[dict(stage=stage.lower()+'_'+name,reference=dict(run='/run/'+name,sha256='a'*64))
                 for name in names]
        records += [dict(stage=stage.lower()+'_power',reference=dict(run='/power/'+str(i),sha256='b'*64))
                    for i in range(12)]
        return dict(status='reports_ready_review_required',child_pid=None,completed=records)

    def test_own_complete_queue_and_no_predecessor_pass(self):
        for stage,other in (('T80','T64'),('T64','T80')):
            state=self.queue(stage)
            self.assertEqual(len(report.completed_references(state,stage)[stage.lower()+'_power']),12)
            with self.assertRaises(ValueError):report.completed_references(state,other)
            for field,value in (('status','running'),('status','failed'),('child_pid',44)):
                changed=copy.deepcopy(state);changed[field]=value
                with self.assertRaises(ValueError):report.completed_references(changed,stage)

    def test_missing_and_extra_measurements_rejected(self):
        for amount in (-1,1):
            state=self.queue('T64')
            if amount<0:state['completed'].pop()
            else:state['completed'].append(copy.deepcopy(state['completed'][-1]))
            with self.assertRaises(ValueError):report.completed_references(state,'T64')


if __name__=='__main__':unittest.main()
