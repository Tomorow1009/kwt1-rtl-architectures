"""Parse passive DMA16 service measurements; never sum overlapping stages.

Cycle values refer to sending/acceptance/ACK clock edges. offer_wait includes
the interval to the next acceptance edge even when READY was already high.
accept_gap is observed spacing, including computation/other traffic gaps;
response_latency includes response backpressure, not only slave latency.
"""
import re

SCHEMA = 'dma16_bus_metrics_v1'
PHASES = ('source_read', 'stage_write', 'shared_read', 'output_write')
METRICS = ('offer_wait', 'accept_gap', 'response_latency')
TRANSITIONS = ('RR', 'RW', 'WR', 'WW')
BINS = ((0, 0), (1, 1), (2, 2), (3, 3), (4, 7), (8, 15), (16, 31), (32, 63), (64, None))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def number(value):
    require(isinstance(value, str) and re.fullmatch(r'0|[1-9][0-9]*', value), 'Invalid unsigned metric')
    return int(value)


def fields(line):
    result = {}
    for word in line.split()[1:]:
        pair = word.split('=', 1)
        require(len(pair) == 2 and pair[0] not in result, 'Malformed/duplicate metric field')
        result[pair[0]] = pair[1]
    return result


def stats(raw, extra):
    require(set(raw) == set(extra)|{'count', 'min', 'max', 'sum', 'hist'}, 'Unexpected metric statistic fields')
    result = {k: number(raw[k]) for k in ('count', 'min', 'max', 'sum')}
    hist = [number(value) for value in raw['hist'].split(',')]
    count, low, high, value_sum = (result[k] for k in ('count', 'min', 'max', 'sum'))
    require(len(hist) == len(BINS) and sum(hist) == count, 'Histogram count mismatch')
    if not count:
        require(low == high == value_sum == 0, 'Nonzero empty statistic')
    else:
        require(low <= high and low*count <= value_sum <= high*count, 'Invalid statistic extrema/sum')
        minimum = sum(n*b[0] for n, b in zip(hist, BINS))
        maximum = sum(n*(b[1] if b[1] is not None else high) for n, b in zip(hist, BINS))
        require(minimum <= value_sum <= maximum, 'Histogram contradicts sum')
        active = [i for i, n in enumerate(hist) if n]
        for value, index in ((low, active[0]), (high, active[-1])):
            require(BINS[index][0] <= value and (BINS[index][1] is None or value <= BINS[index][1]),
                    'Histogram contradicts extrema')
    result['histogram'] = hist
    return result


def parse_metrics(text, require_complete=True, expected_window=None):
    require('DMA16_BUS_METRICS_PROTOCOL_ERROR' not in text, 'Bus monitor detected a protocol violation')
    lines = [line.strip() for line in text.splitlines() if line.startswith('DMA16_BUS_')]
    require(lines and lines[0].startswith('DMA16_BUS_HEADER ') and lines[-1] == 'DMA16_BUS_END schema='+SCHEMA,
            'Missing complete bus metrics block')
    require(len(lines) == 23, 'Missing/duplicate bus metric records')
    header = fields(lines[0]); require(header.pop('schema', None) == SCHEMA, 'Wrong bus metrics schema')
    outcome = header.pop('outcome', None); require(outcome in ('complete', 'cancelled', 'error'), 'Invalid outcome')
    expected_header = {'started', 'cancelled', 'first_offer_cycle', 'last_ack_cycle', 'published_cycle', 'total_cycles',
                       'issued', 'accepted', 'successes', 'errors', 'cancelled_acks', 'committed_bytes', 'input_words', 'output_words'}
    require(set(header) == expected_header, 'Unexpected header counters')
    header = {k: number(v) for k, v in header.items()}
    require(header['started'] in (0, 1) and header['cancelled'] in (0, 1), 'Invalid Boolean counter')
    require(header['input_words'] == 11744 and header['output_words'] == 12672, 'Nonstandard task geometry')
    require(header['last_ack_cycle'] >= header['first_offer_cycle'] and
            header['total_cycles'] == header['last_ack_cycle']-header['first_offer_cycle'] and
            header['published_cycle'] >= header['last_ack_cycle'], 'Invalid measurement window')
    phases = {}; measures = {}; switches = {}; contention = None
    counters = {'issued', 'accepted', 'successes', 'errors', 'cancelled_acks', 'committed_bytes'}
    for line in lines[1:-1]:
        kind = line.split()[0]; row = fields(line)
        if kind == 'DMA16_BUS_PHASE':
            phase = row.pop('phase', None)
            require(phase in PHASES and phase not in phases and set(row) == counters, 'Invalid/duplicate phase')
            phases[phase] = {k: number(v) for k, v in row.items()}
        elif kind == 'DMA16_BUS_STAT':
            phase, metric = row.get('phase'), row.get('metric')
            require(phase in PHASES and metric in METRICS and (phase, metric) not in measures, 'Invalid/duplicate phase statistic')
            measures[phase, metric] = stats(row, ('phase', 'metric'))
        elif kind == 'DMA16_BUS_SWITCH':
            transition = row.get('transition')
            require(transition in TRANSITIONS and transition not in switches, 'Invalid/duplicate switch statistic')
            switches[transition] = stats(row, ('transition',))
        elif kind == 'DMA16_BUS_CONTENTION':
            require(contention is None, 'Duplicate contention record')
            required = {'competing_cycles', 'cpu_grants', 'dma_grants', 'competing_cpu_grants', 'competing_dma_grants',
                        'competing_blocked', 'arb_grants', 'arb_acks', 'ready_wait_cycles', 'response_backpressure_cycles',
                        'cpu_owned_wait_cycles', 'initial_global_pending', 'initial_global_cpu'}
            require(set(row) == required, 'Incomplete contention counters')
            contention = {k: number(v) for k, v in row.items()}
        else:
            raise ValueError('Unexpected bus metric record')
    require(set(phases) == set(PHASES) and len(measures) == 12 and set(switches) == set(TRANSITIONS) and contention is not None,
            'Incomplete phase/switch/competition coverage')
    for phase, row in phases.items():
        require(row['issued'] == row['accepted'] == row['successes']+row['errors'], 'Task did not drain issued requests')
        require(row['committed_bytes'] == row['successes']*4 and row['cancelled_acks'] <= row['accepted'], 'Invalid ACK byte/cancel counters')
        for metric, count in (('offer_wait', row['accepted']), ('accept_gap', max(0, row['accepted']-1)),
                              ('response_latency', row['successes']+row['errors'])):
            require(measures[phase, metric]['count'] == count, 'Statistic sample count differs from handshakes')
    for key in counters:
        require(header[key] == sum(row[key] for row in phases.values()), 'Phase total mismatch '+key)
    require(sum(row['count'] for row in switches.values()) == max(0, header['accepted']-1), 'Switch count mismatch')
    require(contention['dma_grants'] == header['accepted'] and
            contention['arb_grants'] == contention['cpu_grants']+contention['dma_grants'], 'Arbiter/DMA grant mismatch')
    require(contention['competing_cycles'] == contention['competing_cpu_grants']+
            contention['competing_dma_grants']+contention['competing_blocked'], 'Competition partition mismatch')
    require(contention['competing_cpu_grants'] <= contention['cpu_grants'] and
            contention['competing_dma_grants'] <= contention['dma_grants'], 'Invalid contested grants')
    require(contention['cpu_owned_wait_cycles'] <= contention['ready_wait_cycles'], 'CPU ownership wait exceeds all command stalls')
    require(contention['initial_global_pending'] in (0, 1) and contention['initial_global_cpu'] in (0, 1) and
            contention['initial_global_cpu'] <= contention['initial_global_pending'], 'Invalid initial owner')
    if outcome == 'complete':
        require(header['started'] == 1 and header['cancelled'] == header['errors'] == header['cancelled_acks'] == 0,
                'Completed task contains cancellation/errors')
        require(header['accepted'] == 47904 and header['committed_bytes'] == 191616 and header['total_cycles'] > 0,
                'Incomplete full DMA task')
        require([phases[k]['successes'] for k in PHASES] == [11744, 11744, 11744, 12672], 'Wrong four-stage task counts')
    elif outcome == 'cancelled':
        require(header['cancelled'] == 1 and header['errors'] == 0, 'Invalid cancelled outcome')
    else:
        require(header['errors'] > 0, 'Error outcome lacks failed response')
    require(not require_complete or outcome == 'complete', 'Partial/error/cancelled task is not performance acceptance')
    if expected_window is not None:
        require(outcome == 'complete' and tuple(header[k] for k in ('first_offer_cycle', 'last_ack_cycle', 'total_cycles')) ==
                tuple(int(expected_window[k]) for k in ('start_cycle', 'end_cycle', 'cycles')), 'Independent full-task window mismatch')
    return dict(schema=SCHEMA, outcome=outcome, full_task_counts_verified=outcome == 'complete', header=header,
                phases={p: dict(phases[p], statistics={m: measures[p, m] for m in METRICS}) for p in PHASES},
                # Receipts are JSON. Return arrays here so a persisted receipt
                # compares exactly with a fresh parse (tuples reload as lists).
                transitions=switches, contention=contention, histogram_cycle_bins=[list(pair) for pair in BINS],
                note='Passive observations; phase gaps include compute/other traffic; response latency includes response backpressure. CPU-owned wait and simultaneous-VALID competition may overlap. Do not add overlapping statistics to form total task cycles.',
                timing_verified=False, system_power_verified=False)


def binding_include(bindings):
    """Use actual gate probe bindings or explicitly supplied RTL fixture paths."""
    require(set(bindings) >= {'accel', 'arb'}, 'Missing observed accelerator/arbiter binding')
    for key in ('accel', 'arb'):
        require(re.fullmatch(r'[A-Za-z_$][A-Za-z0-9_$]*(?:\.[A-Za-z_$][A-Za-z0-9_$]*)+', bindings[key]), 'Unsafe instance path')
    accel, arb = bindings['accel'], bindings['arb']
    ports = [('clk', 'a3_mon_clk'), ('rst_n', 'a3_mon_rst_n'), ('task_arm', 'a3_task_arm'),
             ('task_cancel', 'a3_task_cancel'), ('task_end', 'a3_window_finished')]
    ports += [('dma_'+n, accel+'.dma_'+n) for n in ('cmd_valid', 'cmd_ready', 'cmd_addr', 'cmd_read', 'cmd_wdata',
              'cmd_wmask', 'rsp_valid', 'rsp_ready', 'rsp_err')]
    ports += [('cpu_'+n, arb+'.cpu_'+n) for n in ('cmd_valid', 'cmd_ready')]
    ports += [('arb_'+n, arb+'.'+n) for n in ('cmd_valid', 'cmd_ready', 'rsp_valid', 'rsp_ready')]
    return '// Passive only; instantiate after original monitor signal declarations.\narch03_dma16_bus_metrics a3_bus_metrics(\n'+',\n'.join(
        '    .%s(%s)' % pair for pair in ports)+'\n);\n'
