"""Export hash-bound DMA16 evidence as JSON, CSV and Chinese Markdown.

No simulator/EDA process is started. Report collection is not acceptance:
timing, area and system-power review remain explicit, and official precision
is never inferred from internal data. Python 3.6 standard library only.
"""
import argparse
import csv
from decimal import Decimal
import json
from pathlib import Path
import re
import dma16_batch as batch
import dma16_power as power
from dma16_power_numbers import extract, require, sha

LAYERS = tuple('layer_%02d' % n for n in range(1, 13))
CASES = set(LAYERS+('extremes', 'rounding'))
MACS = 1622016


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def load_stage(ref, stage):
    run = Path(ref['run']).resolve(); digest = ref['sha256']
    require(re.fullmatch('[a-f0-9]{64}', digest) and sha(run/'summary.json') == digest, 'Stage summary changed: '+stage)
    report = read(run/'summary.json'); state = read(run.parent/'state.json')['stages'][stage]
    require(state['status'] == 'passed' and state['summary_sha256'] == digest, 'Stage is not complete: '+stage)
    for name, expected in report.get('artifacts', {}).items():
        require(Path(name).name == name and sha(run/name) == expected, 'Changed/unsafe stage artifact '+name)
    return report


def source_inventory(path):
    result = read(path)
    require(result and all(re.fullmatch('[a-f0-9]{64}', v) for v in result.values()), 'Invalid source inventory')
    for filename, digest in result.items():
        require(Path(filename).is_absolute() and sha(filename) == digest, 'Source changed: '+filename)
    return result


def rtl_inventory(values):
    result = {}
    for filename, digest in values.items():
        parts = filename.replace('\\', '/').split('/workspaces/')
        if len(parts) != 2 or '/rtl/' not in parts[1] or Path(filename).suffix not in ('.v', '.sv', '.vh', '.svh'):
            continue
        key = parts[1]
        require(key not in result or result[key] == digest, 'Conflicting RTL provenance')
        result[key] = digest
    require(len(result) >= 10, 'Incomplete production RTL identity')
    return result


def platform_inventory(values):
    result = {}
    for filename, digest in values.items():
        parts = filename.replace('\\', '/').split('/platform/rtl/')
        if len(parts) == 2:
            require(parts[1] not in result or result[parts[1]] == digest, 'Conflicting platform RTL provenance')
            result[parts[1]] = digest
    require(result, 'Missing fixed-platform RTL inventory')
    return result


def indexed_cases(report, gate=False):
    rows = report.get('cases', [])
    require(len(rows) == 14 and {r['case'] for r in rows} == CASES, 'Require complete 14-case matrix suite')
    for row in rows:
        require(row.get('outputs') == 25344 and row['result']['cycles'] == row['task_window']['cycles'], 'Case output/cycle mismatch')
        power.window_values(row['task_window'])
        if gate and row['case'] in LAYERS: power.validate_activity(row['activity'], row['task_window'])
    return {r['case']: r for r in rows}


def boundary_fields(raw):
    boundary = raw.get('boundary_inclusive') if raw else None
    return dict(boundary_inclusive=boundary,
                raw_boundary_inclusive_average_power_w=boundary['reported_power_w']['total'] if boundary else None,
                raw_boundary_inclusive_energy_j=boundary['raw_reported_energy_j'] if boundary else None)


def boundary_aggregate(rows, duration):
    selected = [r['raw_boundary_inclusive_energy_j'] for r in rows if r['raw_boundary_inclusive_energy_j'] is not None]
    energy = sum(Decimal(v) for v in selected) if len(selected) == 12 else None
    return dict(boundary_power_layers=len(selected),
                raw_boundary_inclusive_total_energy_j=str(energy) if energy is not None else None,
                raw_boundary_inclusive_energy_per_task_j=str(energy/12) if energy is not None else None,
                raw_boundary_inclusive_time_weighted_average_power_w=str(energy/(duration*Decimal('1e-9'))) if energy is not None else None)


def join_cases(asic, gate, synthesis, refs, numbers):
    require(asic.get('scope') == 'asic_rtl_functional' and asic.get('cpu_executed') is True and
            asic.get('asic_cpu_verified') is True and asic.get('global_FPGA_defined') is False, 'Wrong ASIC scope')
    require(gate.get('scope') == power.GATE_SCOPE and gate.get('gate_simulation_verified') is True and
            gate.get('cpu_executed') is True, 'Wrong mapped gate scope')
    require(synthesis.get('scope') == 'dma16_whole_soc_task_mode_preliminary_synthesis' and
            synthesis.get('synthesis_completed') is True, 'Wrong synthesis scope')
    require(Decimal(str(synthesis['metrics']['period_ns'])) == Decimal('6.666666') and
            int(synthesis['metrics']['RAMSP128X16']) == 32 and int(synthesis['metrics']['RAMSP4096X16']) == 130,
            'Synthesis clock/SRAM configuration differs')
    require(gate['synthesis_summary_sha256'] == refs['synthesis']['sha256'] and
            gate['firmware_sha256'] == asic['compile_receipt']['firmware_sha256'], 'Mixed frozen synthesis/firmware')
    a, g = indexed_cases(asic), indexed_cases(gate, True)
    selected = {}
    for item in numbers:
        name = item['case']; require(name in LAYERS and name not in selected, 'Duplicate/unknown power layer')
        require(item['synthesis_summary_sha256'] == refs['synthesis']['sha256'] and
                item['gate_summary_sha256'] == refs['gate']['sha256'] and
                item['firmware_sha256'] == gate['firmware_sha256'] and
                item['layout_sha256'] == g[name]['layout_sha256'] and
                item['activity']['sha256'] == g[name]['activity']['sha256'], 'Mixed frozen power provenance')
        require(Decimal(item['duration_ns']) == Decimal(power.validate_activity(g[name]['activity'], g[name]['task_window'])),
                'Power duration differs from actual gate window')
        selected[name] = item
    rows = []
    for name in LAYERS:
        x, y = a[name], g[name]
        require(x['layout_sha256'] == y['layout_sha256'] and x['result'] == y['result'], 'ASIC and gate result/layout differ')
        cycles = y['task_window']['cycles']; duration = power.window_values(y['task_window'])[2]
        raw = selected.get(name); watts = raw['reported_power_w'] if raw else None
        rows.append(dict(case=name, cycles=cycles, duration_ns=duration, outputs=25344,
            nominal_150mhz_tasks_per_second=str(Decimal(150000000)/cycles),
            nominal_150mhz_mmac_per_second=str(Decimal(150*MACS)/cycles),
            tool_period_tasks_per_second=str(Decimal('1e9')/Decimal(duration)),
            raw_dynamic_w=raw['derived_dynamic_w'] if raw else None,
            raw_leakage_w=watts['leakage'] if raw else None, raw_average_power_w=watts['total'] if raw else None,
            raw_energy_j=raw['raw_reported_energy_j'] if raw else None,
            approved_average_power_w=None, approved_energy_j=None,
            layout_sha256=y['layout_sha256'], activity_sha256=y['activity']['sha256'],
            active_value_records=y['activity']['active_value_records'], unknown_value_records=y['activity']['unknown_value_records'],
            module_breakdown=raw['module_breakdown'] if raw else None,
            sram_breakdown=raw['sram_breakdown'] if raw else None,
            warning_occurrences_by_artifact=raw['warning_occurrences_by_artifact'] if raw else None,
            power_summary_sha256=raw['power_summary_sha256'] if raw else None,
            system_power_verified=False))
        rows[-1].update(boundary_fields(raw))
    total_cycles = sum(r['cycles'] for r in rows)
    duration = sum(Decimal(r['duration_ns']) for r in rows)
    total_energy = sum(Decimal(r['raw_energy_j']) for r in rows) if len(selected) == 12 else None
    aggregate = dict(tasks=12, total_cycles=total_cycles, mean_cycles=str(Decimal(total_cycles)/12),
        nominal_150mhz_tasks_per_second=str(Decimal(12*150000000)/total_cycles),
        nominal_150mhz_mmac_per_second=str(Decimal(12*150*MACS)/total_cycles),
        tool_period_duration_ns=str(duration), power_layers=len(selected),
        raw_total_energy_j=str(total_energy) if total_energy is not None else None,
        raw_energy_per_task_j=str(total_energy/12) if total_energy is not None else None,
        raw_time_weighted_average_power_w=str(total_energy/(duration*Decimal('1e-9'))) if total_energy is not None else None,
        approved_average_power_w=None, approved_energy_per_task_j=None,
        goal_500_tasks_per_second_met_by_cycles=total_cycles <= 12*300000,
        note='Nominal 150 MHz throughput is conservative; energy uses each actual 6.666666 ns window. Missing powers are null, not zero.')
    aggregate.update(boundary_aggregate(rows, duration))
    return rows, aggregate


def audit_batch(ref, contract):
    if ref is None: return dict(status='not_run', tasks=0, outputs=0, official_precision_verified=False)
    root = Path(ref['run']).resolve(); state_path = root/'state.json'
    require(sha(state_path) == ref['sha256'], 'Batch state changed')
    state = read(state_path); identity = state['identity']
    require(state['status'] == 'passed' and state.get('asic_executed') is True and
            state.get('outputs') == 30412800 and len(state['completed']) == 1200, 'Final ASIC batch incomplete')
    require(identity['frozen'] == batch.validate_contract(contract) and
            identity['dataset'] == dict(manifest_sha256=batch.DATASET_SHA256, samples=100, cases=1200), 'Mixed batch build/dataset')
    tasks = identity['tasks']
    require(len(tasks) == 1200 and {(t['sample'], t['layer']) for t in tasks} ==
            {(s, l) for s in range(1, 101) for l in range(1, 13)}, 'Batch is not all 100 samples/12 layers')
    rows = []
    for task, entry in zip(tasks, state['completed']):
        attempt = (root/entry['attempt']).resolve(); attempt.relative_to(root)
        require(entry['task_key'] == task['key'] and sha(attempt/'receipt.json') == entry['receipt_sha256'], 'Batch receipt changed/order differs')
        record = batch.verified_receipt(attempt, task['source'], identity, task)
        require(record['asic_executed'] is True and record['evidence_mode'] == 'hardware', 'Non-ASIC batch receipt')
        rows.append(dict(task=task['key'], sample=task['sample'], layer=task['layer'], result=record['result'],
                         receipt_sha256=entry['receipt_sha256'], host_total_seconds=entry['host_total_seconds']))
    require(sha(state_path) == ref['sha256'], 'Batch changed during report audit')
    return dict(status='passed_reaudited', tasks=1200, outputs=30412800, state_sha256=ref['sha256'],
                cases=rows, failed_attempts=state['failed_attempts'], host_budget=state['host_budget'],
                official_precision_verified=False)


def build(request):
    require(request.get('schema') == 'dma16-report-request-v1', 'Wrong report request schema')
    refs = {k: request[k] for k in ('asic', 'synthesis', 'gate')}
    a = load_stage(refs['asic'], 'dma16_soc'); s = load_stage(refs['synthesis'], 'dma16_synth')
    g = load_stage(refs['gate'], 'dma16_gate')
    arun, srun, grun = (Path(refs[k]['run']).resolve() for k in ('asic', 'synthesis', 'gate'))
    require(sha(arun/'source_inputs.json') == a['compile_receipt']['source_inputs_sha256'] and
            read(arun/'compile_receipt.json') == a['compile_receipt'], 'ASIC source/compile receipt differs')
    ai, si = source_inventory(arun/'source_inputs.json'), source_inventory(srun/'source_inputs.json')
    rtl = rtl_inventory(ai); require(rtl == rtl_inventory(si), 'ASIC and synthesized production RTL differ')
    platform = platform_inventory(ai)
    require(platform == platform_inventory(si) and a['compile_receipt']['platform_baseline_sha256'] ==
            s['link_report']['platform_baseline_sha256'], 'ASIC and synthesized platform differ')
    require(sha(grun/'source_inputs.json') == g['source_inputs_sha256'], 'Gate source receipt changed')
    source_inventory(grun/'source_inputs.json')
    contract = read(arun/'batch_contract.json')
    require(sha(arun/'batch_contract.json') == a['batch_contract_sha256'], 'Frozen ASIC batch contract changed')
    batch.validate_contract(contract)
    numbers = [extract(Path(r['run']), r['sha256']) for r in request.get('power', [])]
    rows, aggregate = join_cases(a, g, s, refs, numbers)
    final_batch = audit_batch(request.get('batch'), contract)
    history = request.get('history', [])
    require(all(h.get('status') in ('failed', 'stopped', 'unverified') and h.get('description') and h.get('run') for h in history),
            'History must state status, description and preserved run')
    pending = ['Strict clock/constraints/disabled arcs and high-fanout review', 'Added-area attribution review',
               'System power models/units/X/annotation and warning review', 'Protocol/recovery/contention evidence audit',
               'Clean-directory final reproduction and official submission materials']
    if len(numbers) != 12: pending.append('Missing complete power reports for one or more performance layers')
    if final_batch['tasks'] != 1200: pending.append('Final 1200 ASIC/E203 tasks have not passed and been re-audited')
    return dict(schema='dma16-evidence-export-v1', status='evidence_exported_review_required', references=refs,
        declared_conditions=dict(corner='SS', voltage_v='0.99', temperature_c=125, clock_period_ns='6.666666',
            analysis='Pre-layout; zero-delay gate activity; no extracted parasitics or physical clock tree'),
        production_rtl_sha256=rtl, firmware_sha256=g['firmware_sha256'],
        installed_platform_rtl_sha256=platform, platform_baseline_sha256=a['compile_receipt']['platform_baseline_sha256'],
        library_inputs_sha256=s['link_report']['library_inputs'], area=s['area_summary'], area_basis=s['area_basis'],
        timing_metrics=s['metrics'], synthesis_required_reviews=s['required_reviews'],
        cases=rows, aggregate=aggregate, batch=final_batch, history=history, unverified=pending,
        power_references=request.get('power', []), power_required_reviews={n['case']: n['required_reviews'] for n in numbers},
        verification=dict(asic_14=True, gate_14_without_sdf=True, activity_12=True,
            timing_verified=False, scoring_area_verified=False, system_power_verified=False,
            official_precision_verified=False, physical_signoff=False), exporter_sha256=sha(__file__))


def write_outputs(report, output):
    output = Path(output); require(not output.exists(), 'Use a new report directory')
    output.mkdir(parents=True)
    with (output/'report.json').open('x', encoding='utf8') as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2, allow_nan=False)
    fields = ['case', 'cycles', 'duration_ns', 'outputs', 'nominal_150mhz_tasks_per_second',
              'nominal_150mhz_mmac_per_second', 'raw_dynamic_w', 'raw_leakage_w', 'raw_average_power_w',
              'raw_energy_j', 'raw_boundary_inclusive_average_power_w', 'raw_boundary_inclusive_energy_j',
              'approved_average_power_w', 'approved_energy_j', 'layout_sha256',
              'activity_sha256', 'active_value_records', 'unknown_value_records', 'power_summary_sha256', 'system_power_verified']
    with (output/'tasks.csv').open('x', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fields, extrasaction='ignore'); writer.writeheader(); writer.writerows(report['cases'])
    aggregate = report['aggregate']
    summary_row = dict(aggregate)
    for name in ('max', 'min', 'latches', 'period_ns'):
        summary_row['timing_'+name] = report.get('timing_metrics', {}).get(name)
    for name in ('known_added_mm2', 'conservative_budget_mm2', 'whole_system_library_area', 'project_budget_mm2'):
        summary_row['area_'+name] = report.get('area', {}).get(name)
    with (output/'summary.csv').open('x', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, list(summary_row)); writer.writeheader(); writer.writerow(summary_row)
    module_fields = ['case', 'module', 'internal_w', 'switching_w', 'leakage_w', 'total_w',
                     'dynamic_w', 'total_print_rounding_bound_w', 'system_power_verified']
    with (output/'modules.csv').open('x', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, module_fields); writer.writeheader()
        for row in report['cases']:
            if row['module_breakdown'] is None: continue
            for name, values in sorted(row['module_breakdown']['modules'].items()):
                entry = {k+'_w': v for k, v in values['derived_power_w'].items()}
                entry.update(case=row['case'], module=name, dynamic_w=values['derived_dynamic_w'],
                             total_print_rounding_bound_w=values['rounding_bound_w']['total'], system_power_verified=False)
                writer.writerow(entry)
    lines = ['# '+report.get('architecture_label', '架构三 DMA16')+' 冻结配置证据汇总', '',
        '本报告由原始运行摘要及文件哈希生成。真实 ASIC 14 例、无 SDF 门级 14 例和 12 个完整活动窗口通过；时序、面积归属及系统功耗仍需独立审核，不能视为最终参评验收。', '',
        '统一计时为首个源请求 valid 至最后结果写响应，包含首请求等待及共享 SRAM 入库；每任务 191,616 B、1,622,016 MAC。声明工艺条件为 SS、0.99 V、125°C，工具周期 6.666666 ns；布局前估算不含提取寄生或物理时钟树。', '',
        '12 任务平均周期：'+aggregate['mean_cycles']+'；名义 150 MHz 吞吐：'+aggregate['nominal_150mhz_tasks_per_second']+' task/s。', '',
        '| 层 | 周期 | task/s（150 MHz） | 原始平均功耗 W | 原始能耗 J/task |',
        '|---|---:|---:|---:|---:|']
    for row in report['cases']:
        lines.append('| %s | %s | %s | %s | %s |' % (row['case'], row['cycles'], row['nominal_150mhz_tasks_per_second'],
            row['raw_average_power_w'] if row['raw_average_power_w'] is not None else '未验证',
            row['raw_energy_j'] if row['raw_energy_j'] is not None else '未验证'))
    lines += ['', '原始功耗与能耗不代表模型及活动审核通过；缺项保持为空。上表采用默认不含输入边界网络的口径；包含该网络开关功耗的数值单列在 JSON/CSV 的 boundary_inclusive 字段，不替换默认值。模块分解采用不重叠范围，CPU 扣除其 TCM 子模块，SRAM 明细不能再次加到模块总值。各模块值及显示舍入误差保留在 JSON。', '',
        '100 样本内部回归：%s，%d 个任务、%d 个输出；不是官方 600 样本精度验收。' %
        (report['batch']['status'], report['batch']['tasks'], report['batch']['outputs']), '', '## 原始证据', '']
    for label, ref in report['references'].items(): lines += ['- %s：`%s`，SHA256 `%s`。' % (label, ref['run'], ref['sha256'])]
    lines += ['', '面积、setup/hold、库/源码/固件/布局/波形哈希和活动未知值见 report.json；逐层数据见 tasks.csv，模块功耗见 modules.csv，总计见 summary.csv。', '', '## 未验证与保留历史', '']
    lines += ['- '+x for x in report['unverified']]
    lines += ['- %s：%s；`%s`。' % (h['status'], h['description'], h['run']) for h in report['history']]
    with (output/'report_zh.md').open('x', encoding='utf8') as stream: stream.write('\n'.join(lines)+'\n')
    receipt = dict(schema=report.get('receipt_schema', 'dma16-evidence-export-receipt-v1'), artifacts={p.name: sha(p) for p in output.iterdir() if p.is_file()})
    with (output/'receipt.json').open('x', encoding='utf8') as stream: json.dump(receipt, stream, indent=2)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args(); require(not args.output.exists(), 'Use a new report directory')
    request_sha = sha(args.request); report = build(read(args.request))
    require(sha(args.request) == request_sha, 'Report request changed')
    report['request_sha256'] = request_sha; write_outputs(report, args.output)
    print('DMA16_EVIDENCE_EXPORTED review_required=true', args.output)


if __name__ == '__main__': main()
