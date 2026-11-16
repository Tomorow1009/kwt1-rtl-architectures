"""Reconstruct an exact firmware-only correction and prepare a new C32 bundle.

The prior failed bundle and every old result stay immutable. The patch changes
only the dedicated CPU-contention firmware, never RTL or IRQ performance FW.
"""
import base64
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import zlib

ROOT=Path('/tmp/s4_21usr_c32_20261116_2010')
OLD_SHA='40fed77e347aad1347f1998f19801652770b176c5f5e0e03f405d68d0a11c602'
PATCH_SHA='115050d5f291747f25ff822abdbb1d3662d9e4b344cdf5587cba8708c680a489'
NEW_SHA='bc73ccd413657fd527628be76f5973de10f8cc30705580c3d5970ccbaed143bc'
COMMIT='91135f61c97c980039793c6637d0a06888638df0'
FILES={'workspaces/arch03/sw/main_c32_contention.c'}|{
    'firmware_contention/'+name for name in ('build_command.json','driver.elf','manifest.json','shift_10.bin','shift_10.verilog')}


def sha(b):return hashlib.sha256(b).hexdigest()


def reconstruct(old,patch):
    assert sha(old)==OLD_SHA and sha(patch)==PATCH_SHA
    data=json.loads(old);change=json.loads(patch)
    assert change['schema']=='c32-exact-payload-prefix-suffix-correction-v1'
    assert change['original_sha256']==OLD_SHA and change['new_payload_sha256']==NEW_SHA
    assert change['source_commit']==COMMIT and set(change['changes'])==FILES
    for name,v in change['changes'].items():
        raw=base64.b64decode(data['files'][name]['base64'],validate=True)
        assert sha(raw)==v['old_sha256']==data['files'][name]['sha256']
        pre,suf=v['prefix'],v['suffix']
        assert type(pre) is int and type(suf) is int and 0<=pre<=len(raw) and 0<=suf<=len(raw)-pre
        new=raw[:pre]+base64.b64decode(v['middle_base64'],validate=True)+(raw[len(raw)-suf:] if suf else b'')
        assert sha(new)==v['new_sha256']
        data['files'][name]=dict(base64=base64.b64encode(new).decode(),sha256=sha(new))
    data['source_commit']=COMMIT
    result=json.dumps(data,sort_keys=True,separators=(',',':')).encode()
    assert sha(result)==NEW_SHA
    return result


def main():
    assert os.name=='posix' and ROOT.resolve()==ROOT and ROOT.stat().st_mode&0o777==0o700
    old=ROOT/'payload_61246bb.json';patch=ROOT/'contention_fix_patch02.b64'
    raw=reconstruct(old.read_bytes(),zlib.decompress(base64.b64decode(patch.read_bytes(),validate=False)))
    target=ROOT/'payload_91135f6.json'
    with target.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
    expected=json.loads(raw)['files']['workspaces/arch03/scripts/c32_prepare_bundle.py']['sha256']
    tool=ROOT/'prepare_61246bb.py';assert sha(tool.read_bytes())==expected
    subprocess.check_call([sys.executable,'-B',str(tool),'--payload',str(target),'--root',str(ROOT),
        '--bundle','light-light126-c32-91135f6'])
    assert sha(old.read_bytes())==OLD_SHA
    print('C32_CONTENTION_FIX_BUNDLE_PREPARED',NEW_SHA,flush=True)


if __name__=='__main__':main()
