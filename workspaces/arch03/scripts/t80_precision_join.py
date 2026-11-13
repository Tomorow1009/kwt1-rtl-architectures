"""Read-only first20 FLOAT/ASIC join; never runs new hardware tasks."""
import argparse,json,math,re
from pathlib import Path
import n1_data as data
import n1_precision as precision_tools
import t80_precision as recovered_precision
import t80_soc as soc
import t80_gate as gate_tools
from t80_window import read_window
from t80_bus_metrics import parse_metrics
from native_saif_replay import verify_inputs
from server_run import save
from icb32_power import stream_sha as sha
from t80_batch import select_first20

def read(path):return json.loads(Path(path).read_text())

def require(ok,message):
    if not ok:raise ValueError(message)

def check_case(row,run,name,source=None,mapped=False):
    run=Path(run);task=run/(name+'_data')
    source=Path(source) if source is not None else run.parents[2]/'validated_data'/name
    data.verify_prepared(source,task)
    capture=(gate_tools.check_capture if mapped else data.check_capture)(run/(name+'.csv'),task)
    require(capture==row['capture'] and row['outputs']==25344 and
        row.get('numeric_format')=='0x000e0c20','Actual T80 output receipt differs')
    require(capture.get('total_checked') is (not mapped),'Total observability scope mismatch')
    if not mapped:require(row.get('total_outputs')==25344,'ASIC total33 proof incomplete')
    for path,key in ((task/'codec.json','codec_sha256'),(task/'layout_manifest.json','layout_sha256'),
        (run/(name+'.log'),'log_sha256'),(run/(name+'_boot')/'manifest.json','boot_manifest_sha256')):
        require(sha(path)==row[key],'Changed per-task provenance '+key)
    boot=read(run/(name+'_boot')/'manifest.json')
    require(boot['input_bytes_preloaded']==0,'Preloaded task data')
    require(all(Path(filename).name==filename for filename in boot['files']),'Unsafe boot filename')
    verify_inputs({str(run/(name+'_boot')/filename):value for filename,value in boot['files'].items()})
    text=(run/(name+'.log')).read_text();size=read(task/'codec.json')['encoded_bytes']
    markers=soc.MARKERS+['ARCH03_ICB32_SOURCE_READY words=%d scope=PC_file_only no_ITCM_task_data=true'%(size//4)]
    require(text.count('T80_BUS_ROUTE_PASS ')==1,'Missing original-System-Bus proof')
    result=(gate_tools.parse_result if mapped else data.parse_result)(text,capture['saturated'],markers)
    require(result==row['result'] and read_window(text,result,size)==row['task_window'],'Changed actual CPU log/window')
    cpu=re.findall(r'^ARCH03_ICB32_CPU_CYCLES (\d+)$',text,re.M)
    irq=re.findall(r'^ARCH03_ICB32_IRQ_PROOF enabled=(\d+) external=(\d+) timer=(\d+) wfi=(\d+) events=(\d+) unhandled=(\d+)$',text,re.M)
    q=row['irq_proof']
    require(len(cpu)==len(irq)==1 and int(cpu[0])==row['cpu_cycles'] and
        tuple(map(int,irq[0]))==tuple(int(q[k]) for k in ('enabled','external','timer','wfi','events','unhandled')) and
        q['enabled'] is True and min(q['external'],q['timer'],q['wfi'])>0 and q['events']&1 and not q['unhandled'],
        'Missing/changed actual IRQ/WFI execution')
    if row.get('passive_metrics') is not None:
        require(parse_metrics(text,row['task_window'])==row['passive_metrics'],'Passive metric receipt differs')


def audit_batch(run, report):
    """Recheck the first20 integer dataset; never reuse B0 float errors."""
    run=Path(run)
    require(report.get('schema')=='arch03-t80-first20-batch-v4' and report.get('asic_cpu_verified') is True and
        report.get('tasks')==240 and report.get('checked_outputs')==6082560 and
        report.get('checked_totals')==6082560 and report.get('failed')==0 and
        report.get('shift')==10 and report.get('numeric_format_id')==0x000e0c20,
        'T80 own actual ASIC240 is incomplete')
    identity=read(run/'batch_identity.json')
    require(sha(run/'batch_identity.json')==report['batch_identity_sha256'] and
        identity['dataset_inventory_sha256']==data.DATA100_INVENTORY_SHA and
        identity['samples']==20 and identity['tasks']==240 and identity['row_lanes']==5 and identity['compile_count']==1,
        'T80 batch data/hardware/firmware identity changed')
    contract=read(run/'t80_build_contract.json');soc.verify_frozen(contract)
    require(contract['schema']=='arch03-t80-asic-build-v4' and contract['diagnostic'] is None and
        contract['row_lanes']==5 and contract['layout_id']==0x00100004 and contract['clock_period_ns']=='6.666666' and
        sha(Path(contract['firmware'])/'manifest.json')==identity['firmware_manifest_sha256'], 'Wrong T80 build/firmware')
    require(sha(run/'t80_build_contract.json')==identity['build_contract_sha256'], 'T80 batch build changed')
    dataset=Path(identity['dataset']);tasks=select_first20(data.index_dataset(dataset))
    require(sha(dataset/'manifest.json')==identity['dataset_manifest_sha256'] and
        tasks==identity['task_list'] and len(report['cases'])==240,'First20 task identities changed')
    saturations=0
    for task,entry in zip(tasks,report['cases']):
        receipt=run/'cases'/task['key']/'receipt.json'
        require(entry['key']==task['key'] and (run/entry['receipt']).resolve()==receipt.resolve() and
            sha(receipt)==entry['receipt_sha256'] and entry['outputs']==entry['total_outputs']==25344,
            'T80 batch task receipt changed')
        row=read(receipt)
        require((row['sample'],row['layer'],row['key'])==(task['sample'],task['layer'],task['key']) and
            row['asic_cpu_verified'] is True and row['source_layout_sha256']==task['source_layout_sha256'] and
            row['batch_identity_sha256']==report['batch_identity_sha256'], 'Wrong T80 task/CPU identity')
        # check_case below is deliberately the strict five-column RTL path.
        check_case(row,receipt.parent,'task',task['source'])
        require(entry['capture_sha256']==row['capture']['capture_sha256'] and
            entry['cycles']==row['task_window']['cycles'],'T80 batch aggregate differs from real task')
        saturations+=row['capture']['saturated']
    return dict(status='first20_integer_bit_exact_float_precision_pending',samples=20,tasks=240,
        outputs=6082560,total_outputs=6082560,integer_bit_exact=True,saturated=saturations,
        batch_run=str(run.resolve()),batch_identity_sha256=report['batch_identity_sha256'],
        batch_summary_sha256=sha(run/'summary.json'),dataset=str(dataset.resolve()),
        dataset_manifest_sha256=identity['dataset_manifest_sha256'],
        dataset_inventory_sha256=identity['dataset_inventory_sha256'],
        maximum_layer_nrmse_percent=None,maximum_task_nrmse_percent=None,
        float_reference_recomputed_this_run=False,fresh_float_reference_verified=False,
        reference_error_metrics_reused_under_bit_exact_proof=False,official_precision_verified=False,
        reason='Requires fresh full matrices from this exact first20 sample order; no Q12 SSE/NRMSE reuse')


def audit_precision(ref,batch):
    """Join a pinned fresh software audit to already rechecked own ASIC240.

    A software PASS alone cannot reach this path. The input ZIP, source HEX,
    original sample order, audit code and every task identity are rechecked.
    This joins the new audit's SSE, never B0/Q12 error statistics.
    """
    require(ref is not None, 'Fresh first20 precision reference required')
    source_mode=ref.get('source_mode','original_archive')
    require(source_mode==recovered_precision.SOURCE_MODE,'Unknown precision source mode')
    recovered=True
    audit_tools=recovered_precision
    archive_sha=ref.get('archive_sha256')
    require(re.fullmatch('[a-f0-9]{64}',archive_sha or ''),'Explicit recovered container SHA required')
    require(batch.get('integer_bit_exact') is True and batch.get('tasks')==240 and
        batch.get('outputs')==batch.get('total_outputs')==6082560,'Precision requires own T80 ASIC240 first')
    run=Path(ref['run']).resolve();summary_path=run/'summary.json';identity_path=run/'identity.json'
    require(re.fullmatch('[a-f0-9]{64}',ref['sha256']) and sha(summary_path)==ref['sha256'],
        'Fresh precision summary digest changed')
    result=read(summary_path);identity=read(identity_path)
    require(sha(identity_path)==result['identity_sha256'] and identity.get('status')=='running' and
        all(result.get(key)==value for key,value in identity.items() if key!='status'),
        'Fresh precision identity changed')
    require(result.get('schema')==audit_tools.SCHEMA and result.get('status')=='passed' and
        result.get('fixture') is False and result.get('samples')==20 and result.get('tasks')==240 and
        result.get('outputs')==6082560 and result.get('numeric_format')==data.FORMAT and
        result.get('numeric_format_id')==0x000e0c20 and result.get('layout_id')==0x00100004 and
        result.get('integer_reference_hex_verified') is True and result.get('internal_precision_verified') is True and
        result.get('cpu_executed') is False and result.get('rtl_integer_match_required') is True and
        result.get('official_precision_verified') is False and result.get('integer_mismatches')==0 and
        result.get('hex_byte_mismatches')==0,'Wrong/incomplete fresh T80 precision scope')
    require(result.get('float_archive_sha256')==archive_sha and
        result.get('dataset_inventory_sha256')==data.DATA100_INVENTORY_SHA==batch['dataset_inventory_sha256'] and
        result.get('dataset_manifest_sha256')==batch['dataset_manifest_sha256'] and
        result.get('converter_commit')==data.PR_COMMIT and result.get('converter_sha256')==data.CONVERTER_SHA and
        sha(data.CONVERTER)==data.CONVERTER_SHA and result.get('audit_script_sha256')==sha(audit_tools.__file__) and
        result.get('data_script_sha256')==sha(data.__file__),'Fresh precision source/tool identity differs')
    if recovered:
        require(result.get('source_mode')==source_mode and result.get('original_float_archive_verified') is False and
            result.get('original_float_archive_expected_sha256')==precision_tools.ARCHIVE_SHA and
            result.get('recovered_original_members_verified') is True and
            result.get('numeric_audit_script_sha256')==sha(precision_tools.__file__),
            'Recovered FLOAT provenance/numeric audit identity differs')
    batch_run=Path(batch['batch_run']);batch_identity=read(batch_run/'batch_identity.json')
    require(sha(batch_run/'batch_identity.json')==batch['batch_identity_sha256'] and
        sha(batch_run/'summary.json')==batch['batch_summary_sha256'],'Actual ASIC240 evidence changed after audit')
    dataset=Path(batch['dataset']).resolve();archive=Path(ref.get('archive',result['float_archive'])).resolve()
    require(Path(batch_identity['dataset']).resolve()==dataset and
        sha(dataset/'manifest.json')==batch['dataset_manifest_sha256'] and
        sha(dataset/'SHA256_FILES.json')==data.DATA100_INVENTORY_SHA and
        archive.is_file() and not archive.is_symlink() and sha(archive)==archive_sha,
        'Fresh precision archive/actual dataset changed')
    # A relocated audit copy is allowed only when its entire fixed inventory is
    # identical to the actual CPU source. Never trust a similarly named folder.
    tasks=select_first20(data.index_dataset(dataset))
    require(tasks==batch_identity['task_list'],'Precision and actual ASIC task order differ')
    rows=result['cases'];provenance=result['samples_provenance']
    require(len(rows)==240 and len(provenance)==20 and
        [row['sample'] for row in provenance]==list(range(1,21)),'Incomplete/reordered precision sample set')
    archive_stamp=precision_tools.stamp(archive)
    manifest=recovered_precision.verified_manifest(dataset)
    require(recovered_precision.verify_members(archive,archive_sha,manifest)[:20]==provenance,
            'Recovered original member provenance changed')
    weights_sha=recovered_precision.WEIGHTS_SHA
    require(weights_sha==result['weights_sha256'],'Recovered original weights changed')
    for task,row in zip(tasks,rows):
        require((row['sample'],row['layer'])==(task['sample'],task['layer']) and row['outputs']==25344 and
            row.get('integer_mismatches')==row.get('hex_byte_mismatches')==0 and
            row['source_layout_sha256']==task['source_layout_sha256']==sha(Path(task['source'])/'layout.json'),
            'Fresh precision task differs from actual ASIC coordinates/order')
        source=read(Path(task['source'])/'layout.json')
        require(row['source_hex_sha256']=={name:source['files'][name]['sha256'] for name in data.FILES} and
            row['sample_float_sha256']==provenance[task['sample']-1]['sample_float_sha256'] and
            row['weights_sha256']==weights_sha,'Fresh precision HEX/FLOAT task identities differ')
        require(all(type(row[k]) in (int,float) and math.isfinite(row[k]) and row[k]>=0
            for k in ('sse','reference_energy','nrmse_percent','max_abs_error')) and
            set(row['clipping'])=={'x','w','b'} and all(type(v) is int and v>=0 for v in row['clipping'].values()) and
            type(row['saturated']) is int and 0<=row['saturated']<=25344,'Invalid precision error/count statistics')
        expected=100*math.sqrt(row['sse']/25344)/max(math.sqrt(row['reference_energy']/25344),1e-8)
        require(math.isclose(row['nrmse_percent'],expected,rel_tol=1e-12,abs_tol=1e-13),
            'Fresh task NRMSE differs from SSE/reference energy')
    layers=precision_tools.aggregate(rows)
    clipping={key:sum(row['clipping'][key] for row in rows) for key in ('x','w','b')}
    saturated=sum(row['saturated'] for row in rows)
    require(layers==result['layer_aggregate'] and all(layer['tasks']==20 and layer['within_limit'] for layer in layers) and
        result['precision_limit_percent']==precision_tools.THRESHOLD_PERCENT and clipping==result['clipping'] and
        saturated==result['saturated']==batch['saturated'] and
        result['max_layer_nrmse_percent']==max(row['nrmse_percent'] for row in layers) and
        result['max_task_nrmse_percent']==max(row['nrmse_percent'] for row in rows),
        'Fresh precision aggregate/saturation differs from actual240')
    require(sha(summary_path)==ref['sha256'] and sha(identity_path)==result['identity_sha256'] and
        precision_tools.stamp(archive)==archive_stamp and
        sha(dataset/'manifest.json')==batch['dataset_manifest_sha256'] and
        sha(batch_run/'summary.json')==batch['batch_summary_sha256'],'Evidence changed during precision join')
    return dict(status='own_T80_ASIC240_and_same_data_fresh_FLOAT_precision_verified',
        samples=20,tasks=240,outputs=6082560,total_outputs=6082560,integer_bit_exact=True,
        fresh_float_reference_verified=True,float_reference_recomputed_in_precision_run=True,
        float_reference_recomputed_in_report_export=False,official_precision_verified=False,
        reference_error_metrics_reused_from_B0=False,reference=ref,identity_sha256=result['identity_sha256'],
        float_archive_sha256=archive_sha,source_mode=source_mode,original_float_archive_verified=not recovered,
        recovered_original_members_verified=recovered,dataset_manifest_sha256=batch['dataset_manifest_sha256'],
        dataset_inventory_sha256=data.DATA100_INVENTORY_SHA,batch_identity_sha256=batch['batch_identity_sha256'],
        maximum_layer_nrmse_percent=result['max_layer_nrmse_percent'],maximum_task_nrmse_percent=result['max_task_nrmse_percent'],
        quantization_clipping_count=clipping,saturation_count=saturated,layer_aggregate=layers,
        internal_three_percent_layer_threshold_passed=True,
        scope='First20 precision only; does not approve timing, area, system power or T64')



def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('batch-run','precision-run','output'):p.add_argument('--'+name,required=True,type=Path)
    for name in ('batch-sha256','precision-sha256'):p.add_argument('--'+name,required=True)
    a=p.parse_args()
    require(not a.output.exists(),'Preserve old precision reports')
    state=read(a.batch_run.parent/'state.json')['stages']['t80_batch20']
    require(state['status']=='passed' and state['summary_sha256']==a.batch_sha256==sha(a.batch_run/'summary.json'),
            'T80 first20 batch has not completed with this identity')
    batch=audit_batch(a.batch_run,read(a.batch_run/'summary.json'))
    fresh=read(a.precision_run/'summary.json')
    ref=dict(run=str(a.precision_run.resolve()),sha256=a.precision_sha256,source_mode=recovered_precision.SOURCE_MODE,
             archive_sha256=fresh['float_archive_sha256'])
    result=audit_precision(ref,batch)
    result.update(schema='arch03-t80-first20-precision-join-v1',batch=batch,auditor_sha256=sha(__file__),
                  timing_verified=False,system_power_verified=False)
    save(a.output,result)
    print('T80_FIRST20_PRECISION_JOIN_PASS tasks=240 outputs=6082560',flush=True)

if __name__=='__main__':main()
