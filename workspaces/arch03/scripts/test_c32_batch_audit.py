"""Exercise the final batch audit with real C32 inputs and independent totals."""
import json
from pathlib import Path
import tempfile
import unittest
import c32_batch as batch
import c80_data as wire
from test_n1_data import fixture


class BatchAudit(unittest.TestCase):
    def test_final_audit_uses_C32_codec_and_rejects_changed_total_or_wire(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);source=root/'source';case=root/'case';case.mkdir()
            _,totals,results,sats=fixture(source)
            target=case/'task_data';wire.prepare_case(source,target)
            lines=['%d,%d,%d,%d,%d'%(i//256,i%256,results[i],sats[i],totals[i])
                   for i in reversed(range(25344))]
            capture=case/'task.csv';capture.write_text('\n'.join(lines)+'\n')
            result=batch.audit_task(source,case)
            self.assertEqual(result['outputs'],25344)
            self.assertTrue(result['total_checked'])
            original=capture.read_bytes()
            fields=lines[0].split(',');fields[-1]=str(int(fields[-1])+1)
            capture.write_text(','.join(fields)+'\n'+'\n'.join(lines[1:])+'\n')
            with self.assertRaises(ValueError):batch.audit_task(source,case)
            capture.write_bytes(original)
            codec=target/'codec.bin';raw=codec.read_bytes()
            codec.write_bytes(raw[:-1]+bytes([raw[-1]^1]))
            with self.assertRaises(ValueError):batch.audit_task(source,case)


if __name__=='__main__':unittest.main()
