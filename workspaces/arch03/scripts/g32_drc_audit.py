"""Read-only N1 constraint/driver inventory; never repairs or grants STA PASS.

Run through the normal locked server runner. Queries are derived from the
selected report, not historical B instance numbers. Unknown formats and
unresolved objects remain explicit review failures.
"""
from collections import Counter
import json
from pathlib import Path
import re

from server_run import sha, save
from g32_gate import verify_synthesis, probe_script, parse_probe, PROBE_MARKER
from soc_power import power_databases, tcl_path
from soc_synth import require_tool_marker
from g32_paths import allowed_run
import g32_gate as gate_dependency
import g32_paths as paths_dependency

SCHEMA = 'g32-readonly-drc-audit-v1'
MARKER = 'G32_DRC_QUERY_COMPLETE netlist_modified=false'
NO_VIOLATIONS = 'This design has no violated constraints'
NET_SECTIONS = {'max_transition', 'max_capacitance', 'max_fanout', 'multiple_port_nets'}
SECTIONS = NET_SECTIONS | {'max_delay/setup', 'min_delay/hold', 'min_period',
                           'min_pulse_width', 'max_area', 'max_dynamic_power',
                           'max_leakage_power', 'clock_gating_setup', 'clock_gating_hold'}
NUMBER = r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?'
VIOLATION_MARKER = r'\(VIOLATED(?:: increase significant digits)?\)'


def constraints_inventory(text):
    """Count report records, retaining unknown/wrapped formats without guessing."""
    section = None
    rows = []
    unparsed = []
    pending = None
    parent_net = None
    for line_number, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        first = stripped.split(' ', 1)[0].split('\t', 1)[0]
        if first in SECTIONS:
            section, pending, parent_net = first, None, None
            continue
        if re.fullmatch(r'(?:max_|min_|clock_gating_|multiple_port)[A-Za-z_/]+', first):
            section, pending, parent_net = None, None, None
            continue
        marker = re.search(VIOLATION_MARKER, line)
        if marker:
            left = line[:marker.start()].strip()
            fields = left.split()
            numeric = []
            while fields and re.fullmatch(NUMBER, fields[-1]):
                numeric.insert(0, fields.pop())
            target = fields[0] if len(fields) == 1 else None
            wrapped = False
            query_target = target
            object_kind = 'object'
            if not fields and pending:
                target, object_kind, query_target = pending
                wrapped = True
            parsed = bool(section and target and numeric and len(re.findall(VIOLATION_MARKER,line)) == 1
                          and not line[marker.end():].strip())
            row = dict(line=line_number, section=section, target=target if parsed else None,
                       numbers=numeric, raw=line, parsed=parsed, wrapped=wrapped,
                       object_kind=object_kind, query_target=query_target if parsed else None,
                       report_precision_warning='increase significant digits' in marker.group(0))
            rows.append(row)
            if not parsed:
                unparsed.append(dict(line=line_number, raw=line, reason='Unrecognized violation row'))
            pending = None
            continue
        if re.search(r'\bVIOLATED\b', line) and NO_VIOLATIONS not in line:
            unparsed.append(dict(line=line_number, raw=line, reason='Unrecognized violation marker'))
        # DC also prints a decorated net header followed by PIN subrecords.
        # Keep every violation, but query its parent net once. Only these exact
        # forms are recognized; blank/unknown continuations still fail closed.
        pin = re.fullmatch(r'PIN\s*:\s*(\S+)', stripped)
        decorated = re.fullmatch(r'(\S+)\s+\(dont_touch\)', stripped)
        if pin and '/' in pin.group(1):
            pending = (pin.group(1), 'pin', parent_net or pin.group(1))
        elif decorated and '/' in decorated.group(1) and section in NET_SECTIONS:
            parent_net = decorated.group(1)
            pending = (parent_net, 'net', parent_net)
        elif len(stripped.split()) == 1 and '/' in stripped and not set(stripped) <= {'-', '*'}:
            pending = (stripped, 'object', stripped)
            parent_net = None
        else:
            pending = None
    clear_markers = text.count(NO_VIOLATIONS)
    if clear_markers and (rows or unparsed):
        raise ValueError('Constraint report contradicts its no-violations marker')
    clear = clear_markers == 1 and not rows and not unparsed
    if not clear and not rows and not unparsed:
        unparsed.append(dict(line=None, raw='', reason='Missing explicit clean marker or violation rows'))
    targets = sorted({r['query_target'] for r in rows if r['parsed'] and r['section'] in NET_SECTIONS})
    return dict(explicit_no_violations=clear, violation_record_count=len(rows),
                by_section=dict(Counter(r['section'] or 'unknown' for r in rows)),
                violations=rows, unparsed=unparsed, extraction_complete=not unparsed,
                query_targets=targets, unique_query_target_count=len(targets),
                count_scope='report records; one net can appear in several pin/constraint records')


def dependency_identity(synthesis):
    """Supplement the frozen synth input list using its original bundle manifest."""
    source_bundle = Path(synthesis).resolve().parents[2]
    relative = 'workspaces/arch03/scripts/install_systolic_b.py'
    manifest_path = source_bundle/'manifest.json'
    manifest = json.loads(manifest_path.read_text())
    expected = manifest['files'].get(relative)
    if not expected or sha(source_bundle/relative) != expected:
        raise ValueError('Original bundle installer dependency changed or is untracked')
    receipts = json.loads((Path(synthesis)/'source_inputs.json').read_text())
    listed = any(Path(p).resolve() == (source_bundle/relative).resolve() and d == expected
                 for p, d in receipts.items())
    return dict(path=str(source_bundle/relative), sha256=expected,
                bundle_manifest=str(manifest_path), bundle_manifest_sha256=sha(manifest_path),
                listed_in_original_source_inputs=listed,
                evidence='original frozen package manifest; no modification of old synthesis receipt')


def _target_list(targets):
    if len(targets) != len(set(targets)):
        raise ValueError('Duplicate DRC query target')
    # Restrict report names to literal Tcl words and literal filter strings.
    # Bracketed bus names remain supported; unsupported escaped names fail.
    for target in targets:
        if not target or re.search(r'[\s{}"\\;]', target):
            raise ValueError('Unsupported DRC object name: '+repr(target))
    return ' '.join(tcl_path(target) for target in targets)


def script(synthesis, targets):
    original = probe_script(Path(synthesis))
    anchor = '    set out [open mapped_port_probe.tsv w]'
    if original.count(anchor) != 1:
        raise ValueError('Mapped query template changed')
    extra = r'''
    # Only get/report operations on the original DDC. No compile, sizing,
    # constraint changes or design writes occur in this query.
    proc n1_optional_attribute {object attribute} {
        if {[catch {get_attribute -quiet $object $attribute} value] || $value eq ""} {
            return unavailable
        }
        return [string map [list "\t" " " "\n" " "] $value]
    }
    set output [open drc_driver_inventory.tsv w]
    puts $output "schema\tg32-drc-driver-query-v1"
    foreach name {@TARGETS@} {
        # -filter exact equality is intentional: [] in bus names must not
        # become glob matches, and no historical U-number is embedded.
        set condition [format {full_name == "%s"} $name]
        set pins [get_pins -quiet -hierarchical -filter $condition]
        set nets [get_nets -quiet -hierarchical -filter $condition]
        set ports [get_ports -quiet -filter $condition]
        puts $output "target\t$name\t[sizeof_collection $pins]\t[sizeof_collection $nets]\t[sizeof_collection $ports]"
        if {[sizeof_collection $pins] > 0} {
            set nets [add_to_collection -unique $nets [get_nets -quiet -of_objects $pins]]
        }
        if {[sizeof_collection $ports] > 0} {
            set nets [add_to_collection -unique $nets [get_nets -quiet -of_objects $ports]]
        }
        foreach_in_collection net $nets {
            set netname [get_object_name $net]
            set connected [all_connected -leaf $net]
            puts $output "net\t$name\t$netname\t[sizeof_collection $connected]"
            foreach attr {total_capacitance max_capacitance max_transition} {
                puts $output "net_attribute\t$name\t$netname\t$attr\t[n1_optional_attribute $net $attr]"
            }
            foreach_in_collection endpoint $connected {
                set object [get_object_name $endpoint]
                set class [get_attribute $endpoint object_class]
                set direction [get_attribute $endpoint direction]
                set driver [expr {($class eq "pin" && $direction eq "out") || ($class eq "port" && $direction eq "in") || $direction eq "inout"}]
                puts $output "endpoint\t$name\t$netname\t$object\t$class\t$direction\t$driver"
                if {$class eq "pin" && $driver} {
                    set cell [get_cells -quiet -of_objects $endpoint]
                    if {[sizeof_collection $cell] != 1} {error "N1 DRC driver cell missing/ambiguous: $object"}
                    set cellname [get_object_name $cell]
                    puts $output "driver\t$name\t$netname\t$object\t$cellname\t[get_attribute $cell ref_name]"
                    foreach attr {area dont_touch dont_size size_only} {
                        puts $output "driver_attribute\t$name\t$cellname\t$attr\t[n1_optional_attribute $cell $attr]"
                    }
                    foreach_in_collection input [get_pins -quiet -of_objects $cell -filter "direction == in"] {
                        puts $output "driver_input\t$name\t$cellname\t[get_object_name $input]\t[get_object_name [get_nets -quiet -of_objects $input]]"
                    }
                }
            }
        }
    }
    close $output
    puts "@MARKER@"
'''.replace('@TARGETS@', _target_list(targets)).replace('@MARKER@', MARKER)
    return original.replace(anchor, extra+anchor)


def parse_driver_inventory(text, targets):
    rows = [line.split('\t') for line in text.splitlines()]
    if not rows or rows[0] != ['schema', 'g32-drc-driver-query-v1']:
        raise ValueError('Missing N1 driver inventory schema')
    sizes = {'target':5, 'net':4, 'net_attribute':5, 'endpoint':7,
             'driver':6, 'driver_attribute':5, 'driver_input':5}
    actual = {}
    nets = {}
    drivers = []
    endpoints = Counter()
    endpoint_keys = set()
    expected_drivers = set()
    actual_drivers = set()
    for row in rows[1:]:
        if not row or row[0] not in sizes or len(row) != sizes[row[0]] or row[1] not in targets:
            raise ValueError('Unknown/malformed N1 driver inventory record')
        kind, target = row[:2]
        if kind == 'target':
            if target in actual or any(not re.fullmatch(r'0|[1-9][0-9]*', x) for x in row[2:]):
                raise ValueError('Duplicate/invalid driver target resolution')
            actual[target] = dict(zip(('pins', 'nets', 'ports'), map(int, row[2:])))
        elif target not in actual:
            raise ValueError('Driver record precedes target resolution')
        elif kind == 'net':
            key = (target, row[2])
            if key in nets or not re.fullmatch(r'0|[1-9][0-9]*', row[3]):
                raise ValueError('Duplicate/invalid connected net')
            nets[key] = int(row[3])
        elif kind == 'endpoint':
            if row[4] not in ('pin', 'port') or row[5] not in ('in', 'out', 'inout') or row[6] not in ('0','1'):
                raise ValueError('Unknown driver endpoint direction/class')
            key = (target,row[2],row[3])
            driver = ((row[4]=='pin' and row[5]=='out') or
                      (row[4]=='port' and row[5]=='in') or row[5]=='inout')
            if key in endpoint_keys or int(row[6]) != int(driver):
                raise ValueError('Duplicate/incorrect driver endpoint classification')
            endpoint_keys.add(key)
            if row[4]=='pin' and driver:
                expected_drivers.add(key)
            endpoints[(target, row[2])] += 1
        elif kind == 'driver':
            key = (target,row[2],row[3])
            if key in actual_drivers or key not in expected_drivers or not row[4] or not row[5]:
                raise ValueError('Unobserved/duplicate/invalid driver cell record')
            actual_drivers.add(key)
            drivers.append(dict(target=target, net=row[2], pin=row[3], cell=row[4], reference=row[5]))
    if (set(actual) != set(targets) or any(endpoints[k] != count for k,count in nets.items()) or
            set(endpoints)-set(nets) or expected_drivers != actual_drivers):
        raise ValueError('Incomplete driver target/net/endpoint inventory')
    unresolved = [name for name,counts in actual.items() if not sum(counts.values()) or
                  not any(t == name for t,_ in nets)]
    return dict(target_resolution=actual, queried_net_count=len(nets),
                unique_net_names=sorted({n for _,n in nets}), driver_records=drivers,
                unique_driver_cells=sorted({r['cell'] for r in drivers}),
                unresolved_targets=unresolved, extraction_complete=not unresolved,
                raw_record_count=len(rows)-1,
                missing_optional_attributes='unavailable is not zero; inspect raw TSV')


def audit(cfg, run, synthesis, expected_sha, call):
    run=allowed_run(run,cfg,'N1 DRC output');synthesis=allowed_run(synthesis,cfg,'N1 synthesis')
    summary, _ = verify_synthesis(synthesis, expected_sha, cfg)
    if any((run/n).exists() for n in ('drc_audit.tcl','summary.json','drc_driver_inventory.tsv')):
        raise ValueError('N1 DRC audit requires a fresh output directory')
    report_names = ('summary.json','mapped.ddc','mapped.v','mapped.sdc','task_mode.sdc',
                    'constraints.rpt','metrics.txt','check_timing.rpt','check_design_mapped.rpt',
                    'latch_inventory.txt','area_inventory.json','mapped_probe_inventory.tsv')
    before = {}
    for name in report_names:
        path = synthesis/name
        digest = expected_sha if name == 'summary.json' else summary['artifacts'][name]
        if sha(path) != digest:
            raise ValueError('Frozen N1 DRC input changed: '+name)
        before[str(path)] = digest
    dependency = dependency_identity(synthesis)
    before[dependency['path']] = dependency['sha256']
    before[dependency['bundle_manifest']] = dependency['bundle_manifest_sha256']
    for path in power_databases(synthesis)+[Path(__file__), Path(gate_dependency.__file__), Path(paths_dependency.__file__)]:
        before[str(path.resolve())] = sha(path)
    inventory = constraints_inventory((synthesis/'constraints.rpt').read_text())
    save(run/'constraint_inventory.json', inventory)
    tcl = run/'drc_audit.tcl'
    tcl.write_text(script(synthesis, inventory['query_targets']))
    before[str(tcl)] = sha(tcl)
    save(run/'source_inputs.json', before)
    command = [cfg['tools']['dc_shell'], '-f', tcl]
    save(run/'drc_audit_command.json', [str(p) for p in command])
    log = call(command, run, 'drc_audit.log')
    for marker in (MARKER, PROBE_MARKER):
        require_tool_marker(log, marker)
    drivers = parse_driver_inventory((run/'drc_driver_inventory.tsv').read_text(), inventory['query_targets'])
    probe = parse_probe((run/'mapped_port_probe.tsv').read_text(),
                        (synthesis/'mapped_probe_inventory.tsv').read_text())
    for name,digest in before.items():
        if sha(Path(name)) != digest:
            raise ValueError('N1 read-only DRC input changed: '+name)
    verify_synthesis(synthesis, expected_sha, cfg)
    return dict(schema=SCHEMA, status='drc_diagnostics_ready_review_required',
                scope='n1_original_mapped_ddc_readonly_constraint_and_driver_inventory',
                synthesis_run=str(synthesis), synthesis_summary_sha256=expected_sha,
                constraints=inventory, drivers=drivers, mapped_probe=probe,
                supplemental_dependency=dependency, metrics=summary['metrics'],
                area_summary=summary['area_summary'], netlist_modified=False,
                constraints_modified=False, strict_timing_verified=False, physical_signoff=False,
                constraint_report_clear=inventory['explicit_no_violations'],
                driver_query_complete=drivers['extraction_complete'] and inventory['extraction_complete'],
                review='DRC, setup/hold, clock/CDC/structural warnings and functional evidence remain separate acceptance checks',
                artifacts={p.name:sha(p) for p in run.iterdir() if p.is_file()})
