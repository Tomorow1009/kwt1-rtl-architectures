"""Clone verified T80 inputs and add a pinned S0 tools overlay, never old runs.

No EDA execution, cleanup, hard links, upload or protected-delivery access.
All paths and bytes from the source remain unchanged. New root is /tmp only.
"""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil

BASE_SHA='181bb96b719363be5350e9e968ac2b2ad29555e2f4606e362721be3c42629b9b'
BASE='/tmp/s4_21usr_t80_20261113_2012/light-light126-t80-activity-cef81d4'
ALLOWED = {
    'workspaces/arch03/scripts/'+n for n in ('s0_prepare_bundle.py','s0_partition_synth.py',
    's0_server.py','s0_validation.py','s0_report.py','s0_finish.py','t80_report.py','t80_precision_join.py',
    'partition_synth_contract.py','n1_process.py','t80_gate.py','t80_structure.py',
    'b0_saif_unknown_inventory.py','transport_review_contract.py')}
ALLOWED.update(('handoff/team/evidence/S0_T80_SOURCE_IDENTITY_20261115.json',
    'workspaces/arch03/IMPLEMENTATION_PLAN_T80_P80_C32_G32_20261115.md',
    'workspaces/arch03/S0_PARTITION_IMPLEMENTATION_NOTES.md'))


def require(value,message):
    if not value:raise ValueError(message)


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def member(name):
    p=PurePosixPath(name)
    require(name and not p.is_absolute() and '\\' not in name and
            '..' not in p.parts and '.' not in p.parts and p.as_posix()==name,'Unsafe manifest member')
    return p


def overlay(payload):
    require(payload['schema']=='s0-tools-overlay-v1' and
            re.fullmatch('[a-f0-9]{40}',payload['operations_source_commit']),'Bad tool identity')
    require(set(payload['files'])==ALLOWED,'Unexpected or missing overlay file')
    values={}
    for name,row in payload['files'].items():
        member(name);raw=base64.b64decode(row['base64'],validate=True)
        require(hashlib.sha256(raw).hexdigest()==row['sha256'],'Changed overlay bytes')
        values[name]=raw
    return values


def prepare(source,target,payload):
    """Caller checks fixed account/root; pure helper supports isolated tests."""
    source=Path(source);target=Path(target);values=overlay(payload)
    require(not target.exists(),'Never overwrite a bundle')
    require(source.resolve()==source.absolute() and not source.is_symlink(),'Symlink source')
    require(sha(source/'manifest.json')==BASE_SHA,'Wrong original T80 input identity')
    original=json.loads((source/'manifest.json').read_text());files=original['files']
    require(len(files)==833,'Incomplete original T80 input bundle')
    for name,want in files.items():
        member(name);path=source/name
        require(path.resolve()==path.absolute() and path.is_file() and sha(path)==want,'Changed source input '+name)
    target.mkdir(mode=0o700)
    for name,want in files.items():
        dest=target/name;dest.parent.mkdir(parents=True,exist_ok=True)
        if name not in values:shutil.copyfile(str(source/name),str(dest))
    for name,raw in values.items():
        dest=target/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    desired=dict(files);desired.update({name:hashlib.sha256(raw).hexdigest() for name,raw in values.items()})
    for name,want in desired.items():require(sha(target/name)==want,'New bundle byte mismatch')
    result=dict(original)
    result.update(files=desired,operations_source_commit=payload['operations_source_commit'],
        hardware_source_commit='876b883d95199f2d1889019cbfec4c93c42d1be5',
        derivation=dict(source_bundle=str(source),source_manifest_sha256=BASE_SHA,
            overlay_files={name:desired[name] for name in sorted(values)},
            source_commit_field_scope='original T80 package; new tools identified by operations_source_commit'),
        architecture='arch03_t80_s0_partition',new_synthesis_verified=False)
    (target/'manifest.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    for name,want in files.items():require(sha(source/name)==want,'Original input changed during clone')
    require(sha(source/'manifest.json')==BASE_SHA,'Original manifest changed')
    return dict(bundle=str(target),manifest_sha256=sha(target/'manifest.json'),files=len(desired),
        source_preserved=True,hardware_source_commit=result['hardware_source_commit'],
        operations_source_commit=payload['operations_source_commit'],eda_started=False)


def main():
    p=argparse.ArgumentParser();p.add_argument('--payload',required=True,type=Path)
    p.add_argument('--root',required=True,type=Path);p.add_argument('--bundle',required=True)
    a=p.parse_args()
    import pwd
    require(os.name=='posix' and pwd.getpwuid(os.getuid()).pw_name=='s4_21usr','Wrong runtime account')
    root=a.root.absolute()
    require(root.parent==Path('/tmp') and re.fullmatch('s4_21usr_t80_[0-9]{8}_[0-9]{4}',root.name),
            'Use an independent T80 S0 private root')
    require(root.resolve()==root and not root.is_symlink() and root.stat().st_uid==os.getuid() and
            root.stat().st_mode & 0o777==0o700,'Invalid private root ownership or permissions')
    require(re.fullmatch('light-light126-t80-s0-[a-f0-9]{7,40}',a.bundle),'Invalid new S0 bundle name')
    result=prepare(Path(BASE),root/a.bundle,json.loads(a.payload.read_text()))
    receipt=root/(a.bundle+'.prepared.json');receipt.write_text(json.dumps(result,indent=2)+'\n')
    print('S0_INPUTS_PREPARED',json.dumps(result,sort_keys=True),flush=True)


if __name__=='__main__':main()
