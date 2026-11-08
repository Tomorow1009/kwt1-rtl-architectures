"""Build independent A/B/A E203 firmware with poison and actual-driver timeout.

This prepares boot images only. CPU execution requires the dedicated sequence
monitor; the old single-task monitor must not accept these images.
"""
import argparse
import json
import struct
import subprocess
from pathlib import Path
from build_firmware import SW,sha
from batch_soc import image_base


def task_data(folder):
    layout=json.loads((folder/'layout.json').read_text())
    for name,digest in layout['sha256'].items():
        if sha(folder/name)!=digest:raise ValueError('Sequence vector changed: '+str(folder/name))
    words=[int(x,16) for x in (folder/'load.hex').read_text().split()]
    if len(words)!=23488 or any(not 0<=v<=65535 for v in words):raise ValueError('Sequence load word format')
    if type(layout['shift']) is not int or not 0<=layout['shift']<=31:raise ValueError('Sequence shift')
    return layout,words


def main():
    p=argparse.ArgumentParser();p.add_argument('--zig',required=True,type=Path)
    p.add_argument('--data',required=True,type=Path);p.add_argument('--output',required=True,type=Path)
    p.add_argument('--cases',nargs='+',default=['layer_01']);p.add_argument('--next-case',default='layer_12')
    a=p.parse_args()
    if len(set(a.cases))!=len(a.cases):raise ValueError('Duplicate primary sequence case')
    for name in a.cases+[a.next_case]:
        if Path(name).name!=name or not name or name in ('.','..'):raise ValueError('Invalid sequence case name')
    secondary,second_words=task_data(a.data/a.next_case)
    primary={name:task_data(a.data/name) for name in a.cases}
    a.output.mkdir(parents=True,exist_ok=False);elf=a.output/'driver.elf'
    command=[str(a.zig),'cc','-target','riscv32-freestanding-none','-mcpu=generic_rv32+m+a+c',
             '-mabi=ilp32','-ffreestanding','-fno-stack-protector','-fno-builtin','-Os',
             '-Wall','-Wextra','-Werror','-nostdlib','-mno-relax','-Wl,-T,'+str(SW/'link.ld'),
             str(SW/'start.S'),str(SW/'kwt.c'),str(SW/'main_sequence.c'),'-o',str(elf)]
    subprocess.run(command,check=True)
    base=image_base(elf);images={}
    for name,(layout,words) in primary.items():
        memory=bytearray(base)
        struct.pack_into('<II',memory,0xfff0,layout['shift'],secondary['shift'])
        struct.pack_into('<23488H',memory,0x10000,*words)
        struct.pack_into('<23488H',memory,0x20000,*second_words)
        target=a.output/(name+'.verilog')
        target.write_text(''.join('%02x\n'%x for x in memory),encoding='ascii')
        images[name]=dict(sha256=sha(target),input_sha256=sha(a.data/name/'load.hex'),shift=layout['shift'],
                          next_case=a.next_case,next_input_sha256=sha(a.data/a.next_case/'load.hex'),
                          next_shift=secondary['shift'],tasks=[name,a.next_case,name])
    report=dict(run_mode='sequence_cpu_v1',cpu_executed=False,
                compiler_version=subprocess.check_output([str(a.zig),'version']).decode().strip(),
                compiler_sha256=sha(a.zig),command=command,elf_sha256=sha(elf),
                source_sha256={x.name:sha(x) for x in SW.iterdir() if x.is_file()},images=images,
                protocol=dict(task_indices=[1,2,3],first_source='0x80010000',second_source='0x80020000',
                              poison_words=17,timeout_cycles=1,phase_mailbox='0xa001f028',
                              poison_begin='0x504f4931',poison_end='0x504f4932',
                              timeout_begin='0x54494d31',timeout_end='0x54494d32'))
    (a.output/'manifest.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print('SEQUENCE_FIRMWARE_BUILT images=%d tasks_per_image=3 cpu_execution_not_yet_verified'%len(images),flush=True)


if __name__=='__main__':main()
