"""T80: original mem_fab upstream arbitration, genuine shared-SRAM readback.

The inherited installer is used only to reconstruct the pinned ASIC platform.
Its old O4-side multi-master arrangement is replaced before anything is run.
No original bus parameters, slave decodes, or SRAM timing are changed.
"""
import json
from pathlib import Path

from install_dma16 import FIELDS, once, sha
from install_n1 import install as install_n1


def patch_mems(text):
    # CPU and DMA now arbitrate at the ORIGINAL bus input. Other i_icb ports
    # (size/lock/excl/burst/beat) retain the platform's constant connections.
    for name, width in FIELDS:
        text = once(text, r'(\.i_icb_' + name + r'\s*\(\s*)mem_icb_' + name +
                    r'(\s*\))', lambda m: m.group(1) + 'a3_bus_' + name + m.group(2),
                    'original mem_fab upstream ' + name)
        old = '.cpu_%s(a3_cpu_%s)' % (name, name)
        if text.count(old) != 1:
            raise ValueError('Expected one inherited CPU arbiter connection: ' + name)
        text = text.replace(old, '.cpu_%s(mem_icb_%s)' % (name, name))

    # The router becomes an ordinary O4 slave: it has no independent DMA input.
    start = text.index('arch03_icb_memory_router_turnover u_arch03_router(')
    end = text.index(');', start) + 2
    router = text[start:end]
    for name, width in FIELDS:
        old = '.%s(a3_bus_%s)' % (name, name)
        if router.count(old) != 1:
            raise ValueError('Expected O4 router connection: ' + name)
        router = router.replace(old, '.%s(a3_cpu_%s)' % (name, name))
    text = text[:start] + router + text[end:]
    old = 'arch03_n1_accel u_arch03_accel'
    if text.count(old) != 1:
        raise ValueError('Expected the ungated N1 accelerator')
    return text.replace(old, 'arch03_t80_accel u_arch03_accel')


def install(source, destination, row_lanes=5):
    if row_lanes != 5:
        raise ValueError('T80 requires the unchanged N1 five-row numeric core')
    destination = Path(destination)
    manifest = install_n1(source, destination, row_lanes)
    mems = destination/'rtl/e203/subsys/e203_subsys_mems.v'
    mems.write_text(patch_mems(mems.read_text()))
    tb = destination/'tb/tb_top.v'
    text = tb.read_text()
    old = '`include "arch03_n1_monitor.svh"'
    if text.count(old) != 1:
        raise ValueError('Expected inherited N1 monitor')
    tb.write_text(text.replace(old, '`include "arch03_t80_monitor.svh"'))
    for path in (mems, tb):
        manifest['modified_files'][path.relative_to(destination).as_posix()] = sha(path)
    spec = manifest.pop('n1')
    spec.update(variant='t80_n1_original_bus_shared_readback',
        peripheral_id='0x4b575308', capability='0x000705bf',
        shared_write_ack_forwarding=False, shared_readback=True,
        arbitration_location='upstream of original e203_subsys_mems.mem_fab',
        dma_routes=['source_read', 'shared_input_write', 'shared_input_read', 'shared_output_write'],
        added_accelerator_icg_count=0,
        inherited_installer_sha256=spec['implementation_sha256'],
        implementation_sha256=sha(Path(__file__)))
    manifest['t80'] = spec
    manifest['competition_memory_compatibility'] = (
        '32-bit original mem_fab upstream arbitration; original O4 slave router; '
        'shared read response is sole decoder input; requires new functional/PPA evidence')
    (destination/'platform_manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    return manifest
