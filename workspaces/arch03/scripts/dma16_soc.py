"""Real ASIC E203 DMA16 build/run, with program-only physical ITCM boot.

No FPGA define, task-data ITCM preload, or expected-answer injection. The
existing server_run owns the shared lock for this build/small suite. A later
standalone dma16_batch invocation owns that same lock for the frozen batch.
Python 3.6 standard library only.
"""
import json
import re
import time
from decimal import Decimal
from pathlib import Path
from server_run import ROOT, A2, A3, sha, save, vendor
from install_platform import platform_sources
from install_dma16 import install
from asic_boot import prepare, loader_include, image_bytes
from build_dma16_firmware import elf_image, metadata_image, irq_config
from stdcell_verify import extract_model
import dma16_batch as batch

MARKERS = [
    'ARCH03_ASIC_BOOT_READY bytes=262144 macros=32 scope=initial_ITCM_only',
    'ARCH03_ASIC_MODE_MATCH test_mode=0 pllbypass=1 divider_bypass=1',
    'ARCH03_BOOT_MODE_MATCH bootrom_selected=1 scope=complete_task',
    'ARCH03_DMA16_SOURCE_READY words=11744 scope=PC_file_only no_ITCM_task_data=true']


def source_list():
    return [A2/'rtl/requantize.sv', A2/'rtl/dot64.sv',
            A2/'arch02/rtl/sram_port.sv', A2/'arch02/rtl/sram_macro_adapter.sv']+[
            A3/'rtl'/n for n in ('arch03_linear16.sv', 'arch03_dma16_accel.sv',
                'arch03_icb_arb2.sv', 'arch03_icb_memory_router.sv', 'arch03_shared_sram.sv')]


def verify_firmware(firmware, source_root=ROOT):
    firmware=Path(firmware); source_root=Path(source_root)
    manifest=batch.read(firmware/'manifest.json')
    batch.require(manifest.get('run_mode')=='single_cpu_dma16_v1' and
                  manifest.get('physical_boot_policy')=='firmware_only_no_task_inputs', 'Wrong DMA16 firmware mode')
    batch.require(manifest['configuration']['mode']==1, 'DMA16 monitor requires DMA firmware')
    mapping=manifest['configuration'].get('irq_mapping')
    if manifest['configuration']['irq_enabled']:
        mapping_path=source_root/'workspaces/arch03/irq_mapping.json'
        batch.require(mapping is not None and irq_config(mapping_path)==mapping,'IRQ build mapping differs from frozen platform mapping')
    else:
        batch.require(mapping is None,'Polling firmware unexpectedly carries an IRQ mapping')
    for rel,digest in manifest['source_sha256'].items():
        p=(source_root/rel).resolve();p.relative_to(source_root.resolve())
        batch.require(sha(p)==digest,'Firmware source changed: '+rel)
    elf=firmware/'driver.elf'
    batch.require(sha(elf)==manifest['elf_sha256'],'Firmware ELF changed')
    base,segments=elf_image(elf.read_bytes())
    batch.require(segments==manifest['segments'],'Firmware segment metadata changed')
    shifts={}
    for name,meta in manifest['images'].items():
        shift=meta['shift']
        batch.require(name=='shift_%02d'%shift and shift not in shifts,'Firmware shift name/duplicate')
        path=firmware/(name+'.verilog');binary=firmware/(name+'.bin')
        wanted=metadata_image(base,shift)
        batch.require(sha(path)==meta['sha256'] and image_bytes(path)==wanted and
                      sha(binary)==meta['binary_sha256'] and binary.read_bytes()==wanted,'Firmware boot bytes changed')
        batch.require(not any(wanted[0x10000:]) and meta['firmware_only'] is True and
                      meta['task_input_region_nonzero_bytes']==0,'Task data entered ITCM boot')
        shifts[shift]=path
    batch.require(shifts,'Missing firmware images')
    return manifest,shifts


def read_window(text,result):
    lines=[s for s in text.splitlines() if s.startswith('DMA16_TASK_WINDOW ')]
    batch.require(len(lines)==1,'Expected unique complete DMA16 task window')
    fields=dict(re.findall(r'(\w+)=([^ ]+)',lines[0]))
    for key,value in dict(finished=1,failed=0,failure_code=0,source_bytes=46976,
                          input_write_bytes=46976,input_read_bytes=46976,output_bytes=50688).items():
        batch.require(int(fields[key])==value,'Invalid window '+key)
    start,end,cycles=[int(fields[k]) for k in ('start_cycle','end_cycle','cycles')]
    batch.require((start,end,cycles)==(result['first_request_cycle'],result['final_response_cycle'],result['cycles']),
                  'Batch/window cycle mismatch')
    t0,t1=Decimal(fields['start_ns']),Decimal(fields['end_ns'])
    batch.require(abs(t1-t0-Decimal(cycles)*Decimal('6.666666'))<=Decimal('0.000002'),
                  'Window time/cycle mismatch')
    batch.require(int(fields['finished_cycle'])>=end and Decimal(fields['finished_ns'])>=t1,'Drain proof precedes final ACK')
    return dict(start_cycle=start,end_cycle=end,cycles=cycles,start_ns=str(t0),end_ns=str(t1),
                period_ns='6.666666',finished_cycle=int(fields['finished_cycle']),finished_ns=fields['finished_ns'],
                boundary='first_source_valid_to_final_write_response_ack_with_drain_proof',
                transfer_bytes=191616,task_per_second=150000000.0/cycles,
                mmac_per_second=1622016.0*150.0/cycles)


def compile_design(cfg,run,platform_source,call,firmware=None):
    firmware=(firmware or ROOT/'firmware').resolve();firmware.relative_to(ROOT.resolve())
    fw,images=verify_firmware(firmware)
    platform=run/'platform';manifest=install(platform_source,platform)
    loader=run/'arch03_asic_boot.svh';loader.write_text(loader_include())
    model=extract_model(cfg,run)
    team=source_list()+[A3/'rtl/arch03_tcm_ram.sv']
    monitors=[A3/'tb'/n for n in ('arch03_task_window16.sv','arch03_dma16_source.sv','arch03_clock_mode_guard.sv')]
    libs=[model]+vendor(cfg,run)
    files=platform_sources(platform)+team+monitors+[platform/'tb/tb_top.v']+libs
    includes=list(dict.fromkeys([run,A3/'tb',platform/'rtl/e203/core']+[p.parent for p in files]))
    cmd=[cfg['tools']['vcs'],'-full64','-sverilog','-timescale=1ns/1fs','+define+ARM_UD_MODEL',
         '+define+functional','-top','tb_top','-o',str(run/'simv')]+['+incdir+'+str(p) for p in includes]+files
    save(run/'compile_command.json',[str(p) for p in cmd])
    tracked=files+[loader,A3/'tb/arch03_dma16_monitor.svh',run/'arch02_sram_config.vh',firmware/'manifest.json']
    tracked += [p for p in platform.rglob('*') if p.is_file()]
    tracked += [p for p in firmware.iterdir() if p.is_file() and p.suffix in ('.elf','.bin','.verilog')]
    firmware_sources=[ROOT/rel for rel in fw['source_sha256']]
    if fw['configuration']['irq_enabled']:firmware_sources.append(A3/'irq_mapping.json')
    tracked += firmware_sources
    # Freeze all transitive team headers and preparation scripts, not only .sv arguments.
    tracked += [p for base in (A2,A3) for p in base.rglob('*') if p.is_file() and p.suffix in ('.vh','.svh')]
    tracked += [A3/'scripts'/n for n in ('install_platform.py','install_dma16.py','asic_boot.py',
        'build_dma16_firmware.py','dma16_soc.py','dma16_batch.py','timing_contract.py','stdcell_verify.py')]
    before={str(p.resolve()):sha(p) for p in tracked};save(run/'source_inputs.json',before)
    started=time.monotonic();log=call(cmd,run,'compile.log')
    if re.search(r'Warning-\[(?:IPDW|PCWM-W|INAV|SIOB)\]',log):
        raise ValueError('DMA16 VCS declaration/width warning requires review')
    batch.require((run/'simv').is_file(),'Missing DMA16 simulator')
    boot_by_shift={};boot_files=[]
    for shift,image in sorted(images.items()):
        boot=run/('boot_shift_%02d'%shift);receipt=prepare(image,boot)
        # Existing converter maps bytes only. Update its description for this
        # strictly program-only use; no source/input data are initialized.
        receipt['scope']='initial_ITCM_firmware_only';receipt['runtime_task_loading']='DMA_original_SysMem_ICB'
        save(boot/'manifest.json',receipt)
        boot_by_shift[str(shift)]=str(boot.resolve());boot_files += list(boot.iterdir())
    receipt=dict(status='compiled_only',scope='asic_rtl_functional',cpu_executed=False,
        elapsed_seconds=time.monotonic()-started,global_FPGA_defined=False,
        platform_baseline_sha256=manifest['baseline_sha256'],firmware_sha256=sha(firmware/'manifest.json'),
        source_inputs_sha256=sha(run/'source_inputs.json'),command_sha256=sha(run/'compile_command.json'),
        executable_sha256=sha(run/'simv'),input_task_bytes_in_boot=0)
    save(run/'compile_receipt.json',receipt)
    roles=dict(executable=[run/'simv'],rtl=team,platform=[p for p in platform.rglob('*') if p.is_file()],
        firmware=[p for p in firmware.iterdir() if p.is_file() and p.suffix in ('.elf','.bin','.verilog','.json')]+firmware_sources,
        boot=boot_files,monitor=monitors+[A3/'tb/arch03_dma16_monitor.svh',loader],
        timing=[A3/'scripts/timing_contract.py',A3/'tb/arch03_task_window16.sv'],
        layout=[A3/'scripts/dma16_batch.py',A3/'scripts/dma16_layout.py'],libraries=libs+[run/'arch02_sram_config.vh'],
        compile_receipt=[run/'compile_receipt.json',run/'compile_command.json',run/'source_inputs.json',run/'compile.log'])
    frozen=dict(before)
    for paths in roles.values():
        for p in paths:frozen[str(p.resolve())]=sha(p)
    contract=dict(schema=batch.SCHEMA,mode='hardware',scope='asic_rtl_functional',timing=batch.TIMING,
        boot_scope='firmware_only_no_task_inputs',timeout_seconds=600,
        lock_directory=str(Path(cfg['server_root'])/'.arch02_team_lock'),
        command_prefix=[str((run/'simv').resolve())],extra_args=[],boot_by_shift=boot_by_shift,
        files=frozen,roles={k:sorted(set(str(p.resolve()) for p in v)) for k,v in roles.items()},
        required_log_markers=MARKERS,build_assertions=dict(actual_asic_models=True,global_FPGA_defined=False,
            firmware_only_physical_boot=True,task_data_preloaded=False,compile_inputs_complete=True))
    batch.validate_contract(contract);save(run/'batch_contract.json',contract)
    for p,digest in before.items():batch.require(sha(Path(p))==digest,'Compile input changed: '+p)
    return contract,receipt,fw


def verify(cfg,run,platform_source,cases,call,activity_cases=(),firmware=None,compile_only=False):
    batch.require(not set(activity_cases)-set(cases),'Unselected DMA16 activity case')
    contract,receipt,fw=compile_design(cfg,run,platform_source,call,firmware)
    results=[]
    if not compile_only:
        for name in cases:
            batch.require(re.fullmatch(r'layer_(?:0[1-9]|1[0-2])|extremes|rounding',name),'Invalid DMA16 case')
            source=ROOT/'validated_data'/name;task=run/(name+'_data')
            info=batch.prepare_case(source,task);batch.verify_prepared(source,task)
            capture=run/(name+'.csv');cmd=batch.command_for(contract,task,capture,info['shift'])
            if name in activity_cases:cmd+=['+ACTIVITY='+str(run/(name+'.vcd'))]
            save(run/(name+'_command.json'),cmd)
            started=time.monotonic();text=call(cmd,run,name+'.log');elapsed=time.monotonic()-started
            captured=batch.check_capture(capture,task)
            result=batch.parse_result(text,captured['saturated'],MARKERS)
            window=read_window(text,result)
            cpu=re.findall(r'^ARCH03_DMA16_CPU_CYCLES (\d+)$',text,re.M)
            batch.require(len(cpu)==1,'Missing CPU cycle cross-check')
            irq=re.findall(r'^ARCH03_DMA16_IRQ_PROOF enabled=(\d+) external=(\d+) timer=(\d+) wfi=(\d+) events=(\d+) unhandled=(\d+)$',text,re.M)
            batch.require(len(irq)==1,'Missing IRQ proof counters')
            enabled,external,timer,wfi,events,unhandled=map(int,irq[0])
            batch.require(enabled==int(fw['configuration']['irq_enabled']),'Firmware IRQ mode differs from actual mailbox')
            if enabled:
                batch.require(external>0 and timer>0 and wfi>0 and events&1 and unhandled==0,'Incomplete actual IRQ/WFI proof')
            item=dict(case=name,outputs=25344,result=result,task_window=window,capture=captured,
                      cpu_cycles=int(cpu[0]),host_elapsed_seconds=elapsed,layout_sha256=sha(task/'layout_manifest.json'),
                      irq_proof=dict(enabled=bool(enabled),external=external,timer=timer,wfi=wfi,events=events,unhandled=unhandled))
            if not fw['configuration']['irq_enabled']:
                batch.require(item['cpu_cycles']>=result['cycles'],'Polling CPU interval does not enclose task')
            if name in activity_cases:
                from activity_fast import audit_activity
                item['activity']=audit_activity(run/(name+'.vcd'),window,run,call)
            batch.validate_contract(contract);batch.verify_prepared(source,task)
            results.append(item);save(run/'case_progress.json',results)
            print('DMA16_ASIC_CASE_PASS',name,'cycles',result['cycles'],'host_seconds',elapsed,flush=True)
    return dict(status='compiled_only' if compile_only else 'passed',scope='asic_rtl_functional',
                cpu_executed=bool(results),asic_cpu_verified=bool(results),global_FPGA_defined=False,
                cases=results,compile_receipt=receipt,batch_contract_sha256=sha(run/'batch_contract.json'),
                gate_simulation_verified=False,timing_verified=False,system_power_verified=False,
                official_precision_verified=False)
