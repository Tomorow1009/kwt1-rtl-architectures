"""Prepare an S0 report request only after its own final-netlist queue completes.

Reuse only the unchanged-hardware ASIC/240/FLOAT references from the pinned
T80 request. All synthesis, gate, activity and power references come from S0.
No EDA, cleanup, accepted status, or modification of previous evidence.
"""
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT=Path('/tmp/s4_21usr_t80_20261115_1830')
BUNDLE=ROOT/'light-light126-t80-s0-a7e7e49'
MANIFEST='4d0699ff21c1708484f182e09a934ea918255ddfc116f1f2a179ec7b015e8766'
MAPPING_BUNDLE=ROOT/'light-light126-t80-s0-a5f138e'
MAPPING_MANIFEST='c4774571c8aebe323657a5aaebc017f24324396b28ea6b2852e32e40a213b924'
OLD_BUNDLE=Path('/tmp/s4_21usr_t80_20261113_2012/light-light126-t80-activity-cef81d4')
OLD_MANIFEST='181bb96b719363be5350e9e968ac2b2ad29555e2f4606e362721be3c42629b9b'
OLD_REQUEST=OLD_BUNDLE/'runs/t80_final_report01/request.json'
OLD_REQUEST_SHA='ec74187f550a70e5bbe0662862b8db5c142448baa223855099b5e391612d9e43'
CACHE_BUNDLE=ROOT/'light-light126-t80-s0-9ffb2a9'
CACHE_MANIFEST='d397b97768c6ce5089aeda32a5e2e22d50e30f0b5a34c6edfae12e71ea9988ba'
SEED_BUNDLE=ROOT/'light-light126-t80-s0-05c923f'
SEED_MANIFEST='4473686ec4bb1b67edd4741fbf171a89788465140b8a1e7d3a9944f4847e7ff2'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text())


def completed(queue,expected):
    assert queue['status']=='reports_ready_review_required' and queue.get('finished')
    rows=queue['completed']
    assert [r['stage'] for r in rows]==list(expected),'Incomplete/repeated/out-of-order S0 queue'
    return {r['stage']:r['reference'] for r in rows}


def main():
    assert sha(BUNDLE/'manifest.json')==MANIFEST
    assert sha(OLD_BUNDLE/'manifest.json')==OLD_MANIFEST
    assert sha(OLD_REQUEST)==OLD_REQUEST_SHA
    sys.path.insert(0,str(BUNDLE/'workspaces/arch03/scripts'))
    import s0_finish,t80_report,t80_paths
    from s0_validation import verify_synthesis
    # Old FLOAT/request evidence has its own explicitly pinned identity above;
    # do not register a different /tmp root under this runtime's permissions.
    cfg=t80_paths.configure(read(BUNDLE/'handoff/team/server_config.json'),BUNDLE,ROOT,MANIFEST,
        [(str(MAPPING_BUNDLE),MAPPING_MANIFEST),(str(CACHE_BUNDLE),CACHE_MANIFEST),(str(SEED_BUNDLE),SEED_MANIFEST)])
    q=BUNDLE/'runs/s0_finish02/state.json';qsha=sha(q);queue=read(q)
    refs=completed(queue,s0_finish.ORDER)
    assert not (Path('/proc')/str(queue['pid'])).exists(),'Original queue owner has not exited'
    old=read(OLD_REQUEST)
    assert old['schema']=='arch03-t80-report-request-v1'
    synthesis=queue['synthesis'];verify_synthesis(synthesis['run'],synthesis['sha256'],cfg)
    for name,ref in refs.items():
        kind='power' if name.startswith('power_') else name
        t80_paths.allowed_run(ref['run'],cfg,'S0 completed report source')
        t80_report.stage(ref,'t80_'+kind)
    request=dict(schema='arch03-s0-report-request-v1',asic=old['asic'],batch=old['batch'],
        precision=old['precision'],synthesis=synthesis,gate=refs['gate'],activity=refs['saif'],
        power=[refs['power_'+layer] for layer in s0_finish.LAYERS],
        history=[dict(original_unchanged_hardware_request=str(OLD_REQUEST),sha256=OLD_REQUEST_SHA,
            reused_scopes=['ASIC14','ASIC240','same_integer_FLOAT_precision'],
            old_netlist_gate_activity_power_reused=False),
            dict(s0_queue=str(q.parent),state_sha256=qsha,
                 timing=refs['timing_audit'],drc=refs['drc_audit'],structure=refs['structure'])])
    assert sha(q)==qsha and sha(OLD_REQUEST)==OLD_REQUEST_SHA
    t80_paths.recheck(cfg)
    output=ROOT/'ops-a7e7e49/s0_report01_request.json'
    with output.open('x') as f:
        json.dump(request,f,indent=2,sort_keys=True);f.write('\n');f.flush();os.fsync(f.fileno())
    print('S0_REPORT_REQUEST_READY',str(output),sha(output),'stage_accepted=false',flush=True)


if __name__=='__main__':main()
