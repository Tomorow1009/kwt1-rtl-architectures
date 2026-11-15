"""Program-only polling N1 X14/W12/b32 sequence firmware; no reset between A/B/A.

Input files are read only for immutable identities and shift metadata. Their
contents never enter the ELF or ITCM image. Python 3.6 standard library only.
"""
import argparse
import n1_codec as codec
import hashlib
import os
from pathlib import Path
import struct
import subprocess
from build_p80_firmware import elf_image, require, save, sha
from n1_data import CASES14, source_case, decode_group8, hex_values, read
from asic_boot import image_bytes

ROOT=Path(__file__).resolve().parents[3]
SW=ROOT/'workspaces/arch03/sw'
MAGIC=0x54385351
FIRMWARE_SOURCES={'workspaces/arch03/sw/'+name for name in
    ('kwt_p80.h','kwt_p80.c','main_p80_sequence.c','start_icb32_sequence.S','link.ld')}
FIRMWARE_SOURCES.update({'workspaces/arch03/scripts/build_p80_sequence.py',
    'workspaces/arch03/scripts/build_p80_firmware.py','workspaces/arch03/scripts/n1_data.py',
    'workspaces/arch03/P80_ABI.md','workspaces/arch03/scripts/n1_codec.py',
    'workspaces/arch03/scripts/systolic_b_codec.py','workspaces/arch03/scripts/dma16_batch.py',
    'workspaces/arch03/scripts/systolic_b_data.py','workspaces/arch03/scripts/icb32_codec.py',
    'workspaces/arch03/scripts/icb32_data.py'})


def task_identity(source, source_id):
    source=Path(source)
    require(source.name in CASES14 and source_id in (0,1), 'Invalid sequence case/source ID')
    meta,words,_,_=source_case(source)
    x,w,bias=decode_group8(words)
    packed=[value & 65535 for row in x for value in row]
    for tile in range(16):
        packed.extend(w[k][tile*16+lane] & 65535 for k in range(64) for lane in range(16))
        for lane in range(16):
            value=bias[tile*16+lane]
            packed.extend((value & 65535,(value>>16)&65535,255 if value<0 else 0))
    raw=struct.pack('<23488H',*packed)
    payload=codec.encode(raw)
    require(codec.decode(payload)==raw and codec.verify_coordinates(raw,codec.decode_wire(payload))==23488,'Sequence codec/coordinate mismatch')
    count=len(payload)//4
    load32=''.join('%08x\n'%word for word in struct.unpack('<%dI'%count,payload)).encode('ascii')
    return dict(case=source.name,source_id=source_id,shift=meta['format']['shift'],descriptor=(count<<17)|(source_id<<16)|meta['format']['shift'],encoded_bytes=len(payload),
        source_layout_sha256=sha(source/'layout.json'),source_sha256={name:record['sha256'] for name,record in meta['files'].items()},
        load32_canonical_lf_sha256=hashlib.sha256(load32).hexdigest(),
        load_payload_sha256=hashlib.sha256(payload).hexdigest(),runtime_layout='n1_x14_w12_b32_lossless_v4',numeric_format='0x000e0c20',layout_id=0x00100004,
        runtime_file_role='external_ICB_source_only_not_ITCM')


def verify_runtime_sources(manifest, first_path, second_path):
    """Check token payloads independently of CRLF/LF, then freeze exact files."""
    require(manifest['run_mode']=='cpu_p80_sequence_v4','Wrong sequence firmware')
    records={}
    for key,path in zip(('A','B'),(Path(first_path),Path(second_path))):
        task=manifest['tasks'][key]
        words=hex_values(path,task['encoded_bytes']//4,32)
        payload=struct.pack('<%dI'%len(words),*words)
        canonical=''.join('%08x\n'%word for word in words).encode('ascii')
        require(hashlib.sha256(payload).hexdigest()==task['load_payload_sha256'] and
                hashlib.sha256(canonical).hexdigest()==task['load32_canonical_lf_sha256'],
                'Sequence source differs from bound task '+key)
        records[key]=dict(path=str(path.resolve()),file_sha256=sha(path),descriptor=task['descriptor'],
            source_id=task['source_id'],shift=task['shift'],load_payload_sha256=task['load_payload_sha256'])
    return records


def metadata_image(base, first, second, timeout):
    require(len(base)==262144 and not any(base[0xfff0:]), 'Invalid program-only base image')
    require(type(timeout) is int and 4096<=timeout<=32768, 'Short timeout outside declared test range')
    for source_id,item in enumerate((first,second)):
        require(type(item['shift']) is int and item['shift']==10 and item['source_id']==source_id and
                32<=item['encoded_bytes']<=47008 and item['encoded_bytes']%4==0 and
                item['descriptor']==((item['encoded_bytes']//4)<<17)|(source_id<<16)|item['shift'], 'Invalid sequence descriptor')
    image=bytearray(base)
    struct.pack_into('<4I',image,0xfff0,MAGIC,first['descriptor'],second['descriptor'],timeout)
    require(not any(image[0x10000:]), 'Task inputs leaked into sequence boot')
    return image


def symbols(raw):
    header=struct.unpack_from('<HHIIIIIHHHHHH',raw,16)
    require(header[10]==40 and header[5]+header[10]*header[11]<=len(raw), 'Invalid ELF section headers')
    sections=[struct.unpack_from('<10I',raw,header[5]+index*40) for index in range(header[11])]
    result={}
    for section in sections:
        if section[1]!=2:continue
        require(section[9]==16 and section[6]<len(sections) and section[4]+section[5]<=len(raw), 'Invalid symbol section')
        strings=sections[section[6]]
        require(strings[4]+strings[5]<=len(raw), 'Invalid string section')
        names=raw[strings[4]:strings[4]+strings[5]]
        for offset in range(section[4],section[4]+section[5],16):
            name,value,size,info,other,index=struct.unpack_from('<IIIBBH',raw,offset)
            require(name<len(names), 'Invalid ELF symbol name')
            end=names.find(b'\0',name);require(end>=0, 'Unterminated ELF symbol')
            result[names[name:end].decode('ascii')]=value
    return result


def verify_fault_sites(raw, base):
    names=symbols(raw)
    required=('sequence_fault_store','sequence_fault_resume','icb32_sequence_trap','trap_entry')
    require(all(name in names for name in required), 'Missing sequence trap symbols')
    store=names['sequence_fault_store'];resume=names['sequence_fault_resume']
    require(resume==store+4 and 0x80000000<=store<0x8000ffec, 'Unexpected guarded store/resume span')
    require(struct.unpack_from('<I',base,store-0x80000000)[0]==0x0062a023, 'Guarded instruction is not 32-bit sw t1,0(t0)')
    return {name:'0x%08x'%names[name] for name in required}


def verify_firmware(firmware,source_root=ROOT):
    """Return (manifest, sequence.verilog Path), suitable for immutable packaging."""
    firmware,source_root=Path(firmware),Path(source_root).resolve()
    manifest=read(firmware/'manifest.json')
    require(manifest.get('run_mode')=='cpu_p80_sequence_v4' and manifest.get('polling_only') is True and
            manifest.get('irq_enabled') is False and
            manifest.get('physical_boot_policy')=='firmware_only_no_task_inputs' and
            manifest.get('numeric_format')=='0x000e0c20' and manifest.get('peripheral_id')=='0x4b57530b','Wrong sequence firmware mode')
    require(manifest.get('capability')=='0x000905bf' and
            manifest['configuration']['layout_id']==0x00100004 and
            manifest['configuration']['row_lanes']==5 and manifest['configuration']['transaction_metadata_depth'] in (2,4,8),'Wrong N1 sequence configuration')
    require(set(manifest['source_sha256'])==FIRMWARE_SOURCES,'Missing sequence firmware source identities')
    for rel,digest in manifest['source_sha256'].items():
        path=(source_root/rel).resolve();path.relative_to(source_root)
        require(sha(path)==digest,'Sequence firmware source changed: '+rel)
    require(set(manifest['tasks'])=={'A','B'},'Sequence needs A/B task identities')
    first,second=manifest['tasks']['A'],manifest['tasks']['B']
    require(first['case']!=second['case'] and first['case'] in CASES14 and second['case'] in CASES14 and
            first['load_payload_sha256']!=second['load_payload_sha256'],'Sequence A/B must be distinct')
    raw=(firmware/'driver.elf').read_bytes()
    require(sha(firmware/'driver.elf')==manifest['elf_sha256'],'Sequence ELF changed')
    base,segments=elf_image(raw)
    require(segments==manifest['segments'] and verify_fault_sites(raw,base)==manifest['fault_sites'],
            'Sequence ELF segments/fault sites changed')
    short_timeout=manifest['configuration']['short_timeout_cycles']
    image=metadata_image(base,first,second,short_timeout)
    require(manifest['metadata']==dict(offset=0xfff0,words=[MAGIC,first['descriptor'],second['descriptor'],short_timeout]),
            'Sequence metadata differs from task identity')
    info=manifest['image'];path=firmware/'sequence.verilog';binary=firmware/'sequence.bin'
    require(info['image_bytes']==262144 and info['task_input_region_nonzero_bytes']==0 and
            sha(path)==info['sha256'] and sha(binary)==info['binary_sha256'] and
            image_bytes(path)==image and binary.read_bytes()==image,'Sequence program-only boot changed')
    require(manifest['phases']==['source_misaligned','input_out_of_bounds','input_output_overlap',
        'wrong_input_length','wrong_output_length','cancel_during_initial_loading',
        'polling_timeout_and_drain','A','B','A'],'Sequence phase contract changed')
    return manifest,path


def build(zig,output,data,first_case='layer_01',second_case='rounding',short_timeout=4096,
          timeout=100000000,cancel_timeout=1000000,transaction_depth=4):
    zig,output,data=Path(zig).resolve(),Path(output).resolve(),Path(data).resolve()
    require(transaction_depth in (2,4,8),'Invalid P80 depth')
    require(not output.exists(), 'Output exists; retain old sequence artifacts')
    require(first_case!=second_case and first_case in CASES14 and second_case in CASES14, 'A and B must be distinct cases')
    require(type(timeout) is int and type(cancel_timeout) is int and 0<timeout<(1<<63) and
            0<cancel_timeout<(1<<63), 'Invalid sequence timeout')
    first,second=task_identity(data/first_case,0),task_identity(data/second_case,1)
    require(first['load_payload_sha256']!=second['load_payload_sha256'], 'A and B source payloads must differ')
    metadata_image(bytearray(262144),first,second,short_timeout)
    sources=[SW/name for name in ('kwt_p80.h','kwt_p80.c','main_p80_sequence.c','start_icb32_sequence.S','link.ld')]
    sources += [Path(__file__).resolve(),Path(__file__).resolve().with_name('build_p80_firmware.py'),
                Path(__file__).resolve().with_name('n1_data.py'),ROOT/'workspaces/arch03/P80_ABI.md',ROOT/'workspaces/arch03/scripts/n1_codec.py']
    sources=[ROOT/rel for rel in sorted(FIRMWARE_SOURCES)]
    before={path.relative_to(ROOT).as_posix():sha(path) for path in sources}
    output.mkdir(parents=True)
    elf=output/'driver.elf'
    command=[str(zig),'cc','-target','riscv32-freestanding-none','-mcpu=generic_rv32+m+a+c',
        '-mabi=ilp32','-ffreestanding','-fno-stack-protector','-fno-builtin','-Os','-g','-Wall','-Wextra','-Werror',
        '-nostdlib','-mno-relax','-Wl,-T,'+str(SW/'link.ld'),'-DKWT_P80_TRANSACTION_DEPTH=%du'%transaction_depth,'-DKWT_ICB32_USE_IRQ=0',
        '-DKWT_SEQUENCE_TIMEOUT_CYCLES=%dull'%timeout,
        '-DKWT_SEQUENCE_CANCEL_TIMEOUT_CYCLES=%dull'%cancel_timeout]
    command += [str(SW/name) for name in ('start_icb32_sequence.S','kwt_p80.c','main_p80_sequence.c')]+['-o',str(elf)]
    environment=os.environ.copy()
    environment['ZIG_LOCAL_CACHE_DIR']=str(output/'zig-local-cache')
    environment['ZIG_GLOBAL_CACHE_DIR']=str(ROOT/'local_runs/zig-n1-sequence-cache')
    save(output/'build_command.json',command)
    compiled=subprocess.run(command,env=environment,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    (output/'build.log').write_bytes(compiled.stdout)
    require(compiled.returncode==0,'Sequence compiler failed; inspect preserved build.log')
    raw=elf.read_bytes();base,segments=elf_image(raw)
    fault_sites=verify_fault_sites(raw,base)
    image=metadata_image(base,first,second,short_timeout)
    (output/'sequence.bin').write_bytes(image)
    (output/'sequence.verilog').write_bytes(''.join('%02x\n'%byte for byte in image).encode('ascii'))
    require(before=={path.relative_to(ROOT).as_posix():sha(path) for path in sources}, 'Sequence source changed during build')
    require(first==task_identity(data/first_case,0) and second==task_identity(data/second_case,1), 'Sequence data changed during build')
    report=dict(run_mode='cpu_p80_sequence_v4',status='compiled_only',polling_only=True,irq_enabled=False,
        compiler_sha256=sha(zig),compiler_version=subprocess.check_output([str(zig),'version'],env=environment).decode().strip(),
        command=command,elf_sha256=sha(elf),source_sha256=before,segments=segments,fault_sites=fault_sites,
        physical_boot_policy='firmware_only_no_task_inputs',numeric_format='0x000e0c20',
        peripheral_id='0x4b57530b',capability='0x000905bf',tasks=dict(A=first,B=second),
        metadata=dict(offset=0xfff0,words=[MAGIC,first['descriptor'],second['descriptor'],short_timeout]),
        image=dict(binary_sha256=sha(output/'sequence.bin'),sha256=sha(output/'sequence.verilog'),
                   image_bytes=262144,task_input_region_nonzero_bytes=0),
        configuration=dict(transaction_metadata_depth=transaction_depth,layout_id=0x00100004,row_lanes=5,timeout_cycles=timeout,cancel_timeout_cycles=cancel_timeout,short_timeout_cycles=short_timeout),
        phases=['source_misaligned','input_out_of_bounds','input_output_overlap','wrong_input_length','wrong_output_length',
                'cancel_during_initial_loading','polling_timeout_and_drain','A','B','A'],
        runtime_selection='mail33 successful ACK selects source; mail32 arms phase; no task transfer before source VALID',
        cpu_executed=False,trap_recovery_executed=False,cancel_executed=False,timeout_recovery_executed=False,
        no_reset_ABA_verified=False,rtl_verified=False,timing_verified=False,system_power_verified=False)
    save(output/'manifest.json',report)
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--zig',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--data',type=Path,required=True)
    p.add_argument('--transaction-depth',type=int,choices=(2,4,8),default=4)
    p.add_argument('--first-case',default='layer_01');p.add_argument('--second-case',default='rounding')
    p.add_argument('--short-timeout-cycles',type=int,default=4096)
    a=p.parse_args()
    m=build(a.zig,a.output,a.data,a.first_case,a.second_case,a.short_timeout_cycles,transaction_depth=a.transaction_depth)
    print('P80_SEQUENCE_COMPILED stages=%d polling_only=true cpu_executed=false'%len(m['phases']))


if __name__=='__main__':main()
