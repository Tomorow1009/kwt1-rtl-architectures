"""Digest-checked small-tool overlay for an already verified immutable bundle.

For VNC-only recovery when FTP refuses new connections. Does not change bundle
inputs. Uses the same team lock/state format and fresh run directories.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import sys


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bundle',required=True,type=Path)
    p.add_argument('--bundle-sha256',required=True)
    p.add_argument('--ops-sha256',required=True)
    activity_stages=('native_saif_r4_replay','native_saif_r4_crosscheck','systolic_b_saif','systolic_b_power')
    p.add_argument('--stage',choices=['systolic_b_saif_units','systolic_b_synth','systolic_b_saif_probe','systolic_b_drc_inspect']+list(activity_stages),required=True)
    p.add_argument('--session',required=True)
    p.add_argument('--synth-run',type=Path)
    p.add_argument('--synth-sha256')
    p.add_argument('--request',type=Path)
    p.add_argument('--request-sha256')
    a=p.parse_args()
    ops=Path(__file__).resolve().parent
    manifest=ops/'manifest.json'
    if sha(manifest)!=a.ops_sha256:raise ValueError('Operations manifest changed')
    ops_files=json.loads(manifest.read_text())['files']
    for name,digest in ops_files.items():
        f=(ops/name).resolve();f.relative_to(ops)
        if not f.is_file() or sha(f)!=digest:raise ValueError('Operations input changed: '+name)
    bundle=a.bundle.resolve()
    if sha(bundle/'manifest.json')!=a.bundle_sha256:raise ValueError('Bundle manifest changed')
    if not re.fullmatch('[A-Za-z0-9_-]{1,64}',a.session):raise ValueError('Invalid session')
    if a.stage in ('systolic_b_synth','systolic_b_saif_probe','systolic_b_drc_inspect') and (a.synth_run is None or a.synth_sha256 is None):
        raise ValueError('Repair/probe requires pinned original synthesis')
    if a.stage=='systolic_b_saif_units' and (a.synth_run is not None or a.synth_sha256 is not None):
        raise ValueError('Unexpected synthesis fields')
    request=None
    if a.stage in activity_stages:
        if a.request is None or a.request_sha256 is None or sha(a.request)!=a.request_sha256:
            raise ValueError('Activity operation requires an immutable request')
        if a.synth_run is not None or a.synth_sha256 is not None:raise ValueError('Use request references for activity')
        request=json.loads(a.request.read_text())
        if request.get('schema')!='systolic-b-activity-operation-v1' or request.get('stage')!=a.stage:
            raise ValueError('Activity request stage mismatch')
    elif a.request is not None or a.request_sha256 is not None:
        raise ValueError('Unexpected activity request')
    # Overlay modules are first, base dependencies second. No base file edited.
    sys.path.insert(1,str(bundle/'workspaces/arch03/scripts'))
    import server_run as base
    if base.ROOT.resolve()!=bundle:raise ValueError('Unexpected base tool root')
    base.inputs()
    cfg=json.loads((bundle/'handoff/team/server_config.json').read_text())
    root=Path(cfg['server_root']).resolve();bundle.relative_to(root);ops.relative_to(root)
    if request is not None:a.request.resolve().relative_to(root)
    session=bundle/'runs'/a.session
    if session.exists():raise ValueError('Use new operations session')
    lock=root/'.arch02_team_lock';lock.mkdir()
    base.LOCK=lock
    owner=dict(pid=os.getpid(),host=socket.gethostname(),bundle=str(bundle),session=a.session,
               operations=str(ops),operations_manifest_sha256=a.ops_sha256)
    base.save(lock/'owner.json',owner)
    try:
        run=session/a.stage;run.mkdir(parents=True)
        record=dict(status='running',pid=os.getpid(),started=datetime.datetime.now().isoformat(),run=str(run))
        state=dict(stages={a.stage:record});base.save(session/'state.json',state)
        try:
            if a.stage=='systolic_b_saif_units':
                from native_saif_units import diagnose
                report=diagnose(cfg,run,base.call)
            elif a.stage=='systolic_b_saif_probe':
                from native_saif_probe import verify
                report=verify(cfg,run,a.synth_run,a.synth_sha256,base.call)
            elif a.stage=='systolic_b_drc_inspect':
                from systolic_b_drc_repair import inspect
                report=inspect(cfg,run,a.synth_run,a.synth_sha256,base.call)
            elif a.stage in activity_stages:
                report=activity_operation(a.stage,request,cfg,run,base.call)
            else:
                from systolic_b_drc_repair import repair
                base.vendor(cfg,run)
                report=repair(cfg,run,a.synth_run,a.synth_sha256,base.call)
            if sha(manifest)!=a.ops_sha256 or any(sha(ops/name)!=digest for name,digest in ops_files.items()):
                raise ValueError('Operations inputs changed while running')
            base.inputs()
            if request is not None and sha(a.request)!=a.request_sha256:raise ValueError('Activity request changed during run')
            report['operations_overlay']=dict(path=str(ops),manifest_sha256=a.ops_sha256,
                immutable_bundle_sha256=a.bundle_sha256,base_inputs_modified=False)
            if request is not None:report['activity_operation_request_sha256']=a.request_sha256
            base.save(run/'summary.json',report)
            record.update(status='passed',summary_sha256=sha(run/'summary.json'))
        except BaseException as exc:
            record.update(status='failed',error=str(exc));raise
        finally:
            record['finished']=datetime.datetime.now().isoformat();base.save(session/'state.json',state)
        print('B_OPERATIONS_STAGE_PASS',a.stage,record['summary_sha256'],flush=True)
    finally:
        actual=json.loads((lock/'owner.json').read_text())
        if ((base.ACTIVE_CHILD is None or base.ACTIVE_CHILD.poll() is not None) and
                all(actual.get(k)==owner[k] for k in ('pid','bundle','session'))):
            (lock/'owner.json').unlink();lock.rmdir()


def activity_operation(stage,request,cfg,run,call):
    def ref(name):
        value=request[name]
        path=Path(value['run']).resolve();path.relative_to(Path(cfg['server_root']).resolve())
        if not re.fullmatch('[0-9a-f]{64}',value['sha256']) or sha(path/'summary.json')!=value['sha256']:
            raise ValueError('Changed activity reference: '+name)
        return path,value['sha256']
    if stage=='native_saif_r4_replay':
        from native_saif_replay import verify
        gate,digest=ref('gate');probe,probe_sha=ref('probe')
        return verify(cfg,run,gate,digest,probe,probe_sha,call)
    if stage=='native_saif_r4_crosscheck':
        from native_saif_crosscheck import verify
        replay,digest=ref('replay');baseline,baseline_sha=ref('baseline_power')
        return verify(cfg,run,replay,digest,baseline,baseline_sha,call)
    if stage=='systolic_b_saif':
        from systolic_b_saif import verify,LAYERS
        gate,digest=ref('gate');qualified,qualified_sha=ref('qualification')
        return verify(cfg,run,gate,digest,qualified,qualified_sha,list(LAYERS),call)
    if stage=='systolic_b_power':
        from systolic_b_power import estimate
        activity,digest=ref('activity')
        return estimate(cfg,run,activity,digest,request['case'],call)
    raise ValueError('Unsupported activity operation')


if __name__=='__main__':main()
