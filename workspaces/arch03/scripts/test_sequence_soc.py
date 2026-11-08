import unittest
from decimal import Decimal
from sequence_soc import sequence_log


def log_fixture(starts=(10,210,410)):
    lines=[];period=Decimal('6.666666')
    for i,start in enumerate(starts,1):
        if i==3:
            lines+=['ARCH03_SEQUENCE_POISON_PASS starts=1 loads=17 aborts=1 output_reads=0',
                    'ARCH03_SEQUENCE_TIMEOUT_PASS starts=1 loads=1 aborts=2 rc=-1 output_reads=0']
        lines.append('ARCH03_TASK_WINDOW start_cycle=%d end_cycle=%d cycles=100 start_ns=%s end_ns=%s period_ns=6.666666 input_words=23488 output_words=25344'
                     %(start,start+100,Decimal(start)*period,Decimal(start+100)*period))
        lines.append('ARCH03_SOC_SEQUENCE_TASK index=%d cycles=150 saturated=0 outputs=25344'%i)
    lines.append('ARCH03_SOC_SEQUENCE_PASS tasks=3 outputs=76032 cpu_executed=true abort_verified=true timeout_verified=true')
    return '\n'.join(lines)


class SequenceLogTests(unittest.TestCase):
    def test_three_independent_windows_and_recovery(self):
        entries,loads=sequence_log(log_fixture())
        self.assertEqual([e['index'] for e in entries],[1,2,3])
        self.assertEqual(loads,1)

    def test_missing_duplicate_and_partial_rejected(self):
        text=log_fixture()
        invalid=[text.replace('index=2','index=1'),text+'\n'+text,
                 text.replace('loads=17 aborts=1','loads=16 aborts=1'),
                 text.replace('loads=1 aborts=2','loads=23488 aborts=2'),
                 text.replace('cycles=150','cycles=99'),
                 text.replace('ARCH03_SEQUENCE_TIMEOUT_PASS','NO_TIMEOUT_EVIDENCE')]
        for value in invalid:
            with self.assertRaises(ValueError):sequence_log(value)

    def test_overlap_and_recovery_order_rejected(self):
        with self.assertRaises(ValueError):sequence_log(log_fixture(starts=(10,50,410)))
        lines=log_fixture().splitlines();lines[4],lines[5]=lines[5],lines[4]
        with self.assertRaises(ValueError):sequence_log('\n'.join(lines))


if __name__=='__main__':unittest.main()
