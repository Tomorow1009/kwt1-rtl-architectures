"""Same-file SAIF unknown-residence sensitivity, not a physical power bound.

Uses the installed PrimeTime all-state static-probability option. Original
production reports are immutable. Only the one option changes before read_saif.
"""
import argparse
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
import re
import time

SETTING = 'power_enable_saif_all_state_static_probability'
LAYERS = tuple('layer_%02d' % i for i in range(1, 13))


def require(ok, message):
    if not ok:raise ValueError(message)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(4*1024**2), b''):h.update(block)
    return h.hexdigest()


def read(path):return json.loads(Path(path).read_text())


def transform(text):
    require(SETTING not in text, 'Original already overrides the reviewed setting')
    anchors = list(re.finditer(r'(?m)^([ \t]*)read_saif\s+[^\n]+$', text))
    require(len(anchors) == 1 and 'read_vcd' not in text, 'Need exactly one native SAIF source')
    at = anchors[0].start();indent = anchors[0].group(1)
    block = '''set previous [get_app_var SETTING]
if {$previous ne "false" && $previous ne "0"} {error "Unexpected initial all-state SAIF setting"}
set_app_var SETTING true
set mode_file [open saif_static_probability_mode.txt w]
puts $mode_file "initial $previous"
puts $mode_file "actual [get_app_var SETTING]"
close $mode_file
'''.replace('SETTING', SETTING)
    return text[:at]+''.join(indent+line+'\n' for line in block.splitlines())+text[at:]


def run(args):
    import server_run as common
    import n1_paths
    from n1_process import ProcessLedger, atomic_save, now
    from native_saif_crosscheck import extract_reports
    from soc_power import power_invocation
    from native_saif_replay import verify_inputs
    require(sha(args.request) == args.request_sha256, 'Request identity changed')
    req = read(args.request)
    profile = 'N1'
    if req.get('transport_stage') is not None:
        import transport_review_contract as contract
        profile, cfg = contract.configure(req, common)
    else:
        cfg = n1_paths.configure(read(common.ROOT/'handoff/team/server_config.json'), common.ROOT,
            req['runtime_root'], req['bundle_manifest_sha256'], req['runtime_evidence'])
    common.inputs()
    require(re.fullmatch('[A-Za-z0-9_-]+', req['session']), 'Unsafe session')
    session = common.ROOT/'runs'/req['session'];require(not session.exists(), 'Preserve old session')
    lock = Path(cfg['server_root'])/'.arch02_team_lock';ledger = ProcessLedger(common, lock, session)
    while True:
        if lock.exists():time.sleep(20);continue
        try:ledger.acquire();break
        except OSError as error:
            if error.errno != 28 or lock.exists():raise
            print('WAIT_SHARED_LOCK_STORAGE', flush=True);time.sleep(30)
    state = dict(schema='arch03-'+profile.lower()+'-server-state-v1', pid=os.getpid(), status='running',
        started=now(), request_sha256=args.request_sha256, source_sha256=sha(__file__), stages={},
        system_power_verified=False, physical_error_bound=False)
    stage = None
    try:
        session.mkdir();ledger.initialize();atomic_save(session/'request.json', req)
        for job in req['jobs']:
            name = job['name'];require(name in (('B0', 'N1') if profile == 'N1' else (profile,)),
                                      'Unknown comparison configuration')
            path = Path(job['report']);require(sha(path) == job['sha256'], 'Original report changed')
            report = read(path);refs = report['power_references']
            if profile != 'N1':contract.report_identity(report, profile)
            require(len(refs) == 12, 'Need complete fixed twelve-layer power set')
            case_rows = []
            for expected, ref in zip(LAYERS, refs):
                stage = profile.lower()+'_saif_sp_'+name.lower()+'_'+expected
                require(stage not in state['stages'], 'Repeated diagnostic stage')
                state['stages'][stage] = dict(status='running', started=now())
                atomic_save(session/'state.json', state)
                output = session/stage;output.mkdir()
                original = Path(ref['run']);summary = original/'summary.json'
                require(sha(summary) == ref['sha256'], 'Original power summary changed')
                frozen = read(summary);require(frozen['case'] == expected, 'Power set order differs')
                verify_inputs({str(original/k):v for k,v in frozen['artifacts'].items()})
                scripts = []
                for file in frozen['artifacts']:
                    if file.endswith('.tcl') and 'read_saif ' in (original/file).read_text():scripts.append(original/file)
                require(len(scripts) == 1, 'Ambiguous original power script')
                source_inputs = read(original/'source_inputs.json');verify_inputs(source_inputs)
                activity = Path(frozen['activity_run'])/frozen['activity']['file']
                require(sha(activity) == frozen['activity']['sha256'], 'Original SAIF changed')
                # cwd-local setup files could silently change the initial tool state.
                require(not (original/'.synopsys_pt.setup').exists(), 'Original local PT setup requires review')
                text = transform(scripts[0].read_text())
                script = output/'saif_static_review.tcl';script.write_text(text)
                command, environment = power_invocation(cfg, script)
                atomic_save(output/'power_environment.json', environment)
                log = ledger.call(command, output, 'power.log')
                require('REPORTS_READY' in log, 'Original power completion marker missing')
                modes = dict(line.split() for line in (output/'saif_static_probability_mode.txt').read_text().splitlines())
                require(modes.get('initial') in ('false', '0') and modes.get('actual') in ('true', '1'),
                        'Actual all-state setting differs')
                numbers = extract_reports(output, 'systolic_b')
                base = frozen['numbers']
                require(numbers['base_units'] == base['base_units'] and numbers['settings'] == base['settings'],
                        'Unrelated power settings changed')
                require(numbers['sram']['cell_count'] == 220 and numbers['sram']['counts'] == base['sram']['counts'],
                        'Changed SRAM model scope')
                ns = Decimal(frozen['duration_ns']);power = Decimal(numbers['reported_power_w']['total'])
                baseline = Decimal(base['reported_power_w']['total'])
                result = dict(schema='saif-static-probability-diagnostic-v1', status='collected_review_required',
                    name=name, case=expected, original_reference=ref, original_report_sha256=job['sha256'],
                    activity_sha256=frozen['activity']['sha256'], original_script_sha256=sha(scripts[0]),
                    script_sha256=sha(script), source_sha256=sha(__file__), numbers=numbers,
                    duration_ns=str(ns), original_power_w=str(baseline), power_w=str(power),
                    energy_j=str(power*ns*Decimal('1e-9')), relative_power_change=str(power/baseline-1),
                    actual_setting=modes, system_power_verified=False, physical_error_bound=False,
                    original_results_modified=False)
                verify_inputs(source_inputs)
                require(sha(activity) == frozen['activity']['sha256'] and sha(summary) == ref['sha256'],
                        'Frozen source changed during diagnostic')
                atomic_save(output/'summary.json', result)
                state['stages'][stage].update(status='passed', finished=now(), summary_sha256=sha(output/'summary.json'))
                case_rows.append(dict(case=expected, duration_ns=str(ns), original_power_w=str(baseline),
                    power_w=str(power), energy_j=result['energy_j'], summary_sha256=sha(output/'summary.json')))
                atomic_save(session/'state.json', state)
                print('SAIF_ALL_STATE_COLLECTED', name, expected, str(power), flush=True)
            require(sha(path) == job['sha256'], 'Original comparison report changed')
            duration = sum(Decimal(x['duration_ns']) for x in case_rows)
            energy = sum(Decimal(x['energy_j']) for x in case_rows)
            atomic_save(session/(name+'_comparison.json'), dict(cases=case_rows,
                weighted_power_w=str(energy/(duration*Decimal('1e-9'))), energy_per_task_j=str(energy/12),
                physical_error_bound=False, system_power_verified=False))
        common.inputs();state['status'] = 'all_state_diagnostic_complete_review_required'
    except BaseException as error:
        if stage is not None:state['stages'][stage].update(status='failed', error=str(error), finished=now())
        state.update(status='failed', error=str(error));raise
    finally:
        state['finished'] = now()
        try:
            if session.is_dir():atomic_save(session/'state.json', state)
        finally:ledger.release()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request', type=Path, required=True)
    parser.add_argument('--request-sha256', required=True)
    run(parser.parse_args())
