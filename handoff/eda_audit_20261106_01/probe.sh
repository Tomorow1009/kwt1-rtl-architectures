#!/bin/sh
set -eu
base=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
run="$base/probe_$(date +%Y%m%d_%H%M%S)_$$"
umask 077
mkdir "$run"
cd "$run"
python3 - "$run" <<'PY' > driver.log 2>&1
import os, sys, shutil, subprocess, signal, re, glob, collections
run=sys.argv[1]
report=open('probe_summary.txt','w',buffering=1)
def say(s):
    report.write(s+'\n'); print(s,flush=True)
def command(argv, folder, limit=45):
    with open(os.path.join(folder,'stdout.log'),'w') as out:
        p=subprocess.Popen(argv,cwd=folder,stdout=out,stderr=subprocess.STDOUT,start_new_session=True)
        try: code=p.wait(timeout=limit)
        except subprocess.TimeoutExpired:
            os.killpg(p.pid,signal.SIGTERM)
            try: p.wait(timeout=5)
            except subprocess.TimeoutExpired: os.killpg(p.pid,signal.SIGKILL); p.wait()
            code=124
    with open(os.path.join(folder,'stdout.log'),errors='replace') as f: text=f.read()
    return code,text
say('EDA AUDIT - STARTUP AND LIBRARY METADATA')
say('RUN='+run)
say('No synthesis, place/route, SRAM generation, or library conversion performed.')
for tool in ['dc_shell','pt_shell','fm_shell','icc2_shell','lc_shell']:
    exe=shutil.which(tool)
    if not exe: say(tool+': NOT_ON_PATH'); continue
    folder=os.path.join(run,tool); os.mkdir(folder)
    script=os.path.join(folder,'startup.tcl')
    with open(script,'w') as f: f.write('puts "AUDIT_SHELL_READY"\nexit\n')
    code,text=command([exe,'-f',script],folder)
    say('%s: exit=%d ready=%s executable=%s'%(tool,code,'AUDIT_SHELL_READY' in text,exe))
    relevant=[line.strip() for line in text.splitlines() if re.search(r'(?i)version|license|checkout|checked out|error|fatal|denied|unable|AUDIT_SHELL_READY',line)]
    for line in relevant[:12]: say('  '+line[:240])
    say('  Scope: startup only; feature licenses not exercised.')
for tool,args in [('vcs',['-ID']),('verdi',['-version'])]:
    exe=shutil.which(tool)
    if not exe: continue
    folder=os.path.join(run,tool); os.mkdir(folder)
    code,text=command([exe]+args,folder,20)
    say('%s: version query exit=%d (not a functional license test)'%(tool,code))
    for line in text.splitlines()[:5]: say('  '+line[:200])
root='/storage1/admin_public_dir/SRAM_Lib_2025'
say('SRAM METADATA (files read on server; contents remain here):')
for macro in sorted(os.listdir(root)):
    folder=os.path.join(root,macro)
    if not os.path.isdir(folder): continue
    counts=collections.Counter(); libs=[]; verilog=[]; errors=[]
    for d,dirs,files in os.walk(folder,followlinks=False,onerror=lambda e:errors.append(str(e))):
        if os.path.relpath(d,folder).count(os.sep)>=5: dirs[:]=[]
        for name in sorted(files):
            ext=os.path.splitext(name)[1].lower(); counts[ext]+=1
            if ext=='.lib': libs.append(os.path.join(d,name))
            if ext=='.v': verilog.append(os.path.join(d,name))
    say(macro+': '+str(dict(sorted(counts.items())))+' errors='+str(len(errors)))
    for error in errors: say('  '+error)
    tt=[p for p in libs if '_tt_' in os.path.basename(p).lower()]
    selected=sorted(tt or libs)[:1]
    for p in selected:
        say('  LIB='+p)
        try:
            with open(p,errors='replace') as f: head=f.read(32768)
            for key in ['library','nom_process','nom_voltage','nom_temperature','time_unit','voltage_unit']:
                pat=r'\blibrary\s*\(\s*([^\)]+)' if key=='library' else r'\b'+key+r'\s*:\s*([^;]+)'
                m=re.search(pat,head)
                if m: say('  '+key+'='+m.group(1).strip())
        except Exception as e: say('  READ_ERROR='+str(e))
    for p in sorted(verilog)[:1]:
        try:
            with open(p,errors='replace') as f: head=f.read(32768)
            m=re.search(r'^\s*module\s+(\w+)',head,re.M)
            say('  VERILOG='+p+' module='+(m.group(1) if m else 'UNCONFIRMED'))
        except Exception as e: say('  READ_ERROR='+str(e))
say('SMIC40 ARCHIVE INDEX (no extraction):')
for archive in sorted(glob.glob('/storage1/admin_public_dir/SMIC40_2025/*.tar.gz')):
    folder=os.path.join(run,'archive_'+os.path.basename(archive)); os.mkdir(folder)
    code,text=command(['tar','-tzf',archive],folder,60)
    names=text.splitlines()
    say(os.path.basename(archive)+': bytes='+str(os.path.getsize(archive))+' index_exit='+str(code)+' entries='+str(len(names)))
    for ext in ['.db','.lib','.lef','.tf','.tluplus','.itf','.ndm','.gds','.v']:
        matches=[n for n in names if n.lower().endswith(ext) or n.lower().endswith(ext+'.gz')]
        if matches:
            say('  '+ext+' count='+str(len(matches)))
            for n in matches[:2]: say('    '+n)
say('AUDIT_PROBE_COMPLETE')
report.close()
PY
pluma "$run/probe_summary.txt" >/dev/null 2>&1 &
