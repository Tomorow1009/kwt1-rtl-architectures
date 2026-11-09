"""DMA front-end protocol tests using an explicitly non-arithmetic core stub."""
import argparse
import json
from datetime import datetime
from pathlib import Path
from local_verify import A3, ROOT, run, sha


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--vivado-bin', required=True, type=Path)
    args = parser.parse_args()
    folder = ROOT / 'local_runs' / ('dma16_protocol_' + datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    folder.mkdir(parents=True)
    files = [A3 / 'rtl/arch03_dma16_accel.sv', A3 / 'tb/tb_arch03_dma16_protocol.sv']
    before = {p: sha(p) for p in files + [Path(__file__).resolve()]}
    tool = lambda name: args.vivado_bin / (name + '.bat')
    run([tool('xvlog'), '--sv'] + files, folder, 'compile.log')
    run([tool('xelab'), 'tb_arch03_dma16_protocol', '-debug', 'typical', '-s', 'dma16_protocol'], folder, 'elaborate.log')
    (folder / 'run.tcl').write_text('run all\nquit\n')
    log = run([tool('xsim'), 'dma16_protocol', '-tclbatch', 'run.tcl'], folder, 'simulation.log')
    marker = 'ARCH03_DMA16_PROTOCOL_PASS cases=14 cpu_executed=false arithmetic_core_stub=true'
    if marker not in log:
        raise ValueError('DMA16 protocol suite did not complete')
    run([tool('xelab'), 'tb_arch03_dma16_zero', '-debug', 'typical', '-s', 'dma16_zero'], folder, 'zero_elaborate.log')
    zero_log = run([tool('xsim'), 'dma16_zero', '-tclbatch', 'run.tcl'], folder, 'zero_simulation.log')
    if 'ARCH03_DMA16_ZERO_PASS requests=47904 outputs=25344 cpu_executed=false arithmetic_core_stub=true' not in zero_log:
        raise ValueError('DMA16 zero-latency test did not complete')
    for path, digest in before.items():
        if sha(path) != digest:
            raise ValueError('Test input changed during execution: ' + str(path))
    report = dict(status='passed', cpu_executed=False, arithmetic_core_stub=True, cases=15,
                  scope='local_dma16_mmio_master_protocol_not_arithmetic_or_soc',
                  source_sha256={p.relative_to(ROOT).as_posix(): h for p, h in before.items()},
                  log_sha256={p.name: sha(p) for p in folder.glob('*.log')})
    (folder / 'summary.json').write_text(json.dumps(report, indent=2) + '\n')
    print('LOCAL_DMA16_PROTOCOL_PASS ' + str(folder), flush=True)


if __name__ == '__main__':
    main()
