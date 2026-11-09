"""Real MMIO8 source/shared/core fixture; bus initiator is NOT an E203 CPU."""
import argparse
import json
import re
import subprocess
from datetime import datetime
from decimal import Decimal
from pathlib import Path
import numpy as np
from local_verify import A2,A3,ROOT,run,sha


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--vivado-bin',required=True,type=Path)
    parser.add_argument('--data',required=True,type=Path)
    parser.add_argument('--cases',nargs='+',default=['layer_01','extremes','rounding'])
    args=parser.parse_args();data=args.data.resolve()
    folder=ROOT/'local_runs'/('mmio8_source_fixture_'+datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    folder.mkdir(parents=True)
    files=[A2/'rtl/requantize.sv',A2/'rtl/dot64.sv',A2/'arch02/rtl/sram_port.sv',
           A2/'arch02/rtl/sram_macro_adapter.sv',A2/'arch02/tb/pin_mock.sv',A2/'arch02/rtl/arch02_linear.sv',
           A3/'rtl/arch03_icb_accel.sv',A3/'rtl/arch03_icb_arb2.sv',A3/'rtl/arch03_icb_memory_router.sv',
           A3/'rtl/arch03_shared_sram.sv',A3/'tb/arch03_dma16_source.sv',A3/'tb/tb_arch03_mmio8_source_fixture.sv']
    cfg_path=A2/'arch02/tb/pin_mock_config.json';cfg=json.loads(cfg_path.read_text());lines=[]
    for size in ('128','4096'):
        for key,width in [('cen_low',1),('gwen_low',1),('wen_low',1),('ema',3),('emaw',2),('ret1n',1)]:
            lines.append("`define A02_%s_%s %d'd%d"%(size,key.upper(),width,cfg['macros'][size][key]))
    config=folder/'arch02_sram_config.vh';config.write_text('\n'.join(lines)+'\n')
    hashes={p:sha(p) for p in files+[cfg_path,config,A3/'tb/arch03_mmio8_source_monitor.svh',Path(__file__).resolve()]}
    data_hashes={}
    for case in args.cases:
        task=data/case;layout=json.loads((task/'layout_manifest.json').read_text())
        for name,digest in layout['sha256'].items():
            if sha(task/name)!=digest:raise ValueError('Input changed: '+case+'/'+name)
            data_hashes[task/name]=digest
        data_hashes[task/'layout_manifest.json']=sha(task/'layout_manifest.json')
    tool=lambda name:args.vivado_bin/(name+'.bat')
    run([tool('xvlog'),'--sv','-d','ARCH02_PIN_MOCK','-i',folder,'-i',A3/'tb']+files,folder,'compile.log')
    run([tool('xelab'),'tb_arch03_mmio8_source_fixture','-debug','typical','-s','fixture'],folder,'elaborate.log')
    (folder/'run.tcl').write_text('run all\nquit\n')
    negative_results=[]
    task=data/args.cases[0];layout=json.loads((task/'layout_manifest.json').read_text())
    descriptions={1:'idle_status_without_clear',2:'clear_without_fresh_status',
                  3:'replacement_clear_response_not_acked',4:'reset_invalidates_old_certificate',
                  5:'reset_during_armed_task',6:'start_consumes_idle_certificate'}
    for number,description in sorted(descriptions.items()):
        tag='negative_%d'%number;capture=folder/(tag+'.csv');options=folder/(tag+'.options')
        options.write_text('fixture\n-tclbatch run.tcl\n-testplusarg DATA_DIR=%s\n-testplusarg LOAD32=%s\n-testplusarg CAPTURE=%s\n-testplusarg SHIFT=%d\n-testplusarg NEGATIVE=%d\n'%(
            task.as_posix(),(task/'load32.hex').as_posix(),capture.as_posix(),layout['shift'],number))
        path=folder/(tag+'.log')
        with path.open('w',encoding='utf8') as output:
            process=subprocess.run([str(tool('xsim')),'-f',str(options)],cwd=str(folder),stdout=output,stderr=subprocess.STDOUT,timeout=120)
        log=path.read_text(errors='replace')
        expected='MMIO8 reset during armed or active task' if number==5 else 'MMIO8 invalid arm: successful clear ACK and fresh idle STATUS required'
        if ('MMIO8_CLEAR_NEGATIVE_START case='+str(number)) not in log or not re.search(r'(?im)^Fatal:\s*'+re.escape(expected),log):
            raise ValueError('Expected clear/reset rejection missing: '+str(path))
        if 'ARCH03_MMIO8_SOURCE_PASS' in log or 'MMIO8_NEGATIVE_NOT_REJECTED' in log:
            raise ValueError('Negative clear test unexpectedly accepted')
        idle_observations=log.count('MMIO8_CLEAR_NEGATIVE_IDLE_STATUS value=00000000')
        required_idle=0 if number==2 else (2 if number==4 else 1)
        if idle_observations!=required_idle:raise ValueError('Negative test did not prove expected zero STATUS reads')
        negative_results.append(dict(case=number,description=description,status='expected_rejection',
                                     idle_status_observations=idle_observations,
                                     process_exit=process.returncode,log_sha256=sha(path)))
        print('PASS MMIO8 expected rejection '+description,flush=True)
    results=[]
    for case in args.cases:
        task=data/case;layout=json.loads((task/'layout_manifest.json').read_text());capture=folder/(case+'.csv')
        options=folder/(case+'.options')
        options.write_text('fixture\n-tclbatch run.tcl\n-testplusarg DATA_DIR=%s\n-testplusarg LOAD32=%s\n-testplusarg CAPTURE=%s\n-testplusarg SHIFT=%d\n'%(
            task.as_posix(),(task/'load32.hex').as_posix(),capture.as_posix(),layout['shift']))
        log=run([tool('xsim'),'-f',options],folder,case+'.log')
        if 'MMIO8_SOURCE_FIXTURE_NO_CPU' not in log or 'MMIO8_SOURCE_FIXTURE_READY cpu_executed=false dma_executed=false' not in log:
            raise ValueError('Missing no-CPU fixture scope')
        accepted=re.findall(r'^ARCH03_MMIO8_SOURCE_PASS (.+)$',log,re.M)
        windows=re.findall(r'^MMIO8_SOURCE_WINDOW (.+)$',log,re.M)
        if len(accepted)!=1 or len(windows)!=1:raise ValueError('Missing MMIO8 source monitor acceptance')
        window=dict(x.split('=') for x in windows[0].split());cycles=int(window['cycles'])
        if cycles!=int(window['end_cycle'])-int(window['start_cycle']):raise ValueError('Cycle arithmetic mismatch')
        if Decimal(window['end_ns'])-Decimal(window['start_ns'])!=cycles*Decimal('6.666666'):
            raise ValueError('Clock/event timestamp mismatch')
        for key,count in [('source_read_acks',11744),('input_write_acks',11744),('input_read_acks',23488),('output_write_acks',25344)]:
            if int(window[key])!=count:raise ValueError('MMIO8 transaction count mismatch '+key)
        actual=np.loadtxt(str(capture),delimiter=',',dtype=np.int64,ndmin=2)
        indexes=actual[:,0]*256+actual[:,1]
        if actual.shape!=(25344,4) or not np.array_equal(np.sort(indexes),np.arange(25344)):raise ValueError('Coordinates incomplete')
        ordered=actual[np.argsort(indexes)]
        with np.load(str(task/'expected.npz'),allow_pickle=False) as expected:
            if not np.array_equal(ordered[:,2],expected['result'].ravel()) or not np.array_equal(ordered[:,3],expected['saturated'].ravel()):
                raise ValueError('MMIO8 output mismatch')
        results.append(dict(case=case,outputs=25344,cycles=cycles,window=window,capture_sha256=sha(capture)))
        print('PASS MMIO8 source fixture '+case+' cycles='+str(cycles),flush=True)
    for path,digest in hashes.items():
        if sha(path)!=digest:raise ValueError('Source changed during run: '+str(path))
    for path,digest in data_hashes.items():
        if sha(path)!=digest:raise ValueError('Data changed during run: '+str(path))
    report=dict(status='passed',scope='original_mmio8_real_source_shared_and_core_procedural_CPU_bus_no_E203',
                cpu_executed=False,dma_executed=False,backend='pin_mock',tasks=len(results),outputs=len(results)*25344,
                production_monitor_cpu_flag_in_fixture_is_not_evidence=True,
                instruction_timing_modeled=False,clock_period_fs=6666666,cases=results,
                clear_reset_negative_cases=negative_results,
                source_sha256={p.relative_to(ROOT).as_posix():h for p,h in hashes.items()},
                data_sha256={p.relative_to(ROOT).as_posix():h for p,h in data_hashes.items()})
    (folder/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
    print('LOCAL_MMIO8_SOURCE_FIXTURE_PASS '+str(folder),flush=True)


if __name__=='__main__':main()
