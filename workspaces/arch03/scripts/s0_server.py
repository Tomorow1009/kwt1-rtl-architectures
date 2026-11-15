"""S0 only, independent new session and the unchanged team coordination lock."""
import argparse
import datetime
import json
from pathlib import Path
import re
import shutil
import os

import server_run as common
import t80_paths
from n1_process import ProcessLedger, atomic_save
from partition_synth_contract import require
import s0_partition_synth as mapping


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('stage',choices=('capability','synth'))
    p.add_argument('--session',required=True)
    p.add_argument('--origin',required=True,type=Path)
    p.add_argument('--runtime-root',required=True,type=Path)
    p.add_argument('--runtime-manifest-sha256',required=True)
    a=p.parse_args()
    require(re.fullmatch('[A-Za-z0-9_-]{1,64}',a.session),'Bad S0 session')
    cfg=t80_paths.configure(json.loads((common.ROOT/'handoff/team/server_config.json').read_text()),
        common.ROOT,a.runtime_root,a.runtime_manifest_sha256)
    t80_paths.allowed_run(a.origin,cfg,'Original T80 synthesis')
    manifest=common.inputs()
    for module in ('s0_server.py','s0_partition_synth.py','partition_synth_contract.py','n1_process.py'):
        name='workspaces/arch03/scripts/'+module
        require(manifest['files'].get(name)==common.sha(common.ROOT/name),'Unfrozen S0 tool '+name)
    mapping.verify_origin(a.origin,common.ROOT)
    session=common.ROOT/'runs'/a.session
    require(not session.exists(),'Preserve previous S0 session')
    free=shutil.disk_usage(str(common.ROOT)).free
    required=int((12 if a.stage=='synth' else 1)*1024**3*1.2)+2*1024**3
    require(free>=required,'Insufficient independent S0 runtime space')
    session.mkdir(parents=True)
    record=dict(status='acquiring_lock',pid=os.getpid(),started=datetime.datetime.now().isoformat(),
        stage='t80_s0_'+a.stage,hardware='876b883d95199f2d1889019cbfec4c93c42d1be5',
        protected_desktop_written=False,old_eight_lane_written=False)
    atomic_save(session/'state.json',record)
    ledger=ProcessLedger(common,Path(cfg['server_root'])/'.arch02_team_lock',session)
    try:
        ledger.acquire();ledger.initialize()
        run=session/('t80_s0_'+a.stage);run.mkdir()
        t80_paths.allowed_run(run,cfg,'S0 output')
        common.save(session/'runtime_storage_receipt.json',t80_paths.receipt(cfg))
        common.save(session/'storage_preflight.json',dict(free_bytes=free,required_bytes=required,margin=1.2))
        record.update(status='running',run=str(run));atomic_save(session/'state.json',record)
        if a.stage=='synth':
            report=mapping.execute(cfg,run,a.origin,ledger.call)
        else:
            text='''
set_app_var sh_continue_on_error false
help characterize
help write_script
help read_ddc
help compile
help report_timing
puts "S0_CAPABILITIES_PRINTED mapping_started=false"
quit
'''
            (run/'capability.tcl').write_text(text)
            output=ledger.call([cfg['tools']['dc_shell'],'-f',run/'capability.tcl'],run,'capability.log')
            from soc_synth import require_tool_marker
            require_tool_marker(output,'S0_CAPABILITIES_PRINTED mapping_started=false')
            report=dict(status='capabilities_printed_manual_review_required',mapping_started=False,
                tool_log_sha256=common.sha(run/'capability.log'))
        common.inputs();t80_paths.recheck(cfg)
        common.save(run/'summary.json',report)
        record.update(status='reports_ready_review_required',summary_sha256=common.sha(run/'summary.json'))
    except BaseException as exc:
        record.update(status='failed',error=str(exc));raise
    finally:
        try:
            if ledger.acquired: ledger.release()
        finally:
            record['finished']=datetime.datetime.now().isoformat();atomic_save(session/'state.json',record)
    print('S0_STAGE_REPORTS_READY',a.stage,str(run),flush=True)


if __name__=='__main__': main()
