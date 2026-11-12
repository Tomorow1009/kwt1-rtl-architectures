"""Explicit fresh-run DRC repair of a digest-pinned B mapped design.

No RTL, task constraints, or historical run is changed. The new mapped design
requires fresh gate/timing/area/activity review; it inherits no gate PASS.
Python 3.6; called only by the normal locked server_run synthesis stage.
"""
import json
import shutil
from pathlib import Path

from asic_link import sha
import systolic_b_synth as synth


def inspect(cfg, run, original, digest, call):
    """Read-only driver/library diagnosis of the actual DRC04 mapped design."""
    from systolic_b_gate import verify_synthesis, probe_script, PROBE_MARKER
    from soc_synth import require_tool_marker
    run, original = Path(run).resolve(), Path(original).resolve()
    verify_synthesis(original, digest, cfg)
    before = {str(original/n): sha(original/n) for n in ('summary.json', 'mapped.ddc', 'mapped.v')}
    text = probe_script(original)
    prior=json.loads((original/'summary.json').read_text())
    remembered=prior.get('mapped_repair',{}).get('compile_library_directory')
    if remembered:
        # Read-only DDC queries must also avoid loading duplicate library
        # identities. The immutable report identifies the compile DB paths.
        from soc_power import power_databases
        for database in power_databases(original):
            source=Path(remembered)/database.name
            if sha(source)!=sha(database):raise ValueError('Inspect library identity changed')
            text=text.replace(str(database),str(source))
    anchor = '    set out [open mapped_port_probe.tsv w]'
    extra = r'''
    set out [open driver_inventory.tsv w]
    set prefix u_e203_subsys_top/u_e203_subsys_main/u_e203_subsys_mems/u_arch03_accel/core
    foreach {instance expected} {U32684 BUFV2RD_12TR40 U32686 BUFV2RD_12TR40 U32433 BUFV2RD_12TR40 U30602 AOI22V2_12TR40} {
        set cell [get_cells $prefix/$instance]
        if {[sizeof_collection $cell]!=1 || [get_attribute $cell ref_name] ne $expected} {error "Unexpected DRC driver $instance"}
        puts $out "driver\t$instance\t$expected"
        foreach attr {dont_touch dont_size size_only} {
            if {[catch {get_attribute $cell $attr} value]} {set value unavailable}
            puts $out "attribute\t$instance\t$attr\t$value"
        }
        foreach_in_collection pin [get_pins -of_objects $cell] {
            if {[get_attribute $pin direction] eq "out"} {
                puts $out "output\t[get_object_name $pin]\t[get_object_name [get_nets -of_objects $pin]]"
            }
        }
    }
    foreach pattern {*/BUFV1_* */BUFV1RD_* */BUFV1R0_* */BUFV1RQ_* */BUFV2_* */BUFV2RD_* */BUFV2R0_* */BUFV2RQ_* */BUFV4_* */BUFV4RD_* */BUFV4R0_* */BUFV4RQ_*} {
        foreach_in_collection cell [get_lib_cells $pattern] {
            puts $out "candidate\t[get_object_name $cell]\t[get_attribute $cell area]"
            foreach_in_collection pin [get_lib_pins [get_object_name $cell]/*] {
                set direction [get_attribute $pin direction]
                if {$direction eq "in"} {
                    puts $out "input_cap\t[get_object_name $pin]\t[get_attribute $pin capacitance]"
                }
            }
        }
    }
    foreach name {n298364 n298366 n298367} {
        set net [get_nets $prefix/$name]
        foreach_in_collection pin [get_pins -of_objects $net -filter "direction == out"] {
            puts $out "upstream\t$name\t[get_object_name $pin]\t[get_attribute [get_cells -of_objects $pin] ref_name]"
        }
    }
    close $out
'''
    if text.count(anchor)!=1:raise ValueError('Unexpected probe template')
    tcl=run/'driver_inspect.tcl';tcl.write_text(text.replace(anchor,extra+anchor))
    log=call([cfg['tools']['dc_shell'],'-f',tcl],run,'driver_inspect.log')
    require_tool_marker(log,PROBE_MARKER)
    for name,value in before.items():
        if sha(Path(name))!=value:raise ValueError('Read-only DRC input changed')
    return dict(status='driver_diagnostics_ready',netlist_modified=False,
        synthesis_run=str(original),synthesis_summary_sha256=digest,
        artifacts={p.name:sha(p) for p in run.iterdir() if p.is_file()})


DRC04_SHA = 'dd960574b5ac119192055932b7fadcf7e245fa97446d4370d8b6a49d4e990ca4'


def repair_script(run, cfg, original=None, targeted=False, library_directory=None):
    text = synth.script(run, cfg)
    if original is not None:
        # DDC remembers the original library file identities. Compiling with
        # byte-identical copies under a second path causes DC OPT-106/OPT-128
        # for fixed technology cells. Keep the original verified DB paths for
        # this compile; fresh local copies still support downstream reporting.
        old = str(Path(run)/'libs')
        new = str(library_directory or Path(original)/'libs')
        if text.count(old)!=3:raise ValueError('Expected exact three DB paths in repair template')
        text=text.replace(old,new)
    text = synth.replace_once(text, 'read_ddc linked.ddc', 'read_ddc repair_seed.ddc')
    text = synth.replace_once(text, 'compile -map_effort high\n', '')
    if targeted:
        # Only the four exact, inspected DRC04 drivers are changed. Verify
        # matching pin directions/functions before selecting higher drive.
        sizing = r'''
set prefix u_e203_subsys_top/u_e203_subsys_main/u_e203_subsys_mems/u_arch03_accel/core
set sized [open targeted_sizing.tsv w]
foreach {instance expected replacement} {
 U32684 BUFV2RD_12TR40 BUFV4RD_12TR40
 U32686 BUFV2RD_12TR40 BUFV4RD_12TR40
 U32433 BUFV2RD_12TR40 BUFV4RD_12TR40
 U30602 AOI22V2_12TR40 AOI22V4_12TR40
} {
 set cell [get_cells $prefix/$instance]
 if {[sizeof_collection $cell]!=1 || [get_attribute $cell ref_name] ne $expected} {error "Targeted driver mismatch $instance"}
 set old [get_lib_cells */$expected]
 set new [get_lib_cells */$replacement]
 if {[sizeof_collection $old]!=1 || [sizeof_collection $new]!=1} {error "Ambiguous sizing library $instance"}
 set oldname [get_object_name $old]
 set newname [get_object_name $new]
 set pins [get_lib_pins $oldname/*]
 if {[sizeof_collection $pins]!=[sizeof_collection [get_lib_pins $newname/*]]} {error "Sizing pin count mismatch"}
 foreach_in_collection pin $pins {
  set name [lindex [split [get_object_name $pin] /] end]
  set other [get_lib_pins $newname/$name]
  if {[sizeof_collection $other]!=1 || [get_attribute $pin direction] ne [get_attribute $other direction]} {error "Sizing pin direction mismatch"}
  if {[get_attribute $pin direction] eq "out" && [get_attribute $pin function] ne [get_attribute $other function]} {error "Sizing function mismatch"}
 }
 size_cell $cell $newname
 if {[get_attribute $cell ref_name] ne $replacement} {error "Sizing failed $instance"}
 # Do not allow the incremental pass to undo this measured drive correction.
 set_dont_touch $cell true
 puts $sized "$instance\t$expected\t$replacement"
}
close $sized
compile -incremental_mapping -map_effort high
'''
        text = synth.replace_once(text, 'compile -incremental_mapping -map_effort high', sizing)
    else:
        text = synth.replace_once(text, 'compile -incremental_mapping -map_effort high',
                                  'compile -incremental_mapping -only_design_rule')
    text = synth.replace_once(text, 'redirect check_design_mapped.rpt',
                              'redirect hierarchy.rpt {report_hierarchy}\nredirect check_design_mapped.rpt')
    return text


def checked_copy(source, target, expected):
    source, target = Path(source), Path(target)
    if target.exists() or not source.is_file() or source.is_symlink() or sha(source) != expected:
        raise ValueError('Invalid/changed repair input or nonfresh destination: '+str(source))
    target.parent.mkdir(parents=True, exist_ok=True)
    with source.open('rb') as src, target.open('xb') as dst:
        shutil.copyfileobj(src, dst)
    if sha(target) != expected:
        raise ValueError('Repair copy digest mismatch: '+str(target))


def repair(cfg, run, original, digest, call):
    from systolic_b_gate import verify_synthesis
    from soc_power import power_databases
    run, original = Path(run).resolve(), Path(original).resolve()
    if any((run/name).exists() for name in ('repair_seed.ddc', 'libs', 'summary.json', 'mapped.v')):
        raise ValueError('Mapped DRC repair requires a fresh run')
    prior, _ = verify_synthesis(original, digest, cfg)
    targeted = digest == DRC04_SHA
    library_directory = Path(prior.get('mapped_repair', {}).get('compile_library_directory', str(original/'libs')))
    library_directory.resolve().relative_to(Path(cfg['server_root']).resolve()) if 'server_root' in cfg else None
    if (original/'task_mode.sdc').read_text() != synth.constraints():
        raise ValueError('Repair must retain the exact original task constraints')
    old_root = original.parents[2]
    # The mapped design must be the same B RTL/installer as this immutable
    # package, not just a compatible top-level port list or SRAM count.
    original_inputs = json.loads((original/'source_inputs.json').read_text())
    current_inputs = dict(original_inputs)
    before = dict(original_inputs)
    before.update(json.loads((original/'synthesis_inputs.json').read_text()))
    for path, value in list(original_inputs.items()):
        source = Path(path)
        try:
            relative = source.relative_to(old_root)
        except ValueError:
            continue
        name = relative.as_posix()
        if name.startswith('workspaces/') and (source.suffix in ('.v', '.sv', '.vh', '.svh') or
                source.name in ('install_systolic_b.py', 'systolic_b_soc.py')):
            current = synth.ROOT/relative
            if sha(current) != value:
                raise ValueError('Changed B hardware/installation input: '+name)
            current_inputs[str(current.resolve())] = value
    # The full original provenance remains immutable and is checked again at
    # completion. Fresh aliases bind the current bundle for downstream audits.
    for database in power_databases(original):
        if not (library_directory/database.name).is_file() or sha(library_directory/database.name)!=sha(database):
            raise ValueError('Original compile library identity/digest mismatch')
        target = run/'libs'/database.name
        checked_copy(database, target, sha(database))
        current_inputs[str(target)] = sha(target)
    for name in ('technology_verification.json', 'memory_library_verification.json'):
        checked_copy(original/name, run/name, prior['artifacts'][name])
        current_inputs[str(run/name)] = sha(run/name)
    checked_copy(original/'mapped.ddc', run/'repair_seed.ddc', prior['artifacts']['mapped.ddc'])
    sdc = run/'task_mode.sdc'
    sdc.write_text(synth.constraints())
    tcl = run/'systolic_b_drc_repair.tcl'
    tcl.write_text(repair_script(run, cfg, original, targeted, library_directory))
    provenance = dict(schema='systolic-b-mapped-drc-repair-v1', original_run=str(original),
        original_summary_sha256=digest, original_mapped_ddc_sha256=sha(run/'repair_seed.ddc'),
        original_task_constraints_sha256=sha(original/'task_mode.sdc'),
        task_constraints_unchanged=True, rtl_changed=False, original_run_modified=False,
        command='targeted equivalent-cell sizing; compile -incremental_mapping -map_effort high' if targeted else 'compile -incremental_mapping -only_design_rule',
        targeted_drc04_drivers=targeted, compile_library_directory=str(library_directory),
        copied_library_databases_sha256_identical=True,
        inherited_gate_pass=False, requires_new_gate_and_ppa=True)
    (run/'repair_provenance.json').write_text(json.dumps(provenance, indent=2)+'\n')
    current_inputs[str(Path(__file__).resolve())] = sha(Path(__file__))
    current_inputs[str(run/'arch02_sram_config.vh')] = sha(run/'arch02_sram_config.vh')
    (run/'source_inputs.json').write_text(json.dumps(current_inputs, indent=2)+'\n')
    before.update(current_inputs)
    for path in (original/'summary.json', original/'mapped.ddc', run/'repair_seed.ddc',
                 sdc, tcl, run/'repair_provenance.json', run/'source_inputs.json'):
        before[str(path)] = sha(path)
    for path, value in before.items():
        if sha(Path(path)) != value:
            raise ValueError('Repair provenance changed before DC: '+path)
    (run/'synthesis_inputs.json').write_text(json.dumps(before, indent=2)+'\n')
    text = call([cfg['tools']['dc_shell'], '-f', tcl], run, 'systolic_b_drc_repair.log')
    report = synth.collect_reports(run, prior['link_report'], before, text)
    report['mapped_repair'] = provenance
    return report
