"""Exercise original and minimally patched official UARTs side by side."""
import re
from pathlib import Path
from install_platform import install,patch_uart_defaults
from server_run import A3,sha,save


def verify(cfg,run,platform_source,call):
    platform=run/'platform'
    installed=install(platform_source,platform,asic=True)
    relative='rtl/e203/perips/apb_uart/apb_uart.v'
    original=platform_source/relative
    text=original.read_text()
    patched=platform/relative
    if patched.read_text()!=patch_uart_defaults(text):raise ValueError('UART installer patch differs')
    reference=run/'apb_uart_reference.v'
    text,n=re.subn(r'\bmodule\s+apb_uart_sv\b','module apb_uart_reference',text)
    if n!=1:raise ValueError('Unexpected UART module name')
    reference.write_text(text)
    sources=sorted(patched.parent.glob('*.v'))+[reference,A3/'tb/tb_arch03_uart_compare.sv']
    if len(sources)!=7:raise ValueError('Pinned UART source set changed')
    before={str(p):sha(p) for p in sources+[original]}
    save(run/'source_inputs.json',before)
    call([cfg['tools']['vcs'],'-full64','-sverilog','-timescale=1ns/1fs',
          '-top','tb_arch03_uart_compare','-o',run/'simv']+sources,run,'compile.log')
    result=call([run/'simv'],run,'simulation.log')
    matches=re.findall(r'ARCH03_UART_COMPARE_PASS cycles=(\d+) writes=(\d+) reads=(\d+) tx_accepts=(\d+) idle_checks=(\d+) tx_edges=(\d+)',result)
    if len(matches)!=1:raise ValueError('UART comparison did not complete')
    for p,h in before.items():
        if sha(Path(p))!=h:raise ValueError('UART comparison input changed')
    return dict(status='passed',scope='actual_original_vs_patched_official_UART_functional_miter',
                baseline_sha256=installed['baseline_sha256'],
                counters=dict(zip(('cycles','writes','reads','tx_accepts','idle_checks','tx_edges'),map(int,matches[0]))),
                cpu_executed=False,timing_verified=False,
                original_sha256=sha(original),patched_sha256=sha(patched),
                artifacts={p.name:sha(p) for p in run.iterdir() if p.is_file()})
