"""Pinned-platform DMA16 integration; preserve the existing installer/baseline.

The original O4 SysMem decode is 0x80000000 with region LSB 31. The SoC
top originally terminates that *existing* interface with an empty zero response.
Expose the same ICB signals to the loading environment instead. Both RTL and
gate simulations must use these ports; never force SRAM or preload task inputs.
Python 3.6 standard library only.
"""
import hashlib
import json
import re
from pathlib import Path
from install_platform import install as install_baseline

FIELDS = [('cmd_valid',1),('cmd_ready',1),('cmd_addr',32),('cmd_read',1),
          ('cmd_wdata',32),('cmd_wmask',4),('rsp_valid',1),('rsp_ready',1),
          ('rsp_rdata',32),('rsp_err',1)]
MASTER_OUTPUTS = {'cmd_valid','cmd_addr','cmd_read','cmd_wdata','cmd_wmask','rsp_ready'}
SOURCE_BASE = 0xb0000000
SOURCE_BYTES = 46976


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def once(text, pattern, replacement, label):
    result, count = re.subn(pattern, replacement, text, flags=re.M)
    if count != 1:
        raise ValueError('%s: expected one match, got %d' % (label,count))
    return result


def declarations(prefix):
    return '\n'.join('wire %s%s%s;' % ('' if w == 1 else '[%d:0] '%(w-1),prefix,k)
                     for k,w in FIELDS)


def connections(prefix, port_prefix=''):
    return ['.%s%s(%s%s)' % (port_prefix,k,prefix,k) for k,w in FIELDS]


def instance(module, name, ports):
    return '%s %s(\n    %s\n);\n' % (module,name,',\n    '.join(ports))


def add_port(text, module, ports):
    return once(text,r'(\bmodule\s+'+module+r'\s*\()',
                lambda m:m.group(1)+'\n'+ports+'\n',module+' header')


def patch_mems(text, variant):
    if variant not in ('dma16','mmio8_reference'):
        raise ValueError('Unknown DMA16 integration variant')
    if not re.search(r'\.O4_BASE_ADDR\s*\(\s*32\s*\x27h8000_?0000\s*\)',text,re.I):
        raise ValueError('Original SysMem base changed')
    if not re.search(r'\.O4_BASE_REGION_LSB\s*\(\s*31\s*\)',text):
        raise ValueError('Original SysMem region changed')
    text=add_port(text,'e203_subsys_mems','    output wire arch03_dma_irq,')
    for k,w in FIELDS:
        text=once(text,r'(\.o4_icb_'+k+r'\s*\(\s*)a3_mem_'+k+r'(\s*\))',
                  lambda m:m.group(1)+'a3_cpu_'+k+m.group(2),'O4 '+k)
    body_start=text.index(');',text.index('module e203_subsys_mems'))+2
    wires='\n'+declarations('a3_cpu_')+'\n'+declarations('a3_dma_')+'\n'+declarations('a3_bus_')
    wires+='\nwire a3_arb_pending,a3_router_pending;\n'
    text=text[:body_start]+wires+text[body_start:]
    start=text.find('assign sysmem_icb_cmd_valid')
    stop=text.rfind('endmodule')
    if start<0 or stop<start or 'arch03_shared_sram u_arch03_shared' not in text[start:stop]:
        raise ValueError('Baseline memory installation changed')
    base=['.clk(clk)','.rst_n(rst_n)']
    patch=instance('arch03_icb_arb2','u_arch03_arb',base+
                   connections('a3_cpu_','cpu_')+connections('a3_dma_','dma_')+
                   connections('a3_bus_')+['.transaction_pending(a3_arb_pending)'])
    patch+=instance('arch03_icb_memory_router','u_arch03_router',base+
                    connections('a3_bus_')+connections('a3_mem_','mem_')+
                    connections('sysmem_icb_','src_')+['.transaction_pending(a3_router_pending)'])
    patch+=instance('arch03_shared_sram','u_arch03_shared',base+connections('a3_mem_'))
    if variant=='dma16':
        patch+=instance('arch03_dma16_accel','u_arch03_accel',base+
                        connections('expl_axi_icb_')+connections('a3_dma_','dma_')+
                        ['.irq(arch03_dma_irq)'])
    else:
        patch+=instance('arch03_icb_accel','u_arch03_accel',base+connections('expl_axi_icb_'))
        patch+='\n'.join("assign a3_dma_%s = 'b0;"%k for k in MASTER_OUTPUTS)+'\n'
        patch+="assign arch03_dma_irq=1'b0;\n"
    return text[:start]+patch+'\n'+text[stop:]


def patch_soc(text):
    ports=[]
    for k,w in FIELDS:
        direction='output' if k in MASTER_OUTPUTS else 'input'
        ports.append('    %s wire %ssysmem_icb_%s,' %
                     (direction,'' if w==1 else '[%d:0] '%(w-1),k))
    # Remove the two original local wires now declared as top interface ports.
    for k in ('cmd_valid','cmd_ready'):
        text=once(text,r'^\s*wire\s+sysmem_icb_'+k+r'\s*;\s*$',
                  '', 'original top SysMem wire '+k)
    text=add_port(text,'e203_soc_top','\n'.join(ports))
    old={'cmd_valid':'sysmem_icb_cmd_valid','cmd_ready':'sysmem_icb_cmd_ready',
         'cmd_addr':'','cmd_read':'','cmd_wdata':'','cmd_wmask':'',
         'rsp_valid':'sysmem_icb_cmd_valid','rsp_ready':'sysmem_icb_cmd_ready',
         'rsp_rdata':"32'b0",'rsp_err':"1'b0"}
    for k,previous in old.items():
        text=once(text,r'(\.sysmem_icb_'+k+r'\s*\()\s*'+re.escape(previous)+r'\s*(\))',
                  lambda m:m.group(1)+'sysmem_icb_'+k+m.group(2),'restore top '+k)
    return text


def patch_main(text):
    start=text.index(');',text.index('module e203_subsys_main'))+2
    text=text[:start]+'\nwire arch03_dma_irq;\n'+text[start:]
    text=once(text,r'(e203_subsys_mems\s+u_e203_subsys_mems\s*\()',
              lambda m:m.group(1)+'\n    .arch03_dma_irq(arch03_dma_irq),','DMA IRQ from mems')
    # All sixteen original PLIC sources are allocated. Share the existing
    # GPIOB source without removing its wire or changing the PLIC implementation.
    # Firmware must inspect DMA status before acknowledging the shared source.
    match=re.search(r'e203_subsys_plic\s+u_e203_subsys_plic\s*\([\s\S]*?\);',text)
    if not match:raise ValueError('Original PLIC instance missing')
    block=once(match.group(0),r'(\.gpioB_irq\s*\()\s*gpioB_irq\s*(\))',
               lambda m:m.group(1)+'gpioB_irq | arch03_dma_irq'+m.group(2),'shared GPIOB/DMA IRQ')
    return text[:match.start()]+block+text[match.end():]


def patch_tb(text):
    text=once(text,r'(\bmodule\s+tb_top\s*(?:\(\s*\))?\s*;)',
              lambda m:m.group(1)+'\n'+declarations('a3_source_')+'\n','TB source signals')
    text=once(text,r'(e203_soc_top\s+u_e203_soc_top\s*\()',
              lambda m:m.group(1)+'\n    '+',\n    '.join(connections('a3_source_','sysmem_icb_'))+',',
              'TB existing SysMem interface')
    if text.count('`include "arch03_monitor.svh"')!=1:
        raise ValueError('Expected baseline monitor before replacement')
    return text.replace('`include "arch03_monitor.svh"','`include "arch03_dma16_monitor.svh"')


def install(source, destination, variant='dma16'):
    if variant!='dma16':
        raise ValueError('Only DMA16 is integrated; MMIO8 reference needs its own loader/monitor validation')
    source=Path(source);destination=Path(destination)
    manifest=install_baseline(source,destination,asic=True,asic_boot=True)
    changes=[('rtl/e203/subsys/e203_subsys_mems.v',lambda s:patch_mems(s,variant)),
             ('rtl/e203/soc/e203_soc_top.v',patch_soc),
             ('rtl/e203/subsys/e203_subsys_main.v',patch_main),('tb/tb_top.v',patch_tb)]
    for name,patch in changes:
        path=destination/name
        path.write_text(patch(path.read_text()))
        manifest['modified_files'][name]=sha(path)
    manifest['dma16']={'variant':variant,'source_base':SOURCE_BASE,'source_bytes':SOURCE_BYTES,
        'shared_base':0xa0000000,'shared_bytes':524288,'layout_id':0x00100001,
        'input_bytes':46976,'output_bytes':50688,'outstanding':1,
        'original_sysmem_decode':{'base':0x80000000,'region_lsb':31},
        'loading_interface':'restored original sysmem_icb at SoC boundary, no private SRAM port',
        'source_model':'testbench file pre-read; synchronous ICB; no input ITCM preload',
        'irq':'DMA OR original GPIOB PLIC source; original GPIOB wire retained',
        'sram_macros':{'4096x16':130,'128x16':32 if variant=='dma16' else 8},
        'implementation_sha256':sha(Path(__file__)),
        'asic_simulation_verified':False,'timing_verified':False}
    manifest['competition_memory_compatibility']='original O4 decode verified; restored SysMem loading interface requires current integration verification'
    (destination/'platform_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest
