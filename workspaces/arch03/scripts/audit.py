"""Audit completed arch03 runs without editing them (Python 3.6 stdlib).

An auditor-only later commit may inspect an earlier immutable runtime bundle.
Every hardware, firmware, data, configuration and execution-script byte must
match the auditor bundle; added audit tools/docs do not imply a hardware rerun.
"""
import argparse,hashlib,importlib.util,json,math,os,re,socket,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
CASES=['layer_%02d'%i for i in range(1,13)]+['extremes','rounding']

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def require(condition,message):
    if not condition:raise ValueError(message)

def manifest(root):
    m=read(root/'manifest.json')
    for rel,digest in m['files'].items():
        p=(root/rel).resolve();p.relative_to(root)
        require(p.is_file() and sha(p)==digest,'Input changed '+str(p))
    return m

def runtime(rel):
    return (rel.startswith(('validated_data/','firmware/','architectures/','workspaces/arch02/'))
            or rel.startswith(('workspaces/arch03/rtl/','workspaces/arch03/sw/','workspaces/arch03/tb/'))
            or rel in ('handoff/team/server_config.json','workspaces/arch03/scripts/server_run.py',
                       'workspaces/arch03/scripts/dc_blocks.py','workspaces/arch03/scripts/install_platform.py'))

def capture(path,expected,saturated,columns):
    seen=set();count=0
    for line in path.read_text().splitlines():
        row=[int(x) for x in line.split(',')]
        require(len(row)==columns,'Capture width '+str(path))
        idx,value=row[:2]
        require(0<=idx<25344 and idx not in seen,'Capture coverage '+str(path))
        require(value==expected[idx],'Capture arithmetic '+str(path))
        if columns==3:require(row[2]==saturated[idx],'Capture saturation '+str(path))
        seen.add(idx);count+=1
    require(count==25344,'Incomplete capture '+str(path))
    return count

def stage(root,session,name):
    s=read(root/'runs'/session/'state.json')['stages'][name]
    require(s['status']=='passed','Stage has not passed: '+name)
    run=Path(s['run']).resolve();require(run==root/'runs'/session/name,'Unexpected stage path')
    require(sha(run/'summary.json')==s['summary_sha256'],'Summary changed '+name)
    result=read(run/'summary.json');require(result['status']=='passed','Summary not passed')
    return run,result

def check_vcs(root,session,name,reference):
    run,result=stage(root,session,name)
    require(result['cpu_executed']==(name=='soc'),'CPU execution scope')
    require([c['case'] for c in result['cases']]==CASES,'Missing/duplicate/reordered case')
    require(result['real_outputs']==304128,'Real output count')
    for path,digest in read(run/'source_inputs.json').items():
        require(sha(Path(path))==digest,'Compiled source changed '+path)
    records=[]
    for c in result['cases']:
        case=c['case'];path=run/(case+'.csv');task=root/'validated_data'/case
        require(c['outputs']==25344 and sha(path)==c['capture_sha256'],'Capture hash '+case)
        require(sha(task/'result.hex')==c['expected_sha256'],'Expected hash '+case)
        totals,values,sats=reference[case]
        capture(path,values,sats,2 if name=='soc' else 3)
        log=(run/(case+'.log')).read_text(errors='replace')
        marker='ARCH03_SOC_PASS outputs=25344 cpu_executed=true' if name=='soc' else 'ARCH03_ICB_PASS outputs=25344'
        require(marker in log,'Missing actual tool acceptance '+case)
        if name=='soc':
            match=re.search(r'ARCH03_SOC_PASS[^\n]*cycles=(\d+) saturated=(\d+)',log)
            require(match is not None,'Missing CPU counters')
            require(int(match.group(1))==c['cycles']>0,'CPU cycle mismatch')
            require(int(match.group(2))==c['saturated']==sum(sats),'CPU saturation count mismatch')
        records.append(dict(case=case,outputs=25344,capture_sha256=sha(path),log_sha256=sha(run/(case+'.log'))))
    return dict(summary_sha256=sha(run/'summary.json'),cases=records,cpu_executed=name=='soc')

def check_dc(root,session,name,output,cfg,lock):
    run,result=stage(root,session,name)
    expected=(8,2) if name=='dc_accel' else (0,64)
    m=result['metrics']
    require((int(m['RAMSP128X16']),int(m['RAMSP4096X16']))==expected,'Wrong SRAM macro count')
    require(int(m['latches'])==0,'Inferred latch')
    require(all(math.isfinite(float(m[k])) for k in ('max','min','area')),'Non-finite synthesis metric')
    require(min(float(m['max']),float(m['min']))>=0 and float(m['area'])>0,'Invalid synthesis metrics')
    require(result['clock_ns']==6.667 and result['scope']=='block_only_not_whole_soc','DC scope changed')
    if name=='dc_accel':require(float(m['area'])<=2250000,'Accelerator area limit')
    for rel,digest in result['artifacts'].items():
        p=(run/rel).resolve();p.relative_to(run)
        require(sha(p)==digest,'Synthesis artifact changed '+str(p))
    for path,digest in result['library_inputs'].items():require(sha(Path(path))==digest,'Library changed '+path)
    dbs=[Path(p) for p in result['library_inputs'] if p.endswith('.db')]
    std=[p for p in dbs if not p.name.startswith('RAMSP')]
    require(len(std)==1 and len(dbs)==3,'Unexpected library set')
    out=output/name;out.mkdir()
    # Reload the actual serialized DDC with its actual libraries, not a fresh synthesis.
    tcl='set_app_var target_library [list {%s}]\n'%std[0]
    tcl+='set_app_var link_library [list * %s]\n'%' '.join('{%s}'%p for p in dbs)
    tcl+='read_ddc {%s}\ncurrent_design %s\nif {![link]} {error "Audit link failed"}\n'%(run/'mapped.ddc',result['top'])
    tcl+='puts "AUDIT_LATCHES [sizeof_collection [all_registers -level_sensitive]]"\n'
    tcl+='puts "AUDIT_CHECK_DESIGN [check_design]"\n'
    for size in (128,4096):
        tcl+='puts "AUDIT_MACRO_%d [sizeof_collection [get_cells -hierarchical -filter {ref_name == RAMSP%dX16}]]"\n'%(size,size)
    tcl+='quit\n';(out/'audit.tcl').write_text(tcl)
    with (out/'dc.log').open('w') as f:
        child=subprocess.Popen([cfg['tools']['dc_shell'],'-f',str(out/'audit.tcl')],cwd=str(out),stdout=f,stderr=subprocess.STDOUT)
        owner=read(lock/'owner.json');owner['child_pid']=child.pid;save(lock/'owner.json',owner)
        print('AUDIT_CHILD_PID',child.pid,flush=True)
        try:code=child.wait()
        except BaseException:
            # Leave the lock if a child is still alive; never kill a job on interruption.
            raise
    log=(out/'dc.log').read_text(errors='replace')
    require(code==0 and not re.search(r'(?m)^Error:',log),'DC reload failed')
    for key,want in [('LATCHES',0),('CHECK_DESIGN',1),('MACRO_128',expected[0]),('MACRO_4096',expected[1])]:
        require(re.search(r'(?m)^AUDIT_%s %d\s*$'%(key,want),log) is not None,'DDC audit '+key)
    return dict(summary_sha256=sha(run/'summary.json'),ddc_sha256=sha(run/'mapped.ddc'),metrics=m,
                reload_log_sha256=sha(out/'dc.log'),scope=result['scope'])

def main():
    p=argparse.ArgumentParser();p.add_argument('bundle',type=Path);p.add_argument('--session',required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    require(re.fullmatch(r'[A-Za-z0-9_-]{1,64}',a.session) is not None,'Invalid session')
    root=a.bundle.resolve();out=a.output.resolve()
    out.relative_to(ROOT);require(not out.exists(),'Audit output already exists')
    own=manifest(ROOT);target=manifest(root)
    require({k:v for k,v in own['files'].items() if runtime(k)}==
            {k:v for k,v in target['files'].items() if runtime(k)},'Auditor and target runtime inputs differ')
    cfg=read(root/'handoff/team/server_config.json');lock=Path(cfg['server_root'])/'.arch02_team_lock'
    lock.mkdir();save(lock/'owner.json',dict(pid=os.getpid(),host=socket.gethostname(),bundle=str(ROOT),session='audit_'+a.session))
    try:
        out.mkdir(parents=True)
        spec=importlib.util.spec_from_file_location('arch02_reference',ROOT/'workspaces/arch02/vcs_run.py')
        ref=importlib.util.module_from_spec(spec);spec.loader.exec_module(ref)
        require(sorted(p.name for p in (root/'validated_data').iterdir() if p.is_dir())==sorted(CASES),'Unexpected data case set')
        reference={}
        for case in CASES:
            reference[case]=ref.reference(root/'validated_data'/case)
            print('AUDIT_SOFTWARE_PASS',case,25344,flush=True)
        result=dict(status='passed',target_source_commit=target['source_commit'],auditor_source_commit=own['source_commit'],
                    target_bundle=str(root),target_manifest_sha256=sha(root/'manifest.json'),session=a.session,
                    software_real_outputs=304128,software_all_outputs=354816,physical_signoff=False,
                    whole_soc_dc_verified=False,official_precision_verified=False,stages={})
        for name in ('icb','soc'):result['stages'][name]=check_vcs(root,a.session,name,reference)
        for name in ('dc_accel','dc_shared'):result['stages'][name]=check_dc(root,a.session,name,out,cfg,lock)
        manifest(root);manifest(ROOT)
        save(out/'summary.json',result)
        print('ARCH03_AUDIT_PASS',out,'real_outputs=304128 physical_signoff=false whole_soc_dc=false',flush=True)
    finally:
        owner=read(lock/'owner.json');alive=False
        if owner.get('child_pid'):
            try:os.kill(owner['child_pid'],0);alive=True
            except ProcessLookupError:pass
        if not alive and owner.get('pid')==os.getpid():
            (lock/'owner.json').unlink();lock.rmdir()
if __name__=='__main__':main()
