"""Continuation must never accept unfinished or unrelated functional evidence."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import systolic_b_power_queue as p


class ContinuationTests(unittest.TestCase):
    def fixture(self,root):
        (root/'manifest.json').write_text('{}')
        refs={k:dict(run=str(root/k),sha256=str(i)*64) for i,k in enumerate(['asic','batch','gate','synthesis'],1)}
        reports=dict(asic=dict(compile_receipt=dict(firmware_manifest_sha256='f'*64)),
            batch=dict(status='passed',tasks=1200,checked_outputs=30412800,failed=0,
                       compile_receipt=dict(firmware_manifest_sha256='f'*64)),
            gate=dict(synthesis_summary_sha256=refs['synthesis']['sha256'],firmware_sha256='f'*64),synthesis={})
        report=dict(schema='systolic-b-report-request-v1',power=[],history=[],**refs)
        rp=root/'report_request.json';rp.write_text(json.dumps(report))
        queue=dict(status='reports_ready_review_required',child_pid=None,report_request_sha256=p.sha(rp),
            completed=[dict(stage='systolic_b_soc',reference=copy.deepcopy(refs['asic'])),dict(stage='systolic_b_batch',reference=copy.deepcopy(refs['batch']))])
        qp=root/'state.json';qp.write_text(json.dumps(queue))
        request=dict(schema='systolic-b-power-continuation-v1',runner_sha256=p.sha(p.__file__),
            bundle_manifest_sha256=p.sha(root/'manifest.json'),functional_queue=dict(path=str(qp),sha256=p.sha(qp)),
            report_request=dict(path=str(rp),sha256=p.sha(rp)),qualification=dict(run='qualified',sha256='e'*64))
        return request,reports,report,queue

    def check(self,root,request,reports):
        with patch.object(p,'ROOT',root),patch.object(p,'checked_operations',return_value=(root,'a'*64)),\
             patch.object(p,'qualification') as method,patch('icb32_report.configuration_identity',return_value={'rtl':'same'}),\
             patch.object(p,'stage',side_effect=lambda ref,kind:reports[Path(ref['run']).name]):
            result=p.preflight(request,dict(server_root=str(root)))
            method.assert_called_once()
            return result

    def test_reuses_completed_evidence_without_starting_any_child(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);request,reports,report,_=self.fixture(root)
            with patch.object(p.subprocess,'Popen') as spawn:
                self.assertEqual(self.check(root,request,reports),report)
                spawn.assert_not_called()

    def test_rejects_partial_batch_changed_firmware_and_active_queue(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);request,reports,report,queue=self.fixture(root)
            bad=copy.deepcopy(reports);bad['batch']['tasks']=1199
            with self.assertRaisesRegex(ValueError,'Own1200'):self.check(root,request,bad)
            bad=copy.deepcopy(reports);bad['gate']['firmware_sha256']='0'*64
            with self.assertRaisesRegex(ValueError,'firmware'):self.check(root,request,bad)
            queue['status']='running';qp=root/'state.json';qp.write_text(json.dumps(queue))
            request['functional_queue']['sha256']=p.sha(qp)
            with self.assertRaisesRegex(ValueError,'incomplete'):self.check(root,request,reports)

    def test_request_cannot_rebind_another_batch_or_mutate_existing_report(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);request,reports,report,queue=self.fixture(root)
            report['batch']['sha256']='0'*64;rp=root/'report_request.json';rp.write_text(json.dumps(report))
            request['report_request']['sha256']=p.sha(rp);queue['report_request_sha256']=p.sha(rp)
            qp=root/'state.json';qp.write_text(json.dumps(queue));request['functional_queue']['sha256']=p.sha(qp)
            with self.assertRaisesRegex(ValueError,'completed functional children'):self.check(root,request,reports)


if __name__=='__main__':unittest.main()
