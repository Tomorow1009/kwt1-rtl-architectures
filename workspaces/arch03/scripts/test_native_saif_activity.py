"""Streaming audit checks using explicit full-window synthetic activity."""
import tempfile
import unittest
from pathlib import Path
from native_saif_activity import audit,SYSMEM

WINDOW=dict(encoded_bytes=32,transfer_bytes=50752,transfer_transactions=12688,
    boundary='first_source_valid_to_final_write_response_ack_with_drain_proof',
    period_ns='6.666666',start_ns='100',end_ns='200099.98',finished_ns='200106.646666',
    start_cycle=15,end_cycle=30015,finished_cycle=30016,cycles=30000)

def fixture():
    def signal(name,unknown=False):
        t=99999990000 if unknown else 199999980000
        return '(%s (T0 %d)(T1 0)(TX %d)(TZ 0)(TC 4)(IG 0))'%(name,t,199999980000-t)
    def instance(name,children=''):
        return '(INSTANCE %s (NET %s) %s)'%(name,signal('sample',True),children)
    ports=''.join(signal('sysmem_icb_'+(name if width==1 else name+'\\[%d\\]'%i))
        for name,(_,width) in SYSMEM.items() for i in range(width))
    cpu=instance('u_e203_cpu_top',instance('u_e203_itcm_ram')+instance('u_e203_dtcm_ram'))
    mem=instance('u_e203_subsys_mems',''.join(instance(n) for n in
        ['u_arch03_accel','u_arch03_arb','u_arch03_router','u_arch03_shared']))
    return '(SAIFILE (DATE "multi\nline") (TIMESCALE 1 fs) (DURATION 199999980000) (INSTANCE tb_top (INSTANCE u_e203_soc_top (PORT %s)%s%s)))'%(ports,cpu,mem)

class ActivityTests(unittest.TestCase):
    def test_actual_vcs_comment_duration_and_combined_XZ(self):
        text='/* generated\n with saif_region */'+fixture().replace('(SAIFILE ',
            '(SAIFILE (PROGRAM_NAME "VCS Q-2020.03-SP2-6_Full64") ').replace(
            '(DURATION 199999980000)','(DURATION 199999980000.00)').replace('(TZ 0)','')
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'actual_format.saif';p.write_text(text)
            result=audit(p,WINDOW)
            self.assertEqual(result['statistics']['unknown_declarations'],8)
            self.assertGreater(result['statistics']['unknown_ticks'],0)
            self.assertIsNone(result['statistics']['TZ_ticks'])
            self.assertIsNone(result['statistics']['TX_ticks'])
            self.assertFalse(result['X_and_Z_separately_measured'])
            for invalid in (text.replace('199999980000.00','199999980000.01'),
                            text.replace('VCS Q-','unknown Q-'),text+'/* truncated'):
                p.write_text(invalid)
                with self.assertRaises(ValueError):audit(p,WINDOW)

    def test_scope_counts_and_exact_window(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'test.saif';text=fixture();p.write_text(text)
            result=audit(p,WINDOW)
            self.assertEqual(result['source_port_bits'],106)
            self.assertEqual(result['statistics']['unknown_declarations'],8)
            self.assertEqual(result['component_activity']['cpu']['declarations'],3)
            self.assertFalse(result['system_power_verified'])
            for before,after in [('DURATION 199999980000','DURATION 199999980001'),
                    ('u_e203_soc_top','wrong_top'),('cmd_addr\\[31\\]','cmd_addr\\[32\\]'),
                    ('(TX 99999990000)','(TX 99999989999)'),('u_arch03_router','wrong_router'),
                    ('(TC 4)','(TC -1)')]:
                p.write_text(text.replace(before,after))
                with self.assertRaises(ValueError):audit(p,WINDOW)
            p.write_text(text[:-1])
            with self.assertRaises(ValueError):audit(p,WINDOW)

if __name__=='__main__':unittest.main()
