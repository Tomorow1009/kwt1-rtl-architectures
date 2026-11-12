"""Read existing B0 power evidence only; no EDA, SAIF scan, or approval.

Python 3.6 standard library. The caller may redirect stdout to a NEW receipt.
Paths must stay inside --scope-root. Only named, bounded small files are read;
large SAIF files are stat'ed, never read. No imports of production run tools.
"""
import argparse
from collections import Counter
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import sys

LAYERS = tuple('layer_%02d' % i for i in range(1, 13))
SMALL_REPORTS = ('numbers.json', 'units.rpt', 'power.rpt', 'power_verbose.rpt',
    'power_with_boundary_nets.rpt', 'power_hierarchy.rpt', 'power_sram.rpt',
    'power_settings.rpt', 'activity_sources.rpt', 'activity_unannotated_before.rpt',
    'activity_unannotated_after.rpt', 'native_isolated_connections.tsv',
    'power.log', 'timing_check.rpt', 'disabled_timing.rpt', 'clocks.rpt',
    'power_clock.txt', 'power_clock_input.json', 'power_component_inventory.tsv',
    'power_sysmem_ports.tsv')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


class Reader:
    def __init__(self, scope, max_file_bytes=16 * 1024 * 1024,
                 max_total_bytes=128 * 1024 * 1024):
        self.scope = Path(scope).resolve()
        self.max_file_bytes = max_file_bytes
        self.max_total_bytes = max_total_bytes
        self.bytes_read = 0
        self.reads = {}

    def path(self, path):
        path = Path(path).resolve()
        path.relative_to(self.scope)
        return path

    def read(self, path, expected=None):
        path = self.path(path)
        require(path.is_file(), 'Missing evidence file: ' + str(path))
        size = path.stat().st_size
        require(size <= self.max_file_bytes, 'File exceeds bounded read: ' + str(path))
        require(self.bytes_read + size <= self.max_total_bytes, 'Small-file read budget exceeded')
        raw = path.read_bytes()
        self.bytes_read += len(raw)
        require(len(raw) == size, 'File changed while reading: ' + str(path))
        value = digest(raw)
        if expected is not None:
            require(re.fullmatch('[0-9a-f]{64}', expected) and value == expected,
                    'Evidence SHA differs: ' + str(path))
        if str(path) in self.reads:
            require(self.reads[str(path)]['sha256'] == value, 'Evidence changed: ' + str(path))
        self.reads[str(path)] = dict(bytes=len(raw), sha256=value)
        return raw

    def json(self, path, expected=None):
        return json.loads(self.read(path, expected).decode('utf8'))

    def stage(self, ref, name):
        run = self.path(ref['run'])
        result = self.json(run / 'summary.json', ref['sha256'])
        state = self.json(run.parent / 'state.json')['stages'][name]
        require(state['status'] == 'passed' and state['summary_sha256'] == ref['sha256'],
                'Stage has not completed: ' + name)
        return run, result

    def artifact(self, run, summary, name):
        require(Path(name).name == name, 'Unsafe artifact name')
        require(name in summary['artifacts'], 'No frozen artifact hash: ' + name)
        return self.read(run / name, summary['artifacts'][name])

    def unchanged(self):
        # All are small evidence files. Never touch raw waves, libraries/netlists,
        # simulation outputs, or the 1200 task tree in this closing check.
        for name, item in list(self.reads.items()):
            self.read(name, item['sha256'])


def compact_activity(activity):
    result = {key: activity[key] for key in (
        'file', 'bytes', 'sha256', 'duration_ns', 'timescale_ns', 'statistics',
        'unknown_representation', 'X_and_Z_separately_measured',
        'declaration_counts_include_aliases', 'component_counts_overlap')}
    result['component_activity'] = {}
    for key, row in activity['component_activity'].items():
        copy = dict(row)
        copy['unknown_examples'] = row.get('unknown_examples', [])[:3]
        copy['examples_are_not_complete_unknown_signal_inventory'] = True
        result['component_activity'][key] = copy
    return result


def excerpts(raw):
    text = raw.decode('utf8', errors='replace')
    warning_codes = Counter(re.findall(r'\b(?:PSW|PWR|PTE|TIM|LINK)-[0-9]+\b', text))
    found = [line.strip()[:350] for line in text.splitlines() if re.search(
        r'(?i)error:|fatal:|warning:|unknown|black.box|wire.load|parasitic|no.clock|disabled|unannotated|boundary|x.transition', line)]
    return dict(warning_code_counts=dict(sorted(warning_codes.items())),
        selected_lines=found[:20], selected_lines_total=len(found),
        excerpt_truncated=len(found) > 20)


def inspect(report_path, scope_root, max_file_bytes=16 * 1024 * 1024,
            max_total_bytes=128 * 1024 * 1024):
    reader = Reader(scope_root, max_file_bytes, max_total_bytes)
    report_path = reader.path(report_path)
    receipt = reader.json(report_path.parent / 'receipt.json')
    require(receipt['schema'] == 'systolic-b-export-receipt-v1', 'Wrong export receipt')
    report = reader.json(report_path, receipt['artifacts']['report.json'])
    require(report['schema'] == 'systolic-b-evidence-export-v1', 'Not a B0 export')
    cases = {row['case']: row for row in report['cases']}
    require(len(report['cases']) == 12 and set(cases) == set(LAYERS), 'Incomplete/duplicate fixed12')
    require(len(report['power_references']) == 12, 'Missing fixed12 power references')
    arun, activity = reader.stage(report['activity_reference'], 'systolic_b_saif')
    require(activity['status'] == 'B_native_saif_function_and_complete_windows_passed', 'Wrong activity status')
    activity_cases = {row['case']: row for row in activity['cases']}
    require(len(activity['cases']) == 12 and set(activity_cases) == set(LAYERS), 'Incomplete activity12')
    srun, synthesis = reader.stage(report['references']['synthesis'], 'systolic_b_synth')
    require(synthesis['artifacts']['mapped.v'] == report['netlist_sha256'], 'Different exported netlist')
    require(synthesis['link_report']['library_inputs'] == report['libraries_sha256'], 'Different exported libraries')
    models = {}
    for name in ('technology_verification.json', 'memory_library_verification.json'):
        if name not in synthesis['artifacts'] or not (srun / name).is_file():
            models[name] = dict(status='missing_receipt_requires_reading_original_synthesis')
        else:
            raw = reader.artifact(srun, synthesis, name)
            models[name] = dict(sha256=digest(raw), receipt=json.loads(raw.decode('utf8')),
                               actual_library_files_rehashed=False)
    layers = {}
    for ref in report['power_references']:
        run, power = reader.stage(ref, 'systolic_b_power')
        name = power['case']
        require(name in LAYERS and name not in layers, 'Wrong/duplicate power layer')
        require(power['scope'] == 'systolic_b_whole_soc_native_saif_pre_layout_power', 'Wrong power scope')
        require(power['status'] == 'reports_and_numbers_ready_unknown_impact_review_required', 'Wrong power status')
        for key, value in (('synthesis_summary_sha256', report['references']['synthesis']['sha256']),
                ('gate_summary_sha256', report['references']['gate']['sha256']),
                ('activity_summary_sha256', report['activity_reference']['sha256']),
                ('firmware_sha256', report['firmware_sha256'])):
            require(power[key] == value, 'Mixed power identity: ' + key)
        row = cases[name]
        act = activity_cases[name]
        require(power['task_window'] == act['task_window'] and
                power['activity'] == act['activity'] == row['activity'], 'Mixed power/activity window')
        require(power['numbers'] == row['power'], 'Exported numbers changed')
        numeric = json.loads(reader.artifact(run, power, 'numbers.json').decode('utf8'))
        require(numeric == power['numbers'], 'numbers.json differs from frozen summary')
        require(Decimal(numeric['duration_ns']) == Decimal(row['duration_ns']), 'Duration differs')
        require(Decimal(numeric['average_power_w']) == Decimal(row['raw_average_power_w']) and
                Decimal(numeric['energy_j']) == Decimal(row['raw_energy_j']), 'Power/energy differs')
        mapping = numeric['sources']
        isolated = numeric['isolated_defaults']
        for table in (mapping, mapping['static_probability']):
            require(table['default'] == isolated['count'] and
                    table['exact_mapping'] + table['implied'] + isolated['count'] == table['total'],
                    'Activity mapping gap beyond proven isolated defaults')
        raw_reports = {}
        for filename in SMALL_REPORTS:
            if filename not in power['artifacts']:
                raw_reports[filename] = dict(status='missing_frozen_small_artifact')
                continue
            raw = reader.artifact(run, power, filename)
            raw_reports[filename] = dict(bytes=len(raw), sha256=digest(raw))
            if filename != 'numbers.json':
                raw_reports[filename].update(excerpts(raw))
            if filename in ('disabled_timing.rpt', 'timing_check.rpt', 'power_with_boundary_nets.rpt'):
                lines = raw.decode('utf8', errors='replace').splitlines()
                raw_reports[filename]['first_40_lines'] = lines[:40]
                raw_reports[filename]['full_line_count'] = len(lines)
        saif = reader.path(arun / act['activity']['file'])
        require(saif.suffix == '.saif', 'Not a SAIF activity file')
        size = saif.stat().st_size if saif.is_file() else None
        require(size == act['activity']['bytes'], 'Stored SAIF absent/size differs')
        condensed = dict(numeric)
        condensed['sram'] = {key: value for key, value in numeric['sram'].items() if key != 'cells'}
        leakage = {}
        for cell in numeric['sram'].get('cells', {}).values():
            owner = cell['owner']
            leakage.setdefault(owner, Counter())[cell['reported_power_w']['leakage']] += 1
        condensed['sram']['per_cell_leakage_w_histogram_by_owner'] = {
            owner: dict(sorted(values.items())) for owner, values in leakage.items()}
        condensed['isolated_defaults'] = {key: value for key, value in isolated.items() if key != 'names'}
        layers[name] = dict(run=str(run), summary_sha256=ref['sha256'],
            numbers=condensed, activity=compact_activity(act['activity']),
            component_leaf_counts=power['component_leaf_counts'], power_clock=power['power_clock'],
            raw_reports=raw_reports, saif_current_bytes=size, saif_fresh_hash_verified=False,
            saif_original_audit_receipt_bound=True, required_reviews=power['required_reviews'])
    require(set(layers) == set(LAYERS), 'Incomplete power12')
    duration = sum(Decimal(cases[name]['duration_ns']) for name in LAYERS)
    energy = sum(Decimal(cases[name]['raw_energy_j']) for name in LAYERS)
    weighted = energy / (duration * Decimal('1e-9'))
    per_task = energy / 12
    require(weighted == Decimal(report['aggregate']['raw_time_weighted_power_w']) and
            per_task == Decimal(report['aggregate']['raw_energy_per_task_j']), 'Exported weighted aggregate differs')
    reader.unchanged()
    return dict(schema='b0-read-only-power-review-inventory-v1',
        status='read_only_inventory_collected_review_required', system_power_verified=False,
        report=str(report_path), report_sha256=receipt['artifacts']['report.json'],
        production_hardware=report['production_hardware'], netlist_sha256=report['netlist_sha256'],
        libraries_sha256=report['libraries_sha256'], conditions=report['conditions'],
        aggregate=dict(duration_ns=str(duration), energy_j=str(energy),
            raw_time_weighted_power_w=str(weighted), raw_energy_per_task_j=str(per_task)),
        model_receipts=models, layers=layers, files_read=reader.reads, bytes_read=reader.bytes_read,
        no_eda_or_simulation_started=True, no_files_written=True, no_large_wave_read=True,
        unresolved=['Mapped unknown-state influence needs separate connected-signal/validity analysis',
            'SAIF residence totals do not preserve X versus valid/CEN temporal correlation',
            'SRAM rail/condition/model excitation and raw tool warnings require scoped review',
            'No new sensitivity run or model/clock/parasitic coverage approval is implied',
            'Pre-layout estimation limits and official/physical signoff remain disclosed'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', required=True, type=Path)
    parser.add_argument('--scope-root', required=True, type=Path)
    parser.add_argument('--max-file-bytes', type=int, default=16 * 1024 * 1024)
    parser.add_argument('--max-total-bytes', type=int, default=128 * 1024 * 1024)
    args = parser.parse_args()
    try:
        value = inspect(args.report, args.scope_root, args.max_file_bytes, args.max_total_bytes)
    except (ValueError, KeyError, TypeError, OSError) as error:
        print(json.dumps(dict(schema='b0-read-only-power-review-inventory-v1',
            status='inventory_rejected', system_power_verified=False, error=str(error)), indent=2))
        return 2
    print(json.dumps(value, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    sys.exit(main())
