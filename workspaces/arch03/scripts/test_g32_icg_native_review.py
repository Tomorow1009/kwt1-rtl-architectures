import json
from pathlib import Path
import tempfile
import unittest
import g32_icg_native_review as m


def fixture(root,bad=None):
    run=root/'icg';run.mkdir();synth=root/'synth';synth.mkdir();(synth/'mapped.v').write_text('mapped')
    cell='u/array/pe/cell_icg'
    mapping=dict(actual_g32_cells=1,rows={cell:{}})
    (synth/'summary.json').write_text(json.dumps(dict(icg_mapping=mapping,artifacts={'mapped.v':m.digest(synth/'mapped.v')})))
    texts={'clock_gating_checks.rpt':'Report : clock gating check\n'+cell+' E CK 0.11 -0.03 0.10 -0.04 High P L\n',
        'clock_gating_paths.tsv':'schema\tg32-clock-gating-paths-v1\ntest_enable\t'+cell+'\t0\npath\t'+cell+'\tmax\t0.1\t'+cell+'/E\npath\t'+cell+'\tmin\t0.2\t'+cell+'/E\ncount\t1\n'}
    for name,delay in [('setup','max'),('hold','min')]:
        texts['clock_gating_'+name+'.rpt']='Report : timing\n-delay_type '+delay+'\n-slack_lesser_than 0.0000000000\nNo paths with slack less than 0.0000000000\n'
    if bad: texts[bad[0]]=bad[1]
    for n,t in texts.items():(run/n).write_text(t)
    s=dict(synthesis_run=str(synth),synthesis_summary_sha256=m.digest(synth/'summary.json'),
        netlist_sha256=m.digest(synth/'mapped.v'),artifacts={n:m.digest(run/n) for n in texts})
    (run/'summary.json').write_text(json.dumps(s));return run,m.digest(run/'summary.json')


class NativeReview(unittest.TestCase):
    def test_explicit_per_gate_paths_plus_no_negative_slack_report(self):
        with tempfile.TemporaryDirectory() as d:
            r=m.review(*fixture(Path(d)));self.assertEqual(r['per_ICG_setup_hold_paths'],2)
            self.assertTrue(r['native_negative_slack_reports_clear']);self.assertFalse(r['physical_signoff'])

    def test_missing_gate_definition_or_unknown_empty_report_is_not_pass(self):
        for bad in [('clock_gating_checks.rpt','Report : clock gating check\n'),
                    ('clock_gating_hold.rpt','No paths.\n')]:
            with tempfile.TemporaryDirectory() as d:
                with self.assertRaises(ValueError):m.review(*fixture(Path(d),bad))


if __name__=='__main__':unittest.main()
