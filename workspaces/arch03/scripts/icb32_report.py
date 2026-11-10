"""Export actual ICB32 ASIC/gate/PPA evidence without granting acceptance.

Read-only collection, Python 3.6. All stages must describe the same hardware;
the optional new 1200-case batch is checked against its own receipts/captures.
"""
import argparse
import csv
import json
import re
from decimal import Decimal
from pathlib import Path

import icb32_data as data
import icb32_soc as soc
import icb32_power as power
from icb32_power_numbers import extract, require, sha
from dma16_report import (read, load_stage, source_inventory, rtl_inventory,
                          platform_inventory, boundary_fields, boundary_aggregate)
from dma16_batch import index_legacy_dataset, DATASET_SHA256

LAYERS = tuple('layer_%02d' % n for n in range(1, 13))


def configuration_identity(run):
    values = source_inventory(Path(run)/'source_inputs.json')
    return dict(rtl=rtl_inventory(values), platform=platform_inventory(values))


def check_case(row, run, source, name):
    run = Path(run); task = run/(name+'_data')
    data.verify_prepared(source, task)
    captured = data.check_capture(run/(name+'.csv'), task)
    require(captured == row['capture'] and row['outputs'] == 25344, 'Capture receipt differs')
    for path, key in ((task/'codec.json', 'codec_sha256'),
                      (task/'layout_manifest.json', 'layout_sha256'),
                      (run/(name+'.log'), 'log_sha256'),
                      (run/(name+'_boot')/'manifest.json', 'boot_manifest_sha256')):
        require(sha(path) == row[key], 'Changed per-case artifact '+str(path))
    boot = read(run/(name+'_boot')/'manifest.json')
    require(boot['input_bytes_preloaded'] == 0, 'Preloaded task data in boot')
    for filename, digest in boot['files'].items():
        require(Path(filename).name == filename and sha(run/(name+'_boot')/filename) == digest,
                'Changed physical boot input')
    size = read(task/'codec.json')['encoded_bytes']
    markers = soc.MARKERS+['ARCH03_ICB32_SOURCE_READY words=%d scope=PC_file_only no_ITCM_task_data=true' % (size//4)]
    text = (run/(name+'.log')).read_text()
    result = data.parse_result(text, captured['saturated'], markers)
    require(result == row['result'] and data.read_window(text, result, size) == row['task_window'],
            'Log/window completion proof differs')
    irq = row['irq_proof']
    matches = re.findall(r'^ARCH03_ICB32_IRQ_PROOF enabled=(\d+) external=(\d+) timer=(\d+) wfi=(\d+) events=(\d+) unhandled=(\d+)$', text, re.M)
    cpu = re.findall(r'^ARCH03_ICB32_CPU_CYCLES (\d+)$', text, re.M)
    require(len(matches) == len(cpu) == 1 and int(cpu[0]) == row['cpu_cycles'] and
            tuple(map(int, matches[0])) == tuple(int(irq[k]) for k in
            ('enabled', 'external', 'timer', 'wfi', 'events', 'unhandled')), 'IRQ/CPU log receipt differs')
    require(irq['enabled'] is True and irq['external'] > 0 and irq['timer'] > 0 and
            irq['wfi'] > 0 and irq['events'] & 1 and irq['unhandled'] == 0, 'Missing IRQ/WFI proof')
    power.window_values(row['task_window'])


def indexed_cases(report, run, gate=False):
    rows = report['cases']
    require(len(rows) == 14 and {r['case'] for r in rows} == set(data.CASES14), 'Incomplete 14 cases')
    for row in rows:
        check_case(row, run, Path(run).parents[2]/'validated_data'/row['case'], row['case'])
        if gate and row['case'] in LAYERS:
            power.validate_activity(row['activity'], row['task_window'])
            require(sha(Path(run)/(row['case']+'.vcd')) == row['activity']['sha256'], 'Changed VCD')
    return {r['case']: r for r in rows}


def join_cases(a, g, s, refs, numbers):
    require(a['scope'] == 'asic_rtl_functional' and a['asic_cpu_verified'] is True and
            a['cpu_executed'] is True and a['global_FPGA_defined'] is False, 'Wrong ASIC scope')
    require(g['scope'] == power.GATE_SCOPE and g['gate_simulation_verified'] is True and
            g['cpu_executed'] is True and g['sdf_annotated'] is False, 'Wrong gate scope')
    require(s['scope'] == 'icb32_whole_soc_task_mode_preliminary_synthesis' and
            s['synthesis_completed'] is True, 'Wrong synthesis scope')
    require(Decimal(str(s['metrics']['period_ns'])) == Decimal('6.666666') and
            int(s['metrics']['RAMSP128X16']) == 96 and int(s['metrics']['RAMSP4096X16']) == 128,
            'Wrong new clock/macro configuration')
    require(g['synthesis_summary_sha256'] == refs['synthesis']['sha256'] and
            g['firmware_sha256'] == a['compile_receipt']['firmware_manifest_sha256'], 'Mixed frozen build')
    left, right = indexed_cases(a, refs['asic']['run']), indexed_cases(g, refs['gate']['run'], True)
    selected = {}
    for item in numbers:
        name = item['case']; require(name in LAYERS and name not in selected, 'Duplicate/unknown power layer')
        require(item['synthesis_summary_sha256'] == refs['synthesis']['sha256'] and
                item['gate_summary_sha256'] == refs['gate']['sha256'] and
                item['firmware_sha256'] == g['firmware_sha256'] and
                item['layout_sha256'] == right[name]['layout_sha256'] and
                item['activity']['sha256'] == right[name]['activity']['sha256'], 'Mixed power identity')
        require(Decimal(item['duration_ns']) == Decimal(power.validate_activity(right[name]['activity'],
                right[name]['task_window'])), 'Power window differs')
        selected[name] = item
    rows = []
    for name in LAYERS:
        x, y = left[name], right[name]
        require(x['layout_sha256'] == y['layout_sha256'] and x['codec_sha256'] == y['codec_sha256'] and
                x['capture'] == y['capture'] and x['result']['cycles'] == y['result']['cycles'],
                'RTL/gate layout, output or complete cycle count differs')
        window = y['task_window']; raw = selected.get(name)
        require(x['task_window']['encoded_bytes'] == window['encoded_bytes'], 'Encoded size differs')
        cycles = window['cycles']; duration = power.window_values(window)[2]
        row = dict(case=name, cycles=cycles, duration_ns=duration, outputs=25344,
            encoded_bytes=window['encoded_bytes'], transfer_bytes=window['transfer_bytes'],
            transfer_transactions=window['transfer_transactions'],
            nominal_150mhz_tasks_per_second=str(Decimal(150000000)/cycles),
            nominal_150mhz_mmac_per_second=str(Decimal(243302400)/cycles),
            raw_dynamic_w=raw['derived_dynamic_w'] if raw else None,
            raw_leakage_w=raw['reported_power_w']['leakage'] if raw else None,
            raw_average_power_w=raw['reported_power_w']['total'] if raw else None,
            raw_energy_j=raw['raw_reported_energy_j'] if raw else None,
            module_breakdown=raw['module_breakdown'] if raw else None,
            sram_breakdown=raw['sram_breakdown'] if raw else None,
            layout_sha256=y['layout_sha256'], codec_sha256=y['codec_sha256'],
            activity_sha256=y['activity']['sha256'],
            active_value_records=y['activity']['active_value_records'],
            unknown_value_records=y['activity']['unknown_value_records'],
            power_summary_sha256=raw['power_summary_sha256'] if raw else None,
            system_power_verified=False, asic_window=x['task_window'], gate_window=window)
        row.update(boundary_fields(raw)); rows.append(row)
    total = sum(r['cycles'] for r in rows); duration = sum(Decimal(r['duration_ns']) for r in rows)
    energy = sum(Decimal(r['raw_energy_j']) for r in rows) if len(selected) == 12 else None
    aggregate = dict(tasks=12, total_cycles=total, mean_cycles=str(Decimal(total)/12),
        nominal_150mhz_tasks_per_second=str(Decimal(1800000000)/total),
        nominal_150mhz_mmac_per_second=str(Decimal(12*243302400)/total),
        power_layers=len(selected), raw_total_energy_j=str(energy) if energy is not None else None,
        raw_energy_per_task_j=str(energy/12) if energy is not None else None,
        raw_time_weighted_average_power_w=str(energy/(duration*Decimal('1e-9'))) if energy is not None else None,
        goal_5000_tasks_per_second_met_by_cycles=total <= 360000)
    aggregate.update(boundary_aggregate(rows, duration))
    return rows, aggregate


def audit_batch(ref, hardware, firmware_sha):
    if ref is None: return dict(status='not_run', tasks=0, outputs=0, official_precision_verified=False)
    report = load_stage(ref, 'icb32_batch'); root = Path(ref['run']).resolve()
    require(report['schema'] == 'arch03-icb32-batch-v2' and report['asic_cpu_verified'] is True and
            report['cpu_executed'] is True and report['global_FPGA_defined'] is False and
            report['tasks'] == 1200 and report['checked_outputs'] == 30412800 and report['failed'] == 0 and
            report['compile_count'] == 1, 'Incomplete actual ICB32 batch')
    identity = read(root/'batch_identity.json')
    require(sha(root/'batch_identity.json') == report['batch_identity_sha256'] and
            identity['dataset_manifest_sha256'] == DATASET_SHA256 and
            identity['firmware_manifest_sha256'] == firmware_sha, 'Mixed batch identity')
    require(configuration_identity(root) == hardware, 'Batch hardware differs from selected version')
    contract = read(root/'icb32_build_contract.json'); soc.verify_frozen(contract)
    require(sha(root/'icb32_build_contract.json') == identity['build_contract_sha256'], 'Batch build changed')
    tasks = index_legacy_dataset(identity['dataset'])
    require(tasks == identity['task_list'] and len(tasks) == len(report['cases']) == 1200, 'Batch task list differs')
    receipts = []
    for task, entry in zip(tasks, report['cases']):
        path = (root/entry['receipt']).resolve(); path.relative_to(root)
        require(path == root/'cases'/task['key']/'receipt.json' and entry['key'] == task['key'] and
                sha(path) == entry['receipt_sha256'], 'Batch receipt/order differs')
        row = read(path)
        require(row['batch_identity_sha256'] == report['batch_identity_sha256'] and
                row['sample'] == task['sample'] and row['layer'] == task['layer'] and
                row['key'] == task['key'] and row['asic_cpu_verified'] is True and
                row['scope'] == 'asic_rtl_functional', 'Wrong task evidence')
        check_case(row, path.parent, task['source'], 'task')
        require(entry['cycles'] == row['task_window']['cycles'] and entry['outputs'] == 25344,
                'Batch aggregate differs from original task')
        receipts.append(dict(key=task['key'], sha256=entry['receipt_sha256']))
    require(sha(root/'summary.json') == ref['sha256'], 'Batch changed during audit')
    return dict(status='passed_reaudited', tasks=1200, outputs=30412800, receipts=receipts,
                summary_sha256=ref['sha256'], official_precision_verified=False)


def build(request):
    require(request['schema'] == 'icb32-report-request-v1', 'Wrong report schema')
    refs = {k: request[k] for k in ('asic', 'synthesis', 'gate')}
    a, s, g = [load_stage(refs[k], stage) for k, stage in
               (('asic', 'icb32_soc'), ('synthesis', 'icb32_synth'), ('gate', 'icb32_gate'))]
    arun, srun, grun = [Path(refs[k]['run']).resolve() for k in ('asic', 'synthesis', 'gate')]
    require(sha(arun/'source_inputs.json') == a['compile_receipt']['source_inputs_sha256'] and
            read(arun/'compile_receipt.json') == a['compile_receipt'], 'ASIC compile receipt changed')
    soc.verify_frozen(read(arun/'icb32_build_contract.json'))
    require(sha(arun/'icb32_build_contract.json') == a['build_contract_sha256'], 'ASIC build changed')
    hardware = configuration_identity(arun)
    require(hardware == configuration_identity(srun) and
            a['compile_receipt']['platform_baseline_sha256'] == s['link_report']['platform_baseline_sha256'],
            'ASIC and synthesis hardware differs')
    require(sha(grun/'source_inputs.json') == g['source_inputs_sha256'], 'Gate inputs changed')
    source_inventory(grun/'source_inputs.json')
    numbers = [extract(Path(r['run']), r['sha256']) for r in request.get('power', [])]
    rows, aggregate = join_cases(a, g, s, refs, numbers)
    final = audit_batch(request.get('batch'), hardware, g['firmware_sha256'])
    history = request.get('history', [])
    require(all(h.get('status') in ('failed', 'stopped', 'unverified') and h.get('description') and h.get('run')
                for h in history), 'History needs preserved run/status/description')
    return dict(schema='icb32-evidence-export-v1', status='evidence_exported_review_required',
        references=refs, hardware=hardware, firmware_sha256=g['firmware_sha256'],
        library_inputs_sha256=s['link_report']['library_inputs'], area=s['area_summary'],
        area_basis=s['area_basis'], timing_metrics=s['metrics'],
        declared_conditions=dict(corner='SS', voltage_v='0.99', temperature_c=125, period_ns='6.666666'),
        cases=rows, aggregate=aggregate, batch=final, history=history,
        power_references=request.get('power', []),
        unverified=s['required_reviews']+['Protocol/recovery/contention and clean-directory reproduction',
            'System power units, models, activity and unknown-state impact review'],
        verification=dict(asic_14=True, gate_14_without_sdf=True, activity_12=True,
            timing_verified=False, scoring_area_verified=False, system_power_verified=False,
            official_precision_verified=False, physical_signoff=False), exporter_sha256=sha(__file__))


def write_outputs(report, output):
    output = Path(output); output.mkdir(parents=True, exist_ok=False)
    data.save(output/'report.json', report)
    fields = ['case', 'cycles', 'encoded_bytes', 'transfer_bytes', 'transfer_transactions',
              'nominal_150mhz_tasks_per_second', 'nominal_150mhz_mmac_per_second',
              'raw_dynamic_w', 'raw_leakage_w', 'raw_average_power_w', 'raw_energy_j',
              'layout_sha256', 'codec_sha256', 'activity_sha256', 'unknown_value_records']
    for filename, rows, columns in [('tasks.csv', report['cases'], fields),
        ('summary.csv', [report['aggregate']], list(report['aggregate']))]:
        with (output/filename).open('x', encoding='utf-8-sig', newline='') as stream:
            writer = csv.DictWriter(stream, columns, extrasaction='ignore'); writer.writeheader(); writer.writerows(rows)
    a = report['aggregate']
    lines = ['# 架构三 ICB32 冻结配置证据汇总', '',
        '真实 ASIC/E203 14例、无SDF门级14例及12个完整活动窗口已逐项核对。时序、面积归属和系统功耗仍待审核；功耗为布局前估算。', '',
        '统一SS、0.99V、125°C、6.666666ns。首源VALID至最终结果写ACK，随后证明排空；每任务冷启动。压缩输入传输量逐层记录，为2×编码字节数+50688B，未省略共享SRAM实际写入。', '',
        '12层平均周期 %s；150MHz折算 %s task/s；目标为5000 task/s。' % (a['mean_cycles'], a['nominal_150mhz_tasks_per_second']), '',
        '| 层 | 周期 | 编码字节 | 平均功耗W | 能耗J/task |', '|---|---:|---:|---:|---:|']
    for r in report['cases']:
        lines.append('| %s | %s | %s | %s | %s |' % (r['case'], r['cycles'], r['encoded_bytes'],
            r['raw_average_power_w'] if r['raw_average_power_w'] is not None else '缺失',
            r['raw_energy_j'] if r['raw_energy_j'] is not None else '缺失'))
    lines += ['', '最终100样本批量：%s，%d任务、%d输出；内部回归不代表官方600样本精度验收。' %
        (report['batch']['status'], report['batch']['tasks'], report['batch']['outputs']), '',
        '源码、固件、库、布局、编码、网表及活动哈希和模块功耗分量见JSON；缺失功耗保持为空，不计为零。', '', '待审核项目：', '']
    lines += ['- '+item for item in report['unverified']]
    lines += ['', '历史失败、停止与未验路径：', '']
    lines += ['- %s：%s；%s' % (h['status'], h['description'], h['run']) for h in report['history']]
    (output/'report_zh.md').write_text('\n'.join(lines)+'\n', encoding='utf8')
    data.save(output/'receipt.json', dict(schema='icb32-evidence-export-receipt-v1',
        artifacts={p.name: sha(p) for p in output.iterdir() if p.is_file()}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args(); digest = sha(args.request)
    report = build(read(args.request)); require(sha(args.request) == digest, 'Request changed')
    report['request_sha256'] = digest; write_outputs(report, args.output)
    print('ICB32_EVIDENCE_EXPORTED review_required=true', args.output)


if __name__ == '__main__': main()
