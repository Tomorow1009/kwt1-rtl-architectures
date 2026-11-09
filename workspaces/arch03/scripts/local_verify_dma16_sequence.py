"""Real DMA16 ten-phase bus sequence, no CPU/trap/instruction execution."""
import argparse
import json
import re
import subprocess
from datetime import datetime
from decimal import Decimal
from pathlib import Path
import numpy as np
from local_verify import A2,A3,ROOT,run,sha
from build_dma16_sequence import verify_runtime_sources


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--vivado-bin',required=True,type=Path)
    parser.add_argument('--data',required=True,type=Path);parser.add_argument('--firmware-manifest',required=True,type=Path)
    args=parser.parse_args();data=args.data.resolve();manifest=args.firmware_manifest.resolve()
    firmware=json.loads(manifest.read_text());first=data/firmware['tasks']['A']['case'];second=data/firmware['tasks']['B']['case']
    inputs=verify_runtime_sources(firmware,first/'load32.hex',second/'load32.hex')
    folder=ROOT/'local_runs'/('dma16_sequence_fixture_'+datetime.now().strftime('%Y%m%d_%H%M%S_%f'));folder.mkdir(parents=True)
    files=[A2/'rtl/requantize.sv',A2/'rtl/dot64.sv',A2/'arch02/rtl/sram_port.sv',
           A2/'arch02/rtl/sram_macro_adapter.sv',A2/'arch02/tb/pin_mock.sv',
           A3/'rtl/arch03_linear16.sv',A3/'rtl/arch03_dma16_accel.sv',A3/'rtl/arch03_icb_arb2.sv',
           A3/'rtl/arch03_icb_memory_router.sv',A3/'rtl/arch03_shared_sram.sv',A3/'tb/arch03_task_window16.sv',
           A3/'tb/arch03_dma16_sequence_source.sv',A3/'tb/tb_arch03_dma16_sequence_fixture.sv']
    cfg_path=A2/'arch02/tb/pin_mock_config.json';cfg=json.loads(cfg_path.read_text());lines=[]
    for size in ('128','4096'):
        for key,width in [('cen_low',1),('gwen_low',1),('wen_low',1),('ema',3),('emaw',2),('ret1n',1)]:
            lines.append("`define A02_%s_%s %d'd%d"%(size,key.upper(),width,cfg['macros'][size][key]))
    config=folder/'arch02_sram_config.vh';config.write_text('\n'.join(lines)+'\n')
    hashes={p:sha(p) for p in files+[cfg_path,config,manifest,A3/'tb/arch03_dma16_sequence_monitor.svh',
                                  A3/'scripts/build_dma16_sequence.py',Path(__file__).resolve()]}
    data_hashes={}
    for task in (first,second):
        layout=json.loads((task/'layout_manifest.json').read_text())
        for name,digest in layout['sha256'].items():
            if sha(task/name)!=digest:raise ValueError('Sequence data changed')
            data_hashes[task/name]=digest
        data_hashes[task/'layout_manifest.json']=sha(task/'layout_manifest.json')
    tool=lambda name:args.vivado_bin/(name+'.bat')
    run([tool('xvlog'),'--sv','-d','ARCH02_PIN_MOCK','-d','ARCH03_SEQUENCE_NO_CPU','-i',folder,'-i',A3/'tb']+files,folder,'compile.log')
    run([tool('xelab'),'tb_arch03_dma16_sequence_fixture','-debug','typical','-s','sequence'],folder,'elaborate.log')
    (folder/'run.tcl').write_text('run all\nquit\n');prefix=folder/'capture';options=folder/'sequence.options'
    option_text='sequence\n-tclbatch run.tcl\n'+''.join('-testplusarg %s=%s\n'%(key,value) for key,value in [
        ('DATA_DIR',first.as_posix()),('SECOND_DIR',second.as_posix()),
        ('FIRST_LOAD32',(first/'load32.hex').as_posix()),('SECOND_LOAD32',(second/'load32.hex').as_posix()),
        ('CAPTURE_PREFIX',prefix.as_posix()),('FIRST_DESCRIPTOR','%08x'%firmware['tasks']['A']['descriptor']),
        ('SECOND_DESCRIPTOR','%08x'%firmware['tasks']['B']['descriptor']),
        ('EXPECTED_FAULT_EPC',firmware['fault_sites']['sequence_fault_store'][2:]),
        ('SHORT_TIMEOUT',firmware['configuration']['short_timeout_cycles'])])
    negative_results=[]
    negatives={1:('early_source_selection','Sequence source switch before drain or wrong descriptor'),
               2:('wrong_fault_epc_receipt','Sequence receipt identity/count/drain mismatch phase=1'),
               3:('missing_receipt_word','Missing phase receipt field 32')}
    for number,(description,message) in sorted(negatives.items()):
        negative_options=folder/('negative_%d.options'%number);negative_log=folder/('negative_%d.log'%number)
        negative_prefix=folder/('negative_%d_capture'%number)
        negative_options.write_text(option_text.replace(prefix.as_posix(),negative_prefix.as_posix())+'-testplusarg NEGATIVE=%d\n'%number)
        with negative_log.open('w',encoding='utf8') as output:
            process=subprocess.run([str(tool('xsim')),'-f',str(negative_options)],cwd=str(folder),stdout=output,stderr=subprocess.STDOUT,timeout=180)
        text=negative_log.read_text(errors='replace')
        if ('DMA16_SEQUENCE_FIXTURE_NEGATIVE_ARM mode='+str(number)) not in text or not re.search(r'(?im)^Fatal:\s*'+re.escape(message),text):
            raise ValueError('Sequence negative test did not produce expected rejection: '+description)
        if 'SEQUENCE_NEGATIVE_NOT_REJECTED' in text or 'DMA16_SEQUENCE_PASS' in text:raise ValueError('Sequence negative test accepted')
        negative_results.append(dict(case=number,description=description,status='expected_rejection',process_exit=process.returncode,log_sha256=sha(negative_log)))
        print('PASS sequence expected rejection '+description,flush=True)
    options.write_text(option_text)
    log=run([tool('xsim'),'-f',options],folder,'sequence.log')
    required=('DMA16_SEQUENCE_FIXTURE_NO_CPU','DMA16_SEQUENCE_FIXTURE_READY cpu_executed=false',
              'DMA16_SEQUENCE_PASS phases=10 tasks=3 outputs=76032 cpu_executed=false')
    if any(marker not in log for marker in required):raise ValueError('Missing sequence acceptance/scope marker')
    phases=[{key:int(value) for key,value in (token.split('=') for token in line.split())}
            for line in re.findall(r'^DMA16_SEQUENCE_PHASE_PASS (.+)$',log,re.M)]
    windows=[dict(token.split('=') for token in line.split()) for line in re.findall(r'^DMA16_TASK_WINDOW (.+)$',log,re.M)]
    if [p['phase'] for p in phases]!=list(range(1,11)) or len(windows)!=10:raise ValueError('Sequence phase/window count')
    receipt_lines=re.findall(r'^DMA16_SEQUENCE_RECEIPT phase=(\d+) words=([0-9a-fA-F,]+)$',log,re.M)
    if [int(p) for p,_ in receipt_lines]!=list(range(1,11)):raise ValueError('Missing sequence full receipts')
    receipts=[]
    for phase,text in receipt_lines:
        tokens=text.split(',')
        if len(tokens)!=33 or any(not re.fullmatch('[0-9a-fA-F]{8}',token) for token in tokens):raise ValueError('Malformed sequence receipt')
        words=[int(token,16) for token in tokens]
        if words[0]!=int(phase) or words[23]!=int(firmware['fault_sites']['sequence_fault_store'],16) or words[24]!=0x40000004:
            raise ValueError('Sequence receipt identity does not match firmware metadata')
        receipts.append(dict(phase=int(phase),words=words))
    for phase,window in zip(phases,windows):
        if phase['phase']>=8:
            if phase['cycles']!=225770 or Decimal(window['end_ns'])-Decimal(window['start_ns'])!=phase['cycles']*Decimal('6.666666'):
                raise ValueError('Successful sequence boundary changed')
        elif phase['window_failed']!=1:raise ValueError('Failed phase window misclassified')
    captures=[]
    for index,task in enumerate((first,second,first),1):
        capture=folder/('capture__task%d.csv'%index)
        actual=np.loadtxt(str(capture),delimiter=',',dtype=np.int64,ndmin=2);indexes=actual[:,0]*256+actual[:,1]
        if actual.shape!=(25344,4) or not np.array_equal(np.sort(indexes),np.arange(25344)):raise ValueError('Sequence output coordinates')
        ordered=actual[np.argsort(indexes)]
        with np.load(str(task/'expected.npz'),allow_pickle=False) as expected:
            if not np.array_equal(ordered[:,2],expected['result'].ravel()) or not np.array_equal(ordered[:,3],expected['saturated'].ravel()):
                raise ValueError('Sequence output value/saturation mismatch')
        captures.append(dict(task=index,case=task.name,outputs=25344,sha256=sha(capture)))
    for path,digest in hashes.items():
        if sha(path)!=digest:raise ValueError('Sequence source changed during run: '+str(path))
    for path,digest in data_hashes.items():
        if sha(path)!=digest:raise ValueError('Sequence data changed during run')
    report=dict(status='passed',scope='real_DMA_core_fabric_pin_mock_sequence_procedural_MMIO_no_CPU',
                cpu_executed=False,dma_executed=True,actual_CPU_traps_verified=False,actual_driver_timeout_verified=False,
                hardware_MMIO_configuration_rejections=5,hardware_partial_cancel_verified=True,
                no_reset_ABA_hardware_verified=True,phases=phases,windows=windows,receipts=receipts,captures=captures,
                negative_tests=negative_results,
                runtime_source_identities=inputs,source_sha256={p.relative_to(ROOT).as_posix():h for p,h in hashes.items()},
                data_sha256={p.relative_to(ROOT).as_posix():h for p,h in data_hashes.items()})
    (folder/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
    print('LOCAL_DMA16_SEQUENCE_FIXTURE_PASS '+str(folder),flush=True)


if __name__=='__main__':main()
