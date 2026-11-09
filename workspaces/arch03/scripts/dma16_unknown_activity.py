"""Locate every unknown record in a frozen full-task VCD, without power claims.

Run only under the shared server_run lock. Counts must agree with the original
complete activity audit. Per-identifier durations measure time with ANY unknown
bit; they are not unknown-bit counts or a power error bound. Alias roles overlap.
"""
from decimal import Decimal
import json
from pathlib import Path
from dma16_power import gate_activity, stream_sha
from server_run import sha, save

COUNTERS = ('signal_declarations', 'unique_identifiers', 'active_value_records',
            'unknown_value_records', 'component_value_records', 'component_declarations')


def require(ok, message):
    if not ok:
        raise ValueError(message)


def validate(scanned, activity):
    require(scanned.get('schema') == 'activity_unknown_stream_v1', 'Unknown scanner schema')
    for key in COUNTERS:
        require(scanned[key] == activity[key], 'Unknown audit differs from frozen full scan: '+key)
    scale = Decimal(scanned['scale_fs'])/Decimal(1000000)
    begin, end = scanned['begin_tick'], scanned['end_tick']
    require(scale > 0 and end > begin, 'Invalid unknown activity interval')
    require(Decimal(begin)*scale == Decimal(activity['start_ns']) and
            Decimal(end)*scale == Decimal(activity['end_ns']), 'Unknown activity window changed')
    signals = scanned['signals']; identifiers = set(); unknown = initial = later = missing = persistent = affected = 0
    roles = {}
    for signal in signals:
        code = signal['identifier']; require(code not in identifiers, 'Duplicate unknown identifier'); identifiers.add(code)
        require(signal['aliases'] and all(p.startswith('tb_top.u_e203_soc_top.') for p in signal['aliases']),
                'Missing/out-of-scope unknown aliases')
        count = signal['unknown_records']; at_begin = signal['unknown_records_at_begin']; after = signal['unknown_records_after_begin']
        require(0 <= count <= signal['value_records'] and count == at_begin+after and min(at_begin, after) >= 0,
                'Invalid unknown record counts')
        first = signal['first_observation_tick']; prefix = signal['unobserved_prefix_ticks']
        require(prefix == (end-begin if first is None else first-begin) and 0 <= prefix <= end-begin,
                'Invalid unobserved prefix')
        require(0 <= signal['any_unknown_ticks'] <= end-begin-prefix, 'Invalid unknown duration')
        require(count or prefix, 'Unexpected fully known identifier in diagnostic details')
        if count:
            require(first is not None and begin <= first <= signal['first_unknown_tick'] <= signal['last_unknown_tick'] <= end,
                    'Invalid unknown record time')
            require(not at_begin or signal['first_unknown_tick'] == begin, 'Initial unknown timestamp changed')
        else:
            require(signal['first_unknown_tick'] is None and signal['last_unknown_tick'] is None and
                    signal['any_unknown_ticks'] == 0 and not signal['unknown_at_end'], 'Unknown state without records')
        unknown += count; initial += at_begin; later += after; missing += bool(prefix)
        persistent += bool(signal['unknown_at_end']); affected += bool(count)
        for role in signal['roles'] or ['other_soc']:
            require(role in ('cpu', 'itcm', 'dtcm', 'accelerator', 'shared', 'interconnect', 'other_soc'), 'Unknown role')
            row = roles.setdefault(role, dict(identifiers=0, unknown_records=0, unknown_records_after_begin=0,
                                              identifiers_unknown_at_end=0, identifiers_without_initial_observation=0))
            row['identifiers'] += 1; row['unknown_records'] += count; row['unknown_records_after_begin'] += after
            row['identifiers_unknown_at_end'] += bool(signal['unknown_at_end'])
            row['identifiers_without_initial_observation'] += bool(prefix)
    expected = dict(unknown_value_records=unknown, unknown_records_at_begin=initial, unknown_records_after_begin=later,
                    identifiers_without_initial_observation=missing, unknown_identifiers_at_end=persistent,
                    unknown_identifiers=affected)
    require(all(scanned[k] == value for k, value in expected.items()), 'Unknown details/summary disagree')
    require(len(identifiers) <= scanned['unique_identifiers'], 'Too many diagnostic identifiers')
    return dict(counters=expected, diagnostic_identifiers=len(identifiers), overlapping_roles=roles,
                timescale_ns=str(scale), start_ns=str(Decimal(begin)*scale), end_ns=str(Decimal(end)*scale))


def audit(cfg, run, gate, expected, case, call):
    run = Path(run); gate = Path(gate)
    report, row, vcd, synthesis, duration = gate_activity(gate, expected, case, cfg)
    source = Path(__file__).with_name('activity_unknown.cpp'); binary = run/'activity_unknown'
    tracked = [Path(__file__), source, gate/'summary.json', gate/'source_inputs.json']
    before = {str(p): sha(p) for p in tracked}; stat = vcd.stat()
    save(run/'source_inputs.json', before)
    call(['g++', '-O2', '-std=c++11', source, '-o', binary], run, 'unknown_compile.log')
    binary_digest = sha(binary)
    text = call([binary, vcd], run, 'unknown_full_scan.json')
    scanned = json.loads(text); checked = validate(scanned, row['activity'])
    require(stream_sha(vcd) == row['activity']['sha256'], 'VCD changed during unknown audit')
    require((stat.st_size, stat.st_mtime_ns) == (vcd.stat().st_size, vcd.stat().st_mtime_ns), 'VCD metadata changed')
    require(sha(binary) == binary_digest, 'Unknown scanner binary changed')
    for name, digest in before.items():
        require(sha(Path(name)) == digest, 'Unknown audit input changed: '+name)
    return dict(status='diagnostics_ready_review_required', scope='dma16_frozen_full_vcd_unknown_localization',
                case=case, gate_run=str(gate), gate_summary_sha256=expected,
                synthesis_summary_sha256=report['synthesis_summary_sha256'],
                vcd_sha256=row['activity']['sha256'], vcd_bytes=stat.st_size, duration_ns=duration,
                scanner_source_sha256=sha(source), scanner_binary_sha256=binary_digest,
                original_activity=row['activity'], localization=checked,
                waveform_modified=False, complete_stream_scanned=True, system_power_verified=False,
                review='Review all aliases and active logic. Any-unknown duration is not a bit count or power bound; missing prefixes remain unobserved.',
                artifacts={p.name: sha(p) for p in run.iterdir() if p.is_file()})
