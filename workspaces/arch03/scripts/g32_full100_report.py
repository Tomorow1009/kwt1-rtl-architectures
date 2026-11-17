"""Export completed G32 full100 results, keeping fixed12 PPA a distinct scope."""
import argparse
import csv
import datetime
import json
from pathlib import Path
import g32_full100_archive_contract as contract
from partition_synth_contract import require, digest

BASELINE_SHA = '836bc334073e0a5fada5ade763126a2b838bad58c5c0196858d3110f1d95b9fc'


def read(p): return json.loads(Path(p).read_text())
def save(p, value):
    with Path(p).open('x', encoding='utf8') as f:
        json.dump(value, f, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
        f.write('\n')


def build_rows(batch, numeric):
    require(len(batch['cases']) == len(numeric['cases']) == 1200, 'Incomplete task set')
    cases = []
    for observed, error in zip(batch['cases'], numeric['cases']):
        key = 'sample_%03d_layer_%02d' % (error['sample'], error['layer'])
        require(observed['key'] == key and observed['outputs'] == observed['total_outputs'] == error['outputs'] == 25344,
                'Task coordinates or output count differ')
        cases.append(dict(key=key, sample=error['sample'], layer=error['layer'],
            cycles=observed['cycles'], encoded_bytes=observed['encoded_bytes'],
            host_seconds=observed['host_seconds'], outputs=observed['outputs'], total_outputs=observed['total_outputs'],
            nrmse_percent=error['nrmse_percent'], sse=error['sse'], reference_energy=error['reference_energy'],
            saturated=error['saturated'], clip_x=error['clipping']['x'], clip_w=error['clipping']['w'],
            clip_b=error['clipping']['b'], capture_sha256=observed['capture_sha256'],
            receipt_sha256=observed['receipt_sha256']))
    from n1_precision import aggregate
    layers = aggregate(numeric['cases'])
    for row in layers:
        selected = [v for v in cases if v['layer'] == row['layer']]
        require(len(selected) == 100, 'Missing layer samples')
        cycles = [v['cycles'] for v in selected]
        row.update(total_complete_cycles=sum(cycles), mean_complete_cycles=sum(cycles)/100.,
            min_complete_cycles=min(cycles), max_complete_cycles=max(cycles),
            nominal_150MHz_task_s=150000000.*100/sum(cycles),
            encoded_bytes_mean=sum(v['encoded_bytes'] for v in selected)/100.)
    return cases, layers


def export(request, baseline, output):
    bundle = Path(request['bundle'])
    proof = contract.evidence(request, bundle)
    baseline = Path(baseline)
    require(digest(baseline) == BASELINE_SHA, 'Frozen G32 conclusion changed')
    old = read(baseline)
    require(old['technical_stage_accepted'] is True and old['pe_count'] == 32 and
        old['production_rtl_commit'] == '0e16994675bb15e53642017a88f6307da9af4a01' and
        old['prelayout_system_power_estimate_reviewed'] is True, 'Wrong frozen PPA baseline')
    refs = proof['references']
    batch = read(Path(refs['batch100']['run'])/'summary.json')
    precision = read(Path(refs['precision100']['run'])/'summary.json')
    numeric = read(Path(precision['reference']['run'])/'summary.json')
    cases, layers = build_rows(batch, numeric)
    cycles = [v['cycles'] for v in cases]
    require(sum(cycles)/1200. == batch['mean_task_cycles'], 'Cycle aggregate differs')
    ppa = {k: old[k] for k in ('fixed12', 'project_conservative_area_mm2', 'known_added_area_mm2',
        'whole_soc_area_mm2', 'period_ns', 'setup_ns', 'hold_ns', 'clock_gating', 'netlist_sha256',
        'scope', 'nonblocking_model_limits')}
    ppa.update(scope_samples=12, source_conclusion_sha256=BASELINE_SHA,
        reused_for_identical_frozen_hardware=True, measured_on_this_full100_batch=False)
    result = dict(schema='arch03-g32-full100-addendum-report-v1', status='passed',
        generated_at=datetime.datetime.now().isoformat(), hardware_commit=old['production_rtl_commit'],
        bundle_manifest_sha256=contract.MANIFEST, batch_summary_sha256=refs['batch100']['sha256'],
        precision_summary_sha256=refs['precision100']['sha256'], queue_state_sha256=request['state_sha256'],
        archive_admission=proof, samples=100, tasks=1200, checked_outputs=30412800,
        checked_totals=30412800, checked_saturation_flags=30412800, failed=0,
        total_complete_cycles=sum(cycles), mean_complete_cycles=sum(cycles)/1200.,
        min_complete_cycles=min(cycles), max_complete_cycles=max(cycles),
        nominal_150MHz_task_s=150000000.*1200/sum(cycles),
        host_elapsed_seconds=batch['host_elapsed_seconds'], compile_count=1,
        maximum_layer_nrmse_percent=precision['maximum_layer_nrmse_percent'],
        maximum_task_nrmse_percent=precision['maximum_task_nrmse_percent'],
        clipping=precision['quantization_clipping_count'], saturated=precision['saturation_count'],
        layer_aggregate=layers, cases=cases, fixed12_frozen_PPA=ppa,
        official600_verified=False, physical_signoff=False, full100_power_measured=False,
        hardware_changed=False, frozen_release_tag='arch03-g32-final-20261117',
        exporter_sha256=digest(__file__), source_modified=False)
    output = Path(output)
    require(not output.exists() and output.parent == bundle.parent, 'Use a new report directory in this runtime root')
    output.mkdir(mode=0o700)
    save(output/'report.json', result)
    with (output/'tasks.csv').open('x', newline='', encoding='utf8') as f:
        writer=csv.DictWriter(f,fieldnames=list(cases[0]));writer.writeheader();writer.writerows(cases)
    with (output/'layers.csv').open('x', newline='', encoding='utf8') as f:
        rows=[{k:v for k,v in row.items() if k!='clipping'} for row in layers]
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    fixed=old['fixed12']
    text = ('# G32完整100条追加回归结果\n\n'
        '同一冻结G32已完成100条×12层、1200个真实ASIC/E203冷启动任务；'
        '30,412,800个结果、total及饱和标志逐项核对通过，零失败。硬件及原冻结标签保持不变。\n\n'
        '完整100条平均周期：%.10f；按150MHz折算吞吐：%.10f task/s。'
        '最坏逐层汇总NRMSE：%.10f%%，最坏单任务NRMSE：%.10f%%。'
        '逐层误差先合并SSE和参考能量再计算，属于内部验证。\n\n'
        '原固定12任务PPA单独保留：平均周期%.10f、吞吐%.10f task/s、'
        '项目面积保守上界%.10f mm²、布局前整机平均功耗%.10f mW、%.10f µJ/task。'
        '本次100条没有重新采集功耗，不能将两批周期与功耗拼接计算能耗。\n\n'
        '首次队列因共享盘不足而在取锁前失败；其记录保留。后续独立队列完成全部1200任务。'
        '旧八路、桌面T80、冻结G32及历史证据保留。官方600条与物理签核不属于本次结果。\n\n'
        '完整逐任务和逐层数据见tasks.csv、layers.csv；身份及检查回执见report.json。\n'
        ) % (result['mean_complete_cycles'], result['nominal_150MHz_task_s'],
            result['maximum_layer_nrmse_percent'],result['maximum_task_nrmse_percent'],
            float(fixed['mean_complete_cycles']),float(fixed['nominal_150MHz_task_s']),
            old['project_conservative_area_mm2'],float(fixed['time_weighted_power_w'])*1e3,
            float(fixed['mean_energy_j'])*1e6)
    with (output/'REPORT_ZH.md').open('x',encoding='utf8') as f:f.write(text)
    save(output/'receipt.json',dict(schema='arch03-g32-full100-export-receipt-v1',
        files={p.name:digest(p) for p in output.iterdir() if p.is_file()},
        inputs=proof['inputs'],baseline_conclusion_sha256=BASELINE_SHA))
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('request','baseline','output'):p.add_argument('--'+key,required=True,type=Path)
    p.add_argument('--request-sha256',required=True);a=p.parse_args()
    require(digest(a.request)==a.request_sha256,'Export request changed')
    result=export(read(a.request),a.baseline,a.output)
    print('G32_FULL100_REPORT_PASS',result['tasks'],result['checked_outputs'],flush=True)
