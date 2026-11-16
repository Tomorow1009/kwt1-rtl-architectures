"""Start fresh gate14/SAIF12/PT12 only after the exact C32 repair is qualified.

The old RTL240 is not rerun; no old final-netlist gate/power evidence is reused.
One original team lock and the existing process ledger control the queue.
"""
import argparse
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path('/tmp/s4_21usr_c32_20261116_2010')
BUNDLE=ROOT/'light-light126-c32-repair-5828804'
OLD=ROOT/'light-light126-c32-91135f6'
OLD_SHA='d877234086f471acb3c7f4ea0c69bb280606d6bbb45fdd212e8bf30366b316c7'
METHOD=Path('/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109/bundles/light-light126-systolic-b-v3-20261112_114355-ced0e139a01e/runs/systolic_b_r4_crosscheck02/native_saif_r4_crosscheck')
METHOD_SHA='a0a9bc6280e7fe5f35b666535157700aac1d9c0b4490873b6199ba9b5c662d26'


def read(path):return json.loads(path.read_text())


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--repair-summary-sha256',required=True)
    args=parser.parse_args()
    sys.path.insert(0,str(BUNDLE/'workspaces/arch03/scripts'))
    import server_run as common
    import c32_paths as paths
    import c32_finish as finish
    from c32_validation import verify_synthesis,require_clear_constraints
    from partition_synth_contract import require,digest
    launch=read(ROOT/'c32_repair03_launch.json');request=read(ROOT/'c32_repair03_request.json')
    require(launch['bundle']==str(BUNDLE) and common.ROOT==BUNDLE and
        digest(BUNDLE/'manifest.json')==launch['manifest_sha256'] and
        digest(ROOT/'c32_repair03_request.json')==launch['request_sha256'],'Changed repair launch')
    require(not Path('/proc/%d'%launch['pid']).exists(),'Repair parent still live')
    cfg=paths.configure(read(BUNDLE/'handoff/team/server_config.json'),BUNDLE,ROOT,
        launch['manifest_sha256'],[[str(OLD),OLD_SHA]])
    common.inputs()
    session=BUNDLE/'runs/c32_repair03';synth=session/'c32_synth'
    state=read(session/'state.json')['stages']['c32_synth']
    require(state['status']=='passed' and state.get('finished') and
        state['summary_sha256']==args.repair_summary_sha256,'Incomplete repaired mapping')
    for path in (session/'process_ledger').glob('child_*.json'):
        child=read(path)
        require(child['status']=='exited' and child['returncode']==0 and child['wait_completed'] and
            not Path('/proc/%d'%child['pid']).exists(),'Repair child incomplete/live')
    report,_=verify_synthesis(synth,args.repair_summary_sha256,cfg)
    require(report['mapped_repair']['only_size_cell_no_compile'] and
        report['setup_hold_nonnegative'] and report['area_summary']['conservative_budget_mm2']<=1.0 and
        int(report['metrics']['latches'])==0,'Repair still violates timing/area/structure')
    require_clear_constraints(synth,report)
    from c32_saif import qualification
    qualification(METHOD,METHOD_SHA,cfg)
    require(not (Path(cfg['server_root'])/'.arch02_team_lock').exists(),'Original team lock is held')
    name='c32_finish_repair03';rp=ROOT/(name+'_request.json');lp=ROOT/(name+'.log');receipt=ROOT/(name+'_launch.json')
    require(not any(p.exists() for p in (rp,lp,receipt,BUNDLE/'runs'/name)),'Preserve previous finish attempt')
    value=dict(schema='c32-final-netlist-finish-v1',bundle=str(BUNDLE),
        bundle_manifest_sha256=launch['manifest_sha256'],runtime_root=str(ROOT),runtime_evidence=[[str(OLD),OLD_SHA]],
        queue_sha256=digest(finish.__file__),synthesis=dict(run=str(synth),sha256=args.repair_summary_sha256),
        qualification=dict(run=str(METHOD),sha256=METHOD_SHA))
    with rp.open('x') as f:json.dump(value,f,indent=2,sort_keys=True);f.write('\n')
    cmd=[sys.executable,'-B',str(BUNDLE/'workspaces/arch03/scripts/c32_finish.py'),
        '--request',str(rp),'--request-sha256',digest(rp),'--session',name]
    with lp.open('x') as log:
        child=subprocess.Popen(cmd,cwd=str(BUNDLE),stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    result=dict(pid=child.pid,started=datetime.datetime.now().isoformat(),command=cmd,source_sha256=digest(__file__),
        manifest_sha256=launch['manifest_sha256'],request_sha256=digest(rp),synthesis=value['synthesis'],
        stage_accepted=False,old_gate_power_reused=False,protected_T80_modified=False,old8_modified=False)
    with receipt.open('x') as f:json.dump(result,f,indent=2,sort_keys=True);f.write('\n')
    print('C32_REPAIR_FINISH_LAUNCHED',child.pid,result['started'],flush=True)


if __name__=='__main__':main()
