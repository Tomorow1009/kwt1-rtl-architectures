"""A C80 export must join the same exited chain, not a predecessor's precision."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

import c80_archive_contract as archive
from test_c80_archive_contract import fixture,save

SOURCE=Path(__file__).resolve().parents[3]/'handoff/team/evidence/C80_EXPORT_REVIEW01_20261116.py'
spec=importlib.util.spec_from_file_location('c80_export_operation',str(SOURCE))
operation=importlib.util.module_from_spec(spec);spec.loader.exec_module(operation)


def complete(root):
    initial=fixture(root,'initial');ref=initial['references']['precision'];p=Path(ref['run'])/'summary.json'
    value=json.loads(p.read_text());value['batch']={'batch_summary_sha256':initial['references']['batch20']['sha256']}
    ref['sha256']=save(p,value);initial['inputs'][str(p)]=ref['sha256']
    # This fixture represents an already resolved chain, including a distinct retry.
    finish=fixture(root,'finish')
    return archive.joined_queues(initial,finish)


class ExportJoin(unittest.TestCase):
    def test_report_uses_own_all12_power_batch_and_float_reference(self):
        with tempfile.TemporaryDirectory() as d:
            proof=complete(Path(d));value=operation.make_request(proof)
            self.assertEqual(value['asic'],proof['initial']['references']['soc'])
            self.assertEqual(value['batch'],proof['initial']['references']['batch20'])
            self.assertEqual(len(value['power']),12)
            self.assertEqual(value['power'][0],proof['finish']['references']['power_layer_01'])
            self.assertTrue(value['precision']['run'].endswith('/float20') or value['precision']['run'].endswith('\\float20'))
            self.assertFalse(value['history'][0]['prior_hardware_results_reused'])

    def test_other_precision_batch_or_changed_join_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            proof=complete(Path(d));ref=proof['initial']['references']['precision'];p=Path(ref['run'])/'summary.json'
            v=json.loads(p.read_text());v['batch']['batch_summary_sha256']='a'*64;p.write_text(json.dumps(v))
            with self.assertRaisesRegex(ValueError,'Changed C80 precision'):operation.make_request(proof)
            ref['sha256']=archive.digest(p);proof['inputs'][str(p)]=ref['sha256']
            with self.assertRaisesRegex(ValueError,'join this C80 batch'):operation.make_request(proof)

    def test_precision_retry_is_disclosed_without_rewriting_original_failure(self):
        with tempfile.TemporaryDirectory() as d:
            proof=complete(Path(d));initial=proof['initial']
            initial['state'].update(status='failed',error="No module named 'numpy'")
            initial['precision_recovery']={'queue':'separate-own-precision','state_sha256':'b'*64}
            value=operation.make_request(proof)
            self.assertTrue(value['history'][1]['original_failed_state_preserved'])
            self.assertEqual(initial['state']['status'],'failed')


if __name__=='__main__':unittest.main()
