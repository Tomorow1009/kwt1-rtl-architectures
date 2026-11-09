"""Extract actual PT numerical reports; never grant system power acceptance.

Format checked against installed T-2022.03-SP5-1 report_units/report_power.
Power units are in report_power -verbose, not report_units. Only the observed
explicit 1-W dynamic AND leakage units are accepted. Other
unit settings need a reviewed conversion, not an inferred multiplier.
"""
import argparse
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import struct
from dma16_power import POWER_SCOPE, validate_activity

NUMBER = r'(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?'
# The frozen runner requests nine significant digits. A low-precision integer
# zero must not acquire a half-watt rounding allowance and hide a bad total.
POWER_NUMBER = r'[0-9]\.[0-9]{8}[eE][+-][0-9]{2,3}'
GROUPS = ('clock_network', 'register', 'combinational', 'sequential', 'memory', 'io_pad', 'black_box')
LABELS = {'Net Switching Power': 'switching', 'Cell Internal Power': 'internal',
          'Cell Leakage Power': 'leakage', 'Total Power': 'total'}
KEYS = ('internal', 'switching', 'leakage', 'total')
MODULES = {'cpu_including_tcm': 'u_e203_cpu_top', 'itcm': 'u_e203_itcm_ram',
           'dtcm': 'u_e203_dtcm_ram', 'accelerator': 'u_arch03_accel',
           'shared': 'u_arch03_shared', 'dma_arbiter': 'u_arch03_arb', 'dma_router': 'u_arch03_router'}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(4*1024*1024), b''): digest.update(chunk)
    return digest.hexdigest()


def number(token):
    require(re.fullmatch(NUMBER, token) is not None, 'Nonfinite/negative/invalid power number')
    value = Decimal(token)
    require(value.is_finite() and value >= 0, 'Invalid power value')
    return value


def rounding(token):
    # The last displayed decimal digit gives an explicit half-unit bound.
    value = number(token)
    return Decimal(0) if value == 0 else Decimal('0.5')*Decimal(10)**value.as_tuple().exponent


def observed_binary32_rounding(token):
    # Actual nine-digit PT cell values round-trip exactly as IEEE binary32.
    # Only those observed representations qualify for a half-ULP allowance;
    # this is not a general relative tolerance or a power-model accuracy claim.
    raw = struct.pack('>f', float(number(token)))
    value = struct.unpack('>f', raw)[0]
    require(format(value, '.8e') == token.lower(), 'Value is not an observed binary32 representation')
    bits = struct.unpack('>I', raw)[0]
    require(bits < 0x7f7fffff, 'Nonfinite/overflowing binary32 power')
    next_value = struct.unpack('>f', struct.pack('>I', bits+1))[0]
    return (Decimal.from_float(next_value)-Decimal.from_float(value))/2


def check_sum(terms, total, context):
    error = abs(sum(number(x) for x in terms)-number(total))
    bound = sum(rounding(x) for x in terms)+rounding(total); basis = 'decimal_display_rounding'
    if error > bound:
        try: bound += sum(observed_binary32_rounding(x) for x in terms+[total])
        except (ValueError, OverflowError, struct.error):
            raise ValueError('Power sum mismatch: '+context)
        basis = 'decimal_display_plus_exact_binary32_roundtrip_half_ulp'
    require(error <= bound, 'Power sum mismatch: '+context)
    return dict(residual_w=str(error), bound_w=str(bound), numerical_basis=basis)


def parse_units(text):
    values = {}
    for line in text.splitlines():
        if re.match(r'\s*(?:Dynamic|Leakage) Power Units\b', line):
            match = re.fullmatch(r'\s*(Dynamic|Leakage) Power Units\s*=\s*('+NUMBER+r')\s+W\s*', line)
            require(match is not None and match.group(1) not in values, 'Unknown/duplicate PT power units')
            require(number(match.group(2)) == 1, 'PT power unit scale changed; review conversion')
            values[match.group(1)] = '1 Watt'
    require(set(values) == {'Dynamic', 'Leakage'}, 'Missing explicit dynamic/leakage power units')
    return values


def parse_base_units(text):
    require(re.search(r'(?m)^\s*Report\s*:\s*units\s*$', text) and
            re.search(r'(?m)^\s*Design\s*:\s*e203_soc_top\s*$', text), 'Not the actual whole-SoC report_units')
    wanted = {'Capacitive_load_unit': (Decimal('1e-12'), 'Farad'),
              'Time_unit': (Decimal('1e-9'), 'Second'), 'Voltage_unit': (Decimal(1), 'Volt')}
    result = {}
    for key, (expected, unit) in wanted.items():
        matches = re.findall(r'(?m)^\s*'+key+r'\s*:\s*('+NUMBER+r')\s+(\S+)\s*$', text)
        require(len(matches) == 1 and number(matches[0][0]) == expected and matches[0][1] == unit,
                'Missing/changed report_units field '+key)
        result[key] = matches[0][0]+' '+unit
    return result


def parse_power(units, text):
    unit_values = parse_units(units)
    require(re.search(r'(?m)^\s*Report\s*:\s*Averaged Power\s*$', text), 'Not the reviewed averaged-power report')
    require(re.search(r'(?m)^\s*Design\s*:\s*e203_soc_top\s*$', text), 'Not whole-SoC power')
    totals = {}; groups = {}
    row_pattern = (r'^\s*('+'|'.join(GROUPS)+r')\s+'+r'\s+'.join(['('+POWER_NUMBER+')']*4)+
                   r'\s+\(\s*'+NUMBER+r'%\s*\)\s*([iu]*)\s*$')
    for line in text.splitlines():
        label = next((key for key in LABELS if re.match(r'\s*'+re.escape(key)+r'\s*=', line)), None)
        if label is not None:
            match = re.fullmatch(r'\s*'+re.escape(label)+r'\s*=\s*('+POWER_NUMBER+r')\s*\(\s*'+NUMBER+r'%\s*\)\s*', line)
            key = LABELS[label]
            require(match is not None and key not in totals, 'Missing/duplicate/invalid PT total '+label)
            totals[key] = match.group(1)
        if re.match(r'\s*(?:'+'|'.join(GROUPS)+r')\s', line):
            match = re.fullmatch(row_pattern, line)
            require(match is not None and match.group(1) not in groups, 'Invalid/duplicate PT power group')
            groups[match.group(1)] = dict(zip(('internal', 'switching', 'leakage', 'total'), match.groups()[1:5]))
        elif re.match(r'\s*[A-Za-z_][A-Za-z_0-9]*\s+'+POWER_NUMBER+r'\s+'+POWER_NUMBER, line):
            raise ValueError('Unreviewed PT power group')
    require(set(totals) == set(LABELS.values()) and set(groups) == set(GROUPS), 'Incomplete PT power table/totals')
    checks = {}
    for name, row in groups.items(): checks['group_'+name] = check_sum([row[k] for k in ('internal', 'switching', 'leakage')], row['total'], name)
    for key in totals: checks['column_'+key] = check_sum([groups[name][key] for name in GROUPS], totals[key], 'all groups '+key)
    checks['whole_soc'] = check_sum([totals[k] for k in ('internal', 'switching', 'leakage')], totals['total'], 'whole SoC')
    return dict(units=unit_values, reported_power_w=totals, reported_group_power_w=groups,
                numerical_sum_checks=checks,
                derived_dynamic_w=str(number(totals['internal'])+number(totals['switching'])),
                note='Strings preserve reported decimal precision; grouping is PT taxonomy, not overlapping module hierarchy.')


def hierarchy_rounding(token):
    # Installed PT hierarchy output uses three significant digits even with
    # -significant_digits 8. Exact zero prints 0.000; small nonzero values use
    # scientific notation, so zero does not mean +/-0.0005 W.
    require(token == '0.000' or re.fullmatch(r'(?:[1-9]\.[0-9]{2}|-[1-9]\.[0-9]{1,2})e[+-][0-9]{2,3}', token),
            'Unreviewed PT hierarchy numerical format')
    return Decimal(0) if token == '0.000' else Decimal('0.5')*Decimal(10)**Decimal(token).as_tuple().exponent


def hierarchy_value(key, token):
    # Actual PT reports contain signed internal contributions for two clock
    # gate rows. Preserve them for model review; never drop or clamp them.
    if key == 'internal':
        require(re.fullmatch('-?'+NUMBER, token), 'Invalid signed internal contribution')
        return Decimal(token)
    return number(token)


def parse_hierarchy(text, totals):
    require(re.search(r'(?m)^\s*Report\s*:\s*Averaged Power\s*$', text) and
            re.search(r'(?m)^\s*Design\s*:\s*e203_soc_top\s*$', text) and
            re.search(r'(?m)^Hierarchy\s+Power\s+Power\s+Power\s+Power\s+%\s*$', text),
            'Unreviewed hierarchy header or design')
    row_pattern = (r'^( *)(\S+)(?: \(([^()\s]+)\))?\s+(-?'+NUMBER+r')\s+'+
                   r'\s+'.join(['('+NUMBER+')']*4)+r'\s*$')
    stack = []; rows = {}; selected = {}; begun = False; negative_internal = []
    for line in text.splitlines():
        match = re.fullmatch(row_pattern, line)
        if match is None:
            require(not begun or not line.strip() or re.fullmatch(r'[- ]+|1', line),
                    'Unparsed hierarchy row')
            continue
        indent, name, reference = match.groups()[:3]; depth = len(indent)
        while stack and stack[-1][0] >= depth: stack.pop()
        require((not rows and name == 'e203_soc_top' and depth == 0 and reference is None) or
                (bool(stack) and reference is not None), 'Broken hierarchy root/indentation')
        path = stack[-1][1]+'/'+name if stack else name
        require(path not in rows, 'Duplicate hierarchy path')
        values = dict(zip(KEYS, match.groups()[3:7]))
        errors = {k: hierarchy_rounding(v) for k, v in values.items()}
        require(number(match.group(8)) <= 100, 'Invalid hierarchy percentage')
        require(abs(sum(hierarchy_value(k, values[k]) for k in KEYS[:3])-number(values['total'])) <= sum(errors.values()),
                'Hierarchy row power sum mismatch')
        if hierarchy_value('internal', values['internal']) < 0:
            negative_internal.append(dict(path=path, reported_internal_w=values['internal']))
        rows[path] = dict(path=path, reported_power_w=values, rounding_bound_w={k: str(v) for k, v in errors.items()})
        for role, token in MODULES.items():
            if name == token:
                require(role not in selected, 'Ambiguous power module '+role)
                selected[role] = rows[path]
        stack.append((depth, path)); begun = True
    require(set(selected) == set(MODULES), 'Missing DMA16 hierarchy modules')
    root = rows['e203_soc_top']
    for key in KEYS:
        require(abs(hierarchy_value(key, root['reported_power_w'][key])-number(totals[key])) <=
                number(root['rounding_bound_w'][key])+rounding(totals[key]), 'Hierarchy/root total differs')
    cpu = selected['cpu_including_tcm']['path']
    require(all(selected[k]['path'].startswith(cpu+'/') for k in ('itcm', 'dtcm')), 'TCM ownership changed')
    outer = ['cpu_including_tcm', 'accelerator', 'shared', 'dma_arbiter', 'dma_router']
    for i, role in enumerate(outer):
        for other in outer[i+1:]:
            a, b = selected[role]['path'], selected[other]['path']
            require(not a.startswith(b+'/') and not b.startswith(a+'/'), 'Overlapping power module subtrees')
    a, b = selected['itcm']['path'], selected['dtcm']['path']
    require(not a.startswith(b+'/') and not b.startswith(a+'/'), 'Overlapping TCM subtrees')

    def difference(base, subtract):
        values = {}; errors = {}
        for key in KEYS:
            value = hierarchy_value(key, base['reported_power_w'][key])-sum(hierarchy_value(key, x['reported_power_w'][key]) for x in subtract)
            require(key == 'internal' or value >= 0, 'Negative rounded power residual; review actual report')
            values[key] = str(value)
            errors[key] = str(number(base['rounding_bound_w'][key])+sum(number(x['rounding_bound_w'][key]) for x in subtract))
        return dict(derived_power_w=values, rounding_bound_w=errors)

    modules = {k: dict(derived_power_w=v['reported_power_w'], rounding_bound_w=v['rounding_bound_w'], path=v['path'])
               for k, v in selected.items() if k != 'cpu_including_tcm'}
    modules['cpu_excluding_tcm'] = difference(selected['cpu_including_tcm'], [selected[k] for k in ('itcm', 'dtcm')])
    accurate_root = dict(reported_power_w=totals, rounding_bound_w={k: str(rounding(v)) for k, v in totals.items()})
    modules['platform_other'] = difference(accurate_root, [selected[k] for k in outer])
    for row in modules.values():
        row['derived_dynamic_w'] = str(sum(hierarchy_value(k, row['derived_power_w'][k]) for k in KEYS[:2]))
        row['dynamic_rounding_bound_w'] = str(sum(number(row['rounding_bound_w'][k]) for k in KEYS[:2]))
    for key in KEYS:
        require(sum(hierarchy_value(key, v['derived_power_w'][key]) for v in modules.values()) == number(totals[key]),
                'Disjoint power sum mismatch')
    return dict(modules=modules, inclusive_module_rows=selected, hierarchy_rows=len(rows),
                negative_internal_rows=negative_internal,
                note='Rounded PT hierarchy values; CPU excludes its full ITCM/DTCM wrappers. Remaining platform is a residual. Bounds include print rounding only, not model uncertainty.')


def parse_sram(text, profile='dma16'):
    require(profile in ('dma16', 'mmio8_source'), 'Unknown SRAM power inventory profile')
    require(re.search(r'(?m)^\s*Design\s*:\s*e203_soc_top\s*$', text) and '-cell_power' in text,
            'Not the complete SoC SRAM cell report')
    pattern = (r'^\s*(\S+)\s+'+r'\s+'.join(['('+POWER_NUMBER+')']*4)+
               r'\s+\(\s*'+NUMBER+r'%\s*\)\s*([abcdh]*)\s*$')
    cells = {}; counts = {}; sums = {}
    tokens = {'u_e203_itcm_gnrl_ram': 'itcm', 'u_e203_dtcm_gnrl_ram': 'dtcm',
              'u_arch03_accel': 'accelerator', 'u_arch03_shared': 'shared'}
    for line in text.splitlines():
        match = re.fullmatch(pattern, line)
        if match is None:
            require(not re.match(r'\s*\S+/\S*\s+', line), 'Unparsed SRAM cell row')
            continue
        path = match.group(1); roles = [v for k, v in tokens.items() if k in path.split('/')[:-1]]
        require(path not in cells and len(roles) == 1, 'Ambiguous/duplicate SRAM ownership')
        # Attribute b explicitly denotes an unresolved black box.
        require('b' not in match.group(6) and 'h' not in match.group(6), 'SRAM is unresolved or hierarchical')
        values = dict(zip(KEYS, match.groups()[1:5])); role = roles[0]
        check = check_sum([values[k] for k in KEYS[:3]], values['total'], 'SRAM cell '+path)
        cells[path] = dict(owner=role, reported_power_w=values, attributes=match.group(6), numerical_sum_check=check)
        counts[role] = counts.get(role, 0)+1
        for key in KEYS: sums[(role, key)] = sums.get((role, key), Decimal(0))+number(values[key])
    expected = {'itcm': 32, 'dtcm': 32, 'shared': 64, 'accelerator': 34 if profile == 'dma16' else 10}
    require(counts == expected, 'Incomplete '+profile+' SRAM cell coverage')
    return dict(cell_count=len(cells), counts=counts, cells=cells,
                summed_cell_power_w={role: {key: str(sums[(role, key)]) for key in KEYS} for role in counts},
                note='SRAM is already included in module/system totals; never add this separate breakdown again. Cell models and activity still require review.')


def extract(run, expected):
    run = Path(run).resolve(); summary = run/'summary.json'
    require(re.fullmatch('[a-f0-9]{64}', expected) and sha(summary) == expected, 'Power summary digest mismatch')
    report = json.loads(summary.read_text())
    state = json.loads((run.parent/'state.json').read_text())['stages']['dma16_power']
    require(state['status'] == 'passed' and state['summary_sha256'] == expected and
            report.get('scope') == POWER_SCOPE and report.get('status') == 'reports_ready_review_required',
            'Need an actual completed DMA16 PT report collection')
    require({'units.rpt', 'power_verbose.rpt', 'power.rpt', 'power.log', 'power_hierarchy.rpt', 'power_sram.rpt'} <= set(report['artifacts']), 'Missing numerical power artifacts')
    texts = {}
    for name, digest in report['artifacts'].items():
        require(Path(name).name == name and sha(run/name) == digest, 'Changed/unsafe power artifact '+name)
        if name.endswith(('.log', '.rpt')): texts[name] = (run/name).read_text(errors='replace')
    require(not any(re.search(r'(?im)^\s*(?:Error-|Error:|Fatal:)', text) for text in texts.values()), 'Actual tool errors require review')
    values = parse_power(texts['power_verbose.rpt'], texts['power.rpt'])
    values['base_units'] = parse_base_units(texts['units.rpt'])
    verbose = parse_power(texts['power_verbose.rpt'], texts['power_verbose.rpt'])
    require(values['reported_power_w'] == verbose['reported_power_w'] and
            values['reported_group_power_w'] == verbose['reported_group_power_w'], 'Normal/verbose power reports disagree')
    values['module_breakdown'] = parse_hierarchy(texts['power_hierarchy.rpt'], values['reported_power_w'])
    values['sram_breakdown'] = parse_sram(texts['power_sram.rpt'])
    duration = Decimal(validate_activity(report['activity'], report['task_window']))
    require(duration == Decimal(str(report['duration_ns'])), 'Reported power/window duration differs')
    warnings = {}
    for name, text in texts.items():
        codes = re.findall(r'(?m)^\s*Warning:.*\(([A-Z]+-[0-9]+)\)\s*$', text)
        if codes: warnings[name] = {code: codes.count(code) for code in sorted(set(codes))}
    values.update(schema='dma16_power_numbers_v1', status='numbers_extracted_review_required',
        power_run=str(run), power_summary_sha256=expected, case=report['case'],
        synthesis_summary_sha256=report['synthesis_summary_sha256'], gate_summary_sha256=report['gate_summary_sha256'],
        firmware_sha256=report['firmware_sha256'], layout_sha256=report['layout_sha256'],
        duration_ns=str(duration), raw_reported_energy_j=str(number(values['reported_power_w']['total'])*duration*Decimal('1e-9')),
        warning_occurrences_by_artifact=warnings, activity=report['activity'],
        component_leaf_counts=report['component_leaf_counts'], artifacts=report['artifacts'],
        system_power_verified=False, timing_verified=False, approved_average_power_w=None, approved_energy_j=None,
        required_reviews=report['required_reviews'], extractor_sha256=sha(__file__))
    require(sha(summary) == expected, 'Power summary changed while extracting')
    return values


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', required=True, type=Path)
    parser.add_argument('--summary-sha256', required=True)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args(); require(not args.output.exists(), 'Use a new output file')
    result = extract(args.run, args.summary_sha256)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x', encoding='utf8') as stream: json.dump(result, stream, indent=2, ensure_ascii=False, allow_nan=False)
    print('DMA16_POWER_NUMBERS_EXTRACTED system_power_verified=false', args.output)
