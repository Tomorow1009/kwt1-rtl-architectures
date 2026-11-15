"""Three fresh P80 ASIC14 runs, one original shared-lock owner throughout."""
import datetime,json,os,shutil,sys
from pathlib import Path

ROOT=Path('/tmp/s4_21usr_p80_20261116_0315')
BUNDLE=ROOT/'light-light126-p80-142fae2'
MANIFEST='7017da04075aea98b7a9dfe414e41621d3974fb43709d542d42ac6b0f43920fc'
sys.path.insert(0,str(BUNDLE/'workspaces/arch03/scripts'))
import server_run as common
import p80_paths,p80_soc,n1_process


def main():
    assert common.ROOT==BUNDLE and common.sha(BUNDLE/'manifest.json')==MANIFEST
    cfg=p80_paths.configure(json.loads((BUNDLE/'handoff/team/server_config.json').read_text()),BUNDLE,ROOT,MANIFEST)
    packaged=common.inputs();dep='workspaces/arch03/scripts/n1_process.py'
    assert Path(n1_process.__file__).resolve()==BUNDLE/dep and common.sha(BUNDLE/dep)==packaged['files'][dep]
    assert callable(getattr(n1_process.ProcessLedger,'register_stage_session',None))
    assert shutil.disk_usage(str(ROOT)).free>20*1024**3
    parent=BUNDLE/'runs/p80_sweep04_coordinator'
    assert not parent.exists() and not (ROOT/'p80_sweep04.json').exists()
    queue=dict(schema='p80-continuous-original-lock-depth-sweep-v1',pid=os.getpid(),
        status='starting',started=datetime.datetime.now().isoformat(),current=None,completed=[],
        controller_sha256=common.sha(Path(__file__)),source_manifest_sha256=MANIFEST)
    save=lambda:common.save(ROOT/'p80_sweep04.json',queue)
    save()
    ledger=n1_process.ProcessLedger(common,Path(cfg['server_root'])/'.arch02_team_lock',parent)
    ledger.acquire()
    try:
        parent.mkdir();ledger.initialize();queue['status']='running';save()
        for depth in (4,2,8):
            if (ROOT/'p80_sweep04.stop').exists():
                queue['status']='stopped_between_stages';break
            session=BUNDLE/'runs'/('p80_fixed_d%d_04'%depth);run=session/'p80_soc'
            assert not session.exists();run.mkdir(parents=True);ledger.register_stage_session(session)
            p80_paths.allowed_run(run,cfg,'P80 depth14 output')
            common.save(run/'runtime_storage_receipt.json',p80_paths.receipt(cfg))
            record=dict(status='running',pid=os.getpid(),started=datetime.datetime.now().isoformat(),run=str(run),
                coordinator=str(parent),controller_sha256=queue['controller_sha256'])
            state=dict(schema='arch03-p80-server-state-v1',stages={'p80_soc':record})
            common.save(session/'state.json',state)
            queue['current']=dict(session=session.name,depth=depth,process_ledger=str(ledger.ledger));save()
            try:
                fw=BUNDLE/('firmware' if depth==4 else 'firmware_d%d'%depth)
                cases=['extremes','rounding']+['layer_%02d'%i for i in range(1,13)]
                report=p80_soc.verify(cfg,run,Path('/storage2/2026contest/server4/s4_21usr/Desktop/e203_hbirdv2-master'),cases,ledger.call,firmware=fw)
                common.inputs();p80_paths.recheck(cfg)
                report['runtime_storage']=dict(receipt_sha256=common.sha(run/'runtime_storage_receipt.json'),
                    durable_archive_required=True,temporary_storage_is_final_delivery=False)
                common.save(run/'summary.json',report)
                record.update(status='passed',summary_sha256=common.sha(run/'summary.json'))
                queue['completed'].append(dict(session=session.name,depth=depth,cases=14,
                    summary_sha256=record['summary_sha256'],cycles=[row['task_window']['cycles'] for row in report['cases']]))
            except BaseException as error:
                record.update(status='failed',error=str(error));raise
            finally:
                record['finished']=datetime.datetime.now().isoformat();common.save(session/'state.json',state)
            queue['current']=None;save()
        else:queue['status']='completed'
    except BaseException as error:
        queue.update(status='failed',error=str(error));raise
    finally:
        ledger.release();queue['finished']=datetime.datetime.now().isoformat();save()


if __name__=='__main__':main()
