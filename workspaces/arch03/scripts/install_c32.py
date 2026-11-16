"""C32-A exact delta on frozen C80 wiring; original fabric stays unchanged."""
import json
from pathlib import Path
from install_c80 import install as install_c80
from install_dma16 import sha


def install(source, destination, row_lanes=2, transaction_depth=2):
    if row_lanes != 2 or transaction_depth != 2:
        raise ValueError('C32-A requires 32 PEs and frozen metadata depth2')
    destination = Path(destination)
    # Reconstruct the fixed platform through the unchanged, strict parent.
    manifest = install_c80(source, destination, 5, 2)
    mems = destination/'rtl/e203/subsys/e203_subsys_mems.v'
    text = mems.read_text()
    old = 'arch03_c80_accel #(.TRANSACTION_DEPTH(2)) u_arch03_accel('
    if text.count(old) != 1:
        raise ValueError('C32 expected exact C80 accelerator instance')
    mems.write_text(text.replace(old, 'arch03_c32_accel #(.TRANSACTION_DEPTH(2)) u_arch03_accel('))
    tb = destination/'tb/tb_top.v'
    text = tb.read_text()
    old = '`include "arch03_c80_monitor.svh"'
    if text.count(old) != 1:
        raise ValueError('C32 expected exact C80 monitor include')
    tb.write_text(text.replace(old, '`include "arch03_c32_monitor.svh"'))
    for path in (mems, tb):
        manifest['modified_files'][path.relative_to(destination).as_posix()] = sha(path)
    spec = manifest.pop('c80')
    spec.update(variant='c32_a_2x16_original_bus_shared_readback', row_lanes=2, processing_elements=32,
        peripheral_id='0x4b57530d', capability='0x000b02bf', layout='0x00100006',
        inherited_c80_installer_sha256=spec['implementation_sha256'],
        implementation_sha256=sha(Path(__file__)), physical_macro_organization_modified=False,
        physical_x_bank_rows=5, logical_compute_rows=2, pe_count=32, result_slot_elements=32,
        block_tag_bits=10, blocks_per_task=800, internal_small_macros=92,
        supported_layout_ids=['0x00100006'])
    manifest['c32'] = spec
    (destination/'platform_manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    return manifest
