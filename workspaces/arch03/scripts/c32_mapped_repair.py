"""Equivalent-cell repair of one pinned C32 mapped design, in a fresh run.

No compile, logic/topology change, timing exception, or inherited gate PASS.
The original three-partition provenance remains a required immutable ancestor.
Python 3.6; the CLI owns the original team lock and every DC child.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import time

import server_run as common
import c32_paths
import s0_partition_synth as partitions
import t80_synth as reports
from partition_synth_contract import require, digest, area_attribution
from n1_process import ProcessLedger, atomic_save, now

SCOPE = 'c32_equivalent_cell_repaired_whole_soc_task_mode'
ORIGIN_SHA = 'ee08629b7cc9181d6e6db4ae21205ae931c6b1fe28f5c4420afd83097e8cef87'
ORIGIN_NETLIST = '3c116d5a026b7e832030cd0c5a8def5a633ade9eaefb4efd1080851acc4bbd2c'
PREFIX = 'u_e203_subsys_top/u_e203_subsys_main/u_e203_subsys_mems/u_arch03_accel/core/'
TARGETS = {PREFIX+n: ('BUFV2RD_12TR40', 'BUFV4RD_12TR40') for n in ('U16528', 'U16527', 'U16523')}


def read(path):
    return json.loads(Path(path).read_text())


def equivalent_tokens(original, repaired):
    """Only the three inspected cell reference tokens may change anywhere."""
    old, new = partitions.module_tokens(original), partitions.module_tokens(repaired)
    require(set(old) == set(new), 'Repair changed the mapped module set')
    remaining = {p.rsplit('/', 1)[1]: pair for p, pair in TARGETS.items()}
    changes = []
    for module, tokens in old.items():
        expected = list(tokens)
        for index in range(len(tokens)-2):
            instance = tokens[index+1]
            if instance not in remaining or tokens[index+2] != '(':
                continue
            before, after = remaining[instance]
            if tokens[index] != before:
                continue
            require(not any(x['instance'] == instance for x in changes), 'Ambiguous repair instance')
            expected[index] = after
            changes.append(dict(module=module, instance=instance, before=before, after=after))
        require(expected == new[module], 'Repair changed tokens beyond equivalent references: '+module)
    require({x['instance'] for x in changes} == set(remaining), 'Missing exact reference replacement')
    return dict(schema='c32-three-buffer-token-proof-v1', changes=sorted(changes, key=lambda x:x['instance']),
                all_other_verilog_tokens_identical=True, rtl_modified=False, topology_changed=False)


def verify_cells(original, repaired):
    def rows(text):
        result = {}
        for line in text.splitlines():
            parts = line.split('\t')
            require(len(parts) == 4 and parts[0] not in result, 'Invalid leaf inventory')
            result[parts[0]] = parts[1:]
        return result
    left, right = rows(original), rows(repaired)
    require(set(left) == set(right), 'Repair added/removed physical leaves')
    delta = 0.0
    for name, before in left.items():
        after = right[name]
        if name in TARGETS:
            require((before[0], after[0]) == TARGETS[name] and
                    before[2].rsplit('/', 1)[0] == after[2].rsplit('/', 1)[0],
                    'Wrong replacement cell/library')
            require(float(after[1]) > float(before[1]), 'Expected stronger buffer area')
            delta += float(after[1])-float(before[1])
        else:
            require(before == after, 'Unrequested leaf change: '+name)
    require(set(TARGETS) <= set(left), 'Missing target leaves')
    return dict(changed_cells=sorted(TARGETS), leaf_count=len(left), area_delta_um2=delta,
                all_other_leaves_identical=True)


def sizing_script():
    triples = '\n'.join(' {%s} %s %s' % (p, pair[0], pair[1]) for p, pair in sorted(TARGETS.items()))
    return r'''
set sized [open equivalent_sizing.tsv w]
foreach {path expected replacement} {@TRIPLES@} {
 set cell [get_cells $path]
 if {[sizeof_collection $cell]!=1 || [get_attribute $cell ref_name] ne $expected} {error "Repair driver mismatch $path"}
 set old [get_lib_cells */$expected]
 set new [get_lib_cells */$replacement]
 if {[sizeof_collection $old]!=1 || [sizeof_collection $new]!=1} {error "Ambiguous equivalent library cells"}
 set oldname [get_object_name $old]
 set newname [get_object_name $new]
 set pins [get_lib_pins $oldname/*]
 if {[sizeof_collection $pins]!=[sizeof_collection [get_lib_pins $newname/*]]} {error "Equivalent pin count differs"}
 foreach_in_collection pin $pins {
  set name [lindex [split [get_object_name $pin] /] end]
  set other [get_lib_pins $newname/$name]
  set direction [get_attribute $pin direction]
  if {[sizeof_collection $other]!=1 || $direction ne [get_attribute $other direction]} {error "Equivalent pin direction differs"}
  set function {}
  if {$direction eq "out"} {
   set function [get_attribute $pin function]
   if {$function ne [get_attribute $other function]} {error "Equivalent Boolean function differs"}
  }
  puts $sized "pin\t$path\t$name\t$direction\t$function"
 }
 # Temporarily unlock only this leaf's ancestor chain for explicit sizing.
 # Restore every prior attribute; no optimization command sees this window.
 set protection {}
 set part {}
 foreach component [split $path /] {
  if {$part eq {}} {set part $component} else {append part / $component}
  set object [get_cells $part]
  if {[sizeof_collection $object]!=1} {error "Missing exact repair hierarchy"}
  if {[catch {get_attribute $object dont_touch} oldvalue]} {set oldvalue absent}
  lappend protection [list $part $oldvalue]
  set_dont_touch $object false
 }
 size_cell $cell $newname
 if {[get_attribute $cell ref_name] ne $replacement} {error "Explicit buffer sizing failed"}
 foreach item $protection {
  set object [get_cells [lindex $item 0]]
  set oldvalue [lindex $item 1]
  if {$oldvalue eq "absent"} {remove_attribute $object dont_touch} else {set_dont_touch $object $oldvalue}
 }
 puts $sized "cell\t$path\t$oldname\t$newname"
}
close $sized
'''.replace('@TRIPLES@', triples)


def repair_script(run, cfg, original):
    # DDC remembers canonical library containers; never load copied aliases.
    text = reports.script(original/'fresh_link', cfg)
    text = reports.replace_once(text, 'read_ddc linked.ddc', 'read_ddc repair_seed.ddc')
    text = reports.replace_once(text, 'set_fix_multiple_port_nets -all -buffer_constants', '# No topology repair')
    text = reports.replace_once(text, 'compile -map_effort high', '# No fresh mapping or inherited mapping claim')
    text = reports.replace_once(text, 'set_fix_hold [all_clocks]', '# Original setup/hold constraints retained')
    text = reports.replace_once(text, 'compile -incremental_mapping -map_effort high', sizing_script())
    text = reports.replace_once(text, 'redirect check_design_mapped.rpt',
                                'redirect hierarchy.rpt {report_hierarchy}\nredirect check_design_mapped.rpt')
    return text


def execute(cfg, run, original, expected, call):
    from c32_validation import verify_synthesis
    original, run = Path(original), Path(run)
    require(expected == ORIGIN_SHA and digest(original/'mapped.v') == ORIGIN_NETLIST,
            'Explicit repair applies only to the inspected C32 netlist')
    prior, _ = verify_synthesis(original, expected, cfg)
    require(prior['scope'] == 'c32_partitioned_whole_soc_task_mode', 'Repair ancestor must be the fresh C32 mapping')
    require(not any(run.iterdir()), 'Repair requires a new empty output directory')
    for name in ('technology_verification.json', 'memory_library_verification.json', 'arch02_sram_config.vh'):
        shutil.copyfile(str(original/name), str(run/name))
    (run/'libs').mkdir()
    for path in (original/'fresh_link/libs').glob('*.db'):
        require(digest(path) == digest(original/'libs'/path.name), 'Compile/report library mismatch')
        shutil.copyfile(str(path), str(run/'libs'/path.name))
    shutil.copyfile(str(original/'mapped.ddc'), str(run/'repair_seed.ddc'))
    (run/'task_mode.sdc').write_text(reports.constraints())
    require((original/'task_mode.sdc').read_text() == reports.constraints(), 'Task assumptions changed')
    (run/'repair.tcl').write_text(repair_script(run, cfg, original))
    provenance = dict(schema='c32-equivalent-cell-repair-v1', original_run=str(original),
        original_summary_sha256=expected, original_netlist_sha256=ORIGIN_NETLIST,
        original_scope=prior['scope'], compile_library_directory=str(original/'fresh_link/libs'),
        original_mapped_ddc_sha256=digest(original/'mapped.ddc'), targets={k:list(v) for k,v in TARGETS.items()},
        rtl_modified=False, topology_changed=False, task_constraints_unchanged=True,
        inherited_gate_pass=False, requires_new_gate_and_ppa=True, only_size_cell_no_compile=True)
    atomic_save(run/'repair_provenance.json', provenance)
    before = read(original/'source_inputs.json')
    before.update(read(original/'synthesis_inputs.json'))
    before.update({str(p.resolve()):digest(p) for p in [original/'summary.json', original/'mapped.v',
        original/'mapped.ddc', Path(__file__)]+[p for p in run.rglob('*') if p.is_file()]})
    atomic_save(run/'source_inputs.json', before)
    before[str(run/'source_inputs.json')] = digest(run/'source_inputs.json')
    atomic_save(run/'synthesis_inputs.json', before)
    started = time.monotonic()
    log = call([cfg['tools']['dc_shell'], '-f', run/'repair.tcl'], run, 'repair.log')
    elapsed = time.monotonic()-started
    proof = equivalent_tokens((original/'mapped.v').read_text(), (run/'mapped.v').read_text())
    proof['leaf_identity'] = verify_cells((original/'leaf_area.tsv').read_text(), (run/'leaf_area.tsv').read_text())
    atomic_save(run/'repair_identity.json', proof)
    result = reports.collect_reports(run, prior['link_report'], before, log)
    area = read(run/'area_inventory.json'); area.pop('conservative_budget_within_1_2mm2', None)
    area.update(project_budget_mm2=1.0, conservative_budget_within_1_0mm2=area['conservative_budget_library_area'] <= 1e6)
    atomic_save(run/'area_inventory.json', area)
    attribution = area_attribution(area); atomic_save(run/'partition_area.json', attribution)
    result.update(scope=SCOPE, project_limit_mm2=1.0, transaction_metadata_depth=2,
        old_linked_ddc_reused=True, block_cache_reused=True, mapped_repair=provenance,
        repair_identity=proof, block_mapping_seconds={}, final_link_seconds=elapsed,
        boundary_origin=prior['boundary_origin'], original_block_mapping_seconds=prior['block_mapping_seconds'],
        area_summary={k:v for k,v in area.items() if k!='rows'},
        partition_area={k:v for k,v in attribution.items() if k!='rows'}, stage_accepted=False)
    result['artifacts'] = {p.name:digest(p) for p in run.iterdir() if p.is_file()}
    verify_synthesis(original, expected, cfg)
    return result


def verify(run, expected, cfg):
    """Independent repaired-route verifier; never labels a repaired DDC fresh."""
    from c32_validation import verify_synthesis
    run = c32_paths.allowed_run(run, cfg, 'C32 repair')
    require(digest(run/'summary.json') == expected, 'Repair summary changed')
    report = read(run/'summary.json'); state = read(run.parent/'state.json')['stages']['c32_synth']
    require(state['status'] == 'passed' and state['summary_sha256'] == expected and
            report['scope'] == SCOPE and report['synthesis_completed'] is True and
            report['old_linked_ddc_reused'] is True and report['block_cache_reused'] is True,
            'Incomplete or falsely described repair route')
    p = report['mapped_repair']; original = Path(p['original_run'])
    require(p['original_summary_sha256'] == ORIGIN_SHA and original != run and
            digest(original/'mapped.v') == ORIGIN_NETLIST and
            p == read(run/'repair_provenance.json') and p['schema'] == 'c32-equivalent-cell-repair-v1' and
            p['targets'] == {k:list(v) for k,v in TARGETS.items()} and
            p['rtl_modified'] is False and p['topology_changed'] is False and
            p['task_constraints_unchanged'] is True and p['only_size_cell_no_compile'] is True and
            p['inherited_gate_pass'] is False and p['requires_new_gate_and_ppa'] is True,
            'Wrong repair ancestor or method')
    prior, _ = verify_synthesis(original, ORIGIN_SHA, cfg)
    require(prior['scope'] == p['original_scope'] == 'c32_partitioned_whole_soc_task_mode',
            'Repair chaining is not authorized by this exact profile')
    require(report['link_report'] == prior['link_report'] and report['transaction_metadata_depth'] == 2 and
            report['project_limit_mm2'] == report['area_summary']['project_budget_mm2'] == 1.0,
            'Repair changed the hardware contract')
    for name, want in report['artifacts'].items():
        require(Path(name).name == name and digest(run/name) == want, 'Changed repair artifact '+name)
    traced = {}
    for receipt in ('source_inputs.json', 'synthesis_inputs.json'):
        for name, want in read(run/receipt).items():
            require(digest(name) == want and (name not in traced or traced[name] == want), 'Changed repair input '+name)
            traced[name] = want
    require((run/'task_mode.sdc').read_text() == reports.constraints() and
            (run/'repair.tcl').read_text() == repair_script(run, cfg, original), 'Repair script/constraints changed')
    proof = equivalent_tokens((original/'mapped.v').read_text(), (run/'mapped.v').read_text())
    proof['leaf_identity'] = verify_cells((original/'leaf_area.tsv').read_text(), (run/'leaf_area.tsv').read_text())
    require(proof == report['repair_identity'] == read(run/'repair_identity.json'), 'Repair identity differs')
    require(digest(run/'repair_seed.ddc') == digest(original/'mapped.ddc') == p['original_mapped_ddc_sha256'],
            'Repair seed changed')
    require(p['compile_library_directory'] == str(original/'fresh_link/libs') and
            {f.name:digest(f) for f in (run/'libs').glob('*.db')} ==
            {f.name:digest(f) for f in (original/'fresh_link/libs').glob('*.db')}, 'Repair libraries differ')
    metrics = report['metrics']
    require(float(metrics['period_ns']) == 6.666666 and float(metrics['lf_period_ns']) == 66 and
            int(metrics['RAMSP128X16']) == 92 and int(metrics['RAMSP4096X16']) == 128,
            'Repaired clock/memory contract changed')
    reports.require_loop_free_timing((run/'check_timing.rpt').read_text())
    area = reports.area_inventory((run/'leaf_area.tsv').read_text(), metrics['area'])
    require(area_attribution(area) == read(run/'partition_area.json'), 'Repair area attribution changed')
    reports.area_basis(run); reports.verify_top_sysmem((run/'mapped.v').read_text())
    for name in ('sysmem_ports.tsv', 'mapped_sysmem_ports.tsv'):
        reports.verify_ports((run/name).read_text())
    return report, area


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request', required=True, type=Path)
    parser.add_argument('--request-sha256', required=True)
    args = parser.parse_args()
    require(digest(args.request) == args.request_sha256, 'Repair request changed')
    request = read(args.request)
    require(request['schema'] == 'c32-three-buffer-repair-request-v1' and
            request['bundle'] == str(common.ROOT) and request['tool_sha256'] == digest(__file__), 'Wrong repair tool/bundle')
    cfg = c32_paths.configure(read(common.ROOT/'handoff/team/server_config.json'), common.ROOT,
        Path(request['runtime_root']), request['manifest_sha256'], request['runtime_evidence'])
    common.inputs()
    session = common.ROOT/'runs'/'c32_repair01'
    require(not session.exists(), 'Preserve prior repair attempts')
    require(shutil.disk_usage(str(common.ROOT)).free >= 4*1024**3, 'Repair runtime space insufficient')
    ledger = ProcessLedger(common, Path(cfg['server_root'])/'.arch02_team_lock', session)
    while True:
        if ledger.lock.exists(): time.sleep(5); continue
        try: ledger.acquire(); break
        except OSError as error:
            if error.errno != 28 or ledger.lock.exists(): raise
            print('WAIT_ORIGINAL_LOCK_STORAGE', flush=True); time.sleep(5)
    run = session/'c32_synth'
    row = dict(status='running', pid=os.getpid(), started=now(), run=str(run))
    state = dict(schema='c32-mapped-repair-stage-v1', stages={'c32_synth':row})
    try:
        run.mkdir(parents=True); ledger.initialize(); atomic_save(session/'state.json', state)
        result = execute(cfg, run, Path(request['original_run']), request['original_summary_sha256'], ledger.call)
        common.inputs(); c32_paths.recheck(cfg); ledger.check_owner()
        atomic_save(run/'summary.json', result)
        row.update(status='passed', summary_sha256=digest(run/'summary.json'))
    except BaseException as error:
        row.update(status='failed', error=str(error)); raise
    finally:
        row['finished'] = now(); atomic_save(session/'state.json', state); ledger.release()
    print('C32_REPAIR_REPORTS_READY', row['summary_sha256'], 'requires_new_gate_and_ppa=true', flush=True)


if __name__ == '__main__':
    main()
