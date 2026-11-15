"""Small evidence fixtures, not simulated hardware or a stage PASS."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

import p80_model_review_snapshot as tool
from test_mmio8_timing_objects import clocks, DISABLED, SDC
from mmio8_timing_objects import DTM


def save(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value));return tool.digest(path)


def fixture(root,control_pin='D',disabled=DISABLED):
    synth=root/'synth/p80_synth';synth.mkdir(parents=True)
    (synth/'mapped.v').write_text('module e203_soc_top; endmodule\n')
    (synth/'mapped.sdc').write_text(SDC)
    area=dict(units='um^2',conservative_budget_mm2=0.95)
    # Actual DC metrics are decimal/count strings, not Python numbers.
    metrics=dict(period_ns='6.666666000000',max='0.001',min='0.002',latches='0')
    summary=dict(scope='p80_partitioned_whole_soc_task_mode',synthesis_completed=True,
        project_limit_mm2=1.0,transaction_metadata_depth=2,old_linked_ddc_reused=False,block_cache_reused=False,
        link_report=dict(schema='arch03-p80-fresh-link-v1',row_lanes=5,transaction_metadata_depth=2),
        metrics=metrics,area_summary=area,artifacts={'mapped.sdc':tool.digest(synth/'mapped.sdc')})
    sr=dict(run=str(synth),sha256=save(synth/'summary.json',summary));powers=[]
    for index in range(1,13):
        run=root/('power_%02d'%index)/'p80_power';run.mkdir(parents=True)
        (run/'timing_check.rpt').write_text(clocks([DTM+'valid_reg/CK']))
        (run/'disabled_timing.rpt').write_text(disabled)
        summary=dict(case='layer_%02d'%index,synthesis_summary_sha256=sr['sha256'],
            activity_summary_sha256='b'*64,power_clock=dict(measured=dict(hf_period_ns='6.666666',lf_period_ns='66')),
            artifacts={n:tool.digest(run/n) for n in ('timing_check.rpt','disabled_timing.rpt')})
        digest=save(run/'summary.json',summary)
        save(run.parent/'state.json',dict(stages=dict(p80_power=dict(status='passed',summary_sha256=digest))))
        powers.append(dict(run=str(run),sha256=digest))
    report=dict(schema='arch03-p80-evidence-export-v1',stage='P80',row_lanes=5,numeric_format='0x000e0c20',
        layout_id=0x00100004,shift=10,transaction_metadata_depth=2,synthesis_route=dict(scope='p80_partitioned_whole_soc_task_mode',partition_area={},old_linked_ddc_reused=False,block_cache_reused=False),
        verification={key:True for key in ('asic14','gate14_without_SDF','final240','activity12','power12_numbers',
            'internal20_precision_verified','fixed12_precision_verified')},references=dict(synthesis=sr),
        timing_metrics=metrics,area=area,drc_inventory=dict(explicit_no_violations=True,extraction_complete=True,violation_record_count=0),
        power_references=powers,activity_reference=dict(sha256='b'*64),netlist_sha256=tool.digest(synth/'mapped.v'),aggregate={})
    rp=root/'report.json';report_sha=save(rp,report)
    linked=root/'connections/p80_unknown_p80';linked.mkdir(parents=True)
    proof=linked/'unknown_connections.tsv';proof.write_text('endpoint\tnet\ttop/reg/'+control_pin+'\tpin\tin\tDFQ\n')
    lp=linked/'summary.json';ld=save(lp,dict(name='P80',targets=1,resolved=0,unresolved=['missing'],
        input_files={str(synth/'mapped.v'):tool.digest(synth/'mapped.v')},proof_sha256=tool.digest(proof)))
    save(linked.parent/'state.json',dict(status='connections_collected_review_required',
        stages=dict(p80_unknown_p80=dict(status='passed',summary_sha256=ld))))
    ap=root/'aliases.json';ad=save(ap,dict(inputs_sha256={str(lp):ld},complete_target_count=1,
        counts={'absent_DDC_net_and_no_local_expression':1}))
    return dict(schema='p80-model-review-request-v1',report=dict(path=str(rp),sha256=report_sha),
        connections=dict(path=str(lp),sha256=ld),aliases=dict(path=str(ap),sha256=ad))


class SnapshotTests(unittest.TestCase):
    def test_real_frozen_files_and_no_implicit_acceptance(self):
        with tempfile.TemporaryDirectory() as tmp:
            request=fixture(Path(tmp));result=tool.snapshot(request)
            self.assertEqual(len(result['power_timing_scope']),12)
            self.assertEqual(result['unknown_review']['unknown_explicit_control_pins'],[])
            self.assertFalse(result['stage_accepted']);self.assertFalse(result['system_power_verified'])
            self.assertTrue(all(tool.digest(path)==want for path,want in result['inputs_sha256'].items()))

    def test_incomplete_mixed_or_modified_evidence_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            original=fixture(Path(tmp));rp=Path(original['report']['path']);report=json.loads(rp.read_text())
            cases=[]
            changed=copy.deepcopy(report);changed['verification']['final240']=False;cases.append(changed)
            changed=copy.deepcopy(report);changed['timing_metrics']['max']=-0.01;cases.append(changed)
            changed=copy.deepcopy(report);changed['area']['conservative_budget_mm2']=1.01;cases.append(changed)
            changed=copy.deepcopy(report);changed['power_references'][-1]=changed['power_references'][0];cases.append(changed)
            changed=copy.deepcopy(report);changed['netlist_sha256']='0'*64;cases.append(changed)
            for index,bad in enumerate(cases):
                req=copy.deepcopy(original);req['report']['sha256']=save(rp,bad)
                with self.subTest(case=index),self.assertRaises(ValueError):tool.snapshot(req)
            req=copy.deepcopy(original);req['report']['sha256']=save(rp,report)
            path=Path(report['power_references'][0]['run'])/'timing_check.rpt'
            path.write_text(path.read_text().replace('valid_reg','changed_reg'))
            with self.assertRaises(ValueError):tool.snapshot(req)

    def test_unknown_clock_and_loop_cut_do_not_get_waived(self):
        for options in (dict(control_pin='CK'),dict(disabled=DISABLED.replace('positive_unate p','positive_unate l'))):
            with self.subTest(options=options),tempfile.TemporaryDirectory() as tmp:
                request=fixture(Path(tmp),**options)
                with self.assertRaises(ValueError):tool.snapshot(request)


if __name__=='__main__':unittest.main()
