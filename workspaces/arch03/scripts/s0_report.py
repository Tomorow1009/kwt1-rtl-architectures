"""Read-only S0 report export; no EDA, inherited netlist PASS, or acceptance.

The common T80 exporter still checks real captures, precision and all twelve
activity/power identities. S0 additionally proves the three-DDC provenance.
"""
import argparse
import json
from pathlib import Path
import re

import s0_partition_synth as mapping
import s0_validation
import t80_paths
from partition_synth_contract import require, digest

ROOT=Path(__file__).resolve().parents[3]


def synthesis_context(reference,cfg):
    run=t80_paths.allowed_run(reference['run'],cfg,'S0 report synthesis')
    report,_=s0_validation.verify_synthesis(run,reference['sha256'],cfg)
    origin=json.loads((run/'origin_identity.json').read_text())
    require(digest(run/'origin_identity.json')==report['link_report']['origin_identity_sha256'] and
            origin['baseline_summary_sha256']==mapping.BASELINE_SUMMARY and
            origin['baseline_netlist_sha256']==mapping.BASELINE_NETLIST,
            'S0 report origin differs from frozen measured T80')
    original=origin['original_summary']
    require(original['scope']=='t80_whole_soc_task_mode_preliminary_synthesis',
            'S0 origin is not the original monolithic T80')
    libraries=original['link_report']['library_inputs']
    # These are the original library identity fields, after the independent S0
    # verifier checked all three new linked DBs against the same original DBs.
    require(libraries,'Missing original T80 library identity')
    return dict(summary=report,
        platform_baseline_sha256=original['link_report']['platform_baseline_sha256'],
        library_inputs=libraries,auditor_sha256=digest(__file__))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--request',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--runtime-root',type=Path,required=True)
    p.add_argument('--runtime-manifest-sha256',required=True)
    p.add_argument('--runtime-evidence',nargs=2,action='append',default=[])
    a=p.parse_args()
    cfg=t80_paths.configure(json.loads((ROOT/'handoff/team/server_config.json').read_text()),
        ROOT,a.runtime_root,a.runtime_manifest_sha256,a.runtime_evidence)
    request_sha=digest(a.request);request=json.loads(a.request.read_text())
    require(request.get('schema')=='arch03-s0-report-request-v1','Not an S0 request')
    output=a.output.absolute()
    require(output.resolve()==output and ROOT in output.parents,'Use this new operations bundle for S0 export')
    parts=output.relative_to(ROOT).parts
    require(len(parts)==3 and parts[0]=='runs' and re.fullmatch('[A-Za-z0-9_-]{1,64}',parts[1]) and
            parts[2]=='t80_s0_report' and not output.exists(),'S0 report requires a fresh named output')
    from t80_report import build,write
    report=build(request,s0_config=cfg)
    require(digest(a.request)==request_sha,'S0 report request changed')
    t80_paths.recheck(cfg)
    report['request_sha256']=request_sha
    write(report,output)
    print('S0_EVIDENCE_EXPORTED stage_accepted=false',output)


if __name__=='__main__':main()
