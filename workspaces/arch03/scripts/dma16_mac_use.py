"""Passive frozen-VCD MAC acceptance audit; not system power approval."""
from decimal import Decimal
from pathlib import Path
import json
from dma16_unknown_activity import require, validate as unknown_validate
from dma16_power import gate_activity, stream_sha
from server_run import sha, save


def validate(scanned, activity, window, dots=1584):
    require(scanned.get('schema') == 'activity_unknown_mac_stream_v1', 'Wrong MAC audit schema')
    original = dict(scanned, schema='activity_unknown_stream_v1')
    localization = unknown_validate(original, activity)
    data = scanned['mac_sampling']
    require(data['semantics'] == 'pre_timestamp_values_on_observed_rising_edge', 'Wrong sampling semantics')
    require(data['accepted_samples_unknown'] == data['ambiguous_controls'] == 0,
            'Unknown accepted data or ambiguous controls require review')
    rows = data['lanes']
    require(len(rows) == 16 and {r['lane'] for r in rows} == set(range(16)), 'Incomplete/duplicate MAC lanes')
    period = Decimal(str(window['period_ns']))*Decimal(1000000)/Decimal(scanned['scale_fs'])
    require(period > 0 and period == int(period), 'Nonintegral clock in VCD ticks')
    period = int(period); begin, end = scanned['begin_tick'], scanned['end_tick']
    fields = {'clk', 'rst_n', 'start_valid', 'start_ready', 'bias', 'shift',
              'in_valid', 'in_ready', 'x', 'w', 'out_valid', 'out_ready', 'result', 'saturated'}
    for row in rows:
        require((row['starts'], row['feeds'], row['outputs']) == (dots, dots*64, dots),
                'Missing or extra accepted MAC operations')
        require(row['violations'] == row['reset_edges'] == 0 and not row['unfinished_dot'],
                'MAC protocol/reset violations require review')
        first, last = row['first_edge_tick'], row['last_edge_tick']
        require(begin < first <= begin+period and end-period <= last <= end and first < last,
                'Incomplete sampled clock coverage')
        require(row['minimum_edge_interval_ticks'] == row['maximum_edge_interval_ticks'] == period and
                last-first == (row['edges']-1)*period, 'MAC clock cadence differs from frozen clock')
        require(first <= row['first_feed_tick'] <= row['last_feed_tick'] <= last, 'Invalid accepted-data interval')
        counts = row['unknown_at_sampled_edges']
        require(set(counts) == fields and all(type(n) is int and 0 <= n <= row['edges'] for n in counts.values()),
                'Invalid per-port unknown edge counts')
    require(len({(r['edges'], r['first_edge_tick'], r['last_edge_tick']) for r in rows}) == 1,
            'MAC lane clock intervals differ')
    return dict(localization=localization, mac_sampling=data, accepted_macs=dots*64*16,
                accepted_outputs=dots*16, mac_valid_samples_verified=True, system_power_verified=False)


def audit(cfg, run, gate, expected, case, call):
    run = Path(run); gate = Path(gate)
    report, row, vcd, synthesis, duration = gate_activity(gate, expected, case, cfg)
    source = Path(__file__).with_name('activity_mac_use.cpp'); binary = run/'activity_mac_use'
    tracked = [Path(__file__), source, Path(__file__).with_name('dma16_unknown_activity.py'),
               gate/'summary.json', gate/'source_inputs.json']
    before = {str(p): sha(p) for p in tracked}; stat = vcd.stat()
    save(run/'source_inputs.json', before)
    call(['g++', '-O2', '-std=c++11', source, '-o', binary], run, 'mac_compile.log')
    binary_digest = sha(binary)
    scanned = json.loads(call([binary, vcd], run, 'mac_full_scan.json'))
    checked = validate(scanned, row['activity'], row['task_window'])
    require(stream_sha(vcd) == row['activity']['sha256'], 'VCD changed during MAC audit')
    require((stat.st_size, stat.st_mtime_ns) == (vcd.stat().st_size, vcd.stat().st_mtime_ns), 'VCD metadata changed')
    require(sha(binary) == binary_digest, 'MAC scanner binary changed')
    for path, digest in before.items():
        require(sha(Path(path)) == digest, 'MAC audit input changed')
    return dict(status='diagnostics_ready_review_required', scope='dma16_frozen_full_vcd_mac_acceptance',
                case=case, gate_run=str(gate), gate_summary_sha256=expected,
                synthesis_summary_sha256=report['synthesis_summary_sha256'],
                vcd_sha256=row['activity']['sha256'], vcd_bytes=stat.st_size, duration_ns=duration,
                scanner_source_sha256=sha(source), scanner_binary_sha256=binary_digest,
                original_activity=row['activity'], checked=checked, waveform_modified=False,
                complete_stream_scanned=True, system_power_verified=False,
                limits=['Known accepted MAC values do not prove idle combinational switching power.',
                        'CPU, memory, interconnect, unused state and X modeling still need review.',
                        'Pre-timestamp sampling excludes post-edge/NBA changes from consumed values.'],
                artifacts={p.name: sha(p) for p in run.iterdir() if p.is_file()})
