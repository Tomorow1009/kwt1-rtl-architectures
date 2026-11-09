"""Synthetic log parser tests only; never execute or pretend to run an ASIC."""
import ast
from decimal import Decimal
from pathlib import Path
import sys
import unittest
import dma16_sequence_soc as soc


def fixture():
    manifest=dict(tasks=dict(A=dict(descriptor=12),B=dict(descriptor=0x1000b)),
        fault_sites=dict(sequence_fault_store='0x80000100'),configuration=dict(short_timeout_cycles=8192))
    captures=[dict(outputs=25344,saturated=0),dict(outputs=25344,saturated=7),dict(outputs=25344,saturated=0)]
    lines=list(soc.MARKERS)
    for phase in range(1,11):
        kind=1 if phase<=5 else 2 if phase==6 else 3 if phase==7 else 4
        descriptor=0x1000b if phase==9 else 12
        counts=[0,0,0,0] if phase<=5 else [35,34,0,0] if phase==6 else [1348,1347,0,0] if phase==7 else [11744,11744,11744,12672]
        failed=int(phase<=7);rc=-1 if phase==7 else 0;sat=7 if phase==9 else 0
        cycles=0 if phase<=5 else 200 if phase<=7 else 225770
        start=0 if phase<=5 else phase*1000000;end=start+cycles
        period=Decimal('6.666666')
        time0=Decimal(start)*period;time1=Decimal(end)*period if phase>=6 else Decimal(phase*100)
        counted=list(counts)
        if phase in (6,7):counted[0]-=1
        window=dict(finished=1,failed=failed,failure_code=11 if failed else 0,start_cycle=start,end_cycle=end,cycles=cycles,
            start_ns='%.6f'%time0,end_ns='%.6f'%time1,finished_cycle=end+1,finished_ns='%.6f'%(time1+period),
            source_bytes=counted[0]*4,input_write_bytes=counted[1]*4,input_read_bytes=counted[2]*4,output_bytes=counted[3]*4)
        words=[0]*33;words[0:3]=[phase,kind,rc&0xffffffff]
        words[3]=0x4050 if phase<=5 else 0x4040 if phase<=7 else 0x4008
        words[4]=48 if failed else 31
        if phase<=5:
            words[6:9]=[3,0x40000004,2]
            words[26:28]={1:[0x28,0xb0000002],2:[0x2c,0xa007f000],3:[0x30,0xa0000000],4:[0x34,46972],5:[0x38,50684]}[phase]
        words[9:13]=counts;words[13:15]=[counts[1]*4,counts[3]*4]
        if phase>=8:words[15:18]=[23488,25344,sat]
        words[18]=max(cycles+1000,10000);words[20]=1
        words[21:26]=[min(phase,5),7,0x80000100,0x40000004,descriptor];words[28]=8192
        if phase==6:words[29:32]=[32,31,1]
        words[32]=rc&0xffffffff
        lines += ['DMA16_SEQUENCE_SOURCE_SELECTED descriptor=%08x'%descriptor,
            'DMA16_SEQUENCE_PHASE_ARM phase=%d descriptor=%08x'%(phase,descriptor),
            'DMA16_TASK_WINDOW '+' '.join('%s=%s'%(k,v) for k,v in window.items()),
            'DMA16_SEQUENCE_RECEIPT phase=%d words='%phase+','.join('%08x'%v for v in words),
            'DMA16_SEQUENCE_PHASE_PASS phase=%d kind=%d rc=%d source_acks=%d stage_acks=%d read_acks=%d output_acks=%d start_cycle=%d end_cycle=%d cycles=%d window_failed=%d saturated=%d'%
            tuple([phase,kind,rc]+counts+[start,end,cycles,failed,sat])]
    lines += ['DMA16_SEQUENCE_PASS phases=10 tasks=3 outputs=76032 cpu_executed=true guarded_faults=5 timeout_recovery=true']
    return '\n'.join(lines)+'\n',manifest,captures


class SequenceSocTests(unittest.TestCase):
    def test_all_ten_receipts_and_three_captures(self):
        text,manifest,captures=fixture();result=soc.parse_transcript(text,manifest,captures)
        self.assertEqual(len(result),10)
        self.assertEqual([r['descriptor'] for r in result[-3:]],[12,65547,12])
        self.assertEqual(sum(r['performance_eligible'] for r in result),3)
        # Cancellation-window counters stop before the final draining ACK.
        self.assertEqual(result[5]['summary']['source_acks'],35)
        self.assertEqual(result[5]['task_window']['source_bytes'],34*4)

    def test_no_cpu_fixture_is_not_cpu_acceptance(self):
        text,manifest,captures=fixture()
        bad=text.replace('cpu_executed=true guarded_faults=5 timeout_recovery=true',
                         'cpu_executed=false actual_CPU_traps_verified=false actual_driver_timeout_verified=false')
        with self.assertRaisesRegex(ValueError,'NO_CPU'):soc.parse_transcript(bad,manifest,captures)

    def test_missing_raw_receipt_rejected(self):
        text,manifest,captures=fixture()
        bad='\n'.join(line for line in text.splitlines() if not line.startswith('DMA16_SEQUENCE_RECEIPT phase=3 '))
        with self.assertRaises(ValueError):soc.parse_transcript(bad,manifest,captures)

    def test_wrong_real_fault_pc_rejected(self):
        text,manifest,captures=fixture()
        with self.assertRaises(ValueError):soc.parse_transcript(text.replace('80000100','80000104'),manifest,captures)

    def test_source_order_and_duplicate_stage_rejected(self):
        text,manifest,captures=fixture()
        for bad in (text.replace('phase=9 descriptor=0001000b','phase=9 descriptor=0000000c'),
                    text.replace('PHASE_ARM phase=9','PHASE_ARM phase=8')):
            with self.assertRaises(ValueError):soc.parse_transcript(bad,manifest,captures)

    def test_success_window_must_have_full_acks(self):
        text,manifest,captures=fixture()
        with self.assertRaises(ValueError):soc.parse_transcript(text.replace('output_bytes=50688','output_bytes=50684'),manifest,captures)

    def test_failed_window_cannot_exceed_drained_ledger(self):
        text,manifest,captures=fixture()
        with self.assertRaises(ValueError):soc.parse_transcript(text.replace('source_bytes=136','source_bytes=144'),manifest,captures)

    def test_actual_capture_saturation_must_match_each_task(self):
        text,manifest,captures=fixture();captures[1]['saturated']=0
        with self.assertRaises(ValueError):soc.parse_transcript(text,manifest,captures)

    def test_timing_and_first_last_difference_rejected(self):
        text,manifest,captures=fixture()
        for bad in (text.replace('cycles=225770','cycles=225771'),
                    text.replace('start_ns=53333328.000000','start_ns=53333329.000000')):
            with self.assertRaises(ValueError):soc.parse_transcript(bad,manifest,captures)

    def test_fatal_or_missing_final_marker_rejected(self):
        text,manifest,captures=fixture()
        for bad in (text+'Fatal: mismatch\n',text.replace('DMA16_SEQUENCE_PASS phases=10','INCOMPLETE phases=10')):
            with self.assertRaises(ValueError):soc.parse_transcript(bad,manifest,captures)

    def test_python36_runtime_syntax(self):
        text=Path(soc.__file__).read_text(encoding='utf8')
        tree=ast.parse(text,feature_version=(3,6)) if sys.version_info>=(3,8) else ast.parse(text)
        imports={item.names[0].name for item in ast.walk(tree) if isinstance(item,ast.Import)}
        self.assertFalse(imports & {'numpy','tensorflow','numeric'})

    def test_asic_clock_guard_aliases_cover_complete_sequence(self):
        old='`include "arch03_dma16_monitor.svh"\narch03_clock_mode_guard a3_asic_mode(.clk(a3_mon_clk));'
        text=soc.sequence_testbench(old)
        self.assertIn('wire a3_window_active=(s16_phase!=0) && (s16_completed<10);',text)
        self.assertIn('wire a3_window_finished=(s16_completed==10);',text)
        self.assertLess(text.index('sequence_monitor.svh'),text.index('wire a3_mon_clk'))
        self.assertLess(text.index('wire a3_mon_clk'),text.index('arch03_clock_mode_guard'))
        with self.assertRaises(ValueError):soc.sequence_testbench(old.replace('arch03_clock_mode_guard','missing_guard'))


if __name__=='__main__':unittest.main()
