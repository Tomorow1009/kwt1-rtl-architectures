"""Apply reviewed team extensions to a NEW copy of the pinned official platform.

Never edits the original. Hashes all platform RTL, tb_top and source list before copying.
External vendor libraries are not copied. Python 3.6 compatible.
"""
import argparse,hashlib,json,re,shutil
from pathlib import Path
from timing_contract import TB_HALF_PERIOD_NS
from technology_binding import patch_generic_cells,mask_comments
EXPECTED='ee8bfecd81e192a974be81479ef8a01793de3e59c2e2f8769886e8e86143e56e'
ROOT=Path(__file__).resolve().parents[3]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def replace_once(text,old,new):
    if text.count(old)!=1:raise ValueError('Platform context changed: '+old[:90])
    return text.replace(old,new,1)
def select_else_interface(text):
    """Remove the pinned `ifndef FPGA wrapper branch, keeping its alternate interface.

    This is applied only to an ASIC copy. The TCM's selected interface is then
    rebound to REAL macros; the ROM's selected implementation is constant logic.
    No global FPGA define or simulation RAM is allowed to implement ASIC TCM.
    """
    lines=text.splitlines(keepends=True)
    masked=mask_comments(text).splitlines(keepends=True)
    starts=[i for i,line in enumerate(masked) if re.match(r'^\s*`ifndef\s+FPGA\b',line)]
    if len(starts)!=1:raise ValueError('Expected one pinned ifndef FPGA memory branch')
    start=starts[0];depth=0;alternative=None;finish=None
    for i in range(start,len(lines)):
        match=re.match(r'^\s*`(ifdef|ifndef|elsif|else|endif)\b',masked[i])
        if not match:continue
        token=match.group(1)
        if token in ('ifdef','ifndef'):depth+=1
        elif token=='elsif' and depth==1:raise ValueError('Unreviewed memory elsif branch')
        elif token=='else' and depth==1:
            if alternative is not None:raise ValueError('Duplicate memory else')
            alternative=i
        elif token=='endif':
            depth-=1
            if depth==0:finish=i;break
    if alternative is None or finish is None:raise ValueError('Incomplete memory conditional')
    return ''.join(lines[:start]+lines[alternative+1:finish]+lines[finish+1:])

def patch_tcm(text):
    """Select the full named TCM interface and bind it to the physical adapter."""
    text=select_else_interface(text)
    text,n=re.subn(r'\bsirv_gnrl_ram\s*#\s*\(', 'arch03_tcm_ram #(', text)
    if n!=1:raise ValueError('Expected exactly one ASIC generic TCM RAM instance')
    return text

def patch_rom(text):
    text=select_else_interface(text)
    masked=mask_comments(text)
    if len(re.findall(r'\bsirv_mrom\s*#',masked))!=1 or re.search(r'\bROM1KX32\b',masked):
        raise ValueError('Expected existing constant boot ROM implementation')
    return text

def platform_sources(platform):
    """Strict source list parser; an unfamiliar file-list directive is an error."""
    result=[]
    for raw in (platform/'vcode_rtl.f').read_text().splitlines():
        line=raw.strip()
        if not line or line.startswith('//') or line=='-sverilog':continue
        candidate=line[3:].strip() if line.startswith('-v ') else line
        # Include directories are collected separately from the pinned RTL tree.
        if candidate.startswith('+incdir+'):continue
        if not candidate.startswith('./'):
            raise ValueError('Unsupported platform file-list entry: '+line)
        path=(platform/candidate[2:]).resolve();path.relative_to(platform.resolve())
        if not path.is_file():raise ValueError('Missing platform source: '+str(path))
        if path not in result:result.append(path)
    if not result:raise ValueError('Empty platform source list')
    return result

def install(source,dest,asic=False,monitor='arch03_monitor.svh'):
    if monitor not in ('arch03_monitor.svh','arch03_sequence_monitor.svh'):
        raise ValueError('Unreviewed platform monitor')
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
    patch=(ties+'\n'+instance('arch03_shared_sram','u_arch03_shared','a3_mem_')+
           instance('arch03_icb_accel','u_arch03_accel','expl_axi_icb_'))
    text=text[:start.start()]+patch+'\n'+text[end:]
    # VCS otherwise creates implicit scalar nets at the first bus connection
    # and reports IPDW/PCWM when a later declaration attempts to widen them.
    buses=list(re.finditer(r'(?m)^\s*sirv_icb1to8_bus\s*#\s*\(',text))
    if len(buses)!=1:raise ValueError('Unexpected platform split-bus declaration')
    pos=buses[0].start();text=text[:pos]+declarations+'\n'+text[pos:]
    path.write_text(text)
    modified=[path]
    if asic:
        for name in ('itcm','dtcm'):
            ram=dest/('rtl/e203/core/e203_%s_ram.v'%name)
            ram.write_text(patch_tcm(ram.read_text()))
            modified.append(ram)
        rom=dest/'rtl/e203/mems/sirv_mrom_top.v'
        rom.write_text(patch_rom(rom.read_text()));modified.append(rom)
        generic=dest/'rtl/e203/generic/GENERIC_RVT_SMIC.v'
        mapped,binding_counts=patch_generic_cells(generic.read_text())
        generic.write_text(mapped);modified.append(generic)
    tb=dest/'tb/tb_top.v';text=tb.read_text()
    text,n=re.subn(r'(`define\s+PC_\w+\s+)[^\n]+',r"\g<1>32'hffffffff",text)
    if n!=5:raise ValueError('Unexpected legacy PC monitor count '+str(n))
    if re.search(r'`timescale\b',text):raise ValueError('Unexpected platform TB time precision')
    text='`timescale 1ns/1fs\n'+text
    text=replace_once(text,'#2 clk <= ~clk;', '#'+TB_HALF_PERIOD_NS+' clk <= ~clk;')
    text=replace_once(text,'#40000000','#1000000000')
    text=text.replace('$finish;', '$fatal(1,"Legacy platform monitor exited without arch03 acceptance");')
    text=re.sub(r'(?m)^(.*\$(?:dump|fsdbDump)\w+\s*\(.*)$',r'// ARCH03 no bulk waves: \1',text)
    text=replace_once(text,'endmodule','`include "'+monitor+'"\nendmodule')
    tb.write_text(text)
    modified.append(tb)
    result=dict(original_root=str(source),baseline_sha256=digest,original_files=records,
                modified_files={p.relative_to(dest).as_posix():sha(p) for p in modified},
                tcm_mode='asic_macro' if asic else 'legacy_functional',
                rom_mode='existing_constant_logic' if asic else 'legacy_functional',
                monitor=monitor,
                generic_cell_bindings=binding_counts if asic else None,
                asic_simulation_ready=False,
                changes=['ICB accelerator at 0x40000000','new 512 KiB SRAM at 0xa0000000',
                         '150 MHz TB clock and CPU writeback acceptance monitor'],
                competition_memory_compatibility='not_confirmed')
    (dest/'platform_manifest.json').write_text(json.dumps(result,indent=2))
    return result
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('destination',type=Path)
    p.add_argument('--asic',action='store_true',help='Replace both ASIC TCM RAM instances; does not adapt the boot TB')
    a=p.parse_args();print(json.dumps(install(a.source,a.destination,asic=a.asic),indent=2))
