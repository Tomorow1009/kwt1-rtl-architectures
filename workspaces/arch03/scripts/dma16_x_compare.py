"""Compare four actual X-model reports without approving system power.

Report-only: verify immutable stage receipts and artifacts, not another VCD scan.
The frozen-setting repeat must reproduce the original printed power numbers.
"""
import argparse
from decimal import Decimal
import json
from pathlib import Path
import re
import dma16_x_sensitivity as sensitivity
import dma16_power_numbers as numbers

require = numbers.require
sha = numbers.sha
IDENTITY = ('case', 'gate_summary_sha256', 'synthesis_summary_sha256',
            'firmware_sha256', 'layout_sha256', 'duration_ns', 'task_window',
            'activity', 'component_leaf_counts', 'tool', 'analysis_inputs')


def analysis_inputs(run):
    data = json.loads((Path(run)/'source_inputs.json').read_text())
    selected = {path: digest for path, digest in data.items()
                if Path(path).name in ('mapped.v', 'mapped.sdc') or Path(path).suffix == '.db'}
    require(sum(Path(p).name == 'mapped.v' for p in selected) == 1 and
            sum(Path(p).name == 'mapped.sdc' for p in selected) == 1 and
            sum(Path(p).suffix == '.db' for p in selected) >= 3,
            'Incomplete mapped design or library identity')
    require(all(re.fullmatch('[a-f0-9]{64}', h) for h in selected.values()),
            'Invalid analysis input digest')
    return selected


def load_point(run, expected):
    run = Path(run).resolve(); summary = run/'summary.json'
    require(re.fullmatch('[a-f0-9]{64}', expected) and sha(summary) == expected,
            'Sensitivity summary digest mismatch')
    report = json.loads(summary.read_text())
    state = json.loads((run.parent/'state.json').read_text())['stages']['dma16_x_sensitivity']
    require(state['status'] == 'passed' and state['summary_sha256'] == expected and
            report.get('scope') == sensitivity.SCOPE and
            report.get('status') == 'diagnostic_reports_ready_review_required',
            'Need a completed sensitivity diagnostic')
    require(all(report.get(k) is False for k in
                ('system_power_verified', 'physical_error_bound', 'replaces_frozen_estimate')),
            'Diagnostic cannot claim power approval')
    required = set(sensitivity.power.REQUIRED) | {'numbers.json', 'power.log', 'source_inputs.json', 'x_sensitivity.tcl'}
    require(required <= set(report['artifacts']), 'Missing sensitivity artifacts')
    for name, digest in report['artifacts'].items():
        require(Path(name).name == name and sha(run/name) == digest, 'Changed sensitivity artifact '+name)
    duration = sensitivity.power.validate_activity(report['activity'], report['task_window'])
    require(Decimal(duration) == Decimal(report['duration_ns']), 'Sensitivity window changed')
    values = sensitivity.numeric_reports(run, duration, report['point'])
    require(values == json.loads((run/'numbers.json').read_text()), 'Saved/recomputed sensitivity numbers differ')
    require(values['actual_settings'] == report['actual_settings'], 'Summary/report settings differ')
    identity = {key: report[key] for key in IDENTITY if key != 'analysis_inputs'}
    identity['analysis_inputs'] = analysis_inputs(run)
    require(sha(summary) == expected, 'Sensitivity summary changed during review')
    return dict(point=report['point'], run=str(run), summary_sha256=expected,
                identity=identity, values=values)


def load_baseline(run, expected):
    run = Path(run).resolve()
    values = numbers.extract(run, expected)
    report = json.loads((run/'summary.json').read_text())
    identity = {key: report[key] for key in IDENTITY if key != 'analysis_inputs'}
    identity['analysis_inputs'] = analysis_inputs(run)
    actual = sensitivity.annotation.settings((run/'power_settings.rpt').read_text())
    require(actual == sensitivity.point_settings('frozen'), 'Original estimate uses different X settings')
    return dict(run=str(run), summary_sha256=expected, identity=identity, values=values)


def compare(points, baseline):
    require(len(points) == 4 and {p['point'] for p in points} == set(sensitivity.POINTS),
            'Require exactly four distinct diagnostic points')
    require(len({p['run'] for p in points}) == 4 and baseline['run'] not in {p['run'] for p in points},
            'Each diagnostic and original estimate needs its own run')
    for point in points:
        require(point['identity'] == baseline['identity'], 'Different frozen design, window, activity or libraries')
        require(point['values']['actual_settings'] == sensitivity.point_settings(point['point']),
                'Wrong diagnostic point settings')
    by_point = {p['point']: p for p in points}; reference = baseline['values']
    frozen = by_point['frozen']['values']
    for field in ('reported_power_w', 'reported_group_power_w', 'module_breakdown', 'sram_breakdown'):
        require(frozen[field] == reference[field], 'Frozen repeat differs from original '+field)
    require(frozen['boundary_inclusive'] == reference['boundary_inclusive'] and
            frozen['raw_reported_energy_j'] == reference['raw_reported_energy_j'],
            'Frozen repeat energy/boundary differs from original')
    rows = []
    for name in ('zero', 'frozen', 'one', 'initial'):
        point = by_point[name]; values = point['values']
        row = dict(point=name, run=point['run'], summary_sha256=point['summary_sha256'],
                   actual_settings=values['actual_settings'], reported_power_w=values['reported_power_w'],
                   raw_reported_energy_j=values['raw_reported_energy_j'],
                   boundary_inclusive=values['boundary_inclusive'])
        row['delta_from_original_power_w'] = {
            key: str(Decimal(values['reported_power_w'][key])-Decimal(reference['reported_power_w'][key]))
            for key in numbers.KEYS}
        row['delta_from_original_energy_j'] = str(Decimal(values['raw_reported_energy_j'])-
                                                  Decimal(reference['raw_reported_energy_j']))
        rows.append(row)
    energies = [Decimal(row['raw_reported_energy_j']) for row in rows]
    return dict(schema='dma16_x_sensitivity_comparison_v1',
                status='diagnostic_comparison_ready_review_required', identity=baseline['identity'],
                baseline=dict(run=baseline['run'], summary_sha256=baseline['summary_sha256']),
                frozen_repeat_exactly_reproduced=True, points=rows,
                selected_point_energy_spread_j=str(max(energies)-min(energies)),
                system_power_verified=False, physical_error_bound=False, replaces_frozen_estimate=False,
                limits=['Selected PT X-model sensitivity is not a bound on physical initial states.',
                        'Original averaged 0.5/false estimate remains the frozen reference.',
                        'Artifact-only review relies on the stage full-waveform integrity checks.'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args(); require(not args.output.exists(), 'Use a new comparison output')
    request = json.loads(args.request.read_text()); before = sha(args.request)
    result = compare([load_point(Path(p['run']), p['summary_sha256']) for p in request['points']],
                     load_baseline(Path(request['baseline']['run']), request['baseline']['summary_sha256']))
    require(sha(args.request) == before, 'Comparison request changed')
    result.update(request_sha256=before, comparison_source_sha256=sha(__file__))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x', encoding='utf8') as stream:
        json.dump(result, stream, indent=2, ensure_ascii=False, allow_nan=False)
    print('DMA16_X_COMPARISON_READY system_power_verified=false', args.output)


if __name__ == '__main__':
    main()
