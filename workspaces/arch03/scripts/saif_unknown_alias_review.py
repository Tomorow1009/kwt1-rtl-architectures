"""Resolve SAIF names omitted by DDC through simple mapped wire assignments.

Read-only evidence classification. An absent declaration or exported dummy net
does not exempt the internal power of its driver. No power acceptance is given.
"""
import argparse
from collections import Counter, defaultdict
import gzip
import hashlib
import json
from pathlib import Path
import re

from dma16_structural_audit import modules, require

IDENT = r'(?:\\[^\s]+|[A-Za-z_$][A-Za-z_0-9$]*)'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def wire(text):
    text = text.strip()
    match = re.fullmatch('(' + IDENT + r')\s*(?:\[\s*(\d+)\s*\])?', text)
    if not match:
        return None
    return match.group(1).lstrip('\\') + (
        '[' + match.group(2) + ']' if match.group(2) is not None else '')


def graph(logic):
    edges = defaultdict(set)
    for lhs, rhs in re.findall(r'\bassign\s+([^;=]+)=([^;]+);', logic):
        a, b = wire(lhs), wire(rhs)
        if a is not None and b is not None:
            edges[a].add(b)
            edges[b].add(a)
    return edges


def aliases(start, edges):
    seen, pending = set(), [start]
    while pending:
        item = pending.pop()
        if item in seen:
            continue
        seen.add(item)
        pending.extend(edges.get(item, ()))
    return seen


def audit(summary, digest):
    summary = Path(summary)
    require(sha(summary) == digest, 'Linked summary changed')
    linked = json.loads(summary.read_text())
    directory = summary.parent
    proof = directory / 'unknown_connections.tsv'
    require(sha(proof) == linked['proof_sha256'], 'Linked proof changed')
    unresolved = set(linked['unresolved'])
    resolved = {line.split('\t')[1] for line in proof.read_text().splitlines()
                if line.startswith('net\t')}
    mapped_paths = [p for p in linked['input_files'] if p.endswith('/mapped.v')]
    require(len(mapped_paths) == 1, 'Ambiguous mapped netlist')
    mapped_path = Path(mapped_paths[0])
    require(sha(mapped_path) == linked['input_files'][str(mapped_path)], 'Mapped netlist changed')
    mapped = modules(mapped_path.read_text())
    selected, inputs = {}, {str(summary): digest, str(proof): linked['proof_sha256'],
                           str(mapped_path): linked['input_files'][str(mapped_path)]}
    for filename, expected in linked['input_files'].items():
        if not filename.endswith('.jsonl.gz'):
            continue
        require(sha(filename) == expected, 'Unknown list changed')
        inputs[filename] = expected
        with gzip.open(filename, 'rt') as stream:
            for line in stream:
                row = json.loads(line)
                key = row['saif_name'].split('tb_top/u_e203_soc_top/', 1)[1]
                if key not in unresolved:
                    continue
                item = row['mapping']
                require(key not in selected or selected[key] == item, 'Mapping changes between layers')
                selected[key] = item
    require(set(selected) == unresolved, 'Missing unresolved names')
    graphs, rows = {}, []
    for name, info in sorted(selected.items()):
        ref = info['reference']
        require(ref in mapped, 'Missing mapped module')
        if ref not in graphs:
            graphs[ref] = graph(mapped[ref]['logic'])
        leaf = wire(info['signal'])
        require(leaf is not None, 'Unsupported selected signal')
        prefix = name.rsplit('/', 1)[0] + '/'
        candidates = sorted(prefix + item for item in aliases(leaf, graphs[ref])
                            if prefix + item in resolved)
        if candidates:
            disposition = 'simple_wire_alias_to_linked_net'
        elif info['expression_occurrences'] == 0:
            disposition = 'absent_DDC_net_and_no_local_expression'
        elif leaf.startswith('SYNOPSYS_UNCONNECTED') and info['expression_occurrences'] == 1:
            disposition = 'exported_dummy_absent_DDC_net_driver_power_not_exempt'
        else:
            disposition = 'requires_further_review'
        rows.append(dict(name=name, reference=ref, disposition=disposition,
                         alias_targets=candidates,
                         local_expression_occurrences=info['expression_occurrences']))
    require(all(sha(p) == expected for p, expected in inputs.items()), 'Input changed during review')
    return dict(schema='saif-unknown-alias-review-v1', name=linked['name'],
                inputs_sha256=inputs, source_sha256=sha(__file__), rows=rows,
                counts=dict(Counter(row['disposition'] for row in rows)),
                complete_target_count=len(rows), system_power_verified=False,
                driver_internal_power_exempted=False, activity_modified=False,
                note='Only simple wire equivalences are followed. Absent declarations are not a global leaf-power waiver.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--summary', type=Path, required=True)
    parser.add_argument('--sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    require(not args.output.exists(), 'Preserve prior review')
    result = audit(args.summary, args.sha256)
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
    print('ALIASES_REVIEWED', result['name'], result['counts'], sha(args.output))
