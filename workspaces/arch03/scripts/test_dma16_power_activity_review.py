"""Report-format and provenance tests, not hardware or power acceptance."""
import ast
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import dma16_power_activity_review as p


def settings():
    return '\n'.join(k+' '+v for k, v in zip(p.SETTINGS, ('averaged', '0.5', 'false')))+'\n'


def sources(counts=None):
    counts = counts or [152986]+[0]*7+[1, 0]
    return ('Report : Switching Activity\n-include_mapping_types\nDesign : e203_soc_top\n'+p.HEADER+
            '\nNets '+' '.join(str(n)+'(0.00%)' for n in counts)+' '+str(sum(counts))+'\n')


def unannotated():
    return ('Report : Switching Activity\n-list_not_annotated\n-show_pin\nDesign : e203_soc_top\n'
            'List of nonannotated nets :\n\n')


def fixture(root):
    refs = []; records = {}
    for i in range(1, 13):
        run = root/('layer_%02d' % i); run.mkdir()
        texts = {'power_settings.rpt': settings(), 'activity_sources.rpt': sources(),
                 'activity_unannotated_before.rpt': unannotated(), 'activity_unannotated_after.rpt': unannotated()}
        for name, text in texts.items():
            (run/name).write_text(text)
        refs.append(dict(run=str(run), sha256=('%064x' % i)))
        records[str(run)] = dict(case=run.name, synthesis_summary_sha256='a'*64,
            gate_summary_sha256='b'*64, firmware_sha256='c'*64,
            activity=dict(sha256='%064x' % (i+100), active_value_records=1000000, unknown_value_records=100+i),
            warning_occurrences_by_artifact={'power.log': {'PSW-208': 774}, 'timing_check.rpt': {'PTE-003': 1}},
            artifacts={name: p.sha(run/name) for name in texts})
    request = dict(schema='dma16-report-request-v1', power=refs,
                   synthesis=dict(sha256='a'*64), gate=dict(sha256='b'*64))
    path = root/'request.json'; path.write_text(json.dumps(request))
    return path, records


class PowerActivityReviewTests(unittest.TestCase):
    def test_settings_are_actual_complete_and_unambiguous(self):
        self.assertEqual(p.settings(settings())['power_x_transition_derate_factor'], '0.5')
        for text in (settings()+'power_analysis_mode averaged\n', settings().replace(' false', ' zero'),
                     settings().replace('0.5', 'NaN'), settings().replace('0.5', '1.1'),
                     settings().replace('averaged', 'time_based'), settings().splitlines()[0]):
            with self.subTest(text=text), self.assertRaises(ValueError):
                p.settings(text)

    def test_mapping_columns_and_counts_are_checked_not_percentages(self):
        values = p.sources(sources())
        self.assertEqual((values['exact_mapping'], values['implied'], values['total']), (152986, 1, 152987))
        for text in (sources().replace('Map File', 'Other Source'), sources()+sources(),
                     sources().replace(' 152987\n', ' 152988\n'), sources().replace('Nets ', 'Pins '),
                     sources().replace('e203_soc_top', 'other_design'), sources().replace('0(0.00%) ', '', 1)):
            with self.subTest(text=text), self.assertRaises(ValueError):
                p.sources(text)

    def test_explicit_empty_list_required_and_no_uncovered_pin_hidden(self):
        self.assertTrue(p.empty_unannotated(unannotated())['explicit_object_list_empty'])
        for text in (unannotated()+'soc/unseen/Q\n', unannotated().replace('nonannotated', 'covered'),
                     unannotated()+unannotated(), unannotated().replace('-show_pin', '')):
            with self.subTest(text=text), self.assertRaises(ValueError):
                p.empty_unannotated(text)

    def test_all_twelve_keep_unknowns_and_do_not_approve_power(self):
        with tempfile.TemporaryDirectory() as directory:
            request, records = fixture(Path(directory))
            with patch.object(p, 'extract', side_effect=lambda run, digest: records[str(run)]):
                result = p.build(request)
            self.assertEqual([x['case'] for x in result['layers']], list(p.LAYERS))
            self.assertEqual([x['unknown_value_records'] for x in result['layers']], list(range(101, 113)))
            self.assertFalse(result['system_power_verified'])
            self.assertFalse(result['waveform_rescanned'])
            self.assertTrue(all(not x['system_power_verified'] for x in result['layers']))

    def test_missing_duplicate_mixed_source_or_unreviewed_warning_is_rejected(self):
        mutations = [lambda r: r.update(case='layer_01'), lambda r: r.update(firmware_sha256='d'*64),
                     lambda r: r.update(synthesis_summary_sha256='e'*64),
                     lambda r: r.update(warning_occurrences_by_artifact={'power.log': {'NEW-999': 1}})]
        with tempfile.TemporaryDirectory() as directory:
            request, base = fixture(Path(directory))
            for mutate in mutations:
                records = copy.deepcopy(base); mutate(records[str(Path(directory)/'layer_12')])
                with patch.object(p, 'extract', side_effect=lambda run, digest: records[str(run)]):
                    with self.assertRaises(ValueError): p.build(request)
            q = json.loads(request.read_text()); q['power'].pop(); request.write_text(json.dumps(q))
            with self.assertRaisesRegex(ValueError, 'twelve'): p.build(request)

    def test_artifact_change_default_mapping_and_sensitivity_settings_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            request, records = fixture(Path(directory)); run = Path(directory)/'layer_12'
            with patch.object(p, 'extract', side_effect=lambda run, digest: records[str(run)]):
                (run/'power_settings.rpt').write_text(settings().replace('0.5', '0'))
                with self.assertRaisesRegex(ValueError, 'changed'): p.build(request)
                records[str(run)]['artifacts']['power_settings.rpt'] = p.sha(run/'power_settings.rpt')
                with self.assertRaisesRegex(ValueError, 'Different frozen X'): p.build(request)
                (run/'power_settings.rpt').write_text(settings())
                records[str(run)]['artifacts']['power_settings.rpt'] = p.sha(run/'power_settings.rpt')
                counts = [152985]+[0]*5+[1, 0, 1, 0]
                (run/'activity_sources.rpt').write_text(sources(counts))
                records[str(run)]['artifacts']['activity_sources.rpt'] = p.sha(run/'activity_sources.rpt')
                with self.assertRaisesRegex(ValueError, 'activity source'): p.build(request)

    def test_request_mutation_during_audit_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            request, records = fixture(Path(directory))
            def change(run, digest):
                if run.name == 'layer_12': request.write_text(request.read_text()+'\n')
                return records[str(run)]
            with patch.object(p, 'extract', side_effect=change):
                with self.assertRaisesRegex(ValueError, 'Request changed'): p.build(request)

    def test_python36_grammar(self):
        ast.parse(Path(p.__file__).read_text(), feature_version=(3, 6))


if __name__ == '__main__':
    unittest.main()
