import ast
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import mmio8_timing_objects as p


def clocks(pins):
    return ('Information: Checking no_clock\nWarning: There are %d register clock pins with no clock.\n'
            '\nClock Pin\n------------------\n%s\n\nInformation: Checking partial_delay\n' %
            (len(pins), '\n'.join(pins)))


DISABLED = '''Report : disable_timing
    -nosplit
Design : e203_soc_top
Flags: C conditional arc
Cell or Port From To Sense Flag Reason
--------------------------------------
top/U1 A1 Z positive_unate p A1 = 0
top/U2 CEN Q nonseq_setup_fall_clk_fall C A & B
top/U3 A Z negative_unate c A = 0
top/U4 A Z non_unate d !(A | B)

1
'''
SDC = ''.join('set_case_analysis 0 [get_ports io_pads_jtag_%s_i_ival]\n' % s for s in ('TCK','TMS','TDI'))


class TimingObjectsTests(unittest.TestCase):
    def test_complete_clock_table_preserves_both_edge_types_and_unreviewed_objects(self):
        pins = [p.DTM+'irReg_reg[0]/CKN', p.RESET+'reset_n_catch_reg/reg_0/q_reg/CK', 'top/other/CK']
        value = p.no_clock(clocks(pins))
        self.assertEqual(value['count'], 3)
        self.assertEqual(value['groups'], {'static_jtag_dtm':1,'static_jtag_reset_sync':1,'unreviewed':1})
        self.assertEqual(value['pin_types'], {'CKN':1,'CK':2})
        self.assertEqual([r['pin'] for r in value['pins']], pins)

    def test_missing_duplicated_or_unparsed_clock_rows_are_rejected(self):
        good = clocks(['top/a/CK', 'top/b/CKN'])
        for text in (good.replace('top/b/CKN\n',''), good.replace('top/b/CKN','top/a/CK'),
                     good.replace('top/b/CKN','top/b/OTHER'), good+good,
                     good.replace('Information: Checking partial_delay','end')):
            with self.subTest(text=text), self.assertRaises(ValueError): p.no_clock(text)

    def test_all_disabled_arcs_conditions_and_duplicate_looking_rows_are_retained(self):
        value = p.disabled_arcs(DISABLED)
        self.assertEqual(value['flag_counts'], {'p':1,'C':1,'c':1,'d':1})
        self.assertEqual(value['rows'][1]['reason'], 'A & B')
        self.assertFalse(value['has_user_or_loop_or_false_net_flags'])
        changed = DISABLED.replace('top/U1 A1 Z positive_unate p A1 = 0',
            'top/U1 A1 Z positive_unate u\ntop/U1 A1 Z positive_unate l conditional')
        parsed = p.disabled_arcs(changed)
        self.assertEqual(parsed['count'], 5)
        self.assertTrue(parsed['has_user_or_loop_or_false_net_flags'])

    def test_incomplete_report_and_unclassified_rows_are_not_silently_filtered(self):
        for text in (DISABLED.replace('\n1\n','\n'), DISABLED.replace('-nosplit',''),
                     DISABLED.replace('top/U3 A Z negative_unate c A = 0','malformed row'),
                     DISABLED.replace('negative_unate c','negative_unate q'),
                     DISABLED.replace('top/U4 A Z non_unate d !(A | B)','top/U4 A Z non_unate'),
                     DISABLED+'other/report/row\n'):
            with self.subTest(text=text), self.assertRaises(ValueError): p.disabled_arcs(text)

    def test_static_jtag_requires_all_three_actual_single_constraints(self):
        self.assertEqual(len(p.jtag_cases(SDC)), 3)
        for text in (SDC.replace('TCK','other'), SDC.replace('set_case_analysis 0','set_case_analysis 1',1), SDC+SDC):
            with self.assertRaises(ValueError): p.jtag_cases(text)

    def test_actual_stage_identity_read_only_and_no_inherited_acceptance(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); s=root/'s'; s.mkdir(); q=root/'p'; q.mkdir()
            for path,text in ((s/'mapped.sdc',SDC),(s/'summary.json','{}'),(q/'summary.json','{}'),
                              (q/'timing_check.rpt',clocks([p.DTM+'a/CK'])),(q/'disabled_timing.rpt',DISABLED)):
                path.write_text(text)
            request=dict(schema='mmio8-timing-objects-request-v1', synthesis={'run':str(s),'sha256':'a'*64},
                         power={'run':str(q),'sha256':'b'*64})
            synthesis=dict(scope=p.mmio8_synth.SCOPE,DMA_present=False)
            power=dict(scope=p.mmio8_power.SCOPE,DMA_present=False,synthesis_summary_sha256='a'*64)
            with patch.object(p.common,'load_stage',side_effect=[synthesis,power]) as load:
                value=p.audit(request)
                self.assertEqual([c.args[1] for c in load.call_args_list], ['mmio8_synth','mmio8_power'])
                self.assertFalse(value['timing_verified']); self.assertFalse(value['netlist_modified'])
                self.assertFalse(value['system_power_verified'])
                self.assertTrue(all(p.sha(Path(x))==h for x,h in value['inputs_sha256'].items()))
            power['synthesis_summary_sha256']='c'*64
            with patch.object(p.common,'load_stage',side_effect=[synthesis,power]):
                with self.assertRaises(ValueError):p.audit(request)

    def test_python36_grammar(self):
        ast.parse(Path(p.__file__).read_text(),feature_version=(3,6))


if __name__ == '__main__': unittest.main()
