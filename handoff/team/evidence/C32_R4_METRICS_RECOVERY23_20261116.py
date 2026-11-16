"""Archive/read back only 578 generated files from one completed R4 metrics run.

Preserve actual outputs, logs, metadata, source, all protected versions and
both archive copies. Then attempt the new C32 queue with an actual metadata
write probe; no arbitrary large shared-volume reserve or old-lock takeover.
"""
import base64
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile

ROOT=Path('/tmp/s4_21usr_c32_20261116_2010')
HELPER=ROOT/'r4_archive21_fixed.py'
HELPER_SHA='2a28e61f85792f4f0d2fc2655950feaeb34a3a9e728ca108042f982dace233c4'
OUT=ROOT/'r4_metrics_generated_recovery23'
SUMMARY='bb0ee4cf23b31730d72c196bfc5101f3d2f49e7d1dea33b49e366a72de54e576'


def need(ok,message):
    if not ok:raise ValueError(message)


def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(4*1024**2),b''):h.update(b)
    return h.hexdigest()


def read(p):return json.loads(Path(p).read_text())


def selected(p):return p.suffix in ('.hex','.bin','.verilog','.o','.so','.a') or p.name=='simv'


def main():
    need(os.name=='posix' and ROOT.resolve()==ROOT and ROOT.stat().st_mode&0o777==0o700 and
         not OUT.exists(),'Fresh private operation required')
    need(sha(HELPER)==HELPER_SHA,'Archive/process helper changed')
    spec=importlib.util.spec_from_file_location('r4_scope23',str(HELPER))
    h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
    need(sha(h.BASE)==h.BASE_SHA,'Process helper changed')
    base=h.load('r4_process23',h.BASE)
    need(sha(base.BUNDLE/'manifest.json')==base.MANIFEST_SHA,'Frozen inspection bundle changed')
    mf=read(base.BUNDLE/'manifest.json')['files']
    for name in ('n1_archive_runtime.py','n1_paths.py','partition_synth_contract.py'):
        rel='workspaces/arch03/scripts/'+name;need(sha(base.BUNDLE/rel)==mf[rel],'Changed dependency')
    sys.path.insert(0,str(base.BUNDLE/'workspaces/arch03/scripts'));import n1_archive_runtime as ar
    run=h.PROJECT/'bundles/light-light126-icb32-r4-20261111_043048-96443c284a1c/runs/icb32_r4_finish01_metrics14/icb32_soc'
    lock=h.PROJECT.parent/'.arch02_team_lock';obs=base.idle(ar,lock,[run])
    need(sha(run/'summary.json')==SUMMARY,'Wrong completed metrics14 summary')
    summary=read(run/'summary.json');stage=read(run.parent/'state.json')['stages']['icb32_soc']
    need(summary['status']=='passed' and summary['asic_cpu_verified'] and len(summary['cases'])==14 and
         stage['status']=='passed' and stage['summary_sha256']==SUMMARY,'Metrics run not passed')
    need(not (ROOT/'light-light126-c32-91135f6/runs/c32_initial03').exists(),'C32 queue already exists')
    rows={};protected={str(run.parent/'state.json'):sha(run.parent/'state.json')}
    for p in sorted(run.rglob('*')):
        if not p.is_file():continue
        st=h.stamp(p);digest=sha(p);need(h.stamp(p)==st,'Source changed while scanning')
        if selected(p):rows[p.relative_to(run).as_posix()]=dict(bytes=st['bytes'],sha256=digest,stamp=st)
        else:protected[str(p)]=digest
    need(len(rows)==578 and sum(x['bytes'] for x in rows.values())==48520513,'Exact generated scope changed')
    need(shutil.disk_usage(str(ROOT)).free>1024**3,'No staged archive margin')
    base.idle(ar,lock,[run]);OUT.mkdir(mode=0o700)
    manifest=dict(source_root=str(run),files=rows,protected=protected,source_sha256=sha(__file__))
    ar.save(OUT/'manifest.json',manifest);packed=OUT/'generated-inputs.tar.gz'
    with tarfile.open(str(packed),'x:gz',compresslevel=1) as tar:
        for name,v in sorted(rows.items()):
            need(h.stamp(run/name)==v['stamp'],'Source changed before archive')
            tar.add(str(run/name),arcname=name,recursive=False)
    with packed.open('rb') as f:os.fsync(f.fileno())
    seen=set()
    with tarfile.open(str(packed),'r:gz') as tar:
        for member in tar:
            need(member.isfile() and member.name in rows and member.name not in seen,'Unexpected archive member')
            with tar.extractfile(member) as f:digest,count=h.digest(f)
            v=rows[member.name];need(digest==v['sha256'] and count==v['bytes'],'Archive readback differs')
            seen.add(member.name)
    need(seen==set(rows),'Incomplete archive')
    state=dict(status='full_archive_verified_source_preserved',members_verified=len(rows),source_bytes=48520513,
        archive=str(packed),archive_bytes=packed.stat().st_size,archive_sha256=sha(packed),
        manifest_sha256=sha(OUT/'manifest.json'),removed_files=0,removed_bytes=0,
        protected_T80_modified=False,old8_modified=False,p80_modified=False,c80_modified=False,
        results_modified=False,process_observation=obs)
    ar.save(OUT/'archive_receipt.json',state);ar.save(OUT/'state.json',state)
    try:
        need(all(sha(p)==v for p,v in protected.items()),'Protected result changed')
        with (OUT/'removal_journal.jsonl').open('x') as journal:
            for i,(name,v) in enumerate(sorted(rows.items())):
                if i%64==0:base.idle(ar,lock,[run])
                p=run/name;need(run in p.parents and p.resolve()==p and h.stamp(p)==v['stamp'] and
                               sha(p)==v['sha256'] and not lock.exists(),'Generated duplicate changed or busy')
                journal.write(json.dumps(dict(action='remove_intent',path=name,sha256=v['sha256']))+'\n')
                journal.flush();os.fsync(journal.fileno());p.unlink();ar.sync_dir(p.parent)
                state['removed_files']+=1;state['removed_bytes']+=v['bytes']
                journal.write(json.dumps(dict(action='removed',path=name))+'\n')
                if i%64==0:journal.flush();os.fsync(journal.fileno());ar.save(OUT/'state.json',state)
            journal.flush();os.fsync(journal.fileno())
        need(all(sha(p)==v for p,v in protected.items()) and sha(packed)==state['archive_sha256'],
             'Retained result or archive changed')
        state.update(status='verified_generated_duplicates_removed_archive_retained',finished=ar.now(),
                     free_after=shutil.disk_usage(str(h.PROJECT)).free)
        ar.save(OUT/'state.json',state)
        target=h.PROJECT/'backups/r4-metrics14-generated-20261116_2216';need(not target.exists(),'Existing destination')
        target.mkdir(mode=0o700)
        for source in (packed,OUT/'manifest.json',OUT/'archive_receipt.json'):
            dest=target/source.name
            with source.open('rb') as src,dest.open('xb') as dst:
                shutil.copyfileobj(src,dst,4*1024**2);dst.flush();os.fsync(dst.fileno())
            need(sha(dest)==sha(source) and dest.stat().st_size==source.stat().st_size,'Persistent copy differs')
        ar.sync_dir(target);ar.save(OUT/'persistent_copy.json',dict(status='verified',directory=str(target),
            archive_sha256=state['archive_sha256'],manifest_sha256=state['manifest_sha256']))
        print('R4_RECOVERY23_PERSISTED',state['removed_files'],state['removed_bytes'],flush=True)
        old=ROOT/'c32fix_launch03_metadata_tool.py'
        need(sha(old)=='60da852cc133dbb5001f9f15d273f487a455aec9719e7fb96ce9d189a9b122ee','Changed metadata launcher')
        raw=old.read_bytes().replace(b'c32_lock_metadata_probe_20261116_2210',b'c32_lock_metadata_probe_20261116_2216')
        raw=raw.replace(b'c32_initial03_metadata_probe.json',b'c32_initial03_metadata_probe23.json')
        need(hashlib.sha256(raw).hexdigest()=='f40276324f849b6a9eff62bb8f1841fb47487c424c57c696924d0d2f8b8918c2',
             'Corrected capacity-launcher differs from reviewed source')
        tool=ROOT/'c32fix_launch03_recovered_tool.py'
        with tool.open('xb') as f:f.write(raw)
        command=[sys.executable,'-B',str(tool),'--manifest-sha256',
                 read(ROOT/'light-light126-c32-91135f6.prepared.json')['manifest_sha256']]
        code=subprocess.call(command);ar.save(OUT/'followup.json',dict(command=command,returncode=code))
        need(code==0,'C32 post-cleanup launch failed; preserve state, never repeat deletion')
    except BaseException as exc:
        state.update(error=str(exc),stopped=ar.now());ar.save(OUT/'state.json',state);raise


if __name__=='__main__':main()
