"""Resume after diagnostic-only row fix; explicitly retain passed ASIC14/240."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,sys

ROOT=Path('/tmp/s4_21usr_t64_20261115_1510')
BUNDLE=ROOT/'light-light126-t64-resume-3552163'
OPS=ROOT/'ops-3552163'
BATCH_BUNDLE=ROOT/'light-light126-t64-resume-9934df8'
ASIC_BUNDLE=ROOT/'light-light126-t64-resume-b9155b4'
MANIFEST='81f861731d29df3252c775e8bc1dcab8628b2f2f79c71fa504827c9e7d2ed763'
BATCH_MANIFEST='32f48cc22391667881476ba6bf6ad7e26b69c6693e19182fb8688a69ac596c68'
ASIC_MANIFEST='c80e6f3355832f6a072cc25353c94f5e8825e49ca274b82510361b8201170804'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
read=lambda p:json.loads(Path(p).read_text())
dump=lambda v:(json.dumps(v,sort_keys=True,indent=2)+'\n').encode()

def main():
    for p,h in ((BUNDLE,MANIFEST),(BATCH_BUNDLE,BATCH_MANIFEST),(ASIC_BUNDLE,ASIC_MANIFEST)):
        assert sha(p/'manifest.json')==h
    previous=read(BATCH_BUNDLE/'runs/t64_serial02/state.json')
    assert previous['status']=='failed' and previous['stage']=='t64_contention'
    assert not Path('/proc/%d'%previous['pid']).exists(),'Resolve old queue process identity first'
    own=subprocess.check_output(['ps','-u','s4_21usr','-o','comm=']).decode().splitlines()
    assert not any(x.strip() in ('dc_shell','pt_shell','simv','vcs','vcs1','vcs2') for x in own)
    request=read(ROOT/'ops-9934df8/singlelock_request03.json')
    script=BUNDLE/'workspaces/arch03/scripts/t64_singlelock_queue.py'
    batch=BATCH_BUNDLE/'runs/t64_serial02_batch20/t64_batch20'
    row=read(batch.parent/'state.json')['stages']['t64_batch20'];digest=sha(batch/'summary.json')
    assert row['status']=='passed' and row['summary_sha256']==digest
    assert digest=='50c42478461985dfd33f0324aa464dc3d775388d6e54e3de4f06c8d46f190d16'
    assert previous['batch_reference']==dict(run=str(batch),sha256=digest)
    assert sha(script)==read(BUNDLE/'manifest.json')['files']['workspaces/arch03/scripts/t64_singlelock_queue.py']
    request.update(bundle=str(BUNDLE),bundle_manifest_sha256=MANIFEST,queue_sha256=sha(script),
        runtime_evidence=[[str(ASIC_BUNDLE),ASIC_MANIFEST],[str(BATCH_BUNDLE),BATCH_MANIFEST]],
        prior_batch=dict(run=str(batch),sha256=digest))
    lock=Path('/storage2/2026contest/server4/s4_21usr/Desktop/IC/.arch02_team_lock')
    assert not lock.exists() and not (BUNDLE/'runs/t64_serial03').exists()
    assert shutil.disk_usage('/tmp').free>12*1024**3
    assert shutil.disk_usage(str(lock.parent)).free>1024**2,'Need original shared lock space'
    req=OPS/'singlelock_request04.json'
    with req.open('xb') as f:f.write(dump(request))
    log=OPS/'t64_serial03.log'
    with log.open('x') as stream:
        child=subprocess.Popen([sys.executable,'-B','-u',str(script),'--request',str(req),
            '--request-sha256',sha(req),'--session','t64_serial03'],cwd=str(OPS),
            stdin=subprocess.DEVNULL,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
    print('T64_REPAIR_LAUNCHED',child.pid,'REQUEST_SHA',sha(req),'REUSED_ASIC240',digest,flush=True)

if __name__=='__main__':main()
