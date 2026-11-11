"""Passive ASIC-RTL counters; never change DUT ports or add overlapping spans.

SRAM counts are accepted 16-bit logical macro-port requests, not bytes or power.
Phase latency is acceptance-to-response in cycles, including backpressure.
Counters exist only in the testbench, outside whole-SoC activity/power scope.
"""
import re
from decimal import Decimal
from pathlib import Path

SCHEMA='systolic_b_passive_v1'
PHASES=('source_read','shared_write','output_write')
FIELDS=('rows cycles encoded_bytes x_reads x_writes w_reads w_writes mac_updates '
        'command_ready_wait response_backpressure pending_response_wait turnovers result_stalls').split()


def require(ok,message):
    if not ok:raise ValueError(message)


def instrument(source,rows):
    require(rows == 5,'Unsupported metric row count')
    template=Path(__file__).parents[1]/'tb/arch03_systolic_b_metrics.svh'
    code=template.read_text().replace('@ROWS@',str(rows))
    anchor='reg [15:0] a3_value;'
    require(source.count(anchor)==1 and source.count('$finish;')==1,'Changed positive observer layout')
    return source.replace(anchor,anchor+'\n'+code).replace('$finish;','a3_report_metrics;\n                        $finish;')


def fields(line):
    result={}
    for word in line.split()[1:]:
        pair=word.split('=');require(len(pair)==2 and pair[0] not in result,'Duplicate/malformed metric field')
        result[pair[0]]=pair[1]
    return result


def integers(values):
    require(all(re.fullmatch(r'0|[1-9][0-9]*',v) for v in values.values()),'Invalid unsigned metric')
    return {k:int(v) for k,v in values.items()}


def parse_metrics(text,expected_window):
    lines=[s for s in text.splitlines() if s.startswith('ICB32_METRICS ')]
    require(len(lines)==1,'Missing/duplicate passive metric receipt')
    raw=fields(lines[0]);require(raw.pop('schema',None)==SCHEMA and set(raw)==set(FIELDS),'Metric schema/fields')
    row=integers(raw);r=row['rows'];n=row['encoded_bytes'];cycles=row['cycles']
    require(r == 5 and cycles==expected_window['cycles'] and n==expected_window['encoded_bytes'],'Metrics/window mismatch')
    # Independently derived from matrix dimensions and physical row grouping.
    expected=dict(x_reads=99*64*16,x_writes=99*64,w_reads=((99+r-1)//r)*16*64*16,
                  w_writes=64*256,mac_updates=99*64*256)
    require(all(row[k]==v for k,v in expected.items()),'Incomplete/extra MAC or SRAM accesses')
    require(all(0<=row[k]<=cycles for k in FIELDS[8:]),'Wait/turnover count exceeds task window')
    phase_lines=[s for s in text.splitlines() if s.startswith('ICB32_METRIC_PHASE ')]
    require(len(phase_lines)==3,'Missing/duplicate phase metrics')
    phases={}
    for line in phase_lines:
        v=fields(line);require(set(v)=={'phase','acks','latency_sum','latency_max'},'Phase fields')
        v=integers(v);p=v.pop('phase');require(p in range(3) and PHASES[p] not in phases,'Phase identity')
        require(v['acks']==(n//4 if p<2 else 12672),'Phase ACK count differs from task')
        require(v['acks']<=v['latency_sum']<=v['acks']*v['latency_max'] and v['latency_max']<=cycles,
                'Phase latency inconsistent with ACK count')
        v['mean_response_latency_cycles']=v['latency_sum']/v['acks'];phases[PHASES[p]]=v
    transactions=sum(v['acks'] for v in phases.values())
    require(transactions==expected_window['transfer_transactions'],'Total transaction count differs')
    result=dict(schema=SCHEMA,measured=row,phases=phases,
        mac_utilization=row['mac_updates']/(r*16.*cycles),
        accepted_transactions_per_cycle=transactions/cycles,
        effective_transfer_bytes_per_cycle=transactions*4./cycles,
        sram_unit='one 16-bit logical macro-port request',
        scope='passive_testbench_outside_SoC_power',
        note='Waits/latencies can overlap. Do not sum them as total task time; no power inferred from counters.')
    schedule=[line for line in text.splitlines() if line.startswith('B_SCHEDULE ')]
    if schedule:
        require(len(schedule)==1,'Duplicate B schedule receipt')
        result['schedule']=parse_schedule(schedule[0],expected_window)
    return result


def parse_schedule(line,window):
    values=fields(line)
    require(values.pop('schema',None)=='systolic_b_schedule_v1','Wrong B schedule schema')
    times=('first_feed_ns','last_feed_ns','first_result_ns','last_result_ns','first_output_ns','last_output_ns')
    stamps={key:Decimal(values.pop(key)) for key in times}
    row=integers(values)
    require(set(row)==set(('blocks feeds results supply_empty x_wait w_wait slot_wait credit_wait '
        'intervals interval_sum interval_min interval_max tile_intervals tile_interval_sum').split()),'Wrong schedule fields')
    require(row['blocks']==320 and row['feeds']==20480 and row['results']==25344 and
        row['intervals']==304 and row['tile_intervals']==15,'Incomplete B block/feed/result schedule')
    require(64<=row['interval_min']<=row['interval_max'] and
        row['intervals']*row['interval_min']<=row['interval_sum']<=row['intervals']*row['interval_max'] and
        row['tile_interval_sum']>=15*64,'Impossible B block intervals')
    start,end=Decimal(str(window['start_ns'])),Decimal(str(window['end_ns']))
    require(all(v.is_finite() and start<=v<=end for v in stamps.values()),'Scheduler time outside full task')
    require(stamps['first_feed_ns']<stamps['first_result_ns']<=stamps['first_output_ns'] and
        stamps['first_feed_ns']<stamps['last_feed_ns']<stamps['last_result_ns']<=stamps['last_output_ns'],
        'Scheduler result/transport event ordering')
    period=Decimal(str(window['period_ns']))
    elapsed=(stamps['last_feed_ns']-stamps['first_feed_ns'])/period
    require(abs(elapsed-Decimal(row['feeds']-1+row['supply_empty']))<Decimal('.000001'),
        'Feed plus supply-wait counts do not cover their measured span')
    require(all(row[key]<=window['cycles'] for key in ('supply_empty','x_wait','w_wait','slot_wait','credit_wait')),
        'Schedule wait count exceeds whole task')
    row.update({key:str(value) for key,value in stamps.items()})
    row.update(first_feed_wait_cycles=str((stamps['first_feed_ns']-start)/period),
        compute_result_tail_cycles=str((stamps['last_result_ns']-stamps['last_feed_ns'])/period),
        final_write_tail_cycles=str((end-stamps['last_result_ns'])/period),
        within_tile_mean_start_interval=row['interval_sum']/304.,
        tile_change_mean_start_interval=row['tile_interval_sum']/15.,
        waits_may_overlap=True,core_ii64_only_for_ready_unblocked_conditions=True)
    return row
