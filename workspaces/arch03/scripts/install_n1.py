"""Independent B installer layered on the pinned R4 wiring, never its RTL/PASS."""
import json
from pathlib import Path
from install_icb32 import install as install_r4
from install_dma16 import sha


def install(source, destination, row_lanes=5):
    if row_lanes != 5:
        raise ValueError('Systolic B requires five physical row lanes')
    destination = Path(destination)
    manifest = install_r4(source, destination, 4)
    mems = destination/'rtl/e203/subsys/e203_subsys_mems.v'
    text = mems.read_text()
    old = 'arch03_icb32_accel #(.ROW_LANES(4)) u_arch03_accel'
    if text.count(old) != 1:
        raise ValueError('Expected independent R4 accelerator instance')
    mems.write_text(text.replace(old, 'arch03_n1_accel u_arch03_accel'))
    tb = destination/'tb/tb_top.v'
    text = tb.read_text()
    old = '`include "arch03_icb32_monitor.svh"'
    if text.count(old) != 1:
        raise ValueError('Expected original positive monitor include')
    tb.write_text(text.replace(old, '`include "arch03_n1_monitor.svh"'))
    for path in (mems, tb):
        manifest['modified_files'][path.relative_to(destination).as_posix()] = sha(path)
    spec = manifest.pop('icb32')
    spec.update(variant='n1_x14_w12_b32_v4', row_lanes=5, processing_elements=80,
                pair_output=True, peripheral_id='0x4b575306', capability='0x000505bf',
                supported_layout_ids=['0x00100004'], numeric_format='0x000e0c20',
                x_macro_mapping='row%5,k%4,segment=floor(floor(row/5)/8)',
                sram_macros={'4096x16':128,'128x16':92},
                accelerator_macros={'4096x16':0,'128x16':92},
                inherited_icb32_installer_sha256=spec['implementation_sha256'],
                implementation_sha256=sha(Path(__file__)))
    manifest['n1'] = spec
    (destination/'platform_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest
