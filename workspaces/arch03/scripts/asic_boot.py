"""Initial ITCM image conversion for the pinned RAMSP4096X16 functional model.

Only program and source bytes in ITCM are initialized before reset release.
Shared SRAM, accelerator memories, and expected outputs are never preloaded.
The CPU still performs every measured task transfer and arithmetic operation.
Python 3.6 standard library only; model identity is checked by server_run.vendor.
"""
import hashlib
import json
import re
from pathlib import Path

IMAGE_BYTES=262144
MACROS=32


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def image_bytes(path):
    tokens=path.read_text().split()
    if len(tokens)!=IMAGE_BYTES or any(not re.fullmatch('[0-9a-fA-F]{2}',s) for s in tokens):
        raise ValueError('Boot image must contain exactly 262144 known byte tokens')
    return bytes(int(s,16) for s in tokens)


def physical_rows(image,bank,half):
    if len(image)!=IMAGE_BYTES or not 0<=bank<8 or not 0<=half<4:
        raise ValueError('Invalid ITCM image geometry')
    rows=[]
    for row in range(512):
        packed=0
        for column in range(8):
            address=(bank*4096+row*8+column)*8+half*2
            word=image[address] | (image[address+1]<<8)
            for bit in range(16):packed|=((word>>bit)&1)<<(bit*8+column)
        rows.append(packed)
    return rows


def prepare(image_path,destination):
    image=image_bytes(image_path)
    destination.mkdir(parents=True,exist_ok=False)
    hashes={}
    for bank in range(8):
        for half in range(4):
            path=destination/('itcm_b%02d_h%d.hex'%(bank,half))
            path.write_text(''.join('%032x\n'%row for row in physical_rows(image,bank,half)),encoding='ascii')
            hashes[path.name]=sha(path)
    report=dict(schema='arch03-pinned-ramsp4096-boot-v1',image_sha256=sha(image_path),
                image_bytes=IMAGE_BYTES,macros=MACROS,rows_per_macro=512,bits_per_row=128,
                physical_bit='16-bit word bit b -> mem[address >> 3][8*b + (address & 7)]',
                scope='initial_ITCM_only',runtime_task_loading='CPU',files=hashes)
    (destination/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


def loader_include():
    lines=[
        '// Initial ITCM source image only. Never preload shared/output SRAM.',
        'reg arch03_boot_ready=0;',
        'reg [4095:0] arch03_boot_dir;',
        'integer arch03_boot_row;',
        'initial begin',
        '  if(!$value$plusargs("BOOT_DIR=%s",arch03_boot_dir)) $fatal(1,"Missing BOOT_DIR");',
        '  #0.001;',
        '  if(rst_n !== 1\'b0) $fatal(1,"ITCM preload requires reset asserted");']
    for bank in range(8):
        for half in range(4):
            memory='`ARCH03_ASIC_ITCM.banks[%d].halves[%d].memory.memory.mem'%(bank,half)
            lines += [
                '  for(arch03_boot_row=0;arch03_boot_row<512;arch03_boot_row=arch03_boot_row+1)',
                '    %s[arch03_boot_row]=128\'bx;'%memory,
                '  $readmemh({arch03_boot_dir,"/itcm_b%02d_h%d.hex"},%s);'%(bank,half,memory),
                '  for(arch03_boot_row=0;arch03_boot_row<512;arch03_boot_row=arch03_boot_row+1)',
                '    if((^%s[arch03_boot_row]) === 1\'bx) $fatal(1,"Incomplete ITCM boot macro b%d h%d");'%(memory,bank,half)]
    lines += ['  arch03_boot_ready=1;',
              '  $display("ARCH03_ASIC_BOOT_READY bytes=262144 macros=32 scope=initial_ITCM_only");',
              'end',
              'always @(posedge rst_n) if(!arch03_boot_ready) $fatal(1,"Reset released before ITCM boot image loaded");']
    return '\n'.join(lines)+'\n'


def patch_testbench(text):
    text,count=re.subn(r'(?m)^\s*`define\s+FPGA\s*$', '// ASIC branch: no FPGA define',text)
    if count!=1:raise ValueError('Expected one original TB FPGA define')
    pattern=r'(?m)^\s*`define\s+ITCM\s+`CPU_TOP\.u_e203_srams\.u_e203_itcm_ram\.u_e203_itcm_gnrl_ram\.u_sirv_sim_ram\s*$'
    text,count=re.subn(pattern,'`define ARCH03_ASIC_ITCM `CPU_TOP.u_e203_srams.u_e203_itcm_ram.u_e203_itcm_gnrl_ram',text)
    if count!=1:raise ValueError('Original ITCM hierarchy changed')
    pattern=r'(?ms)^\s*reg\s+\[7:0\]\s+itcm_mem\s*\[[^;]+;\s*initial\s+begin\s*\$readmemh\(\{testcase,\s*"\.verilog"\},\s*itcm_mem\);.*?\$display\("ITCM 0x20:[^\n]+\n\s*end\b'
    text,count=re.subn(pattern,'\n`include "arch03_asic_boot.svh"',text)
    if count!=1 or re.search(r'`ITCM\b|\bitcm_mem\b',text):
        raise ValueError('Original ITCM loader changed or remains active')
    return text
