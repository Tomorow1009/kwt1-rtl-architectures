import unittest
import p80_precision_join as join
import t80_precision as numeric


class P80PrecisionTests(unittest.TestCase):
    def test_old_hardware_pass_and_full100_are_not_p80_first20(self):
        for schema,tasks in (('arch03-t80-first20-batch-v4',240),('arch03-p80-first20-batch-v4',1200)):
            with self.assertRaisesRegex(ValueError,'ASIC240 is incomplete'):
                join.audit_batch('.',dict(schema=schema,asic_cpu_verified=True,tasks=tasks))

    def test_float_pass_without_own_integer_hardware_cannot_pass(self):
        with self.assertRaisesRegex(ValueError,'own P80 ASIC240'):
            join.audit_precision(dict(source_mode=numeric.SOURCE_MODE,archive_sha256='a'*64),
                dict(integer_bit_exact=False))


if __name__=='__main__':unittest.main()
