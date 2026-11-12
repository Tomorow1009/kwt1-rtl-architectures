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


def repair_script(run, cfg):
    text = synth.script(run, cfg)
    text = synth.replace_once(text, 'read_ddc linked.ddc', 'read_ddc repair_seed.ddc')
    text = synth.replace_once(text, 'compile -map_effort high\n', '')
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
    tcl.write_text(repair_script(run, cfg))
    provenance = dict(schema='systolic-b-mapped-drc-repair-v1', original_run=str(original),
        original_summary_sha256=digest, original_mapped_ddc_sha256=sha(run/'repair_seed.ddc'),
        original_task_constraints_sha256=sha(original/'task_mode.sdc'),
        task_constraints_unchanged=True, rtl_changed=False, original_run_modified=False,
        command='compile -incremental_mapping -only_design_rule',
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
