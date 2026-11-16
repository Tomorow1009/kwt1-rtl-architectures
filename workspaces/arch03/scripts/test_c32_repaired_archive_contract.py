import copy
from pathlib import Path
import tempfile
import unittest

import c32_archive_contract as old
import c32_repaired_archive_contract as c
import c32_mapped_repair as repair
from test_c32_archive_contract import fixture,save,export


def setup(root):
    a=fixture(root/'original','initial')
    fixture(root/'repaired','initial');b=fixture(root/'repaired','finish')
    a['references']['synth']['sha256']=repair.ORIGIN_SHA
    route=dict(scope=repair.SCOPE,old_linked_ddc_reused=True,block_cache_reused=True,
        mapped_repair=dict(schema='c32-equivalent-cell-repair-v1',original_run=a['references']['synth']['run'],
            original_summary_sha256=repair.ORIGIN_SHA,original_netlist_sha256=repair.ORIGIN_NETLIST,
            original_scope='c32_partitioned_whole_soc_task_mode',
            targets={k:list(v) for k,v in repair.TARGETS.items()},rtl_modified=False,topology_changed=False,
            task_constraints_unchanged=True,inherited_gate_pass=False,requires_new_gate_and_ppa=True,only_size_cell_no_compile=True),
        repair_identity=dict(schema='c32-equivalent-driver-token-proof-v2',all_other_verilog_tokens_identical=True,
            leaf_identity=dict(all_other_leaves_identical=True)))
    p=root/'repaired/runs/repair/c32_synth/summary.json';h=save(p,route)
    b['state']['synthesis']=dict(run=str(p.parent),sha256=h)
    return a,b,route


class RepairedArchive(unittest.TestCase):
    def test_explicit_join_preserves_old_strict_route(self):
        with tempfile.TemporaryDirectory() as d:
            a,b,s=setup(Path(d));proof=c.joined_repair(a,b,s)
            self.assertFalse(proof['archive_implies_acceptance'])
            self.assertFalse(proof['old_gate_or_power_reused'])
            with self.assertRaises(ValueError):old.joined_queues(a,b)

    def test_another_qualification_or_false_fresh_repair_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            a,b,s=setup(Path(d));changed=copy.deepcopy(a);changed['references']['synth']['sha256']='0'*64
            with self.assertRaisesRegex(ValueError,'derive'):c.joined_repair(changed,b,s)
            s['old_linked_ddc_reused']=False
            b['state']['synthesis']['sha256']=save(Path(b['state']['synthesis']['run'])/'summary.json',s)
            with self.assertRaisesRegex(ValueError,'explicit'):c.joined_repair(a,b,s)

    def test_changed_report_and_old_netlist_activity_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);a,b,s=setup(root);proof=c.joined_repair(a,b,s)
            run,_,report=export(root/'repaired',proof)
            report['references']['synthesis']=proof['synthesis'];report['synthesis_route']=s
            def write():
                h=save(run/'report.json',report)
                save(run/'receipt.json',dict(schema='arch03-c32-export-receipt-v1',artifacts={'report.json':h}))
                return h
            h=write();self.assertFalse(c.exported_report(run,h,proof)['stage_accepted'])
            report['activity_reference']=dict(run='old-finish',sha256='0'*64)
            with self.assertRaisesRegex(ValueError,'another netlist'):c.exported_report(run,write(),proof)


if __name__=='__main__':unittest.main()
