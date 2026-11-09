"""Package committed DMA16 source, verified legacy/tile data and program-only firmware."""
import argparse
import datetime
import json
from pathlib import Path
import re
import shutil
import subprocess
import zipfile
from package import ROOT,git,sha
from dma16_soc import verify_firmware
from dma16_layout import verify_export
from dma16_batch import CASES14,source_case


def verify_review_document(bundle):
    """Check the Git-exported bytes, which can differ from Windows CRLF files."""
    bundle = Path(bundle).resolve()
    record = bundle/'workspaces/arch03/FROZEN_REVIEW_20261110.json'
    if not record.exists():
        return
    values = json.loads(record.read_text(encoding='utf8'))
    document = (bundle/values['review_document']).resolve()
    document.relative_to(bundle)
    if sha(document) != values['review_document_sha256']:
        raise ValueError('Packaged review document digest differs; bind canonical LF bytes before packaging')


def copy_firmware(source,target,bundle,verifier=verify_firmware):
    meta,_=verifier(source,bundle)
    target.mkdir()
    names=['driver.elf']+[n+suffix for n in meta['images'] for suffix in ('.verilog','.bin')]
    for name in names:shutil.copyfile(str(source/name),str(target/name))
    meta.pop('command',None)
    (target/'manifest.json').write_text(json.dumps(meta,indent=2)+'\n',encoding='utf8')
    verifier(target,bundle)


def copy_sequence_firmware(source,target,bundle):
    from build_dma16_sequence import verify_firmware as verify_sequence
    meta,_=verify_sequence(source,bundle)
    target.mkdir()
    for name in ('driver.elf','sequence.verilog','sequence.bin'):
        shutil.copyfile(str(source/name),str(target/name))
    meta.pop('command',None)
    (target/'manifest.json').write_text(json.dumps(meta,indent=2)+'\n',encoding='utf8')
    verify_sequence(target,bundle)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data',required=True,type=Path,help='Verified original 14-case packet directory')
    p.add_argument('--tile-data',required=True,type=Path,help='Independently verified tile16 export of those cases')
    p.add_argument('--firmware',required=True,type=Path)
    p.add_argument('--irq-firmware',type=Path)
    p.add_argument('--mmio8-firmware',type=Path,help='Original MMIO8 driver with the same real source-loading boundary')
    p.add_argument('--sequence-firmware',type=Path,help='Program-only polling DMA16 errors/cancel/timeout and A/B/A validation')
    p.add_argument('--contention-firmware',type=Path,help='Separate polling CPU/shared-SRAM contention validation, not PPA firmware')
    p.add_argument('--member',required=True)
    a=p.parse_args()
    if not re.fullmatch('[A-Za-z0-9_-]{1,60}',a.member):raise ValueError('Member identifier')
    if git('status','--porcelain'):raise ValueError('Commit source first; worktree is not clean')
    commit=git('rev-parse','HEAD')
    for name in CASES14:
        source_case(a.data/name);verify_export(a.data/name,a.tile_data/name)
    verify_firmware(a.firmware)
    if a.irq_firmware:verify_firmware(a.irq_firmware)
    if a.mmio8_firmware:
        from mmio8_soc import verify_firmware as verify_mmio8
        verify_mmio8(a.mmio8_firmware)
    if a.contention_firmware:
        from dma16_contention import verify_firmware as verify_contention
        verify_contention(a.contention_firmware)
    if a.sequence_firmware:
        from build_dma16_sequence import verify_firmware as verify_sequence
        sequence,_=verify_sequence(a.sequence_firmware)
        from build_dma16_sequence import verify_runtime_sources
        verify_runtime_sources(sequence,a.tile_data/sequence['tasks']['A']['case']/'load32.hex',
                               a.tile_data/sequence['tasks']['B']['case']/'load32.hex')
    bundle_name=a.member+'-dma16-'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')+'-'+commit[:12]
    folder=ROOT/'local_runs'/bundle_name;folder.mkdir()
    prefixes=('workspaces/arch02/','workspaces/arch03/',
              'architectures/arch01_serial_mac/v1.3.0/KWT1/model_data/outputs/real_sample_001/')
    for rel in git('ls-files').splitlines():
        if rel.startswith(prefixes) or rel in ('handoff/team/server_config.json','handoff/team/unpack.py',
                                             'handoff/team/evidence/UNDERGRAD_D3_SERVER_20261109.json'):
            target=folder/rel;target.parent.mkdir(parents=True,exist_ok=True)
            raw=subprocess.check_output(['git','-c','safe.directory='+ROOT.as_posix(),'show',commit+':'+rel],cwd=str(ROOT))
            target.write_bytes(raw)
    verify_review_document(folder)
    copy_firmware(a.firmware,folder/'firmware',folder)
    if a.irq_firmware:copy_firmware(a.irq_firmware,folder/'firmware_irq',folder)
    if a.mmio8_firmware:copy_firmware(a.mmio8_firmware,folder/'firmware_mmio8',folder,verify_mmio8)
    if a.contention_firmware:copy_firmware(a.contention_firmware,folder/'firmware_contention',folder,verify_contention)
    if a.sequence_firmware:copy_sequence_firmware(a.sequence_firmware,folder/'firmware_sequence',folder)
    # Only the explicitly validated fourteen cases are inputs to this smoke package.
    for case_name in CASES14:
        shutil.copytree(str(a.data/case_name),str(folder/'validated_data'/case_name))
        shutil.copytree(str(a.tile_data/case_name),str(folder/'validated_tile16'/case_name))
        source_case(folder/'validated_data'/case_name)
        verify_export(folder/'validated_data'/case_name,folder/'validated_tile16'/case_name)
    files={p.relative_to(folder).as_posix():sha(p) for p in sorted(folder.rglob('*')) if p.is_file()}
    manifest=dict(source_commit=commit,member=a.member,architecture='arch03_dma16',files=files,
        input_data_format='legacy14 independently crosschecked with tile16',
        runtime_layout='kwt1-arch03-dma-tile16-q12-v1',task_input_boot_bytes=0,
        platform_dependency='pinned official external source; installer checks complete RTL fingerprint',
        cpu_execution_verified=False,timing_verified=False,official_precision_verified=False)
    (folder/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf8')
    archive=folder.with_suffix('.zip')
    with zipfile.ZipFile(str(archive),'w',zipfile.ZIP_DEFLATED) as z:
        for path in sorted(folder.rglob('*')):
            if path.is_file():z.write(str(path),bundle_name+'/'+path.relative_to(folder).as_posix())
    receipt=dict(source_commit=commit,archive=archive.name,bytes=archive.stat().st_size,
                 sha256=sha(archive),files=len(files),hardware_executed=False)
    (folder.parent/(bundle_name+'.receipt.json')).write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8')
    print(json.dumps(receipt,indent=2))


if __name__=='__main__':main()
