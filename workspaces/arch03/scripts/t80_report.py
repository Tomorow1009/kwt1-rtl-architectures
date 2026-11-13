"""Export one frozen T80 configuration as JSON/CSV/Chinese Markdown.

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
import t80_precision as recovered_precision
from t80_drc_audit import constraints_inventory
import t80_soc as soc
from t80_bus_metrics import parse_metrics
import t80_gate as gate_tools
from t80_power import extract_reports
from native_saif_activity import audit as activity_audit
from native_saif_replay import verify_inputs
from icb32_power import stream_sha as sha
from t80_window import window_values
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


from t80_precision_join import check_case


def cases(report,run,mapped=False):
    rows=report['cases']
    require(len(rows)==14 and {r['case'] for r in rows}==set(data.CASES14),'Incomplete T8014')
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
        power_layers=len(powered),activity_layers=sum(r['activity'] is not None for r in rows),
        raw_energy_per_task_j=str(energy/12) if energy is not None else None,
        raw_time_weighted_power_w=str(energy/(duration*Decimal('1e-9'))) if energy is not None else None,
        raw_arithmetic_layer_mean_power_w=str(sum(Decimal(r['raw_average_power_w']) for r in rows)/12) if energy is not None else None)


def audit_batch(run, report, hardware, firmware_sha):
    from t80_precision_join import audit_batch as collect
    identity=read(Path(run)/'batch_identity.json')
    require(configuration_identity(run)==hardware and identity['firmware_manifest_sha256']==firmware_sha,
            'T80 first20 evidence belongs to different hardware or firmware')
    return collect(run,report)


def audit_precision(ref,batch):
    if ref is None:
        return dict(status='first20_float_audit_not_completed',fresh_float_reference_verified=False,
            official_precision_verified=False,maximum_layer_nrmse_percent=None,maximum_task_nrmse_percent=None)
    from t80_precision_join import audit_precision as collect
    return collect(ref,batch)


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
    """Independently retain the fixed B0-comparison input proof, never first20."""
    bundle=Path(run).parents[2]
    source_root=Path(source_root) if source_root is not None else bundle/'validated_data'
    float_root=Path(float_root) if float_root is not None else bundle/'architectures/arch01_serial_mac/v1.3.0/KWT1/model_data/outputs/real_sample_001'
    missing=[name for name in LAYERS if not (source_root/name/'conversion_audit.json').is_file() or
             not (float_root/name/'float_tensors.npz').is_file()]
    if missing:return dict(status='fixed12_float_evidence_not_available',tasks=12,verified=False,missing=missing,
                           scope='Separate fixed performance samples; cannot satisfy first20 precision')
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
        official_precision_verified=False,first20_precision_satisfied=False,
        scope='Same original fixed B0 performance FLOAT inputs, independent of first20 acceptance')


def frozen_drc_inventory(synthesis,run):
    path=Path(run)/'constraints.rpt'
    require(synthesis.get('artifacts',{}).get('constraints.rpt')==sha(path),
        'Frozen constraint report identity changed')
    result=constraints_inventory(path.read_text())
    result.update(report_sha256=synthesis['artifacts']['constraints.rpt'],source=str(path),
        strict_timing_verified=False,scope='Frozen report inventory; detailed scoped STA/DRC review remains separate')
    return result


def selection(aggregate, area):
    bound=Decimal(str(area['conservative_budget_mm2']))
    return dict(conservative_area_mm2=str(bound),project_limit_mm2='1.20',
        numerical_area_limit_met=bound<=Decimal('1.20'),area_attribution_reviewed=False,
        eligible_for_next_hardware_stage=False,
        reason='Current T80/T64/G64 plan: report measured throughput and energy; independent acceptance remains required')


def build(request):
    require(request['schema']=='arch03-t80-report-request-v1','Wrong T80 report schema')
    refs={key:request[key] for key in ('asic','synthesis','gate')}
    arun,srun,grun=[Path(refs[key]['run']).resolve() for key in ('asic','synthesis','gate')]
    a,s,g=[stage(refs[key],name) for key,name in
        (('asic','t80_soc'),('synthesis','t80_synth'),('gate','t80_gate'))]
    require(a['asic_cpu_verified'] is True and a['cpu_executed'] is True and a['global_FPGA_defined'] is False and
        g['gate_simulation_verified'] is True and g['sdf_annotated'] is False and
        g['cpu_executed'] is True and g['global_FPGA_defined'] is False and s['synthesis_completed'] is True and
        g['scope']=='t80_whole_soc_mapped_functional_without_SDF' and
        g.get('numeric_format')=='0x000e0c20' and g.get('internal_total_observable') is False and
        s['scope']=='t80_whole_soc_task_mode_preliminary_synthesis','Wrong T80 hardware execution scope')
    require(g['synthesis_summary_sha256']==refs['synthesis']['sha256'] and
        g['firmware_sha256']==a['compile_receipt']['firmware_manifest_sha256'],'Mixed T80 synthesis/firmware')
    require(sha(arun/'source_inputs.json')==a['compile_receipt']['source_inputs_sha256'] and
        read(arun/'compile_receipt.json')==a['compile_receipt'],'ASIC compile receipt changed')
    soc.verify_frozen(read(arun/'t80_build_contract.json'))
    require(sha(arun/'t80_build_contract.json')==a['build_contract_sha256'],'ASIC build changed')
    hardware=configuration_identity(arun)
    require(configuration_identity(srun)==hardware and
        a['compile_receipt']['platform_baseline_sha256']==s['link_report']['platform_baseline_sha256'],
        'ASIC and synthesis production hardware differ')
    require(sha(grun/'source_inputs.json')==g['source_inputs_sha256'],'Gate provenance changed')
    verify_inputs(read(grun/'source_inputs.json'))
    require(Decimal(str(s['metrics']['period_ns']))==Decimal('6.666666') and
        int(s['metrics']['RAMSP128X16'])==92 and int(s['metrics']['RAMSP4096X16'])==128,'Wrong T80 clock/macro configuration')
    left,right=cases(a,arun),cases(g,grun,mapped=True)
    act={};activity_ref=request.get('activity')
    if activity_ref:
        activity=stage(activity_ref,'t80_saif')
        require(activity.get('schema')=='arch03-t80-native-saif-v1' and
            activity.get('numeric_format')=='0x000e0c20' and activity.get('layout_id')==0x00100004 and
            activity.get('internal_total_observable') is False and
            activity['status']=='T80_native_saif_function_and_complete_windows_passed' and
            activity['gate_summary_sha256']==refs['gate']['sha256'] and
            activity['synthesis_summary_sha256']==refs['synthesis']['sha256'] and
            activity['firmware_sha256']==g['firmware_sha256'],'Mixed T80 native activity')
        act={r['case']:r for r in activity['cases']}
        require(set(act)==set(LAYERS) and len(activity['cases'])==12,'Incomplete T80 activity12')
        for name,row in act.items():
            require(row['task_window']==right[name]['task_window'] and
                row['layout_sha256']==right[name]['layout_sha256'],'Activity layout/window differs')
            actual=activity_audit(Path(activity_ref['run'])/row['activity']['file'],row['task_window'],window_reader=window_values)
            require(actual==row['activity'],'Activity audit differs')
    powers={}
    for ref in request.get('power',[]):
        raw=stage(ref,'t80_power');name=raw['case']
        require(raw.get('schema')=='arch03-t80-native-saif-power-v1' and
            raw.get('numeric_format')=='0x000e0c20' and raw.get('layout_id')==0x00100004 and
            raw.get('scope')=='t80_whole_soc_native_saif_pre_layout_power' and
            raw.get('status')=='reports_and_numbers_ready_unknown_impact_review_required' and
            name in act and name not in powers and
            raw['activity_summary_sha256']==activity_ref['sha256'] and
            raw['gate_summary_sha256']==refs['gate']['sha256'] and
            raw['synthesis_summary_sha256']==refs['synthesis']['sha256'] and
            raw['firmware_sha256']==g['firmware_sha256'] and
            raw['layout_sha256']==right[name]['layout_sha256'] and
            raw['task_window']==act[name]['task_window'] and raw['activity']==act[name]['activity'],
            'Mixed T80 power/window provenance')
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
        require(numbers==raw['numbers'] and read(Path(ref['run'])/'numbers.json')==numbers,'Changed T80 power extraction')
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
        note='T80 PT imports a separate exact 6.666666 ns SDC; original DC export is preserved. Comparison conditions and complete windows remain explicit.')
    batch=dict(status='not_run',tasks=0,outputs=0,official_precision_verified=False)
    if request.get('batch'):
        ref=request['batch'];b=stage(ref,'t80_batch20');brun=Path(ref['run'])
        require(configuration_identity(brun)==hardware and
            read(brun/'batch_identity.json')['firmware_manifest_sha256']==g['firmware_sha256'],
            'Final240 belongs to different T80 hardware/firmware')
        batch=audit_batch(brun,b,hardware,g['firmware_sha256'])
        batch['mean_cycles']=b['mean_task_cycles'];batch['host_elapsed_seconds']=b['host_elapsed_seconds']
    precision=audit_precision(request.get('precision'),batch)
    fixed_precision=fixed12_precision(arun,left)
    if precision['fresh_float_reference_verified']:
        batch.update(status='first20_integer_and_same_data_float_precision_verified',
            fresh_float_reference_verified=True,maximum_layer_nrmse_percent=precision['maximum_layer_nrmse_percent'],
            maximum_task_nrmse_percent=precision['maximum_task_nrmse_percent'],
            reason='Fresh T80 precision joined to this actual ASIC240; official600 remains unverified')
    drc=frozen_drc_inventory(s,srun)
    unverified=['Independent scoped timing/area review is separate from numerical report collection',
        'Unknown activity/model influence and pre-layout estimation limits','Official random600 and physical signoff']
    if not precision['fresh_float_reference_verified']:
        unverified.append('Fresh same-sample float20 recomputation; no old Q12 SSE/NRMSE reuse')
    return dict(schema='arch03-t80-evidence-export-v1',status='evidence_exported_stage_unaccepted',
        stage='T80',numeric_format='0x000e0c20',layout_id=0x00100004,shift=10,row_lanes=5,
        gate_internal_total_observable=False,
        selection=selection(aggregate,s['area_summary']),
        precision=precision,fixed12_precision=fixed_precision,
        stage_handoff=dict(next_stage='T64',allowed=False,reason='Numerical collection does not replace independent precision, timing, area and system-power review'),
        references=refs,activity_reference=activity_ref,power_references=request.get('power',[]),
        batch_reference=request.get('batch'),precision_reference=request.get('precision'),
        production_hardware=hardware,firmware_sha256=g['firmware_sha256'],netlist_sha256=s['artifacts']['mapped.v'],
        libraries_sha256=s['link_report']['library_inputs'],area=s['area_summary'],area_basis=s['area_basis'],
        timing_metrics=s['metrics'],drc_inventory=drc,conditions=conditions,
        cases=rows,aggregate=aggregate,batch=batch,history=request.get('history',[]),
        verification=dict(asic14=True,gate14_without_SDF=True,final240=batch.get('tasks')==240,
            activity12=len(act)==12,power12_numbers=len(powers)==12,
            internal20_precision_verified=precision['fresh_float_reference_verified'],
            fixed12_precision_verified=fixed_precision['verified'],
            task_mode_timing_verified=False,project_area_reviewed=False,system_power_verified=False,
            official_precision_verified=False,physical_signoff=False),
        unverified=unverified,exporter_sha256=sha(__file__),
        precision_auditor_sha256=sha(recovered_precision.__file__),
        numeric_auditor_sha256=sha(precision_tools.__file__),drc_parser_sha256=sha(__import__('t80_drc_audit').__file__))


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
    lines=['# T80原总线真实共享读回80PE配置证据报告','',
        '本报告复核ASIC/E203的total33/result/sat及无SDF门级result/sat。门级不观察内部total，不用参考值伪造第五列。功耗为布局前估算。独立时序、面积归属和未知活动影响审核另行记录；本导出不自动授予验收。','',
        'SS、0.99V、125°C；DC与任务周期6.666666ns。计时从首源VALID至最终写ACK并证明排空，保留原System Bus的源读、共享写、同地址真实读回及完整输出写回。','',
        '12层平均 %.6f 周期，按150MHz折算 %.6f task/s。'%
            (a['mean_cycles'],a['nominal_150MHz_tasks_per_second']),'',
        '| 层 | 周期 | 编码字节 | 平均功耗W | 能耗J |','|---|---:|---:|---:|---:|']
    for r in report['cases']:
        lines.append('| %s | %d | %d | %s | %s |'%(r['case'],r['cycles'],r['encoded_bytes'],
            r['raw_average_power_w'] if r['raw_average_power_w'] is not None else '未验证',
            r['raw_energy_j'] if r['raw_energy_j'] is not None else '未验证'))
    lines+=['','完整活动%d/12，功耗数值%d/12。时间加权平均功耗W：%s；平均J/task：%s。'%
        (a['activity_layers'],a['power_layers'],a['raw_time_weighted_power_w'],a['raw_energy_per_task_j']),
        '内部最终批量：%s，%d任务、%d输出；不代表官方600样本精度验收。'%(b['status'],b['tasks'],b['outputs']),
        '同批20条浮点精度：%s；最大逐层NRMSE：%s，最大逐任务NRMSE：%s。'%
            (precision['status'],'未验证' if layer_error is None else '%.10f%%'%layer_error,
             '未验证' if task_error is None else '%.10f%%'%task_error),
        '浮点来源模式：%s；原ZIP容器验证：%s；恢复的原NPZ成员核验：%s。'%
            (precision.get('source_mode','未验证'),precision.get('original_float_archive_verified',False),
             precision.get('recovered_original_members_verified',False)),
        '固定12性能任务的独立浮点核验：%s；不能替代完整20条。'%report['fixed12_precision']['status'],
        '冻结综合约束报告：违例记录%d，解析完整=%s，明确无违例标记=%s；严格时序审核仍独立。'%
            (report['drc_inventory']['violation_record_count'],report['drc_inventory']['extraction_complete'],
             report['drc_inventory']['explicit_no_violations']),
        '源码、固件、布局、数据、库、网表及活动身份、模块功耗、SRAM、未知驻留及全部计数见JSON。重叠等待不相加作为总周期，缺失功耗不作零。','',
        '项目面积上限1.20mm²；全部PPA来自T80自身配置。历史N1/B0证据独立保留，不转移PASS。缺同批20样本浮点精度或未知活动审核时，T80未验收，不进入T64。','',
        '历史失败/停止路径：']
    lines+=['- '+json.dumps(item,ensure_ascii=False) for item in report['history']]
    (output/'report_zh.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
    data.save(output/'receipt.json',dict(schema='arch03-t80-export-receipt-v1',
        artifacts={p.name:sha(p) for p in output.iterdir() if p.is_file()}))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--request',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();digest=sha(a.request);result=build(read(a.request))
    require(sha(a.request)==digest,'Request changed during audit');result['request_sha256']=digest
    write(result,a.output);print('T80_EVIDENCE_EXPORTED stage_accepted=false review_required=true',a.output)
