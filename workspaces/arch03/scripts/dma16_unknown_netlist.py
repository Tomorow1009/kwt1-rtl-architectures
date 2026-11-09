"""Join every frozen unknown VCD identifier to the actual mapped hierarchy.

This is a conservative structural inventory, not an X waiver or power approval.
Only aliases declared in mapped modules with zero expression references can be
called declaration-only. Model internals, unresolved names, and referenced bits
remain explicit review items. No VCD is rewritten or rescanned. Python 3.6.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import re
from dma16_structural_audit import modules, require, sha
from dma16_unknown_activity import validate

IDENT = r'(?:\\[^\s]+|[A-Za-z_$][A-Za-z_0-9$]*)'
ROOT = 'tb_top.u_e203_soc_top'


def index_netlist(text):
    mapped = modules(text)
    clean = re.sub(r'/\*.*?\*/|\(\*.*?\*\)|//[^\n]*', '', text, flags=re.S)
    block = r'(?ms)^\s*module\s+(\S+)\s*\((.*?)\);(.*?)^\s*endmodule\b'
    declaration = re.compile(r'(?m)^\s*(input|output|inout|wire|reg)\s+([^;]+);')
    for match in re.finditer(block, clean):
        name, _, body = match.groups(); module = mapped[name]; nets = {}
        for kind, raw in declaration.findall(body):
            raw = re.sub(r'^(?:(?:wire|reg|signed)\s+)+', '', raw.strip())
            require('=' not in raw, 'Initialized net declaration requires review')
            width = re.match(r'\[\s*(\d+)\s*:\s*(\d+)\s*\]\s*', raw)
            bounds = tuple(int(x) for x in width.groups()) if width else None
            if width: raw = raw[width.end():]
            for token in raw.split(','):
                token = token.strip()
                require(re.fullmatch(IDENT, token), 'Unsupported mapped net declaration')
                token = token.lstrip('\\')
                require(token not in nets or nets[token] == bounds, 'Conflicting net bounds')
                nets[token] = bounds
        logic = module['logic']
        require(not re.search(r'\b(always|initial|generate|function|task)\b', logic),
                'Nonstructural mapped logic requires separate review')
        instances = {}
        for ref, inst in re.findall(r'(?m)^\s*('+IDENT+r')\s+('+IDENT+r')\s*\(', logic):
            ref, inst = ref.lstrip('\\'), inst.lstrip('\\')
            require(inst not in instances, 'Duplicate mapped instance')
            instances[inst] = ref
        # Remove named pin LABELS, never their expressions. Everything else
        # counts conservatively, including an unrecognized variable select.
        expressions = re.sub(r'\.\s*'+IDENT+r'\s*\(', '(', logic)
        uses = {}
        pattern = r'(?<![A-Za-z_0-9$\\.])('+IDENT+r')(\s*\[\s*([^\]]+)\])?'
        for token in re.finditer(pattern, expressions):
            net = token.group(1).lstrip('\\')
            if net not in nets: continue
            select = token.group(3); span = None
            if select is not None:
                constant = re.fullmatch(r'\s*(\d+)\s*(?::\s*(\d+)\s*)?', select)
                if constant:
                    lo = int(constant.group(1)); hi = int(constant.group(2) or constant.group(1))
                    span = (min(lo, hi), max(lo, hi))
                else:
                    # The index expression itself can consume another net.
                    # Treat every such net as a whole-vector use; do not drop
                    # it merely because the outer token consumed the brackets.
                    for index_name in re.findall(IDENT, select):
                        index_name = index_name.lstrip('\\')
                        if index_name in nets:
                            uses.setdefault(index_name, []).append(None)
            uses.setdefault(net, []).append(span)
        module.update(nets=nets, instances=instances, net_uses=uses)
    require('e203_soc_top' in mapped, 'Missing actual mapped top')
    scopes, external = {}, {}

    def visit(path, name, ancestors):
        require(name not in ancestors, 'Recursive mapped hierarchy')
        require(path not in scopes and path not in external, 'Ambiguous mapped hierarchy')
        if name not in mapped:
            external[path] = name; return
        scopes[path] = name
        for inst, ref in mapped[name]['instances'].items():
            visit(path+'.'+inst, ref, ancestors+(name,))

    visit(ROOT, 'e203_soc_top', ())
    return dict(modules=mapped, scopes=scopes, external=external)


def resolve_alias(alias, index):
    require(alias.startswith(ROOT+'.'), 'Unknown alias outside actual DUT')
    path, sep, signal = alias.rpartition('.')
    while sep:
        if path in index['external']:
            return dict(disposition='external_model_internal_requires_review',
                        scope=path, reference=index['external'][path], signal=signal)
        if path in index['scopes']:
            reference = index['scopes'][path]; module = index['modules'][reference]
            net = signal.strip(); selected = None
            # VCD separates a declared vector's select from its identifier by
            # whitespace. Escaped scalar names may themselves contain [n].
            match = re.fullmatch(r'(.*?)\s+\[(\d+)(?::(\d+))?\]', net)
            if match:
                net = match.group(1); lo = int(match.group(2)); hi = int(match.group(3) or match.group(2))
                selected = (min(lo, hi), max(lo, hi))
            net = net.lstrip('\\')
            if net not in module['nets']:
                return dict(disposition='unresolved_mapped_signal_requires_review', scope=path,
                            reference=reference, signal=signal)
            bounds = module['nets'][net]
            if selected is not None:
                require(bounds and min(bounds) <= selected[0] <= selected[1] <= max(bounds),
                        'VCD select outside mapped declaration')
            occurrences = sum(1 for span in module['net_uses'].get(net, []) if
                selected is None or span is None or max(span[0], selected[0]) <= min(span[1], selected[1]))
            return dict(disposition='mapped_expression_requires_time_review' if occurrences else 'mapped_declaration_only',
                        scope=path, reference=reference, signal=signal, expression_occurrences=occurrences,
                        declared_bounds=bounds, selected_bits=selected)
        signal = path.rpartition('.')[2]+'.'+signal
        path, sep, _ = path.rpartition('.')
    return dict(disposition='unresolved_hierarchy_requires_review', signal=alias)


def classify(scanned, index):
    rows = []; counts = Counter(); aliases = Counter(); roles = {}; seen = set()
    for signal in scanned['signals']:
        code = signal['identifier']; require(code not in seen, 'Duplicate unknown identifier'); seen.add(code)
        details = [dict(alias=a, **resolve_alias(a, index)) for a in signal['aliases']]
        require(details, 'Unknown identifier lacks aliases')
        kinds = {r['disposition'] for r in details}
        if kinds == {'mapped_declaration_only'}:
            disposition = 'all_aliases_mapped_declaration_only'
        elif 'mapped_expression_requires_time_review' in kinds:
            disposition = 'mapped_expression_requires_time_review'
        else:
            disposition = 'model_or_unresolved_alias_requires_review'
        counts[disposition] += 1
        aliases.update(r['disposition'] for r in details)
        first = min(signal['aliases'], key=lambda x: (len(x), x))
        scope = re.sub(r'\[\d+\]', '[]', first.rsplit('.', 1)[0])
        stats = roles.setdefault(scope, dict(identifiers=0, unknown_records=0,
            unknown_records_after_begin=0, unknown_at_end=0, missing_initial=0))
        stats['identifiers'] += 1; stats['unknown_records'] += signal['unknown_records']
        stats['unknown_records_after_begin'] += signal['unknown_records_after_begin']
        stats['unknown_at_end'] += bool(signal['unknown_at_end'])
        stats['missing_initial'] += bool(signal['unobserved_prefix_ticks'])
        rows.append(dict(identifier=code, disposition=disposition, aliases=details,
            unknown_records=signal['unknown_records'], any_unknown_ticks=signal['any_unknown_ticks'],
            unknown_at_end=signal['unknown_at_end'], unobserved_prefix_ticks=signal['unobserved_prefix_ticks']))
    require(sum(counts.values()) == len(scanned['signals']), 'Incomplete unknown coverage')
    return dict(identifier_count=len(rows), disposition_counts=dict(counts), alias_disposition_counts=dict(aliases),
                canonical_scope_counts=roles, identifiers=rows, system_power_verified=False,
                note='Every alias is retained. No data-valid or time exemption is inferred from names. Declaration-only means no mapped expression use; external model internals remain separate. X duration is not a power bound.')


def audit(unknown, expected_unknown, synth, expected_synth):
    from dma16_report import load_stage
    unknown, synth = Path(unknown).resolve(), Path(synth).resolve()
    u = load_stage(dict(run=str(unknown), sha256=expected_unknown), 'dma16_unknown_activity')
    s = load_stage(dict(run=str(synth), sha256=expected_synth), 'dma16_synth')
    require(u['complete_stream_scanned'] is True and u['waveform_modified'] is False and
            u['synthesis_summary_sha256'] == expected_synth and
            s['scope'] == 'dma16_whole_soc_task_mode_preliminary_synthesis', 'Unknown and mapped design identity differ')
    scan = unknown/'unknown_full_scan.json'; netlist = synth/'mapped.v'
    tracked = {str(scan): u['artifacts'][scan.name], str(netlist): s['artifacts'][netlist.name],
               str(unknown/'summary.json'): expected_unknown, str(synth/'summary.json'): expected_synth}
    require(all(sha(p) == h for p, h in tracked.items()), 'Changed structural input')
    data = json.loads(scan.read_text()); validate(data, u['original_activity'])
    index = index_netlist(netlist.read_text()); result = classify(data, index)
    require(all(sha(p) == h for p, h in tracked.items()), 'Input changed during classification')
    result.update(schema='dma16_unknown_mapped_inventory_v1', inputs_sha256=tracked,
        auditor_sha256=sha(__file__), unknown_summary_sha256=expected_unknown,
        synthesis_summary_sha256=expected_synth, mapped_module_count=len(index['modules']),
        mapped_scope_count=len(index['scopes']), external_leaf_count=len(index['external']),
        waveform_modified=False, netlist_modified=False)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--unknown-run', type=Path, required=True)
    parser.add_argument('--unknown-summary-sha256', required=True)
    parser.add_argument('--synth-run', type=Path, required=True)
    parser.add_argument('--synth-summary-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); require(not args.output.exists(), 'Use a new structural output')
    result = audit(args.unknown_run, args.unknown_summary_sha256, args.synth_run, args.synth_summary_sha256)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x', encoding='utf8') as stream: json.dump(result, stream, indent=2, allow_nan=False)
    print('UNKNOWN_MAPPED_INVENTORY_REVIEW_REQUIRED', result['identifier_count'], result['disposition_counts'])
