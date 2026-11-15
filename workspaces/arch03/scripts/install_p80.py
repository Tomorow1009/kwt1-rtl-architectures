"""P80 replaces only the team arbiter/accelerator on the frozen T80 wiring."""
import json
from pathlib import Path
from install_t80 import install as install_t80
from install_dma16 import sha

def install(source,destination,row_lanes=5,transaction_depth=4):
    if row_lanes!=5 or transaction_depth not in (2,4,8):
        raise ValueError('P80 requires 80 PEs and metadata queue depth 2/4/8')
    destination=Path(destination);manifest=install_t80(source,destination,row_lanes)
    mems=destination/'rtl/e203/subsys/e203_subsys_mems.v';text=mems.read_text()
    replacements={
        'arch03_icb_arb2_turnover u_arch03_arb(': 'arch03_icb_arb2_queued #(.TRANSACTION_DEPTH(%d)) u_arch03_arb('%transaction_depth,
        'arch03_t80_accel u_arch03_accel(': 'arch03_p80_accel #(.TRANSACTION_DEPTH(%d)) u_arch03_accel('%transaction_depth}
    for old,new in replacements.items():
        if text.count(old)!=1:raise ValueError('P80 expected exact T80 instance: '+old)
        text=text.replace(old,new)
    # No rewrite of mem_fab, its parameters, the slave router or the SRAM path.
    mems.write_text(text)
    tb=destination/'tb/tb_top.v';text=tb.read_text()
    old='`include "arch03_t80_monitor.svh"'
    if text.count(old)!=1:raise ValueError('P80 expected frozen T80 monitor include')
    tb.write_text(text.replace(old,'`include "arch03_p80_monitor.svh"'))
    for path in (mems,tb):manifest['modified_files'][path.relative_to(destination).as_posix()]=sha(path)
    spec=manifest.pop('t80');spec.update(variant='p80_ordered_original_bus_shared_readback',
        peripheral_id='0x4b57530b',capability='0x000905bf',transaction_metadata_depth=transaction_depth,
        source_credits=3,data_fifo_depths=dict(source=16,read_response=16,output=32),
        unpresented_descriptor_depth=8,original_fabric_parameters_modified=False,
        inherited_t80_installer_sha256=spec['implementation_sha256'],implementation_sha256=sha(Path(__file__)))
    manifest['p80']=spec
    (destination/'platform_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest
