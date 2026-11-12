"""Collect existing B0 L02-L12 selected controls, reusing the frozen scanner.

No L01 SAIF reread, unknown inventory generation, simulation, or EDA. The
completed L01 receipt is bound as an input, never treated as a power waiver.
Python 3.6; sequential worker; launch at low priority in a fresh private path.
"""
import argparse
from pathlib import Path

import b0_saif_control_probe as probe

PROBE_SHA = 'b1c6df556c7df0f2b8e13c1be6c2ba8babb4b994f50c2d99b5f78af24d7bc963'
CASES = tuple('layer_%02d' % n for n in range(2, 13))
SCHEMA = 'b0-selected-controls-remaining11-v1'


def identity():
    result = dict(wrapper=dict(path=str(Path(__file__).resolve()), sha256=probe.sha(__file__)),
                  scanner=probe.dependencies())
    probe.require(result['scanner']['tool']['sha256'] == PROBE_SHA, 'Frozen control scanner changed')
    return result


def selection_contract():
    return dict(shared_top=list(probe.SHARED_TOP + probe.SHARED_BITS),
        macro_required=list(probe.MACRO_REQUIRED), adapter_required=list(probe.ADAPTER_REQUIRED),
        aon_top_required=list(probe.AON_REQUIRED), aon_name_regex=probe.AON_CONTROL.pattern,
        limit_records=probe.LIMIT_SELECTED)


def input_contract(inventory, inventory_sha, l01_path, l01_sha, scope_root, runtime):
    scope = Path(scope_root).resolve()
    inventory = probe.scoped(inventory, scope);inv = probe.small(inventory, inventory_sha)
    probe.require(inv['schema'] == 'b0-complete-saif-unknown-map-v1' and
        inv['status'] == 'complete_existing_unknown_inventory_review_required' and
        inv['tool_sha256'] == probe.UNKNOWN_TOOL_SHA, 'Wrong frozen unknown inventory')
    cases = inv['cases']
    probe.require(len(cases) == 11 and {r['case'] for r in cases} == set(CASES),
                  'Inventory must contain exactly L02-L12, without L01')
    report_path = probe.scoped(inv['report'], scope);report = probe.small(report_path, inv['report_sha256'])
    probe.require(report['schema'] == 'systolic-b-evidence-export-v1' and
        report['netlist_sha256'] == inv['netlist_sha256'], 'B0 report/netlist identity differs')
    arun = probe.scoped(report['activity_reference']['run'], scope)
    activity_path = arun / 'summary.json';activity_sha = report['activity_reference']['sha256']
    probe.require(activity_sha == inv['activity_summary_sha256'], 'Activity identity differs')
    activity = probe.small(activity_path, activity_sha)
    state_path = arun.parent / 'state.json';state_sha = probe.sha(state_path)
    state = probe.small(state_path, state_sha)['stages']['systolic_b_saif']
    probe.require(state['status'] == 'passed' and state['summary_sha256'] == activity_sha and
        activity['status'] == 'B_native_saif_function_and_complete_windows_passed' and
        activity['firmware_sha256'] == report['firmware_sha256'] and
        activity['synthesis_summary_sha256'] == report['references']['synthesis']['sha256'],
        'Original B0 activity is not frozen passed')
    rows = activity['cases']
    probe.require(len(rows) == 12 and {r['case'] for r in rows} == {'layer_%02d' % n for n in range(1, 13)},
                  'Original activity needs exactly twelve distinct cases')
    by_case = {r['case']: r for r in rows}
    for row in cases:
        probe.require(by_case[row['case']]['activity'] == row['activity'], 'Existing case audit differs')
    l01_path = Path(l01_path)
    probe.require(l01_path.is_absolute() and l01_path.resolve() == l01_path, 'Use exact absolute L01 receipt')
    l01 = probe.small(l01_path, l01_sha)
    probe.require(l01['schema'] == 'b0-selected-control-residence-v1' and
        l01['status'] == 'selected_control_residence_collected_review_required' and
        l01['case'] == 'layer_01' and l01['activity'] == by_case['layer_01']['activity'] and
        l01['netlist_sha256'] == report['netlist_sha256'] and
        l01['firmware_sha256'] == report['firmware_sha256'] and
        l01['selection_contract'] == selection_contract(), 'Existing L01 control receipt differs')
    probe.require({k: v['sha256'] for k, v in l01['runtime_dependencies'].items()} ==
                  {k: v['sha256'] for k, v in runtime['scanner'].items()},
                  'L01 and remaining11 scanner dependencies differ')
    probe.require(l01['source_read_passes'] == 1 and l01['source_activity_modified'] is False and
        l01['system_power_verified'] is False and l01['joint_timing_proved'] is False and
        l01['full_control_cone_audited'] is False, 'L01 receipt scope differs')
    tracked = {str(inventory): inventory_sha, str(report_path): inv['report_sha256'],
               str(activity_path): activity_sha, str(state_path): state_sha, str(l01_path): l01_sha}
    selected = []
    for name in CASES:
        row = by_case[name];path = probe.scoped(arun / row['activity']['file'], scope)
        probe.require(path.parent == arun and path.suffix == '.saif', 'Unsafe activity basename')
        selected.append((name, path, row))
    probe.require(len({str(path) for _, path, _ in selected}) == 11 and
        str(arun / by_case['layer_01']['activity']['file']) not in {str(path) for _, path, _ in selected},
        'Repeated activity path or attempted L01 rescan')
    return dict(tracked=tracked, selected=selected, report=report, l01=l01,
                l01_path=str(l01_path), l01_sha256=l01_sha)


def collect(inventory, inventory_sha, l01_path, l01_sha, scope_root, output):
    output = Path(output)
    probe.require(output.is_absolute() and output.resolve() == output and not output.exists() and
                  output.parent.is_dir(), 'Use fresh absolute output directory; no overwrite')
    output.mkdir(mode=0o700)
    request = dict(schema=SCHEMA, status='collecting', cases=list(CASES),
        inventory=str(inventory), inventory_sha256=inventory_sha,
        l01_control=str(l01_path), l01_control_sha256=l01_sha,
        scope_root=str(scope_root), selection_contract=selection_contract(),
        system_power_verified=False, full_control_cone_audited=False, joint_timing_proved=False,
        source_activity_modified=False, no_eda_or_simulation_started=True,
        l01_saif_rescanned=False, unknown_inventory_regenerated=False)
    probe.save(output / 'request.json', request)
    completed = [];captured = [];current = None;case_output = None
    try:
        probe.require(probe.shutil.disk_usage(str(output)).free >= probe.RESERVE + 15 * probe.LIMIT_OUTPUT,
                      'Initial output reserve insufficient')
        runtime = identity()
        inputs = input_contract(inventory, inventory_sha, l01_path, l01_sha, scope_root, runtime)
        request.update(runtime_dependencies=runtime, input_sha256=inputs['tracked'],
            netlist_sha256=inputs['report']['netlist_sha256'],
            firmware_sha256=inputs['report']['firmware_sha256'])
        probe.save(output / 'verified_request.json', request)
        for number, (current, path, row) in enumerate(inputs['selected']):
            captured = [];case_output = output / current;case_output.mkdir(mode=0o700)
            case_request = dict(request, case=current, saif=str(path), saif_sha256=row['activity']['sha256'])
            probe.save(case_output / 'request.json', case_request)
            probe.require(probe.shutil.disk_usage(str(output)).free >=
                          probe.RESERVE + (14 - number) * probe.LIMIT_OUTPUT, 'Output reserve reached')
            result = probe.scan(path, row['task_window'], row['activity'], captured)
            probe.require(identity() == runtime, 'Runtime dependency identity changed')
            result.update(case_request);result['status'] = 'selected_control_residence_collected_review_required'
            probe.save(case_output / 'summary.json', result)
            completed.append(dict(case=current, summary=str(case_output / 'summary.json'),
                summary_sha256=probe.sha(case_output / 'summary.json'), saif_sha256=row['activity']['sha256'],
                selected_count=result['selected_count'], missing_count=len(result['coverage']['missing']),
                selected_unknown_records=result['coverage']['selected_unknown_records']))
            print('B0_REMAINING_CONTROL_COLLECTED', current, len(completed), 'of', len(CASES), flush=True)
        probe.require(all(probe.sha(p) == expected for p, expected in inputs['tracked'].items()),
                      'Frozen receipt changed during collection')
        probe.require(identity() == runtime, 'Runtime dependency identity changed')
        probe.require(probe.shutil.disk_usage(str(output)).free >= probe.RESERVE + probe.LIMIT_OUTPUT,
                      'Final output reserve reached')
        result = dict(request, status='complete_existing_remaining11_controls_review_required',
            cases=completed, new_source_read_passes=11, reused_l01_receipt=True,
            full12_receipt_coverage=True, completed_cases=11)
        probe.save(output / 'summary.json', result)
        print('B0_REMAINING11_CONTROLS_COLLECTED', probe.sha(output / 'summary.json'), flush=True)
        return result
    except Exception as error:
        failure = dict(request, status='failed', error=str(error), failed_case=current,
            completed_cases=completed, retained_selected_count=len(captured), full12_receipt_coverage=False)
        probe.save(output / 'failure.json', failure)
        if case_output is not None and captured:
            probe.save(case_output / 'partial_selected.json', dict(unqualified=True, selected=captured))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inventory', type=Path, required=True)
    parser.add_argument('--inventory-sha256', required=True)
    parser.add_argument('--l01-control', type=Path, required=True)
    parser.add_argument('--l01-control-sha256', required=True)
    parser.add_argument('--scope-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    collect(args.inventory, args.inventory_sha256, args.l01_control, args.l01_control_sha256,
            args.scope_root, args.output)
