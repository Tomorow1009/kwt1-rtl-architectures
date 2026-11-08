"""Immutable-bundle architecture-3 VCS stages, Python 3.6 standard library.

Uses the SAME team lock as architecture 2. Never retries a recorded stage in place.
"""
import argparse,datetime,hashlib,json,os,re,socket,subprocess,sys
from pathlib import Path
from install_platform import install
ROOT=Path(__file__).resolve().parents[3]
A2=ROOT/'workspaces/arch02';A3=ROOT/'workspaces/arch03'
ACTIVE_CHILD=None
LOCK=None
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):
    temp=p.with_suffix('.tmp');temp.write_text(json.dumps(v,indent=2));os.replace(str(temp),str(p))
def inputs():
    m=json.loads((ROOT/'manifest.json').read_text())
    for rel,digest in m['files'].items():
        p=(ROOT/rel).resolve();p.relative_to(ROOT)
        if not p.is_file() or sha(p)!=digest:raise ValueError('Changed bundle input '+rel)
    return m
def call(cmd,run,log):
    global ACTIVE_CHILD
    with (run/log).open('w') as f:
        p=subprocess.Popen([str(x) for x in cmd],cwd=str(run),stdout=f,stderr=subprocess.STDOUT)
        ACTIVE_CHILD=p
        if LOCK is not None:
            owner=json.loads((LOCK/'owner.json').read_text());owner['child_pid']=p.pid;owner['log']=str(run/log)
            save(LOCK/'owner.json',owner)
        print('CHILD_PID',p.pid,'LOG',run/log,flush=True)
        code=p.wait()
        ACTIVE_CHILD=None
    text=(run/log).read_text(errors='replace')
    if code or re.search(r'(?im)^\s*(Error-|Fatal:|Error:)',text):
        raise RuntimeError('Tool failed '+str(run/log)+' exit='+str(code))
    return text
def source_list():
    return [A2/'rtl/requantize.sv',A2/'rtl/dot64.sv',A2/'arch02/rtl/sram_port.sv',
            A2/'arch02/rtl/sram_macro_adapter.sv',A2/'arch02/rtl/arch02_linear.sv',
            A3/'rtl/arch03_icb_accel.sv',A3/'rtl/arch03_shared_sram.sv']
def vendor(cfg,run):
    sources=[];lines=[]
    for size in ('128','4096'):
        model=cfg['models'][size];p=Path(model['path'])
        if sha(p)!=model['sha256']:raise ValueError('Vendor model hash changed')
        sources.append(p)
        for key,width,value in [('CEN_LOW',1,1),('GWEN_LOW',1,1),('WEN_LOW',1,1),('EMA',3,2),('EMAW',2,0),('RET1N',1,1)]:
            lines.append("`define A02_%s_%s %d'd%d"%(size,key,width,value))
    (run/'arch02_sram_config.vh').write_text('\n'.join(lines)+'\n')
    return sources
def check_capture(p,task,cols):
    expected=[int(x,16) for x in (task/'result.hex').read_text().split()]
    sats=[int(x,16) for x in (task/'saturated.hex').read_text().split()]
    seen=set()
    for line in p.read_text().splitlines():
        row=[int(x) for x in line.split(',')]
        if len(row)!=cols:raise ValueError('Capture columns')
        i,v=row[:2]
        if not 0<=i<25344 or i in seen:raise ValueError('Capture coordinate coverage')
        want=expected[i] if expected[i]<32768 else expected[i]-65536
        if v!=want or (cols==3 and row[2]!=sats[i]):raise ValueError('Capture mismatch')
        seen.add(i)
    if len(seen)!=25344:raise ValueError('Incomplete matrix')
    return dict(outputs=len(seen),capture_sha256=sha(p),expected_sha256=sha(task/'result.hex'))
def vcs_tcm(cfg,run):
    files=[A3/'rtl/arch03_shared_sram.sv',A3/'rtl/arch03_tcm_ram.sv',A3/'tb/tb_arch03_tcm.sv']+vendor(cfg,run)
    tracked=files+[run/'arch02_sram_config.vh']
    before={str(p):sha(p) for p in tracked}
    save(run/'source_inputs.json',before)
    cmd=[cfg['tools']['vcs'],'-full64','-sverilog','-timescale=1ns/1ps','+define+ARM_UD_MODEL',
         '+incdir+'+str(run),'-top','tb_arch03_tcm','-o',str(run/'simv')]+files
    log=call(cmd,run,'compile.log')
    if re.search(r'Warning-\[(?:IPDW|PCWM-W|INAV|SIOB)\]',log):raise ValueError('TCM VCS width/declaration warning')
    text=call([run/'simv'],run,'tcm.log')
    if 'ARCH03_TCM_PASS macros=64 cpu_executed=false' not in text:raise ValueError('TCM vendor test did not complete')
    geometries=re.findall(r'TCM_GEOMETRY_PASS DW=(\d+) DP=(\d+) checks=(\d+) macros=32',text)
    if sorted(geometries)!=[('32','65536','65621'),('64','32768','33061')]:
        raise ValueError('TCM coverage does not match complete address/mask regression')
    for path,digest in before.items():
        if sha(Path(path))!=digest:raise ValueError('TCM vendor test input changed')
    return dict(status='passed',scope='tcm_vendor_functional_only',cpu_executed=False,
                vendor_model='ARM_UD_MODEL',geometry_checks=geometries,
                timing_verified=False,whole_soc_verified=False,
                artifacts={p.name:sha(p) for p in run.iterdir() if p.is_file()})
def vcs(stage,cfg,run,platform_source,cases,activity_cases=()):
    if stage=='soc':
        firmware=json.loads((ROOT/'firmware/manifest.json').read_text())
        if firmware.get('run_mode','single_cpu_v2')!='single_cpu_v2':
            raise ValueError('Single-task SoC monitor cannot accept sequence firmware')
    if activity_cases and (stage!='soc' or not set(activity_cases).issubset(cases)):
        raise ValueError('Activity cases must be selected SoC cases')
    files=source_list();includes=[run,A3/'tb']
    top='tb_arch03_icb';cols=3
    if stage=='soc':
        platform=run/'platform';install(platform_source,platform)
        pf=[]
        for line in (platform/'vcode_rtl.f').read_text().splitlines():
            line=line.strip()
            if not line or line.startswith('//'):continue
            candidate=line[3:].strip() if line.startswith('-v ') else line
            if candidate.startswith('./'):
                p=platform/candidate[2:]
                if not p.is_file():raise ValueError('Missing official source '+str(p))
                if p not in pf:pf.append(p)
        if not pf:raise ValueError('Empty platform file list')
        # Defines precede CPU source files, as in the original list. TB is last.
        files=pf+files+[A3/'tb/arch03_task_window.sv',platform/'tb/tb_top.v'];top='tb_top';cols=2
        includes += [platform/'rtl/e203/core']
    else:files.append(A3/'tb/tb_arch03_icb.sv')
    files+=vendor(cfg,run)
    includes+=list(dict.fromkeys(p.parent for p in files))
    cmd=[cfg['tools']['vcs'],'-full64','-sverilog','-timescale=1ns/1ps','+define+ARM_UD_MODEL',
         '-top',top,'-o',str(run/'simv')]+['+incdir+'+str(p) for p in includes]+files
    # The official TB defines FPGA only after the RTL has already been parsed.
    # Select its existing functional TCM/ROM/clock branch for the entire SoC.
    # Accelerator/shared SRAM remain the actual ARM_UD_MODEL vendor macros.
    if stage=='soc':cmd.insert(4,'+define+FPGA')
    tracked=files+[run/'arch02_sram_config.vh',A3/'tb/arch03_monitor.svh']
    if stage=='soc':tracked+= [p for p in platform.rglob('*') if p.is_file()]
    source_hashes={str(p):sha(p) for p in tracked}
    save(run/'source_inputs.json',source_hashes)
    compile_text=call(cmd,run,'compile.log')
    if re.search(r'Warning-\[(?:IPDW|PCWM-W|INAV|SIOB)\]',compile_text):
        raise ValueError('VCS declaration/width warning requires review; see compile.log')
    results=[]
    for name in cases:
        if not re.fullmatch(r'layer_(?:0[1-9]|1[0-2])|extremes|rounding|worst_error|largest_input|largest_output|zero|shift00|shift31|cancellation',name):
            raise ValueError('Invalid case')
        task=ROOT/'validated_data'/name
        info=json.loads((task/'layout.json').read_text())
        for rel,h in info['sha256'].items():
            if sha(task/rel)!=h:raise ValueError('Changed vector')
        capture=run/(name+'.csv')
        cmd=[run/'simv','+DATA_DIR='+str(task),'+CAPTURE='+str(capture),'+SHIFT='+str(info['shift'])]
        if stage=='soc':cmd+=['+TESTCASE='+str(ROOT/'firmware'/name)]
        if name in activity_cases:cmd+=['+ACTIVITY='+str(run/(name+'.vcd'))]
        text=call(cmd,run,name+'.log')
        marker='ARCH03_SOC_PASS outputs=25344 cpu_executed=true' if stage=='soc' else 'ARCH03_ICB_PASS outputs=25344'
        if marker not in text:raise ValueError('Missing acceptance marker '+name)
        result=check_capture(capture,task,cols);result['case']=name
        if stage=='soc':
            found=re.search(r'ARCH03_SOC_PASS[^\n]*cycles=(\d+) saturated=(\d+)',text)
            if not found:raise ValueError('Missing cycle accounting')
            result.update(cycles=int(found.group(1)),saturated=int(found.group(2)))
            window=read_task_window(text)
            if window['cycles']>result['cycles']:raise ValueError('Bus timing window exceeds enclosing CPU cycle interval')
            result['task_window']=window
            if name in activity_cases:
                activity=run/(name+'.vcd')
                if not activity.is_file() or activity.stat().st_size==0:raise ValueError('Missing system activity')
                from activity import audit_vcd
                result['activity']=audit_vcd(activity,window)
        results.append(result);print('CASE_PASS',stage,name,flush=True)
    for path,digest in source_hashes.items():
        if sha(Path(path))!=digest:raise ValueError('Input changed during VCS '+path)
    return dict(status='passed',stage=stage,cpu_executed=stage=='soc',cases=results,
                real_outputs=sum(r['outputs'] for r in results if r['case'].startswith('layer_')),
                official_precision_verified=False,physical_signoff=False)

def read_task_window(text):
    from timing_contract import validate_period,TB_PERIOD_NS
    from decimal import Decimal
    matches=re.findall(r'ARCH03_TASK_WINDOW start_cycle=(\d+) end_cycle=(\d+) cycles=(\d+) start_ns=([0-9.]+) end_ns=([0-9.]+) period_ns=([0-9.]+) input_words=(\d+) output_words=(\d+)',text)
    if len(matches)!=1:raise ValueError('Expected exactly one full-task bus timing window')
    start,end,cycles,t0,t1,period,loads,outputs=matches[0]
    start,end,cycles,loads,outputs=map(int,(start,end,cycles,loads,outputs))
    validate_period(period)
    if not (end-start==cycles>0 and loads==23488 and outputs==25344):raise ValueError('Invalid task window counts')
    if Decimal(period)!=Decimal(TB_PERIOD_NS):raise ValueError('Measured TB period differs from frozen period')
    if abs((Decimal(t1)-Decimal(t0))-Decimal(cycles)*Decimal(period))>Decimal('0.000002'):
        raise ValueError('Task waveform time and cycle count disagree')
    return dict(start_cycle=start,end_cycle=end,cycles=cycles,start_ns=t0,end_ns=t1,period_ns=period,
                input_words=loads,output_words=outputs,boundary='begin_marker_response_to_last_output_write_response')
def main():
    global LOCK
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['status','icb','soc','sequence','tcm','stdcell','asic_boot','asic_soc','gate_soc','asic_power','dc_accel','dc_shared','asic_link','asic_synth'])
    p.add_argument('--session',required=True)
    p.add_argument('--platform',type=Path,default=Path('/storage2/2026contest/server4/s4_21usr/Desktop/e203_hbirdv2-master'))
    p.add_argument('--cases',nargs='+',default=['layer_%02d'%n for n in range(1,13)]+['extremes','rounding'])
    p.add_argument('--activity-cases',nargs='*',default=[],help='SoC cases to record complete-system VCD over the measured task window')
    p.add_argument('--synth-run',type=Path,help='Completed ASIC synthesis directory for mapped gate verification')
    p.add_argument('--synth-summary-sha256',help='Explicit expected digest of that synthesis summary')
    p.add_argument('--gate-run',type=Path,help='Passed gate verification directory containing audited task activity')
    p.add_argument('--gate-summary-sha256',help='Explicit expected digest of that gate summary')
    p.add_argument('--synth-reports-from',type=Path,help='Re-audit a marker-only failed synthesis into a new run; no mapping rerun')
    a=p.parse_args()
    if a.synth_reports_from is not None and a.stage!='asic_synth':
        raise ValueError('Synthesis report re-audit is only for asic_synth')
    if a.stage=='asic_power' and (a.gate_run is None or a.gate_summary_sha256 is None or len(a.cases)!=1):
        raise ValueError('Power requires gate run, summary digest and exactly one --cases selection')
    if a.stage!='asic_power' and (a.gate_run is not None or a.gate_summary_sha256 is not None):
        raise ValueError('Gate activity selection is only for power estimation')
    if a.stage=='gate_soc' and (a.synth_run is None or a.synth_summary_sha256 is None):
        raise ValueError('Gate verification requires synthesis run and summary digest')
    if a.stage!='gate_soc' and (a.synth_run is not None or a.synth_summary_sha256 is not None):
        raise ValueError('Synthesis artifact selection is only for gate verification')
    if len(a.cases)!=len(set(a.cases)):raise ValueError('Duplicate case names would overwrite run artifacts')
    if a.activity_cases and (a.stage not in ('soc','asic_soc','gate_soc') or not set(a.activity_cases).issubset(a.cases)):
        raise ValueError('Activity cases must be selected SoC cases')
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,64}',a.session):raise ValueError('Bad session')
    cfg=json.loads((ROOT/'handoff/team/server_config.json').read_text())
    session=ROOT/'runs'/a.session
    if a.stage=='status':
        print((session/'state.json').read_text() if (session/'state.json').exists() else 'SESSION_NOT_STARTED')
        lock=Path(cfg['server_root'])/'.arch02_team_lock'
        if lock.exists():print('TEAM_LOCK', (lock/'owner.json').read_text() if (lock/'owner.json').is_file() else 'incomplete lock')
        return
    inputs()
    lock=Path(cfg['server_root'])/'.arch02_team_lock'
    # Existing owner, including stale locks, must be resolved by the owner, never silently removed.
    lock.mkdir()
    LOCK=lock
    save(lock/'owner.json',dict(pid=os.getpid(),host=socket.gethostname(),bundle=str(ROOT),session=a.session))
    record={}
    try:
        session.mkdir(parents=True,exist_ok=True);run=session/a.stage;run.mkdir()
        state_path=session/'state.json'
        state=json.loads(state_path.read_text()) if state_path.exists() else dict(stages={})
        if a.stage in state['stages']:raise ValueError('Stage already recorded; use new session')
        record=dict(status='running',pid=os.getpid(),started=datetime.datetime.now().isoformat(),run=str(run))
        state['stages'][a.stage]=record;save(state_path,state)
        try:
            if a.stage=='asic_power':
                from soc_power import estimate
                report=estimate(cfg,run,a.gate_run.resolve(),a.gate_summary_sha256,a.cases[0],call)
            elif a.stage=='gate_soc':
                from gate_soc import verify
                report=verify(cfg,run,a.synth_run.resolve(),a.synth_summary_sha256,a.cases,call,a.activity_cases)
            elif a.stage=='asic_boot':
                from asic_soc import boot_test
                report=boot_test(cfg,run,call)
            elif a.stage=='asic_soc':
                from asic_soc import verify
                report=verify(cfg,run,a.platform,a.cases,call,a.activity_cases)
            elif a.stage=='sequence':
                from sequence_soc import verify
                report=verify(cfg,run,a.platform,a.cases,call)
            elif a.stage=='stdcell':
                from stdcell_verify import verify
                report=verify(cfg,run,call)
            elif a.stage=='tcm':
                report=vcs_tcm(cfg,run)
            elif a.stage=='asic_link':
                from asic_link import link_soc
                vendor(cfg,run)
                report=link_soc(cfg,run,a.platform,source_list(),call)
            elif a.stage=='asic_synth':
                from soc_synth import synth,recover_reports
                if a.synth_reports_from is not None:
                    report=recover_reports(cfg,run,a.synth_reports_from,ROOT)
                else:
                    vendor(cfg,run)
                    report=synth(cfg,run,a.platform,source_list(),call)
            elif a.stage.startswith('dc_'):
                from dc_blocks import synth
                vendor(cfg,run)
                top='arch03_icb_accel' if a.stage=='dc_accel' else 'arch03_shared_sram'
                report=synth(cfg,run,top,source_list(),call)
            else:report=vcs(a.stage,cfg,run,a.platform,a.cases,a.activity_cases)
            inputs();save(run/'summary.json',report)
            record.update(status='passed',summary_sha256=sha(run/'summary.json'))
        except BaseException as exc:record.update(status='failed',error=str(exc));raise
        finally:
            record['finished']=datetime.datetime.now().isoformat();save(state_path,state)
        print('ARCH03_STAGE_PASS',a.stage,run,flush=True)
    finally:
        # Delete only the lock still owned by THIS process/bundle/session.
        owner=json.loads((lock/'owner.json').read_text())
        if (ACTIVE_CHILD is None or ACTIVE_CHILD.poll() is not None) and owner.get('pid')==os.getpid() and owner.get('bundle')==str(ROOT) and owner.get('session')==a.session:
            (lock/'owner.json').unlink();lock.rmdir()
if __name__=='__main__':main()
