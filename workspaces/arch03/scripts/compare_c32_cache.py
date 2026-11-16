"""Compare completed A/B local cache evaluations using identical wire inputs.

This selects whether to spend server time on C32-B; it does not grant ASIC,
mapped timing, area or power acceptance to the compact-cache candidate.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path


def require(ok, message):
    if not ok:
        raise ValueError(message)


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def compare(a, b):
    for item in (a, b):
        require(item['status'] == 'passed' and not item['cpu_executed'] and
                item['backend'] == 'pin_mock' and item['total_result_sat_checked'] and
                item['cold_start'] and item['cancel_held_request_drained'],
                'Require complete local functional results, not partial logs')
    for key in ('layout', 'numeric_format', 'source_credits', 'transaction_metadata_depth'):
        require(a[key] == b[key], 'Changed comparison setting: '+key)
    names = ['layer_%02d' % n for n in range(1, 13)] + ['extremes', 'rounding']
    require(a['tasks'] == b['tasks'] == 14 and a['outputs'] == b['outputs'] == 354816,
            'Require all fourteen independent tasks')
    sides = []
    for report in (a, b):
        rows = {row['case']: row for row in report['cases']}
        require(len(rows) == len(report['cases']) == 14 and set(rows) == set(names),
                'Missing or duplicate local test')
        sides.append(rows)
    shared = set(a['source_sha256']) & set(b['source_sha256'])
    # Generated config location is per-run; the source model/config and all
    # unchanged transport, decoder, arithmetic files are independently pinned.
    critical = [name for name in shared if not name.startswith('local_runs/')]
    require(len(critical) >= 12 and all(a['source_sha256'][n] == b['source_sha256'][n]
                                     for n in critical), 'Shared implementation changed')
    rows = []
    for name in names:
        x, y = [side[name] for side in sides]
        for key in ('sequence_index', 'read_latency', 'prefetch', 'jitter',
                    'encoded_bytes', 'transactions', 'encoded_sha256', 'source_layout_sha256'):
            require(x[key] == y[key], name+' changed '+key)
        require(x['sequence_index'] == 0 and x['cycles'] > 0 and y['cycles'] > 0,
                'Not a standalone measured task')
        rows.append(dict(case=name, c32_a_cycles=x['cycles'], c32_b_cycles=y['cycles'],
                         change_cycles=y['cycles']-x['cycles'],
                         encoded_sha256=x['encoded_sha256'],
                         a_x_write_conflicts=x['pipeline']['x_write_conflicts'],
                         b_x_write_conflicts=y['pipeline']['x_write_conflicts']))
    ca = sum(row['c32_a_cycles'] for row in rows[:12])
    cb = sum(row['c32_b_cycles'] for row in rows[:12])
    return dict(schema='c32-cache-local-feasibility-v1',
        scope='Identical local pin-mock DMA harness; no original mem_fab, E203 or vendor SRAM',
        c32_a_fixed12_total_cycles=ca, c32_b_fixed12_total_cycles=cb,
        c32_a_fixed12_mean_cycles=ca/12., c32_b_fixed12_mean_cycles=cb/12.,
        throughput_change_percent=(ca/cb-1)*100,
        candidate_meets_local_nondecreasing_throughput=cb <= ca,
        recommend_c32_b_for_server_qualification=cb <= ca,
        own_local14_outputs_and_totals=354816, identical_common_source_files=len(critical),
        c32_b_asic_verified=False, c32_b_area_verified=False, c32_b_power_verified=False,
        c32_b_stage_accepted=False,
        decision=('Qualify compact cache on server before selecting it' if cb <= ca else
                  'Retain frozen C32-A cache for G32; compact candidate not promoted'), cases=rows)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('baseline', 'candidate', 'output'):
        p.add_argument('--'+name, type=Path, required=True)
    args = p.parse_args()
    require(not args.output.exists(), 'Preserve previous comparisons')
    before = {str(x): sha(x) for x in (args.baseline, args.candidate)}
    report = compare(read(args.baseline), read(args.candidate))
    require(all(sha(path) == digest for path, digest in before.items()), 'Input report changed')
    report.update(input_sha256=before, source_sha256=sha(__file__))
    args.output.mkdir(parents=True)
    (args.output/'summary.json').write_text(json.dumps(report, indent=2)+'\n')
    with (args.output/'cases.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(report['cases'][0]))
        writer.writeheader()
        writer.writerows(report['cases'])
    print('C32_CACHE_COMPARISON', report['decision'], report['throughput_change_percent'])


if __name__ == '__main__':
    main()
