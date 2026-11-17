"""Read native ICG definitions and zero-violation reports without rerunning PT."""
import argparse
import json
from pathlib import Path
import re
from partition_synth_contract import require,digest
from g32_icg_timing import parse


def review(run,expected):
    run=Path(run);p=run/'summary.json';require(digest(p)==expected,'Changed own ICG summary')
    s=json.loads(p.read_text());synth=Path(s['synthesis_run'])
    require(digest(synth/'summary.json')==s['synthesis_summary_sha256'],'Changed ICG mapping')
    mapped=json.loads((synth/'summary.json').read_text())
    require(digest(synth/'mapped.v')==s['netlist_sha256']==mapped['artifacts']['mapped.v'],'Changed final netlist')
    for name in ('clock_gating_checks.rpt','clock_gating_setup.rpt','clock_gating_hold.rpt','clock_gating_paths.tsv'):
        require(digest(run/name)==s['artifacts'][name],'Native report changed')
    paths=parse((run/'clock_gating_paths.tsv').read_text(),mapped['icg_mapping'])
    require(paths['enable_path_setup_hold_nonnegative'] and paths['static_TE_zero'],'Actual ICG paths failed')
    native=(run/'clock_gating_checks.rpt').read_text();names=[]
    require('Report : clock gating check' in native,'Wrong native definition report')
    for line in native.splitlines():
        f=line.split()
        if len(f)>=8 and f[1:3]==['E','CK']:
            require(f[0] not in names and f[7]=='High','Unexpected ICG definition')
            for number in f[3:7]:require(re.fullmatch(r'[+-]?\d+\.\d+',number),'Missing native library check')
            names.append(f[0])
    require(set(names)==set(mapped['icg_mapping']['rows']) and len(names)==paths['actual_g32_cells'],
            'Native definitions do not cover exactly all accelerator ICGs')
    for name,delay in (('clock_gating_setup.rpt','max'),('clock_gating_hold.rpt','min')):
        text=(run/name).read_text()
        require('Report : timing' in text and re.search(r'-delay_type\s+'+delay+r'\b',text) and
                re.search(r'-slack_lesser_than\s+0\.0+\b',text) and
                re.search(r'No paths with slack less than 0\.0+',text),
                'Native timing report is not the explicit zero-violation report')
    return dict(schema='g32-native-clock-gating-review-v1',icg_summary_sha256=expected,
        netlist_sha256=s['netlist_sha256'],actual_g32_cells=len(names),
        per_ICG_setup_hold_paths=2*len(names),setup_slack_ns=paths['setup_slack_ns'],
        hold_slack_ns=paths['hold_slack_ns'],static_TE_zero=True,native_definition_coverage_complete=True,
        native_negative_slack_reports_clear=True,short_native_reports_reason='PT report_timing -max_paths defaults to slack_lesser_than 0; all explicit per-ICG paths are nonnegative',
        checks_disabled=False,netlist_modified=False,energy_verified=False,physical_signoff=False,
        remaining_scope='Global disabled timing and task-mode clock coverage retained for final mapped-model review',
        inputs={str(run/n):digest(run/n) for n in ('summary.json','clock_gating_checks.rpt',
            'clock_gating_setup.rpt','clock_gating_hold.rpt','clock_gating_paths.tsv')})


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run',required=True,type=Path)
    p.add_argument('--summary-sha256',required=True);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
    result=review(a.run,a.summary_sha256)
    with a.output.open('x') as f:json.dump(result,f,sort_keys=True,indent=2);f.write('\n')
    print('G32_NATIVE_ICG_REVIEW_READY',digest(a.output),result['actual_g32_cells'])
