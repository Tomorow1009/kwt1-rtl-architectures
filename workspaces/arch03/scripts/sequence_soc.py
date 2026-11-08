"""Dedicated real-E203 A/B/A regression; Python 3.6 standard library only.

Uses legacy functional TCM/clock branches, as explicitly reported. This does
not claim ASIC CPU/gate simulation or system-power acceptance.
"""
import importlib.util
import json
import re
import struct
from pathlib import Path
from install_platform import install,platform_sources
from server_run import ROOT,A3,A2,sha,save,source_list,vendor,check_capture,read_task_window
from batch_soc import image_base


def sequence_log(text):
    marker='ARCH03_SOC_SEQUENCE_PASS tasks=3 outputs=76032 cpu_executed=true abort_verified=true timeout_verified=true'
    if text.count(marker)!=1:raise ValueError('Missing/duplicate sequence acceptance')
    entries=re.findall(r'ARCH03_SOC_SEQUENCE_TASK index=(\d+) cycles=(\d+) saturated=(\d+) outputs=25344',text)
    if [int(e[0]) for e in entries]!=[1,2,3]:raise ValueError('Sequence task ordering/count')
    lines=re.findall(r'(?m)^ARCH03_TASK_WINDOW[^\r\n]*',text)
    if len(lines)!=3:raise ValueError('Sequence requires three full-task timing windows')
    windows=[read_task_window(line) for line in lines]
    for i,(entry,window) in enumerate(zip(entries,windows)):
        if not 0<window['cycles']<=int(entry[1]):raise ValueError('Sequence CPU/bus duration mismatch')
        if i and window['start_cycle']<=windows[i-1]['end_cycle']:raise ValueError('Overlapping/reordered sequence windows')
    poison='ARCH03_SEQUENCE_POISON_PASS starts=1 loads=17 aborts=1 output_reads=0'
    if text.count(poison)!=1:raise ValueError('Missing/duplicate poison-abort evidence')
    timeout=re.findall(r'ARCH03_SEQUENCE_TIMEOUT_PASS starts=1 loads=(\d+) aborts=2 rc=-1 output_reads=0',text)
    if len(timeout)!=1 or not 0<int(timeout[0])<23488:raise ValueError('Missing/incomplete actual-driver timeout evidence')
    task_positions=[m.start() for m in re.finditer(r'ARCH03_SOC_SEQUENCE_TASK index=',text)]
    window_positions=[m.start() for m in re.finditer(r'(?m)^ARCH03_TASK_WINDOW',text)]
    ordered=[window_positions[0],task_positions[0],window_positions[1],task_positions[1],
             text.index(poison),text.index('ARCH03_SEQUENCE_TIMEOUT_PASS'),window_positions[2],task_positions[2],text.index(marker)]
    if ordered!=sorted(set(ordered)):raise ValueError('Sequence/recovery evidence order changed')
    return [dict(index=int(e[0]),cycles=int(e[1]),saturated=int(e[2]),task_window=w)
            for e,w in zip(entries,windows)],int(timeout[0])


def verify_firmware(firmware,data,cases):
    manifest=json.loads((firmware/'manifest.json').read_text())
    if manifest.get('run_mode')!='sequence_cpu_v1':raise ValueError('Dedicated sequence firmware is required')
    if len(cases)!=len(set(cases)) or not set(cases).issubset(manifest['images']):raise ValueError('Sequence cases missing/duplicate')
    if sha(firmware/'driver.elf')!=manifest['elf_sha256']:raise ValueError('Sequence ELF changed')
    base=image_base(firmware/'driver.elf')
    for name in cases:
        meta=manifest['images'][name];other=meta['next_case']
        if Path(name).name!=name or Path(other).name!=other or other in ('.','..'):raise ValueError('Invalid sequence case path')
        if meta['tasks']!=[name,other,name]:raise ValueError('Unexpected sequence order')
        memory=bytearray(base)
        for case,offset,shift_offset,hash_key,shift_key in (
                (name,0x10000,0xfff0,'input_sha256','shift'),
                (other,0x20000,0xfff4,'next_input_sha256','next_shift')):
            folder=data/case;layout=json.loads((folder/'layout.json').read_text())
            for filename,digest in layout['sha256'].items():
                if sha(folder/filename)!=digest:raise ValueError('Sequence input snapshot changed')
            if sha(folder/'load.hex')!=meta[hash_key] or layout['shift']!=meta[shift_key]:raise ValueError('Sequence input/scale changed')
            words=[int(x,16) for x in (folder/'load.hex').read_text().split()]
            if len(words)!=23488 or any(not 0<=v<=65535 for v in words):raise ValueError('Bad sequence packet')
            struct.pack_into('<I',memory,shift_offset,layout['shift']);struct.pack_into('<23488H',memory,offset,*words)
        image=firmware/(name+'.verilog')
        if sha(image)!=meta['sha256']:raise ValueError('Sequence boot image changed')
        if bytes(int(x,16) for x in image.read_text().split())!=memory:raise ValueError('Sequence boot image payload/layout mismatch')
    return manifest


def verify(cfg,run,platform_source,cases,call):
    firmware=ROOT/'firmware';data=ROOT/'validated_data'
    manifest=verify_firmware(firmware,data,cases)
    spec=importlib.util.spec_from_file_location('sequence_reference',A2/'vcs_run.py')
    reference=importlib.util.module_from_spec(spec);spec.loader.exec_module(reference)
    names=set(case for name in cases for case in manifest['images'][name]['tasks'])
    for name in sorted(names):reference.reference(data/name)
    platform=run/'platform';install(platform_source,platform,monitor='arch03_sequence_monitor.svh')
    files=platform_sources(platform)+source_list()+[A3/'tb/arch03_task_window.sv',platform/'tb/tb_top.v']+vendor(cfg,run)
    includes=list(dict.fromkeys([run,A3/'tb',platform/'rtl/e203/core']+[p.parent for p in files]))
    tracked=files+[A3/'tb/arch03_sequence_monitor.svh',run/'arch02_sram_config.vh',firmware/'manifest.json']
    tracked += [p for p in platform.rglob('*') if p.is_file()]
    before={str(p):sha(p) for p in tracked};save(run/'source_inputs.json',before)
    cmd=[cfg['tools']['vcs'],'-full64','-sverilog','-timescale=1ns/1ps','+define+FPGA','+define+ARM_UD_MODEL',
         '-top','tb_top','-o',str(run/'simv')]+['+incdir+'+str(p) for p in includes]+files
    log=call(cmd,run,'compile.log')
    if re.search(r'Warning-\[(?:IPDW|PCWM-W|INAV|SIOB)\]',log):raise ValueError('Sequence VCS width/declaration warning')
    results=[]
    for name in cases:
        meta=manifest['images'][name]
        text=call([run/'simv','+TESTCASE='+str(firmware/name),'+DATA_DIR='+str(data/name),
                   '+SECOND_DIR='+str(data/meta['next_case']),'+CAPTURE_PREFIX='+str(run/name)],run,name+'.log')
        entries,timeout_loads=sequence_log(text)
        for index,(entry,case) in enumerate(zip(entries,meta['tasks']),1):
            capture=run/(name+'__task%d.csv'%index)
            checked=check_capture(capture,data/case,2)
            sats=sum(int(x,16) for x in (data/case/'saturated.hex').read_text().split())
            if entry['saturated']!=sats:raise ValueError('Sequence saturation counter mismatch')
            entry.update(case=case,capture=capture.name,**checked)
        results.append(dict(primary_case=name,tasks=entries,timeout_loads=timeout_loads,
                            log_sha256=sha(run/(name+'.log')),firmware_sha256=sha(firmware/(name+'.verilog'))))
        print('SEQUENCE_CASE_PASS',name,flush=True)
    for path,digest in before.items():
        if sha(Path(path))!=digest:raise ValueError('Sequence compile input changed')
    return dict(status='passed',cpu_executed=True,scope='real_cpu_consecutive_and_recovery_functional_tcm',
                cases=results,tasks=3*len(results),outputs=76032*len(results),reset_between_tasks=False,
                poison_abort_verified=True,actual_driver_timeout_verified=True,
                asic_cpu_verified=False,gate_simulation_verified=False,system_power_verified=False)
