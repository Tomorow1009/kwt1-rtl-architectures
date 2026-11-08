"""ASIC-bound RTL E203 simulation with actual SRAM and standard-cell models.

No FPGA define. This is functional RTL, not synthesized gates or timing/power
acceptance. Initial ITCM preload supplies firmware/source bytes only; CPU loads
shared memory and the accelerator and writes every output during the task.
"""
import importlib.util
import json
import re
import struct
from pathlib import Path
from asic_boot import prepare,loader_include,image_bytes
from install_platform import install,platform_sources
from stdcell_verify import extract_model
from server_run import ROOT,A2,A3,sha,save,source_list,vendor,check_capture,read_task_window
from batch_soc import image_base


def verify_images(firmware,data,cases):
    manifest=json.loads((firmware/'manifest.json').read_text())
    if manifest.get('run_mode')!='single_cpu_v2':raise ValueError('ASIC SoC requires single-task firmware')
    if not cases or len(cases)!=len(set(cases)) or not set(cases).issubset(manifest['images']):
        raise ValueError('ASIC cases missing or duplicate')
    if sha(firmware/'driver.elf')!=manifest['elf_sha256']:raise ValueError('ASIC firmware ELF changed')
    base=image_base(firmware/'driver.elf')
    for case in cases:
        if not re.fullmatch(r'layer_(?:0[1-9]|1[0-2])|extremes|rounding|worst_error|largest_input|largest_output|zero|shift00|shift31|cancellation',case):
            raise ValueError('Invalid ASIC case name')
        meta=manifest['images'][case];task=data/case
        layout=json.loads((task/'layout.json').read_text())
        for name,digest in layout['sha256'].items():
            if sha(task/name)!=digest:raise ValueError('ASIC vector changed')
        if sha(task/'load.hex')!=meta['input_sha256'] or layout['shift']!=meta['shift']:
            raise ValueError('ASIC firmware input/shift changed')
        words=[int(x,16) for x in (task/'load.hex').read_text().split()]
        if len(words)!=23488 or any(not 0<=x<65536 for x in words):raise ValueError('Invalid ASIC load packet')
        memory=bytearray(base)
        struct.pack_into('<I',memory,0xfff0,layout['shift']);struct.pack_into('<23488H',memory,0x10000,*words)
        image=firmware/(case+'.verilog')
        if sha(image)!=meta['sha256'] or image_bytes(image)!=memory:raise ValueError('ASIC boot image layout mismatch')
    return manifest


def boot_test(cfg,run,call):
    image=run/'source.verilog'
    image.write_text(''.join('%02x\n'%((i*37+(i>>8)*13+(i>>16)*19)&255) for i in range(262144)))
    prepared=prepare(image,run/'boot')
    (run/'arch03_asic_boot.svh').write_text(loader_include())
    files=[A3/'rtl/arch03_shared_sram.sv',A3/'rtl/arch03_tcm_ram.sv',A3/'tb/tb_arch03_asic_boot.sv']+vendor(cfg,run)
    tracked=files+[A3/'scripts/asic_boot.py',run/'arch03_asic_boot.svh',run/'arch02_sram_config.vh',image]
    tracked += list((run/'boot').iterdir())
    before={str(p):sha(p) for p in tracked};save(run/'source_inputs.json',before)
    cmd=[cfg['tools']['vcs'],'-full64','-sverilog','+define+ARM_UD_MODEL','+define+ARCH03_VENDOR_BOOT_TEST',
         '+incdir+'+str(run),'-top','tb_arch03_asic_boot','-o',str(run/'simv')]+files
    compiled=call(cmd,run,'compile.log')
    if re.search(r'Warning-\[(?:IPDW|PCWM-W|INAV|SIOB)\]',compiled):raise ValueError('Boot VCS width/declaration warning')
    text=call([run/'simv','+BOOT_DIR='+str(run/'boot'),'+IMAGE='+str(image)],run,'boot.log')
    marker='ARCH03_BOOT_MAPPING_PASS bytes=262144 words=32768 macros=32 cpu_executed=false vendor_verified=true'
    if text.count(marker)!=1:raise ValueError('Actual vendor boot mapping test did not complete')
    for path,digest in before.items():
        if sha(Path(path))!=digest:raise ValueError('Boot test input changed')
    return dict(status='passed',scope='vendor_functional_boot_mapping',cpu_executed=False,vendor_verified=True,
                bytes=262144,words=32768,macros=32,timing_verified=False,
                preparation=prepared,artifacts={p.name:sha(p) for p in run.iterdir() if p.is_file()})


def verify(cfg,run,platform_source,cases,call,activity_cases=()):
    if not set(activity_cases).issubset(cases):raise ValueError('Unselected ASIC activity case')
    data=ROOT/'validated_data';firmware=ROOT/'firmware'
    verify_images(firmware,data,cases)
    spec=importlib.util.spec_from_file_location('asic_reference',A2/'vcs_run.py')
    reference=importlib.util.module_from_spec(spec);spec.loader.exec_module(reference)
    for name in cases:reference.reference(data/name)
    platform=run/'platform';manifest=install(platform_source,platform,asic=True,asic_boot=True)
    loader=run/'arch03_asic_boot.svh';loader.write_text(loader_include())
    model=extract_model(cfg,run)
    files=platform_sources(platform)+source_list()+[A3/'rtl/arch03_tcm_ram.sv',A3/'tb/arch03_task_window.sv',A3/'tb/arch03_clock_mode_guard.sv',platform/'tb/tb_top.v',model]+vendor(cfg,run)
    includes=list(dict.fromkeys([run,A3/'tb',platform/'rtl/e203/core']+[p.parent for p in files]))
    tracked=files+[loader,A3/'tb/arch03_monitor.svh',run/'arch02_sram_config.vh',firmware/'manifest.json']
    tracked += [p for p in platform.rglob('*') if p.is_file()]
    before={str(p):sha(p) for p in tracked};save(run/'source_inputs.json',before)
    # Official platform modules have no timescale; a default is required when
    # mixed with explicit team/vendor units. TB's explicit 1 fs precision stays.
    cmd=[cfg['tools']['vcs'],'-full64','-sverilog','-timescale=1ns/1fs','+define+ARM_UD_MODEL','+define+functional',
         '-top','tb_top','-o',str(run/'simv')]+['+incdir+'+str(p) for p in includes]+files
    compiled=call(cmd,run,'compile.log')
    if re.search(r'Warning-\[(?:IPDW|PCWM-W|INAV|SIOB)\]',compiled):raise ValueError('ASIC VCS width/declaration warning')
    results=[]
    for name in cases:
        task=data/name;image=firmware/(name+'.verilog');boot=run/(name+'_boot')
        prepared=prepare(image,boot)
        capture=run/(name+'.csv');layout=json.loads((task/'layout.json').read_text())
        cmd=[run/'simv','+TESTCASE='+str(firmware/name),'+BOOT_DIR='+str(boot),
             '+DATA_DIR='+str(task),'+CAPTURE='+str(capture),'+SHIFT='+str(layout['shift'])]
        if name in activity_cases:cmd+=['+ACTIVITY='+str(run/(name+'.vcd'))]
        text=call(cmd,run,name+'.log')
        marker='ARCH03_ASIC_BOOT_READY bytes=262144 macros=32 scope=initial_ITCM_only'
        if text.count(marker)!=1:raise ValueError('Missing/duplicate ASIC boot evidence')
        if text.count('ARCH03_ASIC_MODE_MATCH test_mode=0 pllbypass=1 divider_bypass=1')!=1:
            raise ValueError('Missing/duplicate actual ASIC task clock-mode evidence')
        if text.count('ARCH03_BOOT_MODE_MATCH bootrom_selected=1 scope=complete_task')!=1:
            raise ValueError('Missing/duplicate actual ASIC task boot-mode evidence')
        matches=re.findall(r'ARCH03_SOC_PASS outputs=25344 cpu_executed=true cycles=(\d+) saturated=(\d+)',text)
        if len(matches)!=1:raise ValueError('ASIC CPU task did not complete uniquely')
        cycles,sats=map(int,matches[0]);window=read_task_window(text)
        if not 0<window['cycles']<=cycles:raise ValueError('ASIC CPU/window cycle mismatch')
        if sats!=sum(int(x,16) for x in (task/'saturated.hex').read_text().split()):raise ValueError('ASIC saturation mismatch')
        result=dict(case=name,cycles=cycles,saturated=sats,task_window=window,boot=prepared,**check_capture(capture,task,2))
        if name in activity_cases:
            activity=run/(name+'.vcd')
            if not activity.is_file() or not activity.stat().st_size:raise ValueError('Missing ASIC system activity')
            from activity_fast import audit_activity
            result['activity']=audit_activity(activity,window,run,call)
        for filename,digest in prepared['files'].items():
            if sha(boot/filename)!=digest:raise ValueError('ASIC boot payload changed')
        results.append(result);print('ASIC_CPU_CASE_PASS',name,flush=True)
    for path,digest in before.items():
        if sha(Path(path))!=digest:raise ValueError('ASIC SoC compile input changed')
    return dict(status='passed',scope='asic_bound_RTL_functional',cpu_executed=True,asic_cpu_verified=True,
                global_FPGA_defined=False,vendor_models='ARM_UD_MODEL and standard-cell functional',cases=results,
                platform_baseline_sha256=manifest['baseline_sha256'],
                gate_simulation_verified=False,timing_verified=False,system_power_verified=False)
