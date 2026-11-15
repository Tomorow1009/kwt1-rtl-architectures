import json
from pathlib import Path
import tempfile
import unittest

import t80_gate as gate


class RelinkMemoryProvenance(unittest.TestCase):
    def fixture(self, root):
        old=root/'original';synth=root/'linked';run=root/'gate'
        for p in (old,synth,run):p.mkdir()
        for p in (old,synth,run):(p/'arch02_sram_config.vh').write_text('`define MACRO_READ_LATENCY 1\n')
        name='arch02_sram_config.vh';digest=gate.sha(old/name)
        source={str(old/name):digest};linked={str(synth/name):digest}
        self.freeze(synth,source,linked)
        return old,synth,run,source,linked

    def freeze(self,synth,source,linked):
        for name,value in [('source_inputs.json',source),('synthesis_inputs.json',linked)]:
            (synth/name).write_text(json.dumps(value))
        report=dict(scope='s0_t80_partitioned_whole_soc_task_mode',artifacts={
            n:gate.sha(synth/n) for n in ('source_inputs.json','synthesis_inputs.json','arch02_sram_config.vh')})
        (synth/'summary.json').write_text(json.dumps(report))

    def test_current_copy_in_frozen_final_receipt_retains_all_ancestors(self):
        with tempfile.TemporaryDirectory() as d:
            old,synth,run,source,linked=self.fixture(Path(d))
            before={str(p):gate.sha(p) for p in synth.iterdir()}
            gate.verify_gate_memory_config(synth,run)
            receipt=json.loads((run/'memory_configuration_receipt.json').read_text())
            self.assertEqual(set(receipt['identical_traced_inputs']),{str((p/'arch02_sram_config.vh').resolve()) for p in (old,synth)})
            self.assertEqual(set(receipt['synthesis_receipts']),{'source_inputs.json','synthesis_inputs.json'})
            self.assertEqual(before,{str(p):gate.sha(p) for p in synth.iterdir()})

    def test_changed_or_ambiguous_provenance_is_rejected(self):
        for bad in ('receipt_changed','current_absent','ancestor_changed','gate_changed','conflict','different_config'):
            with self.subTest(bad=bad),tempfile.TemporaryDirectory() as d:
                old,synth,run,source,linked=self.fixture(Path(d))
                name='arch02_sram_config.vh'
                if bad=='receipt_changed':(synth/'synthesis_inputs.json').write_text('{}')
                elif bad=='current_absent':self.freeze(synth,source,{})
                elif bad=='ancestor_changed':(old/name).write_text('changed')
                elif bad=='gate_changed':(run/name).write_text('changed')
                elif bad=='conflict':
                    linked[str(old/name)]='0'*64;self.freeze(synth,source,linked)
                else:
                    (synth/name).write_text('different');linked[str(synth/name)]=gate.sha(synth/name)
                    self.freeze(synth,source,linked)
                with self.assertRaises(ValueError):gate.verify_gate_memory_config(synth,run)
                self.assertFalse((run/'memory_configuration_receipt.json').exists())

    def test_non_s0_does_not_inherit_relink_exception(self):
        with tempfile.TemporaryDirectory() as d:
            old,synth,run,source,linked=self.fixture(Path(d))
            (synth/'summary.json').write_text(json.dumps(dict(scope='t80_whole_soc_task_mode_preliminary_synthesis')))
            with self.assertRaisesRegex(ValueError,'not traced'):gate.verify_gate_memory_config(synth,run)


if __name__=='__main__':unittest.main()
