"""Unmodified production source/monitor with real DMA datapath, NO E203.

The production monitor's hardcoded CPU flag is explicitly not applicable to
this procedural initiator fixture. Only the source, monitor and datapath are tested.
"""
import argparse
import json
import re
import struct
from icb32_codec import encode, decode
from datetime import datetime
from pathlib import Path
import numpy as np
from local_verify import A2,A3,ROOT,run,sha


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--vivado-bin',required=True,type=Path)
    parser.add_argument('--data',required=True,type=Path)
    parser.add_argument('--cases',nargs='+',default=['layer_01','extremes','rounding'])
    parser.add_argument('--prefetch',nargs='+',type=int,choices=[0,1],default=[0,1])
    parser.add_argument('--activity',action='store_true',help='Dump the production monitor task window; select exactly one case and prefetch mode')
    parser.add_argument('--bus-metrics',action='store_true',help='Add passive metrics using the same ASIC binding/instrumentation functions')
    args=parser.parse_args()
    if args.activity and (len(args.cases)!=1 or len(args.prefetch)!=1):
        parser.error('--activity requires exactly one --cases item and one --prefetch item')
    folder=ROOT/'local_runs'/('icb32_monitor_fixture_'+datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    folder.mkdir(parents=True)
    data=args.data.resolve()
    files=[A2/'rtl/requantize.sv',A2/'rtl/dot64.sv',A2/'arch02/rtl/sram_port.sv',
           A2/'arch02/rtl/sram_macro_adapter.sv',A2/'arch02/tb/pin_mock.sv',
           A3/'rtl/arch03_linear16x4.sv',A3/'rtl/arch03_icb32_accel.sv',
           A3/'rtl/arch03_icb32_decoder.sv',A3/'rtl/arch03_icb32_transport.sv',
           A3/'rtl/arch03_icb_arb2_turnover.sv',A3/'rtl/arch03_icb_memory_router_turnover.sv',A3/'rtl/arch03_shared_sram_turnover.sv',
           A3/'tb/arch03_task_window_icb32.sv',A3/'tb/arch03_icb32_source.sv',A3/'tb/tb_arch03_icb32_monitor_fixture.sv']
    instrumentation=[]
    if args.bus_metrics: raise ValueError('New passive metrics not yet implemented')
    cfg_path=A2/'arch02/tb/pin_mock_config.json'
    cfg=json.loads(cfg_path.read_text());lines=[]
    for size in ('128','4096'):
        for key,width in [('cen_low',1),('gwen_low',1),('wen_low',1),('ema',3),('emaw',2),('ret1n',1)]:
            lines.append("`define A02_%s_%s %d'd%d"%(size,key.upper(),width,cfg['macros'][size][key]))
    config=folder/'arch02_sram_config.vh';config.write_text('\n'.join(lines)+'\n')
    hashes={p:sha(p) for p in files+instrumentation+[cfg_path,config,A3/'tb/arch03_icb32_monitor.svh',A3/'scripts/icb32_codec.py',Path(__file__).resolve()]}
    data_hashes={}
    for name in args.cases:
        task=data/name;layout=json.loads((task/'layout_manifest.json').read_text())
        for filename,digest in layout['sha256'].items():
            if sha(task/filename)!=digest:raise ValueError('Changed fixture data '+filename)
        data_hashes[name]=sha(task/'layout_manifest.json')
    tool=lambda name:args.vivado_bin/(name+'.bat')
    run([tool('xvlog'),'--sv','-d','ARCH02_PIN_MOCK','-i',folder,'-i',A3/'tb']+files,folder,'compile.log')
    run([tool('xelab'),'tb_arch03_icb32_monitor_fixture','-debug','typical','-s','monitor_fixture'],folder,'elaborate.log')
    (folder/'run.tcl').write_text('run all\nquit\n')
    results=[]
    for name in args.cases:
        task=data/name;layout=json.loads((task/'layout_manifest.json').read_text())
        raw=struct.pack('<23488H',*[int(x,16) for x in (task/'load.hex').read_text().split()])
        encoded=encode(raw)
        if decode(encoded)!=raw:raise ValueError('Codec mismatch')
        load_path=folder/(name+'_encoded.hex')
        load_path.write_text(''.join('%08x\n'%x[0] for x in struct.iter_unpack('<I',encoded)))
        for pf in args.prefetch:
            tag=name+'_pf%d'%pf;capture=folder/(tag+'.csv');options=folder/(tag+'.options')
            option_text='monitor_fixture\n-tclbatch run.tcl\n-testplusarg DATA_DIR=%s\n-testplusarg LOAD32=%s\n-testplusarg CAPTURE=%s\n-testplusarg SHIFT=%d\n-testplusarg PREFETCH=%d\n-testplusarg CODEC_BYTES=%d\n'%(
                task.as_posix(),load_path.as_posix(),capture.as_posix(),layout['numeric_format']['shift'],pf,len(encoded))
            activity=folder/(tag+'.vcd')
            if args.activity:option_text+='-testplusarg ACTIVITY=%s\n'%activity.as_posix()
            options.write_text(option_text)
            text=run([tool('xsim'),'-f',options],folder,tag+'.log')
            if 'ICB32_MONITOR_FIXTURE_NO_CPU' not in text or 'ICB32_MONITOR_FIXTURE_READY_TO_CHECK cpu_executed=false' not in text:
                raise ValueError('Missing explicit no-CPU fixture scope')
            matches=re.findall(r'^ARCH03_ICB32_BATCH_RESULT (\{.+\})$',text,re.M)
            if len(matches)!=1:raise ValueError('Production monitor did not accept fixture')
            observed=json.loads(matches[0])
            if observed['cycles']!=observed['final_response_cycle']-observed['first_request_cycle']:
                raise ValueError('Monitor cycle contract')
            actual=np.loadtxt(str(capture),delimiter=',',dtype=np.int64,ndmin=2)
            if actual.shape!=(25344,4):raise ValueError('Fixture capture shape')
            indexes=actual[:,0]*256+actual[:,1]
            if not np.array_equal(np.sort(indexes),np.arange(25344)):raise ValueError('Fixture coordinates')
            ordered=actual[np.argsort(indexes)]
            with np.load(str(task/'expected.npz'),allow_pickle=False) as expected:
                for column,key in ((2,'result'),(3,'saturated')):
                    if not np.array_equal(ordered[:,column],expected[key].ravel()):raise ValueError('Fixture '+key)
            results.append(dict(case=name,encoded_bytes=len(encoded),prefetch=pf,cycles=observed['cycles'],outputs=25344,
                                source_earliest_ack_cycles=1,cpu_executed=False,dma_executed=True,
                                layout_sha256=data_hashes[name],capture_sha256=sha(capture)))
            if args.bus_metrics:
                results[-1]['bus_metrics']=metrics.parse_metrics(text,expected_window=read_window(text,observed))
            if args.activity:
                requested_activity=activity
                if not activity.is_file():
                    # XSim 2018.3 has been observed to emit a packed-reg
                    # $dumpfile argument as "dcv". Each run has a fresh directory;
                    # preserve and explicitly label that actual artifact.
                    alternate=folder/'dcv'
                    if alternate.is_file():
                        activity=alternate
                        print('XSIM_ACTIVITY_FILENAME requested='+str(requested_activity)+' actual='+str(activity),flush=True)
                if not activity.is_file() or activity.stat().st_size==0:raise ValueError('Missing task-window activity')
                results[-1]['activity_file']=activity.relative_to(ROOT).as_posix()
                results[-1]['requested_activity_file']=requested_activity.relative_to(ROOT).as_posix()
                results[-1]['activity_bytes']=activity.stat().st_size
                results[-1]['activity_boundary_audit']='requires separate VCD directive/timestamp audit'
            print('PASS ICB32 production-monitor fixture '+tag+' cycles='+str(observed['cycles']),flush=True)
    for path,digest in hashes.items():
        if sha(path)!=digest:raise ValueError('Fixture source changed during run: '+str(path))
    for name,digest in data_hashes.items():
        if sha(data/name/'layout_manifest.json')!=digest:raise ValueError('Fixture vector changed')
        layout=json.loads((data/name/'layout_manifest.json').read_text())
        for filename,expected_digest in layout['sha256'].items():
            if sha(data/name/filename)!=expected_digest:raise ValueError('Fixture vector content changed: '+filename)
    report=dict(status='passed',cpu_executed=False,dma_executed=True,backend='pin_mock',bus_metrics=bool(args.bus_metrics),
                scope='production_source_and_monitor_real_dma_datapath_procedural_MMIO_no_E203',
                production_monitor_cpu_flag_in_fixture_is_not_evidence=True,tasks=len(results),
                outputs=len(results)*25344,cases=results,source_sha256={p.relative_to(ROOT).as_posix():h for p,h in hashes.items()})
    (folder/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
    print('LOCAL_ICB32_MONITOR_FIXTURE_PASS '+str(folder),flush=True)


if __name__=='__main__':main()
