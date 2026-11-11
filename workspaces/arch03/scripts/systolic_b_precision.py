"""Apply pinned floating-reference errors only after B's own bit-exact1200.

The unchanged Q12 output equals the pinned integer reference element-for-
element. Therefore its error to that reference's original float matrix is
identical. This reuses hashed SSE/energy, not old hardware PASS, and never
labels the internal100 as official600 or claims a new float forward pass.
"""
import argparse
import json
import math
from pathlib import Path
from server_run import sha,save
from dma16_batch import DATASET_SHA256,index_legacy_dataset
import systolic_b_soc as soc
import systolic_b_data as data


def nrmse(sse,energy,count):
    if (type(count) is not int or count<=0 or
        any(type(v) not in (int,float) or not math.isfinite(v) or v<0 for v in (sse,energy))):
        raise ValueError('Invalid floating-reference error statistics')
    return math.sqrt(sse/count)/max(math.sqrt(energy/count),1e-8)


def reference_rows(manifest):
    rows={};totals={layer:[0.,0.,0] for layer in range(1,13)}
    for sample in manifest['samples']:
        for entry in sample['layers']:
            key=(sample['sample'],entry['layer_number'])
            if key in rows or key[1] not in totals or entry['outputs']!=25344 or entry['shift']!=12:
                raise ValueError('Invalid sample/layer reference')
            sse=entry['error_squared_sum'];energy=entry['float_reference_squared_sum']
            value=nrmse(sse,energy,entry['outputs'])
            if not math.isclose(value,entry['nrmse'],rel_tol=1e-12,abs_tol=1e-15):
                raise ValueError('Pinned task NRMSE differs from its SSE/energy')
            rows[key]=dict(sample=key[0],layer=key[1],sse=sse,reference_energy=energy,
                outputs=25344,nrmse=value,nrmse_percent=value*100)
            total=totals[key[1]];total[0]+=sse;total[1]+=energy;total[2]+=25344
    if set(rows)!={(s,l) for s in range(1,101) for l in range(1,13)}:
        raise ValueError('Not the full fixed100 x12 reference')
    layers=[]
    for layer,(sse,energy,count) in sorted(totals.items()):
        value=nrmse(sse,energy,count)
        if not math.isclose(value,manifest['aggregate_layer_nrmse'][layer-1],rel_tol=1e-12,abs_tol=1e-15):
            raise ValueError('Pinned layer NRMSE differs from aggregated SSE/energy')
        layers.append(dict(layer=layer,outputs=count,sse=sse,reference_energy=energy,nrmse=value,nrmse_percent=value*100))
    if not math.isclose(max(r['nrmse_percent'] for r in layers),manifest['aggregate_max_nrmse_percent'],rel_tol=1e-12,abs_tol=1e-13):
        raise ValueError('Pinned maximum layer NRMSE mismatch')
    return rows,layers


def audit(run,expected_sha):
    run=Path(run).resolve();report=json.loads((run/'summary.json').read_text())
    state=json.loads((run.parent/'state.json').read_text())['stages']['systolic_b_batch']
    if (sha(run/'summary.json')!=expected_sha or state.get('status')!='passed' or
        state.get('summary_sha256')!=expected_sha or report.get('schema')!='arch03-systolic-b-batch-v3' or
        report.get('asic_cpu_verified') is not True or report.get('tasks')!=1200 or
        report.get('checked_outputs')!=30412800 or report.get('failed')!=0):
        raise ValueError('B own actual ASIC1200 is not complete')
    identity=json.loads((run/'batch_identity.json').read_text())
    if sha(run/'batch_identity.json')!=report['batch_identity_sha256'] or identity['dataset_manifest_sha256']!=DATASET_SHA256:
        raise ValueError('B batch identity changed')
    contract=json.loads((run/'systolic_b_build_contract.json').read_text());soc.verify_frozen(contract)
    if sha(run/'systolic_b_build_contract.json')!=identity['build_contract_sha256']:
        raise ValueError('Wrong frozen ASIC build')
    dataset=Path(identity['dataset']);tasks=index_legacy_dataset(dataset)
    if tasks!=identity['task_list'] or len(report['cases'])!=1200:raise ValueError('Batch task identity changed')
    reference=json.loads((dataset/'manifest.json').read_text());rows,layers=reference_rows(reference)
    actual=[]
    for task,entry in zip(tasks,report['cases']):
        case_run=run/'cases'/task['key'];receipt=case_run/'receipt.json'
        if entry['key']!=task['key'] or (run/entry['receipt']).resolve()!=receipt or sha(receipt)!=entry['receipt_sha256']:
            raise ValueError('B task receipt changed')
        row=json.loads(receipt.read_text())
        if (row['sample'],row['layer'],row['key'])!=(task['sample'],task['layer'],task['key']) or row['asic_cpu_verified'] is not True:
            raise ValueError('Wrong task/CPU proof')
        data.verify_prepared(Path(task['source']),case_run/'task_data')
        capture=data.check_capture(case_run/'task.csv',Path(task['source']))
        if capture!=row['capture'] or row['source_layout_sha256']!=sha(Path(task['source'])/'layout.json'):
            raise ValueError('Actual capture/saturation differs from pinned integer reference')
        text=(case_run/'task.log').read_text()
        result=data.parse_result(text,capture['saturated'],soc.MARKERS)
        if data.read_window(text,result,row['task_window']['encoded_bytes'])!=row['task_window']:
            raise ValueError('Actual CPU log/window changed')
        values=dict(rows[(task['sample'],task['layer'])]);values.update(
            actual_capture_sha256=capture['capture_sha256'],receipt_sha256=entry['receipt_sha256'])
        actual.append(values)
    soc.verify_frozen(contract)
    if sha(dataset/'manifest.json')!=DATASET_SHA256 or sha(run/'summary.json')!=expected_sha:
        raise ValueError('Frozen evidence changed during precision audit')
    return dict(status='internal100_precision_from_actual_bit_exact_outputs',dataset_kind='development',
        samples=100,tasks=1200,outputs=30412800,integer_bit_exact=True,layers=layers,task_metrics=actual,
        maximum_layer_nrmse_percent=max(r['nrmse_percent'] for r in layers),
        maximum_task_nrmse_percent=max(r['nrmse_percent'] for r in actual),
        internal_three_percent_threshold_passed=all(r['nrmse']<=.03 for r in layers+actual),
        official_precision_verified=False,float_reference_recomputed_this_run=False,
        reference_error_metrics_reused_under_bit_exact_proof=True,
        dataset_manifest_sha256=DATASET_SHA256,float_manifest_sha256=reference['float_manifest_sha256'],
        batch_run=str(run),batch_summary_sha256=expected_sha,runner_sha256=sha(Path(__file__)),
        method='Sum pinned per-task SSE and reference energy by layer only after rechecking all actual B integer outputs; never average NRMSE ratios')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--batch-run',type=Path,required=True)
    parser.add_argument('--batch-summary-sha256',required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():raise ValueError('Use a fresh precision output')
    result=audit(args.batch_run,args.batch_summary_sha256);save(args.output,result)
    print('B_INTERNAL100_PRECISION_REAUDITED official_precision_verified=false',args.output)
