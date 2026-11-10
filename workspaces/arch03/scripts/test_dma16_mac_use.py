"""Synthetic event ordering tests, not a hardware acceptance result."""
import ast
import copy
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from activity import audit_vcd, ROLES
import dma16_mac_use as p

FIELDS = [('clk',1),('rst_n',1),('start_valid',1),('start_ready',1),('bias',40),('shift',5),
          ('in_valid',1),('in_ready',1),('x',16),('w',16),('out_valid',1),('out_ready',1),('result',16),('saturated',1)]


def waveform(split=False, post_edge_unknown=False, accepted_unknown=False):
    lines = ['$timescale 1ns $end', '$scope module tb_top $end', '$scope module u_e203_soc_top $end']
    for i, instance in enumerate(ROLES.values()):
        lines += ['$scope module '+instance+' $end', '$var wire 1 r%d clk $end'%i, '$upscope $end']
    for scope in ('u_e203_subsys_top','u_e203_subsys_main','u_e203_subsys_mems','u_arch03_accel','core'):
        lines.append('$scope module '+scope+' $end')
    for lane in range(16):
        lines.append('$scope module lanes[%d].mac $end'%lane)
        for name, width in FIELDS:
            if split and width > 1:
                for bit in reversed(range(width)):
                    lines.append('$var wire 1 %s_%d %s [%d] $end'%(name,bit,name,bit))
            else:
                lines.append('$var wire %d %s %s %s$end'%(width,name,name,'' if width==1 else '[%d:0] '%(width-1)))
        lines.append('$upscope $end')
    lines += ['$upscope $end']*7+['$enddefinitions $end','#0','$dumpoff $end','#100','$dumpon']
    def value(name, raw):
        width = dict(FIELDS)[name]
        if split and width>1:
            # Exercise every scalar bit in the mapped report format.
            bits = raw.rjust(width, 'x' if raw=='x' else '0')
            return [bits[-1-bit]+name+'_'+str(bit) for bit in range(width)]
        return [raw+name if width==1 else 'b'+raw+' '+name]
    for i in range(len(ROLES)): lines.append('0r%d'%i)
    for name, width in FIELDS:
        raw = '1' if name in ('rst_n','start_valid','start_ready') else ('x' if name in ('x','w') else '0')
        lines += value(name, raw)
    lines += ['$end','#110','1clk']
    for i in range(len(ROLES)): lines.append('1r%d'%i)
    lines += ['0start_valid','0start_ready','1in_ready','#115','0clk','1in_valid']
    lines += value('x','1')+value('w','1')
    if accepted_unknown: lines += ['#119']+value('x','x')
    for n in range(64):
        tick=120+n*10; lines += ['#'+str(tick),'1clk']
        if n==0 and post_edge_unknown: lines += value('x','x')
        if n==63: lines += ['0in_valid','0in_ready']
        lines += ['#'+str(tick+5),'0clk']
        if n==0: lines += value('x','1')
    lines += ['1out_valid','1out_ready']+value('result','1')
    lines += ['#760','1clk','0out_valid','0out_ready','1start_ready','#765','0clk','#770','1clk',
              '#771','$dumpoff','xclk','$end']
    return '\n'.join(lines)+'\n'


@unittest.skipUnless(os.environ.get('ARCH03_MAC_SCANNER'), 'Explicit compiled MAC scanner required')
class MacUseTests(unittest.TestCase):
    def scan(self, text, fail=False):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'sample.vcd'; path.write_text(text)
            r=subprocess.run([os.environ['ARCH03_MAC_SCANNER'],str(path)],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            if fail:
                self.assertNotEqual(r.returncode,0); return
            self.assertEqual(r.returncode,0,r.stderr.decode())
            return json.loads(r.stdout.decode()), audit_vcd(path,dict(start_ns='100',end_ns='771'))

    def checked(self, result): return p.validate(*result,dict(period_ns='10'),dots=1)

    def test_known_accepted_values_with_idle_unknown_and_full_counter_agreement(self):
        result=self.scan(waveform()); checked=self.checked(result)
        self.assertTrue(checked['mac_valid_samples_verified']); self.assertFalse(checked['system_power_verified'])
        self.assertEqual(checked['accepted_macs'],1024)
        self.assertEqual(checked['mac_sampling']['lanes'][0]['unknown_at_sampled_edges']['x'],1)

    def test_split_bits_and_shared_aliases_match_vectors(self):
        a=self.checked(self.scan(waveform())); b=self.checked(self.scan(waveform(split=True)))
        self.assertEqual(a['mac_sampling'],b['mac_sampling'])

    def test_post_edge_unknown_is_not_consumed_but_pre_edge_unknown_is_rejected(self):
        self.checked(self.scan(waveform(post_edge_unknown=True)))
        result=self.scan(waveform(accepted_unknown=True))
        self.assertEqual(result[0]['mac_sampling']['accepted_samples_unknown'],16)
        with self.assertRaisesRegex(ValueError,'Unknown accepted'): self.checked(result)

    def test_ambiguous_handshake_is_reported_and_zero_masks_unknown(self):
        bad=waveform().replace('#115\n0clk\n1in_valid','#115\n0clk\nxin_valid')
        result=self.scan(bad)
        self.assertGreater(result[0]['mac_sampling']['ambiguous_controls'],0)
        masked=bad.replace('1in_ready','#110\n0in_ready')
        result=self.scan(masked)
        self.assertEqual(result[0]['mac_sampling']['ambiguous_controls'],0)
        with self.assertRaisesRegex(ValueError,'Missing or extra'): self.checked(result)

    def test_missing_duplicate_wrong_bit_range_and_clock_glitch_are_rejected(self):
        text=waveform(split=True)
        for bad in (text.replace('$var wire 1 shift_4 shift [4] $end\n','',1),
                    text.replace('$var wire 1 shift_4 shift [4] $end','$var wire 1 shift_3 shift [3] $end',1),
                    text.replace('shift [4]','shift [5]',1),
                    text.replace('#120\n1clk','#120\n1clk\n0clk\n1clk'),
                    text[:text.rfind('#771')]):
            with self.subTest(): self.scan(bad,True)

    def test_frozen_counter_clock_and_operation_counts_cannot_be_relaxed(self):
        original,activity=self.scan(waveform())
        for key,value in [('feeds',63),('starts',2),('reset_edges',1),('last_edge_tick',760),
                          ('maximum_edge_interval_ticks',11),('unfinished_dot',True)]:
            bad=copy.deepcopy(original);bad['mac_sampling']['lanes'][0][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError): self.checked((bad,activity))
        bad=dict(activity,unknown_value_records=0)
        with self.assertRaises(ValueError): self.checked((original,bad))

    def test_stage_preserves_waveform_and_does_not_approve_system_power(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); gate=root/'gate'; gate.mkdir(); run=root/'audit'; run.mkdir()
            vcd=gate/'layer_01.vcd'; vcd.write_text(waveform())
            for name in ('summary.json','source_inputs.json'): (gate/name).write_text('{}')
            activity=audit_vcd(vcd,dict(start_ns='100',end_ns='771'))
            actual_validate=p.validate
            def call(cmd, directory, log):
                if cmd[0]=='g++':
                    Path(cmd[-1]).write_bytes(Path(os.environ['ARCH03_MAC_SCANNER']).read_bytes()); text='fixture binary copy\n'
                else: text=subprocess.check_output([os.environ['ARCH03_MAC_SCANNER'],str(vcd)]).decode('ascii')
                (directory/log).write_text(text); return text
            before=p.stream_sha(vcd)
            with patch.object(p,'gate_activity',return_value=({'synthesis_summary_sha256':'a'*64},
                              {'activity':activity,'task_window':dict(period_ns='10')},vcd,root/'synth','671')):
                with patch.object(p,'validate',side_effect=lambda scan,act,win: actual_validate(scan,act,win,dots=1)):
                    result=p.audit({},run,gate,'b'*64,'layer_01',call)
            self.assertEqual(p.stream_sha(vcd),before)
            self.assertTrue(result['checked']['mac_valid_samples_verified'])
            self.assertFalse(result['system_power_verified']); self.assertFalse(result['waveform_modified'])
            self.assertIn('mac_full_scan.json',result['artifacts'])

    def test_python36_grammar(self):
        ast.parse(Path(p.__file__).read_text(),feature_version=(3,6))


if __name__=='__main__': unittest.main()
