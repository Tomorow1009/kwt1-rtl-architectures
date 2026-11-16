"""Fresh read-only C32 driver query with the corrected decorated-row parser.

Frozen bundle and old failed summaries stay byte-identical. No repair or new
acceptance occurs here. The original collaboration lock owns the sole DC child.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys
import time

ROOT=Path('/tmp/s4_21usr_c32_20261116_2010')
BUNDLE=ROOT/'light-light126-c32-91135f6'
MANIFEST='d877234086f471acb3c7f4ea0c69bb280606d6bbb45fdd212e8bf30366b316c7'
SYNTH=BUNDLE/'runs/c32_initial03_synth/c32_synth'
SYNTH_SHA='ee08629b7cc9181d6e6db4ae21205ae931c6b1fe28f5c4420afd83097e8cef87'
AUDIT_SHA='3e698243214e9b1480bade07a3d849a456675d1dd9b1dd8e0dfcd0d1986c17ae'


def main():
    sys.path.insert(0,str(BUNDLE/'workspaces/arch03/scripts'))
    import server_run as common
    import c32_paths
    from partition_synth_contract import require,digest
    from n1_process import ProcessLedger,atomic_save,now
    source=Path(__file__).resolve().with_name('c32_drc_audit.py')
    require(os.name=='posix' and digest(source)==AUDIT_SHA and common.ROOT==BUNDLE,'Wrong independent parser or original bundle')
    require(digest(BUNDLE/'manifest.json')==MANIFEST and digest(SYNTH/'summary.json')==SYNTH_SHA,'Frozen C32 identity changed')
    cfg=c32_paths.configure(json.loads((BUNDLE/'handoff/team/server_config.json').read_text()),BUNDLE,ROOT,MANIFEST,[])
    common.inputs()
    prior=json.loads((ROOT/'c32_export_review03/state.json').read_text())
    require(prior['status']=='failed_preserved' and prior.get('finished') and
            'Unresolved C32 constraints' in (ROOT/'c32_export_review03/snapshot.log').read_text(),
            'Inspect the existing failed review; do not restart a live or unrelated queue')
    for p in (ROOT/'c32_export_review03').glob('*_process.json'):
        pid=json.loads(p.read_text())['pid'];require(not Path('/proc/%d'%pid).exists(),'Prior review child is still live')
    require(not Path('/proc/%d'%prior['pid']).exists(),'Prior review parent is still live')
    spec=importlib.util.spec_from_file_location('c32_drc_inspect_v2',str(source))
    audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
    inventory=audit.constraints_inventory((SYNTH/'constraints.rpt').read_text())
    prefix='u_e203_subsys_top/u_e203_subsys_main/u_e203_subsys_mems/u_arch03_accel/core/'
    require(inventory['violation_record_count']==326 and inventory['extraction_complete'] and
            inventory['by_section']=={'max_transition':326} and
            inventory['query_targets']==sorted(prefix+n for n in ('n9916','n9882','n9950')),
            'Actual report differs from the reviewed three-net format')
    session=BUNDLE/'runs/c32_drc_inspect02';require(not session.exists(),'Preserve previous independent inspection')
    ledger=ProcessLedger(common,Path(cfg['server_root'])/'.arch02_team_lock',session)
    while True:
        if ledger.lock.exists():time.sleep(5);continue
        try:ledger.acquire();break
        except OSError as error:
            if error.errno!=28 or ledger.lock.exists():raise
            print('WAIT_ORIGINAL_LOCK_STORAGE',flush=True);time.sleep(5)
    state=dict(status='running',pid=os.getpid(),started=now(),source_sha256=digest(__file__),
        parser_sha256=digest(source),synthesis_summary_sha256=SYNTH_SHA,
        old_failed_review_sha256=digest(ROOT/'c32_export_review03/state.json'),netlist_modified=False,
        constraints_modified=False,stage_accepted=False,protected_T80_modified=False,old8_modified=False)
    try:
        run=session/'c32_drc_audit';run.mkdir(parents=True,exist_ok=False);ledger.initialize()
        atomic_save(session/'state.json',state)
        result=audit.audit(cfg,run,SYNTH,SYNTH_SHA,ledger.call)
        require(result['driver_query_complete'] and not result['constraint_report_clear'],
                'Must collect complete drivers without concealing actual violations')
        common.inputs();c32_paths.recheck(cfg)
        require(digest(source)==AUDIT_SHA,'Independent parser changed during query')
        atomic_save(run/'summary.json',result)
        state.update(status='driver_facts_ready_constraints_still_violated',summary_sha256=digest(run/'summary.json'),
            unique_driver_cells=result['drivers']['unique_driver_cells'])
    except BaseException as error:
        state.update(status='failed_preserved',error=str(error));raise
    finally:
        state['finished']=now();atomic_save(session/'state.json',state);ledger.release()
    print('C32_DRC_INSPECT02_COMPLETE',state['summary_sha256'],'constraints_clear=false',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--inspect-only',action='store_true',required=True)
    p.parse_args();main()
