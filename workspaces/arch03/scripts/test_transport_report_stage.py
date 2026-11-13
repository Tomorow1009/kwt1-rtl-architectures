import copy
import unittest
import transport_report_stage as report


class CompletedQueueContract(unittest.TestCase):
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
