"""Architecture 2 verification with explicit SRAM backend; no PPA signoff."""
import argparse
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
import re
import shutil
import subprocess
import sys
from threading import Lock
import uuid
from data import ARCH,PROJECT,DEFAULT_DATA,prepare,compare,sha,save


def tool(name,folder=''):
    p=str(Path(folder)/(name+('.bat' if name in ('xvlog','xelab','xsim') else '.exe'))) if folder else shutil.which(name)
    if not p or not Path(p).is_file():raise FileNotFoundError('Missing tool '+name)
    return p


def call(argv,cwd,log,expected=None):
    with Path(log).open('w',encoding='utf-8') as f:
        process=subprocess.run([str(x) for x in argv],cwd=cwd,stdout=f,stderr=subprocess.STDOUT,timeout=1800)
    text=Path(log).read_text(errors='replace')
    fatal=bool(re.search(r'(?im)^\s*(?:fatal|error):',text))
    if expected:
        # XSim 2018.3 can return zero after $fatal followed by Tcl quit.
        if expected not in text or not fatal or 'PASS: arch02' in text:raise RuntimeError(f'Negative case did not fail as expected: {log}')
    elif process.returncode or fatal:raise RuntimeError(f'Command failed: {log}')
    return text


def configure_backend(args):
    args.vendor_sources=[]
    args.config_path=None
    if args.backend=='behavioral':return
    if args.backend=='pin_mock':
        args.config_path=ARCH/'tb/pin_mock_config.json'
    else:
        if not args.vendor_filelist or not args.sram_config:
            raise ValueError('vendor requires --vendor-filelist and --sram-config; no mock fallback')
        args.config_path=Path(args.sram_config).resolve()
        filelist=Path(args.vendor_filelist).resolve()
        for line in filelist.read_text(encoding='utf-8-sig').splitlines():
            line=line.strip()
            if not line or line.startswith('#'):continue
            source=(filelist.parent/line).resolve()
            if not source.is_file():raise ValueError('Missing vendor source '+str(source))
            if source==ARCH/'tb/pin_mock.sv' or re.search(r'\bmodule\s+arch02_pin_mock\b',source.read_text(errors='replace')):
                raise ValueError('Mock source forbidden in vendor filelist')
            args.vendor_sources.append(source)
        if not args.vendor_sources:raise ValueError('Empty vendor filelist')
    args.config=json.loads(args.config_path.read_text(encoding='utf-8-sig'))
    if args.backend=='vendor' and (args.config.get('kind')!='vendor_confirmed' or not args.config.get('evidence')):
        raise ValueError('Vendor configuration needs kind=vendor_confirmed and evidence reference')
    lines=['// Explicit run configuration; see summary.json for origin.']
    for size in ('128','4096'):
        cfg=args.config['macros'][size]
        if cfg['read_latency']!=1 or cfg['clock_edge']!='posedge':
            raise ValueError('Adapter requires native one-cycle posedge macro; other timing needs RTL adaptation')
        for key,width in [('cen_low',1),('gwen_low',1),('wen_low',1),('ema',3),('emaw',2),('ret1n',1)]:
            value=cfg[key]
            if type(value) is not int or not 0<=value<(1<<width):raise ValueError('Invalid SRAM config '+size+'.'+key)
            lines.append(f"`define A02_{size}_{key.upper()} {width}'d{value}")
    args.config_header='\n'.join(lines)+'\n'


def build(engine,folder,args):
    files=[PROJECT/'rtl/requantize.sv',PROJECT/'rtl/dot64.sv',ARCH/'rtl/sram_port.sv',ARCH/'rtl/arch02_linear.sv',
           ARCH/'tb/sram_model.sv',ARCH/'tb/tb_arch02.sv',ARCH/'tb/tb_lanes.sv',ARCH/'tb/tb_sram_guard.sv']
    files.append(ARCH/'tb/tb_sram_adapter.sv')
    tops=['tb_arch02','tb_arch02_l2','tb_lanes','tb_sram_guard','tb_sram_adapter']
    defines=['ARCH02_BEHAVIORAL'] if args.backend=='behavioral' else []
    includes=[PROJECT/'vectors',folder]
    if args.backend!='behavioral':
        (folder/'arch02_sram_config.vh').write_text(args.config_header,encoding='ascii')
        files.append(ARCH/'rtl/sram_macro_adapter.sv')
        if args.backend=='pin_mock':
            files.append(ARCH/'tb/pin_mock.sv');defines=['ARCH02_PIN_MOCK'];tops.append('tb_pin_mask')
        else:
            files+=args.vendor_sources
            includes+=list(dict.fromkeys(x.parent for x in args.vendor_sources))
            includes+=[Path(x).resolve() for x in args.vendor_include]
    if engine=='iverilog':
        for top in tops:
            call([tool('iverilog',args.icarus_bin),'-g2012','-Wall']+['-D'+d for d in defines]+[v for inc in includes for v in ['-I',inc]]+['-s',top,'-o',top+'.vvp']+files,folder,folder/(top+'_compile.log'))
    else:
        call([tool('xvlog',args.vivado_bin),'--sv']+[v for d in defines for v in ['-d',d]]+[v for inc in includes for v in ['-i',inc]]+files,folder,folder/'compile.log')
        for top in tops:call([tool('xelab',args.vivado_bin),top,'-debug','typical','-s',top+'_sim'],folder,folder/(top+'_elaborate.log'))


def simulate(engine,folder,top,tag,plus,args,wave=False,negative=None):
    if engine=='iverilog':
        text=call([tool('vvp',args.icarus_bin),top+'.vvp']+['+'+x for x in plus]+(['+VCD'] if wave else []),folder,folder/(tag+'.log'),negative)
        if wave and (folder/'arch02.vcd').exists():(folder/'arch02.vcd').rename(folder/(tag+'.vcd'))
    else:
        hierarchy='/tb_arch02_l2/test/dut' if top=='tb_arch02_l2' else '/tb_arch02/dut'
        commands=[]
        if wave:commands=[f'log_wave {hierarchy}/*',f'add_wave {hierarchy}/*',f'save_wave_config {tag}.wcfg']
        (folder/(tag+'.tcl')).write_text('\n'.join(commands+['run all','quit'])+'\n',encoding='ascii')
        (folder/(tag+'.options')).write_text('\n'.join([f'-testplusarg "{x}"' for x in plus]+[f'-tclbatch {tag}.tcl',f'-wdb {tag}.wdb'])+'\n',encoding='ascii')
        text=call([tool('xsim',args.vivado_bin),top+'_sim','-f',tag+'.options'],folder,folder/(tag+'.log'),negative)
    return text


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data-root',type=Path,default=DEFAULT_DATA)
    p.add_argument('--mode',choices=['all','smoke','software'],default='all')
    p.add_argument('--simulator',choices=['both','iverilog','xsim'],default='both')
    p.add_argument('--backend',choices=['behavioral','pin_mock','vendor'],default='behavioral')
    p.add_argument('--vendor-filelist');p.add_argument('--sram-config')
    p.add_argument('--vendor-include',action='append',default=[])
    p.add_argument('--vivado-bin',default='');p.add_argument('--icarus-bin',default='')
    args=p.parse_args()
    try:configure_backend(args)
    except (ValueError,OSError,KeyError,TypeError) as exc:p.error(str(exc))
    run=ARCH/'sim'/(datetime.now().strftime('%Y%m%d_%H%M%S')+'_'+uuid.uuid4().hex[:8]);run.mkdir(parents=True)
    print('Run directory: '+str(run),flush=True)
    dependencies=[PROJECT/'rtl/dot64.sv',PROJECT/'rtl/requantize.sv',PROJECT/'scripts/full_matrix_data.py',PROJECT/'scripts/verify_real_hex.py']
    dependencies+=list((ARCH/'rtl').glob('*.sv'))+list((ARCH/'tb').glob('*.sv'))+list((ARCH/'scripts').glob('*.py'))
    dependencies+=list((PROJECT/'vectors').glob('*.hex'))+[PROJECT/'vectors/cases.vh']
    dependencies+=args.vendor_sources
    if args.config_path:dependencies.append(args.config_path)
    summary=dict(status='running',mode=args.mode,run=str(run),backend=args.backend,
                 verification_scope='substitute model only' if args.backend=='pin_mock' else 'behavioral only' if args.backend=='behavioral' else 'external model functional simulation only; no PPA signoff',
                 sram_config=getattr(args,'config',None),results=[],
                 sources={str(x):sha(x) for x in dependencies})
    save(run/'summary.json',summary);lock=Lock()
    def record(item):
        with lock:
            summary['results'].append(item);save(run/'summary.json',summary)
        print('PASS '+item['simulator']+' '+item['tag'],flush=True)
    try:
        software=prepare(args.data_root,run/'data');save(run/'software.json',software)
        engines=[] if args.mode=='software' else ['iverilog','xsim'] if args.simulator=='both' else [args.simulator]
        layers=range(1,13) if args.mode=='all' else [1]
        def worker(engine):
            folder=run/engine;folder.mkdir();build(engine,folder,args)
            text=simulate(engine,folder,'tb_sram_adapter','sram_adapter',[],args)
            if 'PASS: SRAM adapter cases=4' not in text:raise ValueError('Adapter unit tests missing')
            record(dict(simulator=engine,tag='sram_adapter',passed=True,cases=4))
            if args.backend=='pin_mock':
                text=simulate(engine,folder,'tb_pin_mask','pin_mask',[],args)
                if 'PASS: pin mock masks and hold' not in text:raise ValueError('Pin mask test missing')
                record(dict(simulator=engine,tag='pin_mask',passed=True))
            jobs=[(f'layer_{n:02d}',1,0,0,None) for n in layers]
            jobs += [('extremes',1,1,0,None),('rounding',2,1,1,'extremes')]
            for name,lat,jitter,resets,second in jobs:
                data=run/'data'/name;tag=name+('_l2' if lat==2 else '')
                shift=11 if name=='rounding' else 12
                capture=folder/(tag+'.csv')
                plus=[f'DATA_DIR={data.as_posix()}',f'OUTPUT_FILE={capture.as_posix()}',f'SHIFT={shift}',f'JITTER={jitter}',f'RESET_PROBES={resets}']
                if second:plus += [f'SECOND_DATA_DIR={(run/"data"/second).as_posix()}','SECOND_SHIFT=12']
                text=simulate(engine,folder,'tb_arch02_l2' if lat==2 else 'tb_arch02',tag,plus,args,wave=(name=='rounding'))
                expected_jobs=2 if second else 1
                if len(re.findall(r'^PASS: arch02 outputs=25344 latency='+str(lat),text,re.M))!=expected_jobs:raise ValueError('Missing PASS '+tag)
                if resets and len(re.findall(r'^PASS reset probe=',text,re.M))!=9:raise ValueError('Missing reset coverage')
                result=compare(capture,data,folder/(tag+'.npz'))
                if second:result['second']=compare(Path(str(capture)+'.second.csv'),run/'data'/second,folder/(tag+'_second.npz'))
                metrics=[dict(zip(['total','load','compute','write','load_wait','write_wait','mac_updates'],map(int,m))) for m in re.findall(r'METRICS total=(\d+) load=(\d+) compute=(\d+) write=(\d+) load_wait=(\d+) write_wait=(\d+) mac_updates=(\d+)',text)]
                if len(metrics)!=expected_jobs:raise ValueError('Missing metrics')
                result.update(simulator=engine,tag=tag,kind='real' if name.startswith('layer_') else 'directed',latency=lat,metrics=metrics,passed=True,reset_probes=9 if resets else 0)
                record(result)
            text=simulate(engine,folder,'tb_lanes','numerical',[f'DATA_DIR={(PROJECT/"vectors").as_posix()}'],args)
            if 'PASS: numerical cases=1103 lanes=8 checks=8824' not in text:raise ValueError('Numerical cases missing')
            record(dict(simulator=engine,tag='numerical',passed=True,cases=1103,lane_checks=8824))
            for case,message in [('padding','Malformed bias padding'),('missing','Missing load.hex'),('short_file','Missing/invalid load word'),('timeout','No progress timeout'),('reference','Mismatch row=0 column=0')]:
                data=folder/('negative_'+case);shutil.copytree(run/'data/layer_01',data)
                if case=='padding':
                    lines=(data/'load.hex').read_text().splitlines();lines[6850]=f'{int(lines[6850],16)|256:04x}';(data/'load.hex').write_text('\n'.join(lines)+'\n',encoding='ascii')
                elif case=='missing':(data/'load.hex').unlink()
                elif case=='short_file':(data/'load.hex').write_text('0000\n',encoding='ascii')
                elif case=='reference':
                    path=data/'result.hex';lines=path.read_text().splitlines();lines[0]=f'{int(lines[0],16)^1:04x}';path.write_text('\n'.join(lines)+'\n',encoding='ascii')
                plus=[f'DATA_DIR={data.as_posix()}',f'OUTPUT_FILE={(data/"actual.csv").as_posix()}']
                if case=='timeout':plus+=['TRUNCATE_WORDS=100']
                simulate(engine,folder,'tb_arch02','negative_'+case,plus,args,negative=message)
                record(dict(simulator=engine,tag='negative_'+case,passed=True,expected_failure=message))
            simulate(engine,folder,'tb_sram_guard','negative_uninitialized',[],args,negative='Uninitialized SRAM read')
            record(dict(simulator=engine,tag='negative_uninitialized',passed=True,expected_failure='Uninitialized SRAM read'))
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures=[pool.submit(worker,e) for e in engines]
            for f in futures:f.result()
        for path,digest in summary['sources'].items():
            if sha(path)!=digest:raise ValueError('Source changed during run '+path)
        summary['status']='passed';summary['software_outputs']=304128
        summary['real_outputs_per_simulator']={e:len(layers)*25344 for e in engines}
        print('PASS: arch02 mode='+args.mode+' software=304128 real_outputs='+str(summary['real_outputs_per_simulator']),flush=True)
        return 0
    except Exception as exc:
        summary.update(status='failed',error=str(exc));print('FAIL: '+str(exc),file=sys.stderr,flush=True);return 1
    finally:save(run/'summary.json',summary)


if __name__=='__main__':sys.exit(main())
