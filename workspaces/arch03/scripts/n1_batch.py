"""One N1 ASIC/E203 compilation, 100 x 12 cold tasks, native signed33 proof.

The PR #9 HEX inventory is pinned independently of all B0/Q12 datasets.  Every
case checks row/column uniqueness and total/result/saturation at actual output
write responses.  The caller owns the server lock; no old queue is resumed.
"""
import datetime
import math
from pathlib import Path
import shutil
import time

from server_run import A3, sha, save
import n1_data as data
import n1_soc as soc

SCHEMA = 'arch03-n1-batch-v4'


def storage_guard(run, remaining, observed_max=8*1024*1024):
    free = shutil.disk_usage(str(run)).free
    required = math.ceil(remaining*observed_max*1.2)+2*1024**3
    receipt = dict(free_bytes=free, remaining_tasks=remaining, maximum_case_bytes=observed_max,
                   margin=1.2, reserve_bytes=2*1024**3, required_bytes=required)
    save(Path(run)/'storage_budget.json', receipt)
    data.require(free >= required, 'Insufficient space for N1 batch with 20% margin; evidence retained')
    return receipt


def verify(cfg, run, platform_source, dataset, call):
    run, dataset = Path(run), Path(dataset).resolve()
    data.require(dataset.is_dir(), 'Missing pinned N1 100-sample dataset')
    tasks = data.index_dataset(dataset)
    data.require(len(tasks) == 1200 and all(task['shift'] == 10 for task in tasks),
                 'Expected 1200 N1 SHIFT10 tasks')
    storage_guard(run, 1200)
    contract, compile_receipt, fw, base = soc.compile_design(cfg, run, platform_source, call)
    data.require(contract.get('diagnostic') is None and contract['row_lanes'] == 5 and
                 contract['layout_id'] == 0x00100004 and fw['configuration']['irq_enabled'] and
                 fw['numeric_format'] == '0x000e0c20', 'N1 batch requires five-row SHIFT10 IRQ firmware')
    identity = dict(schema=SCHEMA, dataset=str(dataset),
        dataset_inventory_sha256=data.DATA100_INVENTORY_SHA,
        dataset_manifest_sha256=sha(dataset/'manifest.json'),
        layout_id=0x00100004, numeric_format_id=0x000e0c20, numeric_format=data.FORMAT,
        row_lanes=5, samples=100, tasks=1200, outputs_per_task=25344, expected_outputs=30412800,
        fields_checked=['total_signed33', 'result_signed16', 'saturated'],
        capture_columns=['row', 'column', 'result', 'saturated', 'total'],
        build_contract_sha256=sha(run/'n1_build_contract.json'),
        runner_sha256=sha(Path(__file__)), data_script_sha256=sha(A3/'scripts/n1_data.py'),
        soc_script_sha256=sha(A3/'scripts/n1_soc.py'),
        firmware_manifest_sha256=sha(Path(contract['firmware'])/'manifest.json'),
        task_list=tasks, compile_count=1, global_FPGA_defined=False,
        cold_task_boot=True, cross_task_prefetch=False, large_waveforms=False,
        started_utc=datetime.datetime.utcnow().isoformat()+'Z')
    save(run/'batch_identity.json', identity)
    identity_sha = sha(run/'batch_identity.json')
    started, results, case_bytes_max = time.monotonic(), [], 0
    for task in tasks:
        case_run = run/'cases'/task['key']
        case_run.mkdir(parents=True, exist_ok=False)
        soc.verify_frozen(contract)
        data.require(sha(Path(task['source'])/'layout.json') == task['source_layout_sha256'],
                     'Frozen source layer changed before task')
        result = soc.run_case(contract, fw, base, Path(task['source']), case_run, 'task', call)
        soc.verify_frozen(contract)
        data.require(sha(run/'batch_identity.json') == identity_sha, 'N1 batch identity changed')
        data.require(result['outputs'] == result['total_outputs'] == 25344 and
                     result['capture']['total_checked'] is True and result['capture']['mismatches'] == 0,
                     'N1 task lacks native total/reference proof')
        result.update(status='passed', asic_cpu_verified=True, sample=task['sample'],
            layer=task['layer'], key=task['key'], batch_identity_sha256=identity_sha,
            source_layout_sha256=task['source_layout_sha256'], scope='asic_rtl_functional',
            timing_verified=False, system_power_verified=False, official_precision_verified=False)
        save(case_run/'receipt.json', result)
        results.append(dict(key=task['key'], outputs=result['outputs'], total_outputs=result['total_outputs'],
            cycles=result['task_window']['cycles'], encoded_bytes=result['task_window']['encoded_bytes'],
            host_seconds=result['host_elapsed_seconds'],
            capture_sha256=result['capture']['capture_sha256'],
            receipt=str((case_run/'receipt.json').relative_to(run)), receipt_sha256=sha(case_run/'receipt.json')))
        case_bytes_max = max(case_bytes_max, sum(p.stat().st_size for p in case_run.rglob('*') if p.is_file()))
        storage_guard(run, 1200-len(results), case_bytes_max)
        elapsed = time.monotonic()-started
        remaining = (1200-len(results))*elapsed/len(results)
        save(run/'batch_progress.json', dict(status='running', completed=len(results), failed=0,
            checked_outputs=sum(item['outputs'] for item in results),
            checked_totals=sum(item['total_outputs'] for item in results), host_elapsed_seconds=elapsed,
            estimated_remaining_seconds_with_20percent_margin=remaining*1.2, cases=results))
        print('N1_BATCH_CASE_PASS', task['key'], 'completed', len(results),
              'cycles', result['task_window']['cycles'], 'host_seconds', result['host_elapsed_seconds'], flush=True)
    # Re-audit actual original captures/references and all root/source identities,
    # rather than treating 1200 PASS labels as the final proof.
    data.require(data.index_dataset(dataset) == tasks, 'Dataset changed during N1 batch')
    soc.verify_frozen(contract)
    for task, entry in zip(tasks, results):
        receipt = run/entry['receipt']
        data.require(sha(receipt) == entry['receipt_sha256'], 'N1 case receipt changed')
        case_run = receipt.parent
        data.verify_prepared(Path(task['source']), case_run/'task_data')
        captured = data.check_capture(case_run/'task.csv', case_run/'task_data')
        data.require(captured['capture_sha256'] == entry['capture_sha256'] and captured['total_checked'],
                     'N1 final capture audit changed')
    outputs = sum(item['outputs'] for item in results)
    totals = sum(item['total_outputs'] for item in results)
    data.require(len(results) == 1200 and outputs == totals == 30412800, 'Incomplete N1 final batch')
    cycles, sizes = [item['cycles'] for item in results], [item['encoded_bytes'] for item in results]
    elapsed = time.monotonic()-started
    data.require(all(type(c) is int and c > 0 for c in cycles) and math.isfinite(elapsed), 'Invalid N1 measurements')
    report = dict(status='passed', schema=SCHEMA, scope='asic_rtl_functional',
        asic_cpu_verified=True, cpu_executed=True, global_FPGA_defined=False,
        samples=100, tasks=1200, checked_outputs=outputs, checked_totals=totals,
        checked_saturation_flags=outputs, failed=0, compile_count=1,
        layout_id=0x00100004, numeric_format_id=0x000e0c20, shift=10, row_lanes=5,
        batch_identity_sha256=identity_sha, compile_receipt=compile_receipt, cases=results,
        host_elapsed_seconds=elapsed, mean_task_cycles=sum(cycles)/1200.,
        min_task_cycles=min(cycles), max_task_cycles=max(cycles),
        encoded_bytes_min=min(sizes), encoded_bytes_mean=sum(sizes)/1200., encoded_bytes_max=max(sizes),
        task_s_at_150MHz=150000000.*1200/sum(cycles),
        precision_scope='integer/reference consistency only; fresh same-data float accuracy is a separate gate',
        official_precision_verified=False, gate_simulation_verified=False,
        timing_verified=False, system_power_verified=False, physical_signoff=False)
    save(run/'batch_progress.json', dict(status='passed', completed=1200, failed=0,
        checked_outputs=outputs, checked_totals=totals, host_elapsed_seconds=elapsed, cases=results))
    return report
