"""Copy-only N1 closeout after the existing R4 storage migration finishes.

Use the unchanged runtime archive contract and explicit 21-entry auxiliary scope.
No EDA, original source mutation, cleanup, old queue resume or lock clearing.
"""
import hashlib, json, os, sys, time
from pathlib import Path
sys.dont_write_bytecode = True
CONTROL = Path('/tmp/s4_21usr_n1_closeout_20261117_2355')
TOOLS = CONTROL/'tools-20261118_0015'
ROOT = Path('/tmp/s4_21usr_n1_20261113_0210')
OPS = ROOT/'light-light126-n1-precisionops02-20261113_090845'
RUNTIME_REQUEST_SHA = '6aa79be2948fa3a5468b7078eff6013ae7b8b47328cce6ddbbeac2b363b760da'
AUX_REQUEST_SHA = 'de9e314894e9d6c9eb7990240b2453ed77e3a24a4e9f127ff463147e2fd2be45'
TOOLS_SHA = {
    'n1_archive_runtime.py': '8a1162f15b3e7c561c11ecc403e5a0bca806078fb47ee080374ff678f7cfb5db',
    'n1_paths.py': 'fe301e1e5f87852103c537b8191c7064f1b8c44a8979f1977901bf26ed16e39d',
    'n1_archive_auxiliary.py': '38841293029d4b59354ef596465ce0bd32f9022bde54cd848e2ab1e8d1271845',
}


def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda: f.read(4*1024**2), b''): h.update(b)
    return h.hexdigest()


def read(p): return json.loads(Path(p).read_text())


def main():
    assert all(sha(TOOLS/n) == h for n, h in TOOLS_SHA.items())
    assert sha(CONTROL/'runtime_request.json') == RUNTIME_REQUEST_SHA
    assert sha(CONTROL/'aux_plan_request.json') == AUX_REQUEST_SHA
    assert not (CONTROL/'archive_state.json').exists()
    sys.path.insert(0, str(TOOLS))
    import n1_archive_runtime as base
    import n1_archive_auxiliary as aux
    state = dict(schema='n1-copy-only-closeout-v1', status='waiting_for_existing_migration',
        pid=os.getpid(), started=base.now(), script_sha256=sha(__file__), tools=TOOLS_SHA,
        hardware_commit='9305c6948c764fed01fe86b20bb3db94170299ab',
        source_modified=False, source_deleted=False, T80_modified=False, old8_modified=False,
        new_hardware_validation_started=False, original_results_reused=True)
    def progress(status):
        state['status'] = status; base.save(CONTROL/'archive_state.json', state)
        print('N1_CLOSEOUT', status, base.now(), flush=True)
    progress(state['status'])
    try:
        deadline = time.monotonic()+3600
        while True:
            migration = read('/tmp/s4_21usr_r4_l05_xzmigrate01_20261117/state.json')
            assert not migration['status'].startswith('failed'), 'Preserve migration failure and stop'
            if migration['status'] == 'durable_xz_verified_original_gzip_copy_retained' and not aux.lock_path().exists(): break
            assert time.monotonic() < deadline, 'Storage predecessor still running; no archive started'
            time.sleep(5)
        state['migration_receipt_sha256'] = sha(Path(migration['destination'])/'receipt.json')
        assert migration['full_durable_readback_verified']
        fixed = {OPS/'final_report01/report.json': '8f778dd1f201855ae6b0fad815e3e3b0e258a64a694fab4cc538569ee522c2e1',
                 OPS/'model_review_1330/snapshot.json': 'b9b2af6c888a0d37144e8eb91ee98f625b3c390701116619096b558f833853ce'}
        assert all(sha(p) == h for p, h in fixed.items())
        state['original_report_identities'] = {str(p): h for p, h in fixed.items()}
        runtime = read(CONTROL/'runtime_request.json'); request = read(CONTROL/'aux_plan_request.json')
        expected = set(aux.ALLOW)|{Path(runtime['ops_bundle']).name}|{Path(v[0]).name for v in runtime['evidence']}
        assert {p.name for p in ROOT.iterdir()} == expected
        progress('auxiliary_plan')
        plan = aux.process(request, 'plan'); base.save(CONTROL/'aux_plan.json', plan)
        print('N1_AUX_PLAN', len(plan['files']), plan['regular_bytes'], flush=True)
        progress('auxiliary_identities')
        ids = aux.process(request, 'identities'); base.save(CONTROL/'aux_identities.json', ids)
        for entry in request['entries']: entry['tree_sha256'] = ids['tree_sha256'][entry['name']]
        base.save(CONTROL/'aux_archive_request.json', request)
        progress('archiving_auxiliary')
        state['auxiliary_receipt'] = aux.process(request, 'archive')
        state['auxiliary_destination'] = request['destination']
        progress('auxiliary_verified')
        assert sha(CONTROL/'runtime_request.json') == RUNTIME_REQUEST_SHA
        progress('archiving_three_runtime_bundles')
        state['runtime_receipt'] = base.archive(runtime)
        state['runtime_destination'] = runtime['destination']
        assert all(sha(p) == h for p, h in fixed.items())
        assert {p.name for p in ROOT.iterdir()} == expected
        state['finished'] = base.now()
        progress('both_archives_verified_original_sources_retained')
        print('N1_CLOSEOUT_COMPLETE', sha(CONTROL/'archive_state.json'), flush=True)
    except BaseException as error:
        state.update(failed_phase=state['status'], error=str(error), finished=base.now())
        progress('failed_preserved'); raise


if __name__ == '__main__': main()
