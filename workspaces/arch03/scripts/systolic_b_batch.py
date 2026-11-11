"""One compiled ASIC/E203 simulator, 100 samples x 12 cold compressed tasks.

Uses the independently pinned legacy dataset and the new ASIC boot/monitor
contract. Every case has its own data, boot metadata, capture and receipt. No
old DMA16/functional-TCM batch PASS can be imported by this entry point.
"""
import datetime
import math
import time
from pathlib import Path

from server_run import ROOT,A3,sha,save
from dma16_batch import index_legacy_dataset,DATASET_SHA256
import systolic_b_data as data
import systolic_b_soc as soc


def verify(cfg,run,platform_source,dataset,call):
    run,dataset=Path(run),Path(dataset).resolve()
    data.require(dataset.is_dir(),'Missing pinned 100-sample dataset')
    # Reject the old 37-case batch or any changed sample list before compiling.
    tasks=index_legacy_dataset(dataset)
    data.require(len(tasks)==1200,'Expected exactly 1200 tasks')
    contract,compile_receipt,fw,base=soc.compile_design(cfg,run,platform_source,call)
    data.require(contract.get('diagnostic') is None and contract['row_lanes']==5 and
        contract['layout_id'] in (0x00100002,0x00100003) and fw['configuration']['irq_enabled'],
        'Final B batch requires the frozen five-row IRQ firmware')
    identity=dict(schema='arch03-systolic-b-batch-v3',dataset=str(dataset),
        dataset_manifest_sha256=DATASET_SHA256,layout_id=contract['layout_id'],row_lanes=5,samples=100,tasks=1200,
        outputs_per_task=25344,expected_outputs=30412800,
        build_contract_sha256=sha(run/'systolic_b_build_contract.json'),
        runner_sha256=sha(Path(__file__)),data_script_sha256=sha(A3/'scripts/systolic_b_data.py'),
        soc_script_sha256=sha(A3/'scripts/systolic_b_soc.py'),
        firmware_manifest_sha256=sha(Path(contract['firmware'])/'manifest.json'),
        task_list=tasks,compile_count=1,global_FPGA_defined=False,
        cold_task_boot=True,cross_task_prefetch=False,large_waveforms=False,
        started_utc=datetime.datetime.utcnow().isoformat()+'Z')
    save(run/'batch_identity.json',identity)
    identity_sha=sha(run/'batch_identity.json');started=time.monotonic();results=[]
    for task in tasks:
        case_run=run/'cases'/task['key'];case_run.mkdir(parents=True,exist_ok=False)
        soc.verify_frozen(contract)
        result=soc.run_case(contract,fw,base,Path(task['source']),case_run,'task',call)
        soc.verify_frozen(contract)
        data.require(sha(run/'batch_identity.json')==identity_sha,'Batch identity changed')
        result.update(status='passed',asic_cpu_verified=True,sample=task['sample'],
            layer=task['layer'],key=task['key'],batch_identity_sha256=identity_sha,
            source_layout_sha256=sha(Path(task['source'])/'layout.json'),
            scope='asic_rtl_functional',timing_verified=False,system_power_verified=False)
        save(case_run/'receipt.json',result)
        results.append(dict(key=task['key'],outputs=result['outputs'],
            cycles=result['task_window']['cycles'],encoded_bytes=result['task_window']['encoded_bytes'],
            host_seconds=result['host_elapsed_seconds'],
            receipt=str((case_run/'receipt.json').relative_to(run)),receipt_sha256=sha(case_run/'receipt.json')))
        elapsed=time.monotonic()-started
        remaining=(1200-len(results))*elapsed/len(results)
        save(run/'batch_progress.json',dict(status='running',completed=len(results),failed=0,
            checked_outputs=sum(r['outputs'] for r in results),host_elapsed_seconds=elapsed,
            estimated_remaining_seconds_with_20percent_margin=remaining*1.2,cases=results))
        print('SYSTOLIC_B_BATCH_CASE_PASS',task['key'],'completed',len(results),
              'cycles',result['task_window']['cycles'],'host_seconds',result['host_elapsed_seconds'],flush=True)
    # Recheck original per-task receipts and data identity, not just a PASS count.
    data.require(index_legacy_dataset(dataset)==tasks,'Dataset changed during batch')
    soc.verify_frozen(contract)
    for entry in results:
        receipt=run/entry['receipt']
        data.require(sha(receipt)==entry['receipt_sha256'],'Case receipt changed')
    outputs=sum(r['outputs'] for r in results)
    data.require(len(results)==1200 and outputs==30412800,'Incomplete final batch')
    cycles=[r['cycles'] for r in results];sizes=[r['encoded_bytes'] for r in results];elapsed=time.monotonic()-started
    data.require(all(type(c) is int and c>0 for c in cycles) and math.isfinite(elapsed),'Invalid batch measurements')
    return dict(status='passed',schema='arch03-systolic-b-batch-v3',scope='asic_rtl_functional',
        asic_cpu_verified=True,cpu_executed=True,global_FPGA_defined=False,
        samples=100,tasks=1200,checked_outputs=outputs,failed=0,compile_count=1,
        layout_id=contract['layout_id'],row_lanes=5,
        batch_identity_sha256=identity_sha,compile_receipt=compile_receipt,cases=results,
        host_elapsed_seconds=elapsed,mean_task_cycles=sum(cycles)/1200.,
        min_task_cycles=min(cycles),max_task_cycles=max(cycles),
        encoded_bytes_min=min(sizes),encoded_bytes_mean=sum(sizes)/1200.,encoded_bytes_max=max(sizes),
        task_s_at_150MHz=150000000.*1200/sum(cycles),
        official_precision_verified=False,gate_simulation_verified=False,
        timing_verified=False,system_power_verified=False,physical_signoff=False)
