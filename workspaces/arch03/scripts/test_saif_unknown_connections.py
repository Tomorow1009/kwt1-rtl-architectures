"""Reject incomplete or misidentified connectivity evidence."""
import gzip
import json
from pathlib import Path
import tempfile
import unittest

import saif_unknown_connections as proof


class ConnectivityEvidence(unittest.TestCase):
    def test_separates_aliases_unresolved_and_real_loads(self):
        text = ('schema\tsaif-unknown-linked-connections-v1\n'
                'net\tunused[0]\t0\t0\nnet\talias\t2\t0\n'
                'net\tloaded\t2\t1\nendpoint\tloaded\tcell/D\tpin\tin\tDFF\n'
                'unresolved\tmissing\n')
        got = proof.parse_connections(text, {'unused[0]', 'alias', 'loaded', 'missing'})
        self.assertEqual(got['leaf_connected'], ['loaded'])
        self.assertEqual(got['isolated_zero_direct_and_leaf'], ['unused[0]'])
        self.assertEqual(got['hierarchy_only_no_leaf'], ['alias'])
        self.assertEqual(got['unresolved'], ['missing'])
        self.assertFalse(got['system_power_verified'])

    def test_rejects_missing_and_duplicate_endpoints(self):
        head = 'schema\tsaif-unknown-linked-connections-v1\n'
        for body in ('net\tn\t1\t1\n', 'net\tn\t1\t2\n'+
                     'endpoint\tn\tc/D\tpin\tin\tDFF\n'*2):
            with self.assertRaises(ValueError):proof.parse_connections(head+body, {'n'})
        with self.assertRaises(ValueError):proof.parse_connections(head, {'n'})

    def test_inventory_is_bound_to_netlist_and_all_layers(self):
        with tempfile.TemporaryDirectory() as root:
            directory = Path(root);cases = []
            for i in range(1, 13):
                path = directory/('layer_%02d.gz' % i)
                with gzip.open(str(path), 'wt') as out:
                    out.write(json.dumps(dict(section='NET', saif_name='tb_top/u_e203_soc_top/a[0]',
                        mapping=dict(disposition='module_expression_reference')))+'\n')
                cases.append(dict(case='layer_%02d'%i, unknown_file=path.name,
                    unknown_file_sha256=proof.sha(path), unknown_rows=1))
            report = dict(status='complete_existing_unknown_inventory_review_required',
                full_unknown_inventory_complete=True, netlist='/original/mapped.v',
                netlist_sha256='a'*64, cases=cases)
            path = directory/'summary.json';path.write_text(json.dumps(report))
            ref = dict(run=root, sha256=proof.sha(path))
            names, _, _ = proof.inventory_targets([ref], '/original/mapped.v', 'a'*64)
            self.assertEqual(names, ['a[0]'])
            with self.assertRaises(ValueError):proof.inventory_targets([ref], '/wrong/mapped.v', 'a'*64)
            with self.assertRaises(ValueError):proof.inventory_targets([ref], '/original/mapped.v', 'b'*64)
            report['cases'].pop();path.write_text(json.dumps(report));ref['sha256'] = proof.sha(path)
            with self.assertRaises(ValueError):proof.inventory_targets([ref], '/original/mapped.v', 'a'*64)


if __name__ == '__main__':unittest.main()
