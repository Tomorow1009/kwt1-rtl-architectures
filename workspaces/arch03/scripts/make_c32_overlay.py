"""Build a local C32 transfer document from committed source and checked FW.

It contains no vendor libraries, personal configuration, task HEX, or results.
The server copies its already verified C80 inputs to a fresh C32 directory.
"""
import argparse
import ast
import base64
import hashlib
import json
from pathlib import Path
import subprocess
import zlib
import c32_prepare_bundle as contract
from c32_soc import verify_firmware
from build_c32_sequence import verify_firmware as verify_sequence
from c32_contention import verify_firmware as verify_contention

ROOT=Path(__file__).resolve().parents[3]

def main():
    p=argparse.ArgumentParser()
    for name in ('firmware','firmware-sequence','firmware-contention','output'):
        p.add_argument('--'+name,required=True,type=Path)
    a=p.parse_args();out=a.output.resolve()
    contract.require(not out.exists(),'Use a new overlay output directory')
    git=['git','-c','safe.directory='+str(ROOT.as_posix()),'-C',str(ROOT)]
    commit=subprocess.check_output(git+['rev-parse','HEAD']).decode().strip()
    tracked=subprocess.check_output(git+['ls-files','workspaces/arch03']).decode().splitlines()
    paths={name:ROOT/name for name in tracked if contract.allowed(name) and 'c32' in Path(name).name.lower()}
    for name in contract.REQUIRED | contract.REVIEW_HELPERS:paths[name]=ROOT/name
    firmware={name:getattr(a,name) for name in contract.FIRMWARE_DIRS}
    for name,folder in firmware.items():
        folder=folder.resolve()
        if name=='firmware_sequence':meta=verify_sequence(folder)[0]
        elif name=='firmware_contention':meta=verify_contention(folder)[0]
        else:meta=verify_firmware(folder)[0]
        expected=2
        contract.require(meta['configuration']['transaction_metadata_depth']==expected,'Firmware metadata depth mismatch')
        for rel in meta['source_sha256']:
            contract.require(contract.allowed(rel),'Unreviewed firmware dependency '+rel);paths[rel]=ROOT/rel
        for item in folder.iterdir():
            if item.name in contract.FIRMWARE_NAMES and item.is_file():paths[name+'/'+item.name]=item
    # git diff also detects staged-but-uncommitted source; metadata records raw
    # tested bytes, while Git's own CRLF normalization defines commit identity.
    source_names=[n for n in paths if n.startswith('workspaces/')]
    subprocess.run(git+['diff','--exit-code','HEAD','--']+source_names,check=True,stdout=subprocess.PIPE)
    files={}
    for name,path in sorted(paths.items()):
        raw=path.read_bytes()
        if path.suffix=='.py':ast.parse(raw.decode('utf8'),filename=name,feature_version=(3,6))
        files[name]=dict(base64=base64.b64encode(raw).decode('ascii'),sha256=hashlib.sha256(raw).hexdigest())
    payload=dict(schema='c32-source-firmware-overlay-v1',source_commit=commit,transaction_metadata_depth=2,files=files)
    contract.overlay(payload)
    raw=(json.dumps(payload,sort_keys=True,separators=(',',':'))+'\n').encode()
    compressed=zlib.compress(raw,9);out.mkdir(parents=True)
    (out/'payload.json').write_bytes(raw);(out/'payload.zlib').write_bytes(compressed)
    receipt=dict(source_commit=commit,files=len(files),payload_sha256=hashlib.sha256(raw).hexdigest(),
        compressed_sha256=hashlib.sha256(compressed).hexdigest(),compressed_bytes=len(compressed),
        old_T80_or_old8_modified=False,server_prepared=False)
    (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print('C32_LOCAL_OVERLAY_READY',json.dumps(receipt,sort_keys=True))

if __name__=='__main__':main()
