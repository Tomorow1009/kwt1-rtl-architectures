"""Audit all twelve frozen PT annotation reports; never approve unknown activity.

This is a report-only check, not a VCD rescan or another power estimate. The
original settings and unknown counters are retained. Python 3.6 standard library.
"""
import argparse
from decimal import Decimal
import json
from pathlib import Path
import re
from dma16_power_numbers import extract, require, sha

LAYERS = tuple('layer_%02d' % i for i in range(1, 13))
MAPPING = ('exact_mapping', 'map_file', 'built_in_mapping', 'ssa', 'sca',
           'clock', 'default', 'propagated', 'implied', 'not_annotated')
HEADER = ('Object Type Exact Mapping (%) Map File (%) Built-in Mapping (%) '
          'SSA (%) SCA (%) Clock (%) Default (%) Propagated(%) Implied(%) Annotated(%) Total')
SETTINGS = ('power_analysis_mode', 'power_x_transition_derate_factor',
            'power_include_initial_x_transitions')


def settings(text):
    result = {}
    for line in text.splitlines():
        fields = line.split()
        if not fields:
            continue
        require(len(fields) == 2 and fields[0] in SETTINGS and fields[0] not in result,
                'Unexpected or duplicate actual power setting')
        result[fields[0]] = fields[1]
    require(set(result) == set(SETTINGS), 'Incomplete actual power settings')
    require(result['power_analysis_mode'] == 'averaged', 'Different power analysis mode')
    factor = Decimal(result['power_x_transition_derate_factor'])
    require(factor.is_finite() and 0 <= factor <= 1, 'Invalid X-transition factor')
    require(result['power_include_initial_x_transitions'] in ('true', 'false'),
            'Invalid initial-X setting')
    result['power_x_transition_derate_factor'] = str(factor.normalize())
    return result


def source_table(lines):
    require(lines.count(HEADER) == 1, 'Unreviewed activity-source columns')
    rows = [line for line in lines if line.startswith('Nets ') and line != 'Nets Driven by']
    require(len(rows) == 1, 'Missing or duplicate whole-design Nets row')
    counts = re.findall(r'(\d+)\(\d+(?:\.\d+)?%\)', rows[0])
    tail = re.sub(r'\d+\(\d+(?:\.\d+)?%\)', '', rows[0]).split()
    require(len(counts) == len(MAPPING) and len(tail) == 2 and tail[0] == 'Nets'
            and tail[1].isdigit(), 'Malformed activity-source counts')
    result = dict(zip(MAPPING, (int(x) for x in counts)))
    result['total'] = int(tail[1])
    require(result['total'] > 0 and sum(result[k] for k in MAPPING) == result['total'],
            'Activity-source counts do not sum to total')
    return result


def sources(text):
    require('-include_mapping_types' in text and re.search(r'(?m)^Design\s*:\s*e203_soc_top\s*$', text),
            'Wrong activity-source report')
    lines = [' '.join(line.split()) for line in text.splitlines()]
    switching = 'Switching Activity Overview Statistics for "e203_soc_top"'
    probability = 'Static Probability Overview Statistics for "e203_soc_top"'
    require(lines.count(switching) == lines.count(probability) == 1,
            'Require separate switching and static-probability overview tables')
    a, b = lines.index(switching), lines.index(probability)
    require(a < b, 'Unreviewed activity-source section order')
    result = source_table(lines[a:b])
    result['static_probability'] = source_table(lines[b:])
    require(result['total'] == result['static_probability']['total'],
            'Switching/static-probability design counts differ')
    return result


def empty_unannotated(text):
    require('-list_not_annotated' in text and '-show_pin' in text and
            re.search(r'(?m)^Design\s*:\s*e203_soc_top\s*$', text), 'Wrong unannotated report')
    marker = 'List of nonannotated nets :'
    require(text.count(marker) == 1, 'Missing or ambiguous unannotated object list')
    require(not text.split(marker, 1)[1].strip(), 'Nonannotated objects require review')
    return dict(explicit_object_list_empty=True)


def build(request_path):
    request_path = Path(request_path).resolve(); request_sha = sha(request_path)
    request = json.loads(request_path.read_text(encoding='utf8'))
    require(request.get('schema') == 'dma16-report-request-v1', 'Wrong frozen report request')
    refs = request.get('power', [])
    require(len(refs) == 12 and len({str(Path(r['run']).resolve()) for r in refs}) == 12,
            'Require twelve distinct power runs')
    rows = []
    for ref in refs:
        run = Path(ref['run']).resolve()
        numeric = extract(run, ref['sha256'])  # Rechecks all original artifact hashes and numbers.
        names = ('power_settings.rpt', 'activity_sources.rpt',
                 'activity_unannotated_before.rpt', 'activity_unannotated_after.rpt')
        require(set(names) <= set(numeric['artifacts']), 'Unbound annotation report')
        texts = {name: (run/name).read_text() for name in names}
        for name in names:
            require(sha(run/name) == numeric['artifacts'][name], 'Annotation report changed')
        actual = settings(texts['power_settings.rpt']); mapping = sources(texts['activity_sources.rpt'])
        require(actual == dict(zip(SETTINGS, ('averaged', '0.5', 'false'))),
                'Different frozen X settings; keep sensitivity runs separate')
        require(mapping['exact_mapping'] + mapping['implied'] == mapping['total'],
                'Default, propagated, unannotated or other activity source requires review')
        probability = mapping['static_probability']
        require(probability['exact_mapping'] + probability['implied'] == probability['total'],
                'Default, propagated, unannotated or other static probability requires review')
        unannotated = {phase: empty_unannotated(texts['activity_unannotated_'+phase+'.rpt'])
                      for phase in ('before', 'after')}
        warnings = numeric['warning_occurrences_by_artifact']
        unknown_codes = sorted({code for counts in warnings.values() for code in counts} - {'PSW-208', 'PTE-003'})
        require(not unknown_codes, 'Additional warning codes require review: '+','.join(unknown_codes))
        rows.append(dict(case=numeric['case'], run=str(run), summary_sha256=ref['sha256'],
            actual_settings=actual, mapping=mapping, unannotated=unannotated,
            activity_sha256=numeric['activity']['sha256'],
            active_value_records=numeric['activity']['active_value_records'],
            unknown_value_records=numeric['activity']['unknown_value_records'],
            warnings_by_artifact=warnings, system_power_verified=False,
            synthesis_summary_sha256=numeric['synthesis_summary_sha256'],
            gate_summary_sha256=numeric['gate_summary_sha256'], firmware_sha256=numeric['firmware_sha256'],
            artifacts_sha256={name: numeric['artifacts'][name] for name in names}))
    require({row['case'] for row in rows} == set(LAYERS), 'Missing/duplicate performance layer')
    for key in ('synthesis_summary_sha256', 'gate_summary_sha256', 'firmware_sha256'):
        require(len({row[key] for row in rows}) == 1, 'Mixed frozen configuration: '+key)
    require(rows[0]['synthesis_summary_sha256'] == request['synthesis']['sha256'] and
            rows[0]['gate_summary_sha256'] == request['gate']['sha256'], 'Wrong requested frozen configuration')
    require(len({row['mapping']['total'] for row in rows}) == 1, 'Mapped design size differs between layers')
    require(sha(request_path) == request_sha, 'Request changed during audit')
    return dict(schema='dma16-twelve-power-annotation-review-v1',
        status='annotation_and_settings_checked_unknown_review_pending',
        request=str(request_path), request_sha256=request_sha, auditor_sha256=sha(__file__),
        numeric_extractor_sha256=sha(Path(__file__).with_name('dma16_power_numbers.py')),
        layers=sorted(rows, key=lambda r: r['case']), system_power_verified=False,
        waveform_rescanned=False, waveform_modified=False,
        limits=['Exact annotation is not proof that unknown values are harmless.',
                'PSW-208 and PTE-003 object reviews remain bound to the original reports.',
                'Unknown durations, valid use, initial-state assumptions and sensitivity require separate review.',
                'Toggle excitation coverage is different from annotation mapping coverage.'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args(); require(not args.output.exists(), 'Use a new diagnostic output')
    result = build(args.request)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x', encoding='utf8') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
    print('DMA16_ANNOTATION_REVIEW_DONE layers=12 system_power_verified=false')


if __name__ == '__main__':
    main()
