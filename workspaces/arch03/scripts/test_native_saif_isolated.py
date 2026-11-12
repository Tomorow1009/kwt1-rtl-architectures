"""A missing activity source is accepted only for proven empty connectivity."""
import copy
from pathlib import Path
import tempfile
import unittest
import tkinter
from test_dma16_power_activity_review import sources,unannotated
from dma16_power_activity_review import sources as parse_sources
from native_saif_isolated import review,comparable_sources,tcl_inventory


class IsolatedTests(unittest.TestCase):
    def fixture(self,root):
        counts=[98,0,0,0,0,0,2,0,0,0]
        tail='u/unused[0] <No-Driver>\nu/unused[1] <No-Driver>\n2 nets with no annotation\n1\n'
        raw=unannotated(counts=counts,tail=tail)
        proof=root/'native_isolated_connections.tsv'
        proof.write_text('net\tdirect_connections\tleaf_connections\nu/unused[0]\t0\t0\nu/unused[1]\t0\t0\n')
        mapping=parse_sources(sources(counts=counts))
        return mapping,raw,proof

    def test_only_empty_exact_connections_can_be_excluded(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);mapping,raw,proof=self.fixture(root)
            value=review(root,mapping,raw,raw)
            self.assertEqual(value['isolated_defaults']['count'],2)
            self.assertFalse(value['isolated_defaults']['activity_values_modified'])
            original=proof.read_text()
            for bad in (original.replace('0\t0','0\t1',1),original.replace('0\t0','1\t0',1),
                        original.replace('u/unused[1]','u/other[1]'),original+original.splitlines(True)[-1]):
                proof.write_text(bad)
                with self.assertRaises(ValueError):review(root,mapping,raw,raw)
            proof.unlink()
            with self.assertRaisesRegex(ValueError,'connectivity proof'):review(root,mapping,raw,raw)

    def test_counts_driven_nets_and_changed_after_set_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);mapping,raw,proof=self.fixture(root)
            for before,after in [(raw.replace('<No-Driver>','U1/Q',1),raw),
                                 (raw,raw.replace('unused[1]','different[1]')),
                                 (raw.replace('2 nets','3 nets'),raw)]:
                with self.assertRaises(ValueError):review(root,mapping,before,after)
            changed=copy.deepcopy(mapping);changed['static_probability']['default']=1
            with self.assertRaises(ValueError):review(root,changed,raw,raw)

    def test_effective_coverage_retains_raw_counts_and_requires_proof(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);mapping,raw,proof=self.fixture(root)
            ref=dict(sources=parse_sources(sources(counts=[100]+[0]*9)))
            native=dict(sources=mapping,**review(root,mapping,raw,raw))
            baseline=copy.deepcopy(ref);candidate=copy.deepcopy(native)
            checked=comparable_sources(ref,native)
            self.assertEqual(checked['isolated_declarations_excluded'],2)
            self.assertFalse(checked['raw_mapping_equal'])
            self.assertEqual((ref,native),(baseline,candidate))
            del native['isolated_defaults']['proof_sha256']
            with self.assertRaises(ValueError):comparable_sources(ref,native)

    def test_empty_legacy_report_and_tcl_structure(self):
        with tempfile.TemporaryDirectory() as d:
            raw=unannotated();v=review(Path(d),parse_sources(sources()),raw,raw)
            self.assertEqual(v['isolated_defaults']['count'],0)
        self.assertEqual(tkinter.Tcl().call('info','complete',tcl_inventory()),1)
        self.assertIn('all_connected -leaf $net',tcl_inventory())
        self.assertNotIn('set_switching_activity',tcl_inventory())


if __name__=='__main__':unittest.main()
