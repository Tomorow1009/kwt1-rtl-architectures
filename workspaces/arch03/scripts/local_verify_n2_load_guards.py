"""Direct N2 cache-ingress validation; decoder is deliberately bypassed."""
import argparse
from datetime import datetime
import json
from pathlib import Path
from local_verify import ROOT, A2, A3, run, sha


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--vivado-bin', required=True, type=Path)
    args = ap.parse_args()
    out = ROOT/'local_runs'/('n2_load_guards_'+datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    out.mkdir(parents=True)
    files = [A2/'arch02/rtl/sram_port.sv', A2/'arch02/rtl/sram_macro_adapter.sv',
             A2/'arch02/tb/pin_mock.sv', A3/'rtl/arch03_n1_requantize.sv', A3/'rtl/arch03_n2_icg.sv', A3/'tb/arch03_n2_icg_test_model.sv',
             A3/'rtl/arch03_n2_systolic5x16.sv', A3/'rtl/arch03_n2_linear16x5.sv',
             A3/'tb/tb_arch03_n2_load_guards.sv']
    cfg_path = A2/'arch02/tb/pin_mock_config.json'
    cfg = json.loads(cfg_path.read_text())
    config = out/'arch02_sram_config.vh'
    config.write_text(''.join("`define A02_%s_%s %d'd%d\n" %
        (size, key.upper(), width, cfg['macros'][size][key])
        for size in ('128', '4096') for key,width in [('cen_low',1),('gwen_low',1),
        ('wen_low',1),('ema',3),('emaw',2),('ret1n',1)]))
    hashes = {p: sha(p) for p in files+[cfg_path, config, Path(__file__).resolve()]}
    tool = lambda n: args.vivado_bin/(n+'.bat')
    run([tool('xvlog'), '--sv', '-d', 'ARCH02_PIN_MOCK', '-i', out]+files, out, 'compile.log')
    run([tool('xelab'), 'tb_arch03_n2_load_guards', '-debug', 'typical', '-s', 'n2_guard'], out, 'elaborate.log')
    (out/'run.tcl').write_text('run all\nquit\n')
    text = run([tool('xsim'), 'n2_guard', '-tclbatch', 'run.tcl'], out, 'simulation.log')
    if 'N2_CORE_LOAD_GUARDS_PASS tests=9 decoder_bypassed=true' not in text:
        raise ValueError('Missing core load guard completion')
    if any(sha(p)!=h for p,h in hashes.items()):
        raise ValueError('Source changed during run')
    (out/'summary.json').write_text(json.dumps(dict(status='passed', tests=9,
        decoder_bypassed=True, cpu_executed=False, backend='pin_mock',
        scope='direct_n2_core_load_guards_debug_dma_bias_sign_and_cancel',
        source_sha256={str(p):h for p,h in hashes.items()}), indent=2)+'\n')
    print('LOCAL_N2_LOAD_GUARDS_PASS '+str(out), flush=True)


if __name__ == '__main__':
    main()
