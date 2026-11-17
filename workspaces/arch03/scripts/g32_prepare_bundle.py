"""Copy immutable C80 inputs plus explicit G32 source/firmware into a fresh root.

No EDA, link-based deduplication, old-result inheritance, or protected delivery
access. Input files are checked before and after the copy; existing destinations
are rejected. The old runtime and its durable backup remain untouched.
"""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path,PurePosixPath
import re
import shutil

BASE='/tmp/s4_21usr_c80_20261116_1245/light-light126-c80-74f3ae7'
BASE_SHA='d0f18e4a6aa8a928df37d4347f1a8853c448e823f0685a83c5b710732e5e7a59'
BASE_COUNT=1008
FIRMWARE_DIRS=('firmware','firmware_sequence','firmware_contention')
REPLACED_DIRS=FIRMWARE_DIRS+('firmware_d2','firmware_d8')
FIRMWARE_NAMES={'manifest.json','driver.elf','shift_10.bin','shift_10.verilog',
    'sequence.bin','sequence.verilog','build_command.json','build.log'}
UNCHANGED_HELPERS={
    'workspaces/arch03/sw/'+n for n in ('start_icb32.S','start_icb32_irq.S','start_icb32_sequence.S','link.ld')}
UNCHANGED_HELPERS.update('workspaces/arch03/scripts/'+n for n in
    ('n1_data.py','n1_codec.py','systolic_b_codec.py','dma16_batch.py','systolic_b_data.py','icb32_codec.py','icb32_data.py',
     'c80_data.py','c80_codec.py','c80_codec_candidate.py','install_c80.py'))
UNCHANGED_HELPERS.add('workspaces/arch03/irq_mapping.json')
REQUIRED={'workspaces/arch03/rtl/arch03_g32_icg.sv','workspaces/arch03/rtl/arch03_g32_accel.sv','workspaces/arch03/rtl/arch03_g32_transport.sv',
    'workspaces/arch03/rtl/arch03_icb_arb2_queued.sv','workspaces/arch03/scripts/g32_server.py',
    'workspaces/arch03/scripts/g32_paths.py','workspaces/arch03/scripts/install_g32.py',
    'workspaces/arch03/rtl/arch03_c80_decoder.sv','workspaces/arch03/rtl/arch03_g32_systolic2x16.sv',
    'workspaces/arch03/rtl/arch03_g32_linear16x2.sv','workspaces/arch03/rtl/arch03_n1_requantize.sv'}
REVIEW_HELPERS={'workspaces/arch03/scripts/'+name for name in
    ('transport_review_contract.py','b0_saif_unknown_inventory.py','n1_archive_runtime.py',
     't80_archive_runtime.py','transport_report_stage.py')}

def require(ok,message):
    if not ok:raise ValueError(message)

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def member(name):
    p=PurePosixPath(name)
    require(name and not p.is_absolute() and '\\' not in name and '..' not in p.parts and
        '.' not in p.parts and p.as_posix()==name,'Unsafe member')
    return p

def allowed(name):
    p=member(name)
    if name in UNCHANGED_HELPERS or name in REQUIRED or name in REVIEW_HELPERS:return True
    if len(p.parts)==2 and p.parts[0] in FIRMWARE_DIRS and p.name in FIRMWARE_NAMES:return True
    return len(p.parts) in (3,4) and p.parts[:2]==('workspaces','arch03') and \
        ('g32' in p.name.lower()) and p.suffix in ('.sv','.svh','.py','.md','.c','.h')

def overlay(payload):
    require(payload['schema']=='g32-source-firmware-overlay-v1' and
        re.fullmatch('[a-f0-9]{40}',payload['source_commit']) and
        type(payload['transaction_metadata_depth']) is int and payload['transaction_metadata_depth']==2,
        'Invalid G32 overlay identity')
    require(REQUIRED<=set(payload['files']),'Incomplete G32 source')
    for directory in FIRMWARE_DIRS:require(directory+'/manifest.json' in payload['files'],'Missing G32 firmware family')
    values={}
    for name,row in payload['files'].items():
        require(allowed(name),'Outside G32 source/firmware scope '+name)
        raw=base64.b64decode(row['base64'],validate=True)
        require(hashlib.sha256(raw).hexdigest()==row['sha256'],'Changed overlay '+name)
        values[name]=raw
    depths={'firmware':payload['transaction_metadata_depth'],
        'firmware_sequence':payload['transaction_metadata_depth'],
        'firmware_contention':payload['transaction_metadata_depth']}
    for directory,depth in depths.items():
        firmware=json.loads(values[directory+'/manifest.json'].decode('utf8'))
        config=firmware.get('configuration',{})
        require(config.get('transaction_metadata_depth')==depth and config.get('row_lanes')==2 and
            firmware.get('peripheral_id')=='0x4b57530f' and firmware.get('numeric_format')=='0x000e0c20',
            'Firmware identity/rows/depth differs from G32 role: '+directory)
    return values

def prepare(source,target,payload):
    source,target=Path(source),Path(target);values=overlay(payload)
    require(not target.exists(),'Never overwrite an input bundle')
    require(source.resolve()==source.absolute() and not source.is_symlink(),'Symlink source')
    require('T80_Delivery_20261113' not in source.parts,'Protected delivery cannot be a package source')
    require(sha(source/'manifest.json')==BASE_SHA,'Wrong frozen C80 source manifest')
    original=json.loads((source/'manifest.json').read_text());files=original['files']
    require(len(files)==BASE_COUNT,'Incomplete C80 source bundle')
    for name,want in files.items():
        member(name);p=source/name
        require(p.resolve()==p.absolute() and p.is_file() and sha(p)==want,'Changed frozen C80 source '+name)
    # New firmware is freshly built; never copy old firmware leftovers into
    # these replaced directories. This filters the NEW copy only.
    kept={n:h for n,h in files.items() if PurePosixPath(n).parts[0] not in REPLACED_DIRS}
    target.mkdir(mode=0o700)
    for name in kept:
        if name in values:continue
        dest=target/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(str(source/name),str(dest))
    for name,raw in values.items():
        dest=target/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    desired=dict(kept);desired.update({n:hashlib.sha256(b).hexdigest() for n,b in values.items()})
    for name,want in desired.items():require(sha(target/name)==want,'New G32 bytes mismatch')
    result=dict(original)
    result.update(source_commit=payload['source_commit'],hardware_source_commit=payload['source_commit'],
        production_hardware_commit=payload['source_commit'],activity_tools_commit=payload['source_commit'],
        operations_source_commit=payload['source_commit'],files=desired,architecture='arch03_g32_ordered_original_bus',
        peripheral_id='0x4b57530f',numeric_format='0x000e0c20',layout_id='0x00100006',row_lanes=2,
        processing_elements=32,capability='0x000d02bf',variant='G32_gated_C32_A',
        runtime_layout='arch03-g32-lossless-layout6',
        input_data_format='Original X14/W12/b32 group8 HEX independently checked then G32 lossless layout6',
        derived_from_manifest_sha256=BASE_SHA,
        diagnostic_firmware={name:desired['firmware_'+name+'/manifest.json'] for name in ('sequence','contention')},
        cpu_execution_verified=False,timing_verified=False,official_precision_verified=False,
        transaction_metadata_depth=payload['transaction_metadata_depth'],
        derivation=dict(source_bundle=str(source),source_manifest_sha256=BASE_SHA,
            source_preserved=True,overlay_files={n:desired[n] for n in sorted(values)}),
        inherited_results_are_not_G32_PASS=True,new_synthesis_verified=False)
    (target/'manifest.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    for name,want in files.items():require(sha(source/name)==want,'Old source changed during clone')
    require(sha(source/'manifest.json')==BASE_SHA,'Old manifest changed')
    return dict(bundle=str(target),manifest_sha256=sha(target/'manifest.json'),files=len(desired),
        source_preserved=True,hardware_source_commit=payload['source_commit'],eda_started=False)

def main():
    p=argparse.ArgumentParser();p.add_argument('--payload',required=True,type=Path)
    p.add_argument('--root',required=True,type=Path);p.add_argument('--bundle',required=True);a=p.parse_args()
    import pwd
    require(os.name=='posix' and pwd.getpwuid(os.getuid()).pw_name=='s4_21usr','Wrong runtime account')
    root=a.root.absolute()
    require(root.parent==Path('/tmp') and re.fullmatch('s4_21usr_g32_[0-9]{8}_[0-9]{4}',root.name),'Use a new private G32 root')
    require(root.resolve()==root and not root.is_symlink() and root.stat().st_uid==os.getuid() and
        root.stat().st_mode & 0o777==0o700,'Invalid root ownership/mode')
    require(re.fullmatch('light-light126-g32-[a-f0-9]{7,40}',a.bundle),'Invalid G32 bundle name')
    result=prepare(Path(BASE),root/a.bundle,json.loads(a.payload.read_text()))
    receipt=root/(a.bundle+'.prepared.json')
    with receipt.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print('G32_INPUTS_PREPARED',json.dumps(result,sort_keys=True),flush=True)

if __name__=='__main__':main()
