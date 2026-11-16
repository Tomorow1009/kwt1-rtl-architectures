"""Export one frozen C80 configuration as JSON/CSV/Chinese Markdown.

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
from c80_drc_audit import constraints_inventory
import c80_soc as soc
from p80_bus_metrics import parse_metrics
import c80_gate as gate_tools
from c80_power import extract_reports
from native_saif_activity import audit as activity_audit
from native_saif_replay import verify_inputs
from icb32_power import stream_sha as sha
from p80_window import window_values
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


from c80_precision_join import check_case


def cases(report,run,mapped=False):
    rows=report['cases']
    require(len(rows)==14 and {r['case'] for r in rows}==set(data.CASES14),'Incomplete C8014')
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
    from c80_precision_join import audit_batch as collect
    identity=read(Path(run)/'batch_identity.json')
    require(configuration_identity(run)==hardware and identity['firmware_manifest_sha256']==firmware_sha,
            'C80 first20 evidence belongs to different hardware or firmware')
    return collect(run,report)


def audit_precision(ref,batch):
    if ref is None:
        return dict(status='first20_float_audit_not_completed',fresh_float_reference_verified=False,
            official_precision_verified=False,maximum_layer_nrmse_percent=None,maximum_task_nrmse_percent=None)
    from c80_precision_join import audit_precision as collect
    return collect(ref,batch)


# Same fixed format and FLOAT data; pure numeric audit, no old hardware PASS.
from t80_report import fixed12_precision


def frozen_drc_inventory(synthesis,run):
    path=Path(run)/'constraints.rpt'
    require(synthesis.get('artifacts',{}).get('constraints.rpt')==sha(path),
        'Frozen constraint report identity changed')
    result=constraints_inventory(path.read_text())
    result.update(report_sha256=synthesis['artifacts']['constraints.rpt'],source=str(path),
        strict_timing_verified=False,scope='Frozen report inventory; detailed scoped STA/DRC review remains separate')
    return result


def selection(aggregate,area):
    bound=Decimal(str(area['conservative_budget_mm2']))
    return dict(conservative_area_mm2=str(bound),project_limit_mm2='1.00',
        numerical_area_limit_met=bound<=Decimal('1.00'),area_attribution_reviewed=False,
        eligible_for_next_hardware_stage=False,
        reason='Own C80 evidence, independent acceptance and matched-codec throughput and own-stage acceptance are required')


def build(request,cfg):
    require(request.get('schema')=='arch03-c80-report-request-v1' and cfg is not None,
        'Only explicit C80 runtime evidence is accepted')
    from c80_paths import allowed_run
    from c80_validation import verify_synthesis
    refs={key:request[key] for key in ('asic','synthesis','gate')}
    for ref in list(refs.values())+[request[k] for k in ('activity','batch') if request.get(k)]+request.get('power',[]):
        allowed_run(ref['run'],cfg,'C80 report source')
    arun,srun,grun=[allowed_run(refs[key]['run'],cfg,'C80 report '+key) for key in ('asic','synthesis','gate')]
    a,s,g=[stage(refs[key],name) for key,name in
        (('asic','c80_soc'),('synthesis','c80_synth'),('gate','c80_gate'))]
    checked,_=verify_synthesis(srun,refs['synthesis']['sha256'],cfg)
    require(checked==s,'C80 synthesis changed during collection')
    platform_sha=s['link_report']['platform_baseline_sha256']
    libraries=s['link_report']['library_inputs']
    depth=s['transaction_metadata_depth'];contract=read(arun/'c80_build_contract.json')
    require(contract['transaction_metadata_depth']==depth and depth==2,
        'ASIC/mapped queue-depth identity differs')
    require(a['asic_cpu_verified'] is True and a['cpu_executed'] is True and a['global_FPGA_defined'] is False and
        g['gate_simulation_verified'] is True and g['sdf_annotated'] is False and
        g['cpu_executed'] is True and g['global_FPGA_defined'] is False and s['synthesis_completed'] is True and
        g['scope']=='c80_whole_soc_mapped_functional_without_SDF' and
        g.get('numeric_format')=='0x000e0c20' and g.get('internal_total_observable') is False and
        s['scope']=='c80_partitioned_whole_soc_task_mode','Wrong C80 hardware execution scope')
    require(g['synthesis_summary_sha256']==refs['synthesis']['sha256'] and
        g['firmware_sha256']==a['compile_receipt']['firmware_manifest_sha256'],'Mixed C80 synthesis/firmware')
    require(sha(arun/'source_inputs.json')==a['compile_receipt']['source_inputs_sha256'] and
        read(arun/'compile_receipt.json')==a['compile_receipt'],'ASIC compile receipt changed')
    soc.verify_frozen(contract)
    require(sha(arun/'c80_build_contract.json')==a['build_contract_sha256'],'ASIC build changed')
    hardware=configuration_identity(arun)
    require(configuration_identity(srun)==hardware and
        a['compile_receipt']['platform_baseline_sha256']==platform_sha,
        'ASIC and synthesis production hardware differ')
    require(sha(grun/'source_inputs.json')==g['source_inputs_sha256'],'Gate provenance changed')
    verify_inputs(read(grun/'source_inputs.json'))
    require(Decimal(str(s['metrics']['period_ns']))==Decimal('6.666666') and
        int(s['metrics']['RAMSP128X16'])==92 and int(s['metrics']['RAMSP4096X16'])==128,'Wrong C80 clock/macro configuration')
    left,right=cases(a,arun),cases(g,grun,mapped=True)
    act={};activity_ref=request.get('activity')
    if activity_ref:
        activity=stage(activity_ref,'c80_saif')
        require(activity.get('schema')=='arch03-c80-native-saif-v1' and
            activity.get('numeric_format')=='0x000e0c20' and activity.get('layout_id')==0x00100006 and
            activity.get('internal_total_observable') is False and
            activity['status']=='C80_native_saif_function_and_complete_windows_passed' and
            activity['gate_summary_sha256']==refs['gate']['sha256'] and
            activity['synthesis_summary_sha256']==refs['synthesis']['sha256'] and
            activity['firmware_sha256']==g['firmware_sha256'],'Mixed C80 native activity')
        act={r['case']:r for r in activity['cases']}
        require(set(act)==set(LAYERS) and len(activity['cases'])==12,'Incomplete C80 activity12')
        for name,row in act.items():
            require(row['task_window']==right[name]['task_window'] and
                row['layout_sha256']==right[name]['layout_sha256'],'Activity layout/window differs')
            actual=activity_audit(Path(activity_ref['run'])/row['activity']['file'],row['task_window'],window_reader=window_values)
            require(actual==row['activity'],'Activity audit differs')
    powers={}
    for ref in request.get('power',[]):
        raw=stage(ref,'c80_power');name=raw['case']
        require(raw.get('schema')=='arch03-c80-native-saif-power-v1' and
            raw.get('numeric_format')=='0x000e0c20' and raw.get('layout_id')==0x00100006 and
            raw.get('scope')=='c80_whole_soc_native_saif_pre_layout_power' and
            raw.get('status')=='reports_and_numbers_ready_unknown_impact_review_required' and
            name in act and name not in powers and
            raw['activity_summary_sha256']==activity_ref['sha256'] and
            raw['gate_summary_sha256']==refs['gate']['sha256'] and
            raw['synthesis_summary_sha256']==refs['synthesis']['sha256'] and
            raw['firmware_sha256']==g['firmware_sha256'] and
            raw['layout_sha256']==right[name]['layout_sha256'] and
            raw['task_window']==act[name]['task_window'] and raw['activity']==act[name]['activity'],
            'Mixed C80 power/window provenance')
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
        require(numbers==raw['numbers'] and read(Path(ref['run'])/'numbers.json')==numbers,'Changed C80 power extraction')
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
        note='C80 PT imports a separate exact 6.666666 ns SDC; original DC export is preserved. Comparison conditions and complete windows remain explicit.')
    batch=dict(status='not_run',tasks=0,outputs=0,official_precision_verified=False)
    if request.get('batch'):
        ref=request['batch'];b=stage(ref,'c80_batch20');brun=Path(ref['run'])
        require(configuration_identity(brun)==hardware and
            read(brun/'batch_identity.json')['firmware_manifest_sha256']==g['firmware_sha256'],
            'Final240 belongs to different C80 hardware/firmware')
        batch=audit_batch(brun,b,hardware,g['firmware_sha256'])
        batch['mean_cycles']=b['mean_task_cycles'];batch['host_elapsed_seconds']=b['host_elapsed_seconds']
    precision=audit_precision(request.get('precision'),batch)
    fixed_precision=fixed12_precision(arun,left)
    if precision['fresh_float_reference_verified']:
        batch.update(status='first20_integer_and_same_data_float_precision_verified',
            fresh_float_reference_verified=True,maximum_layer_nrmse_percent=precision['maximum_layer_nrmse_percent'],
            maximum_task_nrmse_percent=precision['maximum_task_nrmse_percent'],
            reason='Fresh C80 precision joined to this actual ASIC240; official600 remains unverified')
    drc=frozen_drc_inventory(s,srun)
    unverified=['Independent scoped timing/area review is separate from numerical report collection',
        'Unknown activity/model influence and pre-layout estimation limits','Official random600 and physical signoff']
    if not precision['fresh_float_reference_verified']:
        unverified.append('Fresh same-sample float20 recomputation; no old Q12 SSE/NRMSE reuse')
    handoff=dict(next_stage='S3_C32',allowed=False,
        reason='Numerical export is not acceptance; review own PPA, recovery/contention and complete-codec throughput')
    return dict(schema='arch03-c80-evidence-export-v1',status='evidence_exported_stage_unaccepted',stage='C80',
        numeric_format='0x000e0c20',layout_id=0x00100006,shift=10,row_lanes=5,transaction_metadata_depth=depth,
        gate_internal_total_observable=False,
        selection=selection(aggregate,s['area_summary']),
        precision=precision,fixed12_precision=fixed_precision,
        stage_handoff=handoff,
        references=refs,activity_reference=activity_ref,power_references=request.get('power',[]),
        batch_reference=request.get('batch'),precision_reference=request.get('precision'),
        production_hardware=hardware,firmware_sha256=g['firmware_sha256'],netlist_sha256=s['artifacts']['mapped.v'],
        libraries_sha256=libraries,area=s['area_summary'],area_basis=s['area_basis'],
        synthesis_route=dict(scope=s['scope'],partition_area=s['partition_area'],
            block_mapping_seconds=s['block_mapping_seconds'],block_cache_reused=s['block_cache_reused'],
            final_link_seconds=s['final_link_seconds'],boundary_origin=s['boundary_origin'],
            old_linked_ddc_reused=False,source_proof='Fresh C80 link and all three freshly mapped partitions',
            context_auditor_sha256=sha(__import__('c80_validation').__file__)),
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
        numeric_auditor_sha256=sha(precision_tools.__file__),drc_parser_sha256=sha(__import__('c80_drc_audit').__file__))

def write(report,output):
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    data.save(output/'report.json',report)
    fields=('case cycles encoded_bytes transfer_bytes transfer_transactions nominal_150MHz_tasks_per_second '
        'mac_utilization raw_average_power_w raw_dynamic_w raw_leakage_w raw_energy_j layout_sha256 codec_sha256').split()
    for name,rows,columns in [('tasks.csv',report['cases'],fields),('summary.csv',[report['aggregate']],list(report['aggregate']))]:
        with (output/name).open('x',encoding='utf-8-sig',newline='') as stream:
            out=csv.DictWriter(stream,columns,extrasaction='ignore');out.writeheader();out.writerows(rows)
    a=report['aggregate'];b=report['batch'];precision=report['precision']
    lines=['# C80 完整编码流与原总线读回配置报告','',
        '原32位ICB和平台参数保持。首源VALID至最终写ACK并排空；保留共享写入及原总线实际读回。',
        '80 PE、X14/W12/累加32/total33、SHIFT10；SS、0.99V、125°C、6.666666ns；面积限制1.00mm²。',
        '本报告仅汇总本版证据，独立时序、面积、未知活动及模型审核另行记录，不自动授予验收。','',
        '事务队列深度%d。固定12层平均%.6f周期，按150MHz折算%.6f task/s。'%
        (report['transaction_metadata_depth'],a['mean_cycles'],a['nominal_150MHz_tasks_per_second']),
        '时间加权平均功耗W：%s；平均J/task：%s；布局前估算。'%(a['raw_time_weighted_power_w'],a['raw_energy_per_task_j']),
        '完整活动%d/12，功耗数值%d/12。'%(a['activity_layers'],a['power_layers']),'',
        '| 层 | 周期 | 字节 | 平均功耗W | J/task |','|---|---:|---:|---:|---:|']
    for row in report['cases']:
        lines.append('|%s|%d|%d|%s|%s|'%(row['case'],row['cycles'],row['encoded_bytes'],
            row['raw_average_power_w'] if row['raw_average_power_w'] is not None else '未测',
            row['raw_energy_j'] if row['raw_energy_j'] is not None else '未测'))
    lines+=['','前20条批量：%s，%d任务、%d输出。'%(b['status'],b['tasks'],b['outputs']),
        '新浮点精度：%s；最大逐层NRMSE：%s%%。'%(precision['status'],precision['maximum_layer_nrmse_percent']),
        '固定12性能任务精度：%s。'%report['fixed12_precision']['status'],
        'ASIC检查total/result/saturated；无SDF门级检查实际result/saturated及坐标，不伪造内部total。',
        '仅20条正式批量；不代表100条、官方600条或物理签核。原T80/S0历史数据保留，不能转移旧PASS。',
        '源码、固件、数据、库、网表和活动哈希、宏模型、缺失项与失败路径详见JSON。','',
        '历史失败/停止路径：']+['- '+json.dumps(item,ensure_ascii=False) for item in report['history']]
    (output/'report_zh.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
    data.save(output/'receipt.json',dict(schema='arch03-c80-export-receipt-v1',
        artifacts={item.name:sha(item) for item in output.iterdir() if item.is_file()}))


def main():
    import server_run as common
    import c80_paths
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('request','output','runtime-root'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--runtime-manifest-sha256',required=True)
    p.add_argument('--runtime-evidence',nargs=2,action='append',default=[])
    a=p.parse_args();require(not a.output.exists(),'Preserve previous C80 export')
    cfg=c80_paths.configure(read(common.ROOT/'handoff/team/server_config.json'),common.ROOT,
        a.runtime_root,a.runtime_manifest_sha256,a.runtime_evidence)
    # Output must be a new named report session in this already verified bundle.
    parts=a.output.absolute().relative_to(common.ROOT).parts
    require(len(parts)==3 and parts[0]=='runs' and re.fullmatch('[A-Za-z0-9_-]{1,64}',parts[1]) and
        parts[2]=='c80_report' and not a.output.parent.exists(),'Use a new private report session')
    digest=sha(a.request);report=build(read(a.request),cfg)
    require(sha(a.request)==digest,'Report request changed during audit')
    c80_paths.recheck(cfg);report['request_sha256']=digest
    write(report,a.output)
    print('C80_EVIDENCE_EXPORTED stage_accepted=false',str(a.output),flush=True)


if __name__=='__main__':main()
