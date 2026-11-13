"""T64: unchanged T80 bus/physical SRAM, four-row systolic compute only."""
import json
from pathlib import Path
from install_t80 import install as install_t80
from install_dma16 import sha


def install(source, destination, row_lanes=4):
    if row_lanes != 4:
        raise ValueError('T64 requires exactly four compute rows')
    destination=Path(destination)
    manifest=install_t80(source,destination,5)
    mems=destination/'rtl/e203/subsys/e203_subsys_mems.v'
    text=mems.read_text()
    if text.count('arch03_t80_accel u_arch03_accel')!=1:
        raise ValueError('Expected frozen T80 topology')
    mems.write_text(text.replace('arch03_t80_accel u_arch03_accel','arch03_t64_accel u_arch03_accel'))
    tb=destination/'tb/tb_top.v'
    text=tb.read_text()
    if text.count('`include "arch03_t80_monitor.svh"')!=1:
        raise ValueError('Expected T80 observer include')
    tb.write_text(text.replace('`include "arch03_t80_monitor.svh"','`include "arch03_t64_monitor.svh"'))
    for path in (mems,tb):
        manifest['modified_files'][path.relative_to(destination).as_posix()]=sha(path)
    spec=manifest.pop('t80')
    spec.update(variant='t64_original_bus_shared_readback',compute_rows=4,processing_elements=64,physical_x_row_banks=5,
                row_lanes=4,peripheral_id='0x4b575309',capability='0x000804bf',
                inherited_t80_installer_sha256=spec['implementation_sha256'],implementation_sha256=sha(Path(__file__)))
    manifest['t64']=spec
    (destination/'platform_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest
