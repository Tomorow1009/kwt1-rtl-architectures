"""New ASIC/E203 compile and run path for compressed ICB32. Python 3.6 only.

One VCS compilation; each task gets a firmware-only boot image whose 16-byte
metadata contains its encoded length. Never import legacy timing/traffic PASS.
The caller owns the original shared server lock throughout this operation.
"""
import json
import re
import time
from pathlib import Path
from server_run import ROOT,A2,A3,sha,save,vendor
from install_platform import platform_sources
from install_g32 import install
from asic_boot import prepare as physical_boot,loader_include,image_bytes
from build_g32_firmware import elf_image,metadata_image,irq_config
from stdcell_verify import extract_model
import n1_data as data
import c80_data
from p80_window import read_window

MARKERS=[
    'ARCH03_ASIC_BOOT_READY bytes=262144 macros=32 scope=initial_ITCM_only',
    'ARCH03_ASIC_MODE_MATCH test_mode=0 pllbypass=1 divider_bypass=1',
    'ARCH03_BOOT_MODE_MATCH bootrom_selected=1 scope=complete_task']


def source_list():
    return [A3/'rtl/arch03_n1_requantize.sv',
        A2/'arch02/rtl/sram_port.sv',A2/'arch02/rtl/sram_macro_adapter.sv']+[
        A3/'rtl'/name for name in ('arch03_g32_systolic2x16.sv','arch03_g32_linear16x2.sv','arch03_g32_accel.sv',
        'arch03_c80_decoder.sv','arch03_g32_transport.sv','arch03_g32_icg.sv','arch03_icb_arb2_queued.sv',
        'arch03_icb_memory_router_turnover.sv','arch03_shared_sram_turnover.sv')]


def verify_firmware(firmware,source_root=ROOT):
    firmware,source_root=Path(firmware),Path(source_root)
    meta=data.read(firmware/'manifest.json')
    data.require(meta.get('run_mode')=='single_cpu_g32_x14_w12_b32_v6' and
        meta.get('physical_boot_policy')=='firmware_only_no_task_inputs','Wrong ICB32 firmware mode')
    cfg=meta['configuration'];rows=cfg['row_lanes']
    data.require(cfg['transaction_metadata_depth']==2,'Wrong P80 metadata depth')
    data.require(cfg['mode']==1 and rows == 2,'Wrong N1 configuration')
    data.require(set(meta['images'])=={'shift_10'},'N1 requires only SHIFT10 boot template')
    expected_id='0x4b57530f'
    data.require(meta['peripheral_id']==expected_id and meta['numeric_layout_id']=='0x%08x'%cfg['default_layout'] and cfg['default_layout']==0x00100006 and meta['supported_layout_ids']==['0x00100006'] and meta['numeric_format']=='0x000e0c20','Wrong ABI identity')
    mapping=cfg['irq_mapping']
    if cfg['irq_enabled']:
        data.require(mapping==irq_config(source_root/'workspaces/arch03/irq_mapping.json'),'IRQ mapping differs')
    else:data.require(mapping is None,'Unexpected IRQ mapping')
    for rel,digest in meta['source_sha256'].items():
        p=(source_root/rel).resolve();p.relative_to(source_root.resolve())
        data.require(sha(p)==digest,'Firmware source changed: '+rel)
    elf=firmware/'driver.elf';data.require(sha(elf)==meta['elf_sha256'],'ELF changed')
    base,segments=elf_image(elf.read_bytes());data.require(segments==meta['segments'],'ELF segment metadata differs')
    for name,record in meta['images'].items():
        data.require(name=='shift_%02d'%record['shift'] and record['row_lanes']==rows and record['layout']==cfg['default_layout'],'Boot template name/rows')
        want=metadata_image(base,record['shift'],record['encoded_bytes'],rows,record['layout'])
        path,binary=firmware/(name+'.verilog'),firmware/(name+'.bin')
        data.require(sha(path)==record['sha256'] and image_bytes(path)==want and
            sha(binary)==record['binary_sha256'] and binary.read_bytes()==want,'Boot template changed')
        data.require(not any(want[0x10000:]) and record['firmware_only'] is True and
            record['task_input_region_nonzero_bytes']==0,'Task data found in boot')
    data.require(meta['images'],'No firmware templates')
    return meta,base


def verify_frozen(contract):
    data.require(contract['schema']=='arch03-g32-asic-build-v6' and
        contract['scope']=='asic_rtl_functional' and contract['global_FPGA_defined'] is False,
        'Not a genuine ASIC ICB32 build contract')
    for role in ('rtl','platform','firmware','monitor','libraries','executable','compile_receipt'):
        data.require(contract['roles'].get(role),'Missing build identity role '+role)
        data.require(all(path in contract['files'] for path in contract['roles'][role]),'Unbound role '+role)
    for path,digest in contract['files'].items():
        data.require(Path(path).is_absolute() and sha(Path(path))==digest,'Frozen input changed: '+path)


def compile_design(cfg,run,platform_source,call,firmware=None,diagnostic=None):
    firmware=(firmware or ROOT/'firmware').resolve();firmware.relative_to(ROOT.resolve())
    fw,base=verify_firmware(firmware)
    platform=run/'platform';manifest=install(platform_source,platform,fw['configuration']['row_lanes'],fw['configuration']['transaction_metadata_depth'])
    data.require(diagnostic in (None,'contention'),'Unknown T80 diagnostic')
    if diagnostic=='contention':
        from g32_contention import verify_firmware as verify_contention
        verify_contention(firmware)
    from g32_bus_metrics import instrument
    generated=run/'arch03_g32_metrics_monitor.svh'
    observer=instrument((A3/'tb/arch03_g32_monitor.svh').read_text(),2)
    if diagnostic=='contention':
        from g32_contention import monitor as contention_monitor
        observer=contention_monitor(observer)
    generated.write_text(observer)
    tb=platform/'tb/tb_top.v';text=tb.read_text()
    data.require(text.count('`include "arch03_g32_monitor.svh"')==1,'Missing B observer include')
    tb.write_text(text.replace('`include "arch03_g32_monitor.svh"','`include "arch03_g32_metrics_monitor.svh"'))
    manifest['modified_files']['tb/tb_top.v']=sha(tb);save(platform/'platform_manifest.json',manifest)
    extra_scripts=[generated,A3/'scripts/g32_bus_metrics.py',A3/'tb/arch03_g32_metrics.svh']
    if diagnostic=='contention':
        extra_scripts += [A3/'scripts/g32_contention.py',A3/'scripts/build_g32_contention.py']
    loader=run/'arch03_asic_boot.svh';loader.write_text(loader_include())
    model=extract_model(cfg,run)
    # Physical TCM still instantiates arch03_sram_half from the original shared
    # file; include that helper implementation as well as the independent new
    # shared-controller implementation. Uninstantiated old controller is unused.
    team=source_list()+[A3/'rtl/arch03_tcm_ram.sv',A3/'rtl/arch03_shared_sram.sv']
    monitors=[A3/'tb'/name for name in ('arch03_task_window_p80.sv','arch03_p80_route_observer.sv','arch03_icb32_source.sv','arch03_clock_mode_guard.sv')]
    libs=[model]+vendor(cfg,run)
    files=platform_sources(platform)+team+monitors+[platform/'tb/tb_top.v']+libs
    includes=list(dict.fromkeys([run,A3/'tb',platform/'rtl/e203/core']+[p.parent for p in files]))
    cmd=[cfg['tools']['vcs'],'-full64','-sverilog','-timescale=1ns/1fs','+define+ARM_UD_MODEL',
         '+define+functional','-top','tb_top','-o',str(run/'simv')]+['+incdir+'+str(p) for p in includes]+files
    save(run/'compile_command.json',[str(x) for x in cmd])
    firmware_files=[p for p in firmware.iterdir() if p.is_file() and p.suffix in ('.elf','.bin','.verilog','.json')]
    firmware_files += [ROOT/rel for rel in fw['source_sha256']]
    if fw['configuration']['irq_enabled']:firmware_files.append(A3/'irq_mapping.json')
    scripts=[A3/'scripts'/name for name in ('g32_soc.py','n1_data.py','n1_codec.py','systolic_b_data.py','icb32_data.py','icb32_codec.py','install_g32.py','install_c80.py','install_p80.py','systolic_b_codec.py',
        'install_icb32.py','install_dma16.py','install_platform.py','asic_boot.py','build_g32_firmware.py','dma16_batch.py',
        'server_run.py','g32_batch.py','c80_data.py','c80_codec.py','c80_codec_candidate.py',
        'timing_contract.py','stdcell_verify.py','technology_binding.py')]
    platform_files=[p for p in platform.rglob('*') if p.is_file()]
    headers=[p for root in (A2,A3) for p in root.rglob('*') if p.is_file() and p.suffix in ('.svh','.vh')]
    scripts+=[A3/'scripts/install_t80.py']
    scripts+=extra_scripts+[A3/'scripts/p80_window.py',A3/'scripts/install_n1.py',A3/'tb/arch03_p80_route_audit.svh']
    tracked=files+firmware_files+scripts+platform_files+headers+[loader,run/'arch02_sram_config.vh']
    before={str(p.resolve()):sha(p) for p in tracked};save(run/'source_inputs.json',before)
    started=time.monotonic();log=call(cmd,run,'compile.log')
    data.require(not re.search(r'Warning-\[(?:IPDW|PCWM-W|INAV|SIOB)\]',log),'VCS declaration/width warning')
    data.require((run/'simv').is_file(),'Missing simulator')
    receipt=dict(status='compiled_only',scope='asic_rtl_functional',cpu_executed=False,
        elapsed_seconds=time.monotonic()-started,global_FPGA_defined=False,task_input_boot_bytes=0,
        row_lanes=fw['configuration']['row_lanes'],platform_baseline_sha256=manifest['baseline_sha256'],
        firmware_manifest_sha256=sha(firmware/'manifest.json'),source_inputs_sha256=sha(run/'source_inputs.json'),
        command_sha256=sha(run/'compile_command.json'),executable_sha256=sha(run/'simv'))
    save(run/'compile_receipt.json',receipt)
    roles=dict(rtl=team,platform=platform_files,firmware=firmware_files,
        monitor=monitors+[A3/'tb/arch03_g32_monitor.svh',loader]+scripts,
        libraries=libs+[run/'arch02_sram_config.vh'],executable=[run/'simv'],
        compile_receipt=[run/'compile_receipt.json',run/'compile_command.json',run/'compile.log',run/'source_inputs.json'])
    frozen=dict(before)
    for paths in roles.values():
        for p in paths:frozen[str(p.resolve())]=sha(p)
    contract=dict(schema='arch03-g32-asic-build-v6',scope='asic_rtl_functional',
        passive_metrics=True,diagnostic=diagnostic,transaction_metadata_depth=fw['configuration']['transaction_metadata_depth'],
        global_FPGA_defined=False,files=frozen,roles={k:sorted(set(str(p.resolve()) for p in v)) for k,v in roles.items()},
        executable=str((run/'simv').resolve()),firmware=str(firmware),row_lanes=fw['configuration']['row_lanes'],
        layout_id=fw['configuration']['default_layout'],lock_directory=str(Path(cfg['server_root'])/'.arch02_team_lock'),clock_period_ns='6.666666',
        boot_policy='per_task_firmware_only_shift_length_metadata',required_markers=MARKERS)
    for path,digest in before.items():data.require(sha(Path(path))==digest,'Compile input changed '+path)
    verify_frozen(contract);save(run/'g32_build_contract.json',contract)
    return contract,receipt,fw,base


def run_case(contract,fw,base,source,run,name,call,activity=False,force_raw=False):
    task=run/(name+'_data');info=c80_data.prepare_case(source,task,force_raw,contract['layout_id'])
    c80_data.verify_prepared(source,task)
    image=metadata_image(base,info['shift'],info['encoded_bytes'],contract['row_lanes'],info['layout'])
    boot_image=run/(name+'_firmware.verilog')
    boot_image.write_bytes(''.join('%02x\n'%value for value in image).encode('ascii'))
    boot=run/(name+'_boot');boot_receipt=physical_boot(boot_image,boot)
    boot_receipt.update(scope='initial_ITCM_firmware_only',encoded_bytes=info['encoded_bytes'],
                        shift=info['shift'],row_lanes=contract['row_lanes'],input_bytes_preloaded=0)
    save(boot/'manifest.json',boot_receipt)
    capture=run/(name+'.csv')
    cmd=[contract['executable'],'+BOOT_DIR='+str(boot.resolve()),'+LOAD32='+str((task/'codec32.hex').resolve()),
        '+CODEC_BYTES='+str(info['encoded_bytes']),'+LAYOUT='+str(info['layout']),'+DATA_DIR='+str(task.resolve()),
        '+CAPTURE='+str(capture.resolve()),'+SHIFT='+str(info['shift'])]
    if activity:cmd+=['+ACTIVITY='+str((run/(name+'.vcd')).resolve())]
    save(run/(name+'_command.json'),cmd)
    started=time.monotonic();text=call(cmd,run,name+'.log');elapsed=time.monotonic()-started
    captured=data.check_capture(capture,task)
    markers=MARKERS+['ARCH03_ICB32_SOURCE_READY words=%d scope=PC_file_only no_ITCM_task_data=true'%(info['encoded_bytes']//4)]
    data.require(text.count('P80_BUS_ROUTE_PASS ')==1, 'Missing original System Bus route proof')
    data.require(text.count('ARCH03_N1_TOTAL_PROOF count=25344 numeric=000e0c20 shift=10 coordinates=unique')==1, 'Missing N1 actual total proof')
    result=data.parse_result(text,captured['saturated'],markers)
    window=read_window(text,result,info['encoded_bytes'])
    metrics=None
    if contract.get('passive_metrics'):
        from g32_bus_metrics import parse_metrics
        metrics=parse_metrics(text,window)
    cpu=re.findall(r'^ARCH03_ICB32_CPU_CYCLES (\d+)$',text,re.M)
    irq=re.findall(r'^ARCH03_ICB32_IRQ_PROOF enabled=(\d+) external=(\d+) timer=(\d+) wfi=(\d+) events=(\d+) unhandled=(\d+)$',text,re.M)
    data.require(len(cpu)==len(irq)==1,'Missing CPU/IRQ completion proof')
    enabled,external,timer,wfi,events,unhandled=map(int,irq[0])
    data.require(enabled==int(fw['configuration']['irq_enabled']),'IRQ mode mismatch')
    if enabled:data.require(external>0 and timer>0 and wfi>0 and events&1 and unhandled==0,'Incomplete IRQ/WFI proof')
    c80_data.verify_prepared(source,task)
    for filename,digest in boot_receipt['files'].items():
        data.require(sha(boot/filename)==digest,'Physical boot changed')
    return dict(case=name,outputs=25344,total_outputs=25344,numeric_format='0x000e0c20',result=result,task_window=window,capture=captured,
        passive_metrics=metrics,
        cpu_cycles=int(cpu[0]),host_elapsed_seconds=elapsed,codec_sha256=sha(task/'codec.json'),
        layout_sha256=sha(task/'layout_manifest.json'),
        boot_manifest_sha256=sha(boot/'manifest.json'),log_sha256=sha(run/(name+'.log')),
        irq_proof=dict(enabled=bool(enabled),external=external,timer=timer,wfi=wfi,events=events,unhandled=unhandled),
        activity_requested=bool(activity),activity_audited=False)


def verify(cfg,run,platform_source,cases,call,activity_cases=(),firmware=None,compile_only=False,diagnostic=None):
    data.require(not activity_cases,'B activity needs the separately verified SAIF path; plain VCD disabled')
    contract,receipt,fw,base=compile_design(cfg,run,platform_source,call,firmware,diagnostic)
    results=[]
    if not compile_only:
        for name in cases:
            data.require(name in data.CASES14,'Unsupported case')
            result=run_case(contract,fw,base,ROOT/'validated_data'/name,run,name,call,name in activity_cases)
            results.append(result);save(run/'case_progress.json',results)
            print('ICB32_ASIC_CASE_PASS',name,'cycles',result['task_window']['cycles'],'host_seconds',result['host_elapsed_seconds'],flush=True)
    verify_frozen(contract)
    return dict(status='compiled_only' if compile_only else 'passed',scope='asic_rtl_functional',
        cpu_executed=bool(results),asic_cpu_verified=bool(results),global_FPGA_defined=False,
        cases=results,compile_receipt=receipt,build_contract_sha256=sha(run/'g32_build_contract.json'),
        gate_simulation_verified=False,timing_verified=False,system_power_verified=False,official_precision_verified=False)
