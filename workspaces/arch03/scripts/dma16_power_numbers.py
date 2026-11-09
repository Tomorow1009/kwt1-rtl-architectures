"""Extract actual PT numerical reports; never grant system power acceptance.

Format checked against installed T-2022.03-SP5-1 report_units/report_power.
Only the observed explicit 1-W dynamic AND leakage units are accepted. Other
unit settings need a reviewed conversion, not an inferred multiplier.
"""
import argparse
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
from dma16_power import POWER_SCOPE, validate_activity

NUMBER = r'(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?'
# The frozen runner requests nine significant digits. A low-precision integer
# zero must not acquire a half-watt rounding allowance and hide a bad total.
POWER_NUMBER = r'[0-9]\.[0-9]{8}[eE][+-][0-9]{2,3}'
GROUPS = ('clock_network', 'register', 'combinational', 'sequential', 'memory', 'io_pad', 'black_box')
LABELS = {'Net Switching Power': 'switching', 'Cell Internal Power': 'internal',
          'Cell Leakage Power': 'leakage', 'Total Power': 'total'}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(4*1024*1024), b''): digest.update(chunk)
    return digest.hexdigest()


def number(token):
    require(re.fullmatch(NUMBER, token) is not None, 'Nonfinite/negative/invalid power number')
    value = Decimal(token)
    require(value.is_finite() and value >= 0, 'Invalid power value')
    return value


def rounding(token):
    # The last displayed decimal digit gives an explicit half-unit bound.
    return Decimal('0.5')*Decimal(10)**number(token).as_tuple().exponent


def check_sum(terms, total, context):
    error = abs(sum(number(x) for x in terms)-number(total))
    require(error <= sum(rounding(x) for x in terms)+rounding(total), 'Power sum mismatch: '+context)


def parse_units(text):
    values = {}
    for line in text.splitlines():
        if re.match(r'\s*(?:Dynamic|Leakage)_power_unit\b', line):
            match = re.fullmatch(r'\s*(Dynamic|Leakage)_power_unit\s*:\s*('+NUMBER+r')\s+Watt\s*', line)
            require(match is not None and match.group(1) not in values, 'Unknown/duplicate PT power units')
            require(number(match.group(2)) == 1, 'PT power unit scale changed; review conversion')
            values[match.group(1)] = '1 Watt'
    require(set(values) == {'Dynamic', 'Leakage'}, 'Missing explicit dynamic/leakage power units')
    return values


def parse_power(units, text):
    unit_values = parse_units(units)
    require(re.search(r'(?m)^\s*Report\s*:\s*Averaged Power\s*$', text), 'Not the reviewed averaged-power report')
    require(re.search(r'(?m)^\s*Design\s*:\s*e203_soc_top\s*$', text), 'Not whole-SoC power')
    totals = {}; groups = {}
    row_pattern = (r'^\s*('+'|'.join(GROUPS)+r')\s+'+r'\s+'.join(['('+POWER_NUMBER+')']*4)+
                   r'\s+\(\s*'+NUMBER+r'%\s*\)\s*([iu]*)\s*$')
    for line in text.splitlines():
        label = next((key for key in LABELS if re.match(r'\s*'+re.escape(key)+r'\s*=', line)), None)
        if label is not None:
            match = re.fullmatch(r'\s*'+re.escape(label)+r'\s*=\s*('+POWER_NUMBER+r')\s*\(\s*'+NUMBER+r'%\s*\)\s*', line)
            key = LABELS[label]
            require(match is not None and key not in totals, 'Missing/duplicate/invalid PT total '+label)
            totals[key] = match.group(1)
        if re.match(r'\s*(?:'+'|'.join(GROUPS)+r')\s', line):
            match = re.fullmatch(row_pattern, line)
            require(match is not None and match.group(1) not in groups, 'Invalid/duplicate PT power group')
            groups[match.group(1)] = dict(zip(('internal', 'switching', 'leakage', 'total'), match.groups()[1:5]))
        elif re.match(r'\s*[A-Za-z_][A-Za-z_0-9]*\s+'+POWER_NUMBER+r'\s+'+POWER_NUMBER, line):
            raise ValueError('Unreviewed PT power group')
    require(set(totals) == set(LABELS.values()) and set(groups) == set(GROUPS), 'Incomplete PT power table/totals')
    for name, row in groups.items(): check_sum([row[k] for k in ('internal', 'switching', 'leakage')], row['total'], name)
    for key in totals: check_sum([groups[name][key] for name in GROUPS], totals[key], 'all groups '+key)
    check_sum([totals[k] for k in ('internal', 'switching', 'leakage')], totals['total'], 'whole SoC')
    return dict(units=unit_values, reported_power_w=totals, reported_group_power_w=groups,
                derived_dynamic_w=str(number(totals['internal'])+number(totals['switching'])),
                note='Strings preserve reported decimal precision; grouping is PT taxonomy, not overlapping module hierarchy.')


def extract(run, expected):
    run = Path(run).resolve(); summary = run/'summary.json'
    require(re.fullmatch('[a-f0-9]{64}', expected) and sha(summary) == expected, 'Power summary digest mismatch')
    report = json.loads(summary.read_text())
    state = json.loads((run.parent/'state.json').read_text())['stages']['dma16_power']
    require(state['status'] == 'passed' and state['summary_sha256'] == expected and
            report.get('scope') == POWER_SCOPE and report.get('status') == 'reports_ready_review_required',
            'Need an actual completed DMA16 PT report collection')
    require({'units.rpt', 'power.rpt', 'power.log'} <= set(report['artifacts']), 'Missing numerical power artifacts')
    texts = {}
    for name, digest in report['artifacts'].items():
        require(Path(name).name == name and sha(run/name) == digest, 'Changed/unsafe power artifact '+name)
        if name.endswith(('.log', '.rpt')): texts[name] = (run/name).read_text(errors='replace')
    require(not any(re.search(r'(?im)^\s*(?:Error-|Error:|Fatal:)', text) for text in texts.values()), 'Actual tool errors require review')
    values = parse_power(texts['units.rpt'], texts['power.rpt'])
    duration = Decimal(validate_activity(report['activity'], report['task_window']))
    require(duration == Decimal(str(report['duration_ns'])), 'Reported power/window duration differs')
    warnings = {}
    for name, text in texts.items():
        codes = re.findall(r'(?m)^\s*Warning:.*\(([A-Z]+-[0-9]+)\)\s*$', text)
        if codes: warnings[name] = {code: codes.count(code) for code in sorted(set(codes))}
    values.update(schema='dma16_power_numbers_v1', status='numbers_extracted_review_required',
        power_run=str(run), power_summary_sha256=expected, case=report['case'],
        synthesis_summary_sha256=report['synthesis_summary_sha256'], gate_summary_sha256=report['gate_summary_sha256'],
        firmware_sha256=report['firmware_sha256'], layout_sha256=report['layout_sha256'],
        duration_ns=str(duration), raw_reported_energy_j=str(number(values['reported_power_w']['total'])*duration*Decimal('1e-9')),
        warning_occurrences_by_artifact=warnings, activity=report['activity'],
        component_leaf_counts=report['component_leaf_counts'], artifacts=report['artifacts'],
        system_power_verified=False, timing_verified=False, approved_average_power_w=None, approved_energy_j=None,
        required_reviews=report['required_reviews'], extractor_sha256=sha(__file__))
    require(sha(summary) == expected, 'Power summary changed while extracting')
    return values


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', required=True, type=Path)
    parser.add_argument('--summary-sha256', required=True)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args(); require(not args.output.exists(), 'Use a new output file')
    result = extract(args.run, args.summary_sha256)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x', encoding='utf8') as stream: json.dump(result, stream, indent=2, ensure_ascii=False, allow_nan=False)
    print('DMA16_POWER_NUMBERS_EXTRACTED system_power_verified=false', args.output)
