"""Raw numeric extraction for the new source-loaded original-MMIO8 reference.

The shared installed-PT parser keeps the exact same units/rounding treatment.
The run scope, activity window and 138-macro inventory remain independent.
No extracted value grants system-power acceptance. Python 3.6 stdlib only.
"""
import argparse
import json
import re
from decimal import Decimal
from pathlib import Path
import dma16_power_numbers as shared
from mmio8_power import SCOPE, validate_activity


def parse_hierarchy(text, totals):
    # Both source-loading fabrics have the same actual hierarchy tokens. These
    # two modules are CPU-source routing in MMIO8, not an eight-lane DMA engine.
    result = shared.parse_hierarchy(text, totals)
    for group in ('modules', 'inclusive_module_rows'):
        rows = result[group]
        for old, new in (('dma_arbiter', 'source_arbiter'), ('dma_router', 'source_router')):
            rows[new] = rows.pop(old)
    return result


def extract(run, expected):
    run = Path(run).resolve(); summary = run/'summary.json'
    shared.require(re.fullmatch('[a-f0-9]{64}', expected) and shared.sha(summary) == expected,
                   'MMIO8 power summary digest mismatch')
    report = json.loads(summary.read_text())
    state = json.loads((run.parent/'state.json').read_text()).get('stages', {}).get('mmio8_power', {})
    shared.require(state.get('status') == 'passed' and state.get('summary_sha256') == expected and
        report.get('scope') == SCOPE and report.get('DMA_present') is False and
        report.get('status') == 'reports_ready_review_required', 'Need actual new-source MMIO8 PT report collection')
    shared.require({'units.rpt', 'power_verbose.rpt', 'power.rpt', 'power.log', 'power_hierarchy.rpt',
                    'power_sram.rpt'} <= set(report['artifacts']), 'Missing MMIO8 numerical power artifacts')
    texts = {}
    for name, digest in report['artifacts'].items():
        shared.require(Path(name).name == name and shared.sha(run/name) == digest, 'Changed/unsafe MMIO8 power artifact '+name)
        if name.endswith(('.log', '.rpt')): texts[name] = (run/name).read_text(errors='replace')
    shared.require(not any(re.search(r'(?im)^\s*(?:Error-|Error:|Fatal:)', text) for text in texts.values()),
                   'Actual MMIO8 tool errors require review')
    values = shared.parse_power(texts['power_verbose.rpt'], texts['power.rpt'])
    values['base_units'] = shared.parse_base_units(texts['units.rpt'])
    verbose = shared.parse_power(texts['power_verbose.rpt'], texts['power_verbose.rpt'])
    shared.require(values['reported_power_w'] == verbose['reported_power_w'] and
        values['reported_group_power_w'] == verbose['reported_group_power_w'], 'MMIO8 normal/verbose reports disagree')
    values['module_breakdown'] = parse_hierarchy(texts['power_hierarchy.rpt'], values['reported_power_w'])
    values['sram_breakdown'] = shared.parse_sram(texts['power_sram.rpt'], profile='mmio8_source')
    duration = Decimal(validate_activity(report['activity'], report['task_window']))
    shared.require(duration == Decimal(str(report['duration_ns'])), 'MMIO8 exact power interval differs')
    values['boundary_inclusive'] = None
    if 'power_with_boundary_nets.rpt' in texts:
        values['boundary_inclusive'] = shared.parse_boundary_power(texts['power_with_boundary_nets.rpt'], values)
        values['boundary_inclusive']['raw_reported_energy_j'] = str(
            shared.number(values['boundary_inclusive']['reported_power_w']['total'])*duration*Decimal('1e-9'))
    warnings = {}
    for name, text in texts.items():
        codes = re.findall(r'(?m)^\s*Warning:.*\(([A-Z]+-[0-9]+)\)\s*$', text)
        if codes: warnings[name] = {code: codes.count(code) for code in sorted(set(codes))}
    values.update(schema='mmio8_source_power_numbers_v1', status='numbers_extracted_review_required', DMA_present=False,
        power_run=str(run), power_summary_sha256=expected, case=report['case'],
        synthesis_summary_sha256=report['synthesis_summary_sha256'], gate_summary_sha256=report['gate_summary_sha256'],
        firmware_sha256=report['firmware_sha256'], layout_sha256=report['layout_sha256'],
        duration_ns=str(duration), raw_reported_energy_j=str(shared.number(values['reported_power_w']['total'])*duration*Decimal('1e-9')),
        warning_occurrences_by_artifact=warnings, activity=report['activity'],
        component_leaf_counts=report['component_leaf_counts'], artifacts=report['artifacts'],
        system_power_verified=False, timing_verified=False, approved_average_power_w=None, approved_energy_j=None,
        required_reviews=report['required_reviews'], extractor_sha256=shared.sha(__file__),
        shared_numeric_parser_sha256=shared.sha(shared.__file__))
    shared.require(shared.sha(summary) == expected, 'MMIO8 summary changed while extracting')
    return values


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', required=True, type=Path)
    parser.add_argument('--summary-sha256', required=True)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args(); shared.require(not args.output.exists(), 'Use a new MMIO8 output file')
    result = extract(args.run, args.summary_sha256)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x', encoding='utf8') as stream:
        json.dump(result, stream, indent=2, ensure_ascii=False, allow_nan=False)
    print('MMIO8_SOURCE_POWER_NUMBERS_EXTRACTED system_power_verified=false', args.output)
