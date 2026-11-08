"""Build real RV32 C driver ELF and official-TB-compatible byte HEX images."""
import argparse,hashlib,json,struct,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
SW=ROOT/'workspaces/arch03/sw'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('--zig',type=Path,required=True)
    p.add_argument('--data',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    elf=a.output/'driver.elf'
    command=[str(a.zig),'cc','-target','riscv32-freestanding-none','-mcpu=generic_rv32+m+a+c',
             '-mabi=ilp32','-ffreestanding','-fno-stack-protector','-fno-builtin','-Os',
             '-Wall','-Wextra','-Werror','-nostdlib','-mno-relax','-Wl,-T,'+str(SW/'link.ld'),
             str(SW/'start.S'),str(SW/'kwt.c'),str(SW/'main.c'),'-o',str(elf)]
    subprocess.run(command,check=True)
    raw=elf.read_bytes()
    if raw[:7]!=b'\x7fELF\x01\x01\x01':raise ValueError('Expected ELF32 little-endian')
    header=struct.unpack_from('<HHIIIIIHHHHHH',raw,16)
    if header[1]!=243 or header[3]!=0x80000000:raise ValueError('Wrong architecture or entry')
    image=bytearray(262144)
    for i in range(header[9]):
        typ,off,va,pa,filesz,memsz,flags,align=struct.unpack_from('<IIIIIIII',raw,header[4]+i*header[8])
        if typ!=1 or not filesz:continue
        if not 0x80000000<=pa<pa+filesz<=0x8000fff0:raise ValueError('Unexpected load segment')
        image[pa-0x80000000:pa-0x80000000+filesz]=raw[off:off+filesz]
    images={}
    for task in sorted(a.data.iterdir()):
        if not (task/'layout.json').is_file():continue
        info=json.loads((task/'layout.json').read_text())
        words=[int(x,16) for x in (task/'load.hex').read_text().split()]
        if len(words)!=23488 or sha(task/'load.hex')!=info['sha256']['load.hex']:raise ValueError('Input hash/count')
        memory=bytearray(image);struct.pack_into('<I',memory,0xfff0,info['shift'])
        struct.pack_into('<23488H',memory,0x10000,*words)
        target=a.output/(task.name+'.verilog')
        target.write_text(''.join('%02x\n'%x for x in memory),encoding='ascii')
        images[task.name]=dict(sha256=sha(target),input_sha256=sha(task/'load.hex'),shift=info['shift'])
    report=dict(run_mode='single_cpu_v2',compiler_version=subprocess.check_output([str(a.zig),'version']).decode().strip(),
                compiler_sha256=sha(a.zig),command=command,elf_sha256=sha(elf),
                source_sha256={x.name:sha(x) for x in SW.iterdir() if x.is_file()},images=images)
    (a.output/'manifest.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print('FIRMWARE_BUILT images=%d cpu_execution_not_yet_verified'%len(images))
if __name__=='__main__':main()
