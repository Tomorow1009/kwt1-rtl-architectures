"""Independent compressed ICB32 installer; no changes to the baseline tree.

Reuse the checked original SysMem/PLIC/ASIC boot wiring installer, then replace
only the accelerator/fabric instances in this new destination. Python 3.6.
"""
import json
from pathlib import Path
from install_dma16 import install as install_dma16, once, sha


def install(source, destination, row_lanes=4):
    if row_lanes not in (1, 4):
        raise ValueError('ICB32 supports R1/R4 only')
    destination = Path(destination)
    manifest = install_dma16(source, destination)
    mems = destination / 'rtl/e203/subsys/e203_subsys_mems.v'
    text = mems.read_text()
    for old, new in [('arch03_icb_arb2', 'arch03_icb_arb2_turnover'),
                     ('arch03_icb_memory_router', 'arch03_icb_memory_router_turnover'),
                     ('arch03_shared_sram', 'arch03_shared_sram_turnover')]:
        text = once(text, r'\b'+old+r'(\s+u_arch03_)', new+r'\1', old)
    text = once(text, r'\barch03_dma16_accel\s+u_arch03_accel',
                'arch03_icb32_accel #(.ROW_LANES(%d)) u_arch03_accel' % row_lanes,
                'independent ICB32 accelerator')
    mems.write_text(text)
    tb = destination / 'tb/tb_top.v'
    text = tb.read_text()
    if text.count('`include "arch03_dma16_monitor.svh"') != 1:
        raise ValueError('Baseline monitor marker changed')
    tb.write_text(text.replace('`include "arch03_dma16_monitor.svh"',
                               '`include "arch03_icb32_monitor.svh"'))
    for path in (mems, tb):
        manifest['modified_files'][path.relative_to(destination).as_posix()] = sha(path)
    old = manifest.pop('dma16')
    manifest['icb32'] = dict(variant='icb32_r%d' % row_lanes, row_lanes=row_lanes,
        source_base=0xb0000000, source_window_bytes=49152, maximum_encoded_bytes=47008,
        shared_base=0xa0000000, shared_bytes=524288, layout_id=0x00100002,
        output_bytes=50688, outstanding=1, same_cycle_retire_accept=True,
        original_sysmem_decode=old['original_sysmem_decode'],
        loading_interface=old['loading_interface'], source_model=old['source_model'], irq=old['irq'],
        original_raw_dma_layout_supported=False, scalar_debug_supported=True,
        shared_write_ack_forwarding=True, shared_readback=False,
        sram_macros={'4096x16':128,'128x16':96},
        accelerator_macros={'4096x16':0,'128x16':96},
        implementation_sha256=sha(Path(__file__)),
        inherited_installer_sha256=old['implementation_sha256'],
        asic_simulation_verified=False, timing_verified=False, system_power_verified=False)
    manifest['competition_memory_compatibility'] = (
        'Original 32-bit SysMem restored; real compressed shared writes before ACK forwarding; '
        'engineering interpretation of supplied loading rules, not separate organizer approval')
    (destination/'platform_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest
