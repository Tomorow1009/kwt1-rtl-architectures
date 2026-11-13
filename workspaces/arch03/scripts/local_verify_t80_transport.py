"""T80 transport protocol tests; no CPU/physical SRAM or timing claim."""
import argparse
from datetime import datetime
import json
from pathlib import Path
from local_verify import ROOT, A3, run, sha


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--vivado-bin', required=True, type=Path)
    args = parser.parse_args()
    folder = ROOT/'local_runs'/('t80_transport_'+datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    folder.mkdir(parents=True)
    files = [A3/'rtl/arch03_t80_transport.sv', A3/'tb/tb_arch03_t80_transport.sv', Path(__file__).resolve()]
    before = {p: sha(p) for p in files}
    tool = lambda n: args.vivado_bin/(n+'.bat')
    run([tool('xvlog'), '--sv']+files[:2], folder, 'compile.log')
    run([tool('xelab'), 'tb_arch03_t80_transport', '-s', 't80_transport'], folder, 'elaborate.log')
    (folder/'run.tcl').write_text('run all\nquit\n')
    log = run([tool('xsim'), 't80_transport', '-tclbatch', 'run.tcl'], folder, 'simulation.log')
    if log.count('T80_TRANSPORT_PROTOCOL_PASS cases=7 independent_read_payload=true no_reset_restart=true') != 1:
        raise ValueError('Missing complete protocol test receipt')
    if any(sha(p) != digest for p, digest in before.items()):
        raise ValueError('Changed transport inputs during run')
    report = dict(status='passed', cases=7, cpu_executed=False, model='isolated_protocol_slave',
        fields=['different_read_payload', 'ready_wait', 'response_wait', 'all_four_error_phases',
                'cancel_held_read', 'no_reset_restart', 'final_ack_and_drain'],
        source_sha256={p.relative_to(ROOT).as_posix(): h for p, h in before.items()})
    (folder/'summary.json').write_text(json.dumps(report, indent=2)+'\n')
    print('LOCAL_T80_TRANSPORT_PASS', folder, flush=True)


if __name__ == '__main__':
    main()
