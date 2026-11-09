"""Read-only inventory of all mapped unused/unconnected port warnings.

Bind to the original synthesis receipt. Locate each warned bit in the actual
mapped module and count its uses after removing headers and declarations.
This explains retained unused interface bits; it never approves timing itself.
Python 3.6 standard library, no EDA process or source/netlist mutation.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def modules(text):
    text = re.sub(r'/\*.*?\*/|\(\*.*?\*\)|//[^\n]*', '', text, flags=re.S)
    pattern = r'(?ms)^\s*module\s+(\S+)\s*\((.*?)\);(.*?)^\s*endmodule\b'
    declarations = re.compile(r'(?m)^\s*(input|output|inout)\s+([^;]+);')
    result = {}
    for match in re.finditer(pattern, text):
        name, header, body = match.groups(); ports = {}
        require(name not in result, 'Duplicate mapped module')
        require(not re.search(r'\b(input|output|inout)\b', header), 'ANSI module requires separate parser review')
        for direction, raw in declarations.findall(body):
            raw = re.sub(r'^(?:(?:wire|reg|signed)\s+)+', '', raw.strip())
            width = re.match(r'\[\s*(\d+)\s*:\s*(\d+)\s*\]\s*', raw)
            bounds = [int(x) for x in width.groups()] if width else None
            if width: raw = raw[width.end():]
            for token in raw.split(','):
                token = token.strip()
                require(re.fullmatch(r'[A-Za-z_$][A-Za-z_0-9$]*', token), 'Unreviewed mapped port identifier')
                require(token not in ports, 'Duplicate port declaration')
                ports[token] = dict(direction=direction, bounds=bounds)
        header_ports = [x.strip() for x in header.split(',')]
        require(ports and set(header_ports) == set(ports) and len(header_ports) == len(ports),
                'Mapped header/declarations disagree')
        logic = declarations.sub('', body)
        net_decl = re.compile(r'(?m)^\s*(?:wire|reg)\s+[^;]+;')
        require(all('=' not in x.group(0) for x in net_decl.finditer(logic)), 'Net declaration initializer requires review')
        logic = net_decl.sub('', logic)
        result[name] = dict(ports=ports, logic=logic)
    require(len(result) == len(re.findall(r'(?m)^\s*module\b', text)) and result, 'Unparsed mapped modules')
    return result


def uses(module, port):
    bit = None; base = port
    if port not in module['ports']:
        match = re.fullmatch(r'([A-Za-z_$][A-Za-z_0-9$]*)\[(\d+)\]', port)
        require(match is not None, 'Unreviewed warning port syntax')
        base, bit = match.group(1), int(match.group(2))
    require(base in module['ports'], 'Warned port absent from mapped module')
    spec = module['ports'][base]; bounds = spec['bounds']
    if bit is not None: require(bounds and min(bounds) <= bit <= max(bounds), 'Warned bit outside declared port')
    count = 0
    pattern = r'(?<![A-Za-z_0-9$\\.])'+re.escape(base)+r'(?![A-Za-z_0-9$])'
    for match in re.finditer(pattern, module['logic']):
        tail = module['logic'][match.end():]
        select = re.match(r'\s*\[\s*(\d+)\s*(?::\s*(\d+)\s*)?\]', tail)
        if bit is not None and select:
            lo = int(select.group(1)); hi = int(select.group(2)) if select.group(2) else lo
            if not min(lo, hi) <= bit <= max(lo, hi): continue
        count += 1
    return dict(direction=spec['direction'], declared_bounds=bounds, expression_occurrences=count,
                disposition='declaration_only' if count == 0 else 'expression_present_requires_review')


def classify(report, netlist):
    mapped = modules(netlist); counts = Counter(); rows = []
    warning = re.compile(r"^Warning: In design '([^']+)', (input )?port '([^']+)' (is not connected to any nets|is unloaded)\. \((LINT-(?:8|28))\)$")
    for line in report.splitlines():
        if not line.startswith('Warning:'): continue
        code = re.findall(r'\((LINT-[0-9]+)\)', line)
        require(len(code) == 1, 'Unparsed structural warning code')
        counts[code[0]] += 1
        if code[0] not in ('LINT-8', 'LINT-28'): continue
        match = warning.fullmatch(line); require(match is not None, 'Unparsed unused/unconnected port warning')
        design, input_word, port, reason, kind = match.groups()
        require(design in mapped, 'Warned design absent from mapped netlist')
        row = dict(design=design, port=port, warning=kind, reason=reason, **uses(mapped[design], port))
        if input_word: require(row['direction'] == 'input', 'Warning/input direction differs')
        rows.append(row)
    require(len(rows) == counts['LINT-8']+counts['LINT-28'] and rows, 'Incomplete warned-port inventory')
    require(len({(r['warning'], r['design'], r['port']) for r in rows}) == len(rows), 'Duplicate warned port')
    return dict(module_count=len(mapped), warning_counts=dict(counts), port_warning_count=len(rows),
                direction_counts=dict(Counter(r['direction'] for r in rows)),
                disposition_counts=dict(Counter(r['disposition'] for r in rows)), ports=rows)


def audit(run, expected):
    run = Path(run).resolve(); source = run/'summary.json'
    require(re.fullmatch('[a-f0-9]{64}', expected) and sha(source) == expected, 'Synthesis summary digest mismatch')
    summary = json.loads(source.read_text()); state = json.loads((run.parent/'state.json').read_text())['stages']['dma16_synth']
    require(state['status'] == 'passed' and state['summary_sha256'] == expected and
            summary['scope'] == 'dma16_whole_soc_task_mode_preliminary_synthesis', 'Not a passed DMA16 synthesis collection')
    tracked = {source: expected}
    for name in ('mapped.v', 'check_design_mapped.rpt'):
        digest = summary['artifacts'][name]; require(sha(run/name) == digest, 'Frozen structural artifact changed')
        tracked[run/name] = digest
    result = classify((run/'check_design_mapped.rpt').read_text(), (run/'mapped.v').read_text())
    require(all(sha(p) == h for p, h in tracked.items()), 'Structural input changed during read')
    result.update(schema='dma16_mapped_port_diagnostic_v1', synthesis_run=str(run), synthesis_summary_sha256=expected,
                  inputs_sha256={str(p): h for p, h in tracked.items()}, auditor_sha256=sha(__file__),
                  timing_verified=False, netlist_modified=False,
                  review='Declaration-only ports have no mapped logic references. Other warning classes and any expression occurrences still require object review.')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--synth-run', type=Path, required=True)
    parser.add_argument('--summary-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); require(not args.output.exists(), 'Use a new diagnostic output')
    result = audit(args.synth_run, args.summary_sha256)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x', encoding='utf8') as stream: json.dump(result, stream, indent=2, allow_nan=False)
    print('MAPPED_PORT_DIAGNOSTIC_READY timing_verified=false', result['port_warning_count'], result['disposition_counts'])
