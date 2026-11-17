"""Archive both G32 queues without accepting live, mixed, or changed evidence."""
import json
from pathlib import Path
import tempfile
import unittest
import g32_archive_contract as c


def save(path,value):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value));return c.digest(path)


def fixture(root,role):
    queue=root/'runs'/role;queue.mkdir(parents=True)
    order=c.INITIAL_ORDER if role=='initial' else c.FINISH_ORDER;rows=[]
    for name in order:
        kind='power' if name.startswith('power_') else name
        run=queue.with_name(queue.name+'_'+name)/('g32_'+kind)
        summary=dict(stage=name)
        if name=='synth':summary.update(artifacts={'mapped.v':'d'*64},icg_mapping={'actual_g32_cells':123})
        if name=='icg':
            synth=next(x['reference'] for x in rows if x['stage']=='synth')
            summary.update(schema='g32-clock-gating-timing-v1',synthesis_summary_sha256=synth['sha256'],
                netlist_sha256='d'*64,actual_g32_cells=123,static_TE_zero=True,
                enable_path_setup_hold_nonnegative=True,setup_slack_ns=0.2,hold_slack_ns=0.1)
        if name=='precision':summary.update(fresh_float_reference_verified=True,
            reference=dict(run=str(run/'float20'),sha256='c'*64),
            batch=dict(batch_summary_sha256=next(x['reference']['sha256'] for x in rows if x['stage']=='batch20')))
        digest=save(run/'summary.json',summary)
        save(run.parent/'state.json',dict(stages={'g32_'+kind:dict(status='passed',finished='time',
            run=str(run),summary_sha256=digest)}))
        rows.append(dict(stage=name,reference=dict(run=str(run),sha256=digest)))
    state=dict(status='qualification_ready_gate_power_pending' if role=='initial' else 'reports_ready_review_required',
        pid=123 if role=='initial' else 124,finished='time',completed=rows)
    if role=='finish':
        p=root/'runs/initial/state.json';prior=json.loads(p.read_text())
        state['synthesis']=next(r['reference'] for r in prior['completed'] if r['stage']=='synth')
    digest=save(queue/'state.json',state)
    return c.completed_queue(queue,digest,lambda pid:False,role)


def export(root,proof):
    initial=proof['initial']['references'];finish=proof['finish']['references']
    run=root/'runs/export/g32_report'
    report=dict(schema='arch03-g32-evidence-export-v1',stage='G32',layout_id=0x00100006,numeric_format='0x000e0c20',
        references=dict(asic=initial['soc'],synthesis=initial['synth'],gate=finish['gate']),
        activity_reference=finish['saif'],power_references=[finish['power_'+n] for n in c.LAYERS],
        batch_reference=initial['batch20'],precision_reference=json.loads(
            (Path(initial['precision']['run'])/'summary.json').read_text())['reference'])
    digest=save(run/'report.json',report)
    save(run/'receipt.json',dict(schema='arch03-g32-export-receipt-v1',artifacts={'report.json':digest}))
    return run,digest,report


class ArchiveIdentity(unittest.TestCase):
    def test_gating_must_bind_same_netlist_and_have_real_checks(self):
        for field,value in [('netlist_sha256','e'*64),('static_TE_zero',False),
                            ('actual_g32_cells',0),('hold_slack_ns',-0.01)]:
            with tempfile.TemporaryDirectory() as d:
                root=Path(d);a=fixture(root,'initial');b=fixture(root,'finish')
                p=Path(a['references']['icg']['run'])/'summary.json'
                row=json.loads(p.read_text());row[field]=value
                a['references']['icg']['sha256']=save(p,row)
                with self.assertRaisesRegex(ValueError,'own-netlist complete clock-gating'):
                    c.joined_queues(a,b)

    def test_both_queues_and_own_export_no_implicit_acceptance(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);a=fixture(root,'initial');b=fixture(root,'finish');proof=c.joined_queues(a,b)
            self.assertEqual(len(a['references']),7);self.assertEqual(len(b['references']),17)
            run,digest,_=export(root,proof);result=c.exported_report(run,digest,proof)
            self.assertFalse(result['stage_accepted']);self.assertFalse(result['archive_implies_acceptance'])

    def test_missing_or_live_queues_and_changed_summaries_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            a=fixture(Path(d),'initial');queue=Path(a['queue']);path=queue/'state.json';digest=c.digest(path)
            with self.assertRaisesRegex(ValueError,'terminal exited'):
                c.completed_queue(queue,digest,lambda pid:True,'initial')
            state=a['state'];state['completed'].pop();save(path,state)
            with self.assertRaisesRegex(ValueError,'every stage'):
                c.completed_queue(queue,c.digest(path),lambda pid:False,'initial')
        with tempfile.TemporaryDirectory() as d:
            a=fixture(Path(d),'initial');queue=Path(a['queue']);ref=a['references']['soc']
            (Path(ref['run'])/'summary.json').write_text('modified')
            with self.assertRaisesRegex(ValueError,'summary changed'):
                c.completed_queue(queue,c.digest(queue/'state.json'),lambda pid:False,'initial')

    def test_wrong_mapped_design_and_predecessor_or_batch_export_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);a=fixture(root,'initial');b=fixture(root,'finish')
            own=b['state']['synthesis'];b['state']['synthesis']={'run':'older','sha256':'a'*64}
            with self.assertRaisesRegex(ValueError,'qualification netlist'):c.joined_queues(a,b)
            b['state']['synthesis']=own;proof=c.joined_queues(a,b);run,digest,report=export(root,proof)
            report['batch_reference']={'run':'P80 batch','sha256':'a'*64}
            want=save(run/'report.json',report)
            with self.assertRaisesRegex(ValueError,'another netlist, batch or queue'):
                c.exported_report(run,want,proof)
            report['schema']='arch03-p80-evidence-export-v1';want=save(run/'report.json',report)
            with self.assertRaisesRegex(ValueError,'layout6'):c.exported_report(run,want,proof)


if __name__=='__main__':unittest.main()
