"""Apply reviewed team extensions to a NEW copy of the pinned official platform.

Never edits the original. Hashes all platform RTL, tb_top and source list before copying.
External vendor libraries are not copied. Python 3.6 compatible.
"""
import argparse,hashlib,json,re,shutil
from pathlib import Path
EXPECTED='ee8bfecd81e192a974be81479ef8a01793de3e59c2e2f8769886e8e86143e56e'
ROOT=Path(__file__).resolve().parents[3]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def replace_once(text,old,new):
    if text.count(old)!=1:raise ValueError('Platform context changed: '+old[:90])
    return text.replace(old,new,1)
def install(source,dest):
    source=source.resolve();dest=dest.resolve()
    if dest.exists():raise ValueError('Refusing existing platform destination')
    files=sorted([p for p in (source/'rtl').rglob('*') if p.is_file() and p.suffix in ('.v','.vh','.sv')]+
                 [source/'tb/tb_top.v',source/'vcode_rtl.f'])
    records={p.relative_to(source).as_posix():sha(p) for p in files}
    digest=hashlib.sha256(''.join(k+':'+records[k]+'\n' for k in sorted(records)).encode()).hexdigest()
    if digest!=EXPECTED or len(records)!=163:
        raise ValueError('Official platform baseline mismatch actual=%s expected=%s files=%d expected_files=163'
                         %(digest,EXPECTED,len(records)))
    dest.mkdir(parents=True)
    for p in files:
        target=dest/p.relative_to(source);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(str(p),str(target))
    for name in ('README.md','LICENSE','LICENSE.txt'):
        if (source/name).is_file():shutil.copy2(str(source/name),str(dest/name))
    path=dest/'rtl/e203/subsys/e203_subsys_mems.v';text=path.read_text()
    # Route the existing SysMem split port internally; do not change ITCM/DTCM decode.
    fields={'cmd_valid':1,'cmd_ready':1,'cmd_addr':32,'cmd_read':1,'cmd_wdata':32,'cmd_wmask':4,
            'rsp_valid':1,'rsp_ready':1,'rsp_rdata':32,'rsp_err':1}
    for field in fields:
        pattern=r'(\.o4_icb_'+field+r'\s*\(\s*)sysmem_icb_'+field+r'(\s*\))'
        text,n=re.subn(pattern,r'\g<1>a3_mem_'+field+r'\g<2>',text)
        if n!=1:raise ValueError('Missing SysMem split port '+field)
    start=re.search(r'\bwire\s+expl_axi_awvalid\s*;',text)
    if not start:raise ValueError('Missing example AXI block start')
    end=text.rfind('endmodule')
    if end<start.start() or text[start.start():end].count('sirv_expl_axi_slv')!=1:
        raise ValueError('Unexpected example AXI tail')
    declarations='\n'.join('wire '+('' if width==1 else '[%d:0] '%(width-1))+'a3_mem_'+key+';'
                           for key,width in fields.items())
    ties='\n'.join('assign sysmem_icb_'+key+" = 'b0;" for key in
                   ('cmd_valid','cmd_addr','cmd_read','cmd_wdata','cmd_wmask','rsp_ready'))
    def instance(module,name,prefix):
        ports=['.clk(clk)','.rst_n(rst_n)']+['.%s(%s%s)'%(key,prefix,key) for key in fields]
        return module+' '+name+'(\n  '+',\n  '.join(ports)+'\n);\n'
    # Existing example ICB signals remain; only its unused AXI implementation is removed.
    patch=(declarations+'\n'+ties+'\n'+instance('arch03_shared_sram','u_arch03_shared','a3_mem_')+
           instance('arch03_icb_accel','u_arch03_accel','expl_axi_icb_'))
    text=text[:start.start()]+patch+'\n'+text[end:]
    path.write_text(text)
    tb=dest/'tb/tb_top.v';text=tb.read_text()
    text,n=re.subn(r'(`define\s+PC_\w+\s+)[^\n]+',r"\g<1>32'hffffffff",text)
    if n!=5:raise ValueError('Unexpected legacy PC monitor count '+str(n))
    text=replace_once(text,'#2 clk <= ~clk;', '#3.3335 clk <= ~clk;')
    text=replace_once(text,'#40000000','#1000000000')
    text=text.replace('$finish;', '$fatal(1,"Legacy platform monitor exited without arch03 acceptance");')
    text=re.sub(r'(?m)^(.*\$(?:dump|fsdbDump)\w+\s*\(.*)$',r'// ARCH03 no bulk waves: \1',text)
    text=replace_once(text,'endmodule','`include "arch03_monitor.svh"\nendmodule')
    tb.write_text(text)
    result=dict(original_root=str(source),baseline_sha256=digest,original_files=records,
                modified_files={p.relative_to(dest).as_posix():sha(p) for p in (path,tb)},
                changes=['ICB accelerator at 0x40000000','new 512 KiB SRAM at 0xa0000000',
                         '150 MHz TB clock and CPU writeback acceptance monitor'],
                competition_memory_compatibility='not_confirmed')
    (dest/'platform_manifest.json').write_text(json.dumps(result,indent=2))
    return result
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('destination',type=Path)
    a=p.parse_args();print(json.dumps(install(a.source,a.destination),indent=2))
