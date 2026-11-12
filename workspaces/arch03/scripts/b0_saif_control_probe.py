"""One-pass, selected B0 control-residence probe; no EDA or activity changes.

This is a bounded semantic-name selector, not a complete control-cone audit.
Absent macro ports are reported missing; adapter controls are not substituted.
Marginal SAIF dwell/toggles cannot prove event ordering or control correlation.
"""
import argparse
from collections import Counter
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys

import native_saif_activity as native
from saif_syntax import integer_ticks

ROOT = 'tb_top.u_e203_soc_top'
LIMIT_INPUT = 256 * 1024**2
LIMIT_JSON = 16 * 1024**2
LIMIT_OUTPUT = 8 * 1024**2
LIMIT_SELECTED = 4096
RESERVE = 2 * 1024**3
UNKNOWN_TOOL_SHA = 'c57ed783754a6411bc3d43139dcf90a420d7c5a2f87ca050b12b98e75b20056d'
DEPENDENCIES = ('native_saif_activity', 'saif_syntax', 'icb32_power', 'soc_power', 'icb32_synth')
SHARED_TOP = ('clk', 'rst_n', 'cmd_valid', 'cmd_ready', 'cmd_read', 'rsp_valid',
              'rsp_ready', 'rsp_err', 'read_pending', 'fire', 'mapped')
SHARED_BITS = tuple('bank_q[%d]' % n for n in range(5)) + tuple('cmd_addr[%d]' % n for n in range(32))
MACRO_REQUIRED = ('CLK', 'CEN', 'GWEN', 'RET1N') + tuple('WEN[%d]' % n for n in range(16))
ADAPTER_REQUIRED = ('clk', 'cs', 'we', 'wenable', 'mask[0]', 'mask[1]')
AON_REQUIRED = ('clock', 'reset', 'io_in_0_valid', 'io_in_0_ready',
                'Queue_1_io_enq_valid', 'Queue_1_io_enq_ready',
                'Queue_1_io_deq_valid', 'Queue_1_io_deq_ready')
AON_CONTROL = re.compile(r'(?:(?:clock|clk|reset|rst)(?:_n)?|(?:^|_)(?:valid|ready|enable|en))(?:\[\d+\])?$', re.I)


def require(ok, message):
    if not ok:raise ValueError(message)


def sha(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024**2), b''):result.update(chunk)
    return result.hexdigest()


def stamp(path):
    s = Path(path).stat()
    return s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns


def small(path, expected=None):
    require(Path(path).stat().st_size <= LIMIT_JSON, 'Small JSON limit exceeded')
    raw = Path(path).read_bytes()
    require(expected is None or hashlib.sha256(raw).hexdigest() == expected, 'Input JSON SHA differs')
    return json.loads(raw.decode('utf8'))


def scoped(path, root):
    result = Path(path).resolve();result.relative_to(root)
    return result


def save(path, value):
    import os
    raw = (json.dumps(value, indent=2, sort_keys=True) + '\n').encode('utf8')
    require(len(raw) <= LIMIT_OUTPUT, 'Bounded output limit exceeded')
    with Path(path).open('xb') as stream:
        stream.write(raw);stream.flush();os.fsync(stream.fileno())


def dependencies():
    result = {'tool': {'path': str(Path(__file__).resolve()), 'sha256': sha(__file__)}}
    for name in DEPENDENCIES:
        path = Path(sys.modules[name].__file__).resolve()
        require(path.suffix == '.py' and path.is_file(), 'Expected source dependency')
        result[name] = {'path': str(path), 'sha256': sha(path)}
    return result


def select(instance, leaf):
    """Return only fixed selector identities, with exact bank/side where known."""
    roles = []
    if instance[-1:] == ('u_arch03_shared',) and leaf in SHARED_TOP + SHARED_BITS:
        roles.append(dict(kind='shared_top', key=leaf))
    if 'u_arch03_shared' in instance:
        tail = '/'.join(instance[instance.index('u_arch03_shared') + 1:])
        match = re.fullmatch(r'banks\[(\d+)\][/.](low|high)(?:[/.](memory))?', tail)
        if match:
            bank, side, memory = match.groups()
            require(0 <= int(bank) < 32, 'Unexpected shared bank index')
            if memory and leaf in MACRO_REQUIRED:
                roles.append(dict(kind='shared_macro', bank=int(bank), side=side, key=leaf))
            elif not memory and leaf in ADAPTER_REQUIRED:
                roles.append(dict(kind='shared_adapter', bank=int(bank), side=side, key=leaf))
    if 'u_sirv_aon' in instance and (leaf in AON_REQUIRED or AON_CONTROL.search(leaf)):
        roles.append(dict(kind='aon_control_name', key=leaf,
                          top=instance[-1:] == ('u_sirv_aon',)))
    return roles


def coverage(rows, observed):
    identities = Counter()
    for row in rows:
        for role in row['roles']:
            if role['kind'] in ('shared_macro', 'shared_adapter'):
                key = (role['kind'], role['bank'], role['side'], role['key'])
            elif role['kind'] == 'aon_control_name':
                if not role['top']:continue
                key = (role['kind'], role['key'])
            else:key = (role['kind'], role['key'])
            identities[key] += 1
    expected = [('shared_top', key) for key in SHARED_TOP + SHARED_BITS]
    expected += [(kind, bank, side, key) for kind, names in (
        ('shared_macro', MACRO_REQUIRED), ('shared_adapter', ADAPTER_REQUIRED))
        for bank in range(32) for side in ('low', 'high') for key in names]
    expected += [('aon_control_name', key) for key in AON_REQUIRED]
    missing = [list(key) for key in expected if not identities[key]]
    duplicate = [dict(identity=list(key), records=count) for key, count in identities.items() if count > 1]
    return dict(required_identity_count=len(expected), missing=missing, duplicate_records=duplicate,
        shared_scope_paths=sorted(observed['shared']), aon_scope_paths=sorted(observed['aon']),
        selected_unknown_records=sum(row['unknown_ticks'] > 0 for row in rows),
        selected_conditional_records=sum(row['conditional_records'] for row in rows),
        required_presence_complete=not missing and len(observed['shared']) == 1 and len(observed['aon']) == 1,
        adapter_is_not_macro_pin_evidence=True, absence_is_not_knownness=True,
        generated_n_and_T_cones_still_require_mapped_review=True)


def scan(path, window, expected, captured=None):
    """Recompute the complete frozen native audit while retaining selected rows."""
    path = Path(path);before = stamp(path)
    require(before[2] == expected['bytes'] and before[2] <= LIMIT_INPUT, 'SAIF size differs/exceeds limit')
    start, end, duration = native.window_values(window);duration = Decimal(duration)
    stats = dict(declarations=0, toggle_count=0, unknown_declarations=0, fully_unknown_declarations=0,
        conditional_records=0, T0_ticks=0, T1_ticks=0, TX_ticks=0, TZ_ticks=0,
        combined_XZ_declarations=0, unknown_ticks=0)
    groups = {key: dict(declarations=0, toggle_count=0, unknown_declarations=0, unknown_examples=[])
              for key in native.COMPONENTS}
    modules = {key: set() for key in ('u_arch03_accel', 'u_arch03_arb', 'u_arch03_router', 'u_arch03_shared')}
    scopes, ports = set(), set();observed = dict(shared=set(), aon=set())
    stack = [];scale = None;ticks = None;root_seen = False;root_closed = False;vcs = False
    units = dict(fs=Decimal('.000001'), ps=Decimal('.001'), ns=Decimal(1), us=Decimal(1000))
    digest = hashlib.sha256();byte_count = [0];retained_bytes = [0]
    selected = [] if captured is None else captured

    def lines():
        with path.open('rb') as stream:
            for line in stream:
                byte_count[0] += len(line)
                require(byte_count[0] <= expected['bytes'], 'SAIF grew during scan')
                digest.update(line);yield line.decode('ascii')

    def observe(node, frames):
        require(node and isinstance(node[0], str) and scale is not None and ticks is not None,
                'Signal before complete SAIF header')
        instance = tuple(native.identifier(frame[1]) for frame in frames
                         if frame and frame[0] == 'INSTANCE' and len(frame) > 1)
        if instance[:2] == ('tb_top', 'u_e203_soc_top'):prefix = 2
        elif instance[:1] == ('u_e203_soc_top',):prefix = 1
        else:raise ValueError('Activity outside frozen whole SoC')
        scopes.add('/'.join(instance[:prefix]));leaf = native.identifier(node[0])
        full = '/'.join(instance + (leaf,));counts = {};conditional = []
        for entry in node[1:]:
            require(isinstance(entry, list) and entry, 'Malformed signal metric')
            if entry[0] in ('T0', 'T1', 'TX', 'TZ', 'TC', 'IG'):
                require(len(entry) == 2 and entry[0] not in counts and
                        re.fullmatch(r'0|[1-9][0-9]*', entry[1]), 'Invalid/duplicate SAIF count')
                counts[entry[0]] = int(entry[1])
            elif entry[0] in ('COND', 'IOPATH'):conditional.append(entry)
            else:raise ValueError('Unreviewed SAIF metric ' + str(entry[0]))
        require({'T0', 'T1', 'TX', 'TC'} <= set(counts), 'Incomplete SAIF counts')
        combined = 'TZ' not in counts
        if combined:
            require(vcs, 'Missing TZ without VCS semantics')
            stats['combined_XZ_declarations'] += 1;counts['TZ'] = 0
        require(sum(counts[key] for key in ('T0', 'T1', 'TX', 'TZ')) == ticks, 'Dwell mismatch: ' + full)
        unknown = counts['TX'] + counts['TZ']
        stats['declarations'] += 1;stats['toggle_count'] += counts['TC']
        stats['unknown_declarations'] += int(unknown > 0)
        stats['fully_unknown_declarations'] += int(unknown == ticks)
        stats['unknown_ticks'] += unknown;stats['conditional_records'] += len(conditional)
        for key in ('T0', 'T1', 'TX', 'TZ'):stats[key + '_ticks'] += counts[key]
        for key, token in native.COMPONENTS.items():
            if token in instance:
                group = groups[key];group['declarations'] += 1;group['toggle_count'] += counts['TC']
                group['unknown_declarations'] += int(unknown > 0)
                if unknown and len(group['unknown_examples']) < 12:group['unknown_examples'].append(full)
        for token in modules:
            if token in instance:modules[token].add('/'.join(instance[:instance.index(token) + 1]))
        if len(instance) == prefix and leaf.startswith('sysmem_icb_'):ports.add(leaf[len('sysmem_icb_'):])
        for key, token in (('shared', 'u_arch03_shared'), ('aon', 'u_sirv_aon')):
            if token in instance:observed[key].add('/'.join(instance[:instance.index(token) + 1]))
        roles = select(instance, leaf)
        if roles:
            row = dict(saif_name=full, section=frames[-1][0], roles=roles,
                T0_ticks=counts['T0'], T1_ticks=counts['T1'], unknown_ticks=unknown,
                reported_TX_ticks=counts['TX'], reported_TZ_ticks=None if combined else counts['TZ'],
                TC=counts['TC'], IG=counts.get('IG'), combined_TX_X_or_Z=combined,
                T0_ns=str(Decimal(counts['T0']) * scale), T1_ns=str(Decimal(counts['T1']) * scale),
                unknown_ns=str(Decimal(unknown) * scale), fully_unknown=unknown == ticks,
                conditional_records=len(conditional), conditional_entries=conditional,
                time_order_or_joint_control_relation_proved=False)
            retained_bytes[0] += len(json.dumps(row))
            require(len(selected) < LIMIT_SELECTED and retained_bytes[0] < LIMIT_OUTPUT // 2,
                    'Selected control output budget exceeded')
            selected.append(row)

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
                require(scale is None and len(node) == 3 and node[2] in units, 'Invalid timescale')
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
    return dict(activity=actual, selected_count=len(selected), selected=selected, coverage=coverage(selected, observed),
        source_read_passes=1, joint_timing_proved=False, full_control_cone_audited=False,
        system_power_verified=False, source_activity_modified=False)


def collect(inventory, inventory_sha, scope_root, output):
    identity = dependencies();scope = Path(scope_root).resolve()
    inventory = scoped(inventory, scope);inv = small(inventory, inventory_sha)
    require(inv['schema'] == 'b0-complete-saif-unknown-map-v1' and
        inv['status'] == 'complete_existing_unknown_inventory_review_required' and
        inv['tool_sha256'] == UNKNOWN_TOOL_SHA, 'Wrong frozen B0 unknown inventory')
    cases = [r for r in inv['cases'] if r['case'] == 'layer_01']
    require(len(cases) == 1, 'Need exactly one existing L01 receipt')
    report_path = scoped(inv['report'], scope);report = small(report_path, inv['report_sha256'])
    require(report['schema'] == 'systolic-b-evidence-export-v1' and
        report['netlist_sha256'] == inv['netlist_sha256'], 'B0 report/netlist identity differs')
    arun = scoped(report['activity_reference']['run'], scope)
    activity_path = arun / 'summary.json';activity_sha = report['activity_reference']['sha256']
    require(activity_sha == inv['activity_summary_sha256'], 'Activity identity differs')
    activity = small(activity_path, activity_sha)
    state_path = arun.parent / 'state.json';state_sha = sha(state_path)
    state = small(state_path, state_sha)['stages']['systolic_b_saif']
    require(state['status'] == 'passed' and state['summary_sha256'] == activity_sha and
        activity['status'] == 'B_native_saif_function_and_complete_windows_passed' and
        activity['firmware_sha256'] == report['firmware_sha256'] and
        activity['synthesis_summary_sha256'] == report['references']['synthesis']['sha256'], 'Activity not frozen passed')
    source_rows = [r for r in activity['cases'] if r['case'] == 'layer_01']
    require(len(source_rows) == 1 and source_rows[0]['activity'] == cases[0]['activity'], 'L01 audit identity differs')
    row = source_rows[0];path = scoped(arun / row['activity']['file'], scope)
    require(path.parent == arun and path.suffix == '.saif', 'Unsafe activity basename')
    output = Path(output)
    require(output.is_absolute() and output.resolve() == output and not output.exists() and output.parent.is_dir(),
            'Use fresh absolute output directory; no overwrite')
    output.mkdir(mode=0o700)
    tracked = {str(inventory): inventory_sha, str(report_path): inv['report_sha256'],
               str(activity_path): activity_sha, str(state_path): state_sha}
    request = dict(schema='b0-selected-control-residence-v1', status='collecting', case='layer_01',
        input_sha256=tracked, netlist_sha256=inv['netlist_sha256'], firmware_sha256=report['firmware_sha256'],
        saif=str(path), saif_sha256=row['activity']['sha256'], runtime_dependencies=identity,
        selection_contract=dict(shared_top=list(SHARED_TOP + SHARED_BITS), macro_required=list(MACRO_REQUIRED),
            adapter_required=list(ADAPTER_REQUIRED), aon_top_required=list(AON_REQUIRED),
            aon_name_regex=AON_CONTROL.pattern, limit_records=LIMIT_SELECTED),
        system_power_verified=False, source_activity_modified=False, no_eda_or_simulation_started=True)
    save(output / 'request.json', request);captured = []
    try:
        require(shutil.disk_usage(str(output)).free >= RESERVE + 2 * LIMIT_OUTPUT, 'Output reserve insufficient')
        result = scan(path, row['task_window'], row['activity'], captured)
        require(dependencies() == identity, 'Runtime dependency identity changed')
        require(all(sha(p) == value for p, value in tracked.items()), 'Frozen receipt changed during scan')
        require(shutil.disk_usage(str(output)).free >= RESERVE + LIMIT_OUTPUT, 'Output reserve reached')
        result.update(request)
        result['status'] = 'selected_control_residence_collected_review_required'
        save(output / 'summary.json', result)
        print('B0_SELECTED_CONTROL_COLLECTED', result['selected_count'], 'MISSING',
              len(result['coverage']['missing']), 'UNKNOWN', result['coverage']['selected_unknown_records'],
              'SUMMARY_SHA', sha(output / 'summary.json'), flush=True)
        return result
    except Exception as error:
        request.update(status='failed', error=str(error), retained_selected_count=len(captured))
        save(output / 'failure.json', request)
        if captured:save(output / 'partial_selected.json', dict(unqualified=True, selected=captured))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inventory', type=Path, required=True)
    parser.add_argument('--inventory-sha256', required=True)
    parser.add_argument('--scope-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    collect(args.inventory, args.inventory_sha256, args.scope_root, args.output)
