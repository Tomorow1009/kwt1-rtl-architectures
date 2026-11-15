"""Prepare one S0 linked-unknown query after complete export/inventory.

Only writes a fresh request JSON. No DC, cleanup, acceptance or new RTL.
"""
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT=Path('/tmp/s4_21usr_t80_20261115_1830')
BUNDLE=ROOT/'light-light126-t80-s0-66b9496'
MANIFEST='2afb9a79e600e4bd1a0493699b50d463f7df8ebef666d99290cde2efbf0426b4'
OPS=ROOT/'ops-66b9496'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text())


def main():
    assert sha(BUNDLE/'manifest.json')==MANIFEST
    sys.path.insert(0,str(BUNDLE/'workspaces/arch03/scripts'))
    import server_run as common
    import s0_finish,t80_paths
    from transport_review_contract import report_identity
    queue=BUNDLE/'runs/s0_finish03';q=read(queue/'state.json')
    assert q['status']=='reports_ready_review_required' and q.get('finished')
    assert [x['stage'] for x in q['completed']]==list(s0_finish.ORDER)
    assert not Path('/proc/%d'%q['pid']).exists()
    exported=OPS/'s0_export01_control/result.json';result=read(exported)
    assert result['status']=='export_and_unknown_inventory_ready'
    assert sha(queue/'state.json')==result['queue_state_sha256']
    report_path=Path(result['report']);assert report_path==BUNDLE/'runs/s0_report01/t80_s0_report/report.json'
    assert sha(report_path)==result['report_sha256'];report=read(report_path);report_identity(report,'S0')
    inventory=Path(result['unknown_inventory']);assert inventory==BUNDLE/'runs/s0_unknown_inventory01'
    assert sha(inventory/'summary.json')==result['unknown_summary_sha256'];unknown=read(inventory/'summary.json')
    assert unknown['report_sha256']==result['report_sha256'] and unknown['netlist_sha256']==report['netlist_sha256']
    assert unknown['status']=='complete_existing_unknown_inventory_review_required'
    assert unknown['full12_collected'] and unknown['full_unknown_inventory_complete']
    evidence=read(queue/'request.json')['runtime_evidence']
    cfg=t80_paths.configure(read(BUNDLE/'handoff/team/server_config.json'),BUNDLE,ROOT,MANIFEST,evidence)
    common.inputs();t80_paths.recheck(cfg)
    session='s0_unknown_connections01';assert not (BUNDLE/'runs'/session).exists()
    request=dict(transport_stage='S0',session=session,review_bundle_manifest_sha256=MANIFEST,
        runtime_root=str(ROOT),bundle_manifest_sha256=MANIFEST,runtime_evidence=evidence,
        jobs=[dict(name='S0',synthesis=report['references']['synthesis'],
            unknown_inventories=[dict(run=str(inventory),sha256=result['unknown_summary_sha256'])])],
        preparation_sha256=sha(__file__),export_result_sha256=sha(exported),
        report_sha256=result['report_sha256'],stage_accepted=False)
    output=OPS/'s0_unknown_connections01_request.json'
    with output.open('x') as f:
        json.dump(request,f,indent=2,sort_keys=True);f.write('\n');f.flush();os.fsync(f.fileno())
    print('S0_CONNECTION_REQUEST_READY',str(output),sha(output),'NO_EDA_STARTED',flush=True)


if __name__=='__main__':main()
