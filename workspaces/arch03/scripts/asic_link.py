"""Prepare and link the complete ASIC SoC. Linking is NOT timing acceptance.

Runs only inside a separately locked, immutable server bundle. The official
platform, licensed libraries, and historical runs remain untouched.
Python 3.6 standard library only.
"""
import hashlib
import json
import re
import shutil
import tarfile
from pathlib import Path
from install_platform import install, platform_sources
from technology_binding import BINDINGS,load_bindings,verify_liberty
from memory_technology import METADATA,verify_memory_liberty


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def libraries(cfg, run, call):
    libs=run/'libs'
    libs.mkdir()
    member=cfg['standard_library_member']
    standard=libs/Path(member).name
    binding=load_bindings()
    liberty=libs/Path(binding['library_member']).name
    wanted={member:standard,binding['library_member']:liberty}
    with tarfile.open(cfg['process_archive'],'r|gz') as archive:
        for item in archive:
            if item.name not in wanted:continue
            if not item.isfile():raise ValueError('Standard DB is not a regular archive member')
            with archive.extractfile(item) as src,wanted[item.name].open('wb') as dst:
                shutil.copyfileobj(src,dst)
            if all(p.is_file() for p in wanted.values()):break
    if not all(p.is_file() for p in wanted.values()):raise ValueError('Missing pinned standard-cell DB/Liberty member')
    verified=verify_liberty(liberty.read_bytes(),binding)
    (run/'technology_verification.json').write_text(json.dumps(verified,indent=2))
    inputs=[standard,liberty,BINDINGS,METADATA]
    databases=[]
    commands=[]
    memories=[]
    for size in (128,4096):
        lib=Path(cfg['sram_root'])/('RAMSP%dX16/lib/RAMSP%dX16_ss_0p99v_0p99v_125c.lib'%(size,size))
        text=lib.read_text()
        memories.append(verify_memory_liberty(lib.read_bytes(),'RAMSP%dX16'%size))
        names=re.findall(r'library\s*\(\s*"?([^\s")]+)',text)
        if len(names)!=1:raise ValueError('Ambiguous SRAM library name')
        db=libs/(names[0]+'.db')
        commands.extend(['read_lib {%s}'%lib,'write_lib {%s} -format db -output {%s}'%(names[0],db)])
        inputs.append(lib);databases.append(db)
    (run/'memory_library_verification.json').write_text(json.dumps(memories,indent=2))
    script=run/'libs.tcl'
    script.write_text('\n'.join(commands+['quit'])+'\n')
    call([cfg['tools']['lc_shell'],'-f',script],run,'lc.log')
    if not all(p.is_file() for p in databases):raise ValueError('SRAM DB compilation incomplete')
    return standard,databases,inputs+databases


def link_script(run, standard, databases, sources, includes):
    template=r'''
set_app_var search_path [concat [list @INCLUDES@] $search_path]
set_app_var target_library [list @STANDARD@]
set_app_var link_library [concat [list *] $target_library [list @DATABASES@]]
define_design_lib WORK -path ./work
# NEVER define FPGA or FPGA_SOURCE for an ASIC link.
analyze -format sverilog -define SYNTHESIS [list @SOURCES@]
elaborate e203_soc_top
current_design e203_soc_top
if {![link]} {error "Whole SoC has unresolved references"}
foreach reference [list @TARGET_CELLS@] {
    if {[sizeof_collection [get_lib_cells */$reference]] != 1} {
        error "Missing or ambiguous mapped standard cell: $reference"
    }
}
uniquify
set m128 [get_cells -hierarchical -filter "ref_name == RAMSP128X16"]
set m4096 [get_cells -hierarchical -filter "ref_name == RAMSP4096X16"]
if {[sizeof_collection $m128] != 8 || [sizeof_collection $m4096] != 130} {
    error "Unexpected whole-SoC SRAM inventory; expected 8 small and 130 large macros"
}
# TCM=64, shared SRAM=64, accelerator=2 large + 8 small. Check each owner.
foreach pattern {*u_e203_itcm_gnrl_ram* *u_e203_dtcm_gnrl_ram*} {
    set count 0
    foreach_in_collection cell $m4096 {
        if {[string match $pattern [get_object_name $cell]]} {incr count}
    }
    if {$count != 32} {error "TCM macro inventory mismatch for $pattern"}
}
foreach forbidden {sirv_sim_ram sram_wrap_32KX64 sram_wrap_64KX32 ROM1KX32} {
    if {[sizeof_collection [get_cells -hierarchical -filter "ref_name =~ $forbidden*"]] != 0} {
        error "Functional memory branch leaked into ASIC SoC: $forbidden"
    }
}
redirect check_design.rpt {check_design}
redirect references.rpt {report_reference -hierarchy}
redirect hierarchy.rpt {report_hierarchy}
write -format ddc -hierarchy -output linked.ddc
set out [open memory_inventory.tsv w]
foreach_in_collection cell [add_to_collection $m128 $m4096] {
    puts $out "[get_object_name $cell]\t[get_attribute $cell ref_name]"
}
close $out
puts "ARCH03_ASIC_LINK_READY whole_soc=true synthesis_verified=false timing_verified=false"
quit
'''
    for key,value in {
        'STANDARD':'{%s}'%standard,
        'DATABASES':' '.join('{%s}'%p for p in databases),
        'SOURCES':' '.join('{%s}'%p for p in sources),
        'TARGET_CELLS':' '.join(sorted(v['target'] for v in load_bindings()['cells'].values())),
        'INCLUDES':' '.join('{%s}'%p for p in includes)
    }.items():template=template.replace('@'+key+'@',value)
    return template


def link_soc(cfg,run,platform_source,team_sources,call):
    platform=run/'platform'
    manifest=install(platform_source,platform,asic=True)
    sources=platform_sources(platform)+team_sources
    sources.append(Path(__file__).resolve().parents[1]/'rtl/arch03_tcm_ram.sv')
    # Keep configuration and source headers in scope, but never compile tb_top.
    includes=list(dict.fromkeys([run,platform/'rtl/e203/core']+[p.parent for p in sources]))
    standard,databases,lib_inputs=libraries(cfg,run,call)
    tracked=sources+lib_inputs+[run/'arch02_sram_config.vh']
    tracked += [p for p in platform.rglob('*') if p.is_file()]
    before={str(p):sha(p) for p in tracked}
    (run/'source_inputs.json').write_text(json.dumps(before,indent=2))
    script=run/'link.tcl'
    script.write_text(link_script(run,standard,databases,sources,includes))
    log=call([cfg['tools']['dc_shell'],'-f',script],run,'dc_link.log')
    if 'ARCH03_ASIC_LINK_READY whole_soc=true synthesis_verified=false timing_verified=false' not in log:
        raise ValueError('Missing whole-SoC link completion marker')
    if not (run/'linked.ddc').is_file():raise ValueError('Missing linked whole-SoC DDC')
    for path,digest in before.items():
        if sha(Path(path))!=digest:raise ValueError('ASIC link input changed: '+path)
    return dict(status='linked',scope='whole_soc_link_only',tcm_mode='asic_macro',
                synthesis_verified=False,timing_verified=False,gate_simulation_verified=False,
                physical_signoff=False,platform_baseline_sha256=manifest['baseline_sha256'],
                expected_macros={'RAMSP128X16':8,'RAMSP4096X16':130},
                check_design_warnings_require_review=True,
                artifacts={p.name:sha(p) for p in run.iterdir() if p.is_file()},
                library_inputs={str(p):sha(p) for p in lib_inputs})
