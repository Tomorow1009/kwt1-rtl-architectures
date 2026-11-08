import os
from pathlib import Path
import json,re,hashlib,subprocess,shutil,datetime,csv,importlib.util
root=Path.cwd();vcs=Path(os.environ['HANDOFF_VCS_RUN'])
dc=Path(os.environ['HANDOFF_HOLD_RUN']);base=Path(os.environ['HANDOFF_SYNTH_RUN'])
audit=root/'audits'/datetime.datetime.now().strftime('%Y%m%d_%H%M%S');audit.mkdir(parents=True)
summary=json.loads((vcs/'summary.json').read_text())
assert summary['status']=='passed' and summary['real_outputs']==304128
assert summary['vendor_model_mode']=='functional'
for path,digest in summary['sources'].items():assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest,path
spec=importlib.util.spec_from_file_location('reference',root/'vcs_run.py');ref=importlib.util.module_from_spec(spec);spec.loader.exec_module(ref)
count=0
for n in range(1,13):
 name='layer_%02d'%n;expected=ref.reference(root/'validated_data'/name);seen=set()
 with (vcs/(name+'.csv')).open() as f:
  for stream,raw in enumerate(csv.reader(f)):
   idx,total,result,sat=map(int,raw);group,rem=divmod(stream,99*8);row,lane=divmod(rem,8)
   assert idx==row*256+group*8+lane and idx not in seen
   assert (total,result,sat)==tuple(a[idx] for a in expected)
   seen.add(idx)
 assert len(seen)==25344;count+=len(seen)
print('FINAL_INTEGER_AND_CAPTURE_RECHECK',count,flush=True)
text=(dc/'summary.txt').read_text()
assert 'RAMSP128X16 count=8' in text and 'RAMSP4096X16 count=2' in text
slacks={k:float(re.search(k+r' slack=([^ ]+)',text).group(1)) for k in ('max','min')}
assert min(slacks.values())>=0
for name in ['arch02_mapped.v','arch02_mapped.ddc','arch02.sdc','qor.rpt','constraints.rpt','check_design.rpt','check_timing.rpt']:
 assert (dc/name).is_file(),name
libpaths=[base/'libs/scc40nll_vhsc40_rvt_ss_v0p99_125c_basic.db']+[base/('libs/RAMSP%dX16_ss_0p99v_0p99v_125c.db'%n) for n in (128,4096)]
tcl='set_app_var target_library [list {%s}]\n'%libpaths[0]
tcl+='set_app_var link_library [list * %s]\n'%' '.join('{%s}'%p for p in libpaths)
tcl+='read_ddc {%s}\ncurrent_design arch02_linear\nif {![link]} {error "Link failed"}\n'%(dc/'arch02_mapped.ddc')
tcl+='puts "FINAL_LATCH_COUNT [sizeof_collection [all_registers -level_sensitive]]"\nputs "FINAL_CHECK_DESIGN [check_design]"\nquit\n'
(audit/'audit.tcl').write_text(tcl)
with (audit/'dc_audit.log').open('w') as f:rc=subprocess.call([shutil.which('dc_shell'),'-f',str(audit/'audit.tcl')],cwd=str(audit),stdout=f,stderr=subprocess.STDOUT)
log=(audit/'dc_audit.log').read_text(errors='replace')
if rc or re.search(r'(?m)^Error:',log):print(log[-6000:]);raise SystemExit(1)
assert re.search(r'^FINAL_LATCH_COUNT 0$',log,re.M)
assert re.search(r'^FINAL_CHECK_DESIGN 1$',log,re.M)
report={'status':'passed','vcs_run':str(vcs),'dc_run':str(dc),'integer_and_capture_rechecked':count,'vendor_model_mode':'functional','corner':'RVT SS 0.99V 125C','clock_ns':6.667,'slack_ns':slacks,'macro_counts':{'RAMSP128X16':8,'RAMSP4096X16':2},'latches':0,'physical_signoff':False,'limitations':['Single SS corner, ideal clock, provisional standalone IO constraints','No post-layout timing, SoC or classification accuracy signoff'],'artifact_hashes':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [dc/'arch02_mapped.v',dc/'arch02_mapped.ddc',dc/'arch02.sdc',vcs/'summary.json']}}
(audit/'summary.json').write_text(json.dumps(report,indent=2))
for name in ['check_design.rpt','check_timing.rpt']:
 t=(dc/name).read_text();codes=re.findall(r'\(([A-Z]+-\d+)\)',t)
 print('CHECK_WARNING_CODES',name,{c:codes.count(c) for c in sorted(set(codes))},flush=True)
print('FINAL_MACROS 128=8 4096=2 LATCHES=0 CHECK_DESIGN=1',flush=True)
print('FINAL_SLACK_NS',slacks,flush=True)
print('FINAL_AUDIT_PASS',audit,flush=True)
