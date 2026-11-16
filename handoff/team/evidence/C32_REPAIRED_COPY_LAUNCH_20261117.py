"""Copy the completed repaired C32 chain; never delete or alter its runtime.

Explicitly invoked only after the one-shot exporter has exited. The archive
contract checks original RTL qualification and the repaired netlist's own PPA.
No stage acceptance, next-stage dispatch, cleanup, or queue restart occurs.
"""
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path('/tmp/s4_21usr_c32_20261116_2010')
BUNDLE=ROOT/'light-light126-c32-repair-5828804'
OLD=ROOT/'light-light126-c32-91135f6'
MANIFEST='321c38f06fe155e491bcb580703eb5fdc96755f4bf4876d7c5545c6ae3b0dd07'
OLD_MANIFEST='d877234086f471acb3c7f4ea0c69bb280606d6bbb45fdd212e8bf30366b316c7'
INITIAL_SHA='37e1279f0c165b6fb50493c4d87edb2a994e159a90e22e48b92c41ef8ab500c0'
NETLIST='4f6e416402f2a178ec0ae0494fab1cddc53d7cf9113ac19990e108580b47c1dc'
SYNTHESIS='78268481a2fc203ae27102239ac9cdfcf83fdac3fef40dd08c8e1e2e2ef878e5'
TOOLS=Path('/tmp/s4_21usr_c32_archiveops01_20261117')
EXPORT=ROOT/'c32_repaired_export_review03/state.json'
FINISH=BUNDLE/'runs/c32_finish_repair04'
BACKUPS=Path('/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109/backups')
HELPER_NAMES=('c32_archive_runtime.py','c32_archive_capacity.py','c32_repaired_archive_contract.py')


def sha(path):
    value=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for data in iter(lambda:stream.read(4*1024**2),b''):value.update(data)
    return value.hexdigest()


def read(path):return json.loads(Path(path).read_text())
def need(ok,message):
    if not ok:raise ValueError(message)


def save_new(path,value):
    with Path(path).open('x') as stream:
        json.dump(value,stream,indent=2,sort_keys=True);stream.write('\n')
        stream.flush();os.fsync(stream.fileno())


def preflight():
    need(sha(BUNDLE/'manifest.json')==MANIFEST and sha(OLD/'manifest.json')==OLD_MANIFEST,
         'Frozen C32 bundles changed')
    export=read(EXPORT);finish=read(FINISH/'state.json')
    initial=read(OLD/'runs/c32_initial03/state.json')
    need(sha(OLD/'runs/c32_initial03/state.json')==INITIAL_SHA,
         'Original unchanged RTL qualification changed')
    need(export.get('status')=='facts_joined_manual_conclusion_required' and export.get('finished') and
         finish.get('status')=='reports_ready_review_required' and finish.get('finished'),
         'Complete the repaired queue and model review before copying')
    for state in (export,finish,initial):
        need(type(state.get('pid')) is int and not Path('/proc/%d'%state['pid']).exists(),
             'C32 queue or exporter is still active')
    waiter=read(ROOT/'c32_finish04_export_wait_launch.json')
    need(type(waiter.get('pid')) is int and not Path('/proc/%d'%waiter['pid']).exists(),
         'Export waiter still owns a log in the source runtime')
    report=BUNDLE/'runs/c32_report_repair03/c32_report/report.json'
    snapshot=ROOT/'c32_repaired_export_review03/model_review_snapshot.json'
    need(export['report']==str(report) and export['snapshot']==str(snapshot) and
         sha(report)==export['report_sha256'] and sha(snapshot)==export['snapshot_sha256'],
         'Wrong repaired report or model snapshot')
    need(read(report)['netlist_sha256']==NETLIST and
         finish['synthesis']==dict(run=str(BUNDLE/'runs/c32_repair03/c32_synth'),sha256=SYNTHESIS),
         'Report or finish uses another final netlist')
    return export


def imports(expected_tools_sha):
    sys.dont_write_bytecode=True
    need(sha(TOOLS/'tools.json')==expected_tools_sha,'Archive helper manifest changed')
    hashes=read(TOOLS/'tools.json')
    need(set(hashes)==set(HELPER_NAMES) and all(sha(TOOLS/n)==h for n,h in hashes.items()),
         'Archive helper bytes changed')
    sys.path[:0]=[str(TOOLS),str(BUNDLE/'workspaces/arch03/scripts')]
    import c32_archive_runtime as archive
    import c32_repaired_archive_contract as repaired
    need(Path(archive.__file__).resolve()==TOOLS/'c32_archive_runtime.py' and
         Path(repaired.__file__).resolve()==TOOLS/'c32_repaired_archive_contract.py',
         'Wrong repaired archive imports')
    files=read(BUNDLE/'manifest.json')['files'];identities={}
    for module in list(sys.modules.values()):
        name=getattr(module,'__file__',None)
        if not name:continue
        p=Path(name).resolve()
        if p.parent==TOOLS and p.name in hashes:
            need(sha(p)==hashes[p.name],'Changed standalone archive helper');identities[str(p)]=sha(p)
        elif BUNDLE in p.parents:
            key=p.relative_to(BUNDLE).as_posix()
            need(key in files and sha(p)==files[key],'Unbound frozen C32 dependency');identities[str(p)]=sha(p)
    need(all(str(TOOLS/n) in identities for n in HELPER_NAMES),'Archive dependency missing')
    return archive,repaired,identities


def worker(control,request_sha,tools_sha):
    control=Path(control).resolve()
    need(control.parent==Path('/tmp') and control.name.startswith('s4_21usr_c32_archive01_') and
         Path.cwd()==control and Path(__file__).resolve()==control/'worker.py',
         'Archive worker must run outside source runtime')
    preflight();need(sha(control/'request.json')==request_sha,'Archive request changed')
    archive,repaired,identities=imports(tools_sha);launch=read(control/'launch.json')
    need(launch['loaded_dependencies']==identities and launch['worker_sha256']==sha(__file__),
         'Archive worker identity changed')
    try:
        result=archive.archive(read(control/'request.json'))
        need(all(sha(p)==h for p,h in identities.items()) and sha(control/'request.json')==request_sha,
             'Archive dependencies changed')
        save_new(control/'result.json',result)
        print('C32_REPAIRED_COPY_VERIFIED',result['archive_sha256'],result['archive_bytes'],flush=True)
    except BaseException as error:
        save_new(control/'failed.json',dict(error=str(error),source_deleted=False));raise


def launch(tools_sha):
    export=preflight();archive,repaired,identities=imports(tools_sha)
    stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M')
    control=Path('/tmp')/('s4_21usr_c32_archive01_'+stamp)
    destination=BACKUPS/('c32-runtime-'+stamp+'-repair03-copy01')
    need(not control.exists() and not destination.exists(),'Preserve previous copy attempts')
    request=dict(schema=repaired.SCHEMA,storage_profile='copy_only_512MiB',runtime_root=str(ROOT),
        bundle=str(BUNDLE),bundle_manifest_sha256=MANIFEST,runtime_evidence=[[str(OLD),OLD_MANIFEST]],
        destination=str(destination),initial=dict(queue=str(OLD/'runs/c32_initial03'),state_sha256=INITIAL_SHA),
        finish=dict(queue=str(FINISH),state_sha256=sha(FINISH/'state.json')),
        lock_wait_driver=str(ROOT/'c32_finish04_driver.py'),
        report_run=str(Path(export['report']).parent),report_sha256=export['report_sha256'])
    repaired.evidence(request,BUNDLE)
    control.mkdir(mode=0o700);entry=control/'worker.py'
    with entry.open('xb') as stream:stream.write(Path(__file__).read_bytes())
    save_new(control/'request.json',request)
    command=[sys.executable,'-B','-u',str(entry),'--worker',str(control),sha(control/'request.json'),tools_sha]
    save_new(control/'launch.json',dict(command=command,loaded_dependencies=identities,
        worker_sha256=sha(entry),export_state_sha256=sha(EXPORT),source_launcher_sha256=sha(__file__),
        source_deleted=False,stage_accepted=False,storage_profile='copy_only_512MiB'))
    preflight()
    with (control/'archive.log').open('x') as log:
        child=subprocess.Popen(command,cwd=str(control),stdin=subprocess.DEVNULL,
            stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    save_new(control/'process.json',dict(pid=child.pid,destination=str(destination),command=command,
        started=datetime.datetime.now().isoformat()))
    print('C32_REPAIRED_COPY_STARTED',child.pid,str(control),str(destination),flush=True)


if __name__=='__main__':
    if len(sys.argv)==5 and sys.argv[1]=='--worker':worker(*sys.argv[2:])
    else:
        need(len(sys.argv)==3 and sys.argv[1]=='--tools-sha256','Explicit helper manifest SHA required')
        launch(sys.argv[2])
