"""Query actual MMIO8 DDC high-fanout nets without remapping or timing approval."""
from pathlib import Path
import mmio8_gate as gate
from dma16_timing_audit import parse_high_fanout
from soc_power import power_databases
from soc_synth import require_tool_marker
from server_run import sha, save


def script(synthesis):
    text = gate.probe_script(synthesis)
    anchor = '    set out [open mapped_port_probe.tsv w]'
    extra = r'''
    set high [all_high_fanout -nets -threshold 1000]
    set out [open high_fanout.tsv w]
    puts $out "threshold\t1000"
    puts $out "count\t[sizeof_collection $high]"
    foreach_in_collection net $high {
        puts $out "net\t[get_object_name $net]"
    }
    close $out
'''
    return gate.synth.shared.replace_once(text, anchor, extra+anchor)


def audit(cfg, run, synthesis, expected_sha, call):
    run = Path(run); synthesis = Path(synthesis)
    gate.verify_synthesis(synthesis, expected_sha, cfg)
    tracked = [synthesis/n for n in ('mapped.ddc', 'mapped.v', 'mapped.sdc', 'summary.json')]
    tracked += power_databases(synthesis)
    tracked += [Path(__file__), Path(gate.__file__), Path(__file__).with_name('dma16_timing_audit.py')]
    before = {str(p): sha(p) for p in tracked}
    tcl = run/'timing_audit.tcl'; tcl.write_text(script(synthesis)); before[str(tcl)] = sha(tcl)
    save(run/'source_inputs.json', before)
    log = call([cfg['tools']['dc_shell'], '-f', tcl], run, 'timing_audit.log')
    require_tool_marker(log, gate.PROBE_MARKER)
    high = parse_high_fanout((run/'high_fanout.tsv').read_text())
    probe = gate.parse_probe((run/'mapped_port_probe.tsv').read_text())
    for name, digest in before.items():
        if sha(Path(name)) != digest:
            raise ValueError('Frozen MMIO8 timing input changed: '+name)
    gate.verify_synthesis(synthesis, expected_sha, cfg)
    return dict(status='diagnostics_ready_review_required', DMA_present=False,
                scope='mmio8_source_frozen_mapped_ddc_readonly_timing_diagnostics',
                synthesis_run=str(synthesis), synthesis_summary_sha256=expected_sha,
                high_fanout=high, mapped_probe=probe, netlist_modified=False,
                strict_timing_verified=False, physical_signoff=False,
                review='Classify actual MMIO8 nets and delay assumptions; no inherited DMA16 waiver.',
                artifacts={p.name: sha(p) for p in run.iterdir() if p.is_file()})
