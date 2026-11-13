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
from t64_soc import verify_firmware
from n1_data import CASES14,source_case


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data',required=True,type=Path)
    parser.add_argument('--zig',required=True,type=Path)
    parser.set_defaults(rows=4)
    parser.add_argument('--layout',type=int,choices=(4,),default=4)
    parser.add_argument('--prefetch',type=int,choices=(0,1),default=1)
    parser.add_argument('--diagnostics',action='store_true',help='Include separately compiled CPU contention and T64 recovery firmware')
    parser.add_argument('--member',required=True)
    args=parser.parse_args()
    if not re.fullmatch('[A-Za-z0-9_-]{1,60}',args.member):raise ValueError('Member identifier')
    if git('status','--porcelain'):raise ValueError('Commit source before making a new immutable package')
    commit=git('rev-parse','HEAD')
    for name in CASES14:source_case(args.data/name)
    name=args.member+'-t64-v%d-'%args.layout+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')+'-'+commit[:12]
    folder=ROOT/'local_runs'/name;folder.mkdir()
    prefixes=('workspaces/arch02/','workspaces/arch03/','docs/data/x14-w12-b32/','tools/kwt-x14-w12-b32/',
        'architectures/arch01_serial_mac/v1.3.0/KWT1/model_data/outputs/real_sample_001/')
    extra=('handoff/team/server_config.json','handoff/team/unpack.py',
           'handoff/team/evidence/UNDERGRAD_D3_SERVER_20261109.json')
    exported=set()
    for rel in git('ls-files').splitlines():
        if rel.startswith(prefixes) or rel in extra:
            if '__pycache__' in Path(rel).parts or Path(rel).suffix in ('.pyc','.pyo'):
                raise ValueError('Tracked Python cache must not enter a source package')
            target=folder/rel;target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(subprocess.check_output(['git','-c','safe.directory='+ROOT.as_posix(),
                'show',commit+':'+rel],cwd=str(ROOT)))
            exported.add(rel)
    verify_review_document(folder)
    # Build in a separate local folder so transient compiler caches cannot be
    # accidentally swept into the competition package.
    build_folder=ROOT/'local_runs'/(name+'-firmware-build')
    command=[sys.executable,str(folder/'workspaces/arch03/scripts/build_t64_firmware.py'),
        '--zig',str(args.zig.resolve()),'--output',str(build_folder),'--rows',str(args.rows),
        '--prefetch',str(args.prefetch),'--irq-config',str(folder/'workspaces/arch03/irq_mapping.json'),
        '--layout',str(args.layout),'--shifts','10']
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
    for case in CASES14:
        shutil.copytree(str(args.data/case),str(folder/'validated_data'/case))
        source_case(folder/'validated_data'/case)
    diagnostic_identities={}
    if args.diagnostics:
        from build_t64_sequence import verify_firmware as verify_sequence
        for variant in ('contention','sequence'):
            diagnostic_build=ROOT/'local_runs'/(name+'-'+variant+'-build')
            command=[sys.executable,str(folder/'workspaces/arch03/scripts'/('build_t64_'+variant+'.py')),
                '--zig',str(args.zig.resolve()),'--output',str(diagnostic_build)]
            if variant=='contention':command += ['--layout',str(args.layout)]
            else:command += ['--data',str(folder/'validated_data')]
            with (ROOT/'local_runs'/(name+'-'+variant+'-build.log')).open('w') as out:
                subprocess.check_call(command,cwd=str(folder),stdout=out,stderr=subprocess.STDOUT)
            if variant=='sequence':
                diagnostic,_=verify_sequence(diagnostic_build,folder)
                filenames=['driver.elf','sequence.bin','sequence.verilog']
            else:
                diagnostic,_=verify_firmware(diagnostic_build,folder)
                if diagnostic.get('performance_firmware') is not False:raise ValueError('Diagnostic firmware misclassified')
                filenames=['driver.elf']+[n+suffix for n in diagnostic['images'] for suffix in ('.verilog','.bin')]
            destination=folder/('firmware_'+variant);destination.mkdir()
            for filename in filenames:shutil.copyfile(str(diagnostic_build/filename),str(destination/filename))
            diagnostic.pop('command',None)
            (destination/'manifest.json').write_text(json.dumps(diagnostic,indent=2)+'\n',encoding='utf8')
            if variant=='sequence':verify_sequence(destination,folder)
            else:verify_firmware(destination,folder)
            diagnostic_identities[variant]=sha(destination/'manifest.json')
    runtime_prefixes=('firmware/','validated_data/','firmware_contention/','firmware_sequence/')
    paths=[]
    for path in sorted(folder.rglob('*')):
        if path.is_file():
            rel=path.relative_to(folder).as_posix()
            # Builders import the exported Python sources and may create
            # __pycache__. Only exact Git exports or explicit runtime assets
            # belong in the immutable archive, never generated source caches.
            if rel in exported or rel.startswith(runtime_prefixes):paths.append(path)
    files={p.relative_to(folder).as_posix():sha(p) for p in paths}
    manifest=dict(source_commit=commit,member=args.member,architecture='arch03_t64',row_lanes=args.rows,
        files=files,runtime_layout='arch03-t64-v%d-with-lossless-codec'%args.layout,task_input_boot_bytes=0,
        numeric_format_id='0x000e0c20',fixed_shift=10,firmware_irq=True,diagnostic_firmware=diagnostic_identities,
        input_data_format='X14/W12/b32 group8 HEX independently checked then tile16/v3 lossless layout4',
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
