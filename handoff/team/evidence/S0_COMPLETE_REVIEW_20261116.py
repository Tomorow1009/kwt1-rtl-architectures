"""After the existing export, collect S0 connectivity and join review facts.

No synthesis, RTL change, automatic acceptance, archive or deletion. One DC
query uses the existing ProcessLedger/team lock; later steps only read files.
"""
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path('/tmp/s4_21usr_t80_20261115_1830')
BUNDLE=ROOT/'light-light126-t80-s0-66b9496'
MANIFEST='2afb9a79e600e4bd1a0493699b50d463f7df8ebef666d99290cde2efbf0426b4'
OPS=ROOT/'ops-66b9496'
REVIEW=ROOT/'ops-review-e516e4c'
BUILDER=OPS/'S0_BUILD_CONNECTION_REQUEST_20261116.py'
CONTROL=OPS/'s0_review01_control'
EXPORT=OPS/'s0_export01_control/result.json'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text())
def now():return datetime.datetime.now().isoformat()


def save(path,value):
    with Path(path).open('x') as f:
        json.dump(value,f,indent=2,sort_keys=True);f.write('\n');f.flush();os.fsync(f.fileno())


def run(name,command):
    save(CONTROL/(name+'_command.json'),command)
    with (CONTROL/(name+'.log')).open('x') as log:
        child=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT)
        save(CONTROL/(name+'_process.json'),dict(pid=child.pid,started=now(),command=command))
        code=child.wait()
    save(CONTROL/(name+'_exit.json'),dict(returncode=code,finished=now()))
    assert code==0,name+' failed; preserve this attempt'


def main(expected_builder):
    assert sha(BUILDER)==expected_builder and sha(BUNDLE/'manifest.json')==MANIFEST
    deployed=read(REVIEW/'receipt.json')
    assert deployed['source_commit']=='e516e4c' and deployed['base_manifest_sha256']==MANIFEST
    assert all(sha(REVIEW/n)==v for n,v in deployed['files'].items())
    CONTROL.mkdir()
    save(CONTROL/'identity.json',dict(pid=os.getpid(),started=now(),source_sha256=sha(__file__),
        builder_sha256=expected_builder,review_receipt_sha256=sha(REVIEW/'receipt.json'),
        waits_existing_export=True,no_automatic_acceptance=True,no_cleanup=True))
    try:
        print('S0_REVIEW_WAIT_EXISTING_EXPORT',now(),flush=True)
        while not EXPORT.exists():
            state=read(BUNDLE/'runs/s0_finish03/state.json')
            assert state['status']!='failed','Original finish queue failed'
            owner=read(OPS/'s0_export01_control/identity.json')['pid']
            cmd=Path('/proc/%d/cmdline'%owner)
            try:active=str(OPS/'S0_EXPORT_AFTER_FINISH_20261115.py').encode() in cmd.read_bytes().split(b'\x00')
            except FileNotFoundError:active=False
            assert active or EXPORT.exists(),'Export owner disappeared/reused'
            time.sleep(20)
        result=read(EXPORT);assert result['status']=='export_and_unknown_inventory_ready'
        assert sha(BUILDER)==expected_builder
        run('request',[sys.executable,'-B',str(BUILDER)])
        request=OPS/'s0_unknown_connections01_request.json'
        run('connections',[sys.executable,'-B','-u',str(BUNDLE/'workspaces/arch03/scripts/saif_unknown_connections.py'),
            '--request',str(request),'--request-sha256',sha(request)])
        linked=BUNDLE/'runs/s0_unknown_connections01/s0_unknown_s0/summary.json'
        alias=CONTROL/'alias_review.json'
        run('aliases',[sys.executable,'-B','-u',str(BUNDLE/'workspaces/arch03/scripts/saif_unknown_alias_review.py'),
            '--summary',str(linked),'--sha256',sha(linked),'--output',str(alias)])
        joined=CONTROL/'snapshot_request.json'
        save(joined,dict(schema='s0-model-review-request-v1',
            report=dict(path=result['report'],sha256=result['report_sha256']),
            connections=dict(path=str(linked),sha256=sha(linked)),
            aliases=dict(path=str(alias),sha256=sha(alias))))
        snapshot=CONTROL/'model_review_snapshot.json'
        assert all(sha(REVIEW/n)==v for n,v in deployed['files'].items())
        # These separate operations modules must import the frozen bundle's tools.
        code='import sys,runpy;sys.path[:0]=%r;sys.argv=%r;runpy.run_path(%r,run_name="__main__")'%(
            [str(REVIEW),str(BUNDLE/'workspaces/arch03/scripts')],
            [str(REVIEW/'s0_model_review_snapshot.py'),'--request',str(joined),
             '--request-sha256',sha(joined),'--output',str(snapshot)],str(REVIEW/'s0_model_review_snapshot.py'))
        run('snapshot',[sys.executable,'-B','-u','-c',code])
        save(CONTROL/'result.json',dict(status='facts_joined_manual_conclusion_required',finished=now(),
            snapshot=str(snapshot),snapshot_sha256=sha(snapshot),connections_sha256=sha(linked),
            aliases_sha256=sha(alias),report_sha256=result['report_sha256'],stage_accepted=False))
        print('S0_REVIEW_FACTS_READY',sha(snapshot),'stage_accepted=false',flush=True)
    except BaseException as error:
        save(CONTROL/'result.json',dict(status='failed_preserved',error=str(error),finished=now(),stage_accepted=False));raise


if __name__=='__main__':
    assert len(sys.argv)==2,'Pass committed builder SHA256'
    main(sys.argv[1])
