"""Bind an explicit engineering review to the already audited frozen reports.

This version accepts scoped synthesis timing and a conservative project area
bound only. It cannot approve system power, physical signoff or official scores.
"""
from decimal import Decimal
import json
from pathlib import Path
from dma16_power_numbers import require, sha


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def bound_file(ref):
    path = Path(ref['path']).resolve()
    require(sha(path) == ref['sha256'], 'Review artifact changed')
    return read(path)


def validate(record, refs, synthesis, timing, ports):
    require(record.get('schema') == 'dma16-frozen-review-v1' and
            record.get('scope') == 'SS_0p99V_125C_stable_task_mode_pre_layout', 'Unsupported review scope')
    for key in ('asic', 'synthesis', 'gate'):
        require(record[key+'_summary_sha256'] == refs[key]['sha256'], 'Review is for a different '+key)
    require(record['physical_signoff'] is False and record['official_scoring_confirmed'] is False and
            record['official_precision_verified'] is False, 'Unsupported official/physical approval')
    decisions = record['decisions']
    require(decisions['task_mode_synthesis_timing'] == 'accepted_for_declared_scope' and
            decisions['project_area_upper_bound'] == 'accepted_for_declared_scope' and
            decisions['system_power'].startswith('pending'), 'Review does not authorize only timing/area')
    require(timing['scope'] == 'dma16_frozen_mapped_ddc_readonly_timing_diagnostics' and
            timing['synthesis_summary_sha256'] == refs['synthesis']['sha256'] and
            timing['netlist_modified'] is False and timing['high_fanout']['count'] == 3 and
            set(timing['high_fanout']['nets']) == {'u_e203_subsys_top/core_csr_clk', 'u_e203_subsys_top/hfclk',
                'u_e203_subsys_top/u_sirv_aon_top/crossing_clock'}, 'Unreviewed timing diagnostic')
    require(ports['schema'] == 'dma16_mapped_port_diagnostic_v1' and
            ports['synthesis_summary_sha256'] == refs['synthesis']['sha256'] and
            ports['netlist_modified'] is False and ports['module_count'] == 1334 and
            ports['port_warning_count'] == 4852 and len(ports['ports']) == 4852 and
            ports['disposition_counts'] == {'declaration_only': 4852} and
            ports['warning_counts'] == {'LINT-1': 4, 'LINT-2': 178, 'LINT-8': 178,
                'LINT-28': 4674, 'LINT-32': 4549, 'LINT-33': 502} and
            all(p['disposition'] == 'declaration_only' and p['expression_occurrences'] == 0 for p in ports['ports']),
            'Structural diagnostic differs from reviewed objects')
    metrics = synthesis['metrics']; expected = record['metrics']
    for actual, declared in (('period_ns', 'period_ns'), ('max', 'setup_slack_ns'), ('min', 'hold_slack_ns')):
        require(Decimal(str(metrics[actual])) == Decimal(expected[declared]), 'Reviewed timing metric differs')
    require(Decimal(expected['period_ns']) == Decimal('6.666666') and
            min(Decimal(expected['setup_slack_ns']), Decimal(expected['hold_slack_ns'])) >= 0 and
            int(metrics['latches']) == 0 and synthesis['loop_check']['combinational_loops_detected'] is False,
            'Timing hard requirements failed')
    area = synthesis['area_summary']; basis = synthesis['area_basis']
    bound = Decimal(str(area['conservative_budget_mm2']))
    require(area['units'] == basis['units'] == 'um^2' and basis['standard_cells_checked'] == 1276 and
            area['leaf_count'] == 143118 and area['macro_count'] == 162 and
            sum(g['standard_cell_count'] for g in area['groups'].values()) == 139266 and
            sum(g['sram_count'] for g in area['groups'].values()) == 162 and
            sum(g['virtual_constant_count'] for g in area['groups'].values()) == 3690 and
            abs(bound-Decimal(expected['area_upper_mm2'])) < Decimal('1e-9') and
            Decimal(expected['project_area_limit_mm2']) == Decimal('2.00') and 0 < bound <= 2,
            'Reviewed conservative area bound differs')
    return dict(timing_verified=True, project_area_upper_bound_verified=True, scoring_area_verified=True,
                system_power_verified=False, official_scoring_confirmed=False, physical_signoff=False,
                scope=record['scope'], project_area_upper_mm2=expected['area_upper_mm2'])


def apply(report, request, synthesis, load_stage):
    record = bound_file(request['record'])
    doc = Path(request['document']).resolve()
    require(sha(doc) == record['review_document_sha256'] and doc.name == Path(record['review_document']).name,
            'Review explanation changed or missing')
    require(request['timing']['sha256'] == record['timing_diagnostic_summary_sha256'] and
            request['ports']['sha256'] == record['port_diagnostic_sha256'] and
            request['first_power']['sha256'] == record['first_power_summary_sha256'], 'Review diagnostic identity differs')
    timing = load_stage(request['timing'], 'dma16_timing_audit')
    # This PT run supplies the reviewed no_clock/disabled-arc reports. Reading
    # it does not approve its power numbers or stand in for the other layers.
    first_power = load_stage(request['first_power'], 'dma16_power')
    require(first_power['synthesis_summary_sha256'] == report['references']['synthesis']['sha256'] and
            first_power['gate_summary_sha256'] == report['references']['gate']['sha256'], 'Reviewed PT configuration differs')
    ports = bound_file(request['ports'])
    # Recheck the diagnostic's original frozen files, including mapped.v/report.
    for filename, digest in ports['inputs_sha256'].items():
        require(sha(Path(filename)) == digest, 'Structural diagnostic source changed')
    accepted = validate(record, report['references'], synthesis, timing, ports)
    report['verification'].update(accepted)
    report['engineering_review'] = dict(record=record, record_sha256=request['record']['sha256'],
        document_sha256=record['review_document_sha256'], timing=request['timing'], ports=request['ports'],
        first_power=request['first_power'],
        consumer_sha256=sha(__file__))
    resolved = {'Strict clock/constraints/disabled arcs and high-fanout review', 'Added-area attribution review'}
    report['unverified'] = [item for item in report['unverified'] if item not in resolved]
    return report
