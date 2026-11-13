"""Export one frozen N1 configuration as JSON/CSV/Chinese Markdown.

Read-only evidence collection, no EDA and no automatic timing/power approval.
Optional missing evidence stays explicit; a preliminary export is not delivery.
"""
import argparse
import ast
import csv
from decimal import Decimal
import json
import math
from pathlib import Path
import re
import struct
import zipfile
import n1_data as data
import n1_precision as precision_tools
import n1_recovered_precision as recovered_precision
from n1_drc_audit import constraints_inventory
import n1_soc as soc
from n1_bus_metrics import parse_metrics
import n1_gate as gate_tools
from n1_power import extract_reports
from native_saif_activity import audit as activity_audit
from native_saif_replay import verify_inputs
from icb32_power import stream_sha as sha,window_values
from icb32_report import configuration_identity,clock_conditions
from dma16_report import read
from icb32_delivery_sdc import restore_clock

LAYERS=tuple('layer_%02d'%i for i in range(1,13))
MACS=1622016


def require(ok,message):
    if not ok:raise ValueError(message)


def stage(ref,name):
    run=Path(ref['run']).resolve();digest=ref['sha256']
    require(re.fullmatch('[a-f0-9]{64}',digest) and sha(run/'summary.json')==digest,'Stage digest changed '+name)
    report=read(run/'summary.json');state=read(run.parent/'state.json')['stages'][name]
    require(state['status']=='passed' and state['summary_sha256']==digest,'Incomplete stage '+name)
    for file,value in report.get('artifacts',{}).items():
        require(Path(file).name==file and sha(run/file)==value,'Changed artifact '+file)
    return report


def check_case(row,run,name,source=None,mapped=False):
    run=Path(run);task=run/(name+'_data')
    source=Path(source) if source is not None else run.parents[2]/'validated_data'/name
    data.verify_prepared(source,task)
    capture=(gate_tools.check_capture if mapped else data.check_capture)(run/(name+'.csv'),task)
    require(capture==row['capture'] and row['outputs']==25344 and
        row.get('numeric_format')=='0x000e0c20','Actual N1 output receipt differs')
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
    result=(gate_tools.parse_result if mapped else data.parse_result)(text,capture['saturated'],markers)
    require(result==row['result'] and data.read_window(text,result,size)==row['task_window'],'Changed actual CPU log/window')
    cpu=re.findall(r'^ARCH03_ICB32_CPU_CYCLES (\d+)$',text,re.M)
    irq=re.findall(r'^ARCH03_ICB32_IRQ_PROOF enabled=(\d+) external=(\d+) timer=(\d+) wfi=(\d+) events=(\d+) unhandled=(\d+)$',text,re.M)
    q=row['irq_proof']
    require(len(cpu)==len(irq)==1 and int(cpu[0])==row['cpu_cycles'] and
        tuple(map(int,irq[0]))==tuple(int(q[k]) for k in ('enabled','external','timer','wfi','events','unhandled')) and
        q['enabled'] is True and min(q['external'],q['timer'],q['wfi'])>0 and q['events']&1 and not q['unhandled'],
        'Missing/changed actual IRQ/WFI execution')
    if row.get('passive_metrics') is not None:
        require(parse_metrics(text,row['task_window'])==row['passive_metrics'],'Passive metric receipt differs')
    window_values(row['task_window'])


def cases(report,run,mapped=False):
    rows=report['cases']
    require(len(rows)==14 and {r['case'] for r in rows}==set(data.CASES14),'Incomplete N114')
    for row in rows:check_case(row,run,row['case'],mapped=mapped)
    return {row['case']:row for row in rows}


def aggregate_rows(rows):
    require(len(rows)==12 and {r['case'] for r in rows}==set(LAYERS),'Incomplete performance layer set')
    for row in rows:
        require(type(row['cycles']) is int and row['cycles']>0,'Invalid measured task cycles')
        duration=Decimal(row['duration_ns'])
        require(duration.is_finite() and duration>0 and
            abs(duration-Decimal(row['cycles'])*Decimal('6.666666'))<=Decimal('0.000002'),
            'Task duration differs from exact period')
        require((row['raw_energy_j'] is None)==(row['raw_average_power_w'] is None),
            'Partial power/energy pair')
        if row['raw_energy_j'] is not None:
            energy,power=Decimal(row['raw_energy_j']),Decimal(row['raw_average_power_w'])
            require(energy.is_finite() and power.is_finite() and energy>0 and power>0 and
                abs(energy-power*duration*Decimal('1e-9'))<=max(Decimal('1e-30'),abs(energy)*Decimal('1e-12')),
                'Invalid or unequal-window task energy')
    total=sum(r['cycles'] for r in rows)
    duration=sum(Decimal(r['duration_ns']) for r in rows)
    powered=[r for r in rows if r['raw_energy_j'] is not None]
    energy=sum(Decimal(r['raw_energy_j']) for r in powered) if len(powered)==12 else None
    return dict(tasks=12,total_cycles=total,mean_cycles=total/12.,
        nominal_150MHz_tasks_per_second=1800000000./total,
        nominal_150MHz_MMAC_per_second=12.*150*MACS/total,
        goal_6300_met_by_cycles=total*6300<=1800000000,
        power_layers=len(powered),activity_layers=sum(r['activity'] is not None for r in rows),
        raw_energy_per_task_j=str(energy/12) if energy is not None else None,
        raw_time_weighted_power_w=str(energy/(duration*Decimal('1e-9'))) if energy is not None else None,
        raw_arithmetic_layer_mean_power_w=str(sum(Decimal(r['raw_average_power_w']) for r in rows)/12) if energy is not None else None)


def audit_batch(run, report, hardware, firmware_sha):
    """Recheck the new100 integer dataset; never reuse B0 float errors."""
    run=Path(run)
    require(report.get('schema')=='arch03-n1-batch-v4' and report.get('asic_cpu_verified') is True and
        report.get('tasks')==1200 and report.get('checked_outputs')==30412800 and
        report.get('checked_totals')==30412800 and report.get('failed')==0 and
        report.get('shift')==10 and report.get('numeric_format_id')==0x000e0c20,
        'N1 own actual ASIC1200 is incomplete')
    identity=read(run/'batch_identity.json')
    require(sha(run/'batch_identity.json')==report['batch_identity_sha256'] and
        identity['dataset_inventory_sha256']==data.DATA100_INVENTORY_SHA and
        identity['firmware_manifest_sha256']==firmware_sha and configuration_identity(run)==hardware,
        'N1 batch data/hardware/firmware identity changed')
    contract=read(run/'n1_build_contract.json');soc.verify_frozen(contract)
    require(sha(run/'n1_build_contract.json')==identity['build_contract_sha256'], 'N1 batch build changed')
    dataset=Path(identity['dataset']);tasks=data.index_dataset(dataset)
    require(sha(dataset/'manifest.json')==identity['dataset_manifest_sha256'] and
        tasks==identity['task_list'] and len(report['cases'])==1200,'New100 task identities changed')
    saturations=0
    for task,entry in zip(tasks,report['cases']):
        receipt=run/'cases'/task['key']/'receipt.json'
        require(entry['key']==task['key'] and (run/entry['receipt']).resolve()==receipt.resolve() and
            sha(receipt)==entry['receipt_sha256'] and entry['outputs']==entry['total_outputs']==25344,
            'N1 batch task receipt changed')
        row=read(receipt)
        require((row['sample'],row['layer'],row['key'])==(task['sample'],task['layer'],task['key']) and
            row['asic_cpu_verified'] is True and row['source_layout_sha256']==task['source_layout_sha256'] and
            row['batch_identity_sha256']==report['batch_identity_sha256'], 'Wrong N1 task/CPU identity')
        # check_case below is deliberately the strict five-column RTL path.
        check_case(row,receipt.parent,'task',task['source'])
        require(entry['capture_sha256']==row['capture']['capture_sha256'] and
            entry['cycles']==row['task_window']['cycles'],'N1 batch aggregate differs from real task')
        saturations+=row['capture']['saturated']
    return dict(status='new100_integer_bit_exact_float_precision_pending',samples=100,tasks=1200,
        outputs=30412800,total_outputs=30412800,integer_bit_exact=True,saturated=saturations,
        batch_run=str(run.resolve()),batch_identity_sha256=report['batch_identity_sha256'],
        batch_summary_sha256=sha(run/'summary.json'),dataset=str(dataset.resolve()),
        dataset_manifest_sha256=identity['dataset_manifest_sha256'],
        dataset_inventory_sha256=identity['dataset_inventory_sha256'],
        maximum_layer_nrmse_percent=None,maximum_task_nrmse_percent=None,
        float_reference_recomputed_this_run=False,fresh_float_reference_verified=False,
        reference_error_metrics_reused_under_bit_exact_proof=False,official_precision_verified=False,
        reason='Requires fresh full matrices from this exact new100 sample order; no Q12 SSE/NRMSE reuse')


def precision_pending(batch):
    return dict(status='same_data_float100_audit_not_completed',integer_bit_exact=batch.get('tasks')==1200,
        fresh_float_reference_verified=False,official_precision_verified=False,
        maximum_layer_nrmse_percent=None,maximum_task_nrmse_percent=None,
        quantization_clipping_count=None,saturation_count=batch.get('saturated'),
        reason='Full100 fresh FLOAT audit and the same own ASIC1200 must both be present; fixed12 is a separate scope')


def audit_precision(ref,batch):
    """Join a pinned fresh software audit to already rechecked own ASIC1200.

    A software PASS alone cannot reach this path. The input ZIP, source HEX,
    original sample order, audit code and every task identity are rechecked.
    This joins the new audit's SSE, never B0/Q12 error statistics.
    """
    if ref is None:return precision_pending(batch)
    source_mode=ref.get('source_mode','original_archive')
    require(source_mode in ('original_archive',recovered_precision.SOURCE_MODE),'Unknown precision source mode')
    recovered=source_mode==recovered_precision.SOURCE_MODE
    audit_tools=recovered_precision if recovered else precision_tools
    archive_sha=ref.get('archive_sha256') if recovered else precision_tools.ARCHIVE_SHA
    require(re.fullmatch('[a-f0-9]{64}',archive_sha or ''),'Explicit recovered container SHA required')
    require(batch.get('integer_bit_exact') is True and batch.get('tasks')==1200 and
        batch.get('outputs')==batch.get('total_outputs')==30412800,'Precision requires own N1 ASIC1200 first')
    run=Path(ref['run']).resolve();summary_path=run/'summary.json';identity_path=run/'identity.json'
    require(re.fullmatch('[a-f0-9]{64}',ref['sha256']) and sha(summary_path)==ref['sha256'],
        'Fresh precision summary digest changed')
    result=read(summary_path);identity=read(identity_path)
    require(sha(identity_path)==result['identity_sha256'] and identity.get('status')=='running' and
        all(result.get(key)==value for key,value in identity.items() if key!='status'),
        'Fresh precision identity changed')
    require(result.get('schema')==audit_tools.SCHEMA and result.get('status')=='passed' and
        result.get('fixture') is False and result.get('samples')==100 and result.get('tasks')==1200 and
        result.get('outputs')==30412800 and result.get('numeric_format')==data.FORMAT and
        result.get('numeric_format_id')==0x000e0c20 and result.get('layout_id')==0x00100004 and
        result.get('integer_reference_hex_verified') is True and result.get('internal_precision_verified') is True and
        result.get('cpu_executed') is False and result.get('rtl_integer_match_required') is True and
        result.get('official_precision_verified') is False and result.get('integer_mismatches')==0 and
        result.get('hex_byte_mismatches')==0,'Wrong/incomplete fresh N1 precision scope')
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
        sha(batch_run/'summary.json')==batch['batch_summary_sha256'],'Actual ASIC1200 evidence changed after audit')
    dataset=Path(batch['dataset']).resolve();archive=Path(ref.get('archive',result['float_archive'])).resolve()
    require(Path(batch_identity['dataset']).resolve()==dataset and
        sha(dataset/'manifest.json')==batch['dataset_manifest_sha256'] and
        sha(dataset/'SHA256_FILES.json')==data.DATA100_INVENTORY_SHA and
        archive.is_file() and not archive.is_symlink() and sha(archive)==archive_sha,
        'Fresh precision archive/actual dataset changed')
    # A relocated audit copy is allowed only when its entire fixed inventory is
    # identical to the actual CPU source. Never trust a similarly named folder.
    tasks=data.index_dataset(dataset)
    require(tasks==batch_identity['task_list'],'Precision and actual ASIC task order differ')
    rows=result['cases'];provenance=result['samples_provenance']
    require(len(rows)==1200 and len(provenance)==100 and
        [row['sample'] for row in provenance]==list(range(1,101)),'Incomplete/reordered precision sample set')
    archive_stamp=precision_tools.stamp(archive)
    if recovered:
        manifest=recovered_precision.verified_manifest(dataset)
        require(recovered_precision.verify_members(archive,archive_sha,manifest)==provenance,
                'Recovered original member provenance changed')
        weights_sha=recovered_precision.WEIGHTS_SHA
        require(weights_sha==result['weights_sha256'],'Recovered original weights changed')
    else:
        with zipfile.ZipFile(str(archive)) as zipped:
            names=zipped.namelist()
            require(len(names)==len(set(names)),'Ambiguous precision archive members')
            weights_sha=precision_tools.digest_bytes(zipped.read(precision_tools.ARCHIVE_ROOT+'shared_weights.npz'))
            require(weights_sha==result['weights_sha256'],'Fresh precision weights changed')
            for sample in provenance:
                prefix=precision_tools.ARCHIVE_ROOT+'sample_%03d/'%sample['sample']
                source_raw=zipped.read(prefix+'source.json');source=json.loads(source_raw.decode('utf-8-sig'))
                require(precision_tools.digest_bytes(zipped.read(prefix+'float_tensors.npz'))==sample['sample_float_sha256'] and
                    precision_tools.digest_bytes(source_raw)==sample['source_json_sha256'] and
                    all(sample[key]==source[key] for key in ('wav','split','wav_sha256')),
                    'Fresh precision original sample provenance changed')
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
    require(layers==result['layer_aggregate'] and all(layer['tasks']==100 and layer['within_limit'] for layer in layers) and
        result['precision_limit_percent']==precision_tools.THRESHOLD_PERCENT and clipping==result['clipping'] and
        saturated==result['saturated']==batch['saturated'] and
        result['max_layer_nrmse_percent']==max(row['nrmse_percent'] for row in layers) and
        result['max_task_nrmse_percent']==max(row['nrmse_percent'] for row in rows),
        'Fresh precision aggregate/saturation differs from actual1200')
    require(sha(summary_path)==ref['sha256'] and sha(identity_path)==result['identity_sha256'] and
        precision_tools.stamp(archive)==archive_stamp and
        sha(dataset/'manifest.json')==batch['dataset_manifest_sha256'] and
        sha(batch_run/'summary.json')==batch['batch_summary_sha256'],'Evidence changed during precision join')
    return dict(status='own_N1_ASIC1200_and_same_data_fresh_FLOAT_precision_verified',
        samples=100,tasks=1200,outputs=30412800,total_outputs=30412800,integer_bit_exact=True,
        fresh_float_reference_verified=True,float_reference_recomputed_in_precision_run=True,
        float_reference_recomputed_in_report_export=False,official_precision_verified=False,
        reference_error_metrics_reused_from_B0=False,reference=ref,identity_sha256=result['identity_sha256'],
        float_archive_sha256=archive_sha,source_mode=source_mode,original_float_archive_verified=not recovered,
        recovered_original_members_verified=recovered,dataset_manifest_sha256=batch['dataset_manifest_sha256'],
        dataset_inventory_sha256=data.DATA100_INVENTORY_SHA,batch_identity_sha256=batch['batch_identity_sha256'],
        maximum_layer_nrmse_percent=result['max_layer_nrmse_percent'],maximum_task_nrmse_percent=result['max_task_nrmse_percent'],
        quantization_clipping_count=clipping,saturation_count=saturated,layer_aggregate=layers,
        internal_three_percent_layer_threshold_passed=True,
        scope='New100 precision only; does not approve timing, area, system power or N2')


def read_float_npz(path,name,shape):
    """Small strict standard-library reader; report export does not need NumPy."""
    with zipfile.ZipFile(str(path)) as zipped:
        require(len(zipped.namelist())==len(set(zipped.namelist())),'Duplicate fixed12 NPZ member')
        raw=zipped.read(name+'.npy')
    require(raw[:6]==b'\x93NUMPY' and raw[6:8] in (b'\x01\x00',b'\x02\x00'),'Unsupported fixed12 NPY format')
    length_size=2 if raw[6]==1 else 4;start=8+length_size
    size=int.from_bytes(raw[8:start],'little')
    require(0<size<=4096 and len(raw)>=start+size,'Invalid fixed12 NPY header')
    header=ast.literal_eval(raw[start:start+size].decode('latin1'))
    require(header.get('fortran_order') is False and header.get('shape')==shape and
        header.get('descr') in ('<f4','<f8','>f4','>f8'),'Wrong fixed12 float shape/dtype/order')
    width=int(header['descr'][2:]);count=math.prod(shape) if hasattr(math,'prod') else __import__('functools').reduce(lambda a,b:a*b,shape,1)
    payload=raw[start+size:]
    require(len(payload)==count*width,'Truncated fixed12 NPY payload')
    values=struct.unpack(header['descr'][0]+str(count)+('f' if width==4 else 'd'),payload)
    require(all(math.isfinite(value) for value in values),'Nonfinite fixed12 FLOAT')
    return values


def fixed12_precision(run,asic_cases,source_root=None,float_root=None):
    """Independently retain the fixed B0-comparison input proof, never full100."""
    bundle=Path(run).parents[2]
    source_root=Path(source_root) if source_root is not None else bundle/'validated_data'
    float_root=Path(float_root) if float_root is not None else bundle/'architectures/arch01_serial_mac/v1.3.0/KWT1/model_data/outputs/real_sample_001'
    missing=[name for name in LAYERS if not (source_root/name/'conversion_audit.json').is_file() or
             not (float_root/name/'float_tensors.npz').is_file()]
    if missing:return dict(status='fixed12_float_evidence_not_available',tasks=12,verified=False,missing=missing,
                           scope='Separate fixed performance samples; cannot satisfy full100 precision')
    require(sha(data.CONVERTER)==data.CONVERTER_SHA,'Fixed12 converter identity changed')
    rows=[]
    for index,name in enumerate(LAYERS,1):
        folder=source_root/name;original=float_root/name/'float_tensors.npz';audit=read(folder/'conversion_audit.json')
        require(audit.get('status')=='passed' and audit.get('fresh_float_reference') is True and
            audit.get('layer')==index and audit.get('outputs')==25344 and audit.get('mismatches')==0 and
            audit['source_float_sha256']==sha(original),'Fixed12 fresh conversion identity changed')
        meta,words,raw_result,saturation=data.source_case(folder);x,w,bias=data.decode_group8(words)
        clipping={}
        for key,field,shape,bits,fraction,actual in (
            ('x','X',(99,64),14,10,[v for row in x for v in row]),
            ('w','W',(64,256),12,12,[v for row in w for v in row]),('b','b',(256,),32,22,bias)):
            values=read_float_npz(original,field,shape);low,high=-(1<<(bits-1)),(1<<(bits-1))-1
            converted=[];count=0
            for value in values:
                scaled=max(low-1,min(high+1,math.ldexp(value,fraction)))
                rounded=int(math.copysign(math.floor(abs(scaled)+.5),scaled))
                encoded=max(low,min(high,rounded));count+=encoded!=rounded;converted.append(encoded)
            require(converted==actual,'Fixed12 fresh quantization coordinates differ: '+key)
            clipping[key]=count
        y=read_float_npz(original,'Y_float',(99,256))
        decoded=[value-65536 if value&32768 else value for value in raw_result]
        sse=math.fsum((value/4096.-reference)**2 for value,reference in zip(decoded,y))
        energy=math.fsum(value*value for value in y)
        error=100*math.sqrt(sse/25344)/max(math.sqrt(energy/25344),1e-8)
        require(clipping==audit['clipping'] and sum(saturation)==audit['saturated']==asic_cases[name]['capture']['saturated'] and
            math.isclose(sse,audit['sse'],rel_tol=1e-11,abs_tol=1e-15) and
            math.isclose(energy,audit['reference_energy'],rel_tol=1e-11,abs_tol=1e-15) and
            math.isclose(error,audit['error']['nrmse_percent'],rel_tol=1e-11,abs_tol=1e-13),
            'Fixed12 fresh error or actual ASIC saturation differs')
        rows.append(dict(case=name,outputs=25344,sse=sse,reference_energy=energy,nrmse_percent=error,
            clipping=clipping,saturated=sum(saturation),float_sha256=audit['source_float_sha256'],
            conversion_audit_sha256=sha(folder/'conversion_audit.json'),source_layout_sha256=sha(folder/'layout.json'),
            source_hex_sha256={key:meta['files'][key]['sha256'] for key in data.FILES}))
    return dict(status='fixed12_fresh_quantization_and_error_rechecked',tasks=12,outputs=304128,verified=True,
        maximum_task_nrmse_percent=max(row['nrmse_percent'] for row in rows),cases=rows,
        internal_three_percent_task_threshold_passed=all(row['nrmse_percent']<=3. for row in rows),
        official_precision_verified=False,full100_precision_satisfied=False,
        scope='Same original fixed B0 performance FLOAT inputs, independent of new100 acceptance')


def frozen_drc_inventory(synthesis,run):
    path=Path(run)/'constraints.rpt'
    require(synthesis.get('artifacts',{}).get('constraints.rpt')==sha(path),
        'Frozen constraint report identity changed')
    result=constraints_inventory(path.read_text())
    result.update(report_sha256=synthesis['artifacts']['constraints.rpt'],source=str(path),
        strict_timing_verified=False,scope='Frozen report inventory; detailed scoped STA/DRC review remains separate')
    return result


def selection(aggregate, area, baseline_ref=None):
    """Show numerical limits without treating unreviewed power as approval."""
    bound=Decimal(str(area['conservative_budget_mm2']))
    require(bound.is_finite() and bound>=0 and area['units']=='um^2', 'Invalid N1 area units/value')
    result=dict(project_area_limit_mm2='1.20',conservative_budget_mm2=str(bound),
        numerical_area_limit_met=bound<=Decimal('1.20'),area_attribution_reviewed=False,
        baseline=None,raw_energy_ratio_to_B0=None,raw_average_power_ratio_to_B0=None,
        raw_energy_nonincrease=None,raw_average_power_increase_at_most_10percent=None,
        relative_power_admission_passed=False,eligible_for_next_hardware_stage=False,
        reason='Raw numerical limits do not establish precision/timing/area/unknown-activity acceptance')
    if baseline_ref is None:return result
    path=Path(baseline_ref['report']).resolve()
    require(re.fullmatch('[a-f0-9]{64}',baseline_ref['sha256']) and sha(path)==baseline_ref['sha256'],
        'B0 comparison report digest changed')
    baseline=read(path)
    require(baseline.get('schema')=='systolic-b-evidence-export-v1' and
        baseline.get('aggregate',{}).get('tasks')==12, 'Need the frozen B0 evidence export')
    result['baseline']=dict(report=str(path),sha256=baseline_ref['sha256'],
        system_power_verified=baseline.get('verification',{}).get('system_power_verified') is True,
        scope='reported_numbers_only_not_transferred_acceptance')
    a,b=aggregate,baseline['aggregate']
    if a['power_layers']==b.get('power_layers')==12:
        ae,be=Decimal(a['raw_energy_per_task_j']),Decimal(b['raw_energy_per_task_j'])
        ap,bp=Decimal(a['raw_time_weighted_power_w']),Decimal(b['raw_time_weighted_power_w'])
        require(all(v.is_finite() and v>0 for v in (ae,be,ap,bp)), 'Invalid complete power comparison')
        result.update(raw_energy_ratio_to_B0=str(ae/be),raw_average_power_ratio_to_B0=str(ap/bp),
            raw_energy_nonincrease=ae<=be,raw_average_power_increase_at_most_10percent=ap<=bp*Decimal('1.10'))
    return result


def build(request):
    require(request['schema']=='arch03-n1-report-request-v1','Wrong N1 report schema')
    refs={key:request[key] for key in ('asic','synthesis','gate')}
    arun,srun,grun=[Path(refs[key]['run']).resolve() for key in ('asic','synthesis','gate')]
    a,s,g=[stage(refs[key],name) for key,name in
        (('asic','n1_soc'),('synthesis','n1_synth'),('gate','n1_gate'))]
    require(a['asic_cpu_verified'] is True and a['cpu_executed'] is True and a['global_FPGA_defined'] is False and
        g['gate_simulation_verified'] is True and g['sdf_annotated'] is False and
        g['cpu_executed'] is True and g['global_FPGA_defined'] is False and s['synthesis_completed'] is True and
        g['scope']=='n1_whole_soc_mapped_functional_without_SDF' and
        g.get('numeric_format')=='0x000e0c20' and g.get('internal_total_observable') is False and
        s['scope']=='n1_whole_soc_task_mode_preliminary_synthesis','Wrong N1 hardware execution scope')
    require(g['synthesis_summary_sha256']==refs['synthesis']['sha256'] and
        g['firmware_sha256']==a['compile_receipt']['firmware_manifest_sha256'],'Mixed N1 synthesis/firmware')
    require(sha(arun/'source_inputs.json')==a['compile_receipt']['source_inputs_sha256'] and
        read(arun/'compile_receipt.json')==a['compile_receipt'],'ASIC compile receipt changed')
    soc.verify_frozen(read(arun/'n1_build_contract.json'))
    require(sha(arun/'n1_build_contract.json')==a['build_contract_sha256'],'ASIC build changed')
    hardware=configuration_identity(arun)
    require(configuration_identity(srun)==hardware and
        a['compile_receipt']['platform_baseline_sha256']==s['link_report']['platform_baseline_sha256'],
        'ASIC and synthesis production hardware differ')
    require(sha(grun/'source_inputs.json')==g['source_inputs_sha256'],'Gate provenance changed')
    verify_inputs(read(grun/'source_inputs.json'))
    require(Decimal(str(s['metrics']['period_ns']))==Decimal('6.666666') and
        int(s['metrics']['RAMSP128X16'])==92 and int(s['metrics']['RAMSP4096X16'])==128,'Wrong N1 clock/macro configuration')
    left,right=cases(a,arun),cases(g,grun,mapped=True)
    act={};activity_ref=request.get('activity')
    if activity_ref:
        activity=stage(activity_ref,'n1_saif')
        require(activity.get('schema')=='arch03-n1-native-saif-v1' and
            activity.get('numeric_format')=='0x000e0c20' and activity.get('layout_id')==0x00100004 and
            activity.get('internal_total_observable') is False and
            activity['status']=='N1_native_saif_function_and_complete_windows_passed' and
            activity['gate_summary_sha256']==refs['gate']['sha256'] and
            activity['synthesis_summary_sha256']==refs['synthesis']['sha256'] and
            activity['firmware_sha256']==g['firmware_sha256'],'Mixed N1 native activity')
        act={r['case']:r for r in activity['cases']}
        require(set(act)==set(LAYERS) and len(activity['cases'])==12,'Incomplete N1 activity12')
        for name,row in act.items():
            require(row['task_window']==right[name]['task_window'] and
                row['layout_sha256']==right[name]['layout_sha256'],'Activity layout/window differs')
            actual=activity_audit(Path(activity_ref['run'])/row['activity']['file'],row['task_window'])
            require(actual==row['activity'],'Activity audit differs')
    powers={}
    for ref in request.get('power',[]):
        raw=stage(ref,'n1_power');name=raw['case']
        require(raw.get('schema')=='arch03-n1-native-saif-power-v1' and
            raw.get('numeric_format')=='0x000e0c20' and raw.get('layout_id')==0x00100004 and
            raw.get('scope')=='n1_whole_soc_native_saif_pre_layout_power' and
            raw.get('status')=='reports_and_numbers_ready_unknown_impact_review_required' and
            name in act and name not in powers and
            raw['activity_summary_sha256']==activity_ref['sha256'] and
            raw['gate_summary_sha256']==refs['gate']['sha256'] and
            raw['synthesis_summary_sha256']==refs['synthesis']['sha256'] and
            raw['firmware_sha256']==g['firmware_sha256'] and
            raw['layout_sha256']==right[name]['layout_sha256'] and
            raw['task_window']==act[name]['task_window'] and raw['activity']==act[name]['activity'],
            'Mixed N1 power/window provenance')
        power_run=Path(ref['run']);clock=raw['power_clock']
        precise,_=restore_clock((srun/'mapped.sdc').read_bytes().decode('ascii'),s['metrics']['period_ns'])
        require((power_run/'mapped.precise.sdc').read_bytes()==precise.encode('ascii') and
            sha(power_run/'mapped.precise.sdc')==clock['imported_sdc_sha256'] and
            clock['original_sdc_sha256']==sha(srun/'mapped.sdc') and
            Decimal(clock['measured']['hf_period_ns'])==Decimal('6.666666') and
            Decimal(clock['measured']['lf_period_ns'])==Decimal('66') and
            clock['original_sdc_modified'] is False and clock['other_constraints_unchanged'] is True,
            'Power did not import the frozen exact clock')
        numbers=extract_reports(Path(ref['run']))
        duration=window_values(raw['task_window'])[2]
        numbers.update(duration_ns=duration,average_power_w=numbers['reported_power_w']['total'])
        numbers['energy_j']=str(Decimal(numbers['average_power_w'])*Decimal(duration)*Decimal('1e-9'))
        require(numbers==raw['numbers'] and read(Path(ref['run'])/'numbers.json')==numbers,'Changed N1 power extraction')
        powers[name]=dict(reference=ref,raw=raw,numbers=numbers)
    rows=[]
    for name in LAYERS:
        x,y=left[name],right[name]
        require(x['capture']['outputs']==y['capture']['outputs']==25344 and
            x['capture']['saturated']==y['capture']['saturated'] and
            x['capture']['mismatches']==y['capture']['mismatches']==0 and
            x['capture']['total_checked'] is True and y['capture']['total_checked'] is False and
            x['layout_sha256']==y['layout_sha256'] and
            x['codec_sha256']==y['codec_sha256'] and x['task_window']['cycles']==y['task_window']['cycles'],
            'ASIC/gate results, layout or complete cycles differ')
        w=y['task_window'];duration=window_values(w)[2];n=powers[name]['numbers'] if name in powers else None
        row=dict(case=name,cycles=w['cycles'],duration_ns=duration,outputs=25344,
            total_outputs=25344,asic_total_checked=True,gate_total_checked=False,
            asic_capture_sha256=x['capture']['capture_sha256'],gate_capture_sha256=y['capture']['capture_sha256'],
            encoded_bytes=w['encoded_bytes'],transfer_transactions=w['transfer_transactions'],
            transfer_bytes=w['transfer_bytes'],nominal_150MHz_tasks_per_second=150000000./w['cycles'],
            nominal_150MHz_MMAC_per_second=150.*MACS/w['cycles'],
            mac_utilization=MACS/(80.*w['cycles']),accepted_transactions_per_cycle=w['transfer_transactions']/w['cycles'],
            passive_metrics=x.get('passive_metrics'),layout_sha256=y['layout_sha256'],codec_sha256=y['codec_sha256'],
            raw_average_power_w=n['average_power_w'] if n else None,
            raw_dynamic_w=n['derived_dynamic_w'] if n else None,
            raw_leakage_w=n['reported_power_w']['leakage'] if n else None,
            raw_energy_j=n['energy_j'] if n else None,power=n,
            activity=act[name]['activity'] if name in act else None,
            system_power_verified=False)
        rows.append(row)
    aggregate=aggregate_rows(rows)
    conditions=clock_conditions(s,srun,False)
    conditions.update(power_imported_original_sdc=False,power_imported_precise_sdc=bool(powers),
        power_period_ns='6.666666' if powers else None,
        note='N1 PT imports a separate exact 6.666666 ns SDC; original DC export is preserved. Comparison conditions and complete windows remain explicit.')
    batch=dict(status='not_run',tasks=0,outputs=0,official_precision_verified=False)
    if request.get('batch'):
        ref=request['batch'];b=stage(ref,'n1_batch');brun=Path(ref['run'])
        require(configuration_identity(brun)==hardware and
            read(brun/'batch_identity.json')['firmware_manifest_sha256']==g['firmware_sha256'],
            'Final1200 belongs to different N1 hardware/firmware')
        batch=audit_batch(brun,b,hardware,g['firmware_sha256'])
        batch['mean_cycles']=b['mean_task_cycles'];batch['host_elapsed_seconds']=b['host_elapsed_seconds']
    precision=audit_precision(request.get('precision'),batch)
    fixed_precision=fixed12_precision(arun,left)
    if precision['fresh_float_reference_verified']:
        batch.update(status='new100_integer_and_same_data_float_precision_verified',
            fresh_float_reference_verified=True,maximum_layer_nrmse_percent=precision['maximum_layer_nrmse_percent'],
            maximum_task_nrmse_percent=precision['maximum_task_nrmse_percent'],
            reason='Fresh N1 precision joined to this actual ASIC1200; official600 remains unverified')
    drc=frozen_drc_inventory(s,srun)
    unverified=['Independent scoped timing/area review is separate from numerical report collection',
        'Unknown activity/model influence and pre-layout estimation limits','Official random600 and physical signoff']
    if not precision['fresh_float_reference_verified']:
        unverified.append('Fresh same-sample float100 recomputation; no old Q12 SSE/NRMSE reuse')
    return dict(schema='arch03-n1-evidence-export-v1',status='evidence_exported_stage_unaccepted',
        stage='N1',numeric_format='0x000e0c20',layout_id=0x00100004,shift=10,row_lanes=5,
        gate_internal_total_observable=False,
        selection=selection(aggregate,s['area_summary'],request.get('baseline')),
        precision=precision,fixed12_precision=fixed_precision,
        stage_handoff=dict(next_stage='N2',allowed=False,reason='Numerical collection does not replace independent precision, timing, area and system-power review'),
        references=refs,activity_reference=activity_ref,power_references=request.get('power',[]),
        batch_reference=request.get('batch'),precision_reference=request.get('precision'),
        production_hardware=hardware,firmware_sha256=g['firmware_sha256'],netlist_sha256=s['artifacts']['mapped.v'],
        libraries_sha256=s['link_report']['library_inputs'],area=s['area_summary'],area_basis=s['area_basis'],
        timing_metrics=s['metrics'],drc_inventory=drc,conditions=conditions,
        cases=rows,aggregate=aggregate,batch=batch,history=request.get('history',[]),
        verification=dict(asic14=True,gate14_without_SDF=True,final1200=batch.get('tasks')==1200,
            activity12=len(act)==12,power12_numbers=len(powers)==12,
            internal100_precision_verified=precision['fresh_float_reference_verified'],
            fixed12_precision_verified=fixed_precision['verified'],
            task_mode_timing_verified=False,project_area_reviewed=False,system_power_verified=False,
            official_precision_verified=False,physical_signoff=False),
        unverified=unverified,exporter_sha256=sha(__file__),
        precision_auditor_sha256=sha(precision_tools.__file__),drc_parser_sha256=sha(__import__('n1_drc_audit').__file__))


def write(report,output):
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    data.save(output/'report.json',report)
    fields=('case cycles encoded_bytes transfer_bytes transfer_transactions nominal_150MHz_tasks_per_second '
        'nominal_150MHz_MMAC_per_second mac_utilization accepted_transactions_per_cycle '
        'raw_average_power_w raw_dynamic_w raw_leakage_w raw_energy_j layout_sha256 codec_sha256').split()
    for name,rows,columns in [('tasks.csv',report['cases'],fields),('summary.csv',[report['aggregate']],list(report['aggregate']))]:
        with (output/name).open('x',encoding='utf-8-sig',newline='') as out:
            writer=csv.DictWriter(out,columns,extrasaction='ignore');writer.writeheader();writer.writerows(rows)
    a=report['aggregate'];b=report['batch']
    precision=report['precision']
    layer_error=precision['maximum_layer_nrmse_percent'];task_error=precision['maximum_task_nrmse_percent']
    lines=['# N1缩位5×16脉动配置证据报告','',
        '本报告复核ASIC/E203的total33/result/sat及无SDF门级result/sat。门级不观察内部total，不用参考值伪造第五列。功耗为布局前估算。独立时序、面积归属和未知活动影响审核另行记录；本导出不自动授予验收。','',
        'SS、0.99V、125°C；DC与任务周期6.666666ns。计时从首源VALID至最终写ACK并证明排空，没有省略真实共享SRAM写入。','',
        '12层平均 %.6f 周期，按150MHz折算 %.6f task/s；6300争取目标：%s。'%
            (a['mean_cycles'],a['nominal_150MHz_tasks_per_second'],'达到' if a['goal_6300_met_by_cycles'] else '未达到'),'',
        '| 层 | 周期 | 编码字节 | 平均功耗W | 能耗J |','|---|---:|---:|---:|---:|']
    for r in report['cases']:
        lines.append('| %s | %d | %d | %s | %s |'%(r['case'],r['cycles'],r['encoded_bytes'],
            r['raw_average_power_w'] if r['raw_average_power_w'] is not None else '未验证',
            r['raw_energy_j'] if r['raw_energy_j'] is not None else '未验证'))
    lines+=['','完整活动%d/12，功耗数值%d/12。时间加权平均功耗W：%s；平均J/task：%s。'%
        (a['activity_layers'],a['power_layers'],a['raw_time_weighted_power_w'],a['raw_energy_per_task_j']),
        '内部最终批量：%s，%d任务、%d输出；不代表官方600样本精度验收。'%(b['status'],b['tasks'],b['outputs']),
        '同批100条浮点精度：%s；最大逐层NRMSE：%s，最大逐任务NRMSE：%s。'%
            (precision['status'],'未验证' if layer_error is None else '%.10f%%'%layer_error,
             '未验证' if task_error is None else '%.10f%%'%task_error),
        '浮点来源模式：%s；原ZIP容器验证：%s；恢复的原NPZ成员核验：%s。'%
            (precision.get('source_mode','未验证'),precision.get('original_float_archive_verified',False),
             precision.get('recovered_original_members_verified',False)),
        '固定12性能任务的独立浮点核验：%s；不能替代完整100条。'%report['fixed12_precision']['status'],
        '冻结综合约束报告：违例记录%d，解析完整=%s，明确无违例标记=%s；严格时序审核仍独立。'%
            (report['drc_inventory']['violation_record_count'],report['drc_inventory']['extraction_complete'],
             report['drc_inventory']['explicit_no_violations']),
        '源码、固件、布局、数据、库、网表及活动身份、模块功耗、SRAM、未知驻留及全部计数见JSON。重叠等待不相加作为总周期，缺失功耗不作零。','',
        '项目面积上限1.20mm²；全部PPA来自N1自身配置。B0独立保留，不转移PASS。缺同批100样本浮点精度或未知活动审核时，N1未验收，不进入N2。','',
        '历史失败/停止路径：']
    lines+=['- '+json.dumps(item,ensure_ascii=False) for item in report['history']]
    (output/'report_zh.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
    data.save(output/'receipt.json',dict(schema='arch03-n1-export-receipt-v1',
        artifacts={p.name:sha(p) for p in output.iterdir() if p.is_file()}))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--request',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();digest=sha(a.request);result=build(read(a.request))
    require(sha(a.request)==digest,'Request changed during audit');result['request_sha256']=digest
    write(result,a.output);print('N1_EVIDENCE_EXPORTED stage_accepted=false review_required=true',a.output)
