"""Local protocol fixture/oracle, not ASIC/CPU or arithmetic acceptance."""
import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from local_verify import ROOT, A3, run, sha
from dma16_bus_metrics import parse_metrics, PHASES, METRICS, TRANSITIONS, BINS, fields


def sample_stat(values):
    hist = [0]*9
    for value in values:
        index = next(i for i, (low, high) in enumerate(BINS) if low <= value and (high is None or value <= high))
        hist[index] += 1
    return dict(count=len(values), min=min(values) if values else 0, max=max(values) if values else 0,
                sum=sum(values), histogram=hist)


def oracle(text, measured):
    samples = {(p, m): [] for p in PHASES for m in METRICS}; switches = {s: [] for s in TRANSITIONS}
    previous = {}; offer = None; pending = None; prior_accept = None; first = None; last = None
    counts = {p: [0, 0] for p in PHASES}; cpu_start = None; cpu_spans = []; waits = []
    for line in text.splitlines():
        if not line.startswith('BUS_ORACLE_'):
            continue
        row = fields(line); time_ns = int(row['time_ns']); event = line.split()[0]
        if event == 'BUS_ORACLE_CPU_ACCEPT':
            if cpu_start is not None: raise ValueError('Oracle overlapping CPU request')
            cpu_start = time_ns; continue
        if event == 'BUS_ORACLE_CPU_ACK':
            cpu_spans.append((cpu_start if cpu_start is not None else 0, time_ns)); cpu_start = None; continue
        if event in ('BUS_ORACLE_OFFER', 'BUS_ORACLE_ACCEPT'):
            addr, read = int(row['addr'], 16), int(row['read'])
            if read and 0xb0000000 <= addr < 0xb000b780: phase = 'source_read'
            elif 0xa0000000 <= addr < 0xa000b780: phase = 'shared_read' if read else 'stage_write'
            elif not read and 0xa000c000 <= addr < 0xa0018600: phase = 'output_write'
            else: raise ValueError('Oracle unexpected address')
        if event == 'BUS_ORACLE_OFFER':
            if offer is not None: raise ValueError('Oracle overlapping offer')
            offer = (phase, time_ns); first = time_ns if first is None else first
        elif event == 'BUS_ORACLE_ACCEPT':
            if offer is None or offer[0] != phase or pending is not None: raise ValueError('Oracle bad accept')
            samples[phase, 'offer_wait'].append((time_ns-offer[1])//10)
            waits.append((offer[1]+10, time_ns-10))
            if phase in previous: samples[phase, 'accept_gap'].append((time_ns-previous[phase])//10)
            if prior_accept is not None:
                key = ('R' if prior_accept[0] else 'W')+('R' if read else 'W')
                switches[key].append((time_ns-prior_accept[1])//10)
            previous[phase] = time_ns; prior_accept = (read, time_ns); pending = (phase, time_ns); offer = None
        else:
            if event != 'BUS_ORACLE_ACK' or pending is None: raise ValueError('Oracle bad response')
            phase, accepted_ns = pending; samples[phase, 'response_latency'].append((time_ns-accepted_ns)//10)
            counts[phase][int(row['error'])] += 1; pending = None; last = time_ns
    if pending is not None or offer is not None: raise ValueError('Oracle task not drained')
    for p in PHASES:
        if [measured['phases'][p][k] for k in ('successes', 'errors')] != counts[p]: raise ValueError('Oracle ACK counter mismatch')
        for m in METRICS:
            if sample_stat(samples[p, m]) != measured['phases'][p]['statistics'][m]: raise ValueError('Independent event-time oracle mismatch '+p+'/'+m)
    for transition in TRANSITIONS:
        if sample_stat(switches[transition]) != measured['transitions'][transition]: raise ValueError('Oracle read/write switch mismatch')
    if measured['header']['total_cycles'] != (last-first)//10: raise ValueError('Oracle complete-window mismatch')
    # Independent interval intersection from CPU accept/ACK and DMA offer/accept
    # event times; no use of the metrics module's owner register or counters.
    owned_wait = 0; cursor = 0
    for start, end in waits:
        while cursor < len(cpu_spans) and cpu_spans[cursor][1] < start: cursor += 1
        index = cursor
        while index < len(cpu_spans) and cpu_spans[index][0]+10 <= end:
            lo = max(start, cpu_spans[index][0]+10); hi = min(end, cpu_spans[index][1])
            if hi >= lo: owned_wait += (hi-lo)//10+1
            index += 1
    if owned_wait != measured['contention']['cpu_owned_wait_cycles']: raise ValueError('Oracle CPU ownership stall mismatch')
    return dict(status='independent_event_time_statistics_match', events=sum(sum(v) for v in counts.values()),
                first_offer_ns=first, final_ack_ns=last, cpu_owned_wait_cycles=owned_wait, cpu_executed=False)


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--vivado-bin', required=True, type=Path)
    parser.add_argument('--cases', nargs='+', type=int, choices=range(7), default=[1, 2, 6, 0, 3, 4, 5]); args = parser.parse_args()
    folder = ROOT/'local_runs'/('dma16_bus_metrics_'+datetime.now().strftime('%Y%m%d_%H%M%S_%f')); folder.mkdir(parents=True)
    files = [A3/'rtl/arch03_icb_arb2.sv', A3/'tb/arch03_dma16_bus_metrics.sv', A3/'tb/tb_arch03_dma16_bus_metrics.sv']
    before = {p.resolve(): sha(p) for p in files+[Path(__file__), Path(__file__).with_name('dma16_bus_metrics.py')]}
    tool = lambda n: args.vivado_bin/(n+'.bat')
    run([tool('xvlog'), '--sv']+files, folder, 'compile.log')
    run([tool('xelab'), 'tb_arch03_dma16_bus_metrics', '-debug', 'typical', '-s', 'bus_metrics'], folder, 'elaborate.log')
    (folder/'run.tcl').write_text('run all\nquit\n')
    results = []
    for mode in args.cases:
        name = 'case_%d.log' % mode; negative = mode in (3, 4, 5)
        options = folder/('case_%d.options' % mode)
        options.write_text('bus_metrics\n-tclbatch run.tcl\n-testplusarg CASE=%d\n' % mode)
        try:
            text = run([tool('xsim'), '-f', options], folder, name)
        except RuntimeError:
            if not negative: raise
            text = (folder/name).read_text(errors='replace')
        if negative:
            expected = {3: '15', 4: '3', 5: '18'}[mode]
            if not re.search(r'DMA16_BUS_METRICS_PROTOCOL_ERROR code='+expected+r'\b', text): raise ValueError('Negative protocol stimulus not rejected: '+name)
            results.append(dict(case=mode, status='expected_protocol_rejection', code=int(expected)))
        else:
            if 'BUS_METRICS_FIXTURE_PASS case=%d' % mode not in text: raise ValueError('Fixture did not finish')
            if mode == 6:
                blocks = list(re.finditer(r'^DMA16_BUS_HEADER .*?^DMA16_BUS_END schema=dma16_bus_metrics_v1$', text, re.M|re.S))
                if len(blocks) != 2: raise ValueError('No-reset two-task metric records missing')
                previous_end = 0; records = []
                for block in blocks:
                    part = text[previous_end:block.end()]; measured = parse_metrics(part, require_complete=False)
                    records.append(dict(measurement=measured, oracle=oracle(part, measured))); previous_end = block.end()
                results.append(dict(case=mode, status='passed', no_reset_tasks=records))
                print('DMA16_BUS_CASE_PASS', mode, flush=True)
                continue
            measured = parse_metrics(text, require_complete=mode == 0)
            proof = oracle(text, measured)
            if mode == 1 and measured['header']['cancelled_acks'] != 1: raise ValueError('Cancellation drain not covered')
            if mode == 2 and (measured['header']['errors'], measured['header']['committed_bytes']) != (1, 4): raise ValueError('Error ACK counted as bytes')
            if mode == 0 and not all(measured['contention'][k] > 0 for k in ('competing_cpu_grants', 'competing_dma_grants', 'competing_blocked', 'response_backpressure_cycles', 'cpu_owned_wait_cycles')):
                raise ValueError('Insufficient CPU/response backpressure coverage')
            results.append(dict(case=mode, status='passed', measurement=measured, oracle=proof))
        print('DMA16_BUS_CASE_PASS', mode, flush=True)
    for path, digest in before.items():
        if sha(path) != digest: raise ValueError('Source changed during verification')
    report = dict(status='passed', scope='local_passive_protocol_metrics_fixture', cpu_executed=False,
                  arithmetic_executed=False, full_task_case_included=0 in args.cases, cases=results, source_sha256={p.relative_to(ROOT).as_posix(): h for p, h in before.items()},
                  logs={p.name: sha(p) for p in folder.glob('*.log')})
    (folder/'summary.json').write_text(json.dumps(report, indent=2)+'\n')
    print('DMA16_BUS_METRICS_PASS '+str(folder), flush=True)


if __name__ == '__main__': main()
