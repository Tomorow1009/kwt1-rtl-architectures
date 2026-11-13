"""Read frozen B0/N1/T80/T64 SAIF and mapped.v; emit every unknown declaration.

Inputs remain unchanged. No simulation, PT run, activity assignment, or power
approval. Output is a new directory containing compressed JSONL and receipts.
SAIF aliases are declarations, not a distinct physical-net inventory.
"""
import argparse
from collections import Counter
from decimal import Decimal
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys

import native_saif_activity as native
import t80_window
from saif_syntax import integer_ticks
from dma16_unknown_netlist import index_netlist, resolve_alias

LAYERS = tuple('layer_%02d' % i for i in range(1, 13))
ROOT = 'tb_top.u_e203_soc_top'
LIMIT_JSON = 16 * 1024**2
LIMIT_NETLIST = 256 * 1024**2
LIMIT_SAIF = 256 * 1024**2
LIMIT_OUTPUT_CASE = 256 * 1024**2
RESERVE_BYTES = 2 * 1024**3
OUTPUT_CHECK_BYTES = 4 * 1024**2
DEPENDENCIES = ('native_saif_activity', 'saif_syntax', 'dma16_unknown_netlist',
                'dma16_structural_audit', 'icb32_power', 'soc_power', 'icb32_synth', 't80_window')


def require(value, message):
    if not value:raise ValueError(message)


def sha(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(4 * 1024**2), b''):result.update(chunk)
    return result.hexdigest()


def stamp(path):
    info = Path(path).stat()
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def scoped(path, root):
    path = Path(path).resolve()
    path.relative_to(root)
    return path


def small(path, expected=None):
    require(Path(path).stat().st_size <= LIMIT_JSON, 'JSON exceeds fixed small-file limit')
    raw = Path(path).read_bytes()
    if expected is not None:require(hashlib.sha256(raw).hexdigest() == expected, 'JSON SHA changed: ' + str(path))
    return json.loads(raw.decode('utf8'))


def save(path, value):
    with Path(path).open('x', encoding='utf8') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n');stream.flush();os.fsync(stream.fileno())


def dependencies():
    result = {'tool': dict(path=str(Path(__file__).resolve()), sha256=sha(__file__))}
    for name in DEPENDENCIES:
        require(name in sys.modules and getattr(sys.modules[name], '__file__', None),
                'Runtime dependency module is absent: ' + name)
        path = Path(sys.modules[name].__file__).resolve()
        require(path.is_file() and path.suffix == '.py', 'Expected explicit Python source dependency: ' + name)
        result[name] = dict(path=str(path), sha256=sha(path))
    return result


def dependencies_unchanged(before):
    require(dependencies() == before, 'Runtime dependency identity changed during unknown inventory')


def output_guard(output):
    free = shutil.disk_usage(str(output)).free
    require(free >= RESERVE_BYTES + 2 * OUTPUT_CHECK_BYTES,
            'Output 2GiB reserve reached; partial inventory retained')
    return free


def mapped_signal(instance, leaf, index):
    parts = tuple(instance)
    if parts[:1] == ('u_e203_soc_top',):parts = ('tb_top',) + parts
    path = '.'.join(parts)
    normalized = leaf
    # SAIF bit selects have no separating space. Preserve a literal escaped
    # scalar ending in [n] if it really exists before trying a vector select.
    if path in index['scopes']:
        module = index['modules'][index['scopes'][path]]
        match = re.fullmatch(r'(.*)\[(\d+)\]', leaf)
        if leaf not in module['nets'] and match and match.group(1) in module['nets']:
            normalized = match.group(1) + ' [' + match.group(2) + ']'
    result = resolve_alias(path + '.' + normalized, index)
    if result['disposition'] == 'mapped_declaration_only':
        result['disposition'] = 'mapped_local_declaration_only_global_alias_review_required'
    elif result['disposition'] == 'external_model_internal_requires_review':
        # Without the linked Liberty pin inventory, a leaf-cell Q/D/CEN is not
        # distinguishable from a private model variable by hierarchy alone.
        result['disposition'] = 'external_cell_port_or_model_internal_requires_review'
        result['library_pin_or_private_model_node_unresolved'] = True
    result['original_saif_leaf'] = leaf
    result['is_no_load_waiver'] = False
    return result


def scan(path, window, expected, index, emit, window_reader=native.window_values):
    """Streaming parser matching the frozen native audit, plus unknown output."""
    path = Path(path)
    before = stamp(path)
    require(before[2] == expected['bytes'] and before[2] <= LIMIT_SAIF, 'SAIF size differs/exceeds explicit limit')
    start, end, duration = window_reader(window);duration = Decimal(duration)
    stats = dict(declarations=0, toggle_count=0, unknown_declarations=0, fully_unknown_declarations=0,
                 conditional_records=0, T0_ticks=0, T1_ticks=0, TX_ticks=0, TZ_ticks=0,
                 combined_XZ_declarations=0, unknown_ticks=0)
    groups = {key: dict(declarations=0, toggle_count=0, unknown_declarations=0, unknown_examples=[])
              for key in native.COMPONENTS}
    modules = {key: set() for key in ('u_arch03_accel', 'u_arch03_arb', 'u_arch03_router', 'u_arch03_shared')}
    scopes, ports = set(), set()
    stack = [];scale = None;ticks = None;root_seen = False;root_closed = False;vcs = False
    units = dict(fs=Decimal('.000001'), ps=Decimal('.001'), ns=Decimal(1), us=Decimal(1000))
    digest = hashlib.sha256();byte_count = [0]
    categories, models = Counter(), Counter()
    watched = []

    def lines():
        with path.open('rb') as stream:
            for line in stream:
                byte_count[0] += len(line)
                require(byte_count[0] <= expected['bytes'], 'SAIF grew while parsing')
                digest.update(line)
                yield line.decode('ascii')

    def observe(node, frames):
        require(node and isinstance(node[0], str) and scale is not None and ticks is not None,
                'Signal before complete SAIF time header')
        instance = tuple(native.identifier(frame[1]) for frame in frames
                         if frame and frame[0] == 'INSTANCE' and len(frame) > 1)
        if instance[:2] == ('tb_top', 'u_e203_soc_top'):prefix = 2
        elif instance[:1] == ('u_e203_soc_top',):prefix = 1
        else:raise ValueError('Activity outside frozen whole SoC')
        scopes.add('/'.join(instance[:prefix]))
        leaf = native.identifier(node[0]);full = '/'.join(instance + (leaf,))
        counts = {};conditional = 0
        for entry in node[1:]:
            require(isinstance(entry, list) and entry, 'Malformed signal metric')
            if entry[0] in ('T0', 'T1', 'TX', 'TZ', 'TC', 'IG'):
                require(len(entry) == 2 and entry[0] not in counts and
                        re.fullmatch(r'0|[1-9][0-9]*', entry[1]), 'Invalid/duplicate SAIF count')
                counts[entry[0]] = int(entry[1])
            elif entry[0] in ('COND', 'IOPATH'):conditional += 1
            else:raise ValueError('Unreviewed SAIF metric ' + str(entry[0]))
        require({'T0', 'T1', 'TX', 'TC'} <= set(counts), 'Incomplete SAIF counts')
        combined = 'TZ' not in counts
        if combined:
            require(vcs, 'Missing TZ without VCS producer semantics')
            stats['combined_XZ_declarations'] += 1;counts['TZ'] = 0
        require(sum(counts[key] for key in ('T0', 'T1', 'TX', 'TZ')) == ticks, 'Dwell mismatch: ' + full)
        unknown = counts['TX'] + counts['TZ']
        stats['declarations'] += 1;stats['toggle_count'] += counts['TC']
        stats['unknown_declarations'] += int(unknown > 0)
        stats['fully_unknown_declarations'] += int(unknown == ticks)
        stats['unknown_ticks'] += unknown;stats['conditional_records'] += conditional
        for key in ('T0', 'T1', 'TX', 'TZ'):stats[key + '_ticks'] += counts[key]
        for key, token in native.COMPONENTS.items():
            if token in instance:
                group = groups[key];group['declarations'] += 1;group['toggle_count'] += counts['TC']
                group['unknown_declarations'] += int(unknown > 0)
                if unknown and len(group['unknown_examples']) < 12:group['unknown_examples'].append(full)
        for token in modules:
            if token in instance:modules[token].add('/'.join(instance[:instance.index(token) + 1]))
        if len(instance) == prefix and leaf.startswith('sysmem_icb_'):ports.add(leaf[len('sysmem_icb_'):])
        watch = instance[-1:] == ('u_arch03_accel',) and bool(re.fullmatch(
            r'committed_(?:data\[\d+\]|valid|ready)', leaf))
        if unknown or watch:
            mapping = mapped_signal(instance, leaf, index)
            item = dict(declaration_ordinal=stats['declarations'], saif_name=full,
                section=frames[-1][0], unknown_ticks=unknown, T0_ticks=counts['T0'], T1_ticks=counts['T1'],
                reported_TX_ticks=counts['TX'], reported_TZ_ticks=None if combined else counts['TZ'],
                combined_TX_X_or_Z=combined, TC=counts['TC'], IG=counts.get('IG'),
                fully_unknown=unknown == ticks, conditional_records=conditional,
                conditional_semantics_need_separate_review=bool(conditional), mapping=mapping)
            if unknown:
                emit(item);categories[mapping['disposition']] += 1
                if 'reference' in mapping:models[mapping['reference']] += 1
            if watch:watched.append(item)

    for token in native.tokens(lines()):
        if token == '(':
            require(not root_closed, 'Multiple SAIF roots');stack.append([])
        elif token == ')':
            require(stack, 'Unbalanced SAIF close');node = stack.pop();require(node, 'Empty SAIF expression')
            if not stack:
                require(node[0] == 'SAIFILE', 'Wrong SAIF root');root_closed = True;continue
            parent = stack[-1];require(parent, 'Missing parent kind')
            if parent[0] in ('PORT', 'NET'):observe(node, stack)
            elif node[0] in ('PORT', 'NET', 'INSTANCE'):pass
            elif parent[0] == 'SAIFILE' and node[0] == 'TIMESCALE':
                require(scale is None and len(node) == 3 and node[2] in units, 'Invalid SAIF timescale')
                scale = Decimal(node[1]) * units[node[2]]
                require(scale.is_finite() and scale > 0, 'Invalid scale')
            elif parent[0] == 'SAIFILE' and node[0] == 'DURATION':
                require(ticks is None and len(node) == 2, 'Invalid duration')
                ticks = integer_ticks(node[1], positive=True)
            elif parent[0] == 'SAIFILE' and node[0] == 'PROGRAM_NAME':
                require(len(node) == 2, 'Invalid producer');vcs = node[1].strip('"').startswith('VCS ')
            elif parent[0] != 'SAIFILE':parent.append(node)
        elif stack:
            stack[-1].append(token)
            if len(stack) == 1 and len(stack[-1]) == 1:
                require(not root_seen and token == 'SAIFILE', 'Wrong/repeated SAIF root');root_seen = True
        else:raise ValueError('SAIF atom outside root')
    require(not stack and root_closed and scale is not None and ticks is not None and scale * ticks == duration,
            'Truncated SAIF or wrong full-task duration')
    require(len(scopes) == 1 and stats['declarations'] and stats['toggle_count'], 'Empty/ambiguous activity')
    require(all(row['declarations'] for row in groups.values()) and all(len(value) == 1 for value in modules.values()),
            'Missing/ambiguous whole-SoC module coverage')
    wanted = {name if width == 1 else name + '[%d]' % bit
              for name, (_, width) in native.SYSMEM.items() for bit in range(width)}
    require(ports == wanted, 'Source port bits differ')
    stats['reported_TX_ticks'] = stats['TX_ticks'];stats['separately_reported_TZ_ticks'] = stats['TZ_ticks']
    if stats['combined_XZ_declarations']:stats['TX_ticks'] = None;stats['TZ_ticks'] = None
    actual = dict(status='saif_scope_duration_and_residence_verified', file=path.name,
        bytes=byte_count[0], sha256=digest.hexdigest(), scope=ROOT, strip_path=next(iter(scopes)),
        start_ns=start, end_ns=end, duration_ns=str(duration), timescale_ns=str(scale), source_port_bits=len(ports),
        statistics=stats, component_activity=groups, module_paths={key: sorted(value) for key, value in modules.items()},
        declaration_counts_include_aliases=True, component_counts_overlap=True,
        timestamps_require_matching_replay_receipt=True, unknown_activity_review_required=True,
        unknown_representation='VCS_combined_TX_X_or_Z' if stats['combined_XZ_declarations'] else 'separate_TX_TZ',
        X_and_Z_separately_measured=not bool(stats['combined_XZ_declarations']), system_power_verified=False)
    require(stamp(path) == before, 'SAIF changed while parsing')
    require(actual == expected, 'Complete parsed SAIF audit differs from frozen receipt')
    require(sum(categories.values()) == stats['unknown_declarations'], 'Unknown rows incomplete')
    return dict(activity=actual, unknown_rows=stats['unknown_declarations'], classifications=dict(categories),
                mapped_reference_counts=dict(models), watched_committed_path=watched,
                top_level_unknown_declarations_listed=True,
                full_unknown_declarations_listed=not bool(stats['conditional_records']),
                conditional_subrecords_expanded=False,
                unknown_inventory_scope=('complete_top_level_no_conditional_subrecords' if not stats['conditional_records']
                                         else 'top_level_only_conditional_subrecords_require_expansion'),
                global_alias_connectivity_proved=False,
                unknown_effect_on_power_approved=False, system_power_verified=False)


def profile_contract(report):
    """Bind the inventory to this export's own stages, never a predecessor PASS."""
    if report.get('schema') == 'systolic-b-evidence-export-v1':
        return ('B0', 'systolic_b_synth', 'systolic_b_saif',
                'B_native_saif_function_and_complete_windows_passed')
    for name, rows in (('T80', 5), ('T64', 4)):
        prefix = name.lower()
        if report.get('schema') == 'arch03-'+prefix+'-evidence-export-v1':
            require(report.get('stage') == name and report.get('numeric_format') == '0x000e0c20' and
                    report.get('layout_id') == 0x00100004 and report.get('shift') == 10 and
                    report.get('row_lanes') == rows, 'Wrong '+name+' frozen numerical identity')
            return (name, prefix+'_synth', prefix+'_saif',
                    name+'_native_saif_function_and_complete_windows_passed')
    require(report.get('schema') == 'arch03-n1-evidence-export-v1' and
            report.get('stage') == 'N1' and report.get('numeric_format') == '0x000e0c20' and
            report.get('layout_id') == 0x00100004 and report.get('shift') == 10 and
            report.get('row_lanes') == 5, 'Not a supported B0 or N1 export identity')
    return ('N1', 'n1_synth', 'n1_saif', 'N1_native_saif_function_and_complete_windows_passed')


def collect(report_path, report_sha, scope_root, output, cases=LAYERS, path_validator=None):
    code_identity = dependencies()
    scope = Path(scope_root).resolve()
    scope_path = path_validator or (lambda path: scoped(path,scope))
    report_path = scope_path(report_path)
    require(re.fullmatch('[0-9a-f]{64}', report_sha), 'Pin the actual export report SHA')
    report = small(report_path, report_sha)
    profile, synth_stage, activity_stage, activity_status = profile_contract(report)
    export_receipt = small(report_path.parent / 'receipt.json')
    require(export_receipt['artifacts']['report.json'] == report_sha, 'Export receipt differs')
    selected = tuple(cases)
    require(selected and len(set(selected)) == len(selected) and set(selected) <= set(LAYERS), 'Invalid case list')
    arun = scope_path(report['activity_reference']['run'])
    activity = small(arun / 'summary.json', report['activity_reference']['sha256'])
    state = small(arun.parent / 'state.json')['stages'][activity_stage]
    require(state['status'] == 'passed' and state['summary_sha256'] == report['activity_reference']['sha256'],
            'Activity stage not frozen passed')
    srun = scope_path(report['references']['synthesis']['run'])
    synthesis = small(srun / 'summary.json', report['references']['synthesis']['sha256'])
    synthesis_state = small(srun.parent / 'state.json')['stages'][synth_stage]
    require(synthesis_state['status'] == 'passed' and
            synthesis_state['summary_sha256'] == report['references']['synthesis']['sha256'],
            'Synthesis stage not frozen passed')
    require(activity['status'] == activity_status and
            activity['synthesis_summary_sha256'] == report['references']['synthesis']['sha256'] and
            activity['firmware_sha256'] == report['firmware_sha256'], 'Mixed activity identity')
    if profile in ('N1', 'T80', 'T64'):
        require(activity.get('numeric_format') == report['numeric_format'] and
                activity.get('layout_id') == report['layout_id'] and
                activity.get('gate_summary_sha256') == report['references']['gate']['sha256'],
                'Mixed '+profile+' format or gate identity')
    netlist = scope_path(srun / 'mapped.v')
    require(synthesis['artifacts']['mapped.v'] == report['netlist_sha256'] and
            netlist.stat().st_size <= LIMIT_NETLIST and sha(netlist) == report['netlist_sha256'], 'Wrong/oversize mapped netlist')
    net_stamp = stamp(netlist);index = index_netlist(netlist.read_text(encoding='utf8'))
    require(stamp(netlist) == net_stamp, 'Netlist changed during index')
    rows = {row['case']: row for row in activity['cases']}
    require(len(rows) == len(activity['cases']) == 12 and set(rows) == set(LAYERS), 'Missing/duplicate activity layer')
    output = Path(output)
    require(output.is_absolute() and output.resolve() == output and not output.exists() and output.parent.is_dir(),
            'Use a fresh absolute output directory; no overwrite/resume')
    output.mkdir(mode=0o700)
    receipt = dict(schema=profile.lower()+'-complete-saif-unknown-map-v1', status='collecting_existing_activity',
        report=str(report_path), report_sha256=report_sha, activity_summary_sha256=report['activity_reference']['sha256'],
        netlist=str(netlist), netlist_sha256=report['netlist_sha256'], cases=[], selected_cases=list(selected),
        system_power_verified=False, no_eda_or_simulation_started=True, source_activity_modified=False,
        only_existing_B0_activity_used=profile == 'B0', only_existing_N1_activity_used=profile == 'N1',
        activity_configuration=profile,
        physical_power_bound_proved=False,
        tool_sha256=code_identity['tool']['sha256'], parser_sha256=code_identity['native_saif_activity']['sha256'],
        runtime_dependencies=code_identity,
        numeric_contract=dict(SYSMEM={key:list(value) for key,value in native.SYSMEM.items()},
                              fixed_per_SAIF_limit_bytes=LIMIT_SAIF),
        output_budget=dict(max_compressed_bytes_per_case=LIMIT_OUTPUT_CASE, reserve_bytes=RESERVE_BYTES,
            required_free_bytes=(LIMIT_OUTPUT_CASE*len(selected)*6+4)//5 + RESERVE_BYTES + LIMIT_JSON,
            free_bytes=shutil.disk_usage(str(output)).free, factor='1.2', summary_allowance_bytes=LIMIT_JSON))
    save(output / 'request.json', receipt)
    try:
        require(receipt['output_budget']['free_bytes'] >= receipt['output_budget']['required_free_bytes'],
                'Insufficient initial bounded output budget plus 2GiB reserve; no SAIF scanned')
        for name in selected:
            row = rows[name];expected = row['activity'];path = scope_path(arun / expected['file'])
            require(path.parent == arun and path.suffix == '.saif', 'Unsafe SAIF basename')
            partial = output / (name + '.unknown.jsonl.gz.partial')
            with partial.open('xb') as raw:
                output_guard(output)
                with gzip.GzipFile(filename=name + '.unknown.jsonl', fileobj=raw, mode='wb', compresslevel=1, mtime=0) as packed:
                    unchecked = [0]
                    def emit(item):
                        payload = (json.dumps(item, sort_keys=True) + '\n').encode('utf8')
                        require(len(payload) <= 1024**2, 'Unknown record exceeds 1MiB output bound')
                        if unchecked[0] + len(payload) > OUTPUT_CHECK_BYTES:
                            output_guard(output);unchecked[0] = 0
                        packed.write(payload);unchecked[0] += len(payload)
                        require(raw.tell() <= LIMIT_OUTPUT_CASE, 'Per-case output cap reached; partial retained')
                    reader = t80_window.window_values if profile == 'T80' else native.window_values
                    result = scan(path, row['task_window'], expected, index, emit,window_reader=reader)
                raw.flush();os.fsync(raw.fileno())
            require(partial.stat().st_size <= LIMIT_OUTPUT_CASE, 'Completed compressed output exceeds cap')
            output_guard(output)
            final = output / (name + '.unknown.jsonl.gz')
            os.link(str(partial), str(final));partial.unlink()
            result.update(case=name, unknown_file=final.name, unknown_file_sha256=sha(final), unknown_file_bytes=final.stat().st_size)
            save(output / (name + '.json'), result);receipt['cases'].append(result)
            print(profile+'_EXISTING_SAIF_UNKNOWN_COLLECTED', name, result['unknown_rows'], flush=True)
        require(sha(netlist) == report['netlist_sha256'] and sha(report_path) == report_sha and
                sha(arun / 'summary.json') == report['activity_reference']['sha256'] and
                sha(srun / 'summary.json') == report['references']['synthesis']['sha256'],
                'Frozen input changed during collection')
        dependencies_unchanged(code_identity)
        full_unknown = all(row['full_unknown_declarations_listed'] for row in receipt['cases'])
        receipt.update(status=('complete_existing_unknown_inventory_review_required' if full_unknown else
                               'top_level_unknown_inventory_conditional_expansion_required'),
                       full12_collected=set(selected) == set(LAYERS),
                       full_unknown_inventory_complete=full_unknown,
                       unknown_declarations=sum(row['unknown_rows'] for row in receipt['cases']))
        save(output / 'summary.json', receipt)
        return receipt
    except BaseException as error:
        receipt.update(status='failed_inventory_preserved', error=str(error))
        save(output / 'failure.json', receipt)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--report-sha256', required=True)
    parser.add_argument('--scope-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--cases', nargs='+', choices=LAYERS, default=LAYERS)
    args = parser.parse_args()
    result = collect(args.report, args.report_sha256, args.scope_root, args.output, args.cases)
    print('SAIF_UNKNOWN_MAP', result['status'], 'full12=' + str(result['full12_collected']), 'system_power_verified=false')
    return 0


if __name__ == '__main__':sys.exit(main())
