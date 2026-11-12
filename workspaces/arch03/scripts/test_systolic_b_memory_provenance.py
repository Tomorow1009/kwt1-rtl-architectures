"""Do not lose SRAM timing provenance when mapped repair retains ancestors."""
import json
from pathlib import Path
import tempfile
import unittest
import systolic_b_gate as gate


class MemoryProvenance(unittest.TestCase):
    def fixture(self, root):
        paths=[root/name for name in ('old','synth','gate')]
        for path in paths:
            path.mkdir();(path/'arch02_sram_config.vh').write_text('same reviewed SRAM timing')
        old,synth,run=paths
        tracked={str(path/'arch02_sram_config.vh'):gate.sha(path/'arch02_sram_config.vh') for path in (old,synth)}
        (synth/'source_inputs.json').write_text(json.dumps(tracked))
        return old,synth,run,tracked

    def test_identical_traced_chain_is_accepted_and_recorded(self):
        with tempfile.TemporaryDirectory() as directory:
            old,synth,run,_=self.fixture(Path(directory))
            gate.verify_gate_memory_config(synth,run)
            receipt=json.loads((run/'memory_configuration_receipt.json').read_text())
            self.assertEqual(len(receipt['identical_traced_inputs']),2)
            (old/'arch02_sram_config.vh').write_text('tampered ancestor')
            with self.assertRaisesRegex(ValueError,'differs'):
                gate.verify_gate_memory_config(synth,run)

    def test_two_valid_but_different_headers_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            old,synth,run,tracked=self.fixture(Path(directory))
            source=old/'arch02_sram_config.vh';source.write_text('different timing')
            tracked[str(source)]=gate.sha(source)
            (synth/'source_inputs.json').write_text(json.dumps(tracked))
            with self.assertRaisesRegex(ValueError,'ambiguous'):
                gate.verify_gate_memory_config(synth,run)
            self.assertFalse((run/'memory_configuration_receipt.json').exists())

    def test_current_synthesis_include_must_be_traced(self):
        with tempfile.TemporaryDirectory() as directory:
            old,synth,run,tracked=self.fixture(Path(directory))
            del tracked[str(synth/'arch02_sram_config.vh')]
            (synth/'source_inputs.json').write_text(json.dumps(tracked))
            with self.assertRaisesRegex(ValueError,'not traced'):
                gate.verify_gate_memory_config(synth,run)


if __name__=='__main__':unittest.main()
