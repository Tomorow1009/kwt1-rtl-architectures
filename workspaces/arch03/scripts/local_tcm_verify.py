"""Full-size TCM adapter regression; test substitutes, never vendor/CPU acceptance."""
import argparse
import json
from datetime import datetime
from pathlib import Path
from local_verify import A2, A3, ROOT, run, sha


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--vivado-bin', type=Path, required=True)
    parser.add_argument('--backend', choices=['behavioral', 'pin_mock'], default='pin_mock')
    args = parser.parse_args()
    folder = ROOT/'local_runs'/('tcm_' + datetime.now().strftime('%Y%m%d_%H%M%S_%f') + '_' + args.backend)
    folder.mkdir(parents=True)
    files = [A3/'rtl/arch03_shared_sram.sv', A3/'rtl/arch03_tcm_ram.sv', A3/'tb/tb_arch03_tcm.sv']
    tracked = files + [Path(__file__).resolve()]
    define = 'ARCH02_BEHAVIORAL'
    if args.backend == 'pin_mock':
        define = 'ARCH02_PIN_MOCK'
        files.append(A2/'arch02/tb/pin_mock.sv')
        cfgpath = A2/'arch02/tb/pin_mock_config.json'
        cfg = json.loads(cfgpath.read_text())
        lines = []
        for size in ('128', '4096'):
            for key, width in [('cen_low', 1), ('gwen_low', 1), ('wen_low', 1), ('ema', 3), ('emaw', 2), ('ret1n', 1)]:
                lines.append("`define A02_%s_%s %d'd%d" % (size, key.upper(), width, cfg['macros'][size][key]))
        config = folder/'arch02_sram_config.vh'
        config.write_text('\n'.join(lines)+'\n', encoding='ascii')
        tracked += [files[-1], cfgpath, config]
    before = {p: sha(p) for p in tracked}
    tool = lambda name: args.vivado_bin/(name+'.bat')
    run([tool('xvlog'), '--sv', '-d', define, '-i', folder]+files, folder, 'compile.log')
    run([tool('xelab'), 'tb_arch03_tcm', '-debug', 'typical', '-s', 'tcm'], folder, 'elaborate.log')
    (folder/'run.tcl').write_text('run all\nquit\n', encoding='ascii')
    log = run([tool('xsim'), 'tcm', '-tclbatch', 'run.tcl'], folder, 'simulation.log')
    if 'ARCH03_TCM_PASS macros=64 cpu_executed=false' not in log:
        raise ValueError('Missing TCM acceptance marker')
    for path, digest in before.items():
        if sha(path) != digest:
            raise ValueError('TCM input changed during run: '+str(path))
    report = dict(status='passed', backend=args.backend, cpu_executed=False,
                  vendor_verified=False, synthesis_verified=False,
                  geometries=[dict(depth=32768, width=64), dict(depth=65536, width=32)],
                  source_sha256={p.relative_to(ROOT).as_posix(): h for p, h in before.items()},
                  simulation_sha256=sha(folder/'simulation.log'))
    (folder/'summary.json').write_text(json.dumps(report, indent=2))
    print('LOCAL_TCM_PASS '+str(folder), flush=True)


if __name__ == '__main__':
    main()
