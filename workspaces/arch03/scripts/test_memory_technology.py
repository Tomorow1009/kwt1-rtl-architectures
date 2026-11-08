import hashlib
import unittest
from memory_technology import verify_memory_liberty


class MemoryTechnologyTests(unittest.TestCase):
    def fixture(self):
        raw=b'''library(fake) {
 time_unit : "1ns";
 leakage_power_unit : "1mW";
 cell(RAMSP128X16) {
 area : 2677.051;
 cell_leakage_power : 0;
 internal_power() { }
 leakage_power() { related_pg_pin : "VDDPE"; when : "!RET1N"; value : 0.001; }
 leakage_power() { related_pg_pin : "VDDCE"; when : "!RET1N"; value : 0.003; }
 leakage_power() { related_pg_pin : "VDDPE"; value : 0.002; }
 leakage_power() { related_pg_pin : "VDDCE"; value : 0.004; }
 }
}'''
        spec=dict(schema='arch03-sram-ss-metadata-v1',time_unit='1ns',leakage_power_unit='1mW',
                  cells={'RAMSP128X16':dict(sha256=hashlib.sha256(raw).hexdigest(),area=2677.051,internal_power_groups=1,leakage_groups=4)})
        return raw,spec

    def test_zero_cell_summary_does_not_hide_conditional_leakage(self):
        raw,spec=self.fixture();result=verify_memory_liberty(raw,'RAMSP128X16',spec)
        self.assertEqual(len(result['leakage_groups']),4)
        self.assertGreater(sum(g['value'] for g in result['leakage_groups']),0)
        self.assertFalse(result['system_power_verified'])

    def test_changed_hash_units_area_and_incomplete_power_fail(self):
        raw,spec=self.fixture()
        with self.assertRaises(ValueError):verify_memory_liberty(raw+b'\n','RAMSP128X16',spec)
        for changed in (raw.replace(b'1mW',b'1nW'),raw.replace(b'2677.051',b'1.0'),
                        raw.replace(b'0.004',b'0.000'),raw.replace(b'VDDCE',b'VDDPE')):
            spec['cells']['RAMSP128X16']['sha256']=hashlib.sha256(changed).hexdigest()
            with self.assertRaises(ValueError):verify_memory_liberty(changed,'RAMSP128X16',spec)


if __name__=='__main__':unittest.main()
