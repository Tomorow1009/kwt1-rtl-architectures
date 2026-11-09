"""Export the original MMIO8 same-source reference with its own frozen proof.

No DMA16/old-BEGIN netlist, activity or firmware may substitute for this build.
Raw power is never auto-approved. Python 3.6 standard library only.
"""
import argparse
from decimal import Decimal
from pathlib import Path
import re
import dma16_report as common
import mmio8_power as power
from mmio8_power_numbers import extract
from dma16_power_numbers import require, sha

LAYERS = common.LAYERS
REFERENCE = 'original_repaired_MMIO8_same_SysMem_source'


def indexed_cases(report, gate=False):
    rows = report.get('cases', [])
    require(len(rows) == 14 and {r['case'] for r in rows} == common.CASES,
            'MMIO8 requires all 14 cases')
    for row in rows:
        require(row.get('outputs') == 25344 and row['capture']['outputs'] == 25344 and
                re.fullmatch('[a-f0-9]{64}', row.get('layout_sha256', '')) and
                re.fullmatch('[a-f0-9]{64}', row['capture']['capture_sha256']), 'Incomplete MMIO8 capture/layout')
        power.window_values(row['task_window'])
        if gate and row['case'] in LAYERS:
            power.validate_activity(row['activity'], row['task_window'])
    return {r['case']: r for r in rows}


def join_cases(asic, gate, synthesis, refs, numbers):
    require(all(r.get('DMA_present') is False for r in (asic, gate, synthesis)),
            'MMIO8 reference must not contain DMA')
    require(asic.get('scope') == 'asic_rtl_functional' and asic.get('cpu_executed') is True and
            asic.get('asic_cpu_verified') is True and asic.get('global_FPGA_defined') is False and
            asic.get('reference') == gate.get('reference') == REFERENCE, 'Wrong MMIO8 ASIC reference')
    require(gate.get('scope') == power.gate_tools.SCOPE and gate.get('gate_simulation_verified') is True and
            gate.get('cpu_executed') is True and gate.get('global_FPGA_defined') is False and
            gate.get('input_task_bytes_in_boot') == 0, 'Wrong MMIO8 gate scope')
    require(synthesis.get('scope') == power.synth.SCOPE and synthesis.get('synthesis_completed') is True and
            Decimal(str(synthesis['metrics']['period_ns'])) == Decimal('6.666666') and
            int(synthesis['metrics']['RAMSP128X16']) == 8 and int(synthesis['metrics']['RAMSP4096X16']) == 130,
            'Wrong MMIO8 synthesis/clock/macro inventory')
    require(gate['synthesis_summary_sha256'] == refs['synthesis']['sha256'] and
            gate['firmware_sha256'] == asic['compile_receipt']['firmware_sha256'], 'Mixed MMIO8 build identity')
    a, g = indexed_cases(asic), indexed_cases(gate, True)
    selected = {}
    for item in numbers:
        name = item['case']
        require(name in LAYERS and name not in selected and item.get('DMA_present') is False,
                'Wrong/duplicate MMIO8 power case')
        require(item['synthesis_summary_sha256'] == refs['synthesis']['sha256'] and
                item['gate_summary_sha256'] == refs['gate']['sha256'] and
                item['firmware_sha256'] == gate['firmware_sha256'] and
                item['layout_sha256'] == g[name]['layout_sha256'] and
                item['activity']['sha256'] == g[name]['activity']['sha256'], 'Mixed MMIO8 power identity')
        require(Decimal(item['duration_ns']) == Decimal(power.validate_activity(g[name]['activity'], g[name]['task_window'])),
                'MMIO8 exact power event duration differs')
        selected[name] = item
    rows = []
    for name in sorted(common.CASES):
        x, y = a[name], g[name]
        require(x['capture'] == y['capture'] and x['layout_sha256'] == y['layout_sha256'],
                'MMIO8 ASIC/gate output or saturation differs')
        require(x['task_window']['cycles'] == y['task_window']['cycles'] and
                power.window_values(x['task_window'])[2] == power.window_values(y['task_window'])[2],
                'MMIO8 ASIC/gate exact duration differs')
        if name not in LAYERS: continue
        cycles = y['task_window']['cycles']; duration = power.window_values(y['task_window'])[2]
        activity = y['activity']; raw = selected.get(name); watts = raw['reported_power_w'] if raw else None
        rows.append(dict(case=name, cycles=cycles, duration_ns=duration, outputs=25344,
            nominal_150mhz_tasks_per_second=str(Decimal(150000000)/cycles),
            nominal_150mhz_mmac_per_second=str(Decimal(150*common.MACS)/cycles),
            tool_period_tasks_per_second=str(Decimal('1e9')/Decimal(duration)),
            raw_dynamic_w=raw['derived_dynamic_w'] if raw else None,
            raw_leakage_w=watts['leakage'] if raw else None, raw_average_power_w=watts['total'] if raw else None,
            raw_energy_j=raw['raw_reported_energy_j'] if raw else None,
            approved_average_power_w=None, approved_energy_j=None,
            layout_sha256=y['layout_sha256'], activity_sha256=activity['sha256'],
            active_value_records=activity['active_value_records'], unknown_value_records=activity['unknown_value_records'],
            module_breakdown=raw['module_breakdown'] if raw else None,
            sram_breakdown=raw['sram_breakdown'] if raw else None,
            warning_occurrences_by_artifact=raw['warning_occurrences_by_artifact'] if raw else None,
            power_summary_sha256=raw['power_summary_sha256'] if raw else None, system_power_verified=False))
    for row in rows:
        row.update(common.boundary_fields(selected.get(row['case'])))
    total_cycles = sum(r['cycles'] for r in rows)
    duration = sum(Decimal(r['duration_ns']) for r in rows)
    energy = sum(Decimal(r['raw_energy_j']) for r in rows) if len(selected) == 12 else None
    aggregate = dict(tasks=12, total_cycles=total_cycles, mean_cycles=str(Decimal(total_cycles)/12),
        nominal_150mhz_tasks_per_second=str(Decimal(12*150000000)/total_cycles),
        nominal_150mhz_mmac_per_second=str(Decimal(12*150*common.MACS)/total_cycles),
        tool_period_duration_ns=str(duration), power_layers=len(selected),
        raw_total_energy_j=str(energy) if energy is not None else None,
        raw_energy_per_task_j=str(energy/12) if energy is not None else None,
        raw_time_weighted_average_power_w=str(energy/(duration*Decimal('1e-9'))) if energy is not None else None,
        approved_average_power_w=None, approved_energy_per_task_j=None,
        goal_500_tasks_per_second_met_by_cycles=total_cycles <= 12*300000,
        note='Original MMIO8, no DMA; throughput uses conservative integer cycles, energy uses exact first-VALID phase. Missing power is null.')
    aggregate.update(common.boundary_aggregate(rows, duration))
    return rows, aggregate


def build(request):
    require(request.get('schema') == 'mmio8-source-report-request-v1' and 'batch' not in request,
            'MMIO8 reference export has its own scope; final DMA16 batch belongs to DMA16 report')
    refs = {k: request[k] for k in ('asic', 'synthesis', 'gate')}
    a = common.load_stage(refs['asic'], 'mmio8_soc'); s = common.load_stage(refs['synthesis'], 'mmio8_synth')
    g = common.load_stage(refs['gate'], 'mmio8_gate')
    arun, srun, grun = (Path(refs[k]['run']).resolve() for k in ('asic', 'synthesis', 'gate'))
    require(sha(arun/'source_inputs.json') == a['compile_receipt']['source_inputs_sha256'] and
            common.read(arun/'compile_receipt.json') == a['compile_receipt'] and
            sha(arun/'frozen_inputs.json') == a['frozen_inputs_sha256'], 'MMIO8 compile/frozen receipt changed')
    common.source_inventory(arun/'frozen_inputs.json')
    ai, si = common.source_inventory(arun/'source_inputs.json'), common.source_inventory(srun/'source_inputs.json')
    rtl = common.rtl_inventory(ai); platform = common.platform_inventory(ai)
    require(rtl == common.rtl_inventory(si) and platform == common.platform_inventory(si) and
            a['compile_receipt']['platform_baseline_sha256'] == s['link_report']['platform_baseline_sha256'],
            'MMIO8 ASIC and synthesis production RTL/platform differ')
    require(sha(grun/'source_inputs.json') == g['source_inputs_sha256'], 'MMIO8 gate source receipt changed')
    common.source_inventory(grun/'source_inputs.json')
    for row in a['cases']:
        require(set(row['artifacts']) == {'_command.json', '.log', '.csv'}, 'Incomplete MMIO8 ASIC artifacts')
        require(row['artifacts']['.csv'] == row['capture']['capture_sha256'], 'MMIO8 capture digest differs from artifact')
        for suffix, digest in row['artifacts'].items():
            require(suffix in ('_command.json', '.log', '.csv') and sha(arun/(row['case']+suffix)) == digest,
                    'MMIO8 ASIC case artifact changed')
    numbers = [extract(Path(r['run']), r['sha256']) for r in request.get('power', [])]
    rows, aggregate = join_cases(a, g, s, refs, numbers)
    history = request.get('history', [])
    require(all(h.get('status') in ('failed', 'stopped', 'unverified') and h.get('description') and h.get('run') for h in history),
            'History must retain status, description and run')
    pending = ['Original MMIO8 reference, no DMA; same source model, different declared tile layout',
               'Timing constraints/disabled arcs, area attribution, power models/X/annotation/warnings require independent review',
               'Final 1200 acceptance belongs to the selected candidate, not inferred from this reference suite',
               'Clean-directory reproduction and final comparison remain required']
    if len(numbers) != 12: pending.append('One or more full-window power layers are missing')
    return dict(schema='mmio8-source-evidence-export-v1', status='evidence_exported_review_required', DMA_present=False,
        architecture_label='架构三原8路MMIO同源对照', receipt_schema='mmio8-source-evidence-export-receipt-v1', references=refs,
        declared_conditions=dict(corner='SS', voltage_v='0.99', temperature_c=125, clock_period_ns='6.666666',
            analysis='Pre-layout; zero-delay gate activity; no extracted parasitics or physical clock tree'),
        production_rtl_sha256=rtl, firmware_sha256=g['firmware_sha256'], installed_platform_rtl_sha256=platform,
        platform_baseline_sha256=a['compile_receipt']['platform_baseline_sha256'],
        library_inputs_sha256=s['link_report']['library_inputs'], area=s['area_summary'], area_basis=s['area_basis'],
        timing_metrics=s['metrics'], synthesis_required_reviews=s['required_reviews'], cases=rows, aggregate=aggregate,
        batch=dict(status='reference_suite_only', tasks=0, outputs=0, official_precision_verified=False),
        history=history, unverified=pending, power_references=request.get('power', []),
        power_required_reviews={n['case']: n['required_reviews'] for n in numbers},
        verification=dict(asic_14=True, gate_14_without_sdf=True, activity_12=True, timing_verified=False,
            scoring_area_verified=False, system_power_verified=False, official_precision_verified=False, physical_signoff=False),
        exporter_sha256=sha(__file__), shared_exporter_sha256=sha(common.__file__))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request', required=True, type=Path); parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args(); require(not args.output.exists(), 'Use a new report directory')
    digest = sha(args.request); report = build(common.read(args.request))
    require(sha(args.request) == digest, 'MMIO8 report request changed')
    report['request_sha256'] = digest; common.write_outputs(report, args.output)
    print('MMIO8_SOURCE_EVIDENCE_EXPORTED review_required=true', args.output)


if __name__ == '__main__': main()
