"""Launch one frozen T64 remainder; preserve existing stages and old sources."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,sys

ROOT=Path('/tmp/s4_21usr_t64_20261115_1510')
BUNDLE=ROOT/'light-light126-t64-resume-9934df8'
OPS=ROOT/'ops-9934df8'
OLD=ROOT/'light-light126-t64-resume-b9155b4'
PROJECT=Path('/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109')
MANIFEST='32f48cc22391667881476ba6bf6ad7e26b69c6693e19182fb8688a69ac596c68'
OLD_MANIFEST='c80e6f3355832f6a072cc25353c94f5e8825e49ca274b82510361b8201170804'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
read=lambda p:json.loads(Path(p).read_text())
dump=lambda v:(json.dumps(v,sort_keys=True,indent=2)+'\n').encode()


def main():
    assert sha(BUNDLE/'manifest.json')==MANIFEST and sha(OLD/'manifest.json')==OLD_MANIFEST
    script=BUNDLE/'workspaces/arch03/scripts/t64_singlelock_queue.py'
    assert sha(script)==read(BUNDLE/'manifest.json')['files']['workspaces/arch03/scripts/t64_singlelock_queue.py']
    assert not (BUNDLE/'runs/t64_serial01').exists()
    lock=PROJECT.parent/'.arch02_team_lock';assert not lock.exists(),'Existing team owner'
    for pid in (268175,268189):
        assert not Path('/proc/%d'%pid).exists(),'Original process identity must be resolved'
    own=subprocess.check_output(['ps','-u','s4_21usr','-o','comm=']).decode().splitlines()
    assert not any(x.strip() in ('dc_shell','pt_shell','simv','vcs','vcs1','vcs2') for x in own),'Active own EDA'
    assert shutil.disk_usage('/tmp').free>12*1024**3
    request=dict(schema='t64-singlelock-remainder-v1',bundle=str(BUNDLE),bundle_manifest_sha256=MANIFEST,
        queue_sha256=sha(script),runtime_root=str(ROOT),runtime_evidence=[[str(OLD),OLD_MANIFEST]],
        asic=dict(run=str(OLD/'runs/t64_soc03/t64_soc'),
            sha256='8eb6e9822817c2bcdba325b977f7d27e381b8f2b0b2eb6f0331049a474f472e2'),
        platform=str(PROJECT.parents[1]/'e203_hbirdv2-master'),dataset=str(PROJECT.parent/'hex_short_all'),
        archive='/tmp/s4_21usr_n1_20261113_0210/n1_precision_inputs_20261113_0840/n1-recovered-float100-20261113.zip',
        archive_sha256='5df11251821d2d36e85e07c8a171195d9d2ed2d4084a979519d23f6df7d683e2',
        numpy_root='/tmp/s4_21usr_n1_20261113_0210/n1_numpy1195_20261113_0905',
        qualification_run=str(PROJECT/'bundles/light-light126-systolic-b-v3-20261112_114355-ced0e139a01e/runs/systolic_b_r4_crosscheck02/native_saif_r4_crosscheck'),
        qualification_sha256='a0a9bc6280e7fe5f35b666535157700aac1d9c0b4490873b6199ba9b5c662d26')
    assert Path(request['platform']).is_dir() and Path(request['dataset']).is_dir()
    req=OPS/'singlelock_request02.json'
    with req.open('xb') as f:f.write(dump(request))
    # Only identical frozen T64 input duplicates. Every old path and byte stays.
    # This is conditional storage deduplication, never waveform/result deletion.
    if shutil.disk_usage(str(PROJECT)).free<4*1024**2:
        old=PROJECT/'bundles/light-light126-t64-v4-65d2507-delta01'
        keep=old.with_name('light-light126-t64-v4-65d2507-fix02')
        assert old.resolve()==old and keep.resolve()==keep and not (old/'runs').exists()
        assert sha(keep/'manifest.json')=='6632a4f266d48f50fd8a9e542cb6e03f05653d7ade3153903b38c3282c3339c1'
        a=read(old/'manifest.json')['files'];b=read(keep/'manifest.json')['files'];rows=[]
        for name,value in sorted(a.items()):
            p=old/name;q=keep/name
            assert p.resolve()==p and q.resolve()==q and p.stat().st_uid==q.stat().st_uid==os.getuid()
            assert value==b[name] and sha(p)==sha(q)==value
            if p.stat().st_ino==q.stat().st_ino or p.stat().st_size<4096:continue
            rows.append(dict(path=str(p),retained_source=str(q),sha256=value,bytes=p.stat().st_size,
                             prior_blocks_bytes=p.stat().st_blocks*512))
        receipt=OPS/'singlelock_dedup02_prepared.json'
        with receipt.open('xb') as f:f.write(dump(rows))
        done=[]
        for row in sorted(rows,key=lambda v:v['bytes'],reverse=True):
            if shutil.disk_usage(str(PROJECT)).free>=4*1024**2:break
            p=Path(row['path']);q=Path(row['retained_source']);tmp=old/'.t64-storage-link'
            assert not lock.exists() and sha(p)==sha(q)==row['sha256'] and not tmp.exists()
            os.link(str(q),str(tmp));os.replace(str(tmp),str(p))
            assert sha(p)==row['sha256'] and p.stat().st_size==row['bytes'] and p.stat().st_ino==q.stat().st_ino
            done.append(row)
        with (OPS/'singlelock_dedup02_complete.json').open('xb') as f:f.write(dump(done))
        print('PATHS_AND_BYTES_PRESERVED',len(done),'SHARED_FREE',shutil.disk_usage(str(PROJECT)).free,flush=True)
    assert not lock.exists()
    logfile=OPS/'t64_serial01.log'
    with logfile.open('x') as stream:
        child=subprocess.Popen([sys.executable,'-B','-u',str(script),'--request',str(req),
            '--request-sha256',sha(req),'--session','t64_serial01'],cwd=str(OPS),
            stdin=subprocess.DEVNULL,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
    print('T64_SINGLELOCK_LAUNCHED',child.pid,'REQUEST_SHA',sha(req),'LOG',str(logfile),flush=True)


if __name__=='__main__':main()
