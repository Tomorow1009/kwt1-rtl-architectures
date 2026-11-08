"""Validate the stdcell testbench against explicit local substitutes only."""
import argparse
import json
from datetime import datetime
from pathlib import Path
from local_verify import A3,ROOT,run,sha


def main():
    p=argparse.ArgumentParser();p.add_argument('--vivado-bin',required=True,type=Path)
    a=p.parse_args();folder=ROOT/'local_runs'/('stdcell_'+datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    folder.mkdir(parents=True)
    files=[A3/'tb/stdcell_pin_mock.sv',A3/'tb/tb_arch03_stdcell.sv']
    hashes={path:sha(path) for path in files+[Path(__file__).resolve()]}
    tool=lambda name:a.vivado_bin/(name+'.bat')
    run([tool('xvlog'),'--sv']+files,folder,'compile.log')
    run([tool('xelab'),'tb_arch03_stdcell','-debug','typical','-s','stdcell'],folder,'elaborate.log')
    (folder/'run.tcl').write_text('run all\nquit\n')
    log=run([tool('xsim'),'stdcell','-tclbatch','run.tcl'],folder,'simulation.log')
    if 'ARCH03_STDCELL_PASS combinational_patterns=8 gate_checks=12 types=11 functional_only=true' not in log:
        raise ValueError('Missing standard-cell bench completion')
    for path,digest in hashes.items():
        if sha(path)!=digest:raise ValueError('Standard-cell bench input changed')
    (folder/'summary.json').write_text(json.dumps(dict(status='passed',backend='independent_pin_mock',
        cpu_executed=False,vendor_verified=False,timing_verified=False,types=11,
        combinational_patterns=8,gate_checks=12,
        source_sha256={p.relative_to(ROOT).as_posix():v for p,v in hashes.items()},
        simulation_sha256=sha(folder/'simulation.log')),indent=2))
    print('LOCAL_STDCELL_PASS '+str(folder),flush=True)


if __name__=='__main__':main()
