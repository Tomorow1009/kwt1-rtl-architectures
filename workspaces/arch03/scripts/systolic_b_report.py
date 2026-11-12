"""Export one frozen B configuration as JSON/CSV/Chinese Markdown.

Read-only evidence collection, no EDA and no automatic timing/power approval.
Optional missing evidence stays explicit; a preliminary export is not delivery.
"""
import argparse
import csv
from decimal import Decimal
import json
from pathlib import Path
import re
import systolic_b_data as data
import systolic_b_soc as soc
from systolic_b_bus_metrics import parse_metrics
from systolic_b_precision import audit as precision_audit
from native_saif_crosscheck import extract_reports
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


def check_case(row,run,name,source=None):
    run=Path(run);task=run/(name+'_data')
    source=Path(source) if source is not None else run.parents[2]/'validated_data'/name
    data.verify_prepared(source,task)
    capture=data.check_capture(run/(name+'.csv'),task)
    require(capture==row['capture'] and row['outputs']==25344,'Actual output receipt differs')
    for path,key in ((task/'codec.json','codec_sha256'),(task/'layout_manifest.json','layout_sha256'),
        (run/(name+'.log'),'log_sha256'),(run/(name+'_boot')/'manifest.json','boot_manifest_sha256')):
        require(sha(path)==row[key],'Changed per-task provenance '+key)
    boot=read(run/(name+'_boot')/'manifest.json')
    require(boot['input_bytes_preloaded']==0,'Preloaded task data')
    require(all(Path(filename).name==filename for filename in boot['files']),'Unsafe boot filename')
    verify_inputs({str(run/(name+'_boot')/filename):value for filename,value in boot['files'].items()})
    text=(run/(name+'.log')).read_text();size=read(task/'codec.json')['encoded_bytes']
    markers=soc.MARKERS+['ARCH03_ICB32_SOURCE_READY words=%d scope=PC_file_only no_ITCM_task_data=true'%(size//4)]
    result=data.parse_result(text,capture['saturated'],markers)
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


def cases(report,run):
    rows=report['cases']
    require(len(rows)==14 and {r['case'] for r in rows}==set(data.CASES14),'Incomplete B14')
    for row in rows:check_case(row,run,row['case'])
    return {row['case']:row for row in rows}


def aggregate_rows(rows):
    require(len(rows)==12 and {r['case'] for r in rows}==set(LAYERS),'Incomplete performance layer set')
    total=sum(r['cycles'] for r in rows)
    duration=sum(Decimal(r['duration_ns']) for r in rows)
    powered=[r for r in rows if r['raw_energy_j'] is not None]
    energy=sum(Decimal(r['raw_energy_j']) for r in powered) if len(powered)==12 else None
    return dict(tasks=12,total_cycles=total,mean_cycles=total/12.,
        nominal_150MHz_tasks_per_second=1800000000./total,
        nominal_150MHz_MMAC_per_second=12.*150*MACS/total,
        goal_7000_met_by_cycles=total*7000<=1800000000,
        power_layers=len(powered),activity_layers=sum(r['activity'] is not None for r in rows),
        raw_energy_per_task_j=str(energy/12) if energy is not None else None,
        raw_time_weighted_power_w=str(energy/(duration*Decimal('1e-9'))) if energy is not None else None,
        raw_arithmetic_layer_mean_power_w=str(sum(Decimal(r['raw_average_power_w']) for r in rows)/12) if energy is not None else None)


def build(request):
    require(request['schema']=='systolic-b-report-request-v1','Wrong B report schema')
    refs={key:request[key] for key in ('asic','synthesis','gate')}
    arun,srun,grun=[Path(refs[key]['run']).resolve() for key in ('asic','synthesis','gate')]
    a,s,g=[stage(refs[key],name) for key,name in
        (('asic','systolic_b_soc'),('synthesis','systolic_b_synth'),('gate','systolic_b_gate'))]
    require(a['asic_cpu_verified'] is True and a['cpu_executed'] is True and a['global_FPGA_defined'] is False and
        g['gate_simulation_verified'] is True and g['sdf_annotated'] is False and
        g['cpu_executed'] is True and g['global_FPGA_defined'] is False and s['synthesis_completed'] is True and
        g['scope']=='systolic_b_whole_soc_mapped_functional_without_SDF' and
        s['scope']=='systolic_b_whole_soc_task_mode_preliminary_synthesis','Wrong B hardware execution scope')
    require(g['synthesis_summary_sha256']==refs['synthesis']['sha256'] and
        g['firmware_sha256']==a['compile_receipt']['firmware_manifest_sha256'],'Mixed B synthesis/firmware')
    require(sha(arun/'source_inputs.json')==a['compile_receipt']['source_inputs_sha256'] and
        read(arun/'compile_receipt.json')==a['compile_receipt'],'ASIC compile receipt changed')
    soc.verify_frozen(read(arun/'systolic_b_build_contract.json'))
    require(sha(arun/'systolic_b_build_contract.json')==a['build_contract_sha256'],'ASIC build changed')
    hardware=configuration_identity(arun)
    require(configuration_identity(srun)==hardware and
        a['compile_receipt']['platform_baseline_sha256']==s['link_report']['platform_baseline_sha256'],
        'ASIC and synthesis production hardware differ')
    require(sha(grun/'source_inputs.json')==g['source_inputs_sha256'],'Gate provenance changed')
    verify_inputs(read(grun/'source_inputs.json'))
    require(Decimal(str(s['metrics']['period_ns']))==Decimal('6.666666') and
        int(s['metrics']['RAMSP128X16'])==92 and int(s['metrics']['RAMSP4096X16'])==128,'Wrong B clock/macro configuration')
    left,right=cases(a,arun),cases(g,grun)
    act={};activity_ref=request.get('activity')
    if activity_ref:
        activity=stage(activity_ref,'systolic_b_saif')
        require(activity['status']=='B_native_saif_function_and_complete_windows_passed' and
            activity['gate_summary_sha256']==refs['gate']['sha256'] and
            activity['synthesis_summary_sha256']==refs['synthesis']['sha256'] and
            activity['firmware_sha256']==g['firmware_sha256'],'Mixed B native activity')
        act={r['case']:r for r in activity['cases']}
        require(set(act)==set(LAYERS) and len(activity['cases'])==12,'Incomplete B activity12')
        for name,row in act.items():
            require(row['task_window']==right[name]['task_window'] and
                row['layout_sha256']==right[name]['layout_sha256'],'Activity layout/window differs')
            actual=activity_audit(Path(activity_ref['run'])/row['activity']['file'],row['task_window'])
            require(actual==row['activity'],'Activity audit differs')
    powers={}
    for ref in request.get('power',[]):
        raw=stage(ref,'systolic_b_power');name=raw['case']
        require(name in act and name not in powers and
            raw['activity_summary_sha256']==activity_ref['sha256'] and
            raw['gate_summary_sha256']==refs['gate']['sha256'] and
            raw['synthesis_summary_sha256']==refs['synthesis']['sha256'] and
            raw['firmware_sha256']==g['firmware_sha256'] and
            raw['layout_sha256']==right[name]['layout_sha256'] and
            raw['task_window']==act[name]['task_window'] and raw['activity']==act[name]['activity'],
            'Mixed B power/window provenance')
        power_run=Path(ref['run']);clock=raw['power_clock']
        precise,_=restore_clock((srun/'mapped.sdc').read_bytes().decode('ascii'),s['metrics']['period_ns'])
        require((power_run/'mapped.precise.sdc').read_bytes()==precise.encode('ascii') and
            sha(power_run/'mapped.precise.sdc')==clock['imported_sdc_sha256'] and
            clock['original_sdc_sha256']==sha(srun/'mapped.sdc') and
            Decimal(clock['measured']['hf_period_ns'])==Decimal('6.666666') and
            Decimal(clock['measured']['lf_period_ns'])==Decimal('66') and
            clock['original_sdc_modified'] is False and clock['other_constraints_unchanged'] is True,
            'Power did not import the frozen exact clock')
        numbers=extract_reports(Path(ref['run']),'systolic_b')
        duration=window_values(raw['task_window'])[2]
        numbers.update(duration_ns=duration,average_power_w=numbers['reported_power_w']['total'])
        numbers['energy_j']=str(Decimal(numbers['average_power_w'])*Decimal(duration)*Decimal('1e-9'))
        require(numbers==raw['numbers'] and read(Path(ref['run'])/'numbers.json')==numbers,'Changed B power extraction')
        powers[name]=dict(reference=ref,raw=raw,numbers=numbers)
    rows=[]
    for name in LAYERS:
        x,y=left[name],right[name]
        require(x['capture']==y['capture'] and x['layout_sha256']==y['layout_sha256'] and
            x['codec_sha256']==y['codec_sha256'] and x['task_window']['cycles']==y['task_window']['cycles'],
            'ASIC/gate results, layout or complete cycles differ')
        w=y['task_window'];duration=window_values(w)[2];n=powers[name]['numbers'] if name in powers else None
        row=dict(case=name,cycles=w['cycles'],duration_ns=duration,outputs=25344,
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
        note='B PT imports a separate exact 6.666666 ns SDC; original rounded DC export is preserved. Historical R4 PT used its original 6.66667 ns export; disclose this serialization difference in comparisons.')
    batch=dict(status='not_run',tasks=0,outputs=0,official_precision_verified=False)
    if request.get('batch'):
        ref=request['batch'];b=stage(ref,'systolic_b_batch');brun=Path(ref['run'])
        require(configuration_identity(brun)==hardware and
            read(brun/'batch_identity.json')['firmware_manifest_sha256']==g['firmware_sha256'],
            'Final1200 belongs to different B hardware/firmware')
        batch=precision_audit(brun,ref['sha256'])
        # Reuse the same complete CPU/IRQ/boot/window audit for every real
        # task. The precision audit also binds its original matrix reference.
        identity=read(brun/'batch_identity.json')
        for task,entry in zip(identity['task_list'],b['cases']):
            receipt=brun/entry['receipt'];row=read(receipt)
            require(row['batch_identity_sha256']==b['batch_identity_sha256'] and
                entry['cycles']==row['task_window']['cycles'] and entry['outputs']==25344,
                'Batch aggregate/identity differs from its actual task')
            check_case(row,receipt.parent,'task',task['source'])
        batch['mean_cycles']=b['mean_task_cycles'];batch['host_elapsed_seconds']=b['host_elapsed_seconds']
    return dict(schema='systolic-b-evidence-export-v1',status='evidence_exported_review_required',
        references=refs,activity_reference=activity_ref,power_references=request.get('power',[]),
        production_hardware=hardware,firmware_sha256=g['firmware_sha256'],netlist_sha256=s['artifacts']['mapped.v'],
        libraries_sha256=s['link_report']['library_inputs'],area=s['area_summary'],area_basis=s['area_basis'],
        timing_metrics=s['metrics'],conditions=conditions,
        cases=rows,aggregate=aggregate,batch=batch,history=request.get('history',[]),
        verification=dict(asic14=True,gate14_without_SDF=True,final1200=batch.get('tasks')==1200,
            activity12=len(act)==12,power12_numbers=len(powers)==12,
            task_mode_timing_verified=False,project_area_reviewed=False,system_power_verified=False,
            official_precision_verified=False,physical_signoff=False),
        unverified=['Independent scoped timing/area review is separate from numerical report collection',
            'Unknown activity/model influence and pre-layout estimation limits',
            'Official random600 and physical signoff'],exporter_sha256=sha(__file__))


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
    lines=['# 5×16脉动B冻结配置证据报告','',
        '本报告逐项复核同一配置的实际ASIC/E203及无SDF门级结果，功耗数值为布局前估算。独立时序、面积归属和未知活动影响审核另行记录；本导出不自动授予验收。','',
        'SS、0.99V、125°C；DC与任务周期6.666666ns。计时从首源VALID至最终写ACK并证明排空，没有省略真实共享SRAM写入。','',
        '12层平均 %.6f 周期，按150MHz折算 %.6f task/s；7000目标：%s。'%
            (a['mean_cycles'],a['nominal_150MHz_tasks_per_second'],'达到' if a['goal_7000_met_by_cycles'] else '未达到'),'',
        '| 层 | 周期 | 编码字节 | 平均功耗W | 能耗J |','|---|---:|---:|---:|---:|']
    for r in report['cases']:
        lines.append('| %s | %d | %d | %s | %s |'%(r['case'],r['cycles'],r['encoded_bytes'],
            r['raw_average_power_w'] if r['raw_average_power_w'] is not None else '未验证',
            r['raw_energy_j'] if r['raw_energy_j'] is not None else '未验证'))
    lines+=['','完整活动%d/12，功耗数值%d/12。时间加权平均功耗W：%s；平均J/task：%s。'%
        (a['activity_layers'],a['power_layers'],a['raw_time_weighted_power_w'],a['raw_energy_per_task_j']),
        '内部最终批量：%s，%d任务、%d输出；不代表官方600样本精度验收。'%(b['status'],b['tasks'],b['outputs']),
        '源码、固件、布局、数据、库、网表及活动身份、模块功耗、SRAM、未知驻留及全部计数见JSON。重叠等待不相加作为总周期，缺失功耗不作零。','',
        '面积保守上界及setup/hold来自本配置综合报告；原R4结果独立保留，不转移PASS。最终R4/B收益只归因整体配置，不单独归因脉动结构。','',
        '历史失败/停止路径：']
    lines+=['- '+json.dumps(item,ensure_ascii=False) for item in report['history']]
    (output/'report_zh.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
    data.save(output/'receipt.json',dict(schema='systolic-b-export-receipt-v1',
        artifacts={p.name:sha(p) for p in output.iterdir() if p.is_file()}))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--request',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();digest=sha(a.request);result=build(read(a.request))
    require(sha(a.request)==digest,'Request changed during audit');result['request_sha256']=digest
    write(result,a.output);print('B_EVIDENCE_EXPORTED review_required=true',a.output)
