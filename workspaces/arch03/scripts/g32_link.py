"""Fresh G32 ASIC link for partition synthesis; never reuse a T80 RTL DDC.

The installed platform, original bus parameters and exact queue depth are
bound to the checked firmware. Library-unit evidence can be reused only for
identical library bytes. This operation maps no hardware and grants no PASS.
"""
import json
from pathlib import Path
import re

import t80_synth as reports
from asic_link import libraries
from install_platform import platform_sources
from install_g32 import install
from g32_soc import source_list, verify_firmware
from partition_synth_contract import require, digest
import soc_synth
from server_run import vendor

ROOT=Path(__file__).resolve().parents[3]
A3=ROOT/'workspaces/arch03'
MARKER='ARCH03_G32_LINK_READY fresh_sources=true mapped=false'

BOUNDARY_INVENTORY=r'''
set boundary_file [open linked_boundaries.tsv w]
foreach {block suffix} {accelerator u_arch03_accel shared_sram u_arch03_shared} {
    current_design e203_soc_top
    set cell [get_cells -hierarchical -filter "full_name =~ */$suffix"]
    if {[sizeof_collection $cell] != 1} {error "G32 boundary instance missing/ambiguous"}
    set reference [get_attribute $cell ref_name]
    puts $boundary_file "$block\t[get_object_name $cell]\t$reference"
    current_design $reference
    set port_file [open ${block}.linked_ports.tsv w]
    foreach_in_collection port [get_ports *] {
        puts $port_file "[get_object_name $port]\t[get_attribute $port direction]"
    }
    close $port_file
}
close $boundary_file
current_design e203_soc_top
'''


def link_script(standard,databases,sources,includes):
    text=reports.link_script(standard,databases,sources,includes)
    text=reports.replace_once(text,'write -format ddc -hierarchy -output linked.ddc',
        BOUNDARY_INVENTORY+'\nwrite -format ddc -hierarchy -output linked.ddc')
    return reports.replace_once(text,reports.LINK_MARKER,MARKER)


def source_contract(cfg,run,platform_source,firmware,call):
    """Build a new immutable link and its trace before any mapping stage."""
    run,firmware=Path(run),Path(firmware)
    require(not any(run.iterdir()),'G32 link requires a fresh empty run')
    fw,_=verify_firmware(firmware)
    depth=fw['configuration']['transaction_metadata_depth']
    vendor(cfg,run)  # Generate the verified ASIC macro pin/polarity include.
    platform=run/'platform'; manifest=install(platform_source,platform,2,depth)
    top=platform/'rtl/e203/soc/e203_soc_top.v'
    require(top.is_file(),'Installed G32 top missing')
    reports.verify_top_sysmem(top.read_text())
    sources=platform_sources(platform)+source_list()+[
        A3/'rtl/arch03_tcm_ram.sv',A3/'rtl/arch03_shared_sram.sv']
    require(len(sources)==len(set(sources)),'Duplicate G32 synthesis source')
    require(not any(p.name in ('arch03_t80_accel.sv','arch03_t80_transport.sv',
        'arch03_icb_arb2_turnover.sv') for p in sources),'Old T80 team RTL in G32 link')
    includes=list(dict.fromkeys([run,platform/'rtl/e203/core']+[p.parent for p in sources]))
    def library_call(cmd,cwd,name):
        text=call(cmd,cwd,name)
        require(not re.search(r'(?im)^\s*(Error-|Fatal:|Error:)',text),'Library tool error')
        return text
    standard,databases,lib_inputs=libraries(cfg,run,library_call)
    require(all(p.is_file() and p.stat().st_size for p in [standard]+databases),'Empty library DB')
    basis=reports.area_basis(run)
    tracked=sources+lib_inputs+[run/'arch02_sram_config.vh',reports.AREA_EVIDENCE,firmware/'manifest.json',
        ROOT/'handoff/team/server_config.json']
    tracked += [p for p in platform.rglob('*') if p.is_file()]
    # Header dependencies include the actual macro binding and all installed
    # SoC includes, not merely the list of .sv translation units.
    tracked += [p for root in (A3,A3.parent/'arch02') for p in root.rglob('*')
                if p.is_file() and p.suffix in ('.vh','.svh')]
    tracked += [A3/'scripts'/n for n in ('g32_link.py','g32_soc.py','install_g32.py','install_c80.py',
        'install_p80.py','install_t80.py','install_n1.py','install_icb32.py','install_dma16.py',
        'install_platform.py','asic_link.py','t80_synth.py','soc_synth.py','dc_blocks.py',
        'technology_binding.py','memory_technology.py','timing_contract.py',
        'build_g32_firmware.py','g32_paths.py','partition_synth_contract.py')]
    sdc=run/'task_mode.sdc';sdc.write_text(reports.constraints())
    tcl=run/'g32_link.tcl';tcl.write_text(link_script(standard,databases,sources,includes))
    tracked += [sdc,tcl]
    before={str(p.resolve()):digest(p) for p in tracked}
    (run/'source_inputs.json').write_text(json.dumps(before,indent=2,sort_keys=True)+'\n')
    log=call([cfg['tools']['dc_shell'],'-f',tcl],run,'g32_link.log')
    soc_synth.require_tool_marker(log,MARKER)
    for name in ('linked.ddc','linked_boundaries.tsv','accelerator.linked_ports.tsv','shared_sram.linked_ports.tsv'):
        require((run/name).is_file() and (run/name).stat().st_size,'Missing G32 link output '+name)
    reports.verify_ports((run/'linked_sysmem_ports.tsv').read_text())
    for path,want in before.items():require(digest(Path(path))==want,'G32 link input changed '+path)
    result=dict(schema='arch03-g32-fresh-link-v1',status='linked',transaction_metadata_depth=depth,
        source_commit=json.loads((ROOT/'manifest.json').read_text())['source_commit'],
        platform_baseline_sha256=manifest['baseline_sha256'],row_lanes=2,
        original_fabric_parameters_modified=False,old_linked_ddc_reused=False,
        expected_macros={'RAMSP128X16':92,'RAMSP4096X16':128},
        source_inputs_sha256=digest(run/'source_inputs.json'),linked_ddc_sha256=digest(run/'linked.ddc'),
        firmware_manifest_sha256=digest(firmware/'manifest.json'),area_basis=basis,
        library_inputs={str(p):digest(p) for p in lib_inputs},
        libraries={str(p):digest(p) for p in [standard]+databases},
        mapped=False,stage_accepted=False)
    (run/'link_receipt.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    return result
