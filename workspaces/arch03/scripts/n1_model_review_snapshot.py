"""Join completed N1 model-review evidence without changing acceptance flags."""
from decimal import Decimal
import hashlib
import json
from pathlib import Path


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def need(ok, message):
    if not ok:
        raise ValueError(message)


def read(path, expected=None):
    if expected is not None:
        need(sha(path) == expected, 'Changed evidence: ' + str(path))
    return json.loads(Path(path).read_text())


def snapshot(request):
    inputs, reports = {}, {}
    for name in ('B0', 'N1'):
        ref = request['reports'][name]
        reports[name] = read(ref['path'], ref['sha256'])
        inputs[ref['path']] = ref['sha256']
    n1 = reports['N1']
    for key in ('asic14', 'gate14_without_SDF', 'final1200', 'activity12',
                'power12_numbers', 'internal100_precision_verified', 'fixed12_precision_verified'):
        need(n1['verification'][key] is True, 'Missing N1 verification: ' + key)
    metrics = n1['timing_metrics']
    need(Decimal(str(metrics['period_ns'])) == Decimal('6.666666') and
         Decimal(str(metrics['max'])) >= 0 and Decimal(str(metrics['min'])) >= 0 and
         int(metrics['latches']) == 0, 'Unacceptable frozen timing/structure')
    need(n1['drc_inventory']['explicit_no_violations'] and
         n1['drc_inventory']['extraction_complete'] and
         n1['drc_inventory']['violation_record_count'] == 0, 'Incomplete DRC')
    need(n1['area']['units'] == 'um^2' and
         Decimal(str(n1['area']['conservative_budget_mm2'])) <= Decimal('1.20'), 'Area limit')
    clocks = []
    for ref in n1['power_references']:
        run = Path(ref['run']); summary = run / 'summary.json'
        power = read(summary, ref['sha256']); inputs[str(summary)] = ref['sha256']
        path = run / 'timing_check.rpt'
        need(sha(path) == power['artifacts'][path.name], 'Timing check changed')
        inputs[str(path)] = power['artifacts'][path.name]
        text = path.read_text().split('Clock Pin', 1)[1].split('Information:', 1)[0]
        pins = [line.strip() for line in text.splitlines() if line.startswith('u_e203')]
        need(len(pins) == 189 and all(pin.startswith('u_e203_subsys_top/u_sirv_debug_module/')
                                    for pin in pins), 'Unexpected unclocked task-mode pins')
        measured = power['power_clock']['measured']
        need(set(measured) == {'hf_period_ns', 'lf_period_ns'} and
             Decimal(measured['hf_period_ns']) == Decimal('6.666666') and
             Decimal(measured['lf_period_ns']) == Decimal('66'),
             'Actual power clocks differ')
        clocks.append(dict(case=power['case'], no_clock_count=len(pins), static_debug_scope=True,
                           timing_report_sha256=sha(path)))
    need(len(clocks) == 12, 'Incomplete power timing scope')
    connections = {}
    for name in ('B0', 'N1'):
        path = Path(request['connections'][name]); stage = read(path.parent.parent / 'state.json')
        digest = stage['stages'][path.parent.name]['summary_sha256']
        linked = read(path, digest); inputs[str(path)] = digest
        proof = path.parent / 'unknown_connections.tsv'
        need(sha(proof) == linked['proof_sha256'], 'Linked proof changed')
        inputs[str(proof)] = linked['proof_sha256']
        ends = {tuple(line.split('\t')[2:]) for line in proof.read_text().splitlines()
                if line.startswith('endpoint\t')}
        critical = []
        for endpoint, kind, direction, ref in sorted(ends):
            if direction not in ('in', 'inout'):
                continue
            pin = endpoint.rsplit('/', 1)[-1]
            if (pin in ('CK', 'CKN', 'CLK', 'CP', 'CPN', 'RDN', 'SDN') or 'CLKLAN' in ref or
                (ref.startswith('RAMSP') and (pin in ('CEN', 'GWEN', 'RET1N') or pin.startswith('WEN[')))):
                critical.append(endpoint)
        alias_path = Path(request['aliases'][name]); alias = read(alias_path)
        need(alias['inputs_sha256'][str(path)] == digest and
             alias['complete_target_count'] == len(linked['unresolved']) and
             not alias['counts'].get('requires_further_review', 0), 'Alias scope unresolved')
        need(all(sha(p) == d for p, d in alias['inputs_sha256'].items()), 'Alias evidence changed')
        inputs[str(alias_path)] = sha(alias_path)
        connections[name] = dict(targets=linked['targets'], resolved=linked['resolved'],
            unresolved_names_classified=alias['complete_target_count'], aliases=alias['counts'],
            unique_leaf_endpoints=len(ends), unknown_explicit_control_pins=critical,
            control_pin_set=['CK', 'CKN', 'CLK', 'CP', 'CPN', 'RDN', 'SDN',
                             'CLKLAN inputs', 'RAMSP CEN/GWEN/RET1N/WEN'],
            all_unknowns_waived=False, driver_internal_power_exempted=False)
        need(not critical, 'Unknown clock/reset/ICG/SRAM control endpoint')
    root = Path(request['diagnostic']); state_path = root / 'state.json'
    state = read(state_path)
    need(state['status'] == 'all_state_diagnostic_complete_review_required' and
         len(state['stages']) == 24, 'Diagnostic not complete')
    inputs[str(state_path)] = sha(state_path)
    diagnostics = {}
    for name in ('B0', 'N1'):
        rows = []
        for index in range(1, 13):
            key = 'n1_saif_sp_%s_layer_%02d' % (name.lower(), index)
            meta = state['stages'][key]; path = root / key / 'summary.json'
            need(meta['status'] == 'passed', 'Diagnostic failure')
            item = read(path, meta['summary_sha256']); inputs[str(path)] = meta['summary_sha256']
            need(item['original_report_sha256'] == request['reports'][name]['sha256'] and
                 item['actual_setting']['initial'] in ('false', '0') and
                 item['actual_setting']['actual'] in ('true', '1') and
                 item['physical_error_bound'] is False and item['original_results_modified'] is False,
                 'Diagnostic scope changed')
            original = Path(item['original_reference']['run']) / 'summary.json'
            raw = read(original, item['original_reference']['sha256'])
            need(item['activity_sha256'] == raw['activity']['sha256'] and
                 Decimal(item['duration_ns']) == Decimal(raw['duration_ns']), 'Diagnostic activity/window mismatch')
            rows.append(item)
        duration = sum(Decimal(row['duration_ns']) for row in rows) * Decimal('1e-9')
        energy = sum(Decimal(row['energy_j']) for row in rows)
        orig_energy = sum(Decimal(row['original_power_w']) * Decimal(row['duration_ns']) * Decimal('1e-9')
                          for row in rows)
        aggregate = reports[name]['aggregate']
        need(orig_energy / 12 == Decimal(aggregate['raw_energy_per_task_j']), 'Original energy mismatch')
        diagnostics[name] = dict(cases=12, weighted_power_w=str(energy / duration),
            energy_per_task_j=str(energy / 12),
            max_absolute_relative_change=str(max(abs(Decimal(row['relative_power_change'])) for row in rows)),
            physical_error_bound=False)
    ratio = {}
    for setting in ('original', 'all_state_static_probability'):
        values = {name: reports[name]['aggregate'] if setting == 'original' else diagnostics[name]
                  for name in ('B0', 'N1')}
        pkey = 'raw_time_weighted_power_w' if setting == 'original' else 'weighted_power_w'
        ekey = 'raw_energy_per_task_j' if setting == 'original' else 'energy_per_task_j'
        power_ratio = Decimal(values['N1'][pkey]) / Decimal(values['B0'][pkey])
        energy_ratio = Decimal(values['N1'][ekey]) / Decimal(values['B0'][ekey])
        ratio[setting] = dict(power_ratio=str(power_ratio), energy_ratio=str(energy_ratio),
                             numerical_limits_met=power_ratio <= Decimal('1.1') and energy_ratio <= 1)
    need(all(sha(p) == digest for p, digest in inputs.items()), 'Inputs changed during review')
    return dict(schema='n1-final-model-review-snapshot-v1', status='collected_manual_review_required',
        inputs_sha256=inputs, source_sha256=sha(__file__), timing_metrics=metrics,
        power_timing_scope=clocks, area_upper_mm2=n1['area']['conservative_budget_mm2'],
        unknown_connection_review=connections, diagnostics=diagnostics, numerical_ratios=ratio,
        system_power_verified=False, stage_accepted=False, physical_error_bound=False,
        physical_signoff=False, original_evidence_modified=False)
