"""C80 exact delta on frozen P80 wiring; never changes original fabric parameters."""
import json
from pathlib import Path
from install_p80 import install as install_p80
from install_dma16 import sha


def install(source,destination,row_lanes=5,transaction_depth=2):
    if row_lanes!=5 or transaction_depth!=2:
        raise ValueError('C80 requires 80 PEs and frozen P80 depth2')
    destination=Path(destination)
    manifest=install_p80(source,destination,row_lanes,transaction_depth)
    mems=destination/'rtl/e203/subsys/e203_subsys_mems.v'
    text=mems.read_text();old='arch03_p80_accel #(.TRANSACTION_DEPTH(2)) u_arch03_accel('
    if text.count(old)!=1:raise ValueError('C80 expected exact P80 accelerator instance')
    mems.write_text(text.replace(old,'arch03_c80_accel #(.TRANSACTION_DEPTH(2)) u_arch03_accel('))
    tb=destination/'tb/tb_top.v';text=tb.read_text();old='`include "arch03_p80_monitor.svh"'
    if text.count(old)!=1:raise ValueError('C80 expected P80 monitor include')
    tb.write_text(text.replace(old,'`include "arch03_c80_monitor.svh"'))
    for path in (mems,tb):manifest['modified_files'][path.relative_to(destination).as_posix()]=sha(path)
    spec=manifest.pop('p80');spec.update(variant='c80_exact_codec_original_bus_shared_readback',
        peripheral_id='0x4b57530c',capability='0x000a05bf',layout='0x00100006',
        inherited_p80_installer_sha256=spec['implementation_sha256'],implementation_sha256=sha(Path(__file__)),
        external_bias_halfwords=2,internal_bias_halfwords=3,physical_macro_organization_modified=False)
    manifest['c80']=spec
    (destination/'platform_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest
