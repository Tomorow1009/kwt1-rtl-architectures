"""Real ASIC E203 polling sequence: rejected configs, recovery, then A/B/A.

The caller holds the common server lock. No functional-TCM shortcut, synthetic
CPU result, activity aggregation, or IRQ claim. Python 3.6 standard library.
"""
import re
import time
from decimal import Decimal, InvalidOperation
from pathlib import Path
from server_run import ROOT,A2,A3,sha,save,vendor
from install_platform import platform_sources
from install_dma16 import install
from asic_boot import prepare,loader_include
from stdcell_verify import extract_model
from timing_contract import TB_PERIOD_NS
import dma16_batch as common
import build_dma16_sequence as firmware_tools

MARKERS=[
 'ARCH03_ASIC_BOOT_READY bytes=262144 macros=32 scope=initial_ITCM_only',
 'ARCH03_ASIC_MODE_MATCH test_mode=0 pllbypass=1 divider_bypass=1',
 'ARCH03_BOOT_MODE_MATCH bootrom_selected=1 scope=complete_task',
 'DMA16_SEQUENCE_SOURCE_READY words_per_bank=11744 scope=PC_file_only no_ITCM_task_data=true']
WINDOW_FIELDS=('finished','failed','failure_code','start_cycle','end_cycle','cycles','start_ns','end_ns',
 'finished_cycle','finished_ns','source_bytes','input_write_bytes','input_read_bytes','output_bytes')
PHASE_FIELDS=('phase','kind','rc','source_acks','stage_acks','read_acks','output_acks',
 'start_cycle','end_cycle','cycles','window_failed','saturated')


def fields(line,prefix,keys):
    parts=line[len(prefix)+1:].split()
    common.require(line.startswith(prefix+' ') and all(re.fullmatch(r'[A-Za-z_]+=[^\s=]+',p) for p in parts),
                   'Malformed '+prefix)
    pairs=[p.split('=',1) for p in parts];result=dict(pairs)
    common.require(len(result)==len(pairs) and set(result)==set(keys),'Incomplete/duplicate '+prefix)
    return result


def integer(value,signed=False):
    common.require(re.fullmatch(r'-?\d+' if signed else r'\d+',value),'Invalid integer field')
    return int(value)


def signed32(value):
    return value if value<0x80000000 else value-0x100000000


def check_window(window,phase,counts):
    result={key:integer(value) for key,value in window.items() if not key.endswith('_ns')}
    common.require(result['finished']==1 and result['failed']==int(phase<=7) and
                   result['failure_code']==(11 if phase<=7 else 0),'Wrong sequence window outcome')
    common.require(result['cycles']==result['end_cycle']-result['start_cycle'] and
                   result['finished_cycle']>=result['end_cycle'],'Sequence cycle/drain mismatch')
    try:timestamps={key:Decimal(window[key]) for key in ('start_ns','end_ns','finished_ns')}
    except InvalidOperation:raise ValueError('Invalid sequence timestamp')
    common.require(all(value.is_finite() and value>=0 for value in timestamps.values()),'Nonfinite sequence timestamp')
    common.require(timestamps['finished_ns']>=timestamps['end_ns'],'Drain time precedes final response')
    if phase<=5:
        common.require(result['start_cycle']==result['end_cycle']==result['cycles']==0,'Rejected config issued task traffic')
    else:
        common.require(result['cycles']>0 and abs(timestamps['end_ns']-timestamps['start_ns']-
            Decimal(result['cycles'])*Decimal(TB_PERIOD_NS))<=Decimal('0.000002'),'Sequence time/cycle mismatch')
    for key,count in zip(('source_bytes','input_write_bytes','input_read_bytes','output_bytes'),counts):
        # Failed window counters stop at cancellation; the independent phase
        # ledger continues counting the real responses that drain afterwards.
        common.require(result[key]%4==0 and 0<=result[key]<=count*4,'Window exceeds actual phase traffic')
        if phase>=8:common.require(result[key]==count*4,'Incomplete successful task transfer')
    result.update({key:str(value) for key,value in timestamps.items()})
    result['period_ns']=TB_PERIOD_NS
    result['performance_eligible']=phase>=8
    return result


def check_phase(phase,summary,window,words,manifest,captures):
    numbers={key:integer(value,key=='rc') for key,value in summary.items()}
    expected_kind=1 if phase<=5 else 2 if phase==6 else 3 if phase==7 else 4
    descriptor=manifest['tasks']['B' if phase==9 else 'A']['descriptor']
    counts=[numbers[key] for key in ('source_acks','stage_acks','read_acks','output_acks')]
    rc=-1 if phase==7 else 0
    common.require(numbers['phase']==phase and numbers['kind']==expected_kind and numbers['rc']==rc and
                   numbers['window_failed']==int(phase<=7),'Wrong phase kind/result')
    common.require(len(words)==33 and words[0]==phase and words[1]==expected_kind and signed32(words[2])==rc and
                   signed32(words[32])==rc and words[25]==descriptor and
                   words[28]==manifest['configuration']['short_timeout_cycles'],'Receipt phase/metadata mismatch')
    common.require(words[21]==min(phase,5) and words[22]==7 and
                   words[23]==int(manifest['fault_sites']['sequence_fault_store'],16) and words[24]==0x40000004,
                   'Missing exact guarded CPU fault evidence')
    common.require(words[3]&0x4000 and not words[3]&0x21a1 and not words[5]&0x1f1f,
                   'Receipt does not prove ready/drain')
    common.require(words[9:13]==counts and words[13]==counts[1]*4 and words[14]==counts[3]*4 and
                   words[17]==numbers['saturated'],'Receipt/independent phase counts mismatch')
    if phase<=5:
        mutations={1:(0x28,0xb0000002),2:(0x2c,0xa007f000),3:(0x30,0xa0000000),4:(0x34,46972),5:(0x38,50684)}
        common.require(counts==[0,0,0,0] and words[15:18]==[0,0,0] and words[6:9]==[3,0x40000004,2] and
                       words[4]&63==48 and words[3]&16 and not words[3]&8 and words[20]==1 and
                       tuple(words[26:28])==mutations[phase],'Incomplete real configuration rejection')
    elif phase<=7:
        common.require(0<counts[0]<11744 and 0<=counts[1]<=counts[0] and counts[1]<11744 and
                       counts[2:]==[0,0] and words[15:18]==[0,0,0] and words[6]==0 and
                       words[4]&63==48 and not words[3]&24 and words[20]==1 and words[26:28]==[0,0],
                       'Incomplete partial task cancellation/recovery')
        if phase==6:
            common.require(32<=words[29]<=counts[0] and words[30]<=counts[1] and words[31]&1,
                           'CANCEL was not observed during initial loading')
        else:
            common.require(words[29:32]==[0,0,0] and (words[18]|words[19]<<32)>=words[28],
                           'Driver timeout budget was not reached')
    else:
        capture=captures[phase-8]
        common.require(counts==[11744,11744,11744,12672] and words[15:17]==[23488,25344] and
                       words[4]&63==31 and words[3]&8 and not words[3]&16 and words[6]==0 and words[26:28]==[0,0] and
                       words[29:32]==[0,0,0] and words[17]==capture['saturated'] and capture['outputs']==25344,
                       'Complete A/B/A task does not match actual capture')
    measured=check_window(window,phase,counts)
    common.require(all(numbers[key]==measured[key] for key in ('start_cycle','end_cycle','cycles')),
                   'Window differs from phase receipt summary')
    cpu_cycles=words[18]|words[19]<<32
    if phase>=6:common.require(cpu_cycles>=measured['cycles'],'CPU interval does not enclose measured transaction window')
    return dict(phase=phase,kind=expected_kind,result=rc,descriptor=descriptor,receipt_words=words,
                summary=numbers,task_window=measured,cpu_cycles=cpu_cycles,
                scope='hardware_observer_checked_receipt',performance_eligible=phase>=8)


def parse_transcript(text,manifest,captures):
    common.require(len(captures)==3,'Expected three independent A/B/A captures')
    common.require(not re.search(r'(?m)^DMA16_SEQUENCE_FIXTURE_|^DMA16_SEQUENCE_PASS .*cpu_executed=false',text),
                   'NO_CPU fixture cannot establish real CPU sequence acceptance')
    common.require(not re.search(r'(?im)^\s*(?:Error-|Fatal:|Error:|FATAL\b|FAIL\b|\S*_FAIL\b)',text),'Sequence simulator failed')
    for marker in MARKERS:common.require(text.splitlines().count(marker)==1,'Missing/duplicate ASIC marker '+marker)
    records=[];active=None;selected=[];final=None
    for line in text.splitlines():
        if line.startswith('DMA16_SEQUENCE_SOURCE_SELECTED '):
            item=fields(line,'DMA16_SEQUENCE_SOURCE_SELECTED',('descriptor',))
            common.require(re.fullmatch('[0-9a-fA-F]{8}',item['descriptor']),'Invalid selected source descriptor')
            selected.append(int(item['descriptor'],16))
        elif line.startswith('DMA16_SEQUENCE_PHASE_ARM '):
            item=fields(line,'DMA16_SEQUENCE_PHASE_ARM',('phase','descriptor'))
            phase=integer(item['phase']);common.require(active is None and phase==len(records)+1<=10,'Missing/duplicate/reordered phase')
            descriptor=manifest['tasks']['B' if phase==9 else 'A']['descriptor']
            common.require(re.fullmatch('[0-9a-fA-F]{8}',item['descriptor']) and int(item['descriptor'],16)==descriptor,'Phase selected wrong A/B source')
            active=dict(phase=phase)
        elif line.startswith('DMA16_TASK_WINDOW '):
            common.require(active is not None and 'window' not in active,'Unowned/duplicate task window')
            active['window']=fields(line,'DMA16_TASK_WINDOW',WINDOW_FIELDS)
        elif line.startswith('DMA16_SEQUENCE_RECEIPT '):
            item=fields(line,'DMA16_SEQUENCE_RECEIPT',('phase','words'))
            common.require(active is not None and 'words' not in active and integer(item['phase'])==active['phase'],'Unowned/duplicate raw receipt')
            words=item['words'].split(',')
            common.require(len(words)==33 and all(re.fullmatch('[0-9a-fA-F]{8}',word) for word in words),'Malformed receipt words')
            active['words']=[int(word,16) for word in words]
        elif line.startswith('DMA16_SEQUENCE_PHASE_PASS '):
            common.require(active is not None and 'window' in active and 'words' in active,'Phase PASS without full evidence')
            records.append(check_phase(active['phase'],fields(line,'DMA16_SEQUENCE_PHASE_PASS',PHASE_FIELDS),
                active['window'],active['words'],manifest,captures));active=None
        elif line.startswith('DMA16_SEQUENCE_PASS '):
            common.require(final is None and active is None and len(records)==10,'Premature/duplicate sequence completion')
            final=fields(line,'DMA16_SEQUENCE_PASS',('phases','tasks','outputs','cpu_executed','guarded_faults','timeout_recovery'))
    expected=[manifest['tasks']['B' if phase==9 else 'A']['descriptor'] for phase in range(1,11)]
    common.require(active is None and len(records)==10 and selected==expected and final is not None,'Incomplete sequence/source selections')
    common.require(final==dict(phases='10',tasks='3',outputs='76032',cpu_executed='true',guarded_faults='5',timeout_recovery='true'),
                   'Actual CPU/trap/timeout evidence missing; NO_CPU fixtures are not ASIC acceptance')
    for previous,current in zip(records[5:],records[6:]):
        common.require(current['task_window']['start_cycle']>previous['task_window']['end_cycle'],
                       'Sequence clocks reset or task windows overlap')
    return records


def check_frozen(items):
    for path,digest in items.items():common.require(sha(Path(path))==digest,'Sequence frozen artifact changed: '+path)


def source_list():
    return [A2/'rtl/requantize.sv',A2/'rtl/dot64.sv',A2/'arch02/rtl/sram_port.sv',
        A2/'arch02/rtl/sram_macro_adapter.sv']+[A3/'rtl'/name for name in
        ('arch03_linear16.sv','arch03_dma16_accel.sv','arch03_icb_arb2.sv',
         'arch03_icb_memory_router.sv','arch03_shared_sram.sv','arch03_tcm_ram.sv')]


def sequence_testbench(text):
    old='`include "arch03_dma16_monitor.svh"'
    common.require(text.count(old)==1 and text.count('arch03_clock_mode_guard a3_asic_mode(')==1,
                   'Unexpected DMA16 ASIC TB integration')
    replacement='`include "arch03_dma16_sequence_monitor.svh"\n'
    # asic_boot's fixed clock/boot guard refers to the original monitor names.
    # Declare after the sequence include (before the guard) to avoid implicit
    # nets, and guard the entire ten-phase sequence including inter-task gaps.
    replacement+='wire a3_mon_clk=s16_clk;\nwire a3_mon_rst_n=s16_rst_n;\n'
    replacement+='wire a3_window_active=(s16_phase!=0) && (s16_completed<10);\n'
    replacement+='wire a3_window_finished=(s16_completed==10);\n'
    return text.replace(old,replacement)


def verify(cfg,run,platform_source,cases,call,firmware=None):
    run=Path(run).resolve();firmware=Path(firmware or ROOT/'firmware_sequence').resolve()
    firmware.relative_to(ROOT.resolve())
    manifest,image=firmware_tools.verify_firmware(firmware)
    common.require(len(cases)==2 and len(set(cases))==2 and list(cases)==[manifest['tasks'][key]['case'] for key in ('A','B')],
                   'Sequence cases must exactly match firmware A/B order')
    tasks={};tracked=[]
    for source_id,key in enumerate(('A','B')):
        original=ROOT/'validated_data'/cases[source_id]
        common.require(firmware_tools.task_identity(original,source_id)==manifest['tasks'][key],'Sequence task identity changed')
        task=run/('task_'+key);common.prepare_case(original,task);common.verify_prepared(original,task);tasks[key]=task
        tracked += [path for folder in (original,task) for path in folder.iterdir() if path.is_file()]
    source_receipt=firmware_tools.verify_runtime_sources(manifest,tasks['A']/'load32.hex',tasks['B']/'load32.hex')
    save(run/'runtime_sources.json',source_receipt)
    platform=run/'platform';platform_manifest=install(platform_source,platform)
    tb=platform/'tb/tb_top.v';text=tb.read_text()
    tb.write_text(sequence_testbench(text))
    platform_manifest['modified_files']['tb/tb_top.v']=sha(tb)
    platform_manifest.update(monitor='arch03_dma16_sequence_monitor.svh',sequence_polling=True,sequence_cpu_verified=False)
    save(platform/'platform_manifest.json',platform_manifest)
    loader=run/'arch03_asic_boot.svh';loader.write_text(loader_include())
    boot=run/'boot_sequence';boot_receipt=prepare(image,boot)
    boot_receipt.update(scope='initial_ITCM_firmware_only',runtime_task_loading='sequence_original_SysMem_ICB')
    save(boot/'manifest.json',boot_receipt)
    model=extract_model(cfg,run);libs=[model]+vendor(cfg,run)
    monitors=[A3/'tb'/name for name in ('arch03_dma16_sequence_source.sv','arch03_task_window16.sv','arch03_clock_mode_guard.sv')]
    files=platform_sources(platform)+source_list()+monitors+[tb]+libs
    includes=list(dict.fromkeys([run,A3/'tb',platform/'rtl/e203/core']+[path.parent for path in files]))
    command=[cfg['tools']['vcs'],'-full64','-sverilog','-timescale=1ns/1fs','+define+ARM_UD_MODEL',
        '+define+functional','-top','tb_top','-o',str(run/'simv')]+['+incdir+'+str(p) for p in includes]+files
    save(run/'compile_command.json',[str(value) for value in command])
    tracked += files+[loader,A3/'tb/arch03_dma16_sequence_monitor.svh',run/'arch02_sram_config.vh',
                       run/'runtime_sources.json',run/'compile_command.json']
    tracked += [path for folder in (platform,boot) for path in folder.rglob('*') if path.is_file()]
    tracked += [firmware/name for name in ('manifest.json','driver.elf','sequence.bin','sequence.verilog')]
    tracked += [ROOT/rel for rel in manifest['source_sha256']]
    tracked += [path for base in (A2,A3) for path in base.rglob('*') if path.is_file() and path.suffix in ('.vh','.svh')]
    tracked += [A3/'scripts'/name for name in ('server_run.py','install_platform.py','install_dma16.py',
        'asic_boot.py','stdcell_verify.py','timing_contract.py','dma16_sequence_soc.py')]
    frozen={str(path.resolve()):sha(path) for path in tracked};save(run/'source_inputs.json',frozen)
    compile_log=call(command,run,'compile.log')
    common.require(not re.search(r'Warning-\[(?:IPDW|PCWM-W|INAV|SIOB)\]',compile_log),'Sequence VCS width/declaration warning')
    common.require((run/'simv').is_file(),'Missing sequence simulator');check_frozen(frozen)
    for path in [run/'simv',run/'compile.log',run/'source_inputs.json']:frozen[str(path.resolve())]=sha(path)
    save(run/'frozen_inputs.json',frozen);frozen_sha=sha(run/'frozen_inputs.json')
    prefix=run/'sequence'
    command=[str(run/'simv'),'+BOOT_DIR='+str(boot),'+FIRST_LOAD32='+str(tasks['A']/'load32.hex'),
        '+SECOND_LOAD32='+str(tasks['B']/'load32.hex'),'+DATA_DIR='+str(tasks['A']),'+SECOND_DIR='+str(tasks['B']),
        '+CAPTURE_PREFIX='+str(prefix),'+EXPECTED_FAULT_EPC=%08x'%int(manifest['fault_sites']['sequence_fault_store'],16),
        '+FIRST_DESCRIPTOR=%08x'%manifest['tasks']['A']['descriptor'],
        '+SECOND_DESCRIPTOR=%08x'%manifest['tasks']['B']['descriptor'],
        '+SHORT_TIMEOUT=%d'%manifest['configuration']['short_timeout_cycles']]
    save(run/'sequence_command.json',command)
    try:
        started=time.monotonic();text=call(command,run,'sequence.log');elapsed=time.monotonic()-started
        captures=[common.check_capture(Path(str(prefix)+'__task%d.csv'%index),tasks[key]) for index,key in enumerate(('A','B','A'),1)]
        phases=parse_transcript(text,manifest,captures)
        check_frozen(frozen)
        common.require(sha(run/'frozen_inputs.json')==frozen_sha,'Sequence frozen manifest changed')
        for source_id,key in enumerate(('A','B')):common.verify_prepared(ROOT/'validated_data'/cases[source_id],tasks[key])
        for phase in phases:save(run/('phase_%02d.json'%phase['phase']),phase)
        total=sum(item['task_window']['cycles'] for item in phases[7:])
        report=dict(status='passed',scope='asic_rtl_functional_sequence',cpu_executed=True,
            polling_only=True,irq_verified=False,actual_CPU_traps_verified=True,actual_driver_timeout_verified=True,
            no_reset_ABA_verified=True,guarded_faults=5,phases=phases,captures=captures,
            outputs=76032,host_elapsed_seconds=elapsed,frozen_inputs_sha256=frozen_sha,
            platform_baseline_sha256=platform_manifest['baseline_sha256'],firmware_manifest_sha256=sha(firmware/'manifest.json'),
            aggregate_success_tasks=dict(tasks=3,cycles=total,average_cycles=total/3.0,task_per_second=450000000.0/total),
            artifacts={name:sha(run/name) for name in ('sequence.log','sequence_command.json','sequence__task1.csv','sequence__task2.csv','sequence__task3.csv')},
            gate_simulation_verified=False,timing_verified=False,system_power_verified=False,official_precision_verified=False)
        save(run/'sequence_result.json',report);return report
    except BaseException as exc:
        save(run/'sequence_failure.json',dict(status='failed',error=str(exc),type=type(exc).__name__,
            scope='ASIC_sequence_attempt',asic_execution_verified=False,frozen_inputs_sha256=frozen_sha))
        raise
