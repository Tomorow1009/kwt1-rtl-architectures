"""Continue a completed B functional queue with qualified activity/power only.

Never re-runs ASIC14/1200 or gate14. Requires the actual completed queue and
R4 method qualification. Uses fresh children and the original shared lock.
"""
import argparse
import datetime
import json
from pathlib import Path
import re
import subprocess
import sys
import time
from server_run import ROOT,inputs,save
from icb32_power import stream_sha as sha
from systolic_b_finalize_queue import checked_operations,activity_request
from systolic_b_report import stage,require
from systolic_b_saif import qualification


def read(path):return json.loads(Path(path).read_text())


def checked_file(ref,root):
    path=Path(ref['path']).resolve();path.relative_to(root)
    require(sha(path)==ref['sha256'],'Continuation input changed: '+str(path))
    return path,read(path)


def preflight(request,cfg):
    root=Path(cfg['server_root']).resolve()
    require(request['schema']=='systolic-b-power-continuation-v1','Wrong continuation schema')
    require(sha(__file__)==request['runner_sha256'],'Continuation runner changed')
    require(sha(ROOT/'manifest.json')==request['bundle_manifest_sha256'],'Wrong immutable bundle')
    qp,q=checked_file(request['functional_queue'],root)
    rp,report=checked_file(request['report_request'],root)
    require(q['status']=='reports_ready_review_required' and q['child_pid'] is None and
        q['report_request_sha256']==request['report_request']['sha256'] and rp.parent==qp.parent,
        'Original functional queue incomplete or mismatched')
    require(report['schema']=='systolic-b-report-request-v1' and report.get('power')==[] and
        'activity' not in report,'Continuation must start from functional-only report')
    refs={name:stage(report[name],kind) for name,kind in [('asic','systolic_b_soc'),
        ('batch','systolic_b_batch'),('gate','systolic_b_gate'),('synthesis','systolic_b_synth')]}
    require(refs['batch']['status']=='passed' and refs['batch']['tasks']==1200 and
        refs['batch']['checked_outputs']==30412800 and refs['batch']['failed']==0,'Own1200 incomplete')
    require(len(q['completed'])==2 and {x['stage'] for x in q['completed']}=={'systolic_b_soc','systolic_b_batch'} and
        all(report['asic' if x['stage']=='systolic_b_soc' else 'batch']==x['reference'] for x in q['completed']),
        'Report does not bind the completed functional children')
    require(refs['gate']['synthesis_summary_sha256']==report['synthesis']['sha256'] and
        refs['gate']['firmware_sha256']==refs['asic']['compile_receipt']['firmware_manifest_sha256']==
        refs['batch']['compile_receipt']['firmware_manifest_sha256'],'Frozen gate/CPU firmware differs')
    from icb32_report import configuration_identity
    require(len({json.dumps(configuration_identity(report[k]['run']),sort_keys=True) for k in ['asic','batch','synthesis']})==1,
        'Frozen hardware differs between stages')
    method=request['qualification'];qualification(method['run'],method['sha256'],cfg)
    checked_operations(request,root)
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--request',required=True,type=Path);p.add_argument('--request-sha256',required=True)
    p.add_argument('--session',required=True);a=p.parse_args()
    require(re.fullmatch('[A-Za-z0-9_-]{1,35}',a.session),'Invalid unique session')
    require(sha(a.request)==a.request_sha256,'Continuation request changed')
    request=read(a.request);cfg=read(ROOT/'handoff/team/server_config.json');inputs()
    report=preflight(request,cfg)
    output=ROOT/'runs'/(a.session+'_queue');output.mkdir(parents=True,exist_ok=False)
    save(output/'request.json',request)
    state=dict(status='ready',pid=__import__('os').getpid(),started=datetime.datetime.now().isoformat(),
        request_sha256=a.request_sha256,runner_sha256=sha(__file__),completed=[],child_pid=None)
    save(output/'state.json',state);lock=Path(cfg['server_root'])/'.arch02_team_lock'

    def execute(kind,suffix,extra):
        session=a.session+'_'+suffix;run=ROOT/'runs'/session/kind
        require(not run.parent.exists(),'Preserve existing child; no retry in place')
        state.update(status='waiting_lock',stage=kind,session=session,child_pid=None);save(output/'state.json',state)
        while lock.exists():time.sleep(20)
        require(sha(a.request)==a.request_sha256,'Continuation request changed while waiting')
        checked_file(request['functional_queue'],Path(cfg['server_root']).resolve())
        checked_file(request['report_request'],Path(cfg['server_root']).resolve())
        inputs();ops,ops_sha=checked_operations(request,Path(cfg['server_root']).resolve())
        operation=output/(suffix+'_operation.json');require(not operation.exists(),'Operation already exists')
        save(operation,activity_request(kind,extra))
        command=[sys.executable,str(ops/'systolic_b_ops.py'),'--bundle',str(ROOT),
            '--bundle-sha256',request['bundle_manifest_sha256'],'--ops-sha256',ops_sha,
            '--stage',kind,'--session',session,'--request',str(operation),'--request-sha256',sha(operation)]
        state.update(status='running',command=command);save(output/'state.json',state)
        with (output/(suffix+'_launcher.log')).open('x') as log:
            child=subprocess.Popen(command,cwd=str(ROOT),stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT)
            state['child_pid']=child.pid;save(output/'state.json',state);code=child.wait()
        state['child_pid']=None;require(code==0,'Child failed; preserved '+str(run))
        ref=dict(run=str(run),sha256=sha(run/'summary.json'));stage(ref,kind)
        state['completed'].append(dict(stage=kind,session=session,reference=ref));save(output/'state.json',state)
        print('B_POWER_CONTINUATION_STEP_DONE',session,ref['sha256'],flush=True)
        return ref

    try:
        g=report['gate'];q=request['qualification']
        report['activity']=execute('systolic_b_saif','activity12',[
            '--gate-run',g['run'],'--gate-summary-sha256',g['sha256'],
            '--saif-qualification-run',q['run'],'--saif-qualification-sha256',q['sha256']])
        save(output/'report_request.json',report)
        activity=report['activity']
        for i in range(1,13):
            report['power'].append(execute('systolic_b_power','power_l%02d'%i,[
                '--saif-activity-run',activity['run'],'--saif-activity-sha256',activity['sha256'],
                '--cases','layer_%02d'%i]))
            save(output/'report_request.json',report)
        state.update(status='reports_ready_review_required',finished=datetime.datetime.now().isoformat(),
            report_request_sha256=sha(output/'report_request.json'),system_power_verified=False,report_exported=False)
    except BaseException as error:
        state.update(status='failed',error=str(error),finished=datetime.datetime.now().isoformat())
        report['history'].append(dict(status='failed',run=str(ROOT/'runs'/state.get('session','')),
            description='Power continuation stopped; no missing component replaced by zero: '+str(error)))
        save(output/'partial_report_request.json',report)
        raise
    finally:save(output/'state.json',state)
    print('B_POWER_CONTINUATION_COMPLETE review_required=true',flush=True)


if __name__=='__main__':main()
