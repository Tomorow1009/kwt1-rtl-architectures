"""Directed continuous-block arithmetic/transport test; not SoC or PPA."""
import argparse
import json
from datetime import datetime
from pathlib import Path
from local_verify_linear16x4 import ROOT, A3, run, sha


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--vivado-bin', required=True, type=Path)
    args = parser.parse_args()
    folder = ROOT/'local_runs'/('systolic_array_'+datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    folder.mkdir(parents=True)
    files = [A3/'rtl/arch03_systolic5x16.sv', A3/'tb/tb_arch03_systolic5x16.sv']
    hashes = {str(p.relative_to(ROOT)): sha(p) for p in files+[Path(__file__).resolve()]}
    tool = lambda n: args.vivado_bin/(n+'.bat')
    run([tool('xvlog'), '--sv']+files, folder, 'compile.log')
    run([tool('xelab'), 'tb_arch03_systolic5x16', '-debug', 'typical', '-s', 'array'], folder, 'elaborate.log')
    (folder/'run.tcl').write_text('run all\nquit\n')
    text = run([tool('xsim'), 'array', '-tclbatch', 'run.tcl'], folder, 'simulate.log')
    marker = 'SYSTOLIC5X16_ARRAY_PASS blocks=14 outputs=1088 continuous_II=64'
    if marker not in text:
        raise ValueError('Missing complete array result')
    if any(sha(ROOT/p) != digest for p, digest in hashes.items()):
        raise ValueError('Input changed during simulation')
    report = dict(status='passed', scope='standalone_systolic_integer_array_only',
                  blocks=14, outputs=1088, continuous_block_II=64, cpu_executed=False,
                  cancels_and_reset=True, global_pause=True, source_sha256=hashes)
    (folder/'summary.json').write_text(json.dumps(report, indent=2)+'\n')
    print('SYSTOLIC_ARRAY_LOCAL_PASS', folder)


if __name__ == '__main__':
    main()
