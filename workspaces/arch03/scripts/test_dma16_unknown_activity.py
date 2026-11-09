import ast
import copy
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from activity import audit_vcd
from test_activity import waveform
import dma16_unknown_activity as p


@unittest.skipUnless(os.environ.get('ARCH03_UNKNOWN_SCANNER'), 'Explicit compiled scanner required')
class UnknownActivityTests(unittest.TestCase):
    def scan(self, text, fail=False):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'test.vcd'; path.write_text(text)
            result = subprocess.run([os.environ['ARCH03_UNKNOWN_SCANNER'], str(path)],
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            if fail:
                self.assertNotEqual(result.returncode, 0); return
            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads(result.stdout)
            original = audit_vcd(path, dict(start_ns='100', end_ns='120'))
            p.validate(data, original)
            return data, original

    def test_known_initial_then_persistent_unknown_matches_frozen_scan(self):
        data, _ = self.scan(waveform()); row = data['signals'][0]
        self.assertEqual(row['identifier'], 's1')
        self.assertEqual(row['any_unknown_ticks'], 10000)
        self.assertEqual(row['unknown_records_after_begin'], 1)
        self.assertTrue(row['unknown_at_end'])
        self.assertEqual(data['unknown_records_at_begin'], 0)
        self.assertEqual(data['identifiers_without_initial_observation'], 0)

    def test_initial_unknown_known_recovery_repeated_unknown_and_end_exclusion(self):
        text = waveform().replace('0s1', 'xs1').replace('xs1\n#120000',
            'xs1\n#112000\nzs1\n#115000\n0s1\n#119000\nxs1\n#120000')
        data, _ = self.scan(text); row = data['signals'][0]
        self.assertEqual(row['unknown_records'], 4)
        self.assertEqual(row['unknown_records_at_begin'], 1)
        self.assertEqual(row['unknown_records_after_begin'], 3)
        self.assertEqual(row['any_unknown_ticks'], 16000)
        self.assertEqual(data['unknown_identifiers'], 1)  # dumpoff xs0 is excluded

    def test_aliases_vector_any_bit_unknown_and_same_tick_updates(self):
        text = waveform().replace('$var wire 1 s1 clk $end',
            '$var wire 8 s1 data [7:0] $end\n$var wire 8 s1 alias [7:0] $end')
        text = text.replace('xs1', 'b01x10101 s1\n0s1\nzs1')
        data, _ = self.scan(text); row = data['signals'][0]
        self.assertEqual(len(row['aliases']), 2); self.assertEqual(row['width'], 8)
        self.assertEqual(row['any_unknown_ticks'], 10000)
        self.assertEqual(row['unknown_records'], 2)
        self.assertIn('[7:0]', row['aliases'][0])

    def test_missing_initial_is_unobserved_not_zero_or_unknown(self):
        text = waveform().replace('0s1\n', '').replace('$var wire 1 s1 clk $end',
            '$var wire 1 s1 clk $end\n$var wire 1 missing never_written $end')
        data, _ = self.scan(text); rows = {x['identifier']: x for x in data['signals']}
        self.assertEqual(rows['s1']['unobserved_prefix_ticks'], 10000)
        self.assertEqual(rows['missing']['unobserved_prefix_ticks'], 20000)
        self.assertEqual(rows['missing']['any_unknown_ticks'], 0)
        self.assertIsNone(rows['missing']['first_observation_tick'])
        self.assertEqual(data['identifiers_without_initial_observation'], 2)

    def test_structural_errors_are_rejected(self):
        text = waveform()
        for bad in (text.replace('1s0', '1undefined'), text.replace('#110000', '#90000'),
                    text[:text.rfind('#120000')], text.replace('xs1', 'b222 s1'),
                    text.replace('u_arch03_accel', 'wrong'),
                    text+'#130000\n$dumpon $end\n#140000\n$dumpoff $end\n'):
            self.scan(bad, True)

    def test_details_must_match_frozen_counts_window_and_each_other(self):
        data, original = self.scan(waveform())
        for key in p.COUNTERS:
            bad = copy.deepcopy(original); bad[key] = -1
            with self.assertRaises(ValueError): p.validate(data, bad)
        bad = dict(original, end_ns='121')
        with self.assertRaisesRegex(ValueError, 'window'): p.validate(data, bad)
        for key, value in [('unknown_records_after_begin', 2), ('any_unknown_ticks', 20001),
                           ('first_unknown_tick', 1), ('unobserved_prefix_ticks', 5)]:
            bad = copy.deepcopy(data); bad['signals'][0][key] = value
            with self.assertRaises(ValueError): p.validate(bad, original)

    def test_stage_keeps_original_hashes_and_cannot_grant_power_acceptance(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); gate = root/'gate'; gate.mkdir(); run = root/'audit'; run.mkdir()
            vcd = gate/'layer_01.vcd'; vcd.write_text(waveform())
            for name in ('summary.json', 'source_inputs.json'): (gate/name).write_text('{}')
            activity = audit_vcd(vcd, dict(start_ns='100', end_ns='120'))
            def call(cmd, directory, log):
                if cmd[0] == 'g++':
                    Path(cmd[-1]).write_bytes(Path(os.environ['ARCH03_UNKNOWN_SCANNER']).read_bytes()); text = 'fixture binary copy\n'
                else:
                    output = subprocess.check_output([os.environ['ARCH03_UNKNOWN_SCANNER'], str(vcd)])
                    text = output.decode('ascii')
                (directory/log).write_text(text); return text
            original_sha = p.stream_sha(vcd)
            with patch.object(p, 'gate_activity', return_value=({'synthesis_summary_sha256': 'a'*64},
                              {'activity': activity}, vcd, root/'synth', '20')):
                result = p.audit({}, run, gate, 'b'*64, 'layer_01', call)
            self.assertFalse(result['system_power_verified']); self.assertTrue(result['complete_stream_scanned'])
            self.assertEqual(p.stream_sha(vcd), original_sha)
            self.assertEqual(result['localization']['counters']['unknown_value_records'], 1)


class SyntaxTests(unittest.TestCase):
    def test_python36_grammar(self):
        ast.parse(Path(p.__file__).read_text(), feature_version=(3, 6))


if __name__ == '__main__': unittest.main()
