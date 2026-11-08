"""Verify the ASIC-mode observer rejects changes and unknown mode controls."""
import argparse,json
from datetime import datetime
from pathlib import Path
from local_verify import ROOT,A3,run,sha


def main():
    p=argparse.ArgumentParser();p.add_argument('--vivado-bin',type=Path,required=True);a=p.parse_args()
    folder=ROOT/'local_runs'/('clock_mode_'+datetime.now().strftime('%Y%m%d_%H%M%S_%f'));folder.mkdir()
    files=[A3/'tb/arch03_clock_mode_guard.sv',A3/'tb/tb_arch03_clock_mode.sv']
    before={p:sha(p) for p in files+[Path(__file__).resolve()]}
    tool=lambda name:a.vivado_bin/(name+'.bat')
    run([tool('xvlog'),'--sv']+files,folder,'compile.log')
    run([tool('xelab'),'tb_arch03_clock_mode','-debug','typical','-s','mode'],folder,'elaborate.log')
    (folder/'run.tcl').write_text('run all\nquit\n')
    cases=['positive','test','bypass','divider','unknown']
    for name in cases:
        options=folder/(name+'.options');options.write_text('-testplusarg MODE_CASE='+name+'\n')
        try:run([tool('xsim'),'mode','-tclbatch','run.tcl','-f',options],folder,name+'.log')
        except RuntimeError:
            if name=='positive':raise
        log=(folder/(name+'.log')).read_text(errors='replace')
        marker='ARCH03_CLOCK_MODE_TEST_PASS cpu_executed=false'
        if name=='positive':
            if marker not in log or log.count('ARCH03_ASIC_MODE_MATCH')!=1:raise ValueError('Positive mode observation failed')
        elif marker in log or 'ASIC task clock mode differs from synthesis assumptions' not in log:
            raise ValueError('Wrong/unknown clock mode was accepted: '+name)
    for p,h in before.items():
        if sha(p)!=h:raise ValueError('Clock-mode test input changed')
    report=dict(status='passed',cpu_executed=False,cases=cases,
                source_sha256={p.relative_to(ROOT).as_posix():h for p,h in before.items()},
                logs={n:sha(folder/(n+'.log')) for n in cases})
    (folder/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
    print('LOCAL_CLOCK_MODE_PASS',folder)


if __name__=='__main__':main()
