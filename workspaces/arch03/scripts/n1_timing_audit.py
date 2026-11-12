"""Read-only diagnostics for the frozen mapped ICB32 design.

This identifies the actual high-fanout nets behind TIM-134. It does not
recompile the design or promote preliminary timing to an accepted result.
"""
import re
from pathlib import Path
from server_run import sha, save
from n1_gate import probe_script, parse_probe, verify_synthesis, PROBE_MARKER
from soc_power import power_databases
from soc_synth import require_tool_marker


def script(synthesis):
    original = probe_script(synthesis)
    anchor = '    set out [open mapped_port_probe.tsv w]'
    if original.count(anchor) != 1:
        raise ValueError('Mapped probe template changed')
    extra = r'''
    # Query the original mapped DDC. Do not map, optimize or write a design.
    set high [all_high_fanout -nets -threshold 1000]
    set out [open high_fanout.tsv w]
    puts $out "threshold\t1000"
    puts $out "count\t[sizeof_collection $high]"
    foreach_in_collection net $high {
        puts $out "net\t[get_object_name $net]"
    }
    close $out
'''
    return original.replace(anchor, extra+anchor)


def parse_high_fanout(text):
    rows = [line.split('\t') for line in text.splitlines()]
    if len(rows) < 2 or rows[0] != ['threshold', '1000'] or len(rows[1]) != 2:
        raise ValueError('Missing high-fanout threshold/count')
    if rows[1][0] != 'count' or not re.fullmatch(r'0|[1-9][0-9]*', rows[1][1]):
        raise ValueError('Invalid high-fanout count')
    names = []
    for row in rows[2:]:
        if (len(row) != 2 or row[0] != 'net' or not row[1] or
                re.search(r'\s', row[1]) or row[1] in names):
            raise ValueError('Malformed/duplicate high-fanout net')
        names.append(row[1])
    if len(names) != int(rows[1][1]):
        raise ValueError('Incomplete high-fanout inventory')
    return dict(threshold=1000, count=len(names), nets=names)


def audit(cfg, run, synthesis, expected_sha, call):
    run = Path(run).resolve(); synthesis = Path(synthesis).resolve()
    verify_synthesis(synthesis, expected_sha, cfg)
    tracked = [synthesis/n for n in ('mapped.ddc', 'mapped.v', 'mapped.sdc',
                                    'summary.json', 'mapped_probe_inventory.tsv')]
    tracked += power_databases(synthesis)
    tracked += [Path(__file__), Path(__file__).with_name('n1_gate.py')]
    before = {str(p): sha(p) for p in tracked}
    tcl = run/'timing_audit.tcl'
    tcl.write_text(script(synthesis)); before[str(tcl)] = sha(tcl)
    save(run/'source_inputs.json', before)
    log = call([cfg['tools']['dc_shell'], '-f', tcl], run, 'timing_audit.log')
    require_tool_marker(log, PROBE_MARKER)
    high = parse_high_fanout((run/'high_fanout.tsv').read_text())
    probe = parse_probe((run/'mapped_port_probe.tsv').read_text(),
                        (synthesis/'mapped_probe_inventory.tsv').read_text())
    for name, digest in before.items():
        if sha(Path(name)) != digest:
            raise ValueError('Frozen timing audit input changed: '+name)
    verify_synthesis(synthesis, expected_sha, cfg)
    return dict(status='diagnostics_ready_review_required',
                scope='n1_frozen_mapped_ddc_readonly_timing_diagnostics',
                synthesis_run=str(synthesis), synthesis_summary_sha256=expected_sha,
                high_fanout=high, mapped_probe=probe, netlist_modified=False,
                strict_timing_verified=False, physical_signoff=False,
                review='Classify actual nets and delay assumptions; this query does not waive TIM-134',
                artifacts={p.name: sha(p) for p in run.iterdir() if p.is_file()})
