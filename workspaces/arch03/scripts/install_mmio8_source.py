"""Original repaired MMIO8 core, same restored SysMem source/shared fabric.

This is a reference configuration, never an eight-lane DMA implementation.
"""
import json
from pathlib import Path
from install_platform import install as baseline
from install_dma16 import patch_mems,patch_main,patch_soc,patch_tb,sha


def install(source,destination):
    destination=Path(destination)
    record=baseline(Path(source),destination,asic=True,asic_boot=True)
    changes=[('rtl/e203/subsys/e203_subsys_mems.v',lambda s:patch_mems(s,'mmio8_reference')),
        ('rtl/e203/subsys/e203_subsys_main.v',patch_main),('rtl/e203/soc/e203_soc_top.v',patch_soc),
        ('tb/tb_top.v',lambda s:patch_tb(s).replace('arch03_dma16_monitor.svh','arch03_mmio8_source_monitor.svh'))]
    for name,fn in changes:
        path=destination/name;path.write_text(fn(path.read_text()))
        record['modified_files'][name]=sha(path)
    record.update(monitor='arch03_mmio8_source_monitor.svh',variant='original_repaired_mmio8_source_reference',
        source_base='0xb0000000',input_boot_bytes=0,source_model='same DMA16 source N accept N+1 earliest ACK',
        DMA_present=False,unused_arbiter_DMA_input='tied inactive; may optimize away',
        firmware_driver='kwt.c unchanged; main_mmio8_source.c performs real source copy',
        asic_simulation_verified=False,timing_verified=False)
    (destination/'platform_manifest.json').write_text(json.dumps(record,indent=2)+'\n')
    return record
