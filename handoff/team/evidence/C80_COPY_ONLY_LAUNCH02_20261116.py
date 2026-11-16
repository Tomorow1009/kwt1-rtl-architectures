"""Prepare one durable C80 copy after its queues and report tool have exited.

Prepared locally; not scheduled by the validation or report controllers.
Copies only, fully verifies the archive, preserves source and old failures.
No hardware-stage acceptance, deletion, EDA or C32 dispatch is performed.
"""
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path('/tmp/s4_21usr_c80_20261116_1245')
BUNDLE=ROOT/'light-light126-c80-74f3ae7'
MANIFEST='d0f18e4a6aa8a928df37d4347f1a8853c448e823f0685a83c5b710732e5e7a59'
OPS=ROOT/'ops-followup-9eda887'
OPS_RECEIPT='508d4f70bbb8f886a59533bf09727ddd4122bcf5e2276336e062d0c62893acb2'
BACKUPS=Path('/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109/backups')
EXPORT=ROOT/'c80_export_review02/state.json'


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(4*1024**2),b''):h.update(chunk)
    return h.hexdigest()


def read(path):return json.loads(Path(path).read_text())
def need(ok,message):
    if not ok:raise ValueError(message)


def save_new(path,value):
    with Path(path).open('x') as stream:
        json.dump(value,stream,indent=2,sort_keys=True);stream.write('\n')
        stream.flush();os.fsync(stream.fileno())


def preflight():
    need(sha(BUNDLE/'manifest.json')==MANIFEST and sha(OPS/'import_receipt.json')==OPS_RECEIPT,
         'Frozen C80 bundle or independent archive tools changed')
    export=read(EXPORT);previous=read(ROOT/'c80_followup02.json')
    need(previous.get('source_sha256')=='d5f012fefa01db49de5cb093774d7afee2547692a3f4611c7a2e25e73221cdc5',
         'Wrong space-recovered followup source')
    need(all(sha(p)==h for p,h in previous['failed_attempts'].items()), 'Preserved ENOSPC failure history changed')
    need(export.get('status')=='facts_joined_manual_conclusion_required' and export.get('finished') and
         previous.get('status')=='reports_ready_independent_review_pending' and previous.get('finished'),
         'Complete own C80 validation and report chain before copying')
    for state in (export,previous,read(BUNDLE/'runs/c80_initial02/state.json')):
        need(type(state.get('pid')) is int and not Path('/proc/%d'%state['pid']).exists(),
             'C80 queue or exporter still active')
    need(export['predecessor_state_sha256']==sha(ROOT/'c80_followup02.json'),
         'Export belongs to another followup state')
    need(export['report']==str(BUNDLE/'runs/c80_report02/c80_report/report.json') and
         export['snapshot']==str(ROOT/'c80_export_review02/model_review_snapshot.json'),
         'Wrong completed C80 report paths')
    need(sha(export['report'])==export['report_sha256'] and sha(export['snapshot'])==export['snapshot_sha256'],
         'Completed C80 report or model snapshot changed')
    return export,previous


def imports():
    sys.dont_write_bytecode=True
    sys.path[:0]=[str(OPS),str(BUNDLE/'workspaces/arch03/scripts')]
    import c80_archive_runtime as archive
    need(Path(archive.__file__).resolve()==OPS/'c80_archive_runtime.py','Wrong C80 archive helper')
    mf=read(BUNDLE/'manifest.json')['files'];ops=read(OPS/'payload.json')['files'];identities={}
    for module in list(sys.modules.values()):
        value=getattr(module,'__file__',None)
        if not value:continue
        path=Path(value).resolve()
        if path.parent==OPS:
            need(path.name in ops and sha(path)==ops[path.name]['sha256'],'Changed C80 operation helper')
            identities[str(path)]=sha(path)
        elif BUNDLE in path.parents:
            key=path.relative_to(BUNDLE).as_posix()
            need(key in mf and sha(path)==mf[key],'Unbound frozen C80 helper')
            identities[str(path)]=mf[key]
    return archive,identities


def worker(control,request_sha):
    control=Path(control).resolve()
    need(control.parent==Path('/tmp') and control.name.startswith('s4_21usr_c80_archive02_') and
         Path.cwd()==control and Path(__file__).resolve()==control/'worker.py',
         'Run the C80 copy worker from its separate control directory')
    preflight();need(sha(control/'request.json')==request_sha,'Copy request changed')
    archive,identities=imports();launch=read(control/'launch.json')
    need(launch['loaded_dependencies']==identities and launch['worker_sha256']==sha(__file__),
         'Copy worker or imported dependencies changed')
    try:
        result=archive.archive(read(control/'request.json'))
        need(all(sha(path)==want for path,want in identities.items()) and
             sha(control/'request.json')==request_sha,'Copy inputs changed')
        save_new(control/'result.json',result)
        print('C80_COPY_ONLY_VERIFIED',result['archive_sha256'],result['archive_bytes'],flush=True)
    except BaseException as error:
        save_new(control/'failed.json',dict(error=str(error),source_deleted=False));raise


def launch():
    export,previous=preflight();archive,identities=imports()
    stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M')
    control=Path('/tmp')/('s4_21usr_c80_archive02_'+stamp)
    target=BACKUPS/('c80-runtime-'+stamp+'-copy02')
    need(not control.exists() and not target.exists(),'Preserve previous C80 archive attempts')
    request=dict(schema=archive.SCHEMA,runtime_root=str(ROOT),bundle=str(BUNDLE),
        bundle_manifest_sha256=MANIFEST,runtime_evidence=[],destination=str(target),
        initial=dict(queue=str(BUNDLE/'runs/c80_initial02'),state_sha256=previous['predecessor_state_sha256']),
        finish=dict(queue=previous['finish_queue'],state_sha256=previous['finish_state_sha256']),
        report_run=str(Path(export['report']).parent),report_sha256=export['report_sha256'])
    if previous.get('precision_recovery'):request['precision_recovery']=previous['precision_recovery']
    # Reuse the strict, tested full-chain checker before creating any archive target.
    archive.evidence(request,BUNDLE)
    control.mkdir(mode=0o700);entry=control/'worker.py'
    with entry.open('xb') as stream:stream.write(Path(__file__).read_bytes())
    save_new(control/'request.json',request)
    command=[sys.executable,'-B','-u',str(entry),'--worker',str(control),sha(control/'request.json')]
    save_new(control/'launch.json',dict(command=command,loaded_dependencies=identities,
        worker_sha256=sha(entry),source_launcher_sha256=sha(__file__),export_state_sha256=sha(EXPORT),
        copy_only=True,source_deleted=False,source_modified=False,stage_accepted=False))
    preflight()
    with (control/'archive.log').open('x') as log:
        child=subprocess.Popen(command,cwd=str(control),stdin=subprocess.DEVNULL,
            stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    save_new(control/'process.json',dict(pid=child.pid,destination=str(target),command=command,
        started=datetime.datetime.now().isoformat()))
    print('C80_COPY_ONLY_STARTED',child.pid,str(control),str(target),flush=True)


if __name__=='__main__':
    if len(sys.argv)==4 and sys.argv[1]=='--worker':worker(sys.argv[2],sys.argv[3])
    else:
        need(len(sys.argv)==1,'No arbitrary paths or partial-copy modes');launch()
