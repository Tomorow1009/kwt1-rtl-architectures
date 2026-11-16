"""C32 model-review identity rejection and unchanged SAIF/connectivity checks."""
import copy
from pathlib import Path
import tempfile
import unittest
import c32_review_contract as c
import c32_saif_unknown_inventory as inventory
import c32_unknown_connections as connections
import b0_saif_unknown_inventory as predecessor
from test_b0_saif_unknown_inventory import fixture,index,WINDOW


def manifest():
    return dict(architecture='arch03_c32_ordered_original_bus',row_lanes=2,fixed_shift=10,
        numeric_format_id='0x000e0c20',numeric_format='0x000e0c20',layout_id='0x00100006',
        peripheral_id='0x4b57530d',transaction_metadata_depth=2)


def report():
    return dict(schema='arch03-c32-evidence-export-v1',stage='C32',row_lanes=2,
        numeric_format='0x000e0c20',layout_id=0x00100006,shift=10,transaction_metadata_depth=2,
        synthesis_route=dict(scope=c.SCOPE,old_linked_ddc_reused=False,block_cache_reused=False))


def synthesis():
    return dict(scope=c.SCOPE,synthesis_completed=True,project_limit_mm2=1.0,
        transaction_metadata_depth=2,old_linked_ddc_reused=False,block_cache_reused=False,
        link_report=dict(schema='arch03-c32-fresh-link-v1',row_lanes=2,transaction_metadata_depth=2))


class Identity(unittest.TestCase):
    def test_frozen_identity_rejects_old_layout_or_hardware(self):
        request=dict(transport_stage='C32',jobs=[dict(name='C32')])
        self.assertEqual(c.profile(request,manifest()),'C32')
        for key,value in [('architecture','arch03_p80_ordered_original_bus'),('layout_id','0x00100004'),
                          ('peripheral_id','0x4b57530b'),('fixed_shift',16),('row_lanes',5),
                          ('transaction_metadata_depth',4),('transaction_metadata_depth',2.0)]:
            with self.assertRaises(ValueError):c.profile(request,dict(manifest(),**{key:value}))
        for jobs in ([],[dict(name='P80')],[dict(name='C32'),dict(name='P80')]):
            with self.assertRaises(ValueError):c.profile(dict(request,jobs=jobs),manifest())

    def test_own_export_and_synthesis_only(self):
        c.report_identity(report());c.synthesis_identity(synthesis())
        for delta in [dict(stage='P80'),dict(layout_id=0x00100004),dict(shift=16),
                      dict(transaction_metadata_depth=4),dict(synthesis_route={})]:
            with self.assertRaises(ValueError):c.report_identity(dict(report(),**delta))
        for delta in [dict(scope='p80_partitioned_whole_soc_task_mode'),dict(project_limit_mm2=1.2),
                      dict(old_linked_ddc_reused=True),dict(block_cache_reused=True),dict(link_report={}),
                      dict(transaction_metadata_depth=4)]:
            with self.assertRaises(ValueError):c.synthesis_identity(dict(synthesis(),**delta))
        self.assertEqual(inventory.profile_contract(report()),
            ('C32','c32_synth','c32_saif','C32_native_saif_function_and_complete_windows_passed'))
        with self.assertRaises(ValueError):predecessor.profile_contract(report())

    def test_complete_original_readback_window_and_unknowns(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'layer_01.saif';path.write_bytes(fixture().encode('ascii'))
            expected=predecessor.native.audit(path,WINDOW)
            four=dict(WINDOW,transfer_bytes=50784,transfer_transactions=12696)
            got=[];reader=inventory.profile_window_reader('C32')
            result=inventory.scan(path,four,expected,index(),got.append,window_reader=reader)
            self.assertEqual(result['unknown_rows'],5);self.assertEqual(len(got),5)
            self.assertFalse(result['unknown_effect_on_power_approved'])
            with self.assertRaises(ValueError):reader(WINDOW)
            with self.assertRaises(ValueError):inventory.profile_window_reader('P80')
            bad=copy.deepcopy(expected);bad['sha256']='0'*64
            with self.assertRaises(ValueError):inventory.scan(path,four,bad,index(),lambda x:None,window_reader=reader)
            identities=inventory.dependencies()
            self.assertIn('c32_review_contract',identities)
            self.assertNotIn('transport_review_contract',identities)

    def test_connectivity_retains_unresolved_and_not_power_approval(self):
        raw='schema\tsaif-unknown-linked-connections-v1\nnet\ta\t0\t0\nunresolved\tb\n'
        got=connections.parse_connections(raw,{'a','b'})
        self.assertEqual(got['unresolved'],['b']);self.assertFalse(got['system_power_verified'])
        with self.assertRaises(ValueError):connections.parse_connections(raw,{'a','b','c'})


if __name__=='__main__':unittest.main()
