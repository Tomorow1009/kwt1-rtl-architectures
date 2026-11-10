"""Export committed ICB32 sources, build firmware from exported LF bytes, package.

Only source, checked 14-case data and program-only firmware enter the archive.
No credentials, vendor libraries, compiler caches, chat or run logs are copied.
"""
import argparse
import datetime
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import zipfile
from package import ROOT,git,sha
from package_dma16 import verify_review_document
from icb32_soc import verify_firmware
from dma16_batch import CASES14,source_case


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data',required=True,type=Path)
    parser.add_argument('--zig',required=True,type=Path)
    parser.add_argument('--rows',type=int,choices=(1,4),default=4)
    parser.add_argument('--prefetch',type=int,choices=(0,1),default=1)
    parser.add_argument('--member',required=True)
    parser.add_argument('--contention',action='store_true',help='Include isolated polling stress firmware, outside performance PPA')
    parser.add_argument('--sequence',action='store_true',help='Include R4 polling cancel/recovery/A-B-A firmware, outside performance PPA')
    args=parser.parse_args()
    if args.sequence and args.rows!=4:raise ValueError('This sequence diagnostic is for R4 only')
    if not re.fullmatch('[A-Za-z0-9_-]{1,60}',args.member):raise ValueError('Member identifier')
    if git('status','--porcelain'):raise ValueError('Commit source before making a new immutable package')
    commit=git('rev-parse','HEAD')
    for name in CASES14:source_case(args.data/name)
    name=args.member+'-icb32-r%d-'%args.rows+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')+'-'+commit[:12]
    folder=ROOT/'local_runs'/name;folder.mkdir()
    prefixes=('workspaces/arch02/','workspaces/arch03/',
        'architectures/arch01_serial_mac/v1.3.0/KWT1/model_data/outputs/real_sample_001/')
    extra=('handoff/team/server_config.json','handoff/team/unpack.py',
           'handoff/team/evidence/UNDERGRAD_D3_SERVER_20261109.json')
    for rel in git('ls-files').splitlines():
        if rel.startswith(prefixes) or rel in extra:
            target=folder/rel;target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(subprocess.check_output(['git','-c','safe.directory='+ROOT.as_posix(),
                'show',commit+':'+rel],cwd=str(ROOT)))
    verify_review_document(folder)
    # Build in a separate local folder so transient compiler caches cannot be
    # accidentally swept into the competition package.
    build_folder=ROOT/'local_runs'/(name+'-firmware-build')
    command=[sys.executable,str(folder/'workspaces/arch03/scripts/build_icb32_firmware.py'),
        '--zig',str(args.zig.resolve()),'--output',str(build_folder),'--rows',str(args.rows),
        '--prefetch',str(args.prefetch),'--irq-config',str(folder/'workspaces/arch03/irq_mapping.json'),
        '--shifts','11','12']
    log=ROOT/'local_runs'/(name+'-firmware-build.log')
    with log.open('w') as out:
        subprocess.check_call(command,cwd=str(folder),stdout=out,stderr=subprocess.STDOUT)
    # The compiler's global cache path is outside the exported source prefixes;
    # it is explicitly excluded from the allowlisted archive below.
    meta,_=verify_firmware(build_folder,folder)
    firmware=folder/'firmware';firmware.mkdir()
    for filename in ['driver.elf']+[n+suffix for n in meta['images'] for suffix in ('.verilog','.bin')]:
        shutil.copyfile(str(build_folder/filename),str(firmware/filename))
    meta.pop('command',None)
    (firmware/'manifest.json').write_text(json.dumps(meta,indent=2)+'\n',encoding='utf8')
    verify_firmware(firmware,folder)
    if args.contention:
        stress_build=ROOT/'local_runs'/(name+'-contention-build')
        command=[sys.executable,str(folder/'workspaces/arch03/scripts/build_icb32_contention.py'),
            '--zig',str(args.zig.resolve()),'--output',str(stress_build),'--rows',str(args.rows)]
        with (ROOT/'local_runs'/(name+'-contention-build.log')).open('x') as out:
            subprocess.check_call(command,cwd=str(folder),stdout=out,stderr=subprocess.STDOUT)
        stress_meta,_=verify_firmware(stress_build,folder)
        stress=folder/'firmware_contention';stress.mkdir()
        for filename in ['driver.elf']+[n+suffix for n in stress_meta['images'] for suffix in ('.verilog','.bin')]:
            shutil.copyfile(str(stress_build/filename),str(stress/filename))
        stress_meta.pop('command',None)
        (stress/'manifest.json').write_text(json.dumps(stress_meta,indent=2)+'\n',encoding='utf8')
        verify_firmware(stress,folder)
    if args.sequence:
        from build_icb32_sequence import verify_firmware as verify_sequence
        sequence_build=ROOT/'local_runs'/(name+'-sequence-build')
        command=[sys.executable,str(folder/'workspaces/arch03/scripts/build_icb32_sequence.py'),
            '--zig',str(args.zig.resolve()),'--output',str(sequence_build),'--data',str(args.data.resolve())]
        with (ROOT/'local_runs'/(name+'-sequence-build.log')).open('x') as out:
            subprocess.check_call(command,cwd=str(folder),stdout=out,stderr=subprocess.STDOUT)
        sequence_meta,_=verify_sequence(sequence_build,folder)
        sequence=folder/'firmware_sequence';sequence.mkdir()
        for filename in ('driver.elf','sequence.bin','sequence.verilog'):
            shutil.copyfile(str(sequence_build/filename),str(sequence/filename))
        sequence_meta.pop('command',None)
        (sequence/'manifest.json').write_text(json.dumps(sequence_meta,indent=2)+'\n',encoding='utf8')
        verify_sequence(sequence,folder)
    for case in CASES14:
        shutil.copytree(str(args.data/case),str(folder/'validated_data'/case))
        source_case(folder/'validated_data'/case)
    allowed_prefixes=prefixes+('firmware/','firmware_contention/','firmware_sequence/','validated_data/')
    paths=[]
    for path in sorted(folder.rglob('*')):
        if path.is_file():
            rel=path.relative_to(folder).as_posix()
            if rel.startswith(allowed_prefixes) or rel in extra:paths.append(path)
    files={p.relative_to(folder).as_posix():sha(p) for p in paths}
    manifest=dict(source_commit=commit,member=args.member,architecture='arch03_icb32',row_lanes=args.rows,
        files=files,runtime_layout='arch03-icb32-lossless-v2',task_input_boot_bytes=0,
        firmware_irq=True,input_data_format='original14 coordinate-checked tile16 then lossless encode per task',
        platform_dependency='pinned official external source; strict ASIC installer checks full RTL fingerprint',
        cpu_execution_verified=False,timing_verified=False,official_precision_verified=False)
    manifest_path=folder/'manifest.json';manifest_path.write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf8')
    archive=folder.with_suffix('.zip')
    with zipfile.ZipFile(str(archive),'w',zipfile.ZIP_DEFLATED) as output:
        for path in paths+[manifest_path]:output.write(str(path),name+'/'+path.relative_to(folder).as_posix())
    # Verify all archive entries and bytes against the explicit manifest; no
    # vendor model or compiler-cache path can slip in through a recursive zip.
    with zipfile.ZipFile(str(archive)) as check:
        import hashlib
        wanted={name+'/'+rel for rel in files}|{name+'/manifest.json'}
        if set(check.namelist())!=wanted:raise ValueError('Archive file allowlist mismatch')
        for rel,digest in files.items():
            if hashlib.sha256(check.read(name+'/'+rel)).hexdigest()!=digest:raise ValueError('Archive hash mismatch '+rel)
    receipt=dict(source_commit=commit,archive=archive.name,bytes=archive.stat().st_size,
        sha256=sha(archive),files=len(files),row_lanes=args.rows,hardware_executed=False,archive_verified=True)
    (folder.parent/(name+'.receipt.json')).write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8')
    print(json.dumps(receipt,indent=2))


if __name__=='__main__':main()
