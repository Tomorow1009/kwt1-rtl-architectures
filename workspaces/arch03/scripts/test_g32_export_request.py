"""Report requests must join own gated mapping, precision, batch and activity."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
import g32_archive_contract as contract
from test_g32_archive_contract import fixture

source=Path(__file__).resolve().parents[3]/'handoff/team/evidence/G32_EXPORT_REVIEW01_20261117.py'
spec=importlib.util.spec_from_file_location('g32_export_ops',str(source))
ops=importlib.util.module_from_spec(spec);spec.loader.exec_module(ops)


class ExportRequest(unittest.TestCase):
    def test_complete_chain_retains_clock_gate_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);a=fixture(root,'initial');b=fixture(root,'finish')
            proof=contract.joined_queues(a,b);r=ops.make_request(proof)
            self.assertEqual(r['schema'],'arch03-g32-report-request-v1')
            self.assertEqual(r['history'][0]['clock_gating'],a['references']['icg'])
            self.assertEqual(r['batch'],a['references']['batch20'])
            self.assertEqual(len(r['power']),12)
            self.assertFalse(r['history'][0]['full100_started'])

    def test_changed_precision_not_accepted(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);a=fixture(root,'initial');b=fixture(root,'finish')
            proof=contract.joined_queues(a,b)
            (Path(a['references']['precision']['run'])/'summary.json').write_text('{}')
            with self.assertRaisesRegex(ValueError,'Changed G32 precision'):
                ops.make_request(proof)


if __name__=='__main__':unittest.main()
