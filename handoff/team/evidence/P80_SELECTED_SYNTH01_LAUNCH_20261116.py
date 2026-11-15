"""Map the smallest P80 depth within 1% of all measured depths, provisionally.

Area is NOT assumed: this launches that candidate's fresh synthesis only.
No final depth selection or next hardware stage is authorized by this script.
"""
import datetime
from fractions import Fraction
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys

ROOT=Path('/tmp/s4_21usr_p80_20261116_0315')
BUNDLE=ROOT/'light-light126-p80-8543440'
FUNCTIONAL=ROOT/'light-light126-p80-142fae2'
FUNCTIONAL_MANIFEST='7017da04075aea98b7a9dfe414e41621d3974fb43709d542d42ac6b0f43920fc'
PAYLOAD_SHA='5915a15ab41d6601684684ecce16272316fa303e645f8732740dc04c3ffd0e89'
BUDGET=Path('/tmp/s4_21usr_t80_20261115_1830/light-light126-t80-s0-a5f138e/runs/s0_synth08/t80_s0_synth')
sys.path.insert(0,str(BUNDLE/'workspaces/arch03/scripts'))
import server_run as common
import p80_paths
import p80_depth_selection as selection
import p80_eda_server


def main():
    assert common.ROOT==BUNDLE
    payload=ROOT/'payload_8543440.json'
    assert common.sha(payload)==PAYLOAD_SHA
    prepared=json.loads((ROOT/(BUNDLE.name+'.prepared.json')).read_text())
    manifest=prepared['manifest_sha256']
    assert prepared['bundle']==str(BUNDLE) and prepared['source_preserved'] is True
    assert common.sha(BUNDLE/'manifest.json')==manifest
    assert common.sha(FUNCTIONAL/'manifest.json')==FUNCTIONAL_MANIFEST
    cfg=p80_paths.configure(json.loads((BUNDLE/'handoff/team/server_config.json').read_text()),
        BUNDLE,ROOT,manifest,[(FUNCTIONAL,FUNCTIONAL_MANIFEST)])
    common.inputs()
    queue=json.loads((ROOT/'p80_sweep05.json').read_text())
    assert queue['status']=='completed' and queue['current'] is None
    assert len(queue['completed'])==3 and {row['depth'] for row in queue['completed']}=={2,4,8}
    lock=Path(cfg['server_root'])/'.arch02_team_lock'
    assert not lock.exists(),'Original queue must finish and release its own lock'
    assert shutil.disk_usage(str(ROOT)).free>20*1024**3
    rows=[]
    for item in queue['completed']:
        assert item['session']=='p80_fixed_d%d_05'%item['depth'] and item['cases']==14
        run=FUNCTIONAL/'runs'/item['session']/'p80_soc'
        p80_paths.allowed_run(run,cfg)
        row=selection.summarize(run,item['summary_sha256'])
        assert row['depth']==item['depth']
        rows.append(row)
    reference=rows[0]
    for row in rows:
        assert len(row['cases'])==12
        for a,b in zip(reference['cases'],row['cases']):
            assert all(a[k]==b[k] for k in ('case','encoded_bytes','codec_sha256','layout_sha256','capture_sha256'))
        assert sorted(row['hardware'].values())==sorted(reference['hardware'].values())
        for name,want in row['hardware'].items():
            relative=Path(name).relative_to(FUNCTIONAL)
            assert common.sha(BUNDLE/relative)==want,'Fresh synthesis hardware differs from measured candidate'
    best=min(row['cycles_sum'] for row in rows)
    near=[row for row in rows if Fraction(best,row['cycles_sum'])>=Fraction(99,100)]
    selected=min(near,key=lambda row:row['depth']);depth=selected['depth']
    session='p80_synth_d%d_01'%depth
    assert not (BUNDLE/'runs'/session).exists()
    result=ROOT/'p80_selected_synth01.json'
    assert not result.exists()
    state=dict(schema='p80-provisional-performance-candidate-synthesis-v1',pid=os.getpid(),
        started=datetime.datetime.now().isoformat(),status='starting',selected_depth=depth,
        performance_candidates=rows,throughput_fraction_of_best=str(Fraction(best,selected['cycles_sum'])),
        area_qualified=False,stage_accepted=False,controller_sha256=common.sha(Path(__file__)),
        operations_manifest_sha256=manifest,depth_sweep_sha256=common.sha(ROOT/'p80_sweep05.json'),
        session=session,protected_T80_modified=False,old8_modified=False)
    common.save(result,state)
    firmware=BUNDLE/('firmware' if depth==4 else 'firmware_d%d'%depth)
    try:
        sys.argv=['p80_eda_server.py','synth','--session',session,'--firmware-root',str(firmware),
            '--budget-origin',str(BUDGET),'--runtime-root',str(ROOT),'--runtime-manifest-sha256',manifest]
        state['status']='running';common.save(result,state)
        p80_eda_server.main()
        run=BUNDLE/'runs'/session/'p80_synth'
        receipt=json.loads((run.parent/'state.json').read_text())['stages']['p80_synth']
        assert receipt['status']=='passed' and receipt['summary_sha256']==common.sha(run/'summary.json')
        state.update(status='synthesis_completed_review_pending',summary_sha256=receipt['summary_sha256'],run=str(run))
    except BaseException as error:
        state.update(status='failed',error=str(error));raise
    finally:
        state['finished']=datetime.datetime.now().isoformat();common.save(result,state)


if __name__=='__main__':main()
