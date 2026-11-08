"""Re-audit a finished gate simulation after interrupted activity postprocessing.

Never change the original run or rerun VCS. New reports bind the original
mapped design and original firmware, not any newer platform installer changes.
"""
import json,re,shutil
from pathlib import Path
from asic_boot import prepare
from asic_soc import verify_images
from gate_soc import verify_synthesis
from activity_fast import audit_activity
from server_run import ROOT,sha,save,check_capture,read_task_window


def verify(cfg,run,origin,cases,call):
    origin=origin.resolve();origin.relative_to(Path(cfg['server_root']).resolve())
    state=json.loads((origin.parent/'state.json').read_text())['stages']['gate_soc']
    if state['status']!='failed' or (origin/'summary.json').exists():
        raise ValueError('Re-audit requires a preserved failed gate stage without a summary')
    bundle=origin.parents[2];manifest=json.loads((bundle/'manifest.json').read_text())
    for name,digest in manifest['files'].items():
        path=(bundle/name).resolve();path.relative_to(bundle)
        if sha(path)!=digest:raise ValueError('Original gate bundle changed')
    if sorted(p.stem for p in origin.glob('*.csv'))!=sorted(cases):
        raise ValueError('Must re-audit exactly all original gate captures')
    before=json.loads((origin/'source_inputs.json').read_text())
    for name,digest in before.items():
        if sha(Path(name))!=digest:raise ValueError('Original gate input changed')
    summaries=[(Path(name),digest) for name,digest in before.items() if name.replace('\\','/').endswith('/asic_synth/summary.json')]
    if len(summaries)!=1:raise ValueError('Missing/ambiguous original synthesis provenance')
    synthesis=summaries[0][0].parent;synth_digest=summaries[0][1]
    synthesis_report,_=verify_synthesis(synthesis,synth_digest,cfg)
    compiled=(origin/'compile.log').read_text()
    if re.search(r'(?im)^\s*(Error-|Fatal:|Error:)',compiled):raise ValueError('Original gate compilation had errors')
    if re.search(r'Warning-\[(?:IPDW|PCWM-W|INAV|SIOB)\]',compiled):raise ValueError('Original gate width/declaration warnings')
    data=bundle/'validated_data';firmware=bundle/'firmware';verify_images(firmware,data,cases)
    snapshot={}
    for name in ['source_inputs.json','compile.log']+[case+suffix for case in cases for suffix in ('.log','.csv')]:
        snapshot[name]=sha(origin/name);shutil.copy2(str(origin/name),str(run/name))
    results=[]
    for name in cases:
        text=(origin/(name+'.log')).read_text();task=data/name
        if re.search(r'(?im)^\s*(Error-|Fatal:|Error:)',text):raise ValueError('Original gate task errors')
        for marker in ('ARCH03_ASIC_BOOT_READY bytes=262144 macros=32 scope=initial_ITCM_only',
                       'ARCH03_ASIC_MODE_MATCH test_mode=0 pllbypass=1 divider_bypass=1'):
            if text.count(marker)!=1:raise ValueError('Original gate boot/mode marker missing')
        matches=re.findall(r'ARCH03_SOC_PASS outputs=25344 cpu_executed=true cycles=(\d+) saturated=(\d+)',text)
        if len(matches)!=1 or '$finish called' not in text:raise ValueError('Original gate simulation not completed')
        cycles,sats=map(int,matches[0]);window=read_task_window(text)
        if not 0<window['cycles']<=cycles:raise ValueError('Original gate cycle/window mismatch')
        if sats!=sum(int(x,16) for x in (task/'saturated.hex').read_text().split()):raise ValueError('Gate saturation mismatch')
        boot=prepare(firmware/(name+'.verilog'),run/(name+'_boot'))
        for filename,digest in boot['files'].items():
            if sha(origin/(name+'_boot')/filename)!=digest:raise ValueError('Original boot data differs from firmware')
        original_vcd=origin/(name+'.vcd')
        if not original_vcd.is_file() or not original_vcd.stat().st_size:raise ValueError('Original activity missing')
        # A new server-local read-only reference avoids copying tens of GB.
        # Both the source and reference are hashed; no original bytes are changed.
        vcd=run/(name+'.vcd');vcd.symlink_to(original_vcd)
        result=dict(case=name,cycles=cycles,saturated=sats,task_window=window,boot=boot,
                    **check_capture(origin/(name+'.csv'),task,2))
        result['activity']=audit_activity(vcd,window,run,call)
        result['activity']['original_file']=str(original_vcd)
        results.append(result)
    for name,digest in before.items():
        if sha(Path(name))!=digest:raise ValueError('Original gate source changed during re-audit')
    for name,digest in snapshot.items():
        if sha(origin/name)!=digest:raise ValueError('Original gate artifact changed during re-audit')
    receipt=dict(origin=str(origin),original_state=state,original_package_source_commit=manifest['source_commit'],
                 original_artifacts=snapshot,simulation_reexecuted=False,
                 reason='Complete original gate output rechecked; interrupted slow activity audit replaced by complete native scan',
                 newer_platform_installer_verified=False)
    save(run/'report_recovery.json',receipt)
    return dict(status='passed',scope='whole_soc_mapped_functional_without_SDF',cases=results,cpu_executed=True,
        synthesis_run=str(synthesis),synthesis_summary_sha256=synth_digest,gate_simulation_verified=True,
        source_setup_hold_nonnegative=synthesis_report['setup_hold_nonnegative'],
        timing_verified=False,system_power_verified=False,physical_signoff=False,report_recovery=receipt)
