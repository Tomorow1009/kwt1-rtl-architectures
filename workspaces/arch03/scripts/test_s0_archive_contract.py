import json
from pathlib import Path
import tempfile
import unittest

import s0_archive_contract as contract


class S0ArchiveIdentity(unittest.TestCase):
    def fixture(self,root):
        queue=root/'runs/finish';queue.mkdir(parents=True)
        rows=[]
        for name in contract.ORDER:
            kind='power' if name.startswith('power_') else name
            run=queue.with_name(queue.name+'_'+name)/('t80_s0_'+kind);run.mkdir(parents=True)
            (run/'summary.json').write_text(json.dumps(dict(stage=name)))
            sha=contract.digest(run/'summary.json')
            receipt=dict(stages={'t80_'+kind:dict(status='passed',finished='time',run=str(run),summary_sha256=sha)})
            (run.parent/'state.json').write_text(json.dumps(receipt))
            rows.append(dict(stage=name,reference=dict(run=str(run),sha256=sha)))
        state=dict(status='reports_ready_review_required',pid=123,finished='time',completed=rows,
                   synthesis=dict(run='new_netlist',sha256='a'*64))
        (queue/'state.json').write_text(json.dumps(state))
        return queue,state

    def test_all_s0_stage_paths_and_same_queue_export(self):
        with tempfile.TemporaryDirectory() as d:
            queue,state=self.fixture(Path(d));sha=contract.digest(queue/'state.json')
            proof=contract.completed_queue(queue,sha,lambda pid:False)
            self.assertEqual(len(proof['references']),17);self.assertFalse(proof['stage_accepted'])
            run=queue.parent/'export/t80_s0_report';run.mkdir(parents=True);refs=proof['references']
            report=dict(schema='arch03-s0-evidence-export-v1',stage='S0',
                references=dict(synthesis=state['synthesis'],gate=refs['gate']),activity_reference=refs['saif'],
                power_references=[refs['power_'+n] for n in contract.LAYERS])
            (run/'report.json').write_text(json.dumps(report));want=contract.digest(run/'report.json')
            (run/'receipt.json').write_text(json.dumps(dict(schema='arch03-s0-export-receipt-v1',artifacts={'report.json':want})))
            result=contract.exported_report(run,want,proof);self.assertFalse(result['archive_implies_acceptance'])
            report['references']['gate']=dict(run='older_gate',sha256='b'*64)
            (run/'report.json').write_text(json.dumps(report))
            with self.assertRaisesRegex(ValueError,'another netlist or queue'):
                contract.exported_report(run,contract.digest(run/'report.json'),proof)

    def test_live_incomplete_and_changed_stages_cannot_be_archived_as_complete(self):
        with tempfile.TemporaryDirectory() as d:
            queue,state=self.fixture(Path(d));sha=contract.digest(queue/'state.json')
            with self.assertRaisesRegex(ValueError,'terminal exited'):
                contract.completed_queue(queue,sha,lambda pid:True)
            ref=state['completed'][-1]['reference'];Path(ref['run'],'summary.json').write_text('changed')
            with self.assertRaisesRegex(ValueError,'summary changed'):
                contract.completed_queue(queue,sha,lambda pid:False)
            state['completed'].pop();(queue/'state.json').write_text(json.dumps(state))
            with self.assertRaisesRegex(ValueError,'all 17'):
                contract.completed_queue(queue,contract.digest(queue/'state.json'),lambda pid:False)


if __name__=='__main__':unittest.main()
